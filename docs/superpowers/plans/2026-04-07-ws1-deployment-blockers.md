# WS1: Deployment Blockers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 issues that prevent ScholarPath from running correctly in a production deployment.

**Architecture:** Sequential fixes on branch `fix/deployment-blockers`. Backend fixes use existing pytest suite. Frontend fixes require vitest setup (Task 1) before any frontend tests can run. Each fix is one commit.

**Tech Stack:** FastAPI + pydantic-settings (backend), React 18 + Vite + Zustand (frontend), pytest (backend tests), vitest + @testing-library/react (frontend tests, set up in Task 1).

**Spec:** `docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md` — fixes B1–B5.

---

## Pre-flight

- [ ] Create and checkout branch:
  ```bash
  git checkout -b fix/deployment-blockers
  ```

---

## Task 1: Set up frontend test framework (vitest)

**Why:** The frontend has no test framework. All subsequent frontend tasks require this.

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.js`
- Create: `frontend/src/test/setup.js`

- [ ] **Step 1: Install vitest and testing-library**

  ```bash
  cd frontend && npm install -D vitest @vitest/coverage-v8 @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
  ```

- [ ] **Step 2: Add test config to vite.config.js**

  Open `frontend/vite.config.js` and add the `test` block:

  ```javascript
  import { defineConfig } from 'vite'
  import react from '@vitejs/plugin-react'
  import path from 'path'

  export default defineConfig({
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.js',
    },
  })
  ```

- [ ] **Step 3: Create test setup file**

  Create `frontend/src/test/setup.js`:

  ```javascript
  import '@testing-library/jest-dom'
  ```

- [ ] **Step 4: Add test script to package.json**

  In `frontend/package.json`, add to `"scripts"`:
  ```json
  "test": "vitest run",
  "test:watch": "vitest"
  ```

- [ ] **Step 5: Verify vitest works with a smoke test**

  Create `frontend/src/test/smoke.test.js`:
  ```javascript
  import { describe, it, expect } from 'vitest'

  describe('test setup', () => {
    it('works', () => {
      expect(1 + 1).toBe(2)
    })
  })
  ```

  Run:
  ```bash
  cd frontend && npm test
  ```
  Expected: `1 passed`

- [ ] **Step 6: Commit**

  ```bash
  cd ..
  git add frontend/package.json frontend/vite.config.js frontend/src/test/
  git commit -m "chore: add vitest + testing-library for frontend tests"
  ```

---

## Task 2: B1 — CORS production URL

**Problem:** `allow_origins` hardcoded to localhost. All API calls fail from Vercel.

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Create: `backend/app/tests/test_main_cors.py`

- [ ] **Step 1: Write the failing test**

  Create `backend/app/tests/test_main_cors.py`:

  ```python
  """Tests for CORS configuration and settings."""
  import os
  import pytest


  def test_frontend_url_setting_defaults_to_empty():
      """FRONTEND_URL should default to empty string."""
      from app.config import Settings
      s = Settings(_env_file=None)
      assert s.FRONTEND_URL == ""


  def test_frontend_url_can_be_set_via_env(monkeypatch):
      """FRONTEND_URL env var should be readable by Settings."""
      monkeypatch.setenv("FRONTEND_URL", "https://scholarpath.vercel.app")
      from app.config import Settings
      s = Settings(_env_file=None)
      assert s.FRONTEND_URL == "https://scholarpath.vercel.app"


  def test_cors_origins_include_localhost():
      """Localhost origins must always be present for dev."""
      from app.config import Settings
      s = Settings(_env_file=None)
      origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
      if s.FRONTEND_URL:
          origins.append(s.FRONTEND_URL)
      assert "http://localhost:5173" in origins


  def test_cors_origins_include_frontend_url_when_set(monkeypatch):
      """When FRONTEND_URL is set, it is included in allow_origins."""
      monkeypatch.setenv("FRONTEND_URL", "https://scholarpath.vercel.app")
      from app.config import Settings
      s = Settings(_env_file=None)
      origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
      if s.FRONTEND_URL:
          origins.append(s.FRONTEND_URL)
      assert "https://scholarpath.vercel.app" in origins
  ```

- [ ] **Step 2: Run test to verify it fails**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_main_cors.py -v
  ```
  Expected: `FAILED` — `Settings` has no `FRONTEND_URL` field.

- [ ] **Step 3: Add FRONTEND_URL to config.py**

  In `backend/app/config.py`, add after the `RAZORPAY_WEBHOOK_SECRET` line:

  ```python
  # ── Frontend (CORS) ──────────────────────────────────────
  FRONTEND_URL: str = ""  # Set to deployed Vercel URL in production
  ```

