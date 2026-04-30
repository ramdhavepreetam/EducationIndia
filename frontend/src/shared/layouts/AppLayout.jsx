/**
 * AppLayout — shell for authenticated app pages (dashboard, exams, etc.).
 *
 * Provides a sidebar, top header with user avatar + logout, and main content area.
 * Minimal for now — will be expanded when more modules are built.
 */
import { Outlet, useNavigate, NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useEffect, useState } from 'react'
import { useAuthStore } from '@/modules/auth'
import { SubscriptionStatus, usePaymentStore } from '@/modules/payment'

export default function AppLayout() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const user = useAuthStore((s) => s.user)
    const logout = useAuthStore((s) => s.logout)
    const { loadStatus } = usePaymentStore()

    const isAdmin = ['exam_admin', 'super_admin'].includes(user?.role)
    const isParent = user?.role === 'parent'

    useEffect(() => {
        if (!isParent) return

        loadStatus()

        const refreshStatus = () => {
            if (document.visibilityState === 'visible') {
                loadStatus()
            }
        }

        window.addEventListener('focus', loadStatus)
        document.addEventListener('visibilitychange', refreshStatus)

        return () => {
            window.removeEventListener('focus', loadStatus)
            document.removeEventListener('visibilitychange', refreshStatus)
        }
    }, [isParent, loadStatus])

    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen)
    const closeMobileMenu = () => setIsMobileMenuOpen(false)

    const handleLogout = async () => {
        await logout()
        navigate('/login', { replace: true })
    }

    const navItems = isAdmin ? [
        { to: '/admin', label: t('nav.dashboard', 'Dashboard'), icon: DashboardIcon },
        { to: '/admin/questions', label: 'Questions', icon: ExamsIcon },
        { to: '/admin/publish', label: 'Publish Exams', icon: ResultsIcon },
        { to: '/admin/subscriptions', label: 'Subscriptions', icon: SubscriptionsIcon },
        { to: '/admin/settings', label: 'Settings', icon: SettingsIcon },
        { to: '/admin/stats', label: 'Stats', icon: ProfileIcon },
        { to: '/admin/images', label: 'Images', icon: AdminIcon },
    ] : isParent ? [
        { to: '/parent', label: 'Dashboard', icon: DashboardIcon },
        { to: '/payment/history', label: 'Payment History', icon: SubscriptionsIcon },
        { to: '/profile', label: t('nav.profile', 'Profile'), icon: SettingsIcon },
    ] : [
        { to: '/dashboard', label: t('nav.dashboard'), icon: DashboardIcon },
        { to: '/exams', label: t('nav.exams'), icon: ExamsIcon },
        { to: '/results', label: t('nav.results'), icon: ResultsIcon },
        { to: '/profile', label: t('nav.profile'), icon: ProfileIcon },
    ]

    return (
        <div className="min-h-screen flex bg-surface-50">
            {/* Mobile menu overlay */}
            {isMobileMenuOpen && (
                <div 
                    data-testid="mobile-overlay"
                    className="fixed inset-0 bg-gray-800 bg-opacity-50 z-40 md:hidden transition-opacity"
                    onClick={closeMobileMenu}
                />
            )}

            {/* Sidebar */}
            <aside className={`flex flex-col w-64 bg-white border-r border-surface-100 fixed md:static inset-y-0 left-0 z-50 transform transition-transform duration-300 md:transform-none ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
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
                            onClick={closeMobileMenu}
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
                    {/* Subscription badge (desktop) */}
                    {isParent && (
                        <div className="mb-4 px-2">
                            <SubscriptionStatus />
                        </div>
                    )}
                    <div className="flex items-center gap-3 px-4 py-2">
                        {user?.avatar_url
                          ? <img src={user.avatar_url}
                                 alt={user?.full_name || 'Avatar'}
                                 className="w-9 h-9 rounded-full object-cover ring-2 ring-surface-100" />
                          : <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-sm">
                                {user?.full_name
                                  ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                                  : 'U'}
                            </div>
                        }
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-surface-900 truncate">
                                {user?.full_name || 'Student'}
                            </p>
                            <p className="text-xs text-surface-400 truncate">
                                {user?.email || user?.role || 'student'}
                            </p>
                            {user?.email && (
                                <p className="text-[11px] text-surface-300 truncate">
                                    {user?.role || 'student'}
                                </p>
                            )}
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
            <div className="flex-1 flex flex-col min-w-0">
                <header className="md:hidden h-16 flex items-center justify-between px-4 bg-white border-b border-surface-100 sticky top-0 z-30">
                    <div className="flex items-center gap-2">
                        <button 
                            onClick={toggleMobileMenu}
                            aria-label="Open menu"
                            className="p-2 -ml-2 rounded-lg text-surface-500 hover:bg-surface-50 focus:outline-none focus:ring-2 focus:ring-brand-500"
                        >
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                        <div className="w-8 h-8 ml-1 rounded-lg bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center">
                            <span className="text-xs font-extrabold text-white">S</span>
                        </div>
                        <span className="text-base font-bold text-gradient">{t('app.name')}</span>
                    </div>
                    <div className="flex items-center gap-3">
                        {isParent && <SubscriptionStatus />}
                        <button
                            onClick={handleLogout}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50 transition-colors"
                        >
                            {t('nav.logout')}
                        </button>
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-y-auto">
                    <Outlet />
                </main>

                {/* Disclaimer footer */}
                <footer className="px-4 py-2 bg-surface-50 border-t border-surface-100">
                    <p className="text-xs text-surface-400 text-center leading-relaxed">
                        ScholarPath is a practice platform only. It does not guarantee any exam outcome, score, or selection.
                        All results are for self-assessment purposes only and have no official standing.
                    </p>
                </footer>
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

function SubscriptionsIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
        </svg>
    )
}

function SettingsIcon() {
    return (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
    )
}
