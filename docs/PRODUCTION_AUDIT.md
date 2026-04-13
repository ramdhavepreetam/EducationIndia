# ScholarPath — Production Readiness Audit
**Date:** 2026-04-12  
**Auditor:** Senior Technical Review  
**Scope:** Full backend + frontend codebase review before production deploy

---

## Executive Summary

The codebase is well-structured with strong module boundaries and a clean architecture. The answer-security boundary (v_exam_questions view excluding correct_option) is implemented correctly at both the DB view and Pydantic schema layers. However, **two race conditions** exist that could corrupt payment and exam data, **no rate limiting** exists on financial endpoints, and several production config gaps need to be closed before go-live.

Severity scale: **P0** = Data corruption / financial loss | **P1** = Security / availability | **P2** = Correctness bug | **P3** = Reliability / UX

---

## P0 — Critical (Fix Before Any Production Traffic)

### P0-1: Race Condition on Exam Submission (TOCTOU)
**File:** `backend/app/modules/attempt/service.py:278-306`  
**File:** `backend/app/modules/attempt/repository.py:59-66`

`submit_exam()` reads attempt status via `get_attempt_by_id()` (plain SELECT), then checks status in Python, then calls `transition()` (which issues an UPDATE). Two concurrent submit requests for the same attempt can both read `status = "ongoing"`, both pass `_assert_ongoing()`, both compute scores, and both call `transition()`. Only one UPDATE will "win" in the DB, but both will have computed and returned scores — and `update_attempt_result()` may be called twice, potentially overwriting the first commit's scores.

**Fix:** Use `SELECT ... FOR UPDATE SKIP LOCKED` in the submit path to acquire a row-level lock.

```python
# In attempt/repository.py — add a new method for the submit path:
async def get_attempt_for_submit(self, db: AsyncSession, attempt_id: UUID) -> Attempt | None:
    """SELECT FOR UPDATE — acquires row lock to prevent double-submit race."""
    result = await db.execute(
        select(Attempt)
        .where(Attempt.id == attempt_id)
        .with_for_update(skip_locked=True)
    )
    return result.scalar_one_or_none()
```

Then in `service.submit_exam()`, replace the `_get_owned_attempt()` call with `get_attempt_for_submit()`. If `skip_locked=True` returns `None` (another request has the lock), raise a `Conflict` error telling the client to retry.

---

### P0-2: Payment Double-Activation Race Condition
**File:** `backend/app/modules/payment/service.py:107-134`  
**File:** `backend/app/modules/payment/repository.py:52-73`

`verify_and_activate()` checks `if sub["status"] == "active"` in Python, then calls `activate_subscription()`. Two concurrent POST /payment/verify calls with the same order_id can both read `status = "pending"`, both pass the idempotency check, and both insert into the `payments` table — creating a duplicate payment record. Revenue stats will double-count this customer.

**Fix — two parts:**

1. Add a DB-level unique constraint on `payments.razorpay_payment_id` (DDL migration):
```sql
ALTER TABLE payments ADD CONSTRAINT payments_razorpay_payment_id_key 
    UNIQUE (razorpay_payment_id);
```

2. In `payment/repository.py:create_payment()`, use `INSERT ... ON CONFLICT DO NOTHING` and return the existing row:
```sql
INSERT INTO payments (...) VALUES (...)
ON CONFLICT (razorpay_payment_id) DO NOTHING
RETURNING *
```

Alternatively, use `activate_subscription()` with a conditional UPDATE:
```sql
UPDATE subscriptions SET status = 'active', ...
WHERE id = :sid AND status != 'active'
RETURNING *
```
If the UPDATE returns no rows, it means another request already activated it — return idempotent success.

---

## P1 — High (Fix Before Public Launch)

### P1-1: SECRET_KEY Has Insecure Default Value
**File:** `backend/app/config.py:16`

```python
SECRET_KEY: str = "change-me-in-production-min-32-chars"
```

