"""
Question module router — HTTP layer only. No business logic or DB queries.

Two routers:
  router        → registered at /api/questions  (student-facing delivery)
  admin_router  → registered at /api/admin/questions (admin management)

SECURITY: router endpoints NEVER return correct_option.
          admin_router endpoints require exam_admin or super_admin role.
"""

from uuid import UUID

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
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
    PdfImportResult,
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
    child_profile_id: UUID | None = Query(
        None,
        description="Child profile UUID for parent-created attempts",
    ),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    List all questions for an exam in delivery format.
    SECURITY: response NEVER includes correct_option or explanation.
    Returns [] if no questions have been imported yet (exam is valid but empty).
    """
    return await question_service.get_questions_for_exam(
        db,
        exam_id,
        user_id=identity.id,
        role=identity.role,
        child_profile_id=child_profile_id,
    )


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
    Single efficient query — service eager-loads options + context.
    """
    return await question_service.list_admin_questions(db, exam_id)


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


@admin_router.post("/pdf-import", response_model=PdfImportResult)
async def import_questions_from_pdf(
    exam_id: int = Form(...),
    mode: Literal["preview", "apply"] = Form("preview"),
    language_strategy: Literal["auto", "bilingual", "english", "marathi"] = Form("auto"),
    answer_set: Literal["A", "B", "C", "D"] = Form("A"),
    english_question_pdf: UploadFile | None = File(None),
    marathi_question_pdf: UploadFile | None = File(None),
    answer_key_pdf: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Import an exam from uploaded PDF question paper(s) plus answer-key PDF.
    Preview mode extracts and validates only. Apply mode replaces this exam's
    question rows after a clean extraction.
    """
    return await question_service.import_questions_from_pdf(
        db,
        exam_id=exam_id,
        mode=mode,
        language_strategy=language_strategy,
        answer_set=answer_set,
        english_question_pdf=await english_question_pdf.read() if english_question_pdf else None,
        marathi_question_pdf=await marathi_question_pdf.read() if marathi_question_pdf else None,
        answer_key_pdf=await answer_key_pdf.read(),
    )


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
