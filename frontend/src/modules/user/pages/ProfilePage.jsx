/**
 * ProfilePage — full settings page at /profile.
 *
 * Two-column layout on desktop, single column on mobile.
 * Left:  Profile card (avatar, name, email, auth provider, subscription)
 * Right: Tabbed form (Personal Details, Preferences, Password)
 *
 * Each tab has its own Save button. Success/error feedback inline.
 */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useUserStore } from '../store/userStore'
import { SubscriptionStatus } from '@/modules/payment'
import AvatarUploader from '../components/AvatarUploader'
import LanguagePicker from '../components/LanguagePicker'
import PasswordChangeForm from '../components/PasswordChangeForm'

const TABS = ['details', 'preferences', 'password']

export default function ProfilePage() {
  const { t, i18n } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const {
    loadProfile, updateProfile, uploadAvatar, changePassword,
    isSaving, saveSuccess, error: storeError, profile,
  } = useUserStore()

  const [activeTab, setActiveTab] = useState('details')

  // ── Form state for Personal Details tab ──
  const [details, setDetails] = useState({
    full_name: '', phone: '', date_of_birth: '', district: '', school_name: ''
  })
  const [detailsDirty, setDetailsDirty] = useState(false)

  // ── Form state for Preferences tab ──
  const [prefs, setPrefs] = useState({
    preferred_language: 'en', medium: ''
  })
  const [prefsDirty, setPrefsDirty] = useState(false)

  // ── Local success/error per tab ──
  const [tabSuccess, setTabSuccess] = useState(null)
  const [tabError, setTabError] = useState(null)

  const isEmailAuth = user?.auth_provider === 'email'
  const isParent = user?.role === 'parent'

  // Load profile on mount
  useEffect(() => {
    loadProfile()
  }, [])

  // Sync form from user/profile
  useEffect(() => {
    const data = profile || user
    if (data) {
      setDetails({
        full_name:     data.full_name || '',
        phone:         data.phone || '',
        date_of_birth: data.date_of_birth || '',
        district:      data.district || '',
        school_name:   data.school_name || '',
      })
      setPrefs({
        preferred_language: data.preferred_language || 'en',
        medium:             data.medium || '',
      })
    }
  }, [profile, user])

  const handleDetailsChange = (field) => (e) => {
    setDetails(prev => ({ ...prev, [field]: e.target.value }))
    setDetailsDirty(true)
    setTabSuccess(null)
    setTabError(null)
  }

  const handleSaveDetails = async () => {
    setTabSuccess(null)
    setTabError(null)
    const payload = {
      full_name:     details.full_name.trim(),
      phone:         details.phone.trim() || null,
      date_of_birth: details.date_of_birth || null,
      district:      details.district.trim() || null,
      school_name:   details.school_name.trim() || null,
    }
    const result = await updateProfile(payload)
    if (result.success) {
      setTabSuccess('details')
      setDetailsDirty(false)
      setTimeout(() => setTabSuccess(null), 3000)
    } else {
      setTabError(result.error)
    }
  }

  const handleSavePrefs = async () => {
    setTabSuccess(null)
    setTabError(null)
    // Update i18n language immediately
    i18n.changeLanguage(prefs.preferred_language)
    localStorage.setItem('sp_language', prefs.preferred_language)

    const payload = {
      preferred_language: prefs.preferred_language,
    }
    if (prefs.medium) payload.medium = prefs.medium

    const result = await updateProfile(payload)
    if (result.success) {
      setTabSuccess('preferences')
      setPrefsDirty(false)
      setTimeout(() => setTabSuccess(null), 3000)
    } else {
      setTabError(result.error)
    }
  }

  const handlePasswordSubmit = async (data) => {
    return await changePassword(data)
  }

  const handleAvatarUpload = async (file) => {
    await uploadAvatar(file)
  }

  // Format join date
  const joinDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
    : null

  return (
    <div className="max-w-6xl mx-auto p-6 md:p-8">
      <h1 className="text-2xl font-bold text-surface-900 mb-6">
        {t('profile.title', 'Profile Settings')}
      </h1>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* ──────── LEFT COLUMN — Profile Card ──────── */}
        <div className="lg:w-80 shrink-0">
          <div className="bg-white rounded-2xl border border-surface-100 p-6 shadow-sm">
            {/* Avatar */}
            <AvatarUploader
              currentAvatarUrl={user?.avatar_url}
              fullName={user?.full_name}
              onUpload={handleAvatarUpload}
            />

            {/* Name + role */}
            <div className="text-center mt-4">
              <h3 className="text-lg font-semibold text-surface-900">
                {user?.full_name || 'User'}
              </h3>
              <p className="text-xs text-surface-400 capitalize">
                {user?.role || 'parent'} · {joinDate ? `joined ${joinDate}` : ''}
              </p>
            </div>

            <hr className="my-4 border-surface-100" />

            {/* Email (read-only) */}
            <div className="flex items-center gap-2 text-sm text-surface-600">
              <span>📧</span>
              <span className="truncate">{user?.email || '—'}</span>
            </div>

            {/* Auth provider */}
            <div className="flex items-center gap-2 text-sm text-surface-500 mt-2">
              <span>🔒</span>
              <span>
                Signed in with{' '}
                <strong className="capitalize">{user?.auth_provider || 'email'}</strong>
              </span>
            </div>

            {/* Subscription status for parents */}
            {isParent && (
              <div className="mt-4">
                <SubscriptionStatus />
              </div>
            )}
          </div>
        </div>

        {/* ──────── RIGHT COLUMN — Tabs ──────── */}
        <div className="flex-1 min-w-0">
          {/* Tab navigation */}
          <div className="flex border-b border-surface-200 mb-6">
            {TABS.map((tab) => {
              // Only show password tab if relevant
              if (tab === 'password' && !isEmailAuth) return null

              const isDirty = (tab === 'details' && detailsDirty) || (tab === 'preferences' && prefsDirty)
              const labels = {
                details: 'Personal Details',
                preferences: 'Preferences',
                password: 'Password',
              }

              return (
                <button
                  key={tab}
                  onClick={() => { setActiveTab(tab); setTabError(null) }}
                  className={`relative px-5 py-3 text-sm font-medium transition-colors
                    ${activeTab === tab
                      ? 'text-brand-600 border-b-2 border-brand-500'
                      : 'text-surface-500 hover:text-surface-700'
                    }`}
                >
                  {labels[tab]}
                  {/* Unsaved changes indicator */}
                  {isDirty && (
                    <span className="absolute top-2 right-1 w-2 h-2 bg-orange-400 rounded-full" />
                  )}
                </button>
              )
            })}

            {/* Auth provider info for non-email users in place of Password tab */}
            {!isEmailAuth && (
              <button
                onClick={() => { setActiveTab('password'); setTabError(null) }}
                className={`px-5 py-3 text-sm font-medium transition-colors
                  ${activeTab === 'password'
                    ? 'text-brand-600 border-b-2 border-brand-500'
                    : 'text-surface-500 hover:text-surface-700'
                  }`}
              >
                Password
              </button>
            )}
          </div>

          {/* Tab error */}
          {tabError && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600 animate-fade-in">
              {tabError}
            </div>
          )}

          {/* ── Tab 1: Personal Details ── */}
          {activeTab === 'details' && (
            <div className="bg-white rounded-2xl border border-surface-100 p-6 shadow-sm animate-fade-in">
              {tabSuccess === 'details' && (
                <div className="mb-4 p-3 rounded-xl bg-green-50 border border-green-200 text-sm text-green-700">
                  ✓ Saved!
                </div>
              )}

              <div className="space-y-5">
                <div>
                  <label htmlFor="profile-name" className="input-label">
                    {t('profile.fullName', 'Full Name')} *
                  </label>
                  <input
                    id="profile-name" type="text" className="input-field"
                    value={details.full_name}
                    onChange={handleDetailsChange('full_name')}
                    required minLength={2} maxLength={100}
                  />
                </div>

                <div>
                  <label htmlFor="profile-phone" className="input-label">
                    {t('profile.phone', 'Phone Number')}
                  </label>
                  <input
                    id="profile-phone" type="tel" className="input-field"
                    placeholder={t('profile.phonePlaceholder', '+91 98765 43210')}
                    value={details.phone}
                    onChange={handleDetailsChange('phone')}
                  />
                </div>

                <div>
                  <label htmlFor="profile-dob" className="input-label">
                    {t('profile.dateOfBirth', 'Date of Birth')}
                  </label>
                  <input
                    id="profile-dob" type="date" className="input-field"
                    value={details.date_of_birth}
                    onChange={handleDetailsChange('date_of_birth')}
                  />
                </div>

                <div>
                  <label htmlFor="profile-district" className="input-label">
                    {t('profile.district', 'District')}
                  </label>
                  <input
                    id="profile-district" type="text" className="input-field"
                    placeholder={t('profile.districtPlaceholder', 'e.g. Pune')}
                    value={details.district}
                    onChange={handleDetailsChange('district')}
                  />
                </div>

                <div>
                  <label htmlFor="profile-school" className="input-label">
                    {t('profile.schoolName', 'School Name')}
                  </label>
                  <input
                    id="profile-school" type="text" className="input-field"
                    value={details.school_name}
                    onChange={handleDetailsChange('school_name')}
                  />
                </div>

                <button
                  id="profile-save-details"
                  type="button"
                  onClick={handleSaveDetails}
                  disabled={isSaving}
                  className="btn-primary w-full"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {/* ── Tab 2: Preferences ── */}
          {activeTab === 'preferences' && (
            <div className="bg-white rounded-2xl border border-surface-100 p-6 shadow-sm animate-fade-in">
              {tabSuccess === 'preferences' && (
                <div className="mb-4 p-3 rounded-xl bg-green-50 border border-green-200 text-sm text-green-700">
                  ✓ Saved!
                </div>
              )}

              <div className="space-y-6">
                <div>
                  <label className="input-label mb-3 block">
                    {t('profile.preferredLanguage', 'Preferred Language')}
                  </label>
                  <LanguagePicker
                    value={prefs.preferred_language}
                    onChange={(lang) => {
                      setPrefs(p => ({ ...p, preferred_language: lang }))
                      setPrefsDirty(true)
                      setTabSuccess(null)
                    }}
                  />
                </div>

                <div>
                  <label htmlFor="profile-medium" className="input-label">
                    {t('onboarding.medium', 'Exam Medium')}
                    <span className="text-surface-400 font-normal ml-1">
                      (default for new child profiles)
                    </span>
                  </label>
                  <select
                    id="profile-medium" className="input-field"
                    value={prefs.medium}
                    onChange={e => {
                      setPrefs(p => ({ ...p, medium: e.target.value }))
                      setPrefsDirty(true)
                      setTabSuccess(null)
                    }}
                  >
                    <option value="">—</option>
                    <option value="english">{t('onboarding.mediumEnglish', 'English')}</option>
                    <option value="marathi">{t('onboarding.mediumMarathi', 'Marathi')}</option>
                    <option value="semi_english">{t('onboarding.mediumSemiEnglish', 'Semi-English')}</option>
                  </select>
                </div>

                <button
                  id="profile-save-prefs"
                  type="button"
                  onClick={handleSavePrefs}
                  disabled={isSaving}
                  className="btn-primary w-full"
                >
                  {isSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          )}

          {/* ── Tab 3: Password ── */}
          {activeTab === 'password' && (
            <div className="bg-white rounded-2xl border border-surface-100 p-6 shadow-sm animate-fade-in">
              {isEmailAuth ? (
                <PasswordChangeForm onSubmit={handlePasswordSubmit} />
              ) : (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-surface-50 border border-surface-200">
                  <span className="text-xl">ℹ️</span>
                  <div>
                    <p className="text-sm font-medium text-surface-700">
                      Your account uses <strong className="capitalize">{user?.auth_provider}</strong> sign-in.
                    </p>
                    <p className="text-xs text-surface-500 mt-1">
                      Password changes are managed through {user?.auth_provider === 'google' ? 'Google' : 'Facebook'}.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
