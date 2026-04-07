import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAdminStore } from '../store/adminStore'

/**
 * AdminDashboardPage — overview of the entire platform.
 * Cards: total students, total attempts, active exams, questions count.
 * Recent attempts table (last 20 across all students).
 */
export function AdminDashboardPage() {
    const { t } = useTranslation()
    const { overview, recentAttempts, overviewLoading, overviewError, fetchOverview } = useAdminStore()

    useEffect(() => {
        fetchOverview()
    }, [fetchOverview])

    if (overviewLoading && !overview) {
        return (
            <div className="p-8 flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    <p className="text-surface-500">{t('common.loading', 'Loading…')}</p>
                </div>
            </div>
        )
    }

    if (overviewError && !overview) {
        return (
            <div className="p-8">
                <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-200">{overviewError}</div>
            </div>
        )
    }

    const cards = [
        { label: t('admin.totalStudents', 'Total Students'), value: overview?.total_students ?? '—', icon: StudentIcon, color: 'bg-blue-50 text-blue-600' },
        { label: t('admin.totalAttempts', 'Total Attempts'), value: overview?.total_attempts ?? '—', icon: AttemptIcon, color: 'bg-purple-50 text-purple-600' },
        { label: t('admin.activeExams', 'Active Exams'), value: overview?.active_exams ?? '—', icon: ExamIcon, color: 'bg-green-50 text-green-600' },
        { label: t('admin.totalQuestions', 'Total Questions'), value: overview?.total_questions ?? '—', icon: QuestionIcon, color: 'bg-orange-50 text-orange-600' },
    ]

    const quickLinks = [
        { to: '/admin/questions', label: t('admin.manageQuestions', 'Manage Questions') },
        { to: '/admin/publish', label: t('admin.publishExams', 'Publish Exams') },
        { to: '/admin/images', label: t('admin.uploadImages', 'Upload Images') },
        { to: '/admin/stats', label: t('admin.viewStats', 'View Stats') },
        { to: '/admin/settings', label: t('admin.systemSettings', 'System Settings') },
        { to: '/admin/subscriptions', label: t('admin.subscriptions', 'Subscriptions') },
    ]

    return (
        <div className="p-4 sm:p-8 max-w-6xl mx-auto pb-24">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('admin.panelTitle', 'Admin Panel')}
                </h1>
                <p className="text-surface-500 mt-1">{t('admin.panelSubtitle', 'Platform management and question administration')}</p>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {cards.map(card => (
                    <div key={card.label} className="bg-white rounded-xl border border-surface-100 shadow-sm p-5">
                        <div className={`w-10 h-10 rounded-xl ${card.color} flex items-center justify-center mb-3`}>
                            <card.icon />
                        </div>
                        <p className="text-2xl font-bold text-surface-900">{card.value.toLocaleString?.() ?? card.value}</p>
                        <p className="text-xs text-surface-500 mt-1 font-medium">{card.label}</p>
                    </div>
                ))}
            </div>

            {/* Quick links */}
            <div className="bg-white rounded-xl border border-surface-100 shadow-sm p-6 mb-8">
                <h2 className="text-base font-bold text-surface-800 mb-4">{t('admin.quickLinks', 'Quick Actions')}</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {quickLinks.map(link => (
                        <Link
                            key={link.to}
                            to={link.to}
                            className="flex items-center justify-center px-4 py-3 bg-surface-50 hover:bg-brand-50 text-surface-700 hover:text-brand-700 rounded-xl text-sm font-medium transition-colors border border-surface-200 hover:border-brand-200"
                        >
                            {link.label}
                        </Link>
                    ))}
                </div>
            </div>

            {/* Recent attempts table */}
            <div className="bg-white rounded-xl border border-surface-100 shadow-sm">
                <div className="px-6 py-4 border-b border-surface-100">
                    <h2 className="text-base font-bold text-surface-800">{t('admin.recentAttempts', 'Recent Attempts')}</h2>
                    <p className="text-xs text-surface-400 mt-0.5">Last 20 across all students</p>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-surface-50 text-xs font-semibold text-surface-500 uppercase text-left">
                                <th className="px-4 py-3">Student</th>
                                <th className="px-4 py-3">Exam</th>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3">Score</th>
                                <th className="px-4 py-3">Grade</th>
                                <th className="px-4 py-3">Date</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {recentAttempts.map(a => (
                                <tr key={String(a.attempt_id)} className="hover:bg-surface-50">
                                    <td className="px-4 py-3 font-medium text-surface-800">{a.student_name || 'Unknown'}</td>
                                    <td className="px-4 py-3 text-surface-600">{a.exam_title || `Exam ${a.exam_id}`}</td>
                                    <td className="px-4 py-3">
                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${a.status === 'submitted' ? 'bg-green-100 text-green-700' :
                                                a.status === 'ongoing' ? 'bg-blue-100 text-blue-700' :
                                                    'bg-surface-100 text-surface-600'
                                            }`}>{a.status}</span>
                                    </td>
                                    <td className="px-4 py-3 font-mono text-surface-700">
                                        {a.total_score != null ? `${a.total_score} (${a.percentage?.toFixed(1)}%)` : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-surface-600">{a.grade || '—'}</td>
                                    <td className="px-4 py-3 text-surface-400 text-xs">
                                        {a.started_at ? new Date(a.started_at).toLocaleDateString() : '—'}
                                    </td>
                                </tr>
                            ))}
                            {recentAttempts.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-4 py-10 text-center text-surface-400">No attempts yet.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

/* ── Inline icons ─────────────────────────────────────────────────────────── */
function StudentIcon() {
    return <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
}
function AttemptIcon() {
    return <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" /></svg>
}
function ExamIcon() {
    return <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
}
function QuestionIcon() {
    return <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
}
