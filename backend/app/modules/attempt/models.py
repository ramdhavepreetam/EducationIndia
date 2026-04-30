"""
Attempt module models — Attempt and Response.

Owns: attempts, responses tables.
Enums use create_type=False — types already exist in DB from migration.

Rules (ADR-005):
  - Status transitions enforced by state_machine.py ONLY.
  - JSONB columns (section_scores etc.) managed by service during submit.
  - question_stats updated by DB trigger — NEVER write from app code.
"""

import enum
from datetime import datetime
from uuid import UUID, uuid4

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
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# ── Python enums — must match PostgreSQL ENUM values exactly ─────────────────

class AttemptStatusEnum(str, enum.Enum):
    ongoing   = "ongoing"
    submitted = "submitted"
    expired   = "expired"
    abandoned = "abandoned"


class AssignmentTypeEnum(str, enum.Enum):
    practice   = "practice"
    assigned   = "assigned"
    mock_test  = "mock_test"


# ── Models ────────────────────────────────────────────────────────────────────

class Attempt(Base):
    """
    One exam attempt by a student. UUID primary key (matches Supabase auth UUIDs).

    State lifecycle (ADR-005):
      not_started → ongoing → submitted | expired | abandoned
      abandoned   → ongoing  (re-open abandoned attempt)

    JSONB columns (section_scores, topic_scores, time_analysis, recommendations):
      Written ONCE during submit() by analysis stub (Day 7) / AnalysisService (Day 9).
      NEVER recomputed after submission (ADR-006).

    score fields are set atomically with status='submitted' in repository.
    """
    __tablename__ = "attempts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    child_profile_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("child_profiles.id", ondelete="SET NULL"),
    )
    student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
    )
    exam_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("exam_assignments.id", ondelete="SET NULL", use_alter=True),
    )
    attempt_number: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    status: Mapped[AttemptStatusEnum] = mapped_column(
        Enum(AttemptStatusEnum, name="attempt_status", create_type=False),
        server_default="ongoing",
        nullable=False,
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_saved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # ── Score summary (written once on submit) ────────────────────────────────
    total_score: Mapped[int | None] = mapped_column(SmallInteger)
    total_correct: Mapped[int | None] = mapped_column(SmallInteger)
    total_wrong: Mapped[int | None] = mapped_column(SmallInteger)
    total_skipped: Mapped[int | None] = mapped_column(SmallInteger)
    percentage: Mapped[float | None] = mapped_column(Numeric(5, 2))
    grade: Mapped[str | None] = mapped_column(Text)

    # ── JSONB analysis (written once on submit) ───────────────────────────────
    section_scores: Mapped[list] = mapped_column(JSONB, server_default="'[]'")
    topic_scores: Mapped[list] = mapped_column(JSONB, server_default="'[]'")
    time_analysis: Mapped[dict] = mapped_column(JSONB, server_default="'{}'")
    recommendations: Mapped[list] = mapped_column(JSONB, server_default="'[]'")

    # ── Audit ─────────────────────────────────────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    responses: Mapped[list["Response"]] = relationship(
        "Response",
        back_populates="attempt",
        order_by="Response.question_no",
        lazy="select",
    )


class Response(Base):
    """
    One question-response row per attempt (upserted on each answer change).

    visit_count tracks how many times the student visited a question
    (used by the exam palette for color coding — ADR-005).

    Palette state (ADR-005):
      visit_count=0, selected=None  → gray    (not visited)
      visit_count>0, selected=None  → white   (visited, unanswered)
      visit_count>0, selected!=None → green   (answered)
      is_marked_review=True, None   → orange  (marked, unanswered)
      is_marked_review=True, set    → purple  (marked + answered)
    """
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    question_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # ── Answer state ──────────────────────────────────────────────────────────
    selected_option: Mapped[int | None] = mapped_column(SmallInteger)  # 1-4 or None
    selected_options: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)    # set on submit
    marks_obtained: Mapped[int] = mapped_column(SmallInteger, server_default="0")

    # ── Timing per question ───────────────────────────────────────────────────
    first_visited_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    time_taken_seconds: Mapped[int | None] = mapped_column(SmallInteger)

    # ── Palette state ─────────────────────────────────────────────────────────
    visit_count: Mapped[int] = mapped_column(Integer, server_default="0")
    is_marked_review: Mapped[bool] = mapped_column(Boolean, server_default="false")

    # Relationships
    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="responses")
