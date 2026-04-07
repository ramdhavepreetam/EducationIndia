/**
 * LanguagePicker — large clickable language cards with flags and checkmarks.
 *
 * Reused on both OnboardingPage (step 3) and ProfilePage (Preferences tab).
 */

const LANGUAGES = [
  { code: 'en', label: 'English',  script: 'English',  flag: '🇬🇧' },
  { code: 'mr', label: 'Marathi',  script: 'मराठी',    flag: '🇮🇳' },
]

export default function LanguagePicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {LANGUAGES.map(lang => (
        <button
          key={lang.code}
          type="button"
          onClick={() => onChange(lang.code)}
          className={`relative flex flex-col items-center gap-2
                      p-5 rounded-2xl border-2 transition-all
                      ${value === lang.code
                        ? 'border-brand-500 bg-brand-50 shadow-sm'
                        : 'border-surface-200 bg-white hover:border-surface-300'
                      }`}
        >
          {/* Selected checkmark */}
          {value === lang.code && (
            <span className="absolute top-2 right-2 w-5 h-5
                             bg-brand-500 text-white rounded-full
                             text-xs flex items-center justify-center">
              ✓
            </span>
          )}

          <span className="text-3xl">{lang.flag}</span>
          <span className={`text-sm font-semibold
                            ${value === lang.code
                              ? 'text-brand-700' : 'text-surface-700'}`}>
            {lang.label}
          </span>
          <span className={`text-xs
                            ${value === lang.code
                              ? 'text-brand-500' : 'text-surface-400'}`}>
            {lang.script}
          </span>
        </button>
      ))}
    </div>
  )
}
