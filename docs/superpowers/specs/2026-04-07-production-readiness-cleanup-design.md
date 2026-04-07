# ScholarPath — Production Readiness Cleanup Design
**Date:** 2026-04-07
**Branch strategy:** Approach A — sequential work streams, each as its own PR
**Test policy:** Fix + tests together for every change
**Scope:** 19 targeted fixes across 4 independent work streams

---

## Context

A full production readiness audit of ScholarPath (FastAPI backend + React 18 frontend) identified 89 issues across backend and frontend. After cross-validation to remove false positives, 19 confirmed issues remain. They are grouped into 4 work streams ordered by deployment criticality.

The `is_paid=True` bypass in `access_control.py` is intentionally excluded from this plan — it remains in place for manual QA and will be reverted separately once testing is complete.

---

## Work Stream 1: Deployment Blockers

**Branch:** `fix/deployment-blockers`
**Depends on:** nothing (can start immediately)
**Goal:** Fix everything that prevents the app from working correctly in a production deployment.

### B1 — CORS production URL (`backend/app/main.py` + `backend/app/config.py`)

**Problem:** `allow_origins` is hardcoded to localhost only. All API calls fail from the deployed Vercel frontend.

**Fix:**
- Add `FRONTEND_URL: str = ""` to `Settings` in `config.py`.
- In `main.py`, build `allow_origins` dynamically: start with localhost dev URLs, append `settings.FRONTEND_URL` if non-empty.
- Tighten `allow_methods` from `["*"]` to `["GET", "POST", "PUT", "DELETE", "OPTIONS"]`.
- Tighten `allow_headers` from `["*"]` to `["Content-Type", "Authorization"]`.

**Test:** Unit test that when `FRONTEND_URL=https://scholarpath.vercel.app` is set, the origins list includes that value.

---

### B2 — Payment API endpoint mismatch (`frontend/src/modules/payment/api/paymentApi.js:5`)

**Problem:** `getStatus()` calls `/api/payment/status` (404). Backend exposes `/api/payment/subscription`.

**Fix:** Change the path from `/api/payment/status` to `/api/payment/subscription`.

**Test:** Update the payment store test mock to use the correct path and assert no 404 occurs.

---

### B3 — UpgradePrompt wrong API call (`frontend/src/shared/components/UpgradePrompt.jsx:37`)

**Problem:** Component calls `GET /api/catalog/settings/payment_amount_inr` — this endpoint does not exist, returns 500. The price is already available in `usePaymentStore().plans`.

**Fix:** Remove the API call entirely. Add `usePaymentStore` to the component. In a `useEffect`, call `loadPlans()` if `plans.length === 0` (the component cannot assume plans are pre-loaded — it is used inside `AttemptMistakesDrawer` and `RecentMistakesCard` which are not guaranteed to have payment state loaded). Read price from `plans[0]?.price_inr`. If plans are empty or still loading, show "Upgrade to Premium" without a price figure.

**Test:** Render `UpgradePrompt` with a mocked payment store containing one plan. Assert price renders from store data. Assert no API call is made to any catalog endpoint. Render with empty plans store — assert graceful fallback text renders.

---

### B4 — React Error Boundary (`frontend/src/App.jsx` + new file)

**Problem:** No Error Boundary exists. Any component crash renders a blank white screen with no recovery path.

**Fix:**
- New file: `frontend/src/shared/components/ErrorBoundary.jsx` — React class component implementing `componentDidCatch`. Renders a centered fallback card with a "Reload page" button when an error is caught.
- Wrap the `<Routes>` block in `App.jsx` with `<ErrorBoundary>`.

**Test:** Render a child component that throws synchronously. Assert the fallback UI renders and the error does not propagate to the test runner.

---

### B5 — Mobile sidebar missing (`frontend/src/shared/layouts/AppLayout.jsx`)

**Problem:** Sidebar is `hidden md:flex` on mobile. The mobile header exists but has no hamburger button. Mobile users cannot navigate anywhere.

**Fix:**
- Add `isMobileMenuOpen` useState to `AppLayout`.
- Add a hamburger `☰` icon button to the existing mobile header (`md:hidden` bar).
- On mobile, render the sidebar as a fixed overlay (`fixed inset-0 z-40`) with a semi-transparent backdrop. Controlled by `isMobileMenuOpen`. Clicking a nav link or the backdrop closes it.
- Desktop layout unchanged.

**Test:** Render `AppLayout` at mobile viewport width. Assert sidebar is not visible by default. Simulate hamburger click — assert sidebar is visible. Simulate backdrop click — assert sidebar closes.

---

