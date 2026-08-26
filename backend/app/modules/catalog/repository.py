"""
Catalog module repository — ALL database queries live here.

CLAUDE.md rule: services call repository, never execute queries directly.
Routers call services, never call repository directly.
"""

from sqlalchemy import select, text, update as sa_update
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
                selectinload(Exam.event),
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

    async def get_paper_health(self, db: AsyncSession, exam_id: int) -> dict | None:
        """
        Read one row from v_paper_health (added 2026-08-17).

        publish_blocker_count counts questions that cannot be answered correctly:
        a blank correct answer, or no stem at all. Any value above zero means the
        paper must not go live. Returns None when the exam has no row.
        """
        row = (
            await db.execute(
                text(
                    """
                    SELECT exam_id, total_questions, cancelled_questions,
                           missing_image_count, missing_stem_count,
                           blank_option_count, blank_correct_answer_count,
                           publish_blocker_count
                    FROM v_paper_health
                    WHERE exam_id = :exam_id
                    """
                ),
                {"exam_id": exam_id},
            )
        ).mappings().first()
        return dict(row) if row else None


    async def create_event(
        self,
        db: AsyncSession,
        *,
        board_id: int,
        category_id: int,
        title_en: str,
        title_mr: str | None,
        std_class: int,
        year: int,
    ) -> ExamEvent:
        """Insert a new exam_event row (draft state, is_active defaults to False)."""
        event = ExamEvent(
            board_id=board_id,
            category_id=category_id,
            title_en=title_en,
            title_mr=title_mr,
            std_class=std_class,
            year=year,
            is_active=False,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event

    async def create_exam_under_event(
        self,
        db: AsyncSession,
        *,
        event_id: int,
        paper_code: str,
        set_code: str,
        title_en: str,
        title_mr: str | None = None,
    ) -> Exam:
        """Insert an exam (paper) under an event. Returns the new Exam row."""
        exam = Exam(
            event_id=event_id,
            paper_code=paper_code,
            set_code=set_code,
            title_en=title_en,
            title_mr=title_mr,
            is_active=False,
        )
        db.add(exam)
        await db.flush()
        await db.refresh(exam)
        return exam

    async def clone_sections_and_topics(
        self,
        db: AsyncSession,
        *,
        source_exam_id: int,
        target_exam_id: int,
    ) -> None:
        """
        Clone sections + topics from source_exam_id into target_exam_id.
        Used when creating a new test to replicate the existing structure.
        """
        source = await self.get_exam_by_id(db, source_exam_id)
        if source is None:
            return
        for src_section in source.sections:
            new_section = Section(
                exam_id=target_exam_id,
                section_label=src_section.section_label,
                subject_en=src_section.subject_en,
                subject_mr=src_section.subject_mr,
                question_from=src_section.question_from,
                question_to=src_section.question_to,
                order_index=src_section.order_index,
                color_hex=src_section.color_hex,
            )
            db.add(new_section)
            await db.flush()
            await db.refresh(new_section)
            for src_topic in src_section.topics:
                db.add(Topic(
                    section_id=new_section.id,
                    name_en=src_topic.name_en,
                    name_mr=src_topic.name_mr,
                    description_en=src_topic.description_en,
                    description_mr=src_topic.description_mr,
                    order_index=src_topic.order_index,
                ))
        await db.flush()


# Module-level singleton — import this in service.py
catalog_repository = CatalogRepository()