If this env var is not set, the application silently runs with a publicly-known default signing key. Any token signed with the real key can be forged. This is the most dangerous misconfiguration possible in a JWT-based system.

**Fix:** Remove the default value and add a startup validator:
```python
SECRET_KEY: str  # No default — will raise ValidationError at startup if not set

@model_validator(mode="after")
def validate_secret_key(self):
    if len(self.SECRET_KEY) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return self
```

---

### P1-2: No Rate Limiting on Financial and Auth Endpoints
**Files:** `backend/app/modules/payment/router.py`, `backend/app/modules/user/router.py`

The following endpoints have no rate limiting:
- `POST /api/payment/create-order` — each call creates a Razorpay order (external API cost + abuse potential)
- `POST /api/payment/verify` — brute-force signature guessing
- `POST /api/users/me/change-password` — account takeover vector
- `POST /api/attempts/{id}/responses` — autosave called up to 75 times per exam; unbounded hammering

**Fix:** Add `slowapi` (ASGI-compatible rate limiter backed by Redis or in-memory):
```bash
pip install slowapi
```
```python
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Payment router
@router.post("/create-order")
@limiter.limit("5/minute")
async def create_order(request: Request, ...):
    ...

# Auth
@router.post("/me/change-password")
@limiter.limit("10/hour")
async def change_password(request: Request, ...):
    ...
```

---

### P1-3: Admin Recent Attempts Drops Child-Profile Names
**File:** `backend/app/modules/admin/router.py:164-186`

The recent attempts query joins on `a.student_id`:
```sql
LEFT JOIN user_profiles up ON up.id = a.student_id
```

When attempts are created via the parent-for-child flow, `attempts.student_id` is `NULL` and `child_profile_id` holds the real student. This JOIN returns `student_name = NULL` for all child-profile attempts, making the admin table useless for monitoring that flow.

**Fix:** Use `COALESCE` to join on either column:
```sql
LEFT JOIN user_profiles up ON up.id = COALESCE(a.student_id, a.child_profile_id)
```

---

### P1-4: `months` Parameter in Revenue Endpoint Has No Cap
**File:** `backend/app/modules/admin/router.py:402-410`

```python
@router.get("/payments/monthly")
async def get_monthly_revenue(months: int = 6, ...):
```

An admin (or an attacker with a stolen admin token) can send `?months=100000`, forcing a full table scan on the payments table over an enormous date range. No validation, no cap.

**Fix:**
```python
from fastapi import Query
async def get_monthly_revenue(
    months: int = Query(default=6, ge=1, le=24),
    ...
):
```

---

### P1-5: `get_all_student_attempts` Loads Unbounded Into Memory
**File:** `backend/app/modules/admin/router.py:69`  
**File:** `backend/app/modules/attempt/repository.py` (`get_all_student_attempts`)

The student dashboard endpoint fetches ALL of a student's attempts into memory to compute stats. For a student who has taken many practice exams, this is unbounded memory growth. The recent attempts list (`recent`) then takes only `[:5]` from the result — but all rows were fetched first.

**Fix:** Split into two queries: a `COUNT`/`AVG`/`MAX` aggregate for stats, and a `LIMIT 5 ORDER BY started_at DESC` query for the recent list.

---

## P2 — Medium (Fix Within First Sprint After Launch)

### P2-1: `sub_id: str` in Admin Routes Should Be `UUID`
**File:** `backend/app/modules/admin/router.py:346, 362`

```python
async def extend_subscription(sub_id: str, ...):
async def cancel_subscription(sub_id: str, ...):
```

Path parameters typed as `str` bypass FastAPI's automatic UUID validation. A non-UUID value silently reaches the repository and fails at the DB level with an opaque error instead of a clean 422.

**Fix:** Change both to `sub_id: UUID` — FastAPI will validate and return 422 automatically.

---

