/**
 * App root — route definitions + auth initialization.
 *
 * Calls authStore.initialize() once on mount to restore any existing
 * Supabase session and set up the auth state change listener.
 */
import { Suspense, lazy, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'
import { ProtectedRoute } from '@/modules/auth'
import { LoginPage, RegisterPage } from '@/modules/auth'
import { OnboardingGuard } from '@/modules/user'
import AuthLayout from '@/shared/layouts/AuthLayout'
import AppLayout from '@/shared/layouts/AppLayout'
import ErrorBoundary from '@/shared/components/ErrorBoundary'
import LandingPage from '@/pages/LandingPage'
import { AdminRoute } from '@/modules/admin/components/AdminRoute'
import { TeacherRoute } from '@/modules/teacher/components/TeacherRoute'

/** Returns the correct landing page for a given user profile, based on role.
 *  Shared between AuthRedirect (OAuth callback) and LoginPage (email/password). */
export function getRoleHome(profile) {
    if (!profile?.is_onboarded) return '/onboarding'
    if (['exam_admin', 'super_admin'].includes(profile?.role)) return '/admin'
    if (profile?.role === 'parent') return '/parent'
    if (profile?.role === 'teacher') return '/teacher'
    return '/dashboard'
}

const lazyNamed = (loader, exportName) => lazy(() =>
    loader().then((module) => ({ default: module[exportName] }))
)

const OnboardingPage = lazy(() => import('@/modules/user/pages/OnboardingPage'))
const ProfilePage = lazy(() => import('@/modules/user/pages/ProfilePage'))

const ExamStartPage = lazyNamed(
    () => import('@/modules/attempt/pages/ExamStartPage'),
    'ExamStartPage'
)
const ExamPage = lazyNamed(
    () => import('@/modules/attempt/pages/ExamPage'),
    'ExamPage'
)
const ExamSubmittedPage = lazyNamed(
    () => import('@/modules/attempt/pages/ExamSubmittedPage'),
    'ExamSubmittedPage'
)
const ResultPage = lazyNamed(
    () => import('@/modules/analysis/pages/ResultPage'),
    'ResultPage'
)
const StudentDashboardPage = lazyNamed(
    () => import('@/modules/dashboard/pages/StudentDashboardPage'),
    'StudentDashboardPage'
)

const AdminDashboardPage = lazyNamed(
    () => import('@/modules/admin/pages/AdminDashboardPage'),
    'AdminDashboardPage'
)
const QuestionManagerPage = lazyNamed(
    () => import('@/modules/admin/pages/QuestionManagerPage'),
    'QuestionManagerPage'
)
const ExamPublisherPage = lazyNamed(
    () => import('@/modules/admin/pages/ExamPublisherPage'),
    'ExamPublisherPage'
)
const CreateTestPage = lazyNamed(
    () => import('@/modules/admin/pages/CreateTestPage'),
    'CreateTestPage'
)
const ImageUploaderPage = lazyNamed(
    () => import('@/modules/admin/pages/ImageUploaderPage'),
    'ImageUploaderPage'
)
const StatsPage = lazyNamed(
    () => import('@/modules/admin/pages/StatsPage'),
    'StatsPage'
)
const AdminSettingsPage = lazyNamed(
    () => import('@/modules/admin/pages/AdminSettingsPage'),
    'AdminSettingsPage'
)
const AdminSubscriptionsPage = lazyNamed(
    () => import('@/modules/admin/pages/AdminSubscriptionsPage'),
    'AdminSubscriptionsPage'
)

const ParentDashboardPage = lazy(() =>
    import('@/modules/parent/pages/ParentDashboardPage')
)
const ChildDetailPage = lazy(() =>
    import('@/modules/parent/pages/ChildDetailPage')
)

const TeacherDashboardPage = lazyNamed(
    () => import('@/modules/teacher/pages/TeacherDashboardPage'),
    'TeacherDashboardPage'
)
const TeacherStudentsPage = lazyNamed(
    () => import('@/modules/teacher/pages/TeacherStudentsPage'),
    'TeacherStudentsPage'
)
const AssignExamPage = lazyNamed(
    () => import('@/modules/teacher/pages/AssignExamPage'),
    'AssignExamPage'
)
const StudentResultsPage = lazyNamed(
    () => import('@/modules/teacher/pages/StudentResultsPage'),
    'StudentResultsPage'
)

const UpgradePage = lazyNamed(
    () => import('@/modules/payment/pages/UpgradePage'),
    'UpgradePage'
)
const PaymentSuccessPage = lazyNamed(
    () => import('@/modules/payment/pages/PaymentSuccessPage'),
    'PaymentSuccessPage'
)
const PaymentFailedPage = lazyNamed(
    () => import('@/modules/payment/pages/PaymentFailedPage'),
    'PaymentFailedPage'
)
const PaymentHistoryPage = lazyNamed(
    () => import('@/modules/payment/pages/PaymentHistoryPage'),
    'PaymentHistoryPage'
)

function RouteFallback() {
    return (
        <div className="min-h-[40vh] flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
        </div>
    )
}

function routeChunk(element) {
    return <Suspense fallback={<RouteFallback />}>{element}</Suspense>
}

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
                {/* Landing page: public for unauthenticated, redirect to app if logged in */}
                <Route index element={<LandingOrRedirect />} />
                {/* Catch-all for unknown routes */}
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
                        <Route path="/onboarding" element={routeChunk(<OnboardingPage />)} />
                    </Route>

                    {/* Exam taking flow (full screen, no sidebar) — OnboardingGuard ensures
                        std_class and medium are set before the student enters an exam */}
                    <Route path="/exam/:examId/start" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ExamStartPage /></OnboardingGuard>)}</ErrorBoundary>} />
                    <Route path="/exam/:examId/attempt" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ExamPage /></OnboardingGuard>)}</ErrorBoundary>} />
                    <Route path="/exam/submitted/:id" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ExamSubmittedPage /></OnboardingGuard>)}</ErrorBoundary>} />

                    {/* Exam result analysis */}
                    <Route path="/attempts/:attemptId/result" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ResultPage /></OnboardingGuard>)}</ErrorBoundary>} />

                    {/* Authenticated app routes — wrapped in AppLayout (sidebar + header) */}
                    <Route element={<AppLayout />}>
                        <Route path="/dashboard" element={<ErrorBoundary>{routeChunk(<StudentDashboardPage />)}</ErrorBoundary>} />
                        {/* /exams and /results have no dedicated module yet — redirect to dashboard */}
                        <Route path="/exams" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/results" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/profile" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ProfilePage /></OnboardingGuard>)}</ErrorBoundary>} />

                        {/* Payment routes — require onboarding */}
                        <Route path="/upgrade" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><UpgradePage /></OnboardingGuard>)}</ErrorBoundary>} />
                        <Route path="/payment/success" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><PaymentSuccessPage /></OnboardingGuard>)}</ErrorBoundary>} />
                        <Route path="/payment/failed" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><PaymentFailedPage /></OnboardingGuard>)}</ErrorBoundary>} />
                        <Route path="/payment/history" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><PaymentHistoryPage /></OnboardingGuard>)}</ErrorBoundary>} />

                        {/* Admin routes — guarded by AdminRoute + per-route ErrorBoundary */}
                        <Route path="/admin" element={<ErrorBoundary>{routeChunk(<AdminRoute><AdminDashboardPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/questions" element={<ErrorBoundary>{routeChunk(<AdminRoute><QuestionManagerPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/publish" element={<ErrorBoundary>{routeChunk(<AdminRoute><ExamPublisherPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/publish/create" element={<ErrorBoundary>{routeChunk(<AdminRoute><CreateTestPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/images" element={<ErrorBoundary>{routeChunk(<AdminRoute><ImageUploaderPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/stats" element={<ErrorBoundary>{routeChunk(<AdminRoute><StatsPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/settings" element={<ErrorBoundary>{routeChunk(<AdminRoute><AdminSettingsPage /></AdminRoute>)}</ErrorBoundary>} />
                        <Route path="/admin/subscriptions" element={<ErrorBoundary>{routeChunk(<AdminRoute><AdminSubscriptionsPage /></AdminRoute>)}</ErrorBoundary>} />

                        {/* Parent routes — guarded by ParentRoute + OnboardingGuard + per-route ErrorBoundary */}
                        <Route path="/parent" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ParentRoute><ParentDashboardPage /></ParentRoute></OnboardingGuard>)}</ErrorBoundary>} />
                        <Route path="/parent/children/:studentId" element={<ErrorBoundary>{routeChunk(<OnboardingGuard><ParentRoute><ChildDetailPage /></ParentRoute></OnboardingGuard>)}</ErrorBoundary>} />

                        {/* Teacher routes — guarded by TeacherRoute */}
                        <Route path="/teacher" element={<ErrorBoundary>{routeChunk(<TeacherRoute><TeacherDashboardPage /></TeacherRoute>)}</ErrorBoundary>} />
                        <Route path="/teacher/students" element={<ErrorBoundary>{routeChunk(<TeacherRoute><TeacherStudentsPage /></TeacherRoute>)}</ErrorBoundary>} />
                        <Route path="/teacher/assign" element={<ErrorBoundary>{routeChunk(<TeacherRoute><AssignExamPage /></TeacherRoute>)}</ErrorBoundary>} />
                        <Route path="/teacher/students/:studentId" element={<ErrorBoundary>{routeChunk(<TeacherRoute><StudentResultsPage /></TeacherRoute>)}</ErrorBoundary>} />
                    </Route>
                </Route>
            </Routes>
        </ErrorBoundary>
    )
}

/**
 * Landing gate: shows LandingPage to unauthenticated users.
 * Authenticated users go directly to their role-home page.
 * While auth is initializing, shows the landing page (avoids flash redirect).
 */
function LandingOrRedirect() {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
    const isLoading = useAuthStore((s) => s.isLoading)
    const user = useAuthStore((s) => s.user)

    // Auth still initializing → show landing page (not a blank spinner)
    if (isLoading) return <LandingPage />
    // Logged-in → go to their role home
    if (isAuthenticated) return <Navigate to={getRoleHome(user)} replace />
    // Not logged in → show the marketing landing page
    return <LandingPage />
}

/**
 * Smart redirect: sends the user to the right place based on auth state.
 * Used for "/*" (unknown routes).
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
