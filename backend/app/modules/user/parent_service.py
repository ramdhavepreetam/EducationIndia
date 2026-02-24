"""
Parent monitoring service — all business logic for the parent dashboard.

Lives in the user module (ADR-009).
Repository handles DB queries. Service handles decisions.

Rules enforced here:
  - Always verify parent-child link before accessing child data (ADR-009)
  - Defence-in-depth: link checked at service level AND inside get_child_attempts()
  - Never import models from other modules — cross-module data via parent_repository raw SQL
  - Sequential DB calls only — single AsyncSession is not concurrency-safe

Singleton: import parent_service (not ParentService) in parent_router.py.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.parent_repository import parent_repository
from app.modules.user.parent_schemas import (
    ChildAttemptSummarySchema,
    ChildDetailSchema,
    ChildProfileSchema,
    ChildStatsSchema,
    ParentDashboardSchema,
    WeakTopicSchema,
)
from app.shared.exceptions import BadRequest, Conflict, Forbidden, NotFound


class ParentService:

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_child_profile(self, row) -> ChildProfileSchema:
        """
        Build ChildProfileSchema from a get_linked_children row.
        Row is a SQLAlchemy Row: (UserProfile, child_nickname, linked_at).
        MediumTypeEnum extends str, so profile.medium is already string-compatible.
        """
        profile, nickname, linked_at = row
        return ChildProfileSchema(
            student_id=profile.id,
            full_name=profile.full_name,
            std_class=profile.std_class,
            medium=profile.medium,
            school_name=profile.school_name,
            district=profile.district,
            avatar_url=profile.avatar_url,
            child_nickname=nickname,
            is_onboarded=profile.is_onboarded,
            linked_at=linked_at,
        )

    def _build_attempt_summary(self, row) -> ChildAttemptSummarySchema:
        """
        Build ChildAttemptSummarySchema from a get_child_attempts mapping row.
        Keys match schema field names exactly (attempt_id, exam_title_en, etc.).
        """
        return ChildAttemptSummarySchema(**dict(row))

    # ── Public methods ────────────────────────────────────────────────────────

    async def get_dashboard(
        self, db: AsyncSession, parent_id: UUID
    ) -> ParentDashboardSchema:
        """
        Returns all linked children + full detail for the first child.
        If no children linked, returns an empty dashboard (no error).
        """
        rows = await parent_repository.get_linked_children(db, parent_id)
        if not rows:
            return ParentDashboardSchema(children=[], selected_child_detail=None)

        children = [self._build_child_profile(r) for r in rows]
        first_child_id = children[0].student_id
        detail = await self.get_child_detail(db, parent_id, first_child_id)

        return ParentDashboardSchema(children=children, selected_child_detail=detail)

    async def get_children(
        self, db: AsyncSession, parent_id: UUID
    ) -> list[ChildProfileSchema]:
        """Return all linked children as profile schemas."""
        rows = await parent_repository.get_linked_children(db, parent_id)
        return [self._build_child_profile(r) for r in rows]

    async def get_child_detail(
        self, db: AsyncSession, parent_id: UUID, student_id: UUID
    ) -> ChildDetailSchema:
        """
        Full detail for one child: profile + stats + recent attempts + topics.
        Service checks link first. get_child_attempts() also checks link (ADR-009
        defence-in-depth — repository is the single authority on the link).
        """
        link = await parent_repository.get_link(db, parent_id, student_id)
        if not link:
            raise Forbidden("You are not linked to this student")

        # Sequential queries — single AsyncSession is not concurrency-safe
        stats_raw = await parent_repository.get_child_stats(db, student_id)
        attempt_rows = await parent_repository.get_child_attempts(
            db, parent_id, student_id
        )
        topics_raw = await parent_repository.get_child_topic_performance(
            db, student_id
        )
        child_rows = await parent_repository.get_linked_children(db, parent_id)

        child_row = next((r for r in child_rows if r[0].id == student_id), None)
        if not child_row:
            raise NotFound("Child profile not found")

        profile = self._build_child_profile(child_row)
        stats = ChildStatsSchema(**stats_raw)
        attempts = [self._build_attempt_summary(r) for r in attempt_rows[:10]]

        weak_topics = [
            WeakTopicSchema(**t) for t in topics_raw if t["status"] == "weak"
        ]
        strong_topics = [
            WeakTopicSchema(**t) for t in topics_raw if t["status"] == "strong"
        ]
        strong_topics.sort(key=lambda t: t.avg_percentage, reverse=True)

        return ChildDetailSchema(
            profile=profile,
            stats=stats,
            recent_attempts=attempts,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
        )

    async def get_child_attempts_paged(
        self,
        db: AsyncSession,
        parent_id: UUID,
        student_id: UUID,
        page: int = 1,
        size: int = 10,
    ) -> dict:
        """
        Paginated attempt history for a child.
        Link is verified before querying — raises Forbidden if not linked.
        """
        link = await parent_repository.get_link(db, parent_id, student_id)
        if not link:
            raise Forbidden("You are not linked to this student")

        all_rows = await parent_repository.get_child_attempts(
            db, parent_id, student_id, limit=200
        )
        total = len(all_rows)
        start = (page - 1) * size
        end = start + size
        page_rows = all_rows[start:end]

        return {
            "items": [self._build_attempt_summary(r) for r in page_rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    async def get_child_topics(
        self, db: AsyncSession, parent_id: UUID, student_id: UUID
    ) -> list[WeakTopicSchema]:
        """Per-topic performance for a child. Link required."""
        link = await parent_repository.get_link(db, parent_id, student_id)
        if not link:
            raise Forbidden("You are not linked to this student")

        topics_raw = await parent_repository.get_child_topic_performance(
            db, student_id
        )
        return [WeakTopicSchema(**t) for t in topics_raw]

    async def link_child(
        self, db: AsyncSession, parent_id: UUID, student_email: str
    ) -> ChildProfileSchema:
        """
        Link a parent to a student account by email.
        Guards: student must exist, not already linked, not a self-link.
        """
        student = await parent_repository.find_student_by_email(db, student_email)
        if not student:
            raise NotFound(
                "No student account found with this email. "
                "Ask your child to register on ScholarPath first."
            )

        student_id = student["id"]

        if str(parent_id) == str(student_id):
            raise BadRequest("You cannot link to your own account")

        existing = await parent_repository.get_link(db, parent_id, student_id)
        if existing:
            raise Conflict("You are already monitoring this student")

        await parent_repository.create_link(db, parent_id, student_id, parent_id)
        await db.commit()

        rows = await parent_repository.get_linked_children(db, parent_id)
        new_row = next((r for r in rows if r[0].id == student_id), None)
        if not new_row:
            raise NotFound("Could not load new child profile after linking")
        return self._build_child_profile(new_row)

    async def update_nickname(
        self,
        db: AsyncSession,
        parent_id: UUID,
        student_id: UUID,
        nickname: str,
    ) -> ChildProfileSchema:
        """Update child nickname on an active link. Raises NotFound if link missing."""
        updated = await parent_repository.update_nickname(
            db, parent_id, student_id, nickname
        )
        if not updated:
            raise NotFound("Active link not found — cannot update nickname")

        await db.commit()

        rows = await parent_repository.get_linked_children(db, parent_id)
        row = next((r for r in rows if r[0].id == student_id), None)
        if not row:
            raise NotFound("Child not found after nickname update")
        return self._build_child_profile(row)

    async def unlink_child(
        self, db: AsyncSession, parent_id: UUID, student_id: UUID
    ) -> bool:
        """
        Soft-deactivates the parent-child link (is_active=False).
        Does NOT delete the student account or any attempt/analysis data.
        """
        link = await parent_repository.get_link(db, parent_id, student_id)
        if not link:
            raise NotFound("Link not found or already removed")

        await parent_repository.deactivate_link(db, parent_id, student_id)
        await db.commit()
        return True


# Module-level singleton — import this in parent_router.py
parent_service = ParentService()