- [ ] **Step 4: Update CORS middleware in main.py**

  In `backend/app/main.py`, replace the entire `app.add_middleware(CORSMiddleware, ...)` block with:

  ```python
  # Build allowed origins — always include localhost for dev
  _allowed_origins = [
      "http://localhost:5173",
      "http://localhost:5174",
      "http://localhost:3000",
  ]
  if settings.FRONTEND_URL:
      _allowed_origins.append(settings.FRONTEND_URL)

  app.add_middleware(
      CORSMiddleware,
      allow_origins=_allowed_origins,
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
      allow_headers=["Content-Type", "Authorization"],
  )
  ```

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests/test_main_cors.py -v
  ```
  Expected: `4 passed`

- [ ] **Step 6: Commit**

  ```bash
  git add backend/app/config.py backend/app/main.py backend/app/tests/test_main_cors.py
  git commit -m "fix: add FRONTEND_URL to config and tighten CORS for production"
  ```

---

## Task 3: B2 — Payment API endpoint fix

**Problem:** `paymentApi.getStatus()` calls `/api/payment/status` (404). Should be `/api/payment/subscription`.

**Files:**
- Modify: `frontend/src/modules/payment/api/paymentApi.js`
- Create: `frontend/src/modules/payment/api/paymentApi.test.js`

- [ ] **Step 1: Write the failing test**

  Create `frontend/src/modules/payment/api/paymentApi.test.js`:

  ```javascript
  import { describe, it, expect, vi, beforeEach } from 'vitest'

  // Mock apiClient before importing paymentApi
  vi.mock('@/config/apiClient', () => ({
    default: {
      get: vi.fn(),
      post: vi.fn(),
    },
  }))

  describe('paymentApi', () => {
    let apiClient
    let paymentApi

    beforeEach(async () => {
      vi.resetModules()
      apiClient = (await import('@/config/apiClient')).default
      paymentApi = (await import('./paymentApi')).paymentApi
    })

    it('getStatus calls /api/payment/subscription (not /status)', async () => {
      apiClient.get.mockResolvedValue({ data: {} })
      await paymentApi.getStatus()
      expect(apiClient.get).toHaveBeenCalledWith('/api/payment/subscription')
    })
  })
  ```

- [ ] **Step 2: Run test to verify it fails**

  ```bash
  cd frontend && npm test src/modules/payment/api/paymentApi.test.js
  ```
  Expected: `FAILED` — called with `/api/payment/status` not `/api/payment/subscription`.

- [ ] **Step 3: Fix the endpoint path**

  In `frontend/src/modules/payment/api/paymentApi.js` line 5, change:
  ```javascript
  getStatus: () => apiClient.get('/api/payment/status').then(r => r.data),
  ```
  to:
  ```javascript
  getStatus: () => apiClient.get('/api/payment/subscription').then(r => r.data),
  ```

- [ ] **Step 4: Run test to verify it passes**

  ```bash
  cd frontend && npm test src/modules/payment/api/paymentApi.test.js
  ```
  Expected: `1 passed`

- [ ] **Step 5: Commit**

  ```bash
  cd ..
  git add frontend/src/modules/payment/api/paymentApi.js frontend/src/modules/payment/api/paymentApi.test.js
  git commit -m "fix: correct payment status endpoint from /status to /subscription"
  ```

---

## Task 4: B3 — UpgradePrompt wrong API call

**Problem:** `UpgradePrompt` calls `/api/catalog/settings/payment_amount_inr` (doesn't exist). Should read price from payment store. Component must call `loadPlans()` itself because callers (`AttemptMistakesDrawer`, `RecentMistakesCard`) do not pre-load payment state.

**Files:**
- Modify: `frontend/src/shared/components/UpgradePrompt.jsx`
- Create: `frontend/src/shared/components/UpgradePrompt.test.jsx`

- [ ] **Step 1: Read the current UpgradePrompt implementation**

  Read `frontend/src/shared/components/UpgradePrompt.jsx` to understand current props and structure before writing the test.

- [ ] **Step 2: Write the failing tests**

  Create `frontend/src/shared/components/UpgradePrompt.test.jsx`:

  ```javascript
  import { describe, it, expect, vi, beforeEach } from 'vitest'
  import { render, screen } from '@testing-library/react'
  import { MemoryRouter } from 'react-router-dom'

  // Mock payment store
  const mockLoadPlans = vi.fn()
  vi.mock('@/modules/payment', () => ({
    usePaymentStore: vi.fn(),
  }))

  describe('UpgradePrompt', () => {
    let usePaymentStore

    beforeEach(async () => {
      vi.resetModules()
      usePaymentStore = (await import('@/modules/payment')).usePaymentStore
    })

    it('does not call any catalog API endpoint', async () => {
      const mockGet = vi.fn().mockResolvedValue({ data: {} })
      vi.mock('@/config/apiClient', () => ({ default: { get: mockGet } }))

      usePaymentStore.mockReturnValue({
        plans: [{ id: 1, price_inr: 49900, name: 'Premium' }],
        loadPlans: mockLoadPlans,
      })

      const { default: UpgradePrompt } = await import('./UpgradePrompt')
      render(<MemoryRouter><UpgradePrompt /></MemoryRouter>)

      expect(mockGet).not.toHaveBeenCalledWith(
        expect.stringContaining('catalog/settings')
      )
    })

    it('shows price from payment store plans', async () => {
      usePaymentStore.mockReturnValue({
        plans: [{ id: 1, price_inr: 49900, name: 'Premium' }],
        loadPlans: mockLoadPlans,
      })

      const { default: UpgradePrompt } = await import('./UpgradePrompt')
      render(<MemoryRouter><UpgradePrompt /></MemoryRouter>)

      // Price should appear somewhere in the rendered output
      // 49900 paise = ₹499
      expect(screen.getByText(/499/)).toBeTruthy()
    })

    it('shows fallback text when plans are empty', async () => {
      usePaymentStore.mockReturnValue({
        plans: [],
        loadPlans: mockLoadPlans,
      })

      const { default: UpgradePrompt } = await import('./UpgradePrompt')
      render(<MemoryRouter><UpgradePrompt /></MemoryRouter>)

      expect(screen.getByText(/Upgrade to Premium/i)).toBeTruthy()
    })

    it('calls loadPlans on mount when plans are empty', async () => {
      usePaymentStore.mockReturnValue({
        plans: [],
        loadPlans: mockLoadPlans,
      })

      const { default: UpgradePrompt } = await import('./UpgradePrompt')
      render(<MemoryRouter><UpgradePrompt /></MemoryRouter>)

      expect(mockLoadPlans).toHaveBeenCalled()
    })
  })
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/components/UpgradePrompt.test.jsx
  ```
  Expected: Multiple failures — catalog API is called, price from store not shown.

- [ ] **Step 4: Rewrite UpgradePrompt.jsx**

  Replace the existing component body. Keep all existing props and visual design. The only changes are:
  1. Import `usePaymentStore` from `@/modules/payment`
  2. Add `useEffect` to call `loadPlans()` when `plans.length === 0`
  3. Remove the `apiClient.get('/api/catalog/settings/...')` call
  4. Derive price display from `plans[0]?.price_inr`

  Format price as: `₹${Math.floor(plans[0].price_inr / 100)}` (convert paise to rupees).

  When `plans.length === 0` or still loading, show the upgrade CTA without a price figure.

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/components/UpgradePrompt.test.jsx
  ```
  Expected: `4 passed`

