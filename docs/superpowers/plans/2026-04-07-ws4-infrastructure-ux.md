# WS4: Infrastructure & UX Debt — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 infrastructure and UX issues: JWKS hard-fail on startup, rate limiting, session timeout warning, Facebook button disabled, offline banner, and consistent loading skeletons.

**Architecture:** Mixed backend (I1, I2) and frontend (I3–I6). No new pages or routes. New shared components for I3, I5, I6. All tests written first. One commit per fix.

**Tech Stack:** FastAPI + slowapi (backend), React 18 + Zustand + Supabase client (frontend), pytest (backend), vitest + @testing-library/react (frontend).

**Spec:** `docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md` — fixes I1–I6.

**Prerequisite:** WS1 merged (vitest installed, branch starts from WS1 merge). Check out:
```bash
git checkout main && git pull && git checkout -b fix/infrastructure-ux
```

**Backend test command:**
```bash
DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short
```

**Frontend test command:**
```bash
cd frontend && npm test
```

---

## Task 1: I1 — JWKS fetch hard-fails on startup

**Problem:** If Supabase JWKS is unreachable at app startup, `set_jwks_keys()` prints a warning but continues. ES256 auth is silently broken. The server appears healthy but nobody can log in.

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/modules/auth/dependencies.py` (only if `set_jwks_keys` lives there)
- Create: `backend/app/tests/__init__.py` (create directory)
- Create: `backend/app/tests/test_startup.py`

- [ ] **Step 0: Create the backend/app/tests directory**

  ```bash
  mkdir -p backend/app/tests && touch backend/app/tests/__init__.py
  ```

- [ ] **Step 1: Read main.py lifespan block**

  Read `backend/app/main.py` focusing on the `lifespan` function. Note exactly where `set_jwks_keys()` is called and what happens on failure.

  Also read `backend/app/modules/auth/dependencies.py` to see `set_jwks_keys()` — note if it raises or just prints on failure.

- [ ] **Step 2: Write the failing test**

  Create `backend/app/tests/test_startup.py`:

  ```python
  """Tests for app startup behavior — JWKS fetch retry and hard-fail."""
  import pytest
  from unittest.mock import patch, AsyncMock


  @pytest.mark.asyncio
  async def test_jwks_fetch_failure_raises_runtime_error():
      """
      If JWKS fetch fails on all 3 retry attempts, app startup must
      raise RuntimeError — not silently continue with broken auth.
      """
      import httpx

      with patch(
          'app.modules.auth.dependencies.httpx.AsyncClient',
      ) as mock_client_class:
          mock_client = AsyncMock()
          mock_client.__aenter__ = AsyncMock(return_value=mock_client)
          mock_client.__aexit__ = AsyncMock(return_value=False)
          mock_client.get.side_effect = httpx.ConnectError("Connection refused")
          mock_client_class.return_value = mock_client

          from app.main import startup_jwks_with_retry
          with pytest.raises(RuntimeError, match="JWKS"):
              await startup_jwks_with_retry()


  @pytest.mark.asyncio
  async def test_jwks_fetch_succeeds_on_second_attempt():
      """
      If JWKS fetch fails on attempt 1 but succeeds on attempt 2,
      startup should complete without raising RuntimeError.
      """
      import httpx

      call_count = 0

      async def mock_get(url, **kwargs):
          nonlocal call_count
          call_count += 1
          if call_count == 1:
              raise httpx.ConnectError("First attempt fails")
          # Second attempt returns valid JWKS
          mock_response = AsyncMock()
          mock_response.json.return_value = {"keys": [{"kty": "EC", "kid": "test"}]}
          mock_response.raise_for_status = lambda: None
          return mock_response

      with patch('app.modules.auth.dependencies.httpx.AsyncClient') as mock_client_class, \
           patch('asyncio.sleep', new_callable=AsyncMock):
          mock_client = AsyncMock()
          mock_client.__aenter__ = AsyncMock(return_value=mock_client)
          mock_client.__aexit__ = AsyncMock(return_value=False)
          mock_client.get = mock_get
          mock_client_class.return_value = mock_client

          from app.main import startup_jwks_with_retry
          # Should not raise
          await startup_jwks_with_retry()

      assert call_count == 2
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_startup.py -v --tb=short
  ```
  Expected: `FAILED` — `startup_jwks_with_retry` doesn't exist yet.

- [ ] **Step 4: Create startup_jwks_with_retry in main.py**

  In `backend/app/main.py`, add this async function **before** the `lifespan` function:

  ```python
  async def startup_jwks_with_retry(max_attempts: int = 3, delay_seconds: int = 2) -> None:
      """
      Fetch Supabase JWKS with retry. Raises RuntimeError if all attempts fail.
      Called during app startup — failure means ES256 auth is broken, so we hard-fail.
      """
      import asyncio
      last_error = None
      for attempt in range(1, max_attempts + 1):
          try:
              await set_jwks_keys()
              return  # Success
          except Exception as exc:
              last_error = exc
              if attempt < max_attempts:
                  print(f"[WARN] JWKS fetch attempt {attempt}/{max_attempts} failed: {exc}. Retrying in {delay_seconds}s...")
                  await asyncio.sleep(delay_seconds)
              else:
                  print(f"[ERROR] JWKS fetch failed after {max_attempts} attempts: {exc}")

      raise RuntimeError(
          f"Cannot fetch JWKS from Supabase after {max_attempts} attempts — aborting startup. "
          f"Last error: {last_error}"
      )
  ```

  Then in the `lifespan` function, replace the existing `set_jwks_keys()` call (and its try/except) with:

  ```python
  await startup_jwks_with_retry()
  ```

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_startup.py -v --tb=short
  ```
  Expected: `2 passed`

