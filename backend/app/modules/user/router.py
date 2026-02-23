"""
User module router.

Rules:
  - Routers call service only — no business logic here.
  - Auth enforcement via require_* dependencies from auth module public interface.
  - Language header set from profile.preferred_language on responses (ADR-003).
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_parent, verify_token
from app.modules.user.schemas import (
    CompleteProfileRequest,
    LinkedChildResponse,
    LinkChildRequest,
    ParentStudentLinkResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.modules.user.service import user_service

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's own profile."""
    profile = await user_service.get_my_profile(db, identity.id)
    return profile


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: UpdateProfileRequest,
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Partial update of own profile.
    Only fields present in the request body are changed.
    A parent cannot call this on a student's profile — endpoint only
    updates the caller's own profile (identity.id).
    """
    profile = await user_service.update_my_profile(db, identity.id, data)
    return profile


@router.post("/me/complete-profile", response_model=UserProfileResponse)
async def complete_profile(
    data: CompleteProfileRequest,
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Onboarding step — sets school, district, std_class, preferred_language.
    Flips is_onboarded = True on success.
    Students must provide std_class. Parents may omit it.
    """
    profile = await user_service.complete_profile(db, identity.id, data)
    return profile


@router.get("/my-children", response_model=list[LinkedChildResponse])
async def get_my_children(
    identity: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """
    Parent-only. Returns active linked students with link metadata.
    A student calling this endpoint receives 403 (enforced by require_parent).
    Response includes child_nickname from the link + the student's profile.
    """
    links = await user_service.get_my_children(db, identity.id)
    return links


@router.post("/link-child", response_model=ParentStudentLinkResponse, status_code=201)
async def link_child(
    data: LinkChildRequest,
    identity: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """
    Parent self-service linking (ADR-009).
    Parent provides the student's registered email.
    - 404 if email not found or not a student account
    - 400 if email belongs to a non-student
    - 409 if already linked
    - Reactivates an existing inactive link if one exists
    """
    link = await user_service.link_child(db, identity.id, data)
    return link
