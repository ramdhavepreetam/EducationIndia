/**
 * OnboardingGuard — wraps protected routes that require onboarding.
 *
 * Redirects to /onboarding if user.is_onboarded is false.
 * Shows a loading spinner while profile is still loading.
 *
 * /onboarding route itself must NOT be wrapped by this guard
 * (otherwise → infinite redirect loop).
 */
import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'
import { useUserStore } from '../store/userStore'

export default function OnboardingGuard({ children }) {
  const user    = useAuthStore((s) => s.user)
  const profile = useUserStore((s) => s.profile)
  const loadProfile = useUserStore((s) => s.loadProfile)

  // Load profile if user is logged in but profile not yet loaded
  useEffect(() => {
    if (user && !profile) {
      loadProfile()
    }
  }, [user, profile, loadProfile])

  // Not authenticated — ProtectedRoute handles this, but just in case
  if (!user) return <Navigate to="/login" replace />

  // Profile still loading — show spinner
  if (!profile) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // Not onboarded — redirect to onboarding
  if (!profile.is_onboarded) {
    return <Navigate to="/onboarding" replace />
  }

  return children
}
