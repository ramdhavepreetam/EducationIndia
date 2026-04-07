/**
 * OnboardingPage — 3-step wizard shown once for new parents.
 *
 * Step 1: Welcome — name + phone
 * Step 2: Child context — class, district, school
 * Step 3: Language — large card picker
 *
 * Calls completeOnboarding({ ...allData, is_onboarded: true }).
 * Redirects to /parent on success. Cannot be skipped.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useUserStore } from '../store/userStore'
import LanguagePicker from '../components/LanguagePicker'

export default function OnboardingPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const completeOnboarding = useUserStore((s) => s.completeOnboarding)

  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    full_name:          user?.full_name || '',
    phone:              '',
    std_class:          null,
    district:           '',
    school_name:        '',
    preferred_language: user?.preferred_language || i18n.language || 'en',
  })

  const updateField = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }))
    setError('')
  }

  // Step validations
  const canProceedStep1 = formData.full_name.trim().length >= 2
  const canComplete     = formData.preferred_language !== null

  const handleNext = () => {
    if (step === 1 && !canProceedStep1) {
      setError(t('profile.nameRequired', 'Please enter your name (min 2 characters)'))
      return
    }
    setError('')
    setStep(s => s + 1)
  }

  const handleBack = () => {
    setError('')
    setStep(s => s - 1)
  }

  const handleComplete = async () => {
    setError('')
    setLoading(true)
    try {
      // Change i18n language
      i18n.changeLanguage(formData.preferred_language)
      localStorage.setItem('sp_language', formData.preferred_language)

      // Build payload — only include non-empty fields
      const payload = {
        full_name: formData.full_name.trim(),
        preferred_language: formData.preferred_language,
      }
      if (formData.phone.trim()) payload.phone = formData.phone.trim()
      if (formData.std_class)    payload.std_class = formData.std_class
      if (formData.district.trim())    payload.district = formData.district.trim()
      if (formData.school_name.trim()) payload.school_name = formData.school_name.trim()

      const result = await completeOnboarding(payload)
      if (result.success) {
        navigate('/parent', { replace: true })
      } else {
        setError(result.error || t('errors.generic'))
      }
    } catch (err) {
      setError(err?.message || t('errors.generic'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between text-xs text-surface-400 mb-2">
          <span>Step {step} of 3</span>
        </div>
        <div className="w-full h-2 bg-surface-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-accent-500 rounded-full transition-all duration-500"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 animate-fade-in">
          {error}
        </div>
      )}

      {/* ─── STEP 1: Welcome + Name + Phone ─── */}
      {step === 1 && (
        <div className="animate-fade-in">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">🎉</div>
            <h2 className="text-2xl font-bold text-surface-900">
              {t('onboarding.welcomeTitle', 'Welcome to ScholarPath!')}
            </h2>
            <p className="mt-1 text-sm text-surface-500">
              {t('onboarding.welcomeDesc', "Let's set up your account. Takes 2 minutes.")}
            </p>
          </div>

          <div className="space-y-5">
            <div>
              <label htmlFor="onboard-name" className="input-label">
                {t('profile.fullName', 'Full Name')} *
              </label>
              <input
                id="onboard-name"
                type="text"
                className="input-field"
                placeholder={t('profile.fullNamePlaceholder', 'Enter your full name')}
                value={formData.full_name}
                onChange={e => updateField('full_name', e.target.value)}
                required
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="onboard-phone" className="input-label">
                {t('profile.phone', 'Phone Number')}
                <span className="text-surface-400 font-normal ml-1">
                  ({t('profile.optional', 'optional')})
                </span>
              </label>
              <input
                id="onboard-phone"
                type="tel"
                className="input-field"
                placeholder={t('profile.phonePlaceholder', '+91 98765 43210')}
                value={formData.phone}
                onChange={e => updateField('phone', e.target.value)}
              />
            </div>

            <button
              id="onboard-next-1"
              type="button"
              onClick={handleNext}
              disabled={!canProceedStep1}
              className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {t('onboarding.next', 'Next →')}
            </button>
          </div>
        </div>
      )}

      {/* ─── STEP 2: Child context ─── */}
      {step === 2 && (
        <div className="animate-fade-in">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-surface-900">
              {t('onboarding.childTitle', 'Tell us about your child')}
            </h2>
          </div>

          <div className="space-y-5">
            <div>
              <label htmlFor="onboard-class" className="input-label">
                {t('onboarding.stdClass', "Child's Class")} *
              </label>
              <select
                id="onboard-class"
                className="input-field"
                value={formData.std_class || ''}
                onChange={e => updateField('std_class', e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">{t('onboarding.stdClassPlaceholder', 'Select class')}</option>
                <option value="5">{t('onboarding.class5', '5th Standard')}</option>
                <option value="8">{t('onboarding.class8', '8th Standard')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="onboard-district" className="input-label">
                {t('onboarding.district', 'District')}
                <span className="text-surface-400 font-normal ml-1">
                  ({t('profile.optional', 'optional')})
                </span>
              </label>
              <input
                id="onboard-district"
                type="text"
                className="input-field"
                placeholder={t('onboarding.districtPlaceholder', 'e.g. Pune, Nashik, Aurangabad')}
                value={formData.district}
                onChange={e => updateField('district', e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="onboard-school" className="input-label">
                {t('onboarding.schoolName', 'School Name')}
                <span className="text-surface-400 font-normal ml-1">
                  ({t('profile.optional', 'optional')})
                </span>
              </label>
              <input
                id="onboard-school"
                type="text"
                className="input-field"
                placeholder={t('onboarding.schoolNamePlaceholder', "Enter your child's school name")}
                value={formData.school_name}
                onChange={e => updateField('school_name', e.target.value)}
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 py-3 rounded-xl border border-surface-200 text-sm font-medium
                           text-surface-600 hover:bg-surface-50 transition-colors"
              >
                {t('onboarding.back', '← Back')}
              </button>
              <button
                id="onboard-next-2"
                type="button"
                onClick={handleNext}
                className="flex-1 btn-primary"
              >
                {t('onboarding.next', 'Next →')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── STEP 3: Language ─── */}
      {step === 3 && (
        <div className="animate-fade-in">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-surface-900">
              {t('onboarding.languageTitle', 'Choose your preferred language')}
            </h2>
            <p className="mt-1 text-sm text-surface-500">
              {t('onboarding.languageDesc', 'This sets the default for exams and all content.')}
            </p>
          </div>

          <div className="space-y-6">
            <LanguagePicker
              value={formData.preferred_language}
              onChange={(lang) => updateField('preferred_language', lang)}
            />

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 py-3 rounded-xl border border-surface-200 text-sm font-medium
                           text-surface-600 hover:bg-surface-50 transition-colors"
              >
                {t('onboarding.back', '← Back')}
              </button>
              <button
                id="onboard-complete"
                type="button"
                onClick={handleComplete}
                disabled={loading || !canComplete}
                className="flex-1 btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading
                  ? t('onboarding.saving', 'Saving…')
                  : t('onboarding.complete', 'Complete Setup ✓')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
