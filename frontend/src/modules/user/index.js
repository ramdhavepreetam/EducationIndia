/**
 * User module public API — ADR-010 convention.
 *
 * Only these exports are allowed to be imported by other modules.
 */

// Pages
export { default as OnboardingPage } from './pages/OnboardingPage'
export { default as ProfilePage } from './pages/ProfilePage'

// Components
export { default as OnboardingGuard } from './components/OnboardingGuard'

// Store
export { useUserStore } from './store/userStore'

// API
export { userApi } from './api/userApi'