## Work Stream 2: Parent & Child Module Gaps

**Branch:** `fix/parent-child-module`
**Depends on:** WS1 merged
**Goal:** Fix architecture clarity, pagination performance, and a SQL safety issue in the parent/analysis layer.

### P1 — Parent service architecture clarity (`backend/app/modules/user/`)

**Problem:** `parent_service.py` uses both `parent_repository` (ADR-009, `parent_student_links`) and `child_repository` (ADR-013, `child_profiles`) with no documentation of which methods use which. Additionally, `child_repository` is instantiated inside `ParentService.__init__()` instead of as a module-level singleton, inconsistent with the project pattern.

**Fix:**
- Move `ChildRepository()` instantiation to module level in `child_repository.py`: `child_repository = ChildRepository()`. Import this singleton into `parent_service.py`.
- Remove `self.child_repo = ChildRepository()` from `ParentService.__init__()`.
- Replace **all** `self.child_repo` call sites in `parent_service.py` with the imported module-level `child_repository` singleton. Failure to replace every call site will cause `AttributeError: 'ParentService' object has no attribute 'child_repo'` at runtime.
- Add a docstring block at the top of `parent_service.py` clearly stating: methods using `parent_repository` operate on `parent_student_links` (ADR-009 — linked student accounts); methods using `child_repository` operate on `child_profiles` (ADR-013 — parent-created profiles for unregistered children).
- Update `child_schemas.py` to use Pydantic v2 `model_config = ConfigDict(from_attributes=True)` — it currently uses the old v1 `class Config: from_attributes = True` style (confirmed at line 34).

**Test:** Assert that a service method for a `child_profile_id` request calls `child_repository` methods (not `parent_repository`), and vice versa for `student_id` requests. Use mock repositories to isolate.

---

### P2 — SQL-level pagination for child attempts (`backend/app/modules/user/parent_repository.py` + `parent_service.py`)

**Problem:** `get_child_attempts_paged()` loads up to 200 rows per call and slices in Python. Inefficient and will worsen as attempt counts grow.

**Fix:**
- `parent_repository.get_child_attempts()` already has `limit: int = 20` and already uses `LIMIT :lim` as a bound parameter in SQL — do not re-add these. The only repository change needed is adding `offset: int = 0` parameter and appending `OFFSET :offset` to the existing SQL query.
- Add new repository method `get_child_attempts_count(db, parent_id, student_id) -> int` — runs `SELECT COUNT(*)` with the same WHERE/JOIN clause as `get_child_attempts()`.
- Update `parent_service.get_child_attempts_paged()`: replace the current `get_child_attempts(db, child_id, limit=200)` + Python slice pattern with a call passing `limit=page_size` and `offset=(page-1)*page_size`. Call `get_child_attempts_count()` in the same method. Return: `{"items": [...], "total": n, "page": p, "page_size": s}`.

**Test:** Mock 25 attempt rows. Request page 2 with page_size=10. Assert 10 items returned with `total=25`, `page=2`. Assert the underlying SQL received `LIMIT 10 OFFSET 10`.

---

### P3 — Parameterize LIMIT in wrong answers query (`backend/app/modules/analysis/wrong_answers.py`)

**Problem:** The SQL query uses an f-string to inject the `limit` value: `f"... LIMIT {limit}"`. No runtime type validation — a non-integer value reaching this point is a SQL injection vector.

**Fix:** Add an explicit guard before query construction:
```python
if limit is not None and (not isinstance(limit, int) or limit < 1):
    raise BadRequest("limit must be a positive integer")
```
Keep the f-string interpolation (SQLAlchemy `text()` does not support LIMIT as a bind parameter in PostgreSQL without additional wrapping) — the guard makes it safe since only validated integers reach interpolation.

**Test:** Assert `limit="DROP TABLE users"` raises `BadRequest`. Assert `limit=5` returns at most 5 wrong answer items. Assert `limit=None` returns all wrong answer items (no LIMIT clause is applied when limit is None).

---

## Work Stream 3: Admin Module Polish

**Branch:** `fix/admin-polish`
**Depends on:** WS1 merged (independent of WS2, can run concurrently if needed)
**Goal:** Fix scalability, i18n, and a data validation gap in the admin layer.

### A1 — Dynamic EXAM_OPTIONS (`frontend/src/modules/admin/`)

**Problem:** `QuestionManagerPage`, `StatsPage`, and `ImageUploaderPage` each hardcode `EXAM_OPTIONS = [{id:1,...},{id:2,...}]` (9 total occurrences). Adding a new exam requires editing 3 files manually — violates ADR-011.

