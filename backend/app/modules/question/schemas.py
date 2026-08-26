"""
Question module schemas — four distinct schemas with different security levels.

SECURITY HIERARCHY (ADR-012):
  QuestionDeliverySchema  — active exam     — NO correct_option, NO explanation
  QuestionReviewSchema    — after submit     — adds correct_option + explanation
  QuestionAdminSchema     — admin only       — full data including hints + stats
  BulkImportSchema        — import endpoint  — mirrors ADR-004 JSON format

This is the #1 security boundary: if correct_option leaks into QuestionDeliverySchema,
students can cheat. The DB view v_exam_questions provides DB-level enforcement;
this schema provides serialization-level enforcement.
"""

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


# ── Option schemas ────────────────────────────────────────────────────────────

class OptionDeliverySchema(BaseModel):
    """Option shown during active exam. No is_correct field."""
    model_config = ConfigDict(from_attributes=True)

    option_no: int
    text_en: Optional[str]
    text_mr: Optional[str]
    image_url: Optional[str]
    image_alt_en: Optional[str]
    image_alt_mr: Optional[str]


class OptionReviewSchema(OptionDeliverySchema):
    """Option shown after exam submission — includes is_correct."""
    is_correct: bool


# ── Context schema ────────────────────────────────────────────────────────────

class ContextSchema(BaseModel):
    """
    Shared question context (passage, poem, image) shown alongside questions.
    Returned nested inside QuestionDeliverySchema when context_id is set.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    context_type: str
    title_en: Optional[str]
    title_mr: Optional[str]
    content_en: Optional[str]
    content_mr: Optional[str]
    image_url: Optional[str]
    image_alt_en: Optional[str]
    image_alt_mr: Optional[str]
    instruction_en: Optional[str]
    instruction_mr: Optional[str]
    applies_from: Optional[int]
    applies_to: Optional[int]


# ── Delivery schema — SECURITY BOUNDARY ──────────────────────────────────────

class QuestionDeliverySchema(BaseModel):
    """
    Question data for active exam delivery.

    MUST NOT contain: correct_option, explanation_en, explanation_mr, hint_en, hint_mr
    These fields are excluded by design — adding them here breaks ADR-012.

    The repository queries v_exam_questions (DB view) which also excludes these
    fields at the database level — double enforcement.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    section_id: int
    topic_id: int
    context_id: Optional[int]
    question_no: int
    question_type: str
    text_en: Optional[str]
    text_mr: Optional[str]
    question_image_url: Optional[str]
    question_image_alt_en: Optional[str]
    question_image_alt_mr: Optional[str]
    marks: int
    difficulty: str
    tags: list[str]
    is_multi_select: bool

    # Nested
    options: list[OptionDeliverySchema] = []
    context: Optional[ContextSchema] = None


# ── Review schema (post-exam) ─────────────────────────────────────────────────

class QuestionReviewSchema(BaseModel):
    """
    Question data shown after exam submission.
    Adds correct_option and explanation — only returned when attempt.status = 'submitted'.
    Service layer enforces the submitted check before returning this schema.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    section_id: int
    topic_id: int
    context_id: Optional[int]
    question_no: int
    question_type: str
    text_en: Optional[str]
    text_mr: Optional[str]
    question_image_url: Optional[str]
    question_image_alt_en: Optional[str]
    question_image_alt_mr: Optional[str]
    marks: int
    difficulty: str
    tags: list[str]

    # Available post-exam
    correct_option: Optional[int]
    correct_options: Optional[list[int]]
    is_multi_select: bool
    is_cancelled: bool = False
    cancelled_reason: Optional[str] = None
    explanation_en: Optional[str]
    explanation_mr: Optional[str]

    # Nested
    options: list[OptionReviewSchema] = []
    context: Optional[ContextSchema] = None


# ── Admin schema (full data) ──────────────────────────────────────────────────

class QuestionAdminSchema(BaseModel):
    """Full question data for admin panel. Includes hints and performance stats."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    section_id: int
    topic_id: int
    context_id: Optional[int]
    question_no: int
    question_type: str
    text_en: Optional[str]
    text_mr: Optional[str]
    question_image_url: Optional[str]
    question_image_alt_en: Optional[str]
    question_image_alt_mr: Optional[str]
    correct_option: Optional[int]
    correct_options: Optional[list[int]]
    is_multi_select: bool
    is_cancelled: bool = False
    cancelled_reason: Optional[str] = None
    explanation_en: Optional[str]
    explanation_mr: Optional[str]
    hint_en: Optional[str]
    hint_mr: Optional[str]
    marks: int
    difficulty: str
    tags: list[str]
    attempt_count: int
    correct_count: int
    actual_difficulty_ratio: Optional[float]

    options: list[OptionReviewSchema] = []
    context: Optional[ContextSchema] = None


