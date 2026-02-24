"""
Local filesystem provider — dev/self-hosted environments.
Files saved under backend/uploads/{folder}/{filename}.
Served via FastAPI StaticFiles mount at /static.
"""

import os
import uuid

import aiofiles

from app.config import settings
from app.modules.media.providers.base import MediaProvider

# Uploads directory relative to backend/ root
_UPLOADS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "uploads"
)
_UPLOADS_DIR = os.path.abspath(_UPLOADS_DIR)


class LocalProvider(MediaProvider):

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        folder: str,
        content_type: str = "image/jpeg",
    ) -> tuple[str, str]:
        """Save file to uploads/{folder}/{uuid}_{filename}. Returns (storage_key, url)."""
        # Sanitise filename
        safe_name = filename.replace(" ", "_")
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        folder_path = os.path.join(_UPLOADS_DIR, folder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, unique_name)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

        # storage_key = relative path from uploads root
        storage_key = f"{folder}/{unique_name}"
        # Public URL via /static mount
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        public_url = f"{base_url}/static/{storage_key}"
        return storage_key, public_url

    async def delete(self, storage_key: str) -> bool:
        """Remove file from filesystem. Returns True if deleted, False if not found."""
        file_path = os.path.join(_UPLOADS_DIR, storage_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
