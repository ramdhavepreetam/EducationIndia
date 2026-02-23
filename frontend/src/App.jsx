/**
 * App root — route definitions + auth initialization.
 *
 * Calls authStore.initialize() once on mount to restore any existing
 * Supabase session and set up the auth state change listener.
 */
import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'
import { ProtectedRoute } from '@/modules/auth'
import { LoginPage, RegisterPage, OnboardingPage } from '@/modules/auth'
import AuthLayout from '@/shared/layouts/AuthLayout'
import AppLayout from '@/shared/layouts/AppLayout'

export default function App() {
    const initialize = useAuthStore((s) => s.initialize)
    const isLoading = useAuthStore((s) => s.isLoading)

    useEffect(() => {
        initialize()
    }, [initialize])

    // Global loading screen while auth initializes (covers OAuth redirect landing)
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-surface-50">
                <div className="flex flex-col items-center gap-4 animate-fade-in">
                    <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    <p className="text-surface-500 text-sm font-medium">Loading…</p>
                </div>
            </div>
        )
    }

    return (
        <Routes>
            {/* Root + catch-all: smart redirect based on auth state.
                Handles OAuth callback landing at "/" and any unknown routes. */}
            <Route index element={<AuthRedirect />} />
            <Route path="*" element={<AuthRedirect />} />

            {/* Public auth routes — redirect away if already authenticated */}
            <Route element={<AuthLayout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Protected routes — require authentication */}
            <Route element={<ProtectedRoute />}>
                {/* Onboarding uses AuthLayout (no sidebar yet) */}
                <Route element={<AuthLayout />}>
                    <Route path="/onboarding" element={<OnboardingPage />} />
                </Route>

                {/* Authenticated app routes — wrapped in AppLayout (sidebar + header) */}
                <Route element={<AppLayout />}>
                    <Route path="/dashboard" element={<DashboardPlaceholder />} />
                </Route>
            </Route>
        </Routes>
    )
}

/**
 * Smart redirect: sends the user to the right place based on auth state.
 * Used for "/" (OAuth callback landing) and "/*" (unknown routes).
 *   - Not authenticated          → /login
 *   - Authenticated, onboarded   → /dashboard
 *   - Authenticated, not yet     → /onboarding
 */
function AuthRedirect() {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
    const user = useAuthStore((s) => s.user)

    if (!isAuthenticated) return <Navigate to="/login" replace />
    if (!user?.is_onboarded) return <Navigate to="/onboarding" replace />
    return <Navigate to="/dashboard" replace />
}

/** Temporary placeholder until the dashboard module is built */
function DashboardPlaceholder() {
    const user = useAuthStore((s) => s.user)
    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold text-surface-900">
                Welcome, {user?.full_name || 'Student'} 🎓
            </h1>
            <p className="mt-2 text-surface-500">
                Dashboard module coming soon. Your auth is working!
            </p>
        </div>
    )
}