- [ ] **Step 6: Commit**

  ```bash
  git add backend/app/main.py backend/app/tests/test_startup.py
  git commit -m "fix: JWKS fetch retries 3 times then hard-fails startup if Supabase unreachable"
  ```

---

## Task 2: I2 — Rate limiting on sensitive endpoints

**Problem:** No rate limiting. Change-password, payment, and webhook endpoints are unprotected against abuse.

**Important:** The `Limiter` instance must live in a standalone `backend/app/limiter.py` module — **not in `main.py`**. If routers import `limiter` from `main.py`, it creates a circular import (`main.py` imports routers → routers import `main.py`).

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/limiter.py` (new module for the Limiter instance)
- Modify: `backend/app/main.py`
- Modify: `backend/app/modules/user/router.py`
- Modify: `backend/app/modules/payment/router.py`
- Create: `backend/app/tests/test_rate_limiting.py`

- [ ] **Step 1: Install slowapi**

  ```bash
  cd backend && backend/.venv/bin/pip install slowapi
  ```

  Add `slowapi` to `backend/requirements.txt`:
  ```
  slowapi>=0.1.9
  ```

- [ ] **Step 2: Write the failing test**

  Create `backend/app/tests/test_rate_limiting.py`:

  ```python
  """Tests for rate limiting on sensitive endpoints."""
  import pytest
  from fastapi.testclient import TestClient
  from unittest.mock import patch, AsyncMock


  def test_change_password_is_rate_limited():
      """
      POST /api/users/me/change-password must have a rate limit decorator.
      We verify the decorator exists, not the actual limit (which requires real time).
      """
      from app.modules.user import router as user_router_module
      import inspect

      source = inspect.getsource(user_router_module)
      # slowapi rate limit decorator appears as @limiter.limit(...)
      assert 'limiter.limit' in source, (
          "user/router.py must apply @limiter.limit(...) to change-password endpoint"
      )


  def test_payment_create_order_is_rate_limited():
      """POST /api/payment/create-order must have a rate limit decorator."""
      from app.modules.payment import router as payment_router_module
      import inspect

      source = inspect.getsource(payment_router_module)
      assert 'limiter.limit' in source, (
          "payment/router.py must apply @limiter.limit(...) to create-order endpoint"
      )


  def test_limiter_registered_in_main():
      """The slowapi Limiter must be registered as a state attribute in main.py."""
      from app.main import app
      assert hasattr(app.state, 'limiter'), (
          "app.state.limiter must be set in main.py for slowapi to work"
      )
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_rate_limiting.py -v --tb=short
  ```
  Expected: All 3 `FAILED`.

- [ ] **Step 4: Create backend/app/limiter.py**

  Create `backend/app/limiter.py`:

  ```python
  """
  Shared rate limiter instance.
  Defined here (not in main.py) to avoid circular imports:
    main.py imports routers → routers cannot import main.py.
  """
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)
  ```

- [ ] **Step 5: Register limiter in main.py**

  In `backend/app/main.py`, add:

  ```python
  from slowapi import _rate_limit_exceeded_handler
  from slowapi.errors import RateLimitExceeded
  from app.limiter import limiter
  ```

  After `app = FastAPI(...)`, add:

  ```python
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
  ```

- [ ] **Step 6: Add rate limit to change-password endpoint in user/router.py**

  In `backend/app/modules/user/router.py`:

  1. Add import: `from app.limiter import limiter`
  2. Add `from fastapi import Request` if not already imported.
  3. Decorate the change-password endpoint:

  ```python
  @router.post("/me/change-password")
  @limiter.limit("5/minute")
  async def change_password(
      request: Request,          # ← required by slowapi (must be first param after self)
      data: ChangePasswordRequest,
      db: AsyncSession = Depends(get_db),
      identity: UserIdentity = Depends(verify_token),
  ):
  ```

  **Note:** slowapi requires `request: Request` as a parameter in the route function signature.

- [ ] **Step 6: Add rate limits to payment endpoints in payment/router.py**

  In `backend/app/modules/payment/router.py`:

  1. Add imports: `from app.main import limiter` and `from fastapi import Request`.
  2. Decorate `create_order`:

  ```python
  @router.post("/create-order")
  @limiter.limit("10/minute")
  async def create_order(
      request: Request,
      body: CreateOrderRequest,
      db: AsyncSession = Depends(get_db),
      identity: UserIdentity = Depends(verify_token),
  ):
  ```

  3. Decorate `verify_payment` with `@limiter.limit("10/minute")` and add `request: Request`.
  4. Decorate `webhook` with `@limiter.limit("30/minute")` and add `request: Request`.

- [ ] **Step 7: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_rate_limiting.py -v --tb=short
  ```
  Expected: `3 passed`

