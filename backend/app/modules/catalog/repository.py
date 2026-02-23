"""
Catalog module repository — ALL database queries live here.

CLAUDE.md rule: services call repository, never execute queries directly.
Routers call services, never call repository directly.
"""

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.models import Exam, ExamBoard, ExamEvent, Section, Topic


class CatalogRepository:

    # ── ExamBoard queries ─────────────────────────────────────────────────────

    async def list_active_boards(self, db: AsyncSession) -> list[ExamBoard]:
        """Return all active boards. Students see these for navigation."""
        result = await db.execute(
            select(ExamBoard).where(ExamBoard.is_active == True).order_by(ExamBoard.id)
        )
        return list(result.scalars().all())

    # ── Exam listing queries ──────────────────────────────────────────────────

    async def list_exams(
        self,
        db: AsyncSession,
        *,
        board_id: int | None = None,
        std_class: int | None = None,
        year: int | None = None,
        include_inactive: bool = False,
    ) -> list[Exam]:
        """
        List exams with optional filters.
        Students always get include_inactive=False (is_active filter applied).
        Admins can pass include_inactive=True to see all exams.
        JOIN path: Exam → ExamEvent (for board_id / std_class / year filters).
        """
        stmt = select(Exam).join(Exam.event)

        if not include_inactive:
            stmt = stmt.where(Exam.is_active == True)

        if board_id is not None:
            stmt = stmt.where(ExamEvent.board_id == board_id)

        if std_class is not None:
            stmt = stmt.where(ExamEvent.std_class == std_class)

        if year is not None:
            stmt = stmt.where(ExamEvent.year == year)

        stmt = stmt.order_by(ExamEvent.year.desc(), Exam.paper_code)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ── Single exam queries ───────────────────────────────────────────────────

    async def get_exam_by_id(self, db: AsyncSession, exam_id: int) -> Exam | None:
        """
        Return a single exam with sections and topics eagerly loaded.
        Used in GET /api/catalog/exams/{id}.
        Uses nested selectinload to avoid N+1 on sections → topics.
        """
        result = await db.execute(
            select(Exam)
            .options(
                selectinload(Exam.sections).selectinload(Section.topics)
            )
            .where(Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    # ── Admin mutations ───────────────────────────────────────────────────────

    async def set_exam_active(
        self, db: AsyncSession, exam_id: int, is_active: bool
    ) -> Exam | None:
        """Toggle is_active on an exam. Returns the updated exam row."""
        await db.execute(
            sa_update(Exam).where(Exam.id == exam_id).values(is_active=is_active)
        )
        await db.flush()
        return await self.get_exam_by_id(db, exam_id)


# Module-level singleton — import this in service.py
catalog_repository = CatalogRepository()
