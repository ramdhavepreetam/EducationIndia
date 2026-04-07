/**
 * Auth module public API — ADR-010 convention.
 *
 * Only these exports are allowed to be imported by other modules.
 * Internal components (e.g. form fields) are NOT exported.
 */

// Pages
export { default as LoginPage } from './pages/LoginPage'
export { default as RegisterPage } from './pages/RegisterPage'
// NOTE: OnboardingPage moved to user module (frontend/src/modules/user/)

// Components
export { default as ProtectedRoute } from './components/ProtectedRoute'

// Store
export { useAuthStore } from './store/authStore'

// API
export { authApi } from './api/authApi'
