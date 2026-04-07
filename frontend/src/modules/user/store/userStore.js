/**
 * User module Zustand store — profile management state.
 *
 * ADR-010: one store per module, always include isLoading + error + reset().
 * After profile edits, syncs back to authStore via updateUser().
 */
import { create } from 'zustand'
import { userApi } from '../api/userApi'
import { useAuthStore } from '@/modules/auth'

export const useUserStore = create((set, get) => ({
  profile:      null,      // ProfileResponse
  isLoading:    false,
  isSaving:     false,
  saveSuccess:  false,
  error:        null,

  loadProfile: async () => {
    set({ isLoading: true })
    try {
      const profile = await userApi.getMe()
      set({ profile, isLoading: false })
    } catch {
      set({ isLoading: false })
    }
  },

  updateProfile: async (data) => {
    set({ isSaving: true, saveSuccess: false, error: null })
    try {
      const profile = await userApi.updateMe(data)
      set({ profile, isSaving: false, saveSuccess: true })

      // Sync back to authStore so nav/header reflects new name/avatar
      useAuthStore.getState().updateUser(profile)

      // Auto-clear success flag after 3 seconds
      setTimeout(() => set({ saveSuccess: false }), 3000)

      return { success: true }
    } catch (err) {
      const message = err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Update failed'
      set({ isSaving: false, error: message })
      return { success: false, error: message }
    }
  },

  uploadAvatar: async (file) => {
    set({ isSaving: true, error: null })
    try {
      const profile = await userApi.uploadAvatar(file)
      set({ profile, isSaving: false })
      useAuthStore.getState().updateUser(profile)
      return { success: true }
    } catch (err) {
      const message = err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Upload failed'
      set({ isSaving: false, error: message })
      return { success: false }
    }
  },

  changePassword: async (data) => {
    set({ isSaving: true, error: null })
    try {
      await userApi.changePassword(data)
      set({ isSaving: false })
      return { success: true }
    } catch (err) {
      const message = err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Password change failed'
      set({ isSaving: false, error: message })
      return { success: false, error: message }
    }
  },

  completeOnboarding: async (data) => {
    // Sends profile data + is_onboarded=true in one call
    return await get().updateProfile({ ...data, is_onboarded: true })
  },

  reset: () => set({ profile: null, error: null, saveSuccess: false })
}))