# ── Update request ────────────────────────────────────────────────────────────

class QuestionUpdateRequest(BaseModel):
    """Fields that can be updated via PUT /api/admin/questions/{id}."""
    question_type: Optional[str] = None
    text_en: Optional[str] = None
    text_mr: Optional[str] = None
    question_image_url: Optional[str] = None
    question_image_alt_en: Optional[str] = None
    question_image_alt_mr: Optional[str] = None
    correct_option: Optional[int] = None
    correct_options: Optional[list[int]] = None
    is_multi_select: Optional[bool] = None
    is_cancelled: Optional[bool] = None
    cancelled_reason: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_mr: Optional[str] = None
    hint_en: Optional[str] = None
    hint_mr: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None


# ── Bulk import schemas (ADR-004 JSON format) ─────────────────────────────────

class OptionImportItem(BaseModel):
    """One option in the bulk import JSON."""
    option_no: int                          # 1-4
    text_en: Optional[str] = None
    text_mr: Optional[str] = None
    image_url: Optional[str] = None
    image_alt_en: Optional[str] = None
    image_alt_mr: Optional[str] = None


class ContextImportItem(BaseModel):
    """
    One context entry in the import JSON.
    Referenced by QuestionImportItem.context_ref (0-based index into contexts array).
    """
    context_type: str
    title_en: Optional[str] = None
    title_mr: Optional[str] = None
    content_en: Optional[str] = None
    content_mr: Optional[str] = None
    image_url: Optional[str] = None
    image_alt_en: Optional[str] = None
    image_alt_mr: Optional[str] = None
    instruction_en: Optional[str] = None
    instruction_mr: Optional[str] = None
    applies_from: Optional[int] = None
    applies_to: Optional[int] = None
    order_index: Optional[int] = None


class QuestionImportItem(BaseModel):
    """
    One question in the bulk import JSON.
    context_ref: 0-based index into the top-level contexts array (None = no context).
    """
    section_id: int
    topic_id: int
    question_no: int
    question_type: str
    text_en: Optional[str] = None
    text_mr: Optional[str] = None
    question_image_url: Optional[str] = None
    question_image_alt_en: Optional[str] = None
    question_image_alt_mr: Optional[str] = None
    correct_option: Optional[int] = None
    correct_options: Optional[list[int]] = None
    is_multi_select: bool = False
    is_cancelled: bool = False
    cancelled_reason: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_mr: Optional[str] = None
    hint_en: Optional[str] = None
    hint_mr: Optional[str] = None
    marks: int = 2
    difficulty: str = "medium"
    tags: list[str] = []
    context_ref: Optional[int] = None      # index into contexts array
    options: list[OptionImportItem] = []   # exactly 4 required


class BulkImportSchema(BaseModel):
    """
    Top-level bulk import payload. POST /api/admin/questions/bulk-import.

    Format:
    {
      "exam_id": 1,
      "contexts": [...],   // shared contexts, referenced by index
      "questions": [...]   // questions with context_ref pointing to above
    }
    """
    exam_id: int
    contexts: list[ContextImportItem] = []
    questions: list[QuestionImportItem]


class BulkImportResult(BaseModel):
    """Response from bulk import endpoint."""
    exam_id: int
    inserted: int
    skipped: int
    errors: list[str] = []


class PdfImportPreviewQuestionSchema(BaseModel):
    """One extracted question row from PDF import preview/apply."""
    question_no: int
    question_type: str
    correct_option: Optional[int]
    is_cancelled: bool = False
    cancelled_reason: Optional[str] = None
    text_en: Optional[str] = None
    text_mr: Optional[str] = None
    options_en: list[str] = []
    options_mr: list[str] = []
    warnings: list[str] = []


class PdfImportResult(BaseModel):
    """Response from admin PDF question-paper + answer-key import."""
    exam_id: int
    mode: str
    language_strategy: str
    answer_set: str
    question_count: int
    importable_count: int
    key_count: int
    cancelled_questions: list[int] = []
    warnings: list[str] = []
    errors: list[str] = []
    inserted: int = 0
    skipped: int = 0
    preview: list[PdfImportPreviewQuestionSchema] = []
