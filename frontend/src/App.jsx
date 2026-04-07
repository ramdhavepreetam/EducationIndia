/**
 * App root — route definitions + auth initialization.
 *
 * Calls authStore.initialize() once on mount to restore any existing
 * Supabase session and set up the auth state change listener.
 */
import { useEffect } from 'react'
import { Routes, Route, Navigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'
import { ProtectedRoute } from '@/modules/auth'
import { LoginPage, RegisterPage } from '@/modules/auth'
import { OnboardingPage, ProfilePage, OnboardingGuard } from '@/modules/user'
import AuthLayout from '@/shared/layouts/AuthLayout'
import AppLayout from '@/shared/layouts/AppLayout'
import { ExamStartPage, ExamPage, ExamSubmittedPage } from '@/modules/attempt'
import { ResultPage } from '@/modules/analysis'
import { StudentDashboardPage } from '@/modules/dashboard'
import {
    AdminRoute,
    AdminDashboardPage,
    QuestionManagerPage,
    ExamPublisherPage,
    ImageUploaderPage,
    StatsPage,
    AdminSettingsPage,
    AdminSubscriptionsPage,
} from '@/modules/admin'
import {
    ParentDashboardPage,
    ChildDetailPage,
} from '@/modules/parent'
import {
    UpgradePage,
    PaymentSuccessPage,
    PaymentFailedPage,
} from '@/modules/payment'

export default function App() {
    const initialize = useAuthStore((s) => s.initialize)

    useEffect(() => {
        initialize()
    }, [initialize])

    // NOTE: No global spinner here — public routes (/login, /register) must
    // always render immediately. isLoading guard lives in ProtectedRoute and
    // AuthRedirect only, so Supabase init latency never blocks auth pages.
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

                {/* Exam taking flow (full screen, no sidebar) */}
                <Route path="/exam/:examId/start" element={<ExamStartPage />} />
                <Route path="/exam/:examId/attempt" element={<ExamPage />} />
                <Route path="/exam/submitted/:id" element={<ExamSubmittedPage />} />

                {/* Exam result analysis (full screen container, might want sidebar later but keeping consistent with attempt for now) */}
                <Route path="/attempts/:attemptId/result" element={<ResultPage />} />

                {/* Authenticated app routes — wrapped in AppLayout (sidebar + header) */}
                <Route element={<AppLayout />}>
                    <Route path="/dashboard" element={<StudentDashboardPage />} />
                    <Route path="/exams" element={<GenericPlaceholder title="Exams" />} />
                    <Route path="/results" element={<GenericPlaceholder title="Results" />} />
                    <Route path="/profile" element={<OnboardingGuard><ProfilePage /></OnboardingGuard>} />

                    {/* Payment routes — require onboarding */}
                    <Route path="/upgrade" element={<OnboardingGuard><UpgradePage /></OnboardingGuard>} />
                    <Route path="/payment/success" element={<OnboardingGuard><PaymentSuccessPage /></OnboardingGuard>} />
                    <Route path="/payment/failed" element={<OnboardingGuard><PaymentFailedPage /></OnboardingGuard>} />

                    {/* Admin routes — guarded by AdminRoute (redirects non-admins) */}
                    <Route path="/admin" element={<AdminRoute><AdminDashboardPage /></AdminRoute>} />
                    <Route path="/admin/questions" element={<AdminRoute><QuestionManagerPage /></AdminRoute>} />
                    <Route path="/admin/publish" element={<AdminRoute><ExamPublisherPage /></AdminRoute>} />
                    <Route path="/admin/images" element={<AdminRoute><ImageUploaderPage /></AdminRoute>} />
                    <Route path="/admin/stats" element={<AdminRoute><StatsPage /></AdminRoute>} />
                    <Route path="/admin/settings" element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
                    <Route path="/admin/subscriptions" element={<AdminRoute><AdminSubscriptionsPage /></AdminRoute>} />

                    {/* Parent routes — guarded by ParentRoute + OnboardingGuard */}
                    <Route path="/parent" element={<OnboardingGuard><ParentRoute><ParentDashboardPage /></ParentRoute></OnboardingGuard>} />
                    <Route path="/parent/children/:studentId" element={<OnboardingGuard><ParentRoute><ChildDetailPage /></ParentRoute></OnboardingGuard>} />
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
    const isLoading = useAuthStore((s) => s.isLoading)
    const user = useAuthStore((s) => s.user)

    // Wait for auth init before redirecting (handles OAuth callback landing at "/")
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-surface-50">
                <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
            </div>
        )
    }
    if (!isAuthenticated) return <Navigate to="/login" replace />
    if (!user?.is_onboarded) return <Navigate to="/onboarding" replace />
    return <Navigate to="/dashboard" replace />
}

/**
 * ParentRoute — wraps parent-only pages.
 * Redirects unauthenticated users to /login.
 * Redirects authenticated non-parents to /dashboard.
 */
function ParentRoute({ children }) {
    const user = useAuthStore((s) => s.user)
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

    if (!isAuthenticated) return <Navigate to="/login" replace />
    if (user?.role !== 'parent') return <Navigate to="/dashboard" replace />
    return children
}

/** Placeholder for missing modules (Exams, Results, Profile) */
function GenericPlaceholder({ title }) {
    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold text-surface-900 mb-4">{title}</h1>
            <p className="mt-2 text-surface-500 mb-8">
                The {title} module is coming soon or handled directly by the Dashboard right now.
            </p>
            <div className="p-6 bg-white border border-brand-200 rounded-xl shadow-sm max-w-md">
                <Link
                    to="/dashboard"
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-surface-100 text-surface-700 font-bold rounded-lg hover:bg-surface-200 transition"
                >
                    Back to Dashboard
                </Link>
            </div>
        </div>
    )
}