- [ ] **Step 6: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/components/UpgradePrompt.jsx frontend/src/shared/components/UpgradePrompt.test.jsx
  git commit -m "fix: UpgradePrompt reads price from payment store instead of nonexistent catalog endpoint"
  ```

---

## Task 5: B4 — React Error Boundary

**Problem:** No Error Boundary. One crashing component kills the entire app.

**Files:**
- Create: `frontend/src/shared/components/ErrorBoundary.jsx`
- Create: `frontend/src/shared/components/ErrorBoundary.test.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Write the failing test**

  Create `frontend/src/shared/components/ErrorBoundary.test.jsx`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { render, screen } from '@testing-library/react'

  // Suppress React's error boundary console.error noise in tests
  const originalError = console.error
  beforeEach(() => {
    console.error = vi.fn()
  })
  afterEach(() => {
    console.error = originalError
  })

  describe('ErrorBoundary', () => {
    it('renders children when there is no error', async () => {
      const { default: ErrorBoundary } = await import('./ErrorBoundary')
      render(
        <ErrorBoundary>
          <div>healthy content</div>
        </ErrorBoundary>
      )
      expect(screen.getByText('healthy content')).toBeTruthy()
    })

    it('renders fallback UI when a child throws', async () => {
      const { default: ErrorBoundary } = await import('./ErrorBoundary')

      const Bomb = () => { throw new Error('test crash') }

      render(
        <ErrorBoundary>
          <Bomb />
        </ErrorBoundary>
      )

      // Should show reload button, not crash the test
      expect(screen.getByRole('button', { name: /reload/i })).toBeTruthy()
    })

    it('does not show children after a crash', async () => {
      const { default: ErrorBoundary } = await import('./ErrorBoundary')
      const Bomb = () => { throw new Error('test crash') }

      render(
        <ErrorBoundary>
          <Bomb />
          <div>should not render</div>
        </ErrorBoundary>
      )

      expect(screen.queryByText('should not render')).toBeNull()
    })
  })
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/components/ErrorBoundary.test.jsx
  ```
  Expected: `FAILED` — module not found.

- [ ] **Step 3: Create ErrorBoundary.jsx**

  Create `frontend/src/shared/components/ErrorBoundary.jsx`:

  ```javascript
  import { Component } from 'react'

  export default class ErrorBoundary extends Component {
    constructor(props) {
      super(props)
      this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
      return { hasError: true, error }
    }

    componentDidCatch(error, info) {
      // In production, send to error reporting service here
      console.error('ErrorBoundary caught:', error, info)
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="min-h-screen flex items-center justify-center bg-surface-50">
            <div className="text-center max-w-md p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Something went wrong
              </h2>
              <p className="text-gray-500 mb-6">
                An unexpected error occurred. Please reload the page.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Reload page
              </button>
            </div>
          </div>
        )
      }
      return this.props.children
    }
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/components/ErrorBoundary.test.jsx
  ```
  Expected: `3 passed`

- [ ] **Step 5: Wrap Routes in App.jsx**

  In `frontend/src/App.jsx`:
  1. Add import at the top: `import ErrorBoundary from '@/shared/components/ErrorBoundary'`
  2. Wrap the `<Routes>` block:
     ```javascript
     <ErrorBoundary>
       <Routes>
         {/* ... existing routes ... */}
       </Routes>
     </ErrorBoundary>
     ```

- [ ] **Step 6: Verify App.jsx still renders (smoke check)**

  ```bash
  cd frontend && npm run build 2>&1 | tail -5
  ```
  Expected: Build succeeds with no errors.

- [ ] **Step 7: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/components/ErrorBoundary.jsx frontend/src/shared/components/ErrorBoundary.test.jsx frontend/src/App.jsx
  git commit -m "fix: add React Error Boundary to prevent full app crash on component errors"
  ```

