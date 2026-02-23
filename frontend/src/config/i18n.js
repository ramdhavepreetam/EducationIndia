/**
 * react-i18next configuration.
 *
 * CLAUDE.md: Default from user_profiles.preferred_language,
 * persisted to localStorage as 'sp_language', applied via useTranslation().
 *
 * Supports: English (en), Marathi (mr).
 * Hindi (hi) — add hi.json later, no code change needed.
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from '@/locales/en.json'
import mr from '@/locales/mr.json'

const savedLanguage = localStorage.getItem('sp_language') || 'en'

i18n.use(initReactI18next).init({
    resources: {
        en: { translation: en },
        mr: { translation: mr },
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
        escapeValue: false,
    },
})

export default i18n
