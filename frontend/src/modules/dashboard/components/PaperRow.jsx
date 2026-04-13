import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useParentStore } from '@/modules/parent/store/parentStore'

/**
 * PaperRow — a compact row for a single exam paper inside a TestGroupCard.
 * Shows Paper I / Paper II label, question count, duration, lock state, and a CTA.
 *
 * Props:
 *   exam — ExamSummaryResponse (or ExamAccessResponse with is_accessible / lock_reason)
 *   paperLabel — e.g. "Paper I" or "Paper II"
 */
export const PaperRow = ({ exam, paperLabel }) => {
    const { t } = useTranslation()
    const { user } = useAuthStore()
    const selectedChildId = useParentStore(s => s.selectedChildId)
    const navigate = useNavigate()

    const title = user?.preferred_language === 'mr' && exam.title_mr ? exam.title_mr : exam.title_en
    const isLocked = exam.is_accessible === false

    const startUrl = selectedChildId
        ? `/exam/${exam.id}/start?childId=${selectedChildId}`
        : `/exam/${exam.id}/start`

    // Map paper_code to a human-readable label
    const resolvedLabel = paperLabel
        || (exam.paper_code === '501' ? t('dashboard.paperI', 'Paper I')
         :  exam.paper_code === '502' ? t('dashboard.paperII', 'Paper II')
         :  exam.paper_code)

    return (
        <div
            className={`flex items-center gap-3 sm:gap-4 py-3 px-4 transition rounded-lg group
                ${isLocked ? 'opacity-70' : 'hover:bg-brand-50/50'}`}
        >
            {/* Paper badge */}
            <div className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full min-w-[72px] text-center
                ${exam.paper_code === '501'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-violet-100 text-violet-700'}`}
            >
                {resolvedLabel}
            </div>

            {/* Title + meta */}
            <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate ${isLocked ? 'text-surface-500' : 'text-surface-800'}`}>
                    {title}
                </p>
                <div className="flex gap-3 text-xs text-surface-400 mt-0.5">
                    <span>{exam.total_questions} {t('dashboard.questions', 'Questions')}</span>
                    <span>·</span>
                    <span>{exam.duration_minutes} {t('dashboard.mins', 'mins')}</span>
                </div>
            </div>

            {/* CTA */}
            {isLocked ? (
                <button
                    onClick={() => navigate('/upgrade')}
                    className="flex-shrink-0 flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 rounded-lg hover:bg-amber-100 transition"
                    aria-label={t('dashboard.upgradeToAccess', 'Upgrade to Access')}
                >
                    🔒 {t('dashboard.upgrade', 'Upgrade')}
                </button>
            ) : (
                <Link
                    to={startUrl}
                    className="flex-shrink-0 px-3 py-1.5 text-xs font-semibold bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition"
                >
                    {t('dashboard.startExam', 'Start')}
                </Link>
            )}
        </div>
    )
}
