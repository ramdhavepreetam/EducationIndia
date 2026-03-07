import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useParentStore } from '@/modules/parent/store/parentStore'

export const AvailableExamCard = ({ exam }) => {
    const { t } = useTranslation()
    const { user } = useAuthStore()
    const selectedChildId = useParentStore(s => s.selectedChildId)
    const navigate = useNavigate()

    const title = user?.preferred_language === 'mr' && exam.title_mr ? exam.title_mr : exam.title_en
    const isLocked = exam.is_accessible === false

    const startUrl = selectedChildId
        ? `/exam/${exam.id}/start?childId=${selectedChildId}`
        : `/exam/${exam.id}/start`

    return (
        <div className={`bg-white p-5 rounded-xl border shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition ${isLocked
                ? 'border-gray-200 opacity-75'
                : 'border-brand-200 hover:shadow-md'
            }`}>
            <div className="flex items-center gap-3">
                {isLocked && (
                    <span className="text-2xl" aria-label="locked">🔒</span>
                )}
                <div>
                    <h3 className={`font-bold text-lg ${isLocked ? 'text-gray-500' : 'text-surface-900'}`}>
                        {title}
                    </h3>
                    <div className="flex gap-4 text-sm text-surface-500 mt-1">
                        <span>{exam.total_questions} {t('dashboard.questions', 'Questions')}</span>
                        <span>{exam.duration_minutes} {t('dashboard.mins', 'mins')}</span>
                    </div>
                </div>
            </div>

            {isLocked ? (
                <button
                    onClick={() => navigate('/upgrade')}
                    className="px-6 py-2 bg-amber-500 text-white font-medium rounded-lg hover:bg-amber-600 transition w-full md:w-auto text-center shrink-0 flex items-center justify-center gap-2"
                >
                    🔒 {t('dashboard.upgradeToAccess', 'Upgrade to Access')}
                </button>
            ) : (
                <Link
                    to={startUrl}
                    className="px-6 py-2 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition w-full md:w-auto text-center shrink-0"
                >
                    {t('dashboard.startExam', 'Start')}
                </Link>
            )}
        </div>
    )
}
