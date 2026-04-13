"""
Catalog module service — business logic layer.

Rules:
- Students can only see is_active=True exams (enforced here, not just in RLS).
- Admins can see all exams and toggle is_active.
- Service calls repository only; never writes raw SQL.
- Exposes: CatalogService.get_exam(), CatalogService.list_exams() (CLAUDE.md contract)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Exam, ExamBoard
from app.modules.catalog.repository import catalog_repository
from app.shared.exceptions import NotFound


class CatalogService:

    # ── Public interface (used by other modules) ──────────────────────────────

    async def list_boards(self, db: AsyncSession) -> list[ExamBoard]:
        """Return all active boards. No auth required — public catalog."""
        return await catalog_repository.list_active_boards(db)

    async def list_exams(
        self,
        db: AsyncSession,
        *,
        board_id: int | None = None,
        std_class: int | None = None,
        year: int | None = None,
        is_admin: bool = False,
    ) -> list[Exam]:
        """
        List exams with optional filters.
        Non-admins only see active exams (is_active=True).
        Admins see all exams so they can verify before publishing.
        """
        return await catalog_repository.list_exams(
            db,
            board_id=board_id,
            std_class=std_class,
            year=year,
            include_inactive=is_admin,
        )

    async def list_exams_with_access(
        self,
        db: AsyncSession,
        parent_id,
        *,
        board_id: int | None = None,
        std_class: int | None = None,
        year: int | None = None,
    ) -> list[dict]:
        """
        List exams with access flags for a parent (ADR-014).
        Returns dicts with is_accessible and lock_reason fields.
        """
        from app.shared.access_control import get_access_context

        exams = await catalog_repository.list_exams(
            db, board_id=board_id, std_class=std_class, year=year, include_inactive=False,
        )
        ctx = await get_access_context(parent_id, db)

        result = []
        for exam in exams:
            is_accessible = ctx.is_paid or (exam.id == ctx.free_exam_id)
            result.append({
                "id": exam.id,
                "event_id": exam.event_id,
                "paper_code": exam.paper_code,
                "set_code": exam.set_code,
                "title_en": exam.title_en,
                "title_mr": exam.title_mr,
                "medium": exam.medium.value if hasattr(exam.medium, "value") else str(exam.medium),
                "total_questions": exam.total_questions,
                "total_marks": exam.total_marks,
                "duration_minutes": exam.duration_minutes,
                "is_active": exam.is_active,
                "is_accessible": is_accessible,
                "lock_reason": None if is_accessible else "upgrade_required_exam",
            })
        return result

    async def get_exam(self, db: AsyncSession, exam_id: int) -> Exam:
        """
        Return a single exam with sections + topics eagerly loaded.
        Public contract method — consumed by question and attempt modules.
        Raises NotFound if exam does not exist.
        """
        exam = await catalog_repository.get_exam_by_id(db, exam_id)
        if exam is None:
            raise NotFound(f"Exam {exam_id} not found")
        return exam

    async def get_active_exam(self, db: AsyncSession, exam_id: int) -> Exam:
        """
        Like get_exam() but raises NotFound for inactive exams.
        Used by attempt module to prevent starting a deactivated exam.
        """
        exam = await self.get_exam(db, exam_id)
        if not exam.is_active:
            raise NotFound(f"Exam {exam_id} is not available")
        return exam

    # ── Admin operations ──────────────────────────────────────────────────────

    async def publish_exam(self, db: AsyncSession, exam_id: int) -> dict:
        """
        Set is_active=True on an exam, making it visible to students.
        Also auto-assigns the exam to all students of the matching grade.
        Admin only — router enforces require_admin.
        Returns: {"exam_id", "is_active", "auto_assigned_count"}
        """
        exam = await self.get_exam(db, exam_id)
        await catalog_repository.set_exam_active(db, exam_id, is_active=True)
        await db.commit()   # always commit is_active=True regardless of auto-assignment

        # Get std_class from exam_event — event is eager-loaded with the exam
        event = exam.event
        std_class = event.std_class if event else None
        auto_count = 0
        if std_class in (5, 8):
            auto_count = await self.auto_assign_exam_to_grade(db, exam_id, std_class)

        return {"exam_id": exam_id, "is_active": True, "auto_assigned_count": auto_count}

    async def unpublish_exam(self, db: AsyncSession, exam_id: int) -> Exam:
        """
        Set is_active=False on an exam, hiding it from students.
        Admin only — router enforces require_admin.
        """
        await self.get_exam(db, exam_id)
        exam = await catalog_repository.set_exam_active(db, exam_id, is_active=False)
        return exam  # type: ignore[return-value]

    async def create_event_with_papers(
        self,
        db: AsyncSession,
        data: "CreateEventRequest",
    ) -> "EventWithExamsResponse":
        """
        Create a new exam_event with Paper I (501) and Paper II (502).
        set_code is set to the 4-digit year to avoid UNIQUE(paper_code, set_code) collisions.
        Sections and topics are cloned from the existing Paper I of the same board.
        """
        from app.modules.catalog.schemas import CreateEventRequest, EventWithExamsResponse, ExamSummaryResponse

        event = await catalog_repository.create_event(
            db,
            board_id=data.board_id,
            category_id=data.category_id,
            title_en=data.title_en,
            title_mr=data.title_mr,
            std_class=data.std_class,
            year=data.year,
        )

        set_code = str(data.year)

        paper1 = await catalog_repository.create_exam_under_event(
            db,
            event_id=event.id,
            paper_code="501",
            set_code=set_code,
            title_en=f"{data.title_en} — Paper I",
            title_mr=f"{data.title_mr} — Paper I" if data.title_mr else None,
        )
        paper2 = await catalog_repository.create_exam_under_event(
            db,
            event_id=event.id,
            paper_code="502",
            set_code=set_code,
            title_en=f"{data.title_en} — Paper II",
            title_mr=f"{data.title_mr} — Paper II" if data.title_mr else None,
        )

        # Clone sections + topics from existing papers of same board as template
        existing = await catalog_repository.list_exams(
            db, board_id=data.board_id, include_inactive=True
        )
        paper1_template = next((e for e in existing if e.paper_code == "501" and e.id != paper1.id), None)
        paper2_template = next((e for e in existing if e.paper_code == "502" and e.id != paper2.id), None)

        if paper1_template:
            await catalog_repository.clone_sections_and_topics(
                db, source_exam_id=paper1_template.id, target_exam_id=paper1.id
            )
        if paper2_template:
            await catalog_repository.clone_sections_and_topics(
                db, source_exam_id=paper2_template.id, target_exam_id=paper2.id
            )

        await db.commit()

        paper1_fresh = await self.get_exam(db, paper1.id)
        paper2_fresh = await self.get_exam(db, paper2.id)

        return EventWithExamsResponse(
            id=event.id,
            title_en=event.title_en,
            title_mr=event.title_mr,
            std_class=event.std_class,
            year=event.year,
            exams=[
                ExamSummaryResponse.model_validate(paper1_fresh),
                ExamSummaryResponse.model_validate(paper2_fresh),
            ],
        )

    async def auto_assign_exam_to_grade(
        self,
        db: AsyncSession,
        exam_id: int,
        std_class: int,
    ) -> int:
        """
        Auto-assign an exam to all students whose std_class matches.
        Returns the count of students assigned.
        Called by publish_exam() after activating a paper.
        Calls attempt_repository.bulk_create_assignments (attempt module owns exam_assignments).
        """
        from sqlalchemy import text
        from app.modules.attempt.repository import attempt_repository

        # Fetch all student UUIDs with matching std_class
        result = await db.execute(
            text(
                "SELECT id FROM user_profiles "
                "WHERE std_class = :cls AND role = 'student' AND is_active = true"
            ),
            {"cls": std_class},
        )
        student_ids = [row[0] for row in result.fetchall()]

        if not student_ids:
            return 0

        rows = [{"exam_id": exam_id, "student_id": sid} for sid in student_ids]
        await attempt_repository.bulk_create_assignments(db, rows)
        await db.commit()
        return len(student_ids)


# Module-level singleton — import this in router.py and other modules
catalog_service = CatalogService()