**Fix:**
- `adminStore.js` already has `exams: []`, `examsLoading: false`, and `fetchAllExams` action — do not add duplicates. The action name is `fetchAllExams`, not `fetchExams`.
- Remove the local `EXAM_OPTIONS` constant from all 3 pages. Replace with `const { exams, examsLoading, fetchAllExams } = useAdminStore()` + a `useEffect(() => { fetchAllExams() }, [])`.
- The exam selector `<select>` in each page maps over `exams`. Show a skeleton/spinner while `examsLoading` is true. Show "No exams found" if the list is empty.

**Test:** Mock API response with 3 exams. Assert all 3 appear in each page's selector. Assert zero occurrences of hardcoded exam IDs 1 or 2 in the component files.

---

### A2 — i18n in AdminSettingsPage + AdminSubscriptionsPage (`frontend/src/modules/admin/pages/`)

**Problem:** Both pages contain hardcoded English strings throughout — error messages, success toasts, labels, button text. Untranslated.

**Fix:**
- Add keys to `en.json` under `admin.settings.*` and `admin.subscriptions.*` namespaces.
- Add matching keys to `mr.json` — use English text as the Marathi value for now, with a `// TODO: translate` comment in the JSON file header. This prevents broken UI while leaving a clear hook.
- Replace every hardcoded string in both pages with `t('admin.settings.xxx')` or `t('admin.subscriptions.xxx')`.

**Keys to add (representative):**
```
admin.settings.title, admin.settings.loadError, admin.settings.saveSuccess,
admin.settings.pricingConfig, admin.settings.accessDuration
admin.subscriptions.title, admin.subscriptions.grantSuccess,
admin.subscriptions.cancelConfirm, admin.subscriptions.loadError
```

**Test:** Render each page with locale set to `mr`. Assert no raw English string literal appears in the rendered output (all text comes through the i18n layer).

---

### A3 — Validate plan_id in grant_subscription endpoint (`backend/app/modules/admin/router.py`)

**Problem:** `POST /api/admin/subscriptions/grant` (in `backend/app/modules/admin/router.py`) accepts `plan_id` from the request body and passes it directly to the DB insert. The user is identified by email in the body, not a path parameter. Invalid plan_id causes an unhandled PostgreSQL FK violation (500) instead of a clean 400.

**Fix:**
- **Route ordering fix (pre-existing bug):** In `admin/router.py`, the literal route `POST /subscriptions/grant` is currently declared *after* the parametric routes `POST /subscriptions/{sub_id}/cancel` and `POST /subscriptions/{sub_id}/extend`. FastAPI will match `/subscriptions/grant` as `sub_id="grant"` against the earlier parametric routes, making `/subscriptions/grant` unreachable. Move the `@router.post("/subscriptions/grant")` handler to before any `/subscriptions/{sub_id}` routes.
- **Validation fix:** Before the insert, query: `SELECT id FROM payment_plans WHERE id = :plan_id AND is_active = true`. If no row returned, raise `BadRequest("plan_id does not exist or is inactive")`.

**Test:** Call endpoint with `plan_id=9999`. Assert HTTP 400 with readable error message. Call with valid plan_id — assert HTTP 200 and subscription created.

---

### A4 — Remove console.log from PDF export (`frontend/src/modules/analysis/pages/ResultPage.jsx:66`)

**Problem:** `console.log('PDF dimensions:', pdfWidth, 'x', pdfHeight)` is present in production code.

**Fix:** Delete that one line.

**Test:** Covered by existing ResultPage tests. No new test required.

---

## Work Stream 4: Infrastructure & UX Debt

**Branch:** `fix/infrastructure-ux`
**Depends on:** WS1 merged (WS3 not required — no WS4 fix imports anything WS3 creates)
**Goal:** Reliability, security, and UX polish for a production-quality experience.

### I1 — JWKS fetch failure hard-fails on startup (`backend/app/main.py`)

**Problem:** If Supabase JWKS is unreachable at startup, the app prints a warning and continues. ES256 token validation silently fails for all users — nobody can log in, but the server appears healthy.

**Fix:** In the lifespan handler, wrap the JWKS fetch in a retry loop: 3 attempts with 2-second delays. If all retries fail, raise `RuntimeError("Cannot fetch JWKS from Supabase — aborting startup")`. This makes the deploy fail visibly rather than silently serving broken auth.

**Test:** Mock the JWKS endpoint to return 503 for all calls. Assert the app raises `RuntimeError` at startup.

---

### I2 — Rate limiting on sensitive endpoints (`backend/`)

**Problem:** No rate limiting exists. Login brute-force, webhook flooding, and payment abuse are unprotected.

