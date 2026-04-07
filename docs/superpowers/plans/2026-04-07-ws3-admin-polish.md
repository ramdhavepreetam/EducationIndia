# WS3: Admin Module Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 issues in the admin layer: dynamic exam list (kill hardcoded IDs), i18n for two admin pages, a backend route ordering + plan validation fix, and a console.log removal.

**Architecture:** Mostly frontend. One backend fix (A3). Frontend tests use vitest (set up in WS1). Each fix is one commit on branch `fix/admin-polish`.

**Tech Stack:** React 18 + Zustand + react-i18next (frontend), FastAPI + SQLAlchemy (backend), pytest (backend), vitest + @testing-library/react (frontend).

**Spec:** `docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md` — fixes A1–A4.

**Prerequisite:** WS1 merged (vitest must be installed). Check out from updated main:
```bash
git checkout main && git pull && git checkout -b fix/admin-polish
```

**Backend test command:**
```bash
DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/admin/ -v --tb=short
```

**Frontend test command:**
```bash
cd frontend && npm test
```

---

## Task 1: A1 — Dynamic EXAM_OPTIONS (kill hardcoded IDs)

**Problem:** `QuestionManagerPage`, `StatsPage`, and `ImageUploaderPage` each define a hardcoded `EXAM_OPTIONS` constant. Adding a new exam requires editing 3 files. The admin store already has `exams`, `examsLoading`, and `fetchAllExams` — pages just need to use them.

**Files:**
- Modify: `frontend/src/modules/admin/pages/QuestionManagerPage.jsx`
- Modify: `frontend/src/modules/admin/pages/StatsPage.jsx`
- Modify: `frontend/src/modules/admin/pages/ImageUploaderPage.jsx`
- Create: `frontend/src/modules/admin/pages/QuestionManagerPage.test.jsx`

- [ ] **Step 1: Read all 3 pages and the admin store**

  Read in full:
  - `frontend/src/modules/admin/pages/QuestionManagerPage.jsx`
  - `frontend/src/modules/admin/pages/StatsPage.jsx`
  - `frontend/src/modules/admin/pages/ImageUploaderPage.jsx`
  - `frontend/src/modules/admin/store/adminStore.js` (confirm `fetchAllExams` and `exams` exist)

