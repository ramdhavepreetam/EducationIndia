"""
Attempt module schemas — request/response Pydantic models.

Schema hierarchy:
  StartAttemptRequest    → POST /api/attempts/start (body)
  SaveResponseRequest    → POST /api/attempts/{id}/responses (body)
  ResponseStateItem      → palette state for one question (no correct_option)
  AttemptStateResponse   → full state for resume/start response
  AttemptSummary         → lightweight row for history lists
  AttemptResultResponse  → full score result after submit

SECURITY: AttemptResultResponse has NO correct_option field.
  Correct answers only used server-side in _compute_result_stub().
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class StartAttemptRequest(BaseModel):
    """Body for POST /api/attempts/start."""
    exam_id: int
    child_profile_id: Optional[UUID] = None   # None for direct student flow
    assignment_id: Optional[int] = None


class SaveResponseRequest(BaseModel):
    """
    Body for POST /api/attempts/{id}/responses.
    Called once per question change (autosave). Must be fast — up to 75 calls/exam.
    selected_option=None means the student cleared their answer or just visited.
    """
    question_id: int
    selected_option: Optional[int] = Field(None, ge=1, le=4)
    is_marked_review: bool = False
    time_taken_seconds: Optional[int] = Field(None, ge=0)


# ── Response state item — palette data per question ───────────────────────────

class ResponseStateItem(BaseModel):
    """
    One question's palette state. Returned in AttemptStateResponse.responses.
    Drives the question palette colour coding on the exam UI.
    """
    model_config = ConfigDict(from_attributes=True)

    question_no: int
    question_id: int
    selected_option: Optional[int]
    is_marked_review: bool
    visit_count: int


# ── Attempt state (start + resume) ───────────────────────────────────────────

class AttemptStateResponse(BaseModel):
    """
    Full attempt state returned on:
      - POST /api/attempts/start (new attempt, responses=[])
      - GET  /api/attempts/{id}/state (resume, responses=all saved)

    time_remaining_seconds is computed server-side from started_at + duration.
    Negative value means timer has expired (service auto-transitions to 'expired').
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    exam_id: int
    attempt_number: int
    status: str
    started_at: datetime
    time_remaining_seconds: int
    responses: list[ResponseStateItem] = []


# ── Attempt summary (history) ─────────────────────────────────────────────────

class AttemptSummary(BaseModel):
    """
    Lightweight attempt row for GET /api/attempts/?exam_id=1.
    Only includes summary fields — no JSONB payload.
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    exam_id: int
    attempt_number: int
    status: str
    total_score: Optional[int]
    total_correct: Optional[int]
    total_wrong: Optional[int]
    total_skipped: Optional[int]
    percentage: Optional[float]
    grade: Optional[str]
    started_at: datetime
    submitted_at: Optional[datetime]


# ── Attempt result (post-submit) ──────────────────────────────────────────────

class AttemptResultResponse(BaseModel):
    """
    Full submission result returned by POST /api/attempts/{id}/submit.

    SECURITY: NO correct_option field. JSONB payloads contain aggregate
    stats — section/topic breakdowns — NOT per-question correct answers.
    Those are only available via GET /api/questions/{id}/review (which
    requires status=submitted gate in the question module).
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    exam_id: int
    status: str                       # always "submitted"
    attempt_number: int
    submitted_at: Optional[datetime]

    # Score fields
    total_score: int
    total_correct: int
    total_wrong: int
    total_skipped: int
    percentage: float
    grade: str

    # JSONB analysis (placeholder on Day 7 — full data on Day 9)
    section_scores: list[Any] = []
    topic_scores: list[Any] = []
    time_analysis: dict[str, Any] = {}
    recommendations: list[str] = []
