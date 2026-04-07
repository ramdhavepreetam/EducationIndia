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

    async def publish_exam(self, db: AsyncSession, exam_id: int) -> Exam:
        """
        Set is_active=True on an exam, making it visible to students.
        Admin only — router enforces require_admin.
        Raises NotFound if exam_id does not exist.
        """
        # Verify exam exists before attempting update
        await self.get_exam(db, exam_id)
        exam = await catalog_repository.set_exam_active(db, exam_id, is_active=True)
        return exam  # type: ignore[return-value]  # get_exam above guarantees non-None

    async def unpublish_exam(self, db: AsyncSession, exam_id: int) -> Exam:
        """
        Set is_active=False on an exam, hiding it from students.
        Admin only — router enforces require_admin.
        """
        await self.get_exam(db, exam_id)
        exam = await catalog_repository.set_exam_active(db, exam_id, is_active=False)
        return exam  # type: ignore[return-value]


# Module-level singleton — import this in router.py and other modules
catalog_service = CatalogService()
