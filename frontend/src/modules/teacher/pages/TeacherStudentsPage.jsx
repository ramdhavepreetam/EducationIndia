import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTeacherStore } from '../store/teacherStore'

function GradeBadge({ grade }) {
    const map = {
        Excellent: 'bg-green-100 text-green-700',
        Good: 'bg-blue-100 text-blue-700',
        Average: 'bg-yellow-100 text-yellow-700',
        'Below Average': 'bg-red-100 text-red-700',
    }
    const cls = map[grade] || 'bg-surface-100 text-surface-600'
    return (
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>
            {grade}
        </span>
    )
}

function StudentCard({ student }) {
    return (
        <div className="bg-white rounded-2xl border border-surface-100 shadow-sm p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-brand-100 text-brand-700 font-bold flex items-center justify-center text-sm">
                        {student.full_name?.slice(0, 2).toUpperCase() || '??'}
                    </div>
                    <div>
                        <p className="font-semibold text-surface-900">{student.full_name}</p>
                        <p className="text-xs text-surface-400">{student.email || 'No email'}</p>
                    </div>
                </div>
                {student.std_class && (
                    <span className="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded-full">
                        Std {student.std_class}
                    </span>
                )}
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div>
                    <p className="text-surface-400 text-xs">Attempts</p>
                    <p className="font-semibold text-surface-800">{student.total_attempts || 0}</p>
                </div>
                <div>
                    <p className="text-surface-400 text-xs">Avg Score</p>
                    <p className="font-semibold text-surface-800">
                        {student.avg_percentage != null
                            ? `${Number(student.avg_percentage).toFixed(1)}%`
                            : '—'}
                    </p>
                </div>
                {student.school_name && (
                    <div className="col-span-2">
                        <p className="text-surface-400 text-xs">School</p>
                        <p className="text-surface-600 text-xs truncate">{student.school_name}</p>
                    </div>
                )}
            </div>

            <Link
                to={`/teacher/students/${student.id}`}
                className="block text-center text-sm font-semibold text-brand-600 border border-brand-200 rounded-xl py-2 hover:bg-brand-50 transition-colors"
            >
                View Results →
            </Link>
        </div>
    )
}

export function TeacherStudentsPage() {
    const { students, isStudentsLoading, error, loadStudents } = useTeacherStore()
    const [search, setSearch] = useState('')
    const [debouncedSearch, setDebouncedSearch] = useState('')

    useEffect(() => {
        const t = setTimeout(() => setDebouncedSearch(search), 300)
        return () => clearTimeout(t)
    }, [search])

    useEffect(() => {
        loadStudents({ search: debouncedSearch || undefined })
    }, [debouncedSearch, loadStudents])

    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">My Students</h1>
                    <p className="text-surface-500 mt-1 text-sm">
                        Students you've assigned exams to.
                    </p>
                </div>
                <Link
                    to="/teacher/assign"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 transition-colors"
                >
                    + Assign Exam
                </Link>
            </div>

            {/* Search */}
            <div className="mb-6">
                <input
                    type="text"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search by name or email…"
                    className="w-full max-w-sm text-sm border border-surface-200 rounded-xl px-4 py-2.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
                />
            </div>

            {error && (
                <div className="mb-6 bg-red-50 text-red-700 p-4 rounded-xl border border-red-100">{error}</div>
            )}

            {isStudentsLoading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            ) : students.length === 0 ? (
                <div className="text-center py-20 text-surface-400">
                    <p className="text-4xl mb-3">👨‍🎓</p>
                    <p className="font-medium text-surface-600 mb-1">
                        {debouncedSearch ? 'No students match your search.' : 'No students yet.'}
                    </p>
                    {!debouncedSearch && (
                        <p className="text-sm">
                            <Link to="/teacher/assign" className="text-brand-600 hover:underline">
                                Assign an exam
                            </Link>{' '}
                            to get started.
                        </p>
                    )}
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {students.map(s => (
                        <StudentCard key={s.id} student={s} />
                    ))}
                </div>
            )}
        </div>
    )
}
