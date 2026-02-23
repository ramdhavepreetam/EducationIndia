/**
 * OnboardingPage — collects student profile info after first login.
 *
 * Fields: school_name, district, std_class (5/8), medium, preferred_language.
 * Calls authApi.completeProfile() → flips is_onboarded = true on backend.
 * Redirects to /dashboard on success.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/authApi'

export default function OnboardingPage() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const updateUser = useAuthStore((s) => s.updateUser)
    const setLanguage = useAuthStore((s) => s.setLanguage)

    const [form, setForm] = useState({
        school_name: '',
        district: '',
        std_class: '',
        medium: '',
        preferred_language: i18n.language,
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (field) => (e) => {
        setForm((prev) => ({ ...prev, [field]: e.target.value }))
    }

    const handleLanguageChange = (e) => {
        const lang = e.target.value
        setForm((prev) => ({ ...prev, preferred_language: lang }))
        i18n.changeLanguage(lang)
        localStorage.setItem('sp_language', lang)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        if (!form.school_name || !form.district || !form.std_class) {
            setError(t('errors.required'))
            return
        }

        try {
            setLoading(true)
            const payload = {
                school_name: form.school_name,
                district: form.district,
                std_class: parseInt(form.std_class, 10),
                medium: form.medium || undefined,
                preferred_language: form.preferred_language,
            }
            await authApi.completeProfile(payload)
            updateUser({ is_onboarded: true, ...payload })
            setLanguage(form.preferred_language)
            navigate('/dashboard', { replace: true })
        } catch (err) {
            setError(err?.response?.data?.detail || err?.message || t('errors.generic'))
        } finally {
            setLoading(false)
        }
    }

    return (
        <>
            {/* Header */}
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-surface-900">{t('onboarding.title')}</h2>
                <p className="mt-1 text-sm text-surface-500">{t('onboarding.subtitle')}</p>
            </div>

            {/* Error */}
            {error && (
                <div className="mb-6 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 animate-fade-in">
                    {error}
                </div>
            )}

            {/* Onboarding form */}
            <form onSubmit={handleSubmit} className="space-y-5">
                {/* School name */}
                <div>
                    <label htmlFor="onboard-school" className="input-label">{t('onboarding.schoolName')}</label>
                    <input
                        id="onboard-school"
                        type="text"
                        className="input-field"
                        placeholder={t('onboarding.schoolNamePlaceholder')}
                        value={form.school_name}
                        onChange={handleChange('school_name')}
                    />
                </div>

                {/* District */}
                <div>
                    <label htmlFor="onboard-district" className="input-label">{t('onboarding.district')}</label>
                    <input
                        id="onboard-district"
                        type="text"
                        className="input-field"
                        placeholder={t('onboarding.districtPlaceholder')}
                        value={form.district}
                        onChange={handleChange('district')}
                    />
                </div>

                {/* Standard / Class */}
                <div>
                    <label htmlFor="onboard-class" className="input-label">{t('onboarding.stdClass')}</label>
                    <select
                        id="onboard-class"
                        className="input-field"
                        value={form.std_class}
                        onChange={handleChange('std_class')}
                    >
                        <option value="" disabled>{t('onboarding.stdClassPlaceholder')}</option>
                        <option value="5">{t('onboarding.class5')}</option>
                        <option value="8">{t('onboarding.class8')}</option>
                    </select>
                </div>

                {/* Medium of study */}
                <div>
                    <label htmlFor="onboard-medium" className="input-label">{t('onboarding.medium')}</label>
                    <select
                        id="onboard-medium"
                        className="input-field"
                        value={form.medium}
                        onChange={handleChange('medium')}
                    >
                        <option value="" disabled>{t('onboarding.mediumPlaceholder')}</option>
                        <option value="english">{t('onboarding.mediumEnglish')}</option>
                        <option value="marathi">{t('onboarding.mediumMarathi')}</option>
                        <option value="semi_english">{t('onboarding.mediumSemiEnglish')}</option>
                    </select>
                </div>

                {/* Preferred language */}
                <div>
                    <label htmlFor="onboard-lang" className="input-label">{t('onboarding.preferredLanguage')}</label>
                    <div className="flex gap-3">
                        <label className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition-all duration-200 ${form.preferred_language === 'en'
                                ? 'border-brand-400 bg-brand-50 text-brand-700 shadow-sm'
                                : 'border-surface-200 bg-white text-surface-600 hover:border-surface-300'
                            }`}>
                            <input
                                type="radio"
                                name="preferred_language"
                                value="en"
                                checked={form.preferred_language === 'en'}
                                onChange={handleLanguageChange}
                                className="sr-only"
                            />
                            <span className="text-sm font-medium">{t('onboarding.languageEn')}</span>
                        </label>
                        <label className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition-all duration-200 ${form.preferred_language === 'mr'
                                ? 'border-brand-400 bg-brand-50 text-brand-700 shadow-sm'
                                : 'border-surface-200 bg-white text-surface-600 hover:border-surface-300'
                            }`}>
                            <input
                                type="radio"
                                name="preferred_language"
                                value="mr"
                                checked={form.preferred_language === 'mr'}
                                onChange={handleLanguageChange}
                                className="sr-only"
                            />
                            <span className="text-sm font-medium">{t('onboarding.languageMr')}</span>
                        </label>
                    </div>
                </div>

                <button
                    id="onboard-submit"
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full mt-2"
                >
                    {loading ? t('onboarding.saving') : t('onboarding.submit')}
                </button>
            </form>
        </>
    )
}
