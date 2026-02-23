/**
 * RegisterPage — email/password sign up + Google + Facebook OAuth.
 *
 * ADR-001: Supabase Auth handles sign up. DB trigger auto-creates user_profiles.
 * If auto-confirmed → redirect to /onboarding.
 * If email confirmation required → show "check your email" message.
 */
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/authStore'

export default function RegisterPage() {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const register = useAuthStore((s) => s.register)
    const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle)
    const loginWithFacebook = useAuthStore((s) => s.loginWithFacebook)

    const [fullName, setFullName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const [loading, setLoading] = useState(false)

    const validate = () => {
        if (!fullName || !email || !password || !confirmPassword) {
            setError(t('errors.required'))
            return false
        }
        if (password.length < 6) {
            setError(t('errors.passwordMin'))
            return false
        }
        if (password !== confirmPassword) {
            setError(t('register.passwordMismatch'))
            return false
        }
        return true
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setSuccess('')

        if (!validate()) return

        try {
            setLoading(true)
            const profile = await register(email, password, fullName)
            if (profile) {
                // Auto-confirmed — go to onboarding
                navigate('/onboarding', { replace: true })
            } else {
                // Email confirmation required
                setSuccess(t('register.checkEmail'))
            }
        } catch (err) {
            const msg = err?.message || t('errors.generic')
            setError(msg.includes('already registered') ? t('errors.emailTaken') : msg)
        } finally {
            setLoading(false)
        }
    }

    const handleOAuth = async (provider) => {
        try {
            setError('')
            if (provider === 'google') await loginWithGoogle()
            if (provider === 'facebook') await loginWithFacebook()
        } catch (err) {
            setError(err?.message || t('errors.generic'))
        }
    }

    return (
        <>
            {/* Header */}
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-surface-900">{t('register.title')}</h2>
                <p className="mt-1 text-sm text-surface-500">{t('register.subtitle')}</p>
            </div>

            {/* Error / Success messages */}
            {error && (
                <div className="mb-6 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 animate-fade-in">
                    {error}
                </div>
            )}
            {success && (
                <div className="mb-6 p-3 rounded-xl bg-green-50 border border-green-200 text-sm text-green-700 animate-fade-in">
                    {success}
                </div>
            )}

            {/* Registration form */}
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="register-name" className="input-label">{t('register.fullName')}</label>
                    <input
                        id="register-name"
                        type="text"
                        className="input-field"
                        placeholder={t('register.fullNamePlaceholder')}
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        autoComplete="name"
                    />
                </div>

                <div>
                    <label htmlFor="register-email" className="input-label">{t('register.email')}</label>
                    <input
                        id="register-email"
                        type="email"
                        className="input-field"
                        placeholder={t('register.emailPlaceholder')}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                    />
                </div>

                <div>
                    <label htmlFor="register-password" className="input-label">{t('register.password')}</label>
                    <input
                        id="register-password"
                        type="password"
                        className="input-field"
                        placeholder={t('register.passwordPlaceholder')}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="new-password"
                    />
                </div>

                <div>
                    <label htmlFor="register-confirm" className="input-label">{t('register.confirmPassword')}</label>
                    <input
                        id="register-confirm"
                        type="password"
                        className="input-field"
                        placeholder={t('register.confirmPasswordPlaceholder')}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        autoComplete="new-password"
                    />
                </div>

                <button
                    id="register-submit"
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full"
                >
                    {loading ? t('register.creating') : t('register.submit')}
                </button>
            </form>

            {/* Divider */}
            <div className="relative my-8">
                <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-surface-200" />
                </div>
                <div className="relative flex justify-center text-xs">
                    <span className="bg-white/70 px-4 text-surface-400 font-medium">
                        {t('register.or')}
                    </span>
                </div>
            </div>

            {/* Social sign-up buttons */}
            <div className="space-y-3">
                <button
                    id="register-google"
                    onClick={() => handleOAuth('google')}
                    className="btn-social"
                >
                    <GoogleIcon />
                    {t('register.google')}
                </button>

                <button
                    id="register-facebook"
                    onClick={() => handleOAuth('facebook')}
                    className="btn-social"
                >
                    <FacebookIcon />
                    {t('register.facebook')}
                </button>
            </div>

            {/* Login link */}
            <p className="mt-8 text-center text-sm text-surface-500">
                {t('register.hasAccount')}{' '}
                <Link
                    to="/login"
                    className="font-semibold text-brand-600 hover:text-brand-700 transition-colors"
                >
                    {t('register.login')}
                </Link>
            </p>
        </>
    )
}

/* ── Inline SVG Icons ─────────────────────────────────────────────────────── */

function GoogleIcon() {
    return (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
    )
}

function FacebookIcon() {
    return (
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#1877F2">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
    )
}
