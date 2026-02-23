"""
Question module service — business logic layer.

Rules:
- Delivery: validates exam is active, returns QuestionDeliverySchema (no correct_option)
- Review: validates attempt is submitted before returning correct answers
- Import: validates all questions before inserting, returns detailed error report
- Service calls repository only; never writes raw SQL.

Public interface (CLAUDE.md contract):
  QuestionService.get_questions_for_exam()  → consumed by attempt module
  QuestionService.validate_answer()         → consumed by attempt module (TODO)
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.service import catalog_service
from app.modules.question.importer import validate_question_import
from app.modules.question.repository import question_repository
from app.modules.question.schemas import (
    BulkImportResult,
    BulkImportSchema,
    QuestionAdminSchema,
    QuestionDeliverySchema,
    QuestionReviewSchema,
    QuestionUpdateRequest,
)
from app.shared.exceptions import BadRequest, Forbidden, NotFound


class QuestionService:

    # ── Public interface (used by other modules) ──────────────────────────────

    async def get_questions_for_exam(
        self, db: AsyncSession, exam_id: int
    ) -> list[QuestionDeliverySchema]:
        """
        Return all questions for an exam in delivery format (no correct_option).
        Validates exam exists and is active (students can't start deactivated exams).
        Called by: attempt module when starting an exam session.
        """
        # Raises NotFound if exam doesn't exist or is inactive
        await catalog_service.get_active_exam(db, exam_id)
        return await question_repository.fetch_by_exam_id(db, exam_id)

    # ── Review (post-exam) ────────────────────────────────────────────────────

    async def get_question_for_review(
        self,
        db: AsyncSession,
        question_id: int,
        attempt_id: UUID,
        student_id: UUID,
    ) -> QuestionReviewSchema:
        """
        Return a question with correct_option and explanation.

        SECURITY GATES (both must pass):
        1. Attempt must belong to the requesting student.
        2. Attempt status must be 'submitted' — ongoing attempts cannot review answers.

        Raises:
          NotFound if question or attempt not found.
          Forbidden if attempt doesn't belong to student or status != submitted.
        """
        # Validate attempt ownership and status
        attempt = await question_repository.get_attempt_status(db, attempt_id)
        if attempt is None:
            raise NotFound("Attempt not found")

        if str(attempt["student_id"]) != str(student_id):
            raise Forbidden("This attempt does not belong to you")

        if attempt["status"] != "submitted":
            raise Forbidden(
                "Answer review is only available after submitting the exam. "
                f"Current status: {attempt['status']}"
            )

        question = await question_repository.fetch_by_id_for_review(db, question_id)
        if question is None:
            raise NotFound(f"Question {question_id} not found")

        return question

    # ── Admin operations ──────────────────────────────────────────────────────

    async def get_admin_question(
        self, db: AsyncSession, question_id: int
    ) -> QuestionAdminSchema:
        """Return full question data for admin panel."""
        question = await question_repository.fetch_by_id_for_admin(db, question_id)
        if question is None:
            raise NotFound(f"Question {question_id} not found")
        return question

    async def update_question(
        self,
        db: AsyncSession,
        question_id: int,
        data: QuestionUpdateRequest,
    ) -> QuestionAdminSchema:
        """
        Partial update on a question. Admin only — router enforces require_admin.
        Uses exclude_unset=True to distinguish unset fields from explicit nulls.
        """
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_admin_question(db, question_id)

        # Validate correct_option range if being updated
        if "correct_option" in updates and updates["correct_option"] not in (1, 2, 3, 4):
            raise BadRequest("correct_option must be 1, 2, 3, or 4")

        updated = await question_repository.update_question(db, question_id, updates)
        if updated is None:
            raise NotFound(f"Question {question_id} not found")

        return await question_repository.fetch_by_id_for_admin(db, question_id)  # type: ignore

    async def delete_question(self, db: AsyncSession, question_id: int) -> None:
        """Hard delete. Super admin only — router enforces require_super_admin."""
        deleted = await question_repository.delete_question(db, question_id)
        if not deleted:
            raise NotFound(f"Question {question_id} not found")

    async def bulk_import(
        self, db: AsyncSession, import_data: BulkImportSchema
    ) -> BulkImportResult:
        """
        Validate and insert questions in bulk.

        Validation steps:
        1. Exam exists (doesn't need to be active for admin import)
        2. Each question passes importer.validate_question_import()
        3. No duplicate question_no within exam
        4. All context_ref indices are valid

        Returns BulkImportResult with inserted count and any per-question errors.
        """
        # Validate exam exists (inactive OK for admin import)
        try:
            await catalog_service.get_exam(db, import_data.exam_id)
        except NotFound:
            raise NotFound(f"Exam {import_data.exam_id} not found")

        # Validate context_ref indices
        max_ctx_idx = len(import_data.contexts) - 1
        validation_errors: list[str] = []

        for q in import_data.questions:
            if q.context_ref is not None and q.context_ref > max_ctx_idx:
                validation_errors.append(
                    f"Q{q.question_no}: context_ref {q.context_ref} is out of range "
                    f"(contexts has {len(import_data.contexts)} entries)"
                )

        # Validate no duplicate question_no within this batch
        seen_q_nos: set[int] = set()
        for q in import_data.questions:
            if q.question_no in seen_q_nos:
                validation_errors.append(
                    f"Duplicate question_no {q.question_no} in import batch"
                )
            seen_q_nos.add(q.question_no)

        # Run per-question validation
        for q in import_data.questions:
            errs = validate_question_import(q)
            validation_errors.extend(errs)

        if validation_errors:
            raise BadRequest(
                f"Import validation failed with {len(validation_errors)} error(s): "
                + "; ".join(validation_errors[:5])
                + (" ..." if len(validation_errors) > 5 else "")
            )

        inserted, errors = await question_repository.bulk_insert(db, import_data)
        return BulkImportResult(
            exam_id=import_data.exam_id,
            inserted=inserted,
            skipped=len(import_data.questions) - inserted,
            errors=errors,
        )


# Module-level singleton — import this in router.py and other modules
question_service = QuestionService()
