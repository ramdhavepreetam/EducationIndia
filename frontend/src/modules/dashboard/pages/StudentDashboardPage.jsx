import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useDashboardStore } from '../store/dashboardStore'
import { StatsOverview } from '../components/StatsOverview'
import { AvailableExamCard } from '../components/AvailableExamCard'
import { RecentAttemptsList } from '../components/RecentAttemptsList'
import { ProgressChart } from '../components/ProgressChart'

import { useParentStore } from '@/modules/parent/store/parentStore'
import { useSearchParams } from 'react-router-dom'

export const StudentDashboardPage = () => {
    const { t } = useTranslation()
    const { user } = useAuthStore()
    const { dashboardData, isLoading, error, fetchDashboard } = useDashboardStore()
    const selectedChildId = useParentStore(s => s.selectedChildId)
    const [searchParams] = useSearchParams()
    const urlChildId = searchParams.get('childId')

    useEffect(() => {
        const effectiveChildId = selectedChildId || urlChildId
        if (user?.role === 'parent' && effectiveChildId) {
            fetchDashboard(effectiveChildId)
        } else {
            fetchDashboard()
        }
    }, [fetchDashboard, user?.role, selectedChildId, urlChildId])

    if (isLoading && !dashboardData) {
        return (
            <div className="p-8 flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4 animate-fade-in">
                    <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    <p className="text-surface-500 font-medium">{t('common.loading', 'Loading dashboard...')}</p>
                </div>
            </div>
        )
    }

    if (error && !dashboardData) {
        return (
            <div className="p-8">
                <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-200">
                    {error}
                </div>
            </div>
        )
    }

    if (!dashboardData) return null;

    const { available_exams, recent_attempts, stats } = dashboardData

    return (
        <div className="p-4 sm:p-8 max-w-6xl mx-auto pb-24">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('dashboard.welcome', 'Welcome')}, {user?.full_name?.split(' ')[0] || 'Student'} 👋
                </h1>
                <p className="text-surface-500 mt-1">
                    {user?.school_name ? `${user.school_name} • ` : ''}
                    {user?.std_class ? `${t('dashboard.stdClass', 'Class')} ${user.std_class} • ` : ''}
                    {user?.medium === 'english' ? 'English Medium' : (user?.medium === 'marathi' ? 'Marathi Medium' : 'Semi-English Medium')}
                </p>
            </div>

            <StatsOverview stats={stats} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Available Exams */}
                <div className="lg:col-span-2 space-y-8">
                    <section>
                        <h2 className="text-xl font-bold text-surface-800 mb-4">{t('dashboard.availableExams', 'Available Exams')}</h2>
                        {(!available_exams || available_exams.length === 0) ? (
                            <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 text-center text-surface-500">
                                {t('dashboard.noExams', 'No exams currently available.')}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {available_exams.map(exam => (
                                    <AvailableExamCard key={exam.id} exam={exam} />
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="hidden lg:block">
                        <ProgressChart attempts={recent_attempts} />
                    </section>
                </div>

                {/* Right Column: Recent Attempts & Progress (Mobile) */}
                <div className="space-y-8">
                    <section>
                        <h2 className="text-xl font-bold text-surface-800 mb-4">{t('dashboard.recentAttempts', 'Recent Attempts')}</h2>
                        <RecentAttemptsList attempts={recent_attempts} />
                    </section>

                    <section className="block lg:hidden">
                        <ProgressChart attempts={recent_attempts} />
                    </section>
                </div>
            </div>
        </div>
    )
}