**Fix:**
- Add `slowapi` to `requirements.txt`.
- Configure `Limiter(key_func=get_remote_address)` in `main.py`. Register `_rate_limit_exceeded_handler` for 429 responses.
- Apply per-IP limits to three endpoint groups:
  - `POST /api/users/me/change-password`: 5 requests/minute
  - `POST /api/payment/create-order` + `POST /api/payment/verify`: 10 requests/minute
  - `POST /api/payment/webhook`: 30 requests/minute (Razorpay may batch events)

**Test:** Simulate 6 rapid POST requests to change-password from the same IP. Assert the 6th returns HTTP 429 with a clear error message.

---

### I3 — Session timeout warning (`frontend/`)

**Problem:** Supabase tokens expire (~1 hour). The 401 handler hard-redirects to `/login` with no warning. Admin form edits and other non-autosaved work is lost.

**Fix:**
- New file: `frontend/src/shared/components/SessionExpiryWarning.jsx` — a dismissible banner that appears 5 minutes before token expiry. Reads the JWT `exp` claim from the token in `authStore`. Uses `setTimeout` scheduled at mount and reset on token refresh.
- "Extend session" button calls `supabase.auth.refreshSession()`. On success, banner dismisses and timeout resets. On failure, triggers a graceful logout.
- Mount once inside `AppLayout.jsx`.

**Test:** Mock a token with `exp = now + 4 minutes`. Assert the warning banner renders. Mock successful `refreshSession()` — assert banner disappears and no logout occurs.

---

### I4 — Facebook OAuth button disabled (`frontend/src/modules/auth/pages/LoginPage.jsx`)

**Problem:** Facebook button shows "Coming Soon" badge but is still clickable. Users who click it get a confusing Supabase error.

**Fix:** Add `disabled` attribute and `cursor-not-allowed opacity-50` Tailwind classes to the Facebook button. Add `title="Facebook login coming soon"` tooltip. When Facebook is enabled in Supabase, removing `disabled` is the only code change needed.

**Test:** Assert the Facebook button element has `disabled` attribute. Assert clicking it fires no navigation event or OAuth call.

---

### I5 — Offline detection banner (`frontend/`)

**Problem:** When connectivity is lost, API calls fail silently with network errors. No user feedback.

**Fix:**
- New file: `frontend/src/shared/hooks/useOnlineStatus.js` — subscribes to `window` `online`/`offline` events, returns `{ isOnline: boolean }`.
- New file: `frontend/src/shared/components/OfflineBanner.jsx` — fixed top bar ("You are offline. Some features may not work.") shown when `isOnline` is false. Auto-dismisses when connection restores.
- Mount once in `AppLayout.jsx`.

**Test:** Simulate `window.dispatchEvent(new Event('offline'))`. Assert banner renders. Simulate `online` event — assert banner disappears.

---

### I6 — Consistent loading skeletons (`frontend/src/shared/components/` + admin pages)

**Problem:** `AdminDashboardPage` and `ParentDashboardPage` use skeleton loaders. `StatsPage` and `ImageUploaderPage` use plain spinners. Inconsistent UX.

**Fix:**
- Extract the existing skeleton pattern into two shared components: `SkeletonCard.jsx` and `SkeletonTable.jsx` in `frontend/src/shared/components/`.
- Replace plain spinners in `StatsPage` and `ImageUploaderPage` with `<SkeletonTable />` during loading state.

**Test:** Snapshot tests for `SkeletonCard` and `SkeletonTable`. Render `StatsPage` in loading state — assert `SkeletonTable` renders, not a spinner element.

---

## Summary

| WS | Branch | Fixes | Depends On |
|----|--------|-------|-----------|
| WS1 | `fix/deployment-blockers` | B1–B5 (5 fixes) | — |
| WS2 | `fix/parent-child-module` | P1–P3 (3 fixes) | WS1 |
| WS3 | `fix/admin-polish` | A1–A4 (4 fixes) | WS1 |
| WS4 | `fix/infrastructure-ux` | I1–I6 (6 fixes) | WS1 |

**Total:** 18 fixes (B1 CORS, B2 payment API, B3 UpgradePrompt, B4 ErrorBoundary, B5 mobile nav, P1 architecture clarity, P2 SQL pagination, P3 LIMIT guard, A1 dynamic exams, A2 admin i18n, A3 plan validation, A4 console.log, I1 JWKS hard-fail, I2 rate limiting, I3 session warning, I4 Facebook disabled, I5 offline banner, I6 skeletons)

**Excluded by user request:** `is_paid=True` bypass in `access_control.py` — left in place for manual QA, to be reverted separately.
