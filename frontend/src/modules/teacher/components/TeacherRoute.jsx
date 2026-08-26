import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/modules/auth'

export function TeacherRoute({ children }) {
    const user = useAuthStore((s) => s.user)
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

    if (!isAuthenticated) return <Navigate to="/login" replace />
    if (user?.role !== 'teacher') return <Navigate to="/dashboard" replace />
    return children
}
