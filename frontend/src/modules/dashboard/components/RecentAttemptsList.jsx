import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useParentStore } from '@/modules/parent/store/parentStore'

export const RecentAttemptsList = ({ attempts }) => {
    const { t } = useTranslation()
    const selectedChildId = useParentStore(s => s.selectedChildId)

    if (!attempts || attempts.length === 0) {
        return <div className="text-surface-500 p-4 bg-surface-50 rounded-lg text-center">{t('dashboard.noAttempts', 'No recent attempts')}</div>
    }

    return (
        <div className="space-y-3">
            {attempts.map(attempt => (
                <div key={attempt.attempt_id} className="bg-white p-4 rounded-xl border border-surface-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 hover:border-brand-300 transition">
                    <div>
                        <div className="font-bold text-surface-900">
                            {t('dashboard.attempt', 'Attempt')} #{attempt.attempt_number}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-sm text-surface-500 mt-1">
                            <span>{new Date(attempt.started_at).toLocaleDateString()}</span>

                            {attempt.status === 'submitted' && attempt.percentage !== null && (
                                <>
                                    <span>•</span>
                                    <span className={`font-medium ${attempt.percentage >= 50 ? 'text-green-600' : 'text-orange-500'}`}>
                                        {attempt.percentage}%
                                    </span>
                                    <span>•</span>
                                    <span className="font-medium text-surface-700">{attempt.grade}</span>
                                </>
                            )}
                            {attempt.status !== 'submitted' && (
                                <>
                                    <span>•</span>
                                    <span className="text-brand-500 capitalize">{attempt.status}</span>
                                </>
                            )}
                        </div>
                    </div>
                    {attempt.status === 'submitted' ? (
                        <Link
                            to={`/attempts/${attempt.attempt_id}/result`}
                            className="bg-surface-50 text-brand-600 font-medium text-sm hover:text-brand-800 transition px-4 py-2 rounded-lg hover:bg-brand-100 shrink-0 border border-brand-100"
                        >
                            {t('dashboard.viewResult', 'View Result')}
                        </Link>
                    ) : (
                        <Link
                            to={`/exam/${attempt.exam_id}/start${selectedChildId ? `?childId=${selectedChildId}` : ''}`}
                            className="bg-brand-50 text-brand-700 font-medium text-sm hover:text-brand-800 transition px-4 py-2 rounded-lg hover:bg-brand-100 shrink-0 border border-brand-200"
                        >
                            {t('dashboard.resume', 'Resume')}
                        </Link>
                    )}
                </div>
            ))}
        </div>
    )
}
