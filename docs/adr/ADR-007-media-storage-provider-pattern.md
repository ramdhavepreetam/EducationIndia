# ADR-007: Media Storage Provider Pattern

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** media (owns), question (consumes image_url), admin (uploads)

---

## Context

ScholarPath questions include images — Intelligence Test figures, pictographs,
advertisements, and diagrams. These images must be stored, served fast, and
referenced by stable URLs in the database. The requirement differs between
development (local machine, no cloud account needed) and production (fast CDN
delivery to students across Maharashtra). The chosen storage must not require
code changes when switching environments — only configuration.

---

## Decision

We will implement a MediaProvider abstract base class with two concrete
implementations: LocalProvider (saves to /uploads, serves via FastAPI /static)
and CloudinaryProvider (uses Cloudinary free tier: 25GB storage, CDN included).
Selection is via MEDIA_PROVIDER environment variable. Zero code changes between
dev and prod — only .env changes.

---

## Alternatives Considered

### Option 1: Supabase Storage
Store images in Supabase Storage bucket alongside the database.
- Pro: One platform for everything
- Con: Free tier is 1GB — Intelligence Test has many figures, will fill quickly
- Con: No built-in CDN for fast delivery to mobile students

### Option 2: AWS S3 + CloudFront
Industry standard, fast CDN.
- Pro: Extremely reliable, best CDN coverage
- Con: Requires AWS account, IAM setup, CloudFront distribution — complex for free tier
- Con: Cost unpredictable at scale vs. Cloudinary's free tier

### Option 3: Cloudinary + Local fallback via provider pattern ← CHOSEN
- Pro: Cloudinary free tier: 25GB storage + CDN + auto image optimization
- Pro: Provider pattern means dev uses local files — no cloud account for new developers
- Pro: If we want to switch to S3 later, implement S3Provider — zero other changes
- Con: Cloudinary dependency for production

---

## Consequences

### Positive
- New developers clone repo, run locally, no cloud account required
- Production images served via Cloudinary CDN (fast for Maharashtra students on mobile)
- Adding new provider (S3, Supabase) = implement MediaProvider interface only
- Image URLs in DB are always absolute (Cloudinary CDN URL or localhost URL)

### Negative
- Local dev URLs (http://localhost:8000/static/...) break if shared with others
- Cloudinary free tier limits: 25GB storage, 25GB bandwidth/month — monitor this

### Neutral
- media_files table tracks all uploads with provider info
- Admin must be authenticated to upload (role: exam_admin or super_admin only)
- Images are immutable after upload — no update endpoint, only delete + re-upload

---

## Module Impact

```
media/providers/base.py          → Abstract class MediaProvider with upload(), delete()
media/providers/local.py         → Saves to /uploads, returns localhost URL
media/providers/cloudinary.py    → Uses cloudinary SDK, returns CDN URL
media/service.py                 → MediaService(provider=get_provider()) factory
media/router.py                  → POST /api/media/upload (admin only)
config.py                        → MEDIA_PROVIDER env var, CLOUDINARY_URL env var
question/models.py               → question_image_url, option image_url = stable URLs from media module
```

---

## Implementation Notes

Provider interface (media/providers/base.py):
```python
from abc import ABC, abstractmethod

class MediaProvider(ABC):
    @abstractmethod
    async def upload(self, file: bytes, filename: str, folder: str) -> str:
        """Upload file and return its public URL."""
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Delete file by ID/path. Returns True if successful."""
        pass
```

Factory function (media/service.py):
```python
def get_provider() -> MediaProvider:
    provider = settings.MEDIA_PROVIDER
    if provider == "cloudinary":
        return CloudinaryProvider(url=settings.CLOUDINARY_URL)
    return LocalProvider(upload_dir="/uploads", base_url=settings.BASE_URL)
```

Folder structure for uploads:
```
/questions/{exam_id}/          → question body images
/contexts/{exam_id}/           → passage/pictograph context images
/options/{question_id}/        → option images (Intelligence Test)
/avatars/{user_id}/            → user profile photos
```

---

## Review Trigger

Revisit when Cloudinary bandwidth approaches 25GB/month (upgrade to paid
or evaluate S3). Revisit when adding mobile app — may need image resizing
middleware (Cloudinary transformation URLs handle this automatically).
