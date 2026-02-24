import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine
from app.modules.auth.dependencies import set_jwks_keys
from app.shared.exceptions import (
    ScholarPathException,
    generic_exception_handler,
    scholarpath_exception_handler,
)

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fetch Supabase JWKS on startup so verify_token can validate ES256 tokens.
    # New Supabase projects sign user JWTs with ES256 (elliptic curve), not HS256.
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            )
            keys = resp.json().get("keys", [])
            set_jwks_keys(keys)
            print(f"[startup] Loaded {len(keys)} Supabase JWKS key(s)")
    except Exception as e:
        print(f"[startup] WARNING: Could not fetch JWKS: {e} — ES256 tokens will fail")

    yield

    # shutdown — release all pooled DB connections
    await engine.dispose()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MSCE Scholarship Exam Preparation Portal — multilingual (EN + MR)",
    lifespan=lifespan,
    # Disable default /docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# In production, replace with the deployed Vercel frontend URL.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (default)
        "http://localhost:5174",   # Vite dev server (fallback port)
        "http://localhost:3000",   # alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ────────────────────────────────────────────────────────

app.add_exception_handler(ScholarPathException, scholarpath_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── Module routers (uncomment as each module is built) ───────────────────────
# Follow ADR-002: each module registers its own router here — one line per module.
#
# from app.modules.auth.router import router as auth_router
from app.modules.user.router import router as user_router
from app.modules.user.parent_router import router as parent_router
from app.modules.catalog.router import router as catalog_router
from app.modules.question.router import router as question_router, admin_router as question_admin_router
from app.modules.attempt.router import router as attempt_router
from app.modules.analysis.router import router as analysis_router
from app.modules.media.router import router as media_router
from app.modules.admin.router import router as admin_router
#
# app.include_router(auth_router,           prefix="/api/auth",            tags=["auth"])
app.include_router(user_router,            prefix="/api/users",           tags=["users"])
app.include_router(parent_router,          prefix="/api/parent",          tags=["parent"])
app.include_router(catalog_router,         prefix="/api/catalog",         tags=["catalog"])
app.include_router(question_router,        prefix="/api/questions",       tags=["questions"])
app.include_router(question_admin_router,  prefix="/api/admin/questions", tags=["admin-questions"])
app.include_router(attempt_router,         prefix="/api/attempts",        tags=["attempts"])
app.include_router(analysis_router,        prefix="/api/analysis",        tags=["analysis"])
app.include_router(media_router,           prefix="/api/media",           tags=["media"])
app.include_router(admin_router,           prefix="/api/admin",           tags=["admin"])

# ── Static file serving (local media provider) ────────────────────────────────
# In production with Cloudinary, this mount is still harmless (empty dir).
_uploads_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
)
os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_uploads_dir), name="static")
