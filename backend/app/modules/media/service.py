"""
Media service — provider-agnostic upload/delete.
Swap providers via MEDIA_PROVIDER env var without code changes (ADR-007).

Allowed types:
  question  → folder: exams/{exam_id}/questions/{question_id}
  option    → folder: options/{option_id}
  avatar    → folder: avatars
"""

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, update as sa_update

from app.config import settings
from app.modules.media.models import MediaFile
from app.modules.media.providers.base import MediaProvider
from app.shared.exceptions import BadRequest


def _get_provider() -> MediaProvider:
    """Factory — selects provider from MEDIA_PROVIDER env var."""
    if settings.MEDIA_PROVIDER == "cloudinary":
        from app.modules.media.providers.cloudinary import CloudinaryProvider
        return CloudinaryProvider()
    if settings.MEDIA_PROVIDER == "r2":
        from app.modules.media.providers.r2 import R2Provider
        return R2Provider()
    from app.modules.media.providers.local import LocalProvider
    return LocalProvider()


_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class MediaService:

    async def upload_file(
        self,
        db: AsyncSession,
        file: UploadFile,
        upload_type: str,
        entity_id: int,
        uploaded_by: str | None = None,
    ) -> dict:
        """
        Upload a file and record it in media_files.

        upload_type: 'question' | 'option' | 'avatar'
        entity_id:   question_id or option_id (unused for avatar)

        Returns dict with file_url and storage_key.
        """
        if file.content_type not in _ALLOWED_CONTENT_TYPES:
            raise BadRequest(f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, GIF, WebP")

        file_bytes = await file.read()
        if len(file_bytes) > _MAX_FILE_SIZE:
            raise BadRequest("File exceeds 5 MB limit")
        self._validate_image_bytes(file_bytes, file.content_type)

        # Look up exam_id for question uploads to build structured folder path
        exam_id: int | None = None
        if upload_type == "question":
            row = (await db.execute(
                text("SELECT exam_id FROM questions WHERE id = :id"),
                {"id": entity_id},
            )).mappings().first()
            exam_id = row["exam_id"] if row else None

        folder = self._folder(upload_type, entity_id, exam_id)
        provider = _get_provider()
        storage_key, public_url = await provider.upload(
            file_bytes=file_bytes,
            filename=file.filename or "image.jpg",
            folder=folder,
            content_type=file.content_type,
        )

        # Persist record
        record = MediaFile(
            uploaded_by=uploaded_by,
            file_type=upload_type,
            original_filename=file.filename or "image.jpg",
            storage_key=storage_key,
            file_url=public_url,
            content_type=file.content_type,
            file_size=len(file_bytes),
        )
        db.add(record)
        await db.flush()

        # Update entity image_url in questions or options table
        await self._update_entity_url(db, upload_type, entity_id, public_url)
        await db.commit()

        return {"id": record.id, "file_url": public_url, "storage_key": storage_key}

    async def delete_file(
        self, db: AsyncSession, media_id: int
    ) -> bool:
        """Soft-delete a media record and remove from provider storage."""
        result = await db.execute(
            text("SELECT id, storage_key FROM media_files WHERE id = :id AND is_active = true"),
            {"id": media_id},
        )
        row = result.mappings().first()
        if not row:
            return False

        provider = _get_provider()
        await provider.delete(row["storage_key"])

        await db.execute(
            text("UPDATE media_files SET is_active = false WHERE id = :id"),
            {"id": media_id},
        )
        await db.commit()
        return True

    def _folder(self, upload_type: str, entity_id: int, exam_id: int | None = None) -> str:
        if upload_type == "question":
            if exam_id:
                return f"exams/{exam_id}/questions/{entity_id}"
            return f"questions/{entity_id}"
        if upload_type == "option":
            return f"options/{entity_id}"
        return "avatars"

    def _validate_image_bytes(self, file_bytes: bytes, content_type: str | None) -> None:
        """Verify the uploaded bytes match the declared image content type."""
        signatures = {
            "image/jpeg": file_bytes.startswith(b"\xff\xd8\xff"),
            "image/jpg": file_bytes.startswith(b"\xff\xd8\xff"),
            "image/png": file_bytes.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/gif": file_bytes.startswith((b"GIF87a", b"GIF89a")),
            "image/webp": (
                len(file_bytes) >= 12
                and file_bytes[:4] == b"RIFF"
                and file_bytes[8:12] == b"WEBP"
            ),
        }
        if not signatures.get(content_type or "", False):
            raise BadRequest("Uploaded file content does not match a supported image format")

    async def _update_entity_url(
        self, db: AsyncSession, upload_type: str, entity_id: int, url: str
    ) -> None:
        """Update image_url on questions or options table after upload."""
        if upload_type == "question":
            await db.execute(
                text("UPDATE questions SET question_image_url = :url WHERE id = :id"),
                {"url": url, "id": entity_id},
            )
        elif upload_type == "option":
            await db.execute(
                text("UPDATE options SET image_url = :url WHERE id = :id"),
                {"url": url, "id": entity_id},
            )


media_service = MediaService()
