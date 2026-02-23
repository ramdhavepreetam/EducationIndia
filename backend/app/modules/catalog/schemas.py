"""
Catalog module schemas — Pydantic v2 request/response models.

All multilingual fields return BOTH language variants (ADR-003).
The frontend decides which language to display; the API never filters.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Topic ─────────────────────────────────────────────────────────────────────

class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section_id: int
    name_en: str
    name_mr: Optional[str]
    description_en: Optional[str]
    description_mr: Optional[str]
    order_index: int


# ── Section ───────────────────────────────────────────────────────────────────

class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    section_label: str
    subject_en: str
    subject_mr: Optional[str]
    question_from: int
    question_to: int
    order_index: int
    color_hex: str
    topics: list[TopicResponse] = []


# ── Exam ──────────────────────────────────────────────────────────────────────

class ExamSummaryResponse(BaseModel):
    """Lightweight exam card — used in listing endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    paper_code: str
    set_code: str
    title_en: str
    title_mr: Optional[str]
    medium: str
    total_questions: int
    total_marks: int
    duration_minutes: int
    is_active: bool


class ExamDetailResponse(BaseModel):
    """Full exam detail — used in GET /api/catalog/exams/{id}."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    paper_code: str
    set_code: str
    paper_number: Optional[int]
    title_en: str
    title_mr: Optional[str]
    medium: str
    total_questions: int
    total_marks: int
    marks_per_question: int
    duration_minutes: int
    instructions_en: Optional[str]
    instructions_mr: Optional[str]
    is_active: bool
    created_at: datetime

    # Nested
    sections: list[SectionResponse] = []


# ── ExamEvent ─────────────────────────────────────────────────────────────────

class ExamEventSummaryResponse(BaseModel):
    """Event with its papers — used inside board listing."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title_en: str
    title_mr: Optional[str]
    std_class: int
    year: int
    exam_date: Optional[date]
    is_active: bool
    exams: list[ExamSummaryResponse] = []


# ── Board ─────────────────────────────────────────────────────────────────────

class BoardResponse(BaseModel):
    """Exam board summary — used in GET /api/catalog/boards."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_en: str
    name_mr: Optional[str]
    short_code: str
    state: Optional[str]
    logo_url: Optional[str]
    is_active: bool


# ── Admin publish ─────────────────────────────────────────────────────────────

class PublishExamResponse(BaseModel):
    """Response after publishing or unpublishing an exam."""
    id: int
    is_active: bool
    message: str
