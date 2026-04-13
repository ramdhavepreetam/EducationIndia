"""
Admin/Orchestrator module schemas.
Aggregates data from multiple modules for dashboard and admin views.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.catalog.schemas import ExamSummaryResponse
from app.modules.attempt.schemas import AttemptSummary


# ── Admin request bodies (typed — replaces raw body: dict) ───────────────────

class UpdateSettingRequest(BaseModel):
    value: str


class ExtendSubscriptionRequest(BaseModel):
    months: int = Field(ge=1, le=120, description="Number of months to extend (1–120)")


class GrantSubscriptionRequest(BaseModel):
    email: EmailStr
    plan_id: int
    months: int = Field(default=5, ge=1, le=120)


# ── Student dashboard ──────────────────────────────────────────────────────────

class StudentDashboardStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_attempts: int
    avg_percentage: float
    best_score: int
    exams_completed: int


class StudentDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    available_exams: List[ExamSummaryResponse]
    recent_attempts: List[AttemptSummary]
    stats: StudentDashboardStats


# ── Admin overview ─────────────────────────────────────────────────────────────

class AdminOverviewStats(BaseModel):
    total_students: int
    total_attempts: int
    active_exams: int
    total_questions: int


# ── Admin recent attempt row ───────────────────────────────────────────────────

class AdminAttemptRow(BaseModel):
    """Lightweight attempt row for admin recent attempts table."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    student_id: Optional[UUID] = None
    student_name: Optional[str]
    exam_id: int
    exam_title: Optional[str]
    status: str
    total_score: Optional[int]
    percentage: Optional[float]
    grade: Optional[str]
    started_at: Optional[datetime]
    submitted_at: Optional[datetime]


# ── Question stats row ────────────────────────────────────────────────────────

class AdminExamRow(BaseModel):
    """Exam row for admin ExamPublisherPage — includes question count and grade."""
    id: int
    paper_code: str
    set_code: str
    title_en: str
    title_mr: Optional[str]
    is_active: bool
    total_questions: int              # from schema (expected)
    question_count: int               # actual count in questions table
    event_title: Optional[str]
    event_year: Optional[int]
    std_class: Optional[int] = None   # 5 or 8 — for grouping in ExamPublisherPage


class QuestionStatRow(BaseModel):
    """One row from question_stats joined with question_no."""
    question_id: int
    question_no: Optional[int]
    total_attempts: int
    correct_count: int
    wrong_count: int
    skip_count: int
    avg_time_seconds: Optional[float]
    actual_difficulty: Optional[float]
    correct_pct: Optional[float]       # computed: correct_count / total_attempts * 100