- [ ] **Step 2: Write the failing test**

  Create `frontend/src/modules/admin/pages/QuestionManagerPage.test.jsx`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { render, screen } from '@testing-library/react'
  import { MemoryRouter } from 'react-router-dom'

  const mockFetchAllExams = vi.fn()

  vi.mock('@/modules/admin/store/adminStore', () => ({
    useAdminStore: () => ({
      exams: [
        { id: 1, title_en: 'Paper I (501)', paper_code: '501' },
        { id: 2, title_en: 'Paper II (502)', paper_code: '502' },
        { id: 3, title_en: 'Paper III (503)', paper_code: '503' },
      ],
      examsLoading: false,
      fetchAllExams: mockFetchAllExams,
      questions: [],
      questionsLoading: false,
      fetchQuestions: vi.fn(),
    }),
  }))

  describe('QuestionManagerPage', () => {
    it('renders all 3 exams from the store in the selector', async () => {
      const { default: QuestionManagerPage } = await import('./QuestionManagerPage')
      render(<MemoryRouter><QuestionManagerPage /></MemoryRouter>)

      // All 3 exams should appear in the dropdown
      expect(screen.getByText('Paper I (501)')).toBeTruthy()
      expect(screen.getByText('Paper II (502)')).toBeTruthy()
      expect(screen.getByText('Paper III (503)')).toBeTruthy()
    })

    it('calls fetchAllExams on mount', async () => {
      const { default: QuestionManagerPage } = await import('./QuestionManagerPage')
      render(<MemoryRouter><QuestionManagerPage /></MemoryRouter>)
      expect(mockFetchAllExams).toHaveBeenCalled()
    })
  })
  ```

- [ ] **Step 3: Run test to verify it fails**

  ```bash
  cd frontend && npm test src/modules/admin/pages/QuestionManagerPage.test.jsx
  ```
  Expected: `FAILED` — only 2 exams rendered (hardcoded), `fetchAllExams` not called.

- [ ] **Step 4: Update QuestionManagerPage.jsx**

  1. Remove: `const EXAM_OPTIONS = [...]` constant (all lines).
  2. Add to the `useAdminStore()` destructure: `exams, examsLoading, fetchAllExams`.
  3. Add effect: `useEffect(() => { fetchAllExams() }, [])`.
  4. In the exam `<select>`:
     - Replace `{EXAM_OPTIONS.map(...)}` with `{exams.map(ex => <option key={ex.id} value={ex.id}>{ex.title_en}</option>)}`.
     - If `examsLoading`, show `<option disabled>Loading exams...</option>` as the only option.

- [ ] **Step 5: Update StatsPage.jsx — same pattern**

  1. Remove `const EXAM_OPTIONS = [...]`.
  2. Add `exams, examsLoading, fetchAllExams` to `useAdminStore()` destructure.
  3. Add `useEffect(() => { fetchAllExams() }, [])`.
  4. Replace the hardcoded map with `exams.map(...)`.

- [ ] **Step 6: Update ImageUploaderPage.jsx — same pattern**

  Same 4 steps as StatsPage.

- [ ] **Step 7: Verify no hardcoded exam IDs remain**

  ```bash
  grep -rn "id: 1\|id: 2\|Paper I\|Paper II\|501\|502" frontend/src/modules/admin/pages/QuestionManagerPage.jsx frontend/src/modules/admin/pages/StatsPage.jsx frontend/src/modules/admin/pages/ImageUploaderPage.jsx
  ```
  Expected: No matches (zero hardcoded exam IDs).

- [ ] **Step 8: Run tests**

  ```bash
  cd frontend && npm test src/modules/admin/pages/QuestionManagerPage.test.jsx
  ```
  Expected: `2 passed`

- [ ] **Step 9: Commit**

  ```bash
  cd ..
  git add frontend/src/modules/admin/pages/QuestionManagerPage.jsx \
          frontend/src/modules/admin/pages/StatsPage.jsx \
          frontend/src/modules/admin/pages/ImageUploaderPage.jsx \
          frontend/src/modules/admin/pages/QuestionManagerPage.test.jsx
  git commit -m "fix: replace hardcoded EXAM_OPTIONS with dynamic exams from admin store"
  ```

---

## Task 2: A2 — i18n for AdminSettingsPage + AdminSubscriptionsPage

**Problem:** Both admin pages have hardcoded English strings. Not translated. The Marathi locale will use English text as a placeholder for now.

**Files:**
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/locales/mr.json`
- Modify: `frontend/src/modules/admin/pages/AdminSettingsPage.jsx`
- Modify: `frontend/src/modules/admin/pages/AdminSubscriptionsPage.jsx`
- Create: `frontend/src/modules/admin/pages/AdminSettingsPage.test.jsx`

- [ ] **Step 1: Read both pages**

  Read `AdminSettingsPage.jsx` and `AdminSubscriptionsPage.jsx` in full. List every hardcoded string that faces users (labels, error messages, success toasts, button text, section headings).

