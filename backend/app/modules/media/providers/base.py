"""
Abstract media provider — swap local ↔ Cloudinary via MEDIA_PROVIDER env var (ADR-007).
"""

from abc import ABC, abstractmethod


class MediaProvider(ABC):

    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        folder: str,
        content_type: str = "image/jpeg",
    ) -> tuple[str, str]:
        """
        Upload a file.
        Returns (storage_key, public_url).
        storage_key — provider-specific path/ID for deletion
        public_url  — URL clients use to load the file
        """
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Delete a file by storage_key. Returns True if deleted."""
        ...
