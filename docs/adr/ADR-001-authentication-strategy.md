# ADR-001: Authentication Strategy

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** auth, user, all modules (consume verify_token)

---

## Context

ScholarPath needs authentication that supports three distinct user types —
students (children age 10-14), parents, and admins — each with different
access patterns. Students and parents expect social login (Google, Facebook)
as a low-friction entry point. The system must also support custom
email/password login for schools or districts without Google accounts.
JWT-based auth is needed for the FastAPI backend to validate requests
independently. We are using Supabase as our database platform.

---

## Decision

We will use Supabase Auth as the primary authentication provider.
Supabase handles Google OAuth, Facebook OAuth, and Email/Password natively.
A PostgreSQL trigger (handle_new_auth_user) auto-creates a user_profiles
row on every new signup regardless of provider. FastAPI validates Supabase
JWTs using the Supabase JWT secret without any additional auth service.

---

## Alternatives Considered

### Option 1: Custom JWT with FastAPI only
Build register/login endpoints, manage passwords, implement OAuth manually.
- Pro: Full control, no external dependency
- Con: Massive implementation burden (OAuth flows are complex and security-critical)
- Con: Article explicitly warns AI should NOT handle security-critical components

### Option 2: Auth0 or Firebase Auth
Third-party auth provider with FastAPI integration.
- Pro: Battle-tested, feature rich
- Con: Additional cost at scale, another vendor dependency
- Con: More complex integration than Supabase which we already use for DB

### Option 3: Supabase Auth ← CHOSEN
Supabase provides auth + database in one platform.
- Pro: Google + Facebook + Email in one dashboard toggle
- Pro: JWT issued by Supabase, verified by FastAPI using shared secret
- Pro: DB trigger auto-creates user_profiles on any signup type
- Pro: RLS policies integrate directly with auth.uid()
- Con: Coupled to Supabase platform (acceptable trade-off at our scale)

---

## Consequences

### Positive
- Social login (Google, Facebook) works with zero backend code — dashboard toggle only
- auth.uid() available in all PostgreSQL RLS policies natively
- One trigger handles all three login providers uniformly
- Parent and student sessions are differentiated by user_profiles.role, not separate auth systems
- No password management, no OAuth flow code to write or maintain

### Negative
- Tightly coupled to Supabase — migrating auth provider later is non-trivial
- FastAPI must validate Supabase JWTs (not issue its own) — slightly different pattern than pure FastAPI auth

### Neutral
- auth.users and user_profiles are separate tables linked by UUID
- The trigger pattern means user_profiles.full_name may initially be email prefix — onboarding flow must prompt for real name

---

## Module Impact

```
auth/dependencies.py   → verify_token() reads Supabase JWT, extracts user_id + role
auth/service.py        → thin wrapper; Supabase handles actual auth operations
auth/router.py         → /api/auth/me only (Supabase handles login/register endpoints)
user/models.py         → user_profiles references auth.users(id) as FK
database migration     → handle_new_auth_user trigger (already in migration SQL)
```

---

## Implementation Notes

FastAPI JWT verification:
```python
from jose import jwt
SUPABASE_JWT_SECRET = settings.SUPABASE_JWT_SECRET

def verify_token(token: str = Depends(oauth2_scheme)) -> UserIdentity:
    payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")
    role = payload.get("role", "student")
    return UserIdentity(id=user_id, role=role)
```

Role in JWT: store role in Supabase user metadata on profile creation.
Frontend: use Supabase JS client for login UI, send JWT to FastAPI for all API calls.

---

## Review Trigger

Revisit if Supabase changes pricing on Auth features, or if we need
multi-tenant auth (different school districts with separate auth domains).