### P2-2: `get_payment_history` Is Unbounded
**File:** `backend/app/modules/payment/repository.py:130-141`

No `LIMIT` on the parent's payment history query. As subscriptions renew over years, this grows without bound.

**Fix:** Add `LIMIT 100 OFFSET :offset` and add `page: int = 1` param to the service/router.

---

### P2-3: `get_all_subscriptions_admin` Is Unbounded
**File:** `backend/app/modules/payment/repository.py:167-177`

Admin subscriptions list has no pagination. At 1,000+ customers this becomes a slow full table read.

**Fix:** Add `LIMIT :limit OFFSET :offset` and expose `page`/`limit` query params in the router (same pattern already used in `get_all_payments_admin`).

---

### P2-4: Admin Routes Accept Untyped `body: dict` — No Request Validation
**File:** `backend/app/modules/admin/router.py:308, 347, 426`

Three admin endpoints accept raw `body: dict` instead of typed Pydantic models:
- `update_setting(key, body: dict)` — value is `body.get("value")`
- `extend_subscription(sub_id, body: dict)` — months is `body.get("months", 0)`
- `grant_subscription(body: dict)` — email, plan_id, months all from unvalidated dict

This bypasses FastAPI's automatic request validation entirely. An admin sending `{"months": "banana"}` to the extend endpoint gets an opaque DB error (or worse, a 500) instead of a clean 422. The `grant_subscription` endpoint is the worst case — it calls `payment_repository.find_parent_by_email(db, email)` with a value that could be empty string or missing entirely (it does check, but via `if not email` — not via schema).

**Fix:** Define typed Pydantic schemas for each:
```python
class UpdateSettingRequest(BaseModel):
    value: str

class ExtendSubscriptionRequest(BaseModel):
    months: int = Field(ge=1, le=120)

class GrantSubscriptionRequest(BaseModel):
    email: EmailStr
    plan_id: int
    months: int = Field(default=5, ge=1, le=120)
```

---

### P2-5: `FRONTEND_URL` Defaults to Localhost
**File:** `backend/app/config.py:36`

```python
FRONTEND_URL: str = "http://localhost:5173"
```

If the `FRONTEND_URL` env var is not set in production, the CORS `allow_origins` list will contain `"http://localhost:5173"` and will **not** include the actual production domain. All API calls from the production frontend will fail with CORS errors.

**Fix:** Require the env var explicitly (no default), or add a startup check:
```python
FRONTEND_URL: str  # Must be set. No default.
```
And document this clearly in the deployment checklist.

---

### P2-6: `get_exam_state` Has a Redundant Double-Load of Exam
**File:** `backend/app/modules/attempt/service.py:204-227`

`get_exam_state()` loads the exam twice — once inside the auto-expire check block (lines 208-211) and again unconditionally on line 222. The second load could be eliminated by reusing the `exam` variable from the first block.

**Fix:** Extract exam loading to a single call before the conditional block.

---

## P3 — Low / Polish (Backlog)

### P3-1: `/exams` and `/results` Are Placeholder Routes
**File:** `frontend/src/App.jsx:92-93`

```jsx
<Route path="/exams" element={<GenericPlaceholder title="Exams" />} />
<Route path="/results" element={<GenericPlaceholder title="Results" />} />
```

These routes are visible in the sidebar but show a "coming soon" placeholder. If these are linked anywhere, students will encounter dead ends.

**Fix:** Either remove from the sidebar navigation or implement the catalog browsing module.

---

### P3-2: No Per-Route Error Boundaries in Frontend
**File:** `frontend/src/App.jsx:61`

The single top-level `<ErrorBoundary>` catches all React errors, but a crash in any one route (e.g., a null-dereference in `AdminDashboardPage`) unmounts the entire app and shows a blank error screen.

**Fix:** Wrap each major route group with its own `<ErrorBoundary>` so a crash in Admin doesn't kill the Parent Dashboard.

---

