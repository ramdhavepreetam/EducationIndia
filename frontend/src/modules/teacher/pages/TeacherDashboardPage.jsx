import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTeacherStore } from '../store/teacherStore'

function StatCard({ label, value, icon, color = 'brand' }) {
    const colorMap = {
        brand: 'bg-brand-50 text-brand-600',
        green: 'bg-green-50 text-green-600',
        orange: 'bg-orange-50 text-orange-600',
        purple: 'bg-purple-50 text-purple-600',
    }
    return (
        <div className="bg-white rounded-2xl border border-surface-100 shadow-sm p-5 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${colorMap[color]}`}>
                {icon}
            </div>
            <div>
                <p className="text-2xl font-bold text-surface-900">{value ?? '—'}</p>
                <p className="text-sm text-surface-500">{label}</p>
            </div>
        </div>
    )
}

function AssignmentRow({ assignment }) {
    const statusDot = assignment.is_active
        ? 'bg-green-400'
        : 'bg-surface-300'

    return (
        <tr className="hover:bg-surface-50 transition-colors">
            <td className="px-4 py-3 font-medium text-surface-800">{assignment.student_name}</td>
            <td className="px-4 py-3 text-surface-600 text-sm">{assignment.exam_title}</td>
            <td className="px-4 py-3 text-surface-500 text-sm font-mono">{assignment.paper_code}</td>
            <td className="px-4 py-3 text-surface-600 text-sm">
                {assignment.attempts_used} / {assignment.max_attempts}
            </td>
            <td className="px-4 py-3">
                <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${assignment.is_active ? 'text-green-700' : 'text-surface-400'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />
                    {assignment.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td className="px-4 py-3">
                <Link
                    to={`/teacher/students/${assignment.student_id}`}
                    className="text-sm text-brand-600 hover:text-brand-700 font-medium"
                >
                    View →
                </Link>
            </td>
        </tr>
    )
}

export function TeacherDashboardPage() {
    const { dashboard, isDashboardLoading, error, loadDashboard } = useTeacherStore()

    useEffect(() => {
        loadDashboard()
    }, [loadDashboard])

    if (isDashboardLoading) {
        return (
            <div className="flex items-center justify-center min-h-[40vh]">
                <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-100">{error}</div>
            </div>
        )
    }

    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-surface-900">Teacher Dashboard</h1>
                <p className="text-surface-500 mt-1 text-sm">Manage your student assignments and track progress.</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <StatCard
                    label="Students Assigned"
                    value={dashboard?.total_students_assigned}
                    icon="👨‍🎓"
                    color="brand"
                />
                <StatCard
                    label="Active Assignments"
                    value={dashboard?.total_assignments_active}
                    icon="📋"
                    color="green"
                />
                <StatCard
                    label="Available Exams"
                    value={dashboard?.total_exams_available}
                    icon="📝"
                    color="purple"
                />
            </div>

            {/* Quick actions */}
            <div className="flex flex-wrap gap-3 mb-8">
                <Link
                    to="/teacher/assign"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 transition-colors"
                >
                    <span>+</span> Assign Exam
                </Link>
                <Link
                    to="/teacher/students"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-surface-200 text-surface-700 text-sm font-semibold rounded-xl hover:bg-surface-50 transition-colors"
                >
                    View All Students
                </Link>
            </div>

            {/* Recent assignments */}
            <div className="bg-white rounded-2xl border border-surface-100 shadow-sm">
                <div className="px-6 py-4 border-b border-surface-100 flex items-center justify-between">
                    <h2 className="text-base font-semibold text-surface-900">Recent Assignments</h2>
                    <Link to="/teacher/students" className="text-sm text-brand-600 hover:text-brand-700">
                        View all
                    </Link>
                </div>

                {!dashboard?.recent_assignments?.length ? (
                    <div className="px-6 py-12 text-center text-surface-400">
                        <p className="text-4xl mb-3">📋</p>
                        <p className="font-medium text-surface-600 mb-1">No assignments yet</p>
                        <p className="text-sm mb-4">Use "Assign Exam" to add a student and select an exam.</p>
                        <Link
                            to="/teacher/assign"
                            className="inline-flex items-center gap-2 px-5 py-2 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 transition-colors"
                        >
                            Assign First Exam
                        </Link>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-surface-50 text-xs font-semibold text-surface-500 uppercase tracking-wide text-left">
                                    <th className="px-4 py-3">Student</th>
                                    <th className="px-4 py-3">Exam</th>
                                    <th className="px-4 py-3">Paper</th>
                                    <th className="px-4 py-3">Attempts</th>
                                    <th className="px-4 py-3">Status</th>
                                    <th className="px-4 py-3"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {dashboard.recent_assignments.map(a => (
                                    <AssignmentRow key={a.id} assignment={a} />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
