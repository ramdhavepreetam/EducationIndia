"""
Parent monitoring schemas — data contracts for the parent dashboard.

Lives in the user module because it owns parent_student_links (ADR-009).
No business logic here — pure data shapes.

Multilingual pattern (ADR-003): text fields carry both _en and _mr variants.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Requests ──────────────────────────────────────────────────────────────────

class LinkChildRequest(BaseModel):
    student_email: str


class UpdateLinkNicknameRequest(BaseModel):
    child_nickname: str = Field(..., max_length=50)


# ── Responses ─────────────────────────────────────────────────────────────────

class ChildProfileSchema(BaseModel):
    """
    Child's public profile as seen by a linked parent.
    Populated from UserProfile ORM object + link metadata.
    """
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    full_name: str
    std_class: Optional[int] = None
    medium: Optional[str] = None
    school_name: Optional[str] = None
    district: Optional[str] = None
    avatar_url: Optional[str] = None
    child_nickname: Optional[str] = None
    is_onboarded: bool
    linked_at: datetime


class ChildStatsSchema(BaseModel):
    """Aggregate performance stats across all submitted attempts."""
    total_attempts: int
    avg_percentage: Optional[float] = None
    best_score: Optional[int] = None
    best_percentage: Optional[float] = None
    last_active: Optional[datetime] = None
    exams_completed: int


class ChildAttemptSummarySchema(BaseModel):
    """One row in the parent's view of a child's attempt history."""
    attempt_id: UUID
    exam_title_en: str
    exam_title_mr: Optional[str] = None
    paper_code: str
    attempt_number: int
    status: str
    submitted_at: Optional[datetime] = None
    total_score: Optional[int] = None
    total_marks: int
    percentage: Optional[float] = None
    grade: Optional[str] = None
    duration_seconds: Optional[int] = None


class WeakTopicSchema(BaseModel):
    """
    Per-topic performance aggregated across all of a child's attempts.
    Used for both weak_topics and strong_topics in ChildDetailSchema —
    status field ('weak' | 'average' | 'strong') distinguishes them.
    """
    topic_id: int
    topic_name_en: str
    topic_name_mr: Optional[str] = None
    avg_percentage: float
    status: str           # weak | average | strong
    attempts_count: int


class ChildDetailSchema(BaseModel):
    """Full detail view for one linked child — profile + stats + history."""
    profile: ChildProfileSchema
    stats: ChildStatsSchema
    recent_attempts: list[ChildAttemptSummarySchema]
    weak_topics: list[WeakTopicSchema]
    strong_topics: list[WeakTopicSchema]


class ParentDashboardSchema(BaseModel):
    """Root schema for the parent dashboard page."""
    children: list[ChildProfileSchema]
    selected_child_detail: Optional[ChildDetailSchema] = None
