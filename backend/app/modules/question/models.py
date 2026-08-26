"""
Question module models — QuestionContext, Question, Option.

Owns: question_contexts, questions, options
Enums use create_type=False — types already exist in DB from migration.

SECURITY (ADR-012):
  Question.correct_option is the security boundary.
  NEVER return this field during active exam delivery.
  Repository.fetch_by_exam_id() queries v_exam_questions view which excludes it.
  QuestionDeliverySchema also excludes it as a belt-and-suspenders measure.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# ── Python enums — must match PostgreSQL ENUM values exactly ─────────────────

class QuestionTypeEnum(str, enum.Enum):
    text          = "text"
    text_image    = "text_image"
    image_only    = "image_only"
    context_text  = "context_text"
    context_image = "context_image"
    marathi_only  = "marathi_only"
    bilingual     = "bilingual"


class DifficultyLevelEnum(str, enum.Enum):
    easy   = "easy"
    medium = "medium"
    hard   = "hard"


class ContextTypeEnum(str, enum.Enum):
    paragraph    = "paragraph"
    poem         = "poem"
    advertisement= "advertisement"
    image        = "image"
    pictograph   = "pictograph"
    instruction  = "instruction"
    venn_diagram = "venn_diagram"
    figure_series= "figure_series"
    table        = "table"
    data_chart   = "data_chart"


# ── Models ────────────────────────────────────────────────────────────────────

class QuestionContext(Base):
    """
    Shared context (passage, poem, image) used by a group of related questions.
    applies_from/applies_to define which question numbers share this context.
    Example: Q27-28 both reference the same venn diagram context.
    """
    __tablename__ = "question_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    context_type: Mapped[ContextTypeEnum] = mapped_column(
        Enum(ContextTypeEnum, name="context_type", create_type=False), nullable=False
    )
    title_en: Mapped[str | None] = mapped_column(Text)
    title_mr: Mapped[str | None] = mapped_column(Text)
    content_en: Mapped[str | None] = mapped_column(Text)    # passage / poem text
    content_mr: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    image_alt_en: Mapped[str | None] = mapped_column(Text)
    image_alt_mr: Mapped[str | None] = mapped_column(Text)
    instruction_en: Mapped[str | None] = mapped_column(Text)   # "Q27-28: Select mirror image..."
    instruction_mr: Mapped[str | None] = mapped_column(Text)
    applies_from: Mapped[int | None] = mapped_column(SmallInteger)  # Q no. range start
    applies_to: Mapped[int | None] = mapped_column(SmallInteger)    # Q no. range end
    order_index: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="context", lazy="select"
    )


class Question(Base):
    """
    Full question row including correct_option and explanations.

    SECURITY: correct_option MUST NOT be sent to frontend during active exam.
      - Use repository.fetch_by_exam_id() which queries v_exam_questions view
      - That view excludes correct_option at the DB level (ADR-012)
      - QuestionDeliverySchema also excludes it at the serialization level
    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=False
    )
    context_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("question_contexts.id", ondelete="SET NULL")
    )
    question_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    question_type: Mapped[QuestionTypeEnum] = mapped_column(
        Enum(QuestionTypeEnum, name="question_type", create_type=False),
        nullable=False,
        server_default="text",
    )
    text_en: Mapped[str | None] = mapped_column(Text)   # NULL for image_only / marathi_only
    text_mr: Mapped[str | None] = mapped_column(Text)   # NULL for english-only questions
    question_image_url: Mapped[str | None] = mapped_column(Text)
    question_image_alt_en: Mapped[str | None] = mapped_column(Text)
    question_image_alt_mr: Mapped[str | None] = mapped_column(Text)

    # ── SECURITY BOUNDARY ────────────────────────────────────────────────────
    is_multi_select: Mapped[bool] = mapped_column(Boolean, server_default="false")
    correct_option: Mapped[int | None] = mapped_column(SmallInteger)
    correct_options: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    is_cancelled: Mapped[bool] = mapped_column(Boolean, server_default="false")
    cancelled_reason: Mapped[str | None] = mapped_column(Text)
    # ^ Never read these fields in exam delivery code paths. See ADR-012.
    # ─────────────────────────────────────────────────────────────────────────

    explanation_en: Mapped[str | None] = mapped_column(Text)  # shown after exam
    explanation_mr: Mapped[str | None] = mapped_column(Text)
    hint_en: Mapped[str | None] = mapped_column(Text)          # practice mode only
    hint_mr: Mapped[str | None] = mapped_column(Text)
    marks: Mapped[int] = mapped_column(SmallInteger, server_default="2")
    difficulty: Mapped[DifficultyLevelEnum] = mapped_column(
        Enum(DifficultyLevelEnum, name="difficulty_level", create_type=False),
        server_default="medium",
    )
    tags: Mapped[list] = mapped_column(ARRAY(Text), server_default="{}")
    attempt_count: Mapped[int] = mapped_column(Integer, server_default="0")
    correct_count: Mapped[int] = mapped_column(Integer, server_default="0")
    actual_difficulty_ratio: Mapped[float | None] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    options: Mapped[list["Option"]] = relationship(
        "Option",
        back_populates="question",
        order_by="Option.option_no",
        lazy="select",
    )
    context: Mapped["QuestionContext | None"] = relationship(
        "QuestionContext", back_populates="questions"
    )


class Option(Base):
    """
    One of four answer options for a question.
    is_correct is maintained by DB trigger (sync_correct_option_trigger).
    NEVER write is_correct from application code.
    """
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    option_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-4
    text_en: Mapped[str | None] = mapped_column(Text)
    text_mr: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    image_alt_en: Mapped[str | None] = mapped_column(Text)
    image_alt_mr: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, server_default="false")
    # ^ Synced by DB trigger — never write from app code

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="options")
