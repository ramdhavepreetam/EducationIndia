"""
Parent monitoring service — all business logic for the parent dashboard.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analysis.schemas import WrongAnswersSummary
from app.modules.analysis.wrong_answers import build_wrong_answers_summary
from app.modules.user.parent_repository import parent_repository
from app.modules.user.child_repository import ChildRepository
from app.modules.user.child_schemas import ChildProfileSchema
from app.modules.user.parent_schemas import (
    ChildAttemptSummarySchema,
    ChildDetailSchema,
    ChildStatsSchema,
    ParentDashboardSchema,
    RecentMistakesSchema,
    WeakTopicSchema,
)
from app.shared.access_control import get_access_context, can_see_full_analysis
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

    # ── Wrong Answers Review (ADR-012, ADR-013, ADR-014) ──────────────────────

    async def get_attempt_wrong_answers(
        self,
        parent_id: UUID,
        child_profile_id: UUID,
        attempt_id: UUID,
        db: AsyncSession,
    ) -> WrongAnswersSummary:
        """
        Returns wrong answers for a specific submitted attempt.
        Reuses analysis.wrong_answers.build_wrong_answers_summary.

        Security checks (all must pass before loading any data):
          1. child_profile belongs to this parent (ADR-013)
          2. attempt belongs to this child_profile
          3. attempt.status == 'submitted' (ADR-012)
        Then:
          4. check paid tier → include_details flag (ADR-014)
          5. call build_wrong_answers_summary
        """
        # Check 1: parent owns child profile
        child = await self.child_repo.get_by_id(child_profile_id, parent_id, db)
        if not child:
            raise Forbidden("Child profile not found")

        # Check 2: attempt belongs to this child_profile
        attempt = await db.execute(
            text("""
                SELECT id, status
                FROM attempts
                WHERE id = :aid
                AND child_profile_id = :cid
            """),
            {"aid": str(attempt_id), "cid": str(child_profile_id)},
        )
        attempt_row = attempt.mappings().first()
        if not attempt_row:
            raise NotFound("Attempt not found for this child")

        # Check 3: must be submitted (ADR-012 — correct_option post-submit only)
        if attempt_row["status"] != "submitted":
            raise Forbidden("Attempt must be submitted to review answers")

        # Check 4: paid tier check (ADR-014)
        ctx = await get_access_context(parent_id, db)
        include_details = can_see_full_analysis(ctx)

        # Check 5: build and return
        return await build_wrong_answers_summary(
            attempt_id=attempt_id,
            db=db,
            include_details=include_details,
        )

    async def get_recent_mistakes_summary(
        self,
        parent_id: UUID,
        child_profile_id: UUID,
        db: AsyncSession,
    ) -> RecentMistakesSchema:
        """
        Returns the most recent 5 wrong questions from the child's
        most recent submitted attempt. Used for the dashboard card.

        Free tier: returns attempt metadata + counts, items=[].
        Paid tier: returns attempt metadata + top 5 wrong items.
        """
        # Check 1: parent owns child
        child = await self.child_repo.get_by_id(child_profile_id, parent_id, db)
        if not child:
            raise Forbidden("Child profile not found")

        # Get most recent SUBMITTED attempt for this child
        result = await db.execute(
            text("""
                SELECT
                    a.id            AS attempt_id,
                    a.submitted_at,
                    a.total_score,
                    a.percentage,
                    a.grade,
                    e.title_en      AS exam_title_en,
                    e.title_mr      AS exam_title_mr,
                    e.paper_code
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                WHERE a.child_profile_id = :cid
                AND   a.status = 'submitted'
                ORDER BY a.submitted_at DESC
                LIMIT 1
            """),
            {"cid": str(child_profile_id)},
        )
        latest = result.mappings().first()

        if not latest:
            return RecentMistakesSchema(
                has_attempts=False,
                attempt_id=None,
                exam_title_en=None,
                exam_title_mr=None,
                submitted_at=None,
                total_score=None,
                grade=None,
                wrong_answers_summary=None,
            )

        # Paid tier check (ADR-014)
        ctx = await get_access_context(parent_id, db)
        include_details = can_see_full_analysis(ctx)

        # Get wrong answers (limit to 5 for dashboard card)
        summary = await build_wrong_answers_summary(
            attempt_id=latest["attempt_id"],
            db=db,
            include_details=include_details,
            limit=5,
        )

        return RecentMistakesSchema(
            has_attempts=True,
            attempt_id=latest["attempt_id"],
            exam_title_en=latest["exam_title_en"],
            exam_title_mr=latest["exam_title_mr"],
            paper_code=latest["paper_code"],
            submitted_at=latest["submitted_at"],
            total_score=latest["total_score"],
            grade=latest["grade"],
            wrong_answers_summary=summary,
        )


parent_service = ParentService()