- [ ] **Step 8: Run full backend test suite**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All pass.

- [ ] **Step 9: Commit**

  ```bash
  cd ..
  git add backend/requirements.txt backend/app/main.py \
          backend/app/modules/user/router.py \
          backend/app/modules/payment/router.py \
          backend/app/tests/test_rate_limiting.py
  git commit -m "fix: add slowapi rate limiting to change-password, payment, and webhook endpoints"
  ```

---

## Task 3: I3 — Session timeout warning

**Problem:** Supabase tokens expire (~1 hour). The 401 handler hard-redirects to `/login` with no warning. Non-autosaved work is lost silently.

**Files:**
- Create: `frontend/src/shared/components/SessionExpiryWarning.jsx`
- Create: `frontend/src/shared/components/SessionExpiryWarning.test.jsx`
- Modify: `frontend/src/shared/layouts/AppLayout.jsx`

- [ ] **Step 1: Understand token storage**

  Read `frontend/src/modules/auth/store/authStore.js`. Find where the JWT token is stored and how to access it. Note: the Supabase session token's `exp` claim (Unix timestamp) tells us when it expires.

- [ ] **Step 2: Write the failing tests**

  Create `frontend/src/shared/components/SessionExpiryWarning.test.jsx`:

  ```javascript
  import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
  import { render, screen, act } from '@testing-library/react'

  // Mock auth store
  vi.mock('@/modules/auth', () => ({
    useAuthStore: vi.fn(),
  }))

  // Mock Supabase client
  vi.mock('@/config/supabaseClient', () => ({
    default: {
      auth: {
        refreshSession: vi.fn(),
      },
    },
  }))

  describe('SessionExpiryWarning', () => {
    let useAuthStore

    beforeEach(async () => {
      vi.useFakeTimers()
      useAuthStore = (await import('@/modules/auth')).useAuthStore
    })

    afterEach(() => {
      vi.useRealTimers()
      vi.resetModules()
    })

    it('does not show banner when token expires in more than 5 minutes', async () => {
      const futureExp = Math.floor(Date.now() / 1000) + 600 // 10 minutes from now
      useAuthStore.mockReturnValue({ token: `header.${btoa(JSON.stringify({ exp: futureExp }))}.sig` })

      const { default: SessionExpiryWarning } = await import('./SessionExpiryWarning')
      render(<SessionExpiryWarning />)

      expect(screen.queryByTestId('session-expiry-banner')).toBeNull()
    })

    it('shows banner when token expires in less than 5 minutes', async () => {
      const nearExp = Math.floor(Date.now() / 1000) + 240 // 4 minutes from now
      useAuthStore.mockReturnValue({ token: `header.${btoa(JSON.stringify({ exp: nearExp }))}.sig` })

      const { default: SessionExpiryWarning } = await import('./SessionExpiryWarning')
      render(<SessionExpiryWarning />)

      // Advance time to trigger the setTimeout
      await act(async () => { vi.runAllTimers() })
      expect(screen.getByTestId('session-expiry-banner')).toBeTruthy()
    })

    it('shows extend session button', async () => {
      const nearExp = Math.floor(Date.now() / 1000) + 240
      useAuthStore.mockReturnValue({ token: `header.${btoa(JSON.stringify({ exp: nearExp }))}.sig` })

      const { default: SessionExpiryWarning } = await import('./SessionExpiryWarning')
      render(<SessionExpiryWarning />)

      await act(async () => { vi.runAllTimers() })
      expect(screen.getByRole('button', { name: /extend/i })).toBeTruthy()
    })
  })
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/components/SessionExpiryWarning.test.jsx
  ```
  Expected: `FAILED` — module not found.

