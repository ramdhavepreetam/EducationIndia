import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth'
import { useDashboardStore } from '../store/dashboardStore'
import { StatsOverview } from '../components/StatsOverview'
import { TestGroupCard } from '../components/TestGroupCard'
import { RecentAttemptsList } from '../components/RecentAttemptsList'
import { ProgressChart } from '../components/ProgressChart'

import { useParentStore } from '@/modules/parent/store/parentStore'
import { useSearchParams } from 'react-router-dom'

/**
 * Shows the student's current access tier with what's included.
 * Free tier limits are static (set in app_settings) — shown informatively
 * so students understand why Paper II may be locked.
 */
function AccessTierCard({ t }) {
    return (
        <section>
            <h2 className="text-xl font-bold text-surface-800 mb-4">
                {t('dashboard.myPlan', 'My Plan')}
            </h2>
            <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
                {/* Free tier header */}
                <div className="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                            <svg className="w-3 h-3 mr-1 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                            </svg>
                            {t('dashboard.freePlan', 'Free Plan')}
                        </span>
                    </div>
                </div>

                {/* What's included */}
                <ul className="px-5 py-4 space-y-2.5 text-sm">
                    <li className="flex items-start gap-2 text-surface-700">
                        <svg className="w-4 h-4 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {t('dashboard.free_paper1', 'Paper I — Marathi + Mathematics')}
                    </li>
                    <li className="flex items-start gap-2 text-surface-700">
                        <svg className="w-4 h-4 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {t('dashboard.free_attempts', 'Up to 3 practice attempts')}
                    </li>
                    <li className="flex items-start gap-2 text-surface-700">
                        <svg className="w-4 h-4 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {t('dashboard.free_score', 'Basic score and grade')}
                    </li>
                    <li className="flex items-start gap-2 text-surface-400">
                        <svg className="w-4 h-4 text-surface-300 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        {t('dashboard.locked_paper2', 'Paper II — English + Intelligence Test')}
                    </li>
                    <li className="flex items-start gap-2 text-surface-400">
                        <svg className="w-4 h-4 text-surface-300 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        {t('dashboard.locked_analysis', 'Detailed topic analysis & PDF report')}
                    </li>
                </ul>

                {/* Parent upgrade note */}
                <div className="mx-4 mb-4 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-xs text-blue-800 leading-relaxed">
                    {t('dashboard.upgrade_note',
                        'Ask your parent to upgrade on ScholarPath to unlock all exams, unlimited attempts, and detailed analysis.'
                    )}
                </div>
            </div>
        </section>
    )
}

/** Group a flat exam list by event_id, returning an ordered array of groups. */
function groupExamsByEvent(exams) {
    const map = new Map()
    for (const exam of exams) {
        const key = exam.event_id ?? `solo-${exam.id}`
        if (!map.has(key)) {
            // Derive event title: strip " — Paper I/II" suffix if present
            const baseTitle = (exam.event_title || exam.title_en || '')
                .replace(/\s*[—–-]\s*Paper\s+(I|II).*$/i, '')
                .trim()
            map.set(key, {
                eventId: key,
                eventTitle: baseTitle || exam.title_en,
                year: exam.year ?? null,
                stdClass: exam.std_class ?? null,
                exams: [],
            })
        }
        map.get(key).exams.push(exam)
    }
    return Array.from(map.values())
}

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
    const examGroups = groupExamsByEvent(available_exams || [])

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
                {/* Left Column: Available Exams — grouped by event */}
                <div className="lg:col-span-2 space-y-8">
                    <section>
                        <h2 className="text-xl font-bold text-surface-800 mb-4">{t('dashboard.availableExams', 'Available Exams')}</h2>
                        {examGroups.length === 0 ? (
                            <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 text-center text-surface-500">
                                {t('dashboard.noExams', 'No exams currently available.')}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {examGroups.map(group => (
                                    <TestGroupCard
                                        key={group.eventId}
                                        eventTitle={group.eventTitle}
                                        year={group.year}
                                        stdClass={group.stdClass}
                                        exams={group.exams}
                                    />
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="hidden lg:block">
                        <ProgressChart attempts={recent_attempts} />
                    </section>
                </div>

                {/* Right Column: Recent Attempts, Access Card & Progress (Mobile) */}
                <div className="space-y-8">
                    <section>
                        <h2 className="text-xl font-bold text-surface-800 mb-4">{t('dashboard.recentAttempts', 'Recent Attempts')}</h2>
                        <RecentAttemptsList attempts={recent_attempts} />
                    </section>

                    <AccessTierCard t={t} />

                    <section className="block lg:hidden">
                        <ProgressChart attempts={recent_attempts} />
                    </section>
                </div>
            </div>
        </div>
    )
}
