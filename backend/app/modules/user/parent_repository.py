"""
Parent monitoring repository — ALL DB queries for the parent dashboard.

Boundary rules:
  - Cross-module reads: attempts, exams — queried via raw SQL (text()) to avoid
    importing models across module boundaries (CLAUDE.md rule).
  - No business logic — queries and auth-guard only.
"""

import uuid
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import ChildProfile
from app.shared.exceptions import Forbidden


class ParentRepository:

    async def get_child_attempts(
        self,
        db: AsyncSession,
        child_profile_id: uuid.UUID,
        limit: int = 20,
    ) -> list:
        """
        Submitted attempts for a child, with exam metadata.
        Cross-module join (attempts + exams) via raw SQL only — no model imports.
        """
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
                WHERE a.child_profile_id = :cid
                AND   a.status = 'submitted'
                ORDER BY a.submitted_at DESC
                LIMIT :lim
            """),
            {"cid": str(child_profile_id), "lim": limit},
        )
        return result.mappings().all()

    async def get_child_stats(
        self, db: AsyncSession, child_profile_id: uuid.UUID
    ) -> dict:
        """
        Aggregate stats across all submitted attempts for one child.
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
                WHERE child_profile_id = :cid
                AND   status = 'submitted'
            """),
            {"cid": str(child_profile_id)},
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
        self, db: AsyncSession, child_profile_id: uuid.UUID
    ) -> list:
        """
        Per-topic average percentage across all submitted attempts.
        Unpacks topic_scores JSONB array from each attempt row.
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
                WHERE child_profile_id = :cid
                AND   status = 'submitted'
                AND   jsonb_array_length(topic_scores) > 0
                GROUP BY topic_id, topic_name_en, topic_name_mr
                ORDER BY avg_percentage ASC
            """),
            {"cid": str(child_profile_id)},
        )
        return [dict(row) for row in result.mappings().all()]


# Module-level singleton
parent_repository = ParentRepository()