- [ ] **Step 4: Create SessionExpiryWarning.jsx**

  Create `frontend/src/shared/components/SessionExpiryWarning.jsx`:

  ```javascript
  import { useState, useEffect, useRef } from 'react'
  import { useAuthStore } from '@/modules/auth'
  import supabase from '@/config/supabaseClient'

  const WARNING_BEFORE_SECONDS = 5 * 60 // Show warning 5 minutes before expiry

  function getTokenExp(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp ?? null
    } catch {
      return null
    }
  }

  export default function SessionExpiryWarning() {
    const { token } = useAuthStore()
    const [showBanner, setShowBanner] = useState(false)
    const timerRef = useRef(null)

    useEffect(() => {
      if (!token) return

      const exp = getTokenExp(token)
      if (!exp) return

      const nowSeconds = Math.floor(Date.now() / 1000)
      const secondsUntilExpiry = exp - nowSeconds
      const secondsUntilWarning = secondsUntilExpiry - WARNING_BEFORE_SECONDS

      // Already in the warning window
      if (secondsUntilWarning <= 0 && secondsUntilExpiry > 0) {
        setShowBanner(true)
        return
      }

      // Schedule banner to appear
      timerRef.current = setTimeout(() => {
        setShowBanner(true)
      }, secondsUntilWarning * 1000)

      return () => clearTimeout(timerRef.current)
    }, [token])

    const handleExtend = async () => {
      const { error } = await supabase.auth.refreshSession()
      if (!error) {
        setShowBanner(false)
        clearTimeout(timerRef.current)
      }
      // On error, let the 401 handler log the user out naturally
    }

    if (!showBanner) return null

    return (
      <div
        data-testid="session-expiry-banner"
        className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-white text-sm py-2 px-4 flex items-center justify-between"
      >
        <span>Your session is about to expire. Save your work.</span>
        <button
          onClick={handleExtend}
          className="ml-4 px-3 py-1 bg-white text-yellow-700 rounded font-medium hover:bg-yellow-50 transition-colors"
        >
          Extend session
        </button>
      </div>
    )
  }
  ```

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/components/SessionExpiryWarning.test.jsx
  ```
  Expected: `3 passed`

- [ ] **Step 6: Mount in AppLayout.jsx**

  In `frontend/src/shared/layouts/AppLayout.jsx`:
  1. Add import: `import SessionExpiryWarning from '@/shared/components/SessionExpiryWarning'`
  2. Render it once as the first child of the outermost div: `<SessionExpiryWarning />`

- [ ] **Step 7: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/components/SessionExpiryWarning.jsx \
          frontend/src/shared/components/SessionExpiryWarning.test.jsx \
          frontend/src/shared/layouts/AppLayout.jsx
  git commit -m "fix: add session expiry warning banner 5 minutes before token expires"
  ```

---

## Task 4: I4 — Disable Facebook OAuth button

**Problem:** Facebook button shows "Coming Soon" badge but is clickable and attempts OAuth. Users get a confusing Supabase error.

**Files:**
- Modify: `frontend/src/modules/auth/pages/LoginPage.jsx`
- Create: `frontend/src/modules/auth/pages/LoginPage.test.jsx`

