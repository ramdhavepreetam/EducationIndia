import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'

export function StatsPage() {
    const { t } = useTranslation()
    const { questionStats, statsLoading, statsError, fetchQuestionStats, exams, fetchAllExams } = useAdminStore()
    const [examId, setExamId] = useState(null)
    const [sortKey, setSortKey] = useState('question_no')
    const [sortDir, setSortDir] = useState('asc')

    useEffect(() => {
        if (exams.length === 0) fetchAllExams()
    }, [exams.length, fetchAllExams])

    useEffect(() => {
        if (!examId && exams.length > 0) {
            setExamId(exams[0].id)
        }
    }, [exams, examId])

    useEffect(() => {
        if (examId) fetchQuestionStats(examId)
    }, [examId, fetchQuestionStats])

    const toggleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortKey(key); setSortDir('asc') }
    }

    const sorted = [...questionStats].sort((a, b) => {
        const va = a[sortKey] ?? 0
        const vb = b[sortKey] ?? 0
        const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
        return sortDir === 'asc' ? cmp : -cmp
    })

    const exportCsv = () => {
        const headers = ['Q.No', 'Total Attempts', 'Correct', 'Wrong', 'Skipped', 'Correct %', 'Avg Time (s)', 'Difficulty']
        const rows = sorted.map(r => [
            r.question_no ?? r.question_id,
            r.total_attempts,
            r.correct_count,
            r.wrong_count,
            r.skip_count,
            r.correct_pct?.toFixed(1) ?? '—',
            r.avg_time_seconds?.toFixed(1) ?? '—',
            r.actual_difficulty?.toFixed(3) ?? '—',
        ])
        const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `question_stats_exam${examId}.csv`
        a.click()
        URL.revokeObjectURL(url)
    }

    const SortIcon = ({ col }) => (
        <span className="ml-1 text-surface-300">{sortKey === col ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>
    )

    const difficultyColor = (d) => {
        if (d == null) return ''
        if (d >= 0.8) return 'text-red-600 font-bold'
        if (d >= 0.5) return 'text-orange-500 font-medium'
        return 'text-green-600'
    }

    return (
        <div className="p-4 sm:p-8 max-w-6xl mx-auto pb-24">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('admin.statsPage', 'Question Stats')}
                </h1>
                <p className="text-surface-500 mt-1">
                    {t('admin.statsPageSub', 'Performance data per question. Red = difficulty > 0.8 (very hard).')}
                </p>
            </div>

            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
                <select
                    value={examId ?? ''}
                    onChange={e => setExamId(Number(e.target.value))}
                    disabled={exams.length === 0}
                    className="text-sm border border-surface-200 rounded-xl px-4 py-2 text-surface-700 font-medium focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white disabled:opacity-50"
                >
                    {exams.map(ex => (
                        <option key={ex.id} value={ex.id}>
                            {ex.title_en || `${ex.paper_code}-${ex.set_code}`}
                        </option>
                    ))}
                </select>

                <button
                    onClick={exportCsv}
                    disabled={questionStats.length === 0}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-semibold border border-surface-200 text-surface-700 rounded-xl hover:bg-surface-100 disabled:opacity-40 transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Export CSV
                </button>
            </div>

            {statsLoading && (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            )}

            {statsError && !statsLoading && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200">{statsError}</div>
            )}

            {!statsLoading && !statsError && (
                <div className="bg-white rounded-xl border border-surface-100 shadow-sm overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-surface-50 text-xs font-semibold text-surface-500 uppercase tracking-wide text-left">
                                {[
                                    { key: 'question_no', label: 'Q.No' },
                                    { key: 'total_attempts', label: 'Attempts' },
                                    { key: 'correct_count', label: 'Correct' },
                                    { key: 'wrong_count', label: 'Wrong' },
                                    { key: 'skip_count', label: 'Skipped' },
                                    { key: 'correct_pct', label: 'Correct %' },
                                    { key: 'avg_time_seconds', label: 'Avg Time' },
                                    { key: 'actual_difficulty', label: 'Difficulty' },
                                ].map(col => (
                                    <th
                                        key={col.key}
                                        className="px-4 py-3 cursor-pointer select-none whitespace-nowrap"
                                        onClick={() => toggleSort(col.key)}
                                    >
                                        {col.label} <SortIcon col={col.key} />
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {sorted.map(row => (
                                <tr
                                    key={row.question_id}
                                    className={`hover:bg-surface-50 ${(row.actual_difficulty ?? 0) >= 0.8 ? 'bg-red-50/40' : ''}`}
                                >
                                    <td className="px-4 py-3 font-mono font-bold text-surface-700">{row.question_no ?? row.question_id}</td>
                                    <td className="px-4 py-3 text-surface-700">{row.total_attempts}</td>
                                    <td className="px-4 py-3 text-green-700">{row.correct_count}</td>
                                    <td className="px-4 py-3 text-red-600">{row.wrong_count}</td>
                                    <td className="px-4 py-3 text-surface-400">{row.skip_count}</td>
                                    <td className="px-4 py-3 font-medium">
                                        {row.correct_pct != null ? `${row.correct_pct.toFixed(1)}%` : '—'}
                                    </td>
                                    <td className="px-4 py-3 text-surface-600">
                                        {row.avg_time_seconds != null ? `${row.avg_time_seconds}s` : '—'}
                                    </td>
                                    <td className={`px-4 py-3 ${difficultyColor(row.actual_difficulty)}`}>
                                        {row.actual_difficulty != null ? row.actual_difficulty.toFixed(3) : '—'}
                                    </td>
                                </tr>
                            ))}
                            {sorted.length === 0 && (
                                <tr>
                                    <td colSpan={8} className="px-4 py-12 text-center text-surface-400">
                                        No stats yet. Students need to submit attempts first.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}
