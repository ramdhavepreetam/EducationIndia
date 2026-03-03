"""
User module models — maps exactly to DB schema in CLAUDE.md.

Owns: user_profiles, parent_student_links
Column names MUST match the Supabase migration exactly.
Enums use create_type=False — types already exist in DB from migration.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# ── Python enums — must match PostgreSQL ENUM values exactly ─────────────────

class UserRoleEnum(str, enum.Enum):
    student     = "student"
    parent      = "parent"
    teacher     = "teacher"
    exam_admin  = "exam_admin"
    super_admin = "super_admin"


class MediumTypeEnum(str, enum.Enum):
    english      = "english"
    marathi      = "marathi"
    hindi        = "hindi"
    semi_english = "semi_english"


# ── Models ────────────────────────────────────────────────────────────────────

class UserProfile(Base):
    """
    Extends auth.users — created automatically by on_auth_user_created trigger.
    id is a UUID FK to auth.users(id), not a generated key.
    """
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(
        Enum(UserRoleEnum, name="user_role", create_type=False),
        nullable=False,
        server_default="student",
    )
    avatar_url: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)

    # Drives default language in API responses (ADR-003)
    preferred_language: Mapped[str] = mapped_column(
        String(5), nullable=False, server_default="en"
    )

    # Student-specific (NULL for parents/admins — not enforced at DB level)
    std_class: Mapped[int | None] = mapped_column(SmallInteger)
    medium: Mapped[MediumTypeEnum | None] = mapped_column(
        Enum(MediumTypeEnum, name="medium_type", create_type=False)
    )
    school_name: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, server_default="Maharashtra")
    date_of_birth: Mapped[date | None] = mapped_column(Date)

    auth_provider: Mapped[str] = mapped_column(Text, server_default="email")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    is_onboarded: Mapped[bool] = mapped_column(Boolean, server_default="false")
    subscription_tier: Mapped[str] = mapped_column(String(20), server_default="free")
    subscription_expiry: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    parent_links: Mapped[list["ParentStudentLink"]] = relationship(
        "ParentStudentLink",
        foreign_keys="[ParentStudentLink.parent_id]",
        back_populates="parent",
        lazy="select",
    )
    student_links: Mapped[list["ParentStudentLink"]] = relationship(
        "ParentStudentLink",
        foreign_keys="[ParentStudentLink.student_id]",
        back_populates="student",
        lazy="select",
    )


class ParentStudentLink(Base):
    """
    Authority table for parent → student cross-user data access (ADR-009).
    RLS uses parent_can_see_student() helper which queries this table.
    is_active=False deactivates access without deleting history.
    """
    __tablename__ = "parent_student_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_nickname: Mapped[str | None] = mapped_column(Text)
    linked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id")
    )
    linked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    # Relationships
    parent: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[parent_id],
        back_populates="parent_links",
    )
    student: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[student_id],
        back_populates="student_links",
    )


class ChildProfile(Base):
    """
    Replaces parent_student_links (ADR-013).
    A lightweight profile owned by a parent. No login credentials.
    """
    __tablename__ = "child_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    std_class: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    medium: Mapped[MediumTypeEnum | None] = mapped_column(
        Enum(MediumTypeEnum, name="medium_type", create_type=False),
        server_default="english",
    )
    school_name: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    avatar_color: Mapped[str] = mapped_column(
        String(7), server_default="#3B82F6"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    parent: Mapped["UserProfile"] = relationship(
        "UserProfile", foreign_keys=[parent_id]
    )
