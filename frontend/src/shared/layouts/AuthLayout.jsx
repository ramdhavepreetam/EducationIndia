/**
 * AuthLayout — shared layout for login, register, and onboarding pages.
 *
 * Renders a gradient background with a centered glassmorphism card.
 * The language toggle is positioned in the top-right corner.
 */
import { Outlet, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function AuthLayout() {
    const { t, i18n } = useTranslation()

    const toggleLanguage = () => {
        const next = i18n.language === 'en' ? 'mr' : 'en'
        i18n.changeLanguage(next)
        localStorage.setItem('sp_language', next)
    }

    return (
        <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800">
            {/* Decorative background orbs */}
            <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-brand-500/20 blur-3xl animate-float" />
            <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-accent-500/15 blur-3xl animate-float [animation-delay:3s]" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[30rem] h-[30rem] rounded-full bg-brand-400/10 blur-3xl" />

            {/* Home link */}
            <Link
                to="/"
                className="absolute top-6 left-6 z-20 px-4 py-2 rounded-xl
                   bg-white/10 backdrop-blur-md border border-white/20
                   text-white/90 text-sm font-medium
                   hover:bg-white/20 transition-all duration-200
                   flex items-center gap-2"
            >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                </svg>
                Home
            </Link>

            {/* Language toggle */}
            <button
                id="language-toggle"
                onClick={toggleLanguage}
                className="absolute top-6 right-6 z-20 px-4 py-2 rounded-xl
                   bg-white/10 backdrop-blur-md border border-white/20
                   text-white/90 text-sm font-medium
                   hover:bg-white/20 transition-all duration-200
                   flex items-center gap-2"
            >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.6 9h16.8M3.6 15h16.8" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a15.3 15.3 0 014 9 15.3 15.3 0 01-4 9 15.3 15.3 0 01-4-9 15.3 15.3 0 014-9z" />
                </svg>
                {i18n.language === 'en' ? t('language.mr') : t('language.en')}
            </button>

            {/* Main content — centered */}
            <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-12">
                {/* Logo / branding — links back to home */}
                <Link to="/" className="mb-8 text-center animate-fade-in block hover:opacity-90 transition-opacity">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-400 to-accent-500 shadow-glow mb-4">
                        <span className="text-2xl font-extrabold text-white">S</span>
                    </div>
                    <h1 className="text-2xl font-bold text-white">{t('app.name')}</h1>
                    <p className="mt-1 text-sm text-brand-200">{t('app.tagline')}</p>
                </Link>

                {/* Page content slot */}
                <div className="w-full max-w-md animate-slide-up">
                    <div className="glass-card p-8">
                        <Outlet />
                    </div>
                </div>
            </div>
        </div>
    )
}
