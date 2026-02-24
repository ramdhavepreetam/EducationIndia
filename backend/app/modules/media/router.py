"""
Media module router — POST /api/media/upload

Accepts multipart/form-data with:
  file        → image file
  upload_type → 'question' | 'option' | 'avatar'
  entity_id   → question_id or option_id (required for question/option types)

Auth: exam_admin or super_admin only (students cannot upload question images).
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_admin
from app.modules.media.service import media_service
from app.shared.exceptions import BadRequest

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(..., description="question | option | avatar"),
    entity_id: int = Form(0, description="question_id or option_id (0 for avatar)"),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(require_admin),
):
    """
    Upload an image file and associate it with a question or option.
    Returns the public URL of the uploaded file.

    upload_type:
      question → updates questions.question_image_url
      option   → updates options.image_url
      avatar   → no entity update (future: user avatar)
    """
    if upload_type not in ("question", "option", "avatar"):
        raise BadRequest("upload_type must be 'question', 'option', or 'avatar'")
    if upload_type in ("question", "option") and entity_id == 0:
        raise BadRequest("entity_id is required for question/option uploads")

    result = await media_service.upload_file(
        db=db,
        file=file,
        upload_type=upload_type,
        entity_id=entity_id,
        uploaded_by=str(identity.id),
    )
    return result


@router.delete("/{media_id}", status_code=204)
async def delete_file(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Delete a media record (soft delete) and remove from storage."""
    await media_service.delete_file(db, media_id)
