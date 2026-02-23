/**
 * Auth module API — FastAPI calls only.
 *
 * ADR-001: Supabase handles login/register/OAuth. This file only covers
 * the backend endpoints that need a Supabase JWT to be present:
 *   - GET  /api/users/me                → fetch own user_profiles row
 *   - POST /api/users/me/complete-profile → onboarding step
 *
 * Social login and token issuance are handled by supabaseClient.js + authStore.
 */
import apiClient from '@/config/apiClient'

export const authApi = {
  /**
   * Fetch the authenticated user's profile from user_profiles (our DB).
   * Called after every login to get is_onboarded, role, preferred_language, etc.
   */
  getMe: () =>
    apiClient.get('/api/users/me').then((r) => r.data),

  /**
   * Onboarding step — sets school, district, std_class, preferred_language.
   * Flips is_onboarded = true on the backend.
   * @param {Object} data - { school_name, district, std_class?, medium?, preferred_language }
   */
  completeProfile: (data) =>
    apiClient.post('/api/users/me/complete-profile', data).then((r) => r.data),
}
