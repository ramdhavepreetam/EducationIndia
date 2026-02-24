import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'

export const AvailableExamCard = ({ exam }) => {
    const { t } = useTranslation()
    const { user } = useAuthStore()

    const title = user?.preferred_language === 'mr' && exam.title_mr ? exam.title_mr : exam.title_en

    return (
        <div className="bg-white p-5 rounded-xl border border-brand-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:shadow-md transition">
            <div>
                <h3 className="font-bold text-surface-900 text-lg">{title}</h3>
                <div className="flex gap-4 text-sm text-surface-500 mt-1">
                    <span>{exam.total_questions} {t('dashboard.questions', 'Questions')}</span>
                    <span>{exam.duration_minutes} {t('dashboard.mins', 'mins')}</span>
                </div>
            </div>
            <Link
                to={`/exam/${exam.id}/start`}
                className="px-6 py-2 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition w-full md:w-auto text-center shrink-0"
            >
                {t('dashboard.startExam', 'Start')}
            </Link>
        </div>
    )
}