- [ ] **Step 1: Write the failing test**

  Create `frontend/src/modules/auth/pages/LoginPage.test.jsx`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { render, screen, fireEvent } from '@testing-library/react'
  import { MemoryRouter } from 'react-router-dom'

  vi.mock('@/modules/auth', () => ({
    useAuthStore: () => ({
      loginWithFacebook: vi.fn(),
      loginWithGoogle: vi.fn(),
      isAuthenticated: false,
      isLoading: false,
      error: null,
    }),
  }))

  describe('LoginPage Facebook button', () => {
    it('Facebook button is disabled', async () => {
      const { default: LoginPage } = await import('./LoginPage')
      render(<MemoryRouter><LoginPage /></MemoryRouter>)

      // Find by text or aria — adjust selector to match actual button text
      const facebookBtn = screen.getByText(/Facebook/i).closest('button')
      expect(facebookBtn).toHaveAttribute('disabled')
    })

    it('clicking the Facebook button does not trigger OAuth', async () => {
      const mockLoginWithFacebook = vi.fn()
      const { useAuthStore } = await import('@/modules/auth')
      useAuthStore.mockReturnValue({
        loginWithFacebook: mockLoginWithFacebook,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      })

      const { default: LoginPage } = await import('./LoginPage')
      render(<MemoryRouter><LoginPage /></MemoryRouter>)

      const facebookBtn = screen.getByText(/Facebook/i).closest('button')
      fireEvent.click(facebookBtn)

      expect(mockLoginWithFacebook).not.toHaveBeenCalled()
    })
  })
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/modules/auth/pages/LoginPage.test.jsx
  ```
  Expected: `FAILED` — button is not disabled.

- [ ] **Step 3: Disable the Facebook button in LoginPage.jsx**

  Read `frontend/src/modules/auth/pages/LoginPage.jsx`. Find the Facebook OAuth button. Add:
  - `disabled` attribute
  - `cursor-not-allowed opacity-50` to className
  - `title="Facebook login coming soon"` tooltip

  Remove or bypass the `onClick` handler (a `disabled` button won't fire click events in the browser, but make it explicit: either `onClick={undefined}` or keep the handler — the `disabled` attribute prevents it from firing).

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/modules/auth/pages/LoginPage.test.jsx
  ```
  Expected: `2 passed`

- [ ] **Step 5: Commit**

  ```bash
  cd ..
  git add frontend/src/modules/auth/pages/LoginPage.jsx \
          frontend/src/modules/auth/pages/LoginPage.test.jsx
  git commit -m "fix: disable Facebook OAuth button until enabled in Supabase"
  ```

---

## Task 5: I5 — Offline detection banner

**Problem:** When connectivity is lost, API calls fail silently. No user feedback.

**Files:**
- Create: `frontend/src/shared/hooks/useOnlineStatus.js`
- Create: `frontend/src/shared/hooks/useOnlineStatus.test.js`
- Create: `frontend/src/shared/components/OfflineBanner.jsx`
- Create: `frontend/src/shared/components/OfflineBanner.test.jsx`
- Modify: `frontend/src/shared/layouts/AppLayout.jsx`

- [ ] **Step 1: Write failing tests for the hook**

  Create `frontend/src/shared/hooks/useOnlineStatus.test.js`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { renderHook, act } from '@testing-library/react'

  describe('useOnlineStatus', () => {
    it('returns true when navigator.onLine is true', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
      const { default: useOnlineStatus } = await import('./useOnlineStatus')
      const { result } = renderHook(() => useOnlineStatus())
      expect(result.current.isOnline).toBe(true)
    })

    it('returns false when offline event fires', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
      const { default: useOnlineStatus } = await import('./useOnlineStatus')
      const { result } = renderHook(() => useOnlineStatus())

      act(() => {
        window.dispatchEvent(new Event('offline'))
      })

      expect(result.current.isOnline).toBe(false)
    })

    it('returns true again when online event fires after offline', async () => {
      const { default: useOnlineStatus } = await import('./useOnlineStatus')
      const { result } = renderHook(() => useOnlineStatus())

      act(() => { window.dispatchEvent(new Event('offline')) })
      act(() => { window.dispatchEvent(new Event('online')) })

      expect(result.current.isOnline).toBe(true)
    })
  })
  ```

- [ ] **Step 2: Run hook tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/hooks/useOnlineStatus.test.js
  ```
  Expected: `FAILED` — module not found.

