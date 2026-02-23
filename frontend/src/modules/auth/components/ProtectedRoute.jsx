/**
 * ProtectedRoute — guards routes that require authentication.
 *
 * ADR-010: Reads authStore.isAuthenticated + isLoading.
 *   - Loading  → spinner (while initialize() hydrates session)
 *   - No token → redirect to /login
 *   - Valid    → render child routes via <Outlet />
 */
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute() {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
    const isLoading = useAuthStore((s) => s.isLoading)

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-surface-50">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    <p className="text-surface-500 text-sm font-medium">Loading…</p>
                </div>
            </div>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return <Outlet />
}
