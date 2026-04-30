"""
User module router.

Rules:
  - Routers call service only — no business logic here.
  - Auth enforcement via require_* dependencies from auth module public interface.
  - Language header set from profile.preferred_language on responses (ADR-003).
"""

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import limiter
from app.modules.auth.dependencies import UserIdentity, require_parent, verify_token
from app.modules.user.schemas import (
    ChangePasswordRequest,
    CompleteProfileRequest,
    LinkedChildResponse,
    LinkChildRequest,
    ParentStudentLinkResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.modules.user.service import user_service
from app.shared.exceptions import BadRequest

router = APIRouter()

_AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2 MB
_AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's own profile."""
    profile = await user_service.get_my_profile(db, identity.id)
    data = UserProfileResponse.model_validate(profile).model_dump()
    data["email"] = identity.email or None
    return data


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: UpdateProfileRequest,
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Partial update of own profile.
    Only fields present in the request body are changed.
    Also used for onboarding: client sends { is_onboarded: true, ...fields }.
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


@router.post("/me/avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a profile avatar image.
    Max size: 2 MB. Allowed types: JPEG, PNG, WebP.
    Uses MediaService for storage, then updates user_profiles.avatar_url.
    """
    if file.content_type not in _AVATAR_ALLOWED_TYPES:
        raise BadRequest(
            f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP"
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > _AVATAR_MAX_SIZE:
        raise BadRequest("File exceeds 2 MB limit")

    # Reset file position for MediaService
    await file.seek(0)

    # Upload via media module
    from app.modules.media.service import media_service

    result = await media_service.upload_file(
        db=db,
        file=file,
        upload_type="avatar",
        entity_id=0,  # not applicable for avatars
        uploaded_by=str(identity.id),
    )

    # Update profile with new avatar URL
    profile = await user_service.update_avatar(db, identity.id, result["file_url"])
    return profile


@router.post("/me/change-password")
@limiter.limit("10/hour")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    identity: UserIdentity = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for email-authenticated users only.
    Google/Facebook users don't have a password to change here.
    """
    # Check auth provider
    profile = await user_service.get_my_profile(db, identity.id)
    if profile.auth_provider != "email":
        raise BadRequest(
            "Password change is only available for email-authenticated accounts. "
            "Your account uses social login."
        )

    result = await user_service.change_password(identity.id, data)
    return result


@router.get("/me/subscription")
async def get_subscription_status(
    identity: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """
    Convenience endpoint — returns subscription status for the parent.
    Canonical endpoint is GET /api/payment/status. Both are fine to use.
    """
    return await user_service.get_subscription_status(db, identity.id)


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

