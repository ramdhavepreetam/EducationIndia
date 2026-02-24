"""
Attempt module router — HTTP layer only. No business logic or DB queries.

All endpoints require authentication (verify_token).
Students can only manipulate their own attempts (service enforces ownership).

Routes:
  POST /api/attempts/start              → start_exam
  GET  /api/attempts/                   → list_student_attempts
  GET  /api/attempts/{attempt_id}/state → get_exam_state (resume)
  POST /api/attempts/{attempt_id}/responses → save_response (autosave)
  POST /api/attempts/{attempt_id}/submit → submit_exam
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, verify_token
from app.modules.attempt.schemas import (
    AttemptResultResponse,
    AttemptStateResponse,
    AttemptSummary,
    ResponseStateItem,
    SaveResponseRequest,
    StartAttemptRequest,
)
from app.modules.attempt.service import attempt_service

router = APIRouter()


@router.post(
    "/start",
    response_model=AttemptStateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new exam attempt",
)
async def start_exam(
    request: StartAttemptRequest,
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Start a new exam attempt for the authenticated student.

    Returns attempt_id and time_remaining_seconds.
    Returns 409 Conflict if the student already has an ongoing attempt for this exam.
    Returns 404 if the exam is not found or not active.
    """
    return await attempt_service.start_exam(db, identity.id, request)


@router.get(
    "/",
    response_model=list[AttemptSummary],
    summary="List student's attempts for an exam",
)
async def list_student_attempts(
    exam_id: int = Query(..., description="Exam ID — required"),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Return all attempts (any status) for the authenticated student + given exam.
    Ordered newest first.
    """
    return await attempt_service.get_student_attempts(db, identity.id, exam_id)


@router.get(
    "/{attempt_id}/state",
    response_model=AttemptStateResponse,
    summary="Restore exam state (resume)",
)
async def get_exam_state(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Return full attempt state for page resume after refresh.

    Includes all saved responses (for question palette re-render) and
    time_remaining_seconds (for timer re-sync).

    If the exam timer expired while the student was away, the attempt is
    automatically transitioned to 'expired' and time_remaining_seconds = 0.

    Returns 404 if attempt not found.
    Returns 403 if attempt belongs to another student.
    """
    return await attempt_service.get_exam_state(db, attempt_id, identity.id)


@router.post(
    "/{attempt_id}/responses",
    response_model=ResponseStateItem,
    summary="Autosave one question response",
)
async def save_response(
    attempt_id: UUID,
    request: SaveResponseRequest,
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Autosave a single question response. Called once per answer change.

    Upserts the response row (INSERT ... ON CONFLICT DO UPDATE).
    Returns current palette state for the question (visit_count, selected_option, etc.)

    Performance target: < 100ms response time.
    Expected call frequency: up to 75 times per exam session.

    Returns 400 if exam timer has expired.
    Returns 403 if attempt is submitted or belongs to another student.
    """
    return await attempt_service.save_response(db, attempt_id, identity.id, request)


@router.post(
    "/{attempt_id}/submit",
    response_model=AttemptResultResponse,
    summary="Submit exam and compute score",
)
async def submit_exam(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    Submit the exam and compute the score immediately (ADR-006).

    Score computation (stub on Day 7, full analysis on Day 9):
      - Counts correct, wrong, skipped answers
      - Stores result as JSONB in attempts table
      - Returns full AttemptResultResponse

    SECURITY: correct_option is read server-side only for scoring.
    It is NEVER included in the response.

    Timer enforcement: 30-second grace period allowed (ADR-005).

    Returns 400 if timer expired beyond grace period.
    Returns 403 if attempt is not ongoing or belongs to another student.
    Returns 409 if attempt is already submitted.
    """
    return await attempt_service.submit_exam(db, attempt_id, identity.id)
