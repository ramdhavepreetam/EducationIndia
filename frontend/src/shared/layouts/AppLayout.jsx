/**
 * AppLayout — shell for authenticated app pages (dashboard, exams, etc.).
 *
 * Provides a sidebar, top header with user avatar + logout, and main content area.
 * Minimal for now — will be expanded when more modules are built.
 */
import { Outlet, useNavigate, NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'

export default function AppLayout() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const user = useAuthStore((s) => s.user)
    const logout = useAuthStore((s) => s.logout)

    const handleLogout = async () => {
        await logout()
        navigate('/login', { replace: true })
    }

    const isAdmin = ['exam_admin', 'super_admin'].includes(user?.role)

    const navItems = [
        { to: '/dashboard', label: t('nav.dashboard'), icon: DashboardIcon },
        { to: '/exams', label: t('nav.exams'), icon: ExamsIcon },
        { to: '/results', label: t('nav.results'), icon: ResultsIcon },
        { to: '/profile', label: t('nav.profile'), icon: ProfileIcon },
        ...(isAdmin ? [
            { to: '/admin', label: t('nav.adminPanel', 'Admin Panel'), icon: AdminIcon },
        ] : []),
    ]

    return (
        <div className="min-h-screen flex bg-surface-50">
            {/* Sidebar */}
            <aside className="hidden md:flex w-64 flex-col bg-white border-r border-surface-100">
                {/* Sidebar header */}
                <div className="h-16 flex items-center gap-3 px-6 border-b border-surface-100">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center">
                        <span className="text-sm font-extrabold text-white">S</span>
                    </div>
                    <span className="text-lg font-bold text-gradient">{t('app.name')}</span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                                    ? 'bg-brand-50 text-brand-700'
                                    : 'text-surface-500 hover:bg-surface-50 hover:text-surface-700'
                                }`
                            }
                        >
                            <item.icon />
                            {item.label}
                        </NavLink>
                    ))}
                </nav>

                {/* User section */}
                <div className="p-4 border-t border-surface-100">
                    <div className="flex items-center gap-3 px-4 py-2">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-sm">
                            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-surface-900 truncate">
                                {user?.full_name || 'Student'}
                            </p>
                            <p className="text-xs text-surface-400 truncate">
                                {user?.role || 'student'}
                            </p>
                        </div>
                    </div>
                    <button
                        id="logout-button"
                        onClick={handleLogout}
                        className="mt-2 w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                       text-red-500 hover:bg-red-50 transition-all duration-200"
                    >
                        <LogoutIcon />
                        {t('nav.logout')}
                    </button>
                </div>
            </aside>

            {/* Mobile header */}
            <div className="flex-1 flex flex-col">
                <header className="md:hidden h-16 flex items-center justify-between px-4 bg-white border-b border-surface-100">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center">
                            <span className="text-xs font-extrabold text-white">S</span>
                        </div>
                        <span className="text-base font-bold text-gradient">{t('app.name')}</span>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50 transition-colors"
                    >
                        {t('nav.logout')}
                    </button>
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-y-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}

/* ── Inline SVG Icons ─────────────────────────────────────────────────────── */

function DashboardIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
        </svg>
    )
}

function LogoutIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
        </svg>
    )
}

function ExamsIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
    )
}

function ResultsIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
        </svg>
    )
}

function ProfileIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
    )
}

function AdminIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
    )
}
