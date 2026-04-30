"""
Question module router — HTTP layer only. No business logic or DB queries.

Two routers:
  router        → registered at /api/questions  (student-facing delivery)
  admin_router  → registered at /api/admin/questions (admin management)

SECURITY: router endpoints NEVER return correct_option.
          admin_router endpoints require exam_admin or super_admin role.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import (
    UserIdentity,
    require_admin,
    require_super_admin,
    verify_token,
)
from app.modules.question.schemas import (
    BulkImportResult,
    BulkImportSchema,
    QuestionAdminSchema,
    QuestionDeliverySchema,
    QuestionReviewSchema,
    QuestionUpdateRequest,
)
from app.modules.question.service import question_service


# ── Student-facing router ─────────────────────────────────────────────────────

router = APIRouter()


@router.get("/", response_model=list[QuestionDeliverySchema])
async def list_questions(
    exam_id: int = Query(..., description="Exam ID — required"),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    List all questions for an exam in delivery format.
    SECURITY: response NEVER includes correct_option or explanation.
    Returns [] if no questions have been imported yet (exam is valid but empty).
    """
    return await question_service.get_questions_for_exam(db, exam_id)


@router.get("/{question_id}/review", response_model=QuestionReviewSchema)
async def get_question_review(
    question_id: int,
    attempt_id: UUID = Query(..., description="Attempt UUID — must belong to caller"),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Get a question with correct_option and explanation for post-exam review.

    SECURITY GATES:
    - Attempt must belong to the requesting student.
    - Attempt status must be 'submitted' — returns 403 if still ongoing.

    Returns 404 if question or attempt not found.
    Returns 403 if attempt is ongoing or belongs to a different student.
    """
    return await question_service.get_question_for_review(
        db,
        question_id=question_id,
        attempt_id=attempt_id,
        student_id=identity.id,
    )


# ── Admin router ──────────────────────────────────────────────────────────────

admin_router = APIRouter()


@admin_router.get("/", response_model=list[QuestionAdminSchema])
async def list_questions_admin(
    exam_id: int = Query(..., description="Exam ID — required"),
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    List all questions with full admin data (correct_option, hints, stats).
    Requires exam_admin or super_admin role.
    Single efficient query — eager-loads options + context in one round-trip.
    """
    from app.modules.question.repository import question_repository
    from app.modules.question.schemas import OptionReviewSchema, ContextSchema
    from app.modules.question.models import Question, Option, QuestionContext
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result_orm = await db.execute(
        select(Question)
        .options(
            selectinload(Question.options),
            selectinload(Question.context),
        )
        .where(Question.exam_id == exam_id)
        .order_by(Question.question_no)
    )
    questions = result_orm.scalars().all()

    result = []
    for q in questions:
        opts = [
            OptionReviewSchema.model_validate(o, from_attributes=True)
            for o in q.options
        ]
        ctx = (
            ContextSchema.model_validate(q.context, from_attributes=True)
            if q.context else None
        )
        result.append(QuestionAdminSchema(
            id=q.id,
            exam_id=q.exam_id,
            section_id=q.section_id,
            topic_id=q.topic_id,
            context_id=q.context_id,
            question_no=q.question_no,
            question_type=q.question_type,
            text_en=q.text_en,
            text_mr=q.text_mr,
            question_image_url=q.question_image_url,
            question_image_alt_en=q.question_image_alt_en,
            question_image_alt_mr=q.question_image_alt_mr,
            correct_option=q.correct_option,
            correct_options=q.correct_options,
            is_multi_select=q.is_multi_select,
            explanation_en=q.explanation_en,
            explanation_mr=q.explanation_mr,
            hint_en=q.hint_en,
            hint_mr=q.hint_mr,
            marks=q.marks,
            difficulty=q.difficulty,
            tags=q.tags or [],
            attempt_count=q.attempt_count,
            correct_count=q.correct_count,
            actual_difficulty_ratio=float(q.actual_difficulty_ratio) if q.actual_difficulty_ratio else None,
            options=opts,
            context=ctx,
        ))
    return result


@admin_router.put("/{question_id}", response_model=QuestionAdminSchema)
async def update_question(
    question_id: int,
    data: QuestionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Update question text, correct_option, explanation, or difficulty.
    Requires exam_admin or super_admin role.
    Returns 404 if question not found.
    """
    return await question_service.update_question(db, question_id, data)


@admin_router.post("/bulk-import", response_model=BulkImportResult)
async def bulk_import_questions(
    import_data: BulkImportSchema,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Bulk import questions for an exam from JSON payload.
    Validates all questions before inserting — returns 400 if any fail validation.
    Requires exam_admin or super_admin role.

    Example payload:
    {
      "exam_id": 1,
      "contexts": [{"context_type": "paragraph", "content_en": "..."}],
      "questions": [{"question_no": 1, "question_type": "text", ...}]
    }
    """
    return await question_service.bulk_import(db, import_data)


@admin_router.delete("/{question_id}", status_code=204)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_super_admin),
):
    """
    Hard delete a question.
    Requires super_admin role (stricter than exam_admin — irreversible action).
    Returns 404 if question not found.
    """
    await question_service.delete_question(db, question_id)