- [ ] **Step 3: Create useOnlineStatus.js**

  Create `frontend/src/shared/hooks/useOnlineStatus.js`:

  ```javascript
  import { useState, useEffect } from 'react'

  export default function useOnlineStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine)

    useEffect(() => {
      const handleOnline = () => setIsOnline(true)
      const handleOffline = () => setIsOnline(false)

      window.addEventListener('online', handleOnline)
      window.addEventListener('offline', handleOffline)

      return () => {
        window.removeEventListener('online', handleOnline)
        window.removeEventListener('offline', handleOffline)
      }
    }, [])

    return { isOnline }
  }
  ```

- [ ] **Step 4: Run hook tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/hooks/useOnlineStatus.test.js
  ```
  Expected: `3 passed`

- [ ] **Step 5: Write failing tests for the banner**

  Create `frontend/src/shared/components/OfflineBanner.test.jsx`:

  ```javascript
  import { describe, it, expect, vi, act } from 'vitest'
  import { render, screen } from '@testing-library/react'

  vi.mock('@/shared/hooks/useOnlineStatus', () => ({
    default: vi.fn(),
  }))

  describe('OfflineBanner', () => {
    it('is not visible when online', async () => {
      const useOnlineStatus = (await import('@/shared/hooks/useOnlineStatus')).default
      useOnlineStatus.mockReturnValue({ isOnline: true })

      const { default: OfflineBanner } = await import('./OfflineBanner')
      render(<OfflineBanner />)

      expect(screen.queryByTestId('offline-banner')).toBeNull()
    })

    it('is visible when offline', async () => {
      const useOnlineStatus = (await import('@/shared/hooks/useOnlineStatus')).default
      useOnlineStatus.mockReturnValue({ isOnline: false })

      const { default: OfflineBanner } = await import('./OfflineBanner')
      render(<OfflineBanner />)

      expect(screen.getByTestId('offline-banner')).toBeTruthy()
    })

    it('shows helpful message when offline', async () => {
      const useOnlineStatus = (await import('@/shared/hooks/useOnlineStatus')).default
      useOnlineStatus.mockReturnValue({ isOnline: false })

      const { default: OfflineBanner } = await import('./OfflineBanner')
      render(<OfflineBanner />)

      expect(screen.getByText(/offline/i)).toBeTruthy()
    })
  })
  ```

- [ ] **Step 6: Run banner tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/components/OfflineBanner.test.jsx
  ```
  Expected: `FAILED` — module not found.

- [ ] **Step 7: Create OfflineBanner.jsx**

  Create `frontend/src/shared/components/OfflineBanner.jsx`:

  ```javascript
  import useOnlineStatus from '@/shared/hooks/useOnlineStatus'

  export default function OfflineBanner() {
    const { isOnline } = useOnlineStatus()

    if (isOnline) return null

    return (
      <div
        data-testid="offline-banner"
        className="fixed top-0 left-0 right-0 z-50 bg-gray-800 text-white text-sm py-2 px-4 text-center"
      >
        You are offline. Some features may not work until your connection is restored.
      </div>
    )
  }
  ```

- [ ] **Step 8: Run banner tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/components/OfflineBanner.test.jsx
  ```
  Expected: `3 passed`

- [ ] **Step 9: Mount in AppLayout.jsx**

  In `frontend/src/shared/layouts/AppLayout.jsx`:
  1. Add import: `import OfflineBanner from '@/shared/components/OfflineBanner'`
  2. Render after `<SessionExpiryWarning />`: `<OfflineBanner />`

- [ ] **Step 10: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/hooks/useOnlineStatus.js \
          frontend/src/shared/hooks/useOnlineStatus.test.js \
          frontend/src/shared/components/OfflineBanner.jsx \
          frontend/src/shared/components/OfflineBanner.test.jsx \
          frontend/src/shared/layouts/AppLayout.jsx
  git commit -m "fix: add offline detection banner via useOnlineStatus hook"
  ```

---

## Task 6: I6 — Consistent loading skeletons

**Problem:** `AdminDashboardPage` and `ParentDashboardPage` use skeleton loaders. `StatsPage` and `ImageUploaderPage` use plain spinners. Inconsistent.

**Files:**
- Create: `frontend/src/shared/components/SkeletonCard.jsx`
- Create: `frontend/src/shared/components/SkeletonTable.jsx`
- Create: `frontend/src/shared/components/SkeletonCard.test.jsx`
- Modify: `frontend/src/modules/admin/pages/StatsPage.jsx`
- Modify: `frontend/src/modules/admin/pages/ImageUploaderPage.jsx`

