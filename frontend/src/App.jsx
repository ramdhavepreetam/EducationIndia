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
import { LoginPage, RegisterPage } from '@/modules/auth'
import { OnboardingPage, ProfilePage, OnboardingGuard } from '@/modules/user'
import AuthLayout from '@/shared/layouts/AuthLayout'
import AppLayout from '@/shared/layouts/AppLayout'
import ErrorBoundary from '@/shared/components/ErrorBoundary'

/** Returns the correct landing page for a given user profile, based on role.
 *  Shared between AuthRedirect (OAuth callback) and LoginPage (email/password). */
export function getRoleHome(profile) {
    if (!profile?.is_onboarded) return '/onboarding'
    if (['exam_admin', 'super_admin'].includes(profile?.role)) return '/admin'
    if (profile?.role === 'parent') return '/parent'
    return '/dashboard'
}
import { ExamStartPage, ExamPage, ExamSubmittedPage } from '@/modules/attempt'
import { ResultPage } from '@/modules/analysis'
import { StudentDashboardPage } from '@/modules/dashboard'
import {
    AdminRoute,
    AdminDashboardPage,
    QuestionManagerPage,
    ExamPublisherPage,
    CreateTestPage,
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
    PaymentHistoryPage,
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
        <ErrorBoundary>
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

                    {/* Exam taking flow (full screen, no sidebar) — OnboardingGuard ensures
                        std_class and medium are set before the student enters an exam */}
                    <Route path="/exam/:examId/start" element={<ErrorBoundary><OnboardingGuard><ExamStartPage /></OnboardingGuard></ErrorBoundary>} />
                    <Route path="/exam/:examId/attempt" element={<ErrorBoundary><OnboardingGuard><ExamPage /></OnboardingGuard></ErrorBoundary>} />
                    <Route path="/exam/submitted/:id" element={<ErrorBoundary><OnboardingGuard><ExamSubmittedPage /></OnboardingGuard></ErrorBoundary>} />

                    {/* Exam result analysis */}
                    <Route path="/attempts/:attemptId/result" element={<ErrorBoundary><OnboardingGuard><ResultPage /></OnboardingGuard></ErrorBoundary>} />

                    {/* Authenticated app routes — wrapped in AppLayout (sidebar + header) */}
                    <Route element={<AppLayout />}>
                        <Route path="/dashboard" element={<ErrorBoundary><StudentDashboardPage /></ErrorBoundary>} />
                        {/* /exams and /results have no dedicated module yet — redirect to dashboard */}
                        <Route path="/exams" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/results" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/profile" element={<ErrorBoundary><OnboardingGuard><ProfilePage /></OnboardingGuard></ErrorBoundary>} />

                        {/* Payment routes — require onboarding */}
                        <Route path="/upgrade" element={<ErrorBoundary><OnboardingGuard><UpgradePage /></OnboardingGuard></ErrorBoundary>} />
                        <Route path="/payment/success" element={<ErrorBoundary><OnboardingGuard><PaymentSuccessPage /></OnboardingGuard></ErrorBoundary>} />
                        <Route path="/payment/failed" element={<ErrorBoundary><OnboardingGuard><PaymentFailedPage /></OnboardingGuard></ErrorBoundary>} />
                        <Route path="/payment/history" element={<ErrorBoundary><OnboardingGuard><PaymentHistoryPage /></OnboardingGuard></ErrorBoundary>} />

                        {/* Admin routes — guarded by AdminRoute + per-route ErrorBoundary */}
                        <Route path="/admin" element={<ErrorBoundary><AdminRoute><AdminDashboardPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/questions" element={<ErrorBoundary><AdminRoute><QuestionManagerPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/publish" element={<ErrorBoundary><AdminRoute><ExamPublisherPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/publish/create" element={<ErrorBoundary><AdminRoute><CreateTestPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/images" element={<ErrorBoundary><AdminRoute><ImageUploaderPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/stats" element={<ErrorBoundary><AdminRoute><StatsPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/settings" element={<ErrorBoundary><AdminRoute><AdminSettingsPage /></AdminRoute></ErrorBoundary>} />
                        <Route path="/admin/subscriptions" element={<ErrorBoundary><AdminRoute><AdminSubscriptionsPage /></AdminRoute></ErrorBoundary>} />

                        {/* Parent routes — guarded by ParentRoute + OnboardingGuard + per-route ErrorBoundary */}
                        <Route path="/parent" element={<ErrorBoundary><OnboardingGuard><ParentRoute><ParentDashboardPage /></ParentRoute></OnboardingGuard></ErrorBoundary>} />
                        <Route path="/parent/children/:studentId" element={<ErrorBoundary><OnboardingGuard><ParentRoute><ChildDetailPage /></ParentRoute></OnboardingGuard></ErrorBoundary>} />
                    </Route>
                </Route>
            </Routes>
        </ErrorBoundary>
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
    // Role-aware redirect: admin → /admin, parent → /parent, student → /dashboard
    return <Navigate to={getRoleHome(user)} replace />
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

