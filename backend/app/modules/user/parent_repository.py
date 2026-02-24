"""
Parent monitoring repository — ALL DB queries for the parent dashboard.

Lives in the user module because it owns parent_student_links (ADR-009).

Boundary rules:
  - Owns: parent_student_links (via ParentStudentLink), user_profiles (via UserProfile)
  - Cross-module reads: attempts, exams — queried via raw SQL (text()) to avoid
    importing models across module boundaries (CLAUDE.md rule).
  - No business logic — queries and auth-guard only.
  - get_child_attempts() enforces the parent-child link check BEFORE querying
    child data (ADR-009: parent_student_links is the single authority).

Singleton: import parent_repository (not ParentRepository) in parent_service.py.
"""

import uuid
from typing import Optional

from sqlalchemy import select, text, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import ParentStudentLink, UserProfile
from app.shared.exceptions import Forbidden


class ParentRepository:

    # ── Link queries ──────────────────────────────────────────────────────────

    async def get_linked_children(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> list:
        """
        All ACTIVE links for this parent, joined with child profile data.
        Returns list of (UserProfile, child_nickname, linked_at) rows.
        Ordered by link creation date ascending (oldest link first).
        """
        result = await db.execute(
            select(
                UserProfile,
                ParentStudentLink.child_nickname,
                ParentStudentLink.linked_at,
            )
            .join(
                ParentStudentLink,
                ParentStudentLink.student_id == UserProfile.id,
            )
            .where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.is_active == True,
            )
            .order_by(ParentStudentLink.linked_at.asc())
        )
        return result.all()

    async def get_link(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Optional[ParentStudentLink]:
        """
        Return the ACTIVE link between parent and student, or None.
        Used as an authorization gate before returning any child data.
        Only active links grant access — deactivated links return None.
        """
        result = await db.execute(
            select(ParentStudentLink).where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
                ParentStudentLink.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def find_student_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[dict]:
        """
        Find a student account by email address.
        ONLY returns accounts with role='student'. Admin, parent, or teacher
        accounts are excluded by the WHERE clause — cannot be linked as children.
        Cross-schema query: auth.users is Supabase-managed (not our ORM).
        """
        result = await db.execute(
            text("""
                SELECT up.id, up.full_name, up.std_class,
                       up.school_name, up.is_active
                FROM user_profiles up
                JOIN auth.users au ON au.id = up.id
                WHERE au.email = :email
                AND   up.role = 'student'
                AND   up.is_active = true
            """),
            {"email": email.lower().strip()},
        )
        return result.mappings().first()

    async def create_link(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
        linked_by: uuid.UUID,
    ) -> ParentStudentLink:
        """Create a new active parent-child link. No nickname set at creation."""
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=student_id,
            linked_by=linked_by,
            is_active=True,
        )
        db.add(link)
        await db.flush()
        return link

    async def deactivate_link(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> bool:
        """
        Soft-delete: set is_active=False on the link.
        Returns True if a row was updated, False if no link existed.
        Does not raise — caller decides whether to 404.
        """
        result = await db.execute(
            sa_update(ParentStudentLink)
            .where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
            )
            .values(is_active=False)
        )
        return result.rowcount > 0

    async def update_nickname(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
        nickname: str,
    ) -> bool:
        """
        Update child_nickname on an active link.
        Returns True if updated, False if no active link found.
        """
        result = await db.execute(
            sa_update(ParentStudentLink)
            .where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
                ParentStudentLink.is_active == True,
            )
            .values(child_nickname=nickname)
        )
        return result.rowcount > 0

    # ── Child data queries (cross-module via raw SQL) ─────────────────────────

    async def get_child_attempts(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
        limit: int = 20,
    ) -> list:
        """
        Submitted attempts for a child, with exam metadata.
        Enforces parent-child link check first (ADR-009).
        Cross-module join (attempts + exams) via raw SQL only — no model imports.
        Raises Forbidden if parent is not linked to this student.
        """
        link = await self.get_link(db, parent_id, student_id)
        if not link:
            raise Forbidden("Not linked to this student")

        result = await db.execute(
            text("""
                SELECT
                    a.id              AS attempt_id,
                    e.title_en        AS exam_title_en,
                    e.title_mr        AS exam_title_mr,
                    e.paper_code,
                    a.attempt_number,
                    a.status,
                    a.submitted_at,
                    a.total_score,
                    e.total_marks,
                    a.percentage,
                    a.grade,
                    a.duration_seconds
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                WHERE a.student_id = :sid
                AND   a.status = 'submitted'
                ORDER BY a.submitted_at DESC
                LIMIT :lim
            """),
            {"sid": str(student_id), "lim": limit},
        )
        return result.mappings().all()

    async def get_child_stats(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> dict:
        """
        Aggregate stats across all submitted attempts for one child.
        Returns safe zero-defaults when the student has no submitted attempts yet.
        COUNT(*) always returns a row — defaults triggered by total_attempts = 0.
        """
        result = await db.execute(
            text("""
                SELECT
                    COUNT(*)                                     AS total_attempts,
                    ROUND(AVG(percentage)::numeric, 1)           AS avg_percentage,
                    MAX(total_score)                             AS best_score,
                    ROUND(MAX(percentage)::numeric, 1)           AS best_percentage,
                    MAX(submitted_at)                            AS last_active,
                    COUNT(DISTINCT exam_id)                      AS exams_completed
                FROM attempts
                WHERE student_id = :sid
                AND   status = 'submitted'
            """),
            {"sid": str(student_id)},
        )
        row = result.mappings().first()
        if not row or not row["total_attempts"]:
            return {
                "total_attempts": 0,
                "avg_percentage": None,
                "best_score": None,
                "best_percentage": None,
                "last_active": None,
                "exams_completed": 0,
            }
        return dict(row)

    async def get_child_topic_performance(
        self, db: AsyncSession, student_id: uuid.UUID
    ) -> list:
        """
        Per-topic average percentage across all submitted attempts.
        Unpacks topic_scores JSONB array from each attempt row.
        Returns rows ordered ASC by avg_percentage (worst topic first).
        status thresholds: strong >= 70%, average >= 50%, weak < 50%.
        """
        result = await db.execute(
            text("""
                SELECT
                    (topic->>'topic_id')::int                          AS topic_id,
                    topic->>'name_en'                                  AS topic_name_en,
                    topic->>'name_mr'                                  AS topic_name_mr,
                    ROUND(
                        AVG((topic->>'percentage')::float)::numeric, 1
                    )                                                  AS avg_percentage,
                    COUNT(*)                                           AS attempts_count,
                    CASE
                        WHEN AVG((topic->>'percentage')::float) >= 70
                            THEN 'strong'
                        WHEN AVG((topic->>'percentage')::float) >= 50
                            THEN 'average'
                        ELSE 'weak'
                    END                                                AS status
                FROM attempts,
                     jsonb_array_elements(topic_scores) AS topic
                WHERE student_id = :sid
                AND   status = 'submitted'
                AND   jsonb_array_length(topic_scores) > 0
                GROUP BY topic_id, topic_name_en, topic_name_mr
                ORDER BY avg_percentage ASC
            """),
            {"sid": str(student_id)},
        )
        return [dict(row) for row in result.mappings().all()]


# Module-level singleton — import this in parent_service.py (next session)
parent_repository = ParentRepository()
