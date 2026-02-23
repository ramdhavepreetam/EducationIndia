# User Module

**Owner:** user module
**Status:** Scaffolded

---

## What This Module Owns

| Table | Description |
|---|---|
| `user_profiles` | Extends `auth.users`. Created by trigger on signup. |
| `parent_student_links` | Authority for parent → student cross-user access. |

---

## Public Interface

Import ONLY from `app.modules.user` (the `__init__.py`), never from internal files.

```python
from app.modules.user import UserService, user_service
```

| Export | Used by |
|---|---|
| `user_service.get_my_profile(db, user_id)` | Any module needing profile data |
| `UserProfile` model | Type hints only — never cross-module DB queries |

---

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/users/me` | Any authenticated | Own profile |
| `PUT` | `/api/users/me` | Any authenticated | Partial update own profile |
| `POST` | `/api/users/me/complete-profile` | Any authenticated | Onboarding — sets `is_onboarded=True` |
| `GET` | `/api/users/my-children` | `parent` role only | List linked students |
| `POST` | `/api/users/link-child` | `parent` role only | Link student by email |

---

## What This Module Consumes

- `app.modules.auth.dependencies` — `verify_token`, `require_parent` (public interface only)
- `app.database` — `get_db` session dependency
- `app.shared.exceptions` — `NotFound`, `BadRequest`, `Conflict`

---

## Module Rules

**Never do this from another module:**
```python
# Wrong — importing module internals
from app.modules.user.repository import user_repository
from app.modules.user.models import UserProfile
```

**Do this instead:**
```python
# Correct — public interface only
from app.modules.user import user_service
profile = await user_service.get_my_profile(db, user_id)
```

---

## Key Business Rules

1. **A user can only update their own profile** — `PUT /me` uses `identity.id`; no endpoint accepts a target user_id.
2. **Parent is READ-ONLY on child data** — `my-children` returns data; there is no endpoint to update a child's profile.
3. **`is_onboarded` is set exactly once** — `complete_profile()` always sets it to `True`; no other method touches it.
4. **`std_class` is required for students** at `complete-profile` time, not at signup.
5. **Inactive links are reactivated** — `link_child()` finds an existing inactive link and reactivates rather than creating a duplicate.
6. **Email lookup crosses schemas** — `auth.users` (Supabase-owned) is queried via raw SQL in `repository.get_user_id_by_email()`. This is the only cross-schema query in this module.

---

## Language (ADR-003)

- Profile fields (`full_name`, `school_name`, etc.) are not bilingual — stored once.
- `preferred_language` is stored per user and drives which language the frontend displays for exam content.
- All profile responses include `preferred_language` so the frontend can apply it globally.

---

## Parent-Student Linking (ADR-009)

Flow: parent provides student's registered email → service validates role = `student` → link created in `parent_student_links`.

RLS in the database enforces the same rule via `parent_can_see_student()` helper function — so even raw DB access is secure.

```
parent_id ──┐
             ├── parent_student_links ──→ student_id
linked_by ──┘
```

To add/remove access: flip `is_active` on the link row (admin panel, not yet exposed).
