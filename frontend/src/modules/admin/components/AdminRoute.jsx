import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'
import { useTranslation } from 'react-i18next'

const ADMIN_ROLES = ['exam_admin', 'super_admin']

/**
 * AdminRoute — wraps admin pages.
 * Redirects to /dashboard if user role is not exam_admin or super_admin.
 * Shows Access Denied for authenticated non-admins (vs ProtectedRoute for unauthenticated).
 */
export function AdminRoute({ children }) {
    const { t } = useTranslation()
    const user = useAuthStore(s => s.user)
    const isAuthenticated = useAuthStore(s => s.isAuthenticated)

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    if (!ADMIN_ROLES.includes(user?.role)) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-surface-50">
                <div className="max-w-md w-full bg-white rounded-2xl shadow-card p-8 text-center">
                    <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                    </div>
                    <h1 className="text-xl font-bold text-surface-900 mb-2">
                        {t('admin.accessDenied', 'Access Denied')}
                    </h1>
                    <p className="text-surface-500 text-sm mb-6">
                        {t('admin.accessDeniedMsg', 'This section is only available to exam administrators.')}
                    </p>
                    <a href="/dashboard"
                        className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 transition-colors">
                        {t('admin.backToDashboard', 'Back to Dashboard')}
                    </a>
                </div>
            </div>
        )
    }

    return children
}
