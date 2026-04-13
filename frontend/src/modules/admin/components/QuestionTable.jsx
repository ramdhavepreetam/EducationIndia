import { useState } from 'react'
import { useTranslation } from 'react-i18next'

const DIFFICULTY_BADGE = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
}

const TYPE_BADGE = {
    text: 'bg-surface-100 text-surface-600',
    text_image: 'bg-blue-100 text-blue-700',
    image_only: 'bg-purple-100 text-purple-700',
    context_text: 'bg-orange-100 text-orange-700',
    context_image: 'bg-orange-100 text-orange-700',
    marathi_only: 'bg-pink-100 text-pink-700',
    bilingual: 'bg-teal-100 text-teal-700',
}

/**
 * QuestionTable — sortable, filterable list of questions for admin QuestionManagerPage.
 * Props:
 *   questions  — QuestionAdminSchema[]
 *   searchTerm — string to filter by text_en or text_mr (case-insensitive)
 *   onEdit     — (question) => void
 *   onDelete   — (questionId) => void  (if undefined, Delete button is hidden)
 */
export function QuestionTable({ questions, searchTerm = '', onEdit, onDelete }) {
    const { t } = useTranslation()
    const [sortKey, setSortKey] = useState('question_no')
    const [sortDir, setSortDir] = useState('asc')
    const [filter, setFilter] = useState({ difficulty: '', type: '' })
    const [showMr, setShowMr] = useState(false)
    const [expandedId, setExpandedId] = useState(null)

    const toggleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortKey(key); setSortDir('asc') }
    }

    const term = searchTerm.toLowerCase()

    const filtered = questions.filter(q => {
        if (filter.difficulty && q.difficulty !== filter.difficulty) return false
        if (filter.type && q.question_type !== filter.type) return false
        if (term) {
            const en = (q.text_en || '').toLowerCase()
            const mr = (q.text_mr || '').toLowerCase()
            if (!en.includes(term) && !mr.includes(term)) return false
        }
        return true
    })

    const sorted = [...filtered].sort((a, b) => {
        const va = a[sortKey] ?? ''
        const vb = b[sortKey] ?? ''
        const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb))
        return sortDir === 'asc' ? cmp : -cmp
    })

    const SortIcon = ({ col }) => (
        <span className="ml-1 text-surface-300">
            {sortKey === col ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
        </span>
    )

    const optionLabel = (no) => ['A', 'B', 'C', 'D'][no - 1] || String(no)

    return (
        <div className="space-y-3">
            {/* Filters row */}
            <div className="flex gap-3 flex-wrap items-center">
                <select
                    value={filter.difficulty}
                    onChange={e => setFilter(f => ({ ...f, difficulty: e.target.value }))}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                    <option value="">{t('admin.allDifficulties', 'All Difficulties')}</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                </select>
                <select
                    value={filter.type}
                    onChange={e => setFilter(f => ({ ...f, type: e.target.value }))}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                    <option value="">{t('admin.allTypes', 'All Types')}</option>
                    {['text', 'text_image', 'image_only', 'context_text', 'context_image', 'marathi_only', 'bilingual'].map(tp => (
                        <option key={tp} value={tp}>{tp}</option>
                    ))}
                </select>

                {/* EN / MR toggle */}
                <button
                    onClick={() => setShowMr(v => !v)}
                    className={`text-xs px-3 py-1.5 rounded-lg font-semibold border transition-colors ${
                        showMr
                            ? 'bg-brand-600 text-white border-brand-600'
                            : 'bg-white text-surface-600 border-surface-200 hover:border-brand-300'
                    }`}
                >
                    {showMr ? 'मराठी' : 'EN → मर'}
                </button>

                <span className="text-sm text-surface-400 ml-auto">
                    {sorted.length} / {questions.length} {t('admin.questions', 'questions')}
                </span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-xl border border-surface-200">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="bg-surface-50 text-left text-xs font-semibold text-surface-500 uppercase tracking-wide">
                            <th className="px-4 py-3 cursor-pointer select-none" onClick={() => toggleSort('question_no')}>
                                Q.No <SortIcon col="question_no" />
                            </th>
                            <th className="px-4 py-3">Type</th>
                            <th className="px-4 py-3">
                                Question {showMr && <span className="normal-case font-normal text-brand-600">(मराठी)</span>}
                            </th>
                            <th className="px-4 py-3 cursor-pointer select-none" onClick={() => toggleSort('correct_option')}>
                                Correct <SortIcon col="correct_option" />
                            </th>
                            <th className="px-4 py-3 cursor-pointer select-none" onClick={() => toggleSort('difficulty')}>
                                Difficulty <SortIcon col="difficulty" />
                            </th>
                            <th className="px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                        {sorted.map(q => {
                            const isExpanded = expandedId === q.id
                            const preview = showMr
                                ? (q.text_mr || q.text_en || '(image only)')
                                : (q.text_en || q.text_mr || '(image only)')

                            return [
                                <tr
                                    key={q.id}
                                    className={`hover:bg-surface-50 transition-colors ${isExpanded ? 'bg-surface-50' : ''}`}
                                >
                                    <td className="px-4 py-3 font-mono font-bold text-surface-700">{q.question_no}</td>
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col gap-1">
                                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_BADGE[q.question_type] || 'bg-surface-100 text-surface-600'}`}>
                                                {q.question_type}
                                            </span>
                                            {q.context_id && (
                                                <span className="text-xs px-2 py-0.5 rounded-full bg-surface-200 text-surface-500 font-medium w-fit">
                                                    📄 ctx
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 max-w-xs">
                                        <button
                                            onClick={() => setExpandedId(isExpanded ? null : q.id)}
                                            className="text-left w-full group"
                                        >
                                            <p className="truncate text-surface-800 group-hover:text-brand-700 transition-colors">
                                                {preview}
                                            </p>
                                            <span className="text-xs text-surface-400 group-hover:text-brand-500">
                                                {isExpanded ? '▲ collapse' : '▼ expand'}
                                            </span>
                                        </button>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="w-7 h-7 flex items-center justify-center bg-green-100 text-green-700 font-bold rounded-full text-xs">
                                            {optionLabel(q.correct_option)}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${DIFFICULTY_BADGE[q.difficulty] || ''}`}>
                                            {q.difficulty}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => onEdit(q)}
                                                className="text-xs px-3 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 font-medium transition-colors"
                                            >
                                                Edit
                                            </button>
                                            {onDelete && (
                                                <button
                                                    onClick={() => onDelete(q.id)}
                                                    className="text-xs px-3 py-1 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 font-medium transition-colors"
                                                >
                                                    Delete
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>,
                                isExpanded && (
                                    <tr key={`${q.id}-expand`} className="bg-surface-50 border-t border-surface-100">
                                        <td colSpan={6} className="px-6 py-4">
                                            <div className="space-y-3 max-w-3xl">
                                                {/* Full question text */}
                                                {(q.text_en || q.text_mr) && (
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        {q.text_en && (
                                                            <div>
                                                                <p className="text-xs font-semibold text-surface-400 mb-1">English</p>
                                                                <p className="text-sm text-surface-800">{q.text_en}</p>
                                                            </div>
                                                        )}
                                                        {q.text_mr && (
                                                            <div>
                                                                <p className="text-xs font-semibold text-surface-400 mb-1">मराठी</p>
                                                                <p className="text-sm text-surface-800">{q.text_mr}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                                {/* Options */}
                                                {q.options?.length > 0 && (
                                                    <div className="grid grid-cols-2 gap-2">
                                                        {q.options.map(opt => (
                                                            <div
                                                                key={opt.option_no}
                                                                className={`flex items-start gap-2 px-3 py-2 rounded-lg text-sm ${opt.option_no === q.correct_option ? 'bg-green-50 border border-green-200' : 'bg-white border border-surface-100'}`}
                                                            >
                                                                <span className={`w-5 h-5 flex-shrink-0 flex items-center justify-center rounded-full text-xs font-bold ${opt.option_no === q.correct_option ? 'bg-green-500 text-white' : 'bg-surface-200 text-surface-600'}`}>
                                                                    {optionLabel(opt.option_no)}
                                                                </span>
                                                                <span className="text-surface-700 text-xs">{opt.text_en || opt.text_mr || '(image)'}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                                {/* Meta */}
                                                <div className="flex gap-3 text-xs text-surface-400">
                                                    <span>ID: {q.id}</span>
                                                    <span>Section: {q.section_id}</span>
                                                    <span>Topic: {q.topic_id}</span>
                                                    {q.tags?.length > 0 && <span>Tags: {q.tags.join(', ')}</span>}
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                )
                            ]
                        })}
                        {sorted.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-4 py-12 text-center text-surface-400">
                                    {term ? `No questions match "${searchTerm}"` : 'No questions match the selected filters.'}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
