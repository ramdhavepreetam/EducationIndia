"""
Auth dependencies — the only public interface of the auth module.

Every other module that needs authentication imports from here:
    from app.modules.auth.dependencies import verify_token, require_role

ADR-001 decision: Supabase issues JWTs; FastAPI only validates them.
  - sub      → user UUID (matches auth.users.id and user_profiles.id)
  - user_profiles.role → trusted app role (student | parent | teacher | exam_admin | super_admin)
  - aud      → "authenticated" (always present in Supabase JWTs)

NEVER issue JWTs here. NEVER call Supabase Auth admin API here.
"""

from typing import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwk, jwt
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.shared.exceptions import Forbidden, Unauthorized

# Points to Supabase JS client login — not an actual FastAPI endpoint.
# auto_error=False so we can return a clean 401 instead of FastAPI's default.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# Valid app roles (must match user_role ENUM in DB — see CLAUDE.md)
VALID_ROLES = frozenset({"student", "parent", "teacher", "exam_admin", "super_admin"})

# ── JWKS cache — populated from Supabase on startup (see main.py lifespan) ──
# Supabase now signs user tokens with ES256 (not HS256).
# We cache the public keys so verify_token doesn't make an HTTP call per request.
_jwks_keys: list[dict] = []


def set_jwks_keys(keys: list[dict]) -> None:
    """Store Supabase JWKS public keys. Called once during app startup."""
    global _jwks_keys
    _jwks_keys = keys


# ── Identity model ────────────────────────────────────────────────────────────

class UserIdentity(BaseModel):
    """
    Extracted from the Supabase JWT on every authenticated request.
    Passed as a dependency argument to route handlers and services.
    """
    id: UUID          # = auth.users.id = user_profiles.id
    role: str         # trusted role loaded from user_profiles.role
    email: str = ""   # from JWT email claim


# ── Core dependency ───────────────────────────────────────────────────────────

async def verify_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserIdentity:
    """
    Validate a Supabase JWT and return the caller's identity.

    Raises 401 if token is missing, expired, tampered, or has no active
    user_profiles row. The JWT proves identity only; authorization role comes
    from user_profiles.role, not user-editable user_metadata.
    """
    if not token:
        raise Unauthorized("Authentication required")

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "ES256":
            # New Supabase projects sign user tokens with ES256 + their private key.
            # Verify using the matching public key from JWKS.
            kid = header.get("kid")
            signing_key = None
            for jwk_entry in _jwks_keys:
                if kid is None or jwk_entry.get("kid") == kid:
                    signing_key = jwk.construct(jwk_entry)
                    break
            if signing_key is None:
                raise Unauthorized("No matching JWKS key — restart the server to refresh keys")
            payload = jwt.decode(
                token, signing_key, algorithms=["ES256"], audience="authenticated"
            )
        else:
            # HS256 — legacy / service tokens signed with the shared secret.
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except JWTError:
        raise Unauthorized("Invalid or expired token")

    user_id_raw: str | None = payload.get("sub")
    if not user_id_raw:
        raise Unauthorized("Invalid token: missing subject")

    try:
        user_id = UUID(user_id_raw)
    except ValueError:
        raise Unauthorized("Invalid token: malformed subject")

    role = await _load_trusted_role(db, user_id)
    if role is None:
        raise Unauthorized("Profile not found or inactive")

    # Guard against unexpected DB values.
    if role not in VALID_ROLES:
        role = "student"

    return UserIdentity(
        id=user_id,
        role=role,
        email=payload.get("email", ""),
    )


async def _load_trusted_role(db: AsyncSession, user_id: UUID) -> str | None:
    """Return the trusted application role from user_profiles."""
    result = await db.execute(
        text(
            "SELECT role::text FROM user_profiles "
            "WHERE id = :uid AND is_active = true"
        ),
        {"uid": str(user_id)},
    )
    return result.scalar_one_or_none()


# ── Role-gating factory ───────────────────────────────────────────────────────

def require_role(*roles: str) -> Callable[..., UserIdentity]:
    """
    Returns a FastAPI dependency that enforces one of the given roles.

    Usage:
        # Single role
        @router.post("/questions")
        async def create_question(
            identity: UserIdentity = Depends(require_role("exam_admin", "super_admin"))
        ):
            ...

        # Convenience aliases are defined below
        @router.get("/admin/users")
        async def list_users(identity: UserIdentity = Depends(require_admin)):
            ...
    """
    role_set = frozenset(roles)

    def dependency(identity: UserIdentity = Depends(verify_token)) -> UserIdentity:
        if identity.role not in role_set:
            raise Forbidden(
                f"Access denied. Required: {', '.join(sorted(role_set))}. "
                f"Your role: {identity.role}"
            )
        return identity

    return dependency


# ── Convenience aliases ───────────────────────────────────────────────────────
# Use these in routers for clarity and to avoid magic strings.

require_student = require_role("student")
require_parent = require_role("parent")
require_teacher = require_role("teacher")
require_admin = require_role("exam_admin", "super_admin")
require_super_admin = require_role("super_admin")