- [ ] **Step 2: Write the failing test**

  Create `frontend/src/modules/admin/pages/AdminSettingsPage.test.jsx`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { render, screen } from '@testing-library/react'
  import { MemoryRouter } from 'react-router-dom'
  import i18n from '@/config/i18n'

  vi.mock('@/modules/admin/store/adminStore', () => ({
    useAdminStore: () => ({
      settings: { payment_amount_inr: '49900', access_duration_months: '6' },
      settingsLoading: false,
      fetchSettings: vi.fn(),
      updateSetting: vi.fn(),
    }),
  }))

  describe('AdminSettingsPage i18n', () => {
    it('renders page title through i18n (not hardcoded English)', async () => {
      // Switch to Marathi
      await i18n.changeLanguage('mr')
      const { default: AdminSettingsPage } = await import('./AdminSettingsPage')
      render(<MemoryRouter><AdminSettingsPage /></MemoryRouter>)

      // If the title is hardcoded, it will always show English.
      // If it goes through t(), it will use the mr locale key.
      // We check that the rendered title matches the mr.json value, not raw English.
      const mrTitle = i18n.t('admin.settings.title')
      expect(mrTitle).not.toBe('admin.settings.title') // key must exist
    })

    afterEach(async () => {
      await i18n.changeLanguage('en')
    })
  })
  ```

- [ ] **Step 3: Run test to verify it fails**

  ```bash
  cd frontend && npm test src/modules/admin/pages/AdminSettingsPage.test.jsx
  ```
  Expected: `FAILED` — key `admin.settings.title` falls back to the key string itself (not found).

- [ ] **Step 4: Add keys to en.json**

  In `frontend/src/locales/en.json`, add under the `"admin"` namespace (create it if absent):

  ```json
  "admin": {
    "settings": {
      "title": "System Settings",
      "loadError": "Failed to load settings",
      "saveSuccess": "Setting updated successfully",
      "saveFailed": "Failed to update setting",
      "pricingConfig": "Pricing Configuration",
      "paymentAmount": "Subscription Price (paise)",
      "accessDuration": "Access Duration (months)",
      "save": "Save"
    },
    "subscriptions": {
      "title": "Subscription Management",
      "loadError": "Failed to load subscriptions",
      "grantTitle": "Grant Subscription",
      "grantEmail": "Parent Email",
      "grantPlan": "Plan ID",
      "grantMonths": "Months",
      "grantButton": "Grant Access",
      "grantSuccess": "Subscription granted successfully",
      "grantFailed": "Failed to grant subscription",
      "cancelConfirm": "Cancel this subscription?",
      "cancelSuccess": "Subscription cancelled",
      "cancelFailed": "Failed to cancel subscription",
      "noSubscriptions": "No subscriptions found"
    }
  }
  ```

- [ ] **Step 5: Add same keys to mr.json**

  In `frontend/src/locales/mr.json`, add the identical structure with the same English values for now:

  ```json
  "admin": {
    "settings": {
      "title": "System Settings",
      "loadError": "Failed to load settings",
      "saveSuccess": "Setting updated successfully",
      "saveFailed": "Failed to update setting",
      "pricingConfig": "Pricing Configuration",
      "paymentAmount": "Subscription Price (paise)",
      "accessDuration": "Access Duration (months)",
      "save": "Save"
    },
    "subscriptions": {
      "title": "Subscription Management",
      "loadError": "Failed to load subscriptions",
      "grantTitle": "Grant Subscription",
      "grantEmail": "Parent Email",
      "grantPlan": "Plan ID",
      "grantMonths": "Months",
      "grantButton": "Grant Access",
      "grantSuccess": "Subscription granted successfully",
      "grantFailed": "Failed to grant subscription",
      "cancelConfirm": "Cancel this subscription?",
      "cancelSuccess": "Subscription cancelled",
      "cancelFailed": "Failed to cancel subscription",
      "noSubscriptions": "No subscriptions found"
    }
  }
  ```

- [ ] **Step 6: Update AdminSettingsPage.jsx**

  1. Add `const { t } = useTranslation()` (import `useTranslation` from `react-i18next`).
  2. Replace every hardcoded user-facing string with the corresponding `t('admin.settings.xxx')` call.
  3. Example replacements:
     - `"System Settings"` → `t('admin.settings.title')`
     - `"Failed to load settings"` → `t('admin.settings.loadError')`
     - `"Setting X updated successfully"` → `t('admin.settings.saveSuccess')`
     - `"Save"` buttons → `t('admin.settings.save')`

- [ ] **Step 7: Update AdminSubscriptionsPage.jsx — same pattern**

  1. Add `const { t } = useTranslation()`.
  2. Replace all hardcoded strings with `t('admin.subscriptions.xxx')` calls.

- [ ] **Step 8: Run tests**

  ```bash
  cd frontend && npm test src/modules/admin/pages/AdminSettingsPage.test.jsx
  ```
  Expected: `1 passed`

- [ ] **Step 9: Commit**

  ```bash
  cd ..
  git add frontend/src/locales/en.json \
          frontend/src/locales/mr.json \
          frontend/src/modules/admin/pages/AdminSettingsPage.jsx \
          frontend/src/modules/admin/pages/AdminSubscriptionsPage.jsx \
          frontend/src/modules/admin/pages/AdminSettingsPage.test.jsx
  git commit -m "fix: add i18n to AdminSettingsPage and AdminSubscriptionsPage"
  ```

---

## Task 3: A3 — Route ordering fix + plan_id validation

**Problem (two parts):**
1. In `admin/router.py`, the literal route `POST /subscriptions/grant` is declared *after* the parametric routes `POST /subscriptions/{sub_id}/extend` and `POST /subscriptions/{sub_id}/cancel`. FastAPI will match `/grant` as `sub_id="grant"` against the earlier parametric route, making the grant endpoint unreachable.
2. The grant handler accepts any `plan_id` without validating it exists — an invalid ID causes an unhandled FK violation (500 instead of 400).

**Files:**
- Modify: `backend/app/modules/admin/router.py`
- Create: `backend/app/modules/admin/tests/test_admin_subscriptions.py`

- [ ] **Step 1: Read the affected router section**

  Read lines 330–415 of `backend/app/modules/admin/router.py` to see the exact order of the three subscription routes.

- [ ] **Step 2: Write the failing tests**

  Create `backend/app/modules/admin/tests/test_admin_subscriptions.py`:

  ```python
  """Tests for admin subscription endpoints — route ordering and plan validation."""
  import pytest
  from unittest.mock import AsyncMock, patch
  from fastapi.testclient import TestClient


  def _get_test_client():
      from app.main import app
      return TestClient(app)


  def test_grant_route_is_reachable_before_parametric_routes():
      """
      /subscriptions/grant must not be swallowed by /subscriptions/{sub_id}/extend.
      FastAPI routes are matched in declaration order — literal routes must come first.
      """
      import inspect
      import app.modules.admin.router as admin_module

      # Inspect the MODULE source (not admin_module.router which is an APIRouter object)
      source = inspect.getsource(admin_module)

      grant_pos = source.find('"/subscriptions/grant"')
      extend_pos = source.find('"/subscriptions/{sub_id}/extend"')
      cancel_pos = source.find('"/subscriptions/{sub_id}/cancel"')

      assert grant_pos != -1, "grant route not found in admin router"
      assert grant_pos < extend_pos, (
          f"'/subscriptions/grant' (pos {grant_pos}) must be declared BEFORE "
          f"'/subscriptions/{{sub_id}}/extend' (pos {extend_pos}) to avoid shadowing"
      )
      assert grant_pos < cancel_pos, (
          f"'/subscriptions/grant' (pos {grant_pos}) must be declared BEFORE "
          f"'/subscriptions/{{sub_id}}/cancel' (pos {cancel_pos})"
      )


  @pytest.mark.asyncio
  async def test_grant_subscription_rejects_invalid_plan_id():
      """
      grant_subscription handler with invalid plan_id must raise BadRequest.
      We call the handler directly (it is a plain async function, not a coroutine wrapper).
      payment_repository is imported inside the function body, so we patch at the module level.
      """
      from app.shared.exceptions import BadRequest

      mock_db = AsyncMock()
      # First execute() call is the plan validation query — scalar() returns None (not found)
      # Second execute() call would be the insert — should never be reached
      mock_db.execute.return_value.scalar.return_value = None

      with patch(
          'app.modules.payment.repository.payment_repository.find_parent_by_email',
          new_callable=AsyncMock,
          return_value={"id": "some-uuid", "full_name": "Test Parent"},
      ):
          from app.modules.admin.router import grant_subscription
          with pytest.raises(BadRequest, match="plan_id"):
              await grant_subscription(
                  body={"email": "parent@test.com", "plan_id": 9999, "months": 3},
                  db=mock_db,
                  _=None,
              )


  @pytest.mark.asyncio
  async def test_grant_subscription_accepts_valid_plan_id():
      """
      grant_subscription handler with valid plan_id proceeds to create subscription.
      """
      mock_db = AsyncMock()
      # Plan validation query returns a valid id
      mock_db.execute.return_value.scalar.return_value = 1

      with patch(
          'app.modules.payment.repository.payment_repository.find_parent_by_email',
          new_callable=AsyncMock,
          return_value={"id": "abc", "full_name": "Test Parent"},
      ), patch(
          'app.modules.payment.repository.payment_repository.grant_subscription',
          new_callable=AsyncMock,
          return_value={"id": "sub-1", "expires_at": "2027-01-01"},
      ):
          from app.modules.admin.router import grant_subscription
          result = await grant_subscription(
              body={"email": "parent@test.com", "plan_id": 1, "months": 3},
              db=mock_db,
              _=None,
          )
          assert result["status"] == "granted"
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/admin/tests/test_admin_subscriptions.py -v --tb=short
  ```
  Expected: `test_grant_route_is_reachable_before_parametric_routes` FAILS (wrong order). Others may fail too.

- [ ] **Step 4: Fix route ordering in admin/router.py**

  Move the entire `@router.post("/subscriptions/grant")` handler (including its docstring and function body) to appear **before** the `@router.post("/subscriptions/{sub_id}/extend")` handler.

  The correct order in the file must be:
  ```
  GET  /subscriptions           ← list (existing, keep position)
  POST /subscriptions/grant     ← ← MOVE HERE (literal before parametric)
  POST /subscriptions/{sub_id}/extend
  POST /subscriptions/{sub_id}/cancel
  ```

- [ ] **Step 5: Add plan_id validation to the grant handler**

  In the `grant_subscription` function, after the existing `email` and `plan_id` presence checks, add:

  ```python
  # Validate plan exists and is active
  plan_check = await db.execute(
      text("SELECT id FROM payment_plans WHERE id = :pid AND is_active = true"),
      {"pid": plan_id},
  )
  if not plan_check.scalar():
      raise BadRequest(f"plan_id {plan_id} does not exist or is inactive")
  ```

  Ensure `text` is imported at the top of `router.py` (it already is — `from sqlalchemy import text`).

- [ ] **Step 6: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/admin/tests/test_admin_subscriptions.py -v --tb=short
  ```
  Expected: All 3 tests pass.

