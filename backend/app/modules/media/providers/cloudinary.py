"""
Cloudinary provider — production CDN storage.
Requires CLOUDINARY_URL env var (format: cloudinary://api_key:api_secret@cloud_name).
Install: pip install cloudinary
"""

import cloudinary
import cloudinary.uploader

from app.config import settings
from app.modules.media.providers.base import MediaProvider


class CloudinaryProvider(MediaProvider):

    def __init__(self):
        # Parse CLOUDINARY_URL and configure SDK
        cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        folder: str,
        content_type: str = "image/jpeg",
    ) -> tuple[str, str]:
        """Upload to Cloudinary. Returns (public_id, secure_url)."""
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            public_id=filename,
            resource_type="image",
            overwrite=False,
            unique_filename=True,
        )
        storage_key = result["public_id"]
        public_url = result["secure_url"]
        return storage_key, public_url

    async def delete(self, storage_key: str) -> bool:
        """Delete from Cloudinary by public_id."""
        result = cloudinary.uploader.destroy(storage_key, resource_type="image")
        return result.get("result") == "ok"