### P3-3: Exam-Taking Routes Are Not Wrapped in `OnboardingGuard`
**File:** `frontend/src/App.jsx:82-84`

```jsx
<Route path="/exam/:examId/start" element={<ExamStartPage />} />
<Route path="/exam/:examId/attempt" element={<ExamPage />} />
<Route path="/exam/submitted/:id" element={<ExamSubmittedPage />} />
```

These routes are under `<ProtectedRoute>` (requires auth) but not under `<OnboardingGuard>`. A freshly registered user who navigates directly to a known exam URL can reach the exam page before completing onboarding, before their `std_class` and `medium` profile fields are set. The API will serve questions but student context fields will be null.

**Fix:** Wrap exam routes in `<OnboardingGuard>` like payment and parent routes.

---

## Implementation Priority Order

| # | Fix | File(s) | Effort |
|---|-----|---------|--------|
| 1 | P0-1: SELECT FOR UPDATE on submit | `attempt/repository.py`, `attempt/service.py` | 1h |
| 2 | P0-2: Unique constraint + ON CONFLICT for payment | `payment/repository.py` + DB migration | 2h |
| 3 | P1-1: Remove SECRET_KEY default + validator | `config.py` | 30m |
| 4 | P1-2: Rate limiting on payment + auth | `main.py`, `payment/router.py`, `user/router.py` | 3h |
| 5 | P1-3: Fix admin attempts JOIN for child_profile | `admin/router.py` | 30m |
| 6 | P1-4: Cap `months` param | `admin/router.py` | 15m |
| 7 | P1-5: Split unbounded student attempts query | `attempt/repository.py`, `admin/router.py` | 1h |
| 8 | P2-1: UUID path params in admin routes | `admin/router.py` | 15m |
| 9 | P2-2/3: Add pagination to payment history + admin subs | `payment/repository.py`, `payment/router.py`, `admin/router.py` | 1h |
| 10 | P2-4: Typed Pydantic schemas for admin body: dict endpoints | `admin/router.py` | 45m |
| 11 | P2-5: Require FRONTEND_URL in config | `config.py` | 15m |
| 12 | P2-6: Deduplicate exam load in `get_exam_state` | `attempt/service.py` | 20m |
| 13 | P3-1: Remove dead placeholder routes | `App.jsx` | 30m |
| 14 | P3-2: Per-route ErrorBoundary | `App.jsx` | 1h |
| 15 | P3-3: OnboardingGuard on exam routes | `App.jsx` | 30m |

**Total estimated effort: ~12 hours of engineering work.**

---

## Documentation Drift (Non-Blocking)

`CLAUDE.md` documents the payment tables as `payment_plans`, `user_subscriptions`, `payment_orders`, `payment_logs`, and `system_settings`. The actual DB tables (as queried in the code) are `subscription_plans`, `subscriptions`, `payments`, and `app_settings`. The code works — the DB clearly has the real names — but the CLAUDE.md schema section is stale. Anyone reading CLAUDE.md to write a new query will use the wrong table names and hit confusing errors.

**Fix:** Update the "DATABASE Schema" section of CLAUDE.md to reflect the actual table names.

---

## What Was Verified as Correct

- `v_exam_questions` view **correctly excludes** `correct_option` at the DB level (confirmed in migration SQL line 3396–3412)
- `QuestionDeliverySchema` **correctly excludes** `correct_option` at the schema level (double enforcement per ADR-012)  
- `generic_exception_handler` does **not** leak stack traces in production (returns generic 500 message)
- Razorpay webhook signature validation fires **before** any state mutation
- `get_db()` session dependency correctly **commits on success, rolls back on exception**
- `_assert_ongoing()` in attempt service correctly prevents modification of non-ongoing attempts
- CORS middleware is correctly configured with `settings.FRONTEND_URL` (will work once env var is set)
- `autoflush=False` on the SQLAlchemy session prevents unintended early writes
