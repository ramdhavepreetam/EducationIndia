import { useTranslation } from 'react-i18next'

export const StatsOverview = ({ stats }) => {
    const { t } = useTranslation()

    if (!stats) return null;

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label={t('dashboard.totalAttempts', 'Attempts')} value={stats.total_attempts} />
            <StatCard label={t('dashboard.avgScore', 'Avg Score')} value={`${stats.avg_percentage}%`} />
            <StatCard label={t('dashboard.bestScore', 'Best Score')} value={`${stats.best_score}`} />
            <StatCard label={t('dashboard.examsCompleted', 'Exams Completed')} value={stats.exams_completed} />
        </div>
    )
}

function StatCard({ label, value }) {
    return (
        <div className="bg-white py-5 px-4 rounded-xl border border-surface-200 shadow-sm flex flex-col items-center justify-center text-center">
            <div className="text-surface-500 text-sm font-medium mb-1">{label}</div>
            <div className="text-2xl font-bold text-brand-700">{value}</div>
        </div>
    )
}