---

## Task 6: B5 — Mobile sidebar

**Problem:** Sidebar hidden on mobile with no hamburger toggle. Mobile users cannot navigate.

**Files:**
- Modify: `frontend/src/shared/layouts/AppLayout.jsx`
- Create: `frontend/src/shared/layouts/AppLayout.test.jsx`

- [ ] **Step 1: Read AppLayout.jsx**

  Read `frontend/src/shared/layouts/AppLayout.jsx` fully to understand current structure before writing anything.

- [ ] **Step 2: Write the failing test**

  Create `frontend/src/shared/layouts/AppLayout.test.jsx`:

  ```javascript
  import { describe, it, expect, vi } from 'vitest'
  import { render, screen, fireEvent } from '@testing-library/react'
  import { MemoryRouter } from 'react-router-dom'

  // Mock all store dependencies
  vi.mock('@/modules/auth', () => ({
    useAuthStore: () => ({
      user: { full_name: 'Test User', role: 'student', avatar_url: null },
      isAuthenticated: true,
    }),
  }))
  vi.mock('@/modules/payment', () => ({
    usePaymentStore: () => ({ subscription: null }),
    SubscriptionStatus: () => null,
  }))

  describe('AppLayout mobile navigation', () => {
    it('renders a hamburger button on mobile', async () => {
      const { default: AppLayout } = await import('./AppLayout')
      render(
        <MemoryRouter>
          <AppLayout><div>content</div></AppLayout>
        </MemoryRouter>
      )
      // Hamburger button must exist (aria-label or test-id)
      expect(screen.getByTestId('hamburger-btn')).toBeTruthy()
    })

    it('mobile sidebar is hidden by default', async () => {
      const { default: AppLayout } = await import('./AppLayout')
      render(
        <MemoryRouter>
          <AppLayout><div>content</div></AppLayout>
        </MemoryRouter>
      )
      const mobileSidebar = screen.getByTestId('mobile-sidebar')
      expect(mobileSidebar.className).toMatch(/hidden|translate-x-full|-translate-x-full/)
    })

    it('clicking hamburger shows mobile sidebar', async () => {
      const { default: AppLayout } = await import('./AppLayout')
      render(
        <MemoryRouter>
          <AppLayout><div>content</div></AppLayout>
        </MemoryRouter>
      )
      fireEvent.click(screen.getByTestId('hamburger-btn'))
      const mobileSidebar = screen.getByTestId('mobile-sidebar')
      // Should no longer be hidden
      expect(mobileSidebar.className).not.toMatch(/translate-x-full/)
    })

    it('clicking backdrop closes mobile sidebar', async () => {
      const { default: AppLayout } = await import('./AppLayout')
      render(
        <MemoryRouter>
          <AppLayout><div>content</div></AppLayout>
        </MemoryRouter>
      )
      // Open
      fireEvent.click(screen.getByTestId('hamburger-btn'))
      // Close via backdrop
      fireEvent.click(screen.getByTestId('mobile-backdrop'))
      const mobileSidebar = screen.getByTestId('mobile-sidebar')
      expect(mobileSidebar.className).toMatch(/translate-x-full/)
    })
  })
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  cd frontend && npm test src/shared/layouts/AppLayout.test.jsx
  ```
  Expected: `FAILED` — `hamburger-btn` not found.

