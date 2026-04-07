/**
 * Auth store — the single source of truth for authentication state.
 *
 * ADR-010 shape: { user, token, isAuthenticated, isLoading, login(), logout() }
 * ADR-001: Supabase issues JWTs; we only store them. FastAPI validates them.
 *
 * IMPORTANT: Call `useAuthStore.getState().initialize()` once on app load
 * (in App.jsx useEffect). This sets up the Supabase auth listener and
 * hydrates the store from any existing session (handles page refresh + OAuth redirect).
 *
 * Token flow:
 *   1. set({ token }) synchronously BEFORE calling authApi.getMe()
 *   2. apiClient reads getState().token in its request interceptor
 *   3. This ordering ensures the token is available when the first API call fires
 */
import { create } from 'zustand'
import { supabase } from '@/config/supabaseClient'
import { authApi } from '../api/authApi'

export const useAuthStore = create((set, get) => ({
  user: null,            // user_profiles row from our backend
  token: null,           // Supabase access_token (JWT sent to FastAPI)
  isAuthenticated: false,
  isLoading: true,       // true until initialize() completes — ProtectedRoute shows spinner

  // ── Initialization ────────────────────────────────────────────────────────

  /**
   * Call once on app mount. Restores session from Supabase (handles page
   * refresh and OAuth redirects) and sets up the auth state change listener.
   */
  initialize: async () => {
    set({ isLoading: true })

    try {
      // Restore existing session (also exchanges OAuth tokens from URL hash)
      const { data: { session } } = await supabase.auth.getSession()

      if (session) {
        // Set token first so apiClient can attach it to the getMe() call
        set({ token: session.access_token })
        const profile = await authApi.getMe()
        set({ user: profile, isAuthenticated: true })
        if (profile.preferred_language) {
          localStorage.setItem('sp_language', profile.preferred_language)
        }
      }
    } catch {
      // Session exists in Supabase but backend profile fetch failed
      // (e.g. profile not yet created, or backend down) — log out cleanly
      set({ user: null, token: null, isAuthenticated: false })
    } finally {
      set({ isLoading: false })
    }

    // Listen for all future auth changes (OAuth return, token refresh, sign-out)
    supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        // Avoid re-fetching if already authenticated with same token
        if (get().token === session.access_token) return

        set({ token: session.access_token, isLoading: true })
        try {
          const profile = await authApi.getMe()
          set({ user: profile, isAuthenticated: true, isLoading: false })
          if (profile.preferred_language) {
            localStorage.setItem('sp_language', profile.preferred_language)
          }
        } catch {
          set({ isLoading: false })
        }
      } else if (event === 'TOKEN_REFRESHED' && session) {
        // Silently update token on background refresh — no profile re-fetch needed
        set({ token: session.access_token })
      } else if (event === 'SIGNED_OUT') {
        set({ user: null, token: null, isAuthenticated: false, isLoading: false })
        localStorage.removeItem('sp_language')
      }
    })
  },

  // ── Auth actions ──────────────────────────────────────────────────────────

  /**
   * Email + password sign in. Returns the user profile on success.
   * Throws the Supabase error on failure (caught in LoginPage).
   */
  login: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error

    // Set token before profile fetch (apiClient reads it synchronously)
    set({ token: data.session.access_token })
    const profile = await authApi.getMe()
    set({ user: profile, isAuthenticated: true })
    if (profile.preferred_language) {
      localStorage.setItem('sp_language', profile.preferred_language)
    }
    return profile
  },

  /**
   * Google OAuth — triggers redirect. No return value.
   * After redirect back, onAuthStateChange fires and hydrates the store.
   */
  loginWithGoogle: async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/`,
      },
    })
    if (error) throw error
  },

  /**
   * Facebook OAuth — triggers redirect. No return value.
   */
  loginWithFacebook: async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'facebook',
      options: {
        redirectTo: `${window.location.origin}/`,
      },
    })
    if (error) throw error
  },

  /**
   * Email + name sign up (creates Supabase auth.users row).
   * The on_auth_user_created DB trigger auto-creates user_profiles.
   * Returns the Supabase user (not the backend profile — not yet onboarded).
   *
   * TODO [PRODUCTION]: Re-enable email confirmation in Supabase Auth settings
   * and set up a custom SMTP provider (SendGrid/Resend). The built-in Supabase
   * mailer is rate-limited to 4 emails/hr and emails often land in spam.
   * Currently disabled for dev/testing convenience.
   */
  register: async (email, password, fullName) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        // ADR-014: Registration is for parents. Students are child_profiles.
        data: { full_name: fullName, role: 'parent' },
      },
    })
    if (error) throw error

    if (data.session) {
      // Auto-confirmed (email confirmation disabled) — log in immediately
      set({ token: data.session.access_token })
      const profile = await authApi.getMe()
      set({ user: profile, isAuthenticated: true })
      return profile
    }
    // Email confirmation required — return null, show "check your email" message
    return null
  },

  /**
   * Sign out from Supabase and clear all local state.
   * Called by components AND by apiClient on 401 (not awaited in that case).
   */
  logout: async () => {
    await supabase.auth.signOut()
    set({ user: null, token: null, isAuthenticated: false })
    localStorage.removeItem('sp_language')
  },

  // ── Store helpers ─────────────────────────────────────────────────────────

  /** Merge updates into the user object — called after profile edits. */
  updateUser: (updates) => {
    set((state) => ({
      user: state.user ? { ...state.user, ...updates } : state.user,
    }))
  },

  /** Change preferred language and persist to localStorage. */
  setLanguage: (lang) => {
    localStorage.setItem('sp_language', lang)
    set((state) => ({
      user: state.user ? { ...state.user, preferred_language: lang } : state.user,
    }))
  },
}))
