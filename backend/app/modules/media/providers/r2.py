"""
Cloudflare R2 provider — S3-compatible object storage (ADR-007).

Required env vars:
  R2_ACCOUNT_ID        — Cloudflare account ID (from endpoint URL)
  R2_ACCESS_KEY_ID     — R2 API token key ID
  R2_SECRET_ACCESS_KEY — R2 API token secret
  R2_BUCKET_NAME       — bucket name (default: scolarpath)
  R2_PUBLIC_URL        — public base URL incl. bucket, no trailing slash
                         e.g. https://<account_id>.r2.cloudflarestorage.com/scolarpath

Install: pip install aioboto3
"""

import uuid

import aioboto3

from app.config import settings
from app.modules.media.providers.base import MediaProvider


class R2Provider(MediaProvider):

    def __init__(self):
        self._session = aioboto3.Session(
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self._endpoint = (
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        )
        self._bucket = settings.R2_BUCKET_NAME
        self._public_url = settings.R2_PUBLIC_URL.rstrip("/")

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        folder: str,
        content_type: str = "image/jpeg",
    ) -> tuple[str, str]:
        """Upload to R2. Returns (storage_key, public_url)."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = f"{folder}/{uuid.uuid4().hex}.{ext}"

        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint,
        ) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )

        public_url = f"{self._public_url}/{key}"
        return key, public_url

    async def delete(self, storage_key: str) -> bool:
        """Delete from R2 by storage key (S3 object key)."""
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint,
        ) as s3:
            await s3.delete_object(Bucket=self._bucket, Key=storage_key)
        return True
