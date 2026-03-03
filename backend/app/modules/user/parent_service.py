"""
Parent monitoring service — all business logic for the parent dashboard.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.parent_repository import parent_repository
from app.modules.user.child_repository import ChildRepository
from app.modules.user.child_schemas import ChildProfileSchema
from app.modules.user.parent_schemas import (
    ChildAttemptSummarySchema,
    ChildDetailSchema,
    ChildStatsSchema,
    ParentDashboardSchema,
    WeakTopicSchema,
)
from app.shared.exceptions import Forbidden, NotFound


class ParentService:

    def __init__(self):
        self.child_repo = ChildRepository()

    def _build_attempt_summary(self, row) -> ChildAttemptSummarySchema:
        return ChildAttemptSummarySchema(**dict(row))

    async def get_dashboard(
        self, db: AsyncSession, parent_id: UUID
    ) -> ParentDashboardSchema:
        children = await self.child_repo.get_children(parent_id, db)
        if not children:
            return ParentDashboardSchema(children=[], selected_child_detail=None)

        child_schemas = [ChildProfileSchema.model_validate(c) for c in children]
        first_child_id = child_schemas[0].id
        detail = await self.get_child_detail(db, parent_id, first_child_id)

        return ParentDashboardSchema(children=child_schemas, selected_child_detail=detail)

    async def get_child_detail(
        self, db: AsyncSession, parent_id: UUID, child_id: UUID
    ) -> ChildDetailSchema:
        child = await self.child_repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise Forbidden("Child profile not found or does not belong to you")

        stats_raw = await parent_repository.get_child_stats(db, child_id)
        attempt_rows = await parent_repository.get_child_attempts(
            db, child_id, limit=10
        )
        topics_raw = await parent_repository.get_child_topic_performance(
            db, child_id
        )

        profile = ChildProfileSchema.model_validate(child)
        stats = ChildStatsSchema(**stats_raw)
        attempts = [self._build_attempt_summary(r) for r in attempt_rows]

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
        child_id: UUID,
        page: int = 1,
        size: int = 10,
    ) -> dict:
        child = await self.child_repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise Forbidden("Child profile not found or does not belong to you")

        all_rows = await parent_repository.get_child_attempts(
            db, child_id, limit=200
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
        self, db: AsyncSession, parent_id: UUID, child_id: UUID
    ) -> list[WeakTopicSchema]:
        child = await self.child_repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise Forbidden("Child profile not found or does not belong to you")

        topics_raw = await parent_repository.get_child_topic_performance(
            db, child_id
        )
        return [WeakTopicSchema(**t) for t in topics_raw]


parent_service = ParentService()