- [ ] **Step 7: Run full backend test suite**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All tests pass.

- [ ] **Step 8: Commit**

  ```bash
  git add backend/app/modules/admin/router.py \
          backend/app/modules/admin/tests/test_admin_subscriptions.py
  git commit -m "fix: reorder admin subscription routes (grant before parametric) and validate plan_id"
  ```

---

## Task 4: A4 — Remove console.log from PDF export

**Problem:** `console.log('PDF dimensions:', pdfWidth, 'x', pdfHeight)` left in production code at `ResultPage.jsx:66`.

**Files:**
- Modify: `frontend/src/modules/analysis/pages/ResultPage.jsx`

- [ ] **Step 1: Verify the line exists**

  ```bash
  grep -n "PDF dimensions\|console.log" frontend/src/modules/analysis/pages/ResultPage.jsx
  ```
  Expected: Shows the offending line number.

- [ ] **Step 2: Delete the console.log line**

  In `frontend/src/modules/analysis/pages/ResultPage.jsx`, delete the line containing:
  ```javascript
  console.log('PDF dimensions:', pdfWidth, 'x', pdfHeight)
  ```

- [ ] **Step 3: Verify it's gone**

  ```bash
  grep -n "console.log" frontend/src/modules/analysis/pages/ResultPage.jsx
  ```
  Expected: No output.

- [ ] **Step 4: Build check**

  ```bash
  cd frontend && npm run build 2>&1 | tail -5
  ```
  Expected: Build succeeds.

- [ ] **Step 5: Commit**

  ```bash
  cd ..
  git add frontend/src/modules/analysis/pages/ResultPage.jsx
  git commit -m "fix: remove console.log from ResultPage PDF export"
  ```

---

## Task 5: Open PR

- [ ] **Step 1: Run full test suite**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -10
  cd frontend && npm test 2>&1 | tail -10
  ```
  Expected: All pass.

- [ ] **Step 2: Open PR**

  ```bash
  cd ..
  gh pr create \
    --title "fix: admin polish — dynamic exams, i18n, route ordering, plan validation, console.log" \
    --body "Fixes A1–A4 from the production readiness audit. See docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md" \
    --base main
  ```
