import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTeacherStore } from '../store/teacherStore'

function GradeBadge({ grade }) {
    const map = {
        Excellent: 'bg-green-100 text-green-700',
        Good: 'bg-blue-100 text-blue-700',
        Average: 'bg-yellow-100 text-yellow-700',
        'Below Average': 'bg-red-100 text-red-700',
    }
    const cls = map[grade] || 'bg-surface-100 text-surface-600'
    return grade ? (
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>{grade}</span>
    ) : null
}

function StatusBadge({ status }) {
    const map = {
        submitted: 'bg-green-100 text-green-700',
        ongoing: 'bg-blue-100 text-blue-700',
        expired: 'bg-orange-100 text-orange-600',
        abandoned: 'bg-surface-100 text-surface-500',
    }
    return (
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${map[status] || 'bg-surface-100 text-surface-600'}`}>
            {status}
        </span>
    )
}

function ScoreBar({ percentage }) {
    const pct = Math.min(100, Math.max(0, Number(percentage) || 0))
    const color = pct >= 70 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-400' : 'bg-red-400'
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-surface-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs font-medium text-surface-600 w-10 text-right">
                {pct.toFixed(1)}%
            </span>
        </div>
    )
}

export function StudentResultsPage() {
    const { studentId } = useParams()
    const { selectedStudent, isDetailLoading, error, loadStudentDetail } = useTeacherStore()

    useEffect(() => {
        loadStudentDetail(studentId)
    }, [studentId, loadStudentDetail])

    if (isDetailLoading) {
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

    if (!selectedStudent) return null

    const s = selectedStudent

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            {/* Back */}
            <Link to="/teacher/students" className="inline-flex items-center gap-1 text-sm text-surface-500 hover:text-surface-800 mb-5">
                ← All Students
            </Link>

            {/* Student header */}
            <div className="bg-white rounded-2xl border border-surface-100 shadow-sm p-6 mb-6">
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-brand-100 text-brand-700 font-bold flex items-center justify-center text-xl flex-shrink-0">
                        {s.full_name?.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                        <h1 className="text-xl font-bold text-surface-900">{s.full_name}</h1>
                        <p className="text-sm text-surface-400">{s.email}</p>
                        {s.school_name && (
                            <p className="text-xs text-surface-400 mt-0.5">{s.school_name}{s.district ? ` · ${s.district}` : ''}</p>
                        )}
                    </div>
                    {s.std_class && (
                        <span className="text-sm bg-surface-100 text-surface-600 px-3 py-1 rounded-full">
                            Std {s.std_class}
                        </span>
                    )}
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t border-surface-100">
                    {[
                        { label: 'Total Attempts', value: s.total_attempts },
                        { label: 'Avg Score', value: s.avg_percentage != null ? `${Number(s.avg_percentage).toFixed(1)}%` : '—' },
                        { label: 'Best Score', value: s.best_percentage != null ? `${Number(s.best_percentage).toFixed(1)}%` : '—' },
                        { label: 'Last Attempt', value: s.last_attempt_at ? new Date(s.last_attempt_at).toLocaleDateString() : '—' },
                    ].map(stat => (
                        <div key={stat.label}>
                            <p className="text-xs text-surface-400">{stat.label}</p>
                            <p className="text-lg font-bold text-surface-900 mt-0.5">{stat.value}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Assignments */}
            {s.assignments?.length > 0 && (
                <div className="bg-white rounded-2xl border border-surface-100 shadow-sm mb-6">
                    <div className="px-6 py-4 border-b border-surface-100">
                        <h2 className="text-base font-semibold text-surface-900">Assigned Exams</h2>
                    </div>
                    <div className="divide-y divide-surface-100">
                        {s.assignments.map(a => (
                            <div key={a.id} className="px-6 py-4 flex items-center justify-between">
                                <div>
                                    <p className="font-medium text-surface-800 text-sm">{a.exam_title}</p>
                                    <p className="text-xs text-surface-400 mt-0.5">
                                        Paper {a.paper_code} · {a.attempts_used} / {a.max_attempts} attempts used
                                    </p>
                                </div>
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${a.is_active ? 'bg-green-100 text-green-700' : 'bg-surface-100 text-surface-500'}`}>
                                    {a.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Attempt history */}
            <div className="bg-white rounded-2xl border border-surface-100 shadow-sm">
                <div className="px-6 py-4 border-b border-surface-100">
                    <h2 className="text-base font-semibold text-surface-900">Attempt History</h2>
                    <p className="text-xs text-surface-400 mt-0.5">Read-only view of all submitted attempts.</p>
                </div>

                {!s.recent_attempts?.length ? (
                    <div className="px-6 py-10 text-center text-surface-400 text-sm">
                        No attempts yet. The student hasn't taken any exams.
                    </div>
                ) : (
                    <div className="divide-y divide-surface-100">
                        {s.recent_attempts.map(a => (
                            <div key={a.attempt_id} className="px-6 py-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="font-medium text-surface-800 text-sm">{a.exam_title}</span>
                                        <span className="text-xs text-surface-400 font-mono">{a.paper_code}</span>
                                        <StatusBadge status={a.status} />
                                        {a.grade && <GradeBadge grade={a.grade} />}
                                    </div>
                                    <span className="text-xs text-surface-400 flex-shrink-0 ml-3">
                                        {a.submitted_at
                                            ? new Date(a.submitted_at).toLocaleDateString()
                                            : new Date(a.started_at).toLocaleDateString()}
                                    </span>
                                </div>

                                {a.status === 'submitted' && (
                                    <div className="mt-2">
                                        <ScoreBar percentage={a.percentage} />
                                        <div className="flex gap-4 mt-1.5 text-xs text-surface-500">
                                            <span className="text-green-600">{a.total_correct} correct</span>
                                            <span className="text-red-500">{a.total_wrong} wrong</span>
                                            <span>{a.total_skipped} skipped</span>
                                            {a.duration_seconds && (
                                                <span>{Math.round(a.duration_seconds / 60)} min</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
