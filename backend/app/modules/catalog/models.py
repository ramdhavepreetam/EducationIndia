"""
Catalog module models — maps exactly to DB schema in CLAUDE.md.

Owns: exam_boards, exam_categories, exam_events, exams, sections, topics
4-level hierarchy (ADR-011): exam_boards → exam_categories → exam_events → exams
Column names MUST match the Supabase migration exactly.
Enums use create_type=False — types already exist in DB from migration.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# ── Python enum — must match PostgreSQL ENUM values exactly ──────────────────

class MediumTypeEnum(str, enum.Enum):
    english      = "english"
    marathi      = "marathi"
    hindi        = "hindi"
    semi_english = "semi_english"


# ── Models — 4-level hierarchy (ADR-011) ─────────────────────────────────────

class ExamBoard(Base):
    """
    Top of the 4-level hierarchy.
    Example: MSCE Maharashtra, CBSE.
    Adding a new board = insert a row; no code change required.
    """
    __tablename__ = "exam_boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_mr: Mapped[str | None] = mapped_column(Text)
    short_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    state: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    categories: Mapped[list["ExamCategory"]] = relationship(
        "ExamCategory", back_populates="board", lazy="select"
    )


class ExamCategory(Base):
    """
    Level 2: Exam categories within a board.
    Example: Pre-Upper Primary Scholarship, Class 10 Board Examination.
    """
    __tablename__ = "exam_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_boards.id", ondelete="CASCADE"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_mr: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_mr: Mapped[str | None] = mapped_column(Text)
    icon_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    board: Mapped["ExamBoard"] = relationship("ExamBoard", back_populates="categories")
    events: Mapped[list["ExamEvent"]] = relationship(
        "ExamEvent", back_populates="category", lazy="select"
    )


class ExamEvent(Base):
    """
    Level 3: A specific year/edition of an exam under a category.
    Example: MSCE 5th Std 2025, MSCE 5th Std 2026.
    Adding a new year = insert one exam_event row + exam rows below it.
    """
    __tablename__ = "exam_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    board_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_boards.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_categories.id", ondelete="CASCADE"), nullable=False
    )
    title_en: Mapped[str] = mapped_column(Text, nullable=False)
    title_mr: Mapped[str | None] = mapped_column(Text)
    std_class: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 5 or 8
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    exam_date: Mapped[date | None] = mapped_column(Date)
    registration_deadline: Mapped[date | None] = mapped_column(Date)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_mr: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    board: Mapped["ExamBoard"] = relationship("ExamBoard")
    category: Mapped["ExamCategory"] = relationship(
        "ExamCategory", back_populates="events"
    )
    exams: Mapped[list["Exam"]] = relationship(
        "Exam", back_populates="event", lazy="select"
    )


class Exam(Base):
    """
    Level 4: A single paper within an exam event.
    Example: Paper I (paper_code=501), Paper II (paper_code=502).
    is_active=False hides from students — admin-controlled publishing.
    """
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_events.id", ondelete="CASCADE"), nullable=False
    )
    paper_code: Mapped[str] = mapped_column(String(10), nullable=False)
    set_code: Mapped[str] = mapped_column(String(5), server_default="A")
    paper_number: Mapped[int | None] = mapped_column(SmallInteger)
    title_en: Mapped[str] = mapped_column(Text, nullable=False)
    title_mr: Mapped[str | None] = mapped_column(Text)
    medium: Mapped[MediumTypeEnum] = mapped_column(
        Enum(MediumTypeEnum, name="medium_type", create_type=False),
        server_default="english",
    )
    total_questions: Mapped[int] = mapped_column(SmallInteger, server_default="75")
    total_marks: Mapped[int] = mapped_column(SmallInteger, server_default="150")
    marks_per_question: Mapped[int] = mapped_column(SmallInteger, server_default="2")
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, server_default="90")
    instructions_en: Mapped[str | None] = mapped_column(Text)
    instructions_mr: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    event: Mapped["ExamEvent"] = relationship("ExamEvent", back_populates="exams")
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="exam", order_by="Section.order_index", lazy="select"
    )


class Section(Base):
    """
    A section within an exam paper.
    Example: Section I (English Q1-25), Section II (Mathematics Q26-75).
    """
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    section_label: Mapped[str] = mapped_column(String(5), nullable=False)  # 'I', 'II'
    subject_en: Mapped[str] = mapped_column(Text, nullable=False)
    subject_mr: Mapped[str | None] = mapped_column(Text)
    question_from: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    question_to: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    order_index: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    color_hex: Mapped[str] = mapped_column(String(7), server_default="#3B82F6")

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="sections")
    topics: Mapped[list["Topic"]] = relationship(
        "Topic", back_populates="section", order_by="Topic.order_index", lazy="select"
    )


class Topic(Base):
    """
    A topic within a section — used for performance analysis (ADR-006).
    Example: Grammar, Fractions, Mirror Images.
    """
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_mr: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_mr: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(SmallInteger, server_default="1")

    # Relationships
    section: Mapped["Section"] = relationship("Section", back_populates="topics")