- [ ] **Step 1: Read existing skeleton pattern**

  Read `frontend/src/modules/admin/pages/AdminDashboardPage.jsx`. Find the existing skeleton card markup to use as the pattern to extract.

- [ ] **Step 2: Write failing tests**

  Create `frontend/src/shared/components/SkeletonCard.test.jsx`:

  ```javascript
  import { describe, it, expect } from 'vitest'
  import { render, screen } from '@testing-library/react'

  describe('SkeletonCard', () => {
    it('renders an animated placeholder element', async () => {
      const { default: SkeletonCard } = await import('./SkeletonCard')
      render(<SkeletonCard />)
      const el = screen.getByTestId('skeleton-card')
      expect(el.className).toMatch(/animate-pulse/)
    })
  })

  describe('SkeletonTable', () => {
    it('renders multiple skeleton rows', async () => {
      const { default: SkeletonTable } = await import('./SkeletonTable')
      render(<SkeletonTable rows={5} />)
      const rows = screen.getAllByTestId('skeleton-row')
      expect(rows.length).toBe(5)
    })

    it('defaults to 3 rows', async () => {
      const { default: SkeletonTable } = await import('./SkeletonTable')
      render(<SkeletonTable />)
      const rows = screen.getAllByTestId('skeleton-row')
      expect(rows.length).toBe(3)
    })
  })
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/components/SkeletonCard.test.jsx
  ```
  Expected: `FAILED` — modules not found.

- [ ] **Step 4: Create SkeletonCard.jsx**

  Create `frontend/src/shared/components/SkeletonCard.jsx`:

  ```javascript
  export default function SkeletonCard({ className = '' }) {
    return (
      <div
        data-testid="skeleton-card"
        className={`animate-pulse bg-gray-200 rounded-xl h-28 ${className}`}
      />
    )
  }
  ```

- [ ] **Step 5: Create SkeletonTable.jsx**

  Create `frontend/src/shared/components/SkeletonTable.jsx`:

  ```javascript
  export default function SkeletonTable({ rows = 3 }) {
    return (
      <div className="animate-pulse space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            data-testid="skeleton-row"
            className="h-10 bg-gray-200 rounded-lg"
          />
        ))}
      </div>
    )
  }
  ```

- [ ] **Step 6: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/components/SkeletonCard.test.jsx
  ```
  Expected: `3 passed`

- [ ] **Step 7: Update StatsPage.jsx**

  In `frontend/src/modules/admin/pages/StatsPage.jsx`:
  1. Add import: `import SkeletonTable from '@/shared/components/SkeletonTable'`
  2. Find the loading state render (where a spinner is shown). Replace:
     ```javascript
     // OLD: <div className="..."><Spinner /></div>  (or similar)
     // NEW:
     if (statsLoading) return <SkeletonTable rows={8} />
     ```

- [ ] **Step 8: Update ImageUploaderPage.jsx — same pattern**

  Same replacement as StatsPage: import `SkeletonTable`, replace spinner with `<SkeletonTable rows={4} />`.

- [ ] **Step 9: Run all frontend tests**

  ```bash
  cd frontend && npm test
  ```
  Expected: All tests pass.

- [ ] **Step 10: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/components/SkeletonCard.jsx \
          frontend/src/shared/components/SkeletonTable.jsx \
          frontend/src/shared/components/SkeletonCard.test.jsx \
          frontend/src/modules/admin/pages/StatsPage.jsx \
          frontend/src/modules/admin/pages/ImageUploaderPage.jsx
  git commit -m "fix: extract SkeletonCard/SkeletonTable components and replace spinners in admin pages"
  ```

---

## Task 7: Final check and PR

- [ ] **Step 1: Run all backend tests**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All pass.

- [ ] **Step 2: Run all frontend tests**

  ```bash
  cd frontend && npm test
  ```
  Expected: All pass.

- [ ] **Step 3: Build check**

  ```bash
  cd frontend && npm run build 2>&1 | tail -5
  ```
  Expected: Build succeeds.

- [ ] **Step 4: Open PR**

  ```bash
  cd ..
  gh pr create \
    --title "fix: infrastructure & UX — JWKS retry, rate limiting, session warning, offline banner, skeletons" \
    --body "Fixes I1–I6 from the production readiness audit. See docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md" \
    --base main
  ```