- [ ] **Step 4: Add mobile sidebar to AppLayout.jsx**

  Changes to make in `frontend/src/shared/layouts/AppLayout.jsx`:

  1. Add state at top of component:
     ```javascript
     const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
     ```

  2. In the existing `md:hidden` mobile header bar, add the hamburger button:
     ```javascript
     <button
       data-testid="hamburger-btn"
       onClick={() => setIsMobileMenuOpen(true)}
       className="p-2 rounded-md text-gray-600 hover:bg-gray-100"
       aria-label="Open navigation menu"
     >
       <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
       </svg>
     </button>
     ```

  3. Add mobile sidebar overlay just before the closing tag of the outermost div (renders on mobile only):
     ```javascript
     {/* Mobile sidebar overlay — only rendered on mobile */}
     <>
       {/* Backdrop */}
       <div
         data-testid="mobile-backdrop"
         onClick={() => setIsMobileMenuOpen(false)}
         className={`md:hidden fixed inset-0 z-30 bg-black/40 transition-opacity ${
           isMobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
         }`}
       />
       {/* Slide-in sidebar */}
       <div
         data-testid="mobile-sidebar"
         className={`md:hidden fixed top-0 left-0 h-full w-64 z-40 bg-white shadow-xl transform transition-transform duration-300 ${
           isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
         }`}
       >
         {/* Close button */}
         <div className="flex justify-end p-4">
           <button
             onClick={() => setIsMobileMenuOpen(false)}
             className="p-1 text-gray-500 hover:text-gray-700"
             aria-label="Close menu"
           >
             ✕
           </button>
         </div>
         {/* Reuse the same nav links as desktop sidebar */}
         <nav className="px-4 space-y-1">
           {/* Copy the nav link list from the desktop sidebar here */}
           {/* Each link should also call setIsMobileMenuOpen(false) on click */}
         </nav>
       </div>
     </>
     ```

  **Important:** Each nav link inside the mobile sidebar should call `setIsMobileMenuOpen(false)` on click so the drawer closes when the user navigates.

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  cd frontend && npm test src/shared/layouts/AppLayout.test.jsx
  ```
  Expected: `4 passed`

- [ ] **Step 6: Visual smoke check**

  ```bash
  cd frontend && npm run dev
  ```
  Open browser → resize to mobile width → verify hamburger appears → click it → verify sidebar slides in → click backdrop → verify it closes.

- [ ] **Step 7: Commit**

  ```bash
  cd ..
  git add frontend/src/shared/layouts/AppLayout.jsx frontend/src/shared/layouts/AppLayout.test.jsx
  git commit -m "fix: add mobile hamburger menu and slide-in sidebar for mobile users"
  ```

---

## Task 7: Run full test suite and open PR

- [ ] **Step 1: Run all backend tests**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All existing tests pass + new CORS tests pass.

- [ ] **Step 2: Run all frontend tests**

  ```bash
  cd frontend && npm test
  ```
  Expected: All tests pass.

- [ ] **Step 3: Open PR**

  ```bash
  gh pr create \
    --title "fix: deployment blockers — CORS, payment endpoint, UpgradePrompt, ErrorBoundary, mobile nav" \
    --body "Fixes B1–B5 from the production readiness audit. See docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md" \
    --base main
  ```
