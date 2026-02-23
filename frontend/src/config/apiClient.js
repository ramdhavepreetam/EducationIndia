/**
 * Axios API client — shared singleton for all FastAPI calls.
 *
 * ADR-010 rules implemented here:
 *   - Request interceptor: attach JWT from authStore (getState() — not a hook)
 *   - Request interceptor: attach X-Language header for bilingual responses (ADR-003)
 *   - Response interceptor: 401 → auto logout + redirect to /login
 *
 * NOTE: This file imports useAuthStore which in turn imports authApi which
 * imports this file — a circular dependency. This is safe because all
 * cross-references are inside interceptor functions (called at runtime,
 * not at module init time). ES modules resolve circular deps lazily.
 */
import axios from 'axios'

// Lazily imported inside interceptors to avoid circular init issues
let _authStore = null
const getAuthStore = async () => {
  if (!_authStore) {
    const mod = await import('@/modules/auth/store/authStore')
    _authStore = mod.useAuthStore
  }
  return _authStore
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// ── Request interceptor ────────────────────────────────────────────────────
apiClient.interceptors.request.use(async (config) => {
  const store = await getAuthStore()
  const { token, user } = store.getState()

  // Attach JWT for FastAPI validation
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // ADR-003: tell the backend which language to resolve for bilingual content
  const lang =
    user?.preferred_language ||
    localStorage.getItem('sp_language') ||
    'en'
  config.headers['X-Language'] = lang

  return config
})

// ── Response interceptor ───────────────────────────────────────────────────
let _loggingOut = false

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 401 → session expired or token tampered — force logout once
    if (error.response?.status === 401 && !_loggingOut) {
      _loggingOut = true
      const store = await getAuthStore()
      store.getState().logout()         // clears store + Supabase session
      window.location.href = '/login'  // hard redirect, clears React state
    }
    return Promise.reject(error)
  }
)

export default apiClient
