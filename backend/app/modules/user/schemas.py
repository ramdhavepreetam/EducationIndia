"""
User module Pydantic schemas.

ADR-003 rule: return BOTH _en and _mr fields — frontend decides which to display.
For user_profiles, fields like full_name/school_name are not bilingual, so this
module just returns everything and lets the frontend use preferred_language.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# ── Response schemas ──────────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    """Full profile — returned for GET /me and POST /me/complete-profile."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    role: str
    avatar_url: str | None
    phone: str | None
    preferred_language: str
    std_class: int | None
    medium: str | None
    school_name: str | None
    district: str | None
    state: str
    date_of_birth: date | None
    auth_provider: str
    is_active: bool
    is_onboarded: bool
    subscription_tier: str
    created_at: datetime
    updated_at: datetime


class ChildProfileResponse(BaseModel):
    """
    Limited student profile returned to parents — READ-ONLY (ADR-009).
    Excludes sensitive fields like date_of_birth, subscription info.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    std_class: int | None
    medium: str | None
    school_name: str | None
    district: str | None
    state: str
    is_onboarded: bool
    preferred_language: str


class LinkedChildResponse(BaseModel):
    """
    Returned for GET /my-children.
    Combines link metadata (child_nickname, linked_at) + student profile.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int                    # parent_student_links.id
    child_nickname: str | None
    linked_at: datetime
    student: ChildProfileResponse


class ParentStudentLinkResponse(BaseModel):
    """Returned for POST /link-child."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: UUID
    student_id: UUID
    child_nickname: str | None
    linked_at: datetime
    is_active: bool


# ── Request schemas ───────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    """
    PUT /me — partial update. Only fields included in the request are updated.
    Uses exclude_unset=True in service so absent fields are not touched.
    NOT updatable: role, is_active, subscription_*, auth_provider.

    is_onboarded can be set to True here — onboarding completion sends
    { is_onboarded: true, ...other fields } through this same endpoint.
    """
    model_config = ConfigDict(extra="ignore")

    full_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = None
    school_name: str | None = Field(None, max_length=200)
    district: str | None = Field(None, max_length=100)
    state: str | None = None
    date_of_birth: date | None = None
    preferred_language: str | None = Field(
        None,
        pattern="^(en|mr|hi)$",
        description="Language code: en, mr, or hi",
    )
    medium: str | None = Field(
        None,
        pattern="^(english|marathi|hindi|semi_english)$",
    )
    std_class: int | None = Field(None, ge=1, le=12)
    is_onboarded: bool | None = None


class CompleteProfileRequest(BaseModel):
    """
    POST /me/complete-profile — onboarding step.
    Sets is_onboarded = True.
    std_class is required for students; ignored for parents.
    """
    school_name: str
    district: str
    preferred_language: str = Field(default="en", pattern="^(en|mr|hi)$")
    std_class: int | None = Field(
        None,
        ge=5,
        le=8,
        description="Required for students. Must be 5 or 8.",
    )
    medium: str | None = Field(
        None,
        pattern="^(english|marathi|hindi|semi_english)$",
    )
    date_of_birth: date | None = None


class LinkChildRequest(BaseModel):
    """
    POST /link-child — parent self-service linking (ADR-009 Option B).
    Parent provides the student's registered email.
    Service validates the email belongs to a student-role account.
    """
    email: EmailStr
    child_nickname: str | None = Field(
        None,
        max_length=100,
        description="Optional nickname shown in parent dashboard",
    )


class ChangePasswordRequest(BaseModel):
    """
    POST /me/change-password — only for auth_provider='email' users.
    Google/Facebook users don't have a password to change here.
    """
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
