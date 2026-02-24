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
 * QuestionTable — sortable list of questions for admin QuestionManagerPage.
 * Shows Q.No, type, text preview, correct option, difficulty, actions.
 */
export function QuestionTable({ questions, onEdit, onDelete }) {
    const { t } = useTranslation()
    const [sortKey, setSortKey] = useState('question_no')
    const [sortDir, setSortDir] = useState('asc')
    const [filter, setFilter] = useState({ difficulty: '', type: '' })

    const toggleSort = (key) => {
        if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortKey(key); setSortDir('asc') }
    }

    const filtered = questions.filter(q => {
        if (filter.difficulty && q.difficulty !== filter.difficulty) return false
        if (filter.type && q.question_type !== filter.type) return false
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

    return (
        <div className="space-y-3">
            {/* Filters */}
            <div className="flex gap-3 flex-wrap">
                <select
                    value={filter.difficulty}
                    onChange={e => setFilter(f => ({ ...f, difficulty: e.target.value }))}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                >
                    <option value="">{t('admin.allDifficulties', 'All Difficulties')}</option>
                    <option value="easy">{t('admin.easy', 'Easy')}</option>
                    <option value="medium">{t('admin.medium', 'Medium')}</option>
                    <option value="hard">{t('admin.hard', 'Hard')}</option>
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
                <span className="text-sm text-surface-400 self-center">
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
                            <th className="px-4 py-3">Question</th>
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
                        {sorted.map(q => (
                            <tr key={q.id} className="hover:bg-surface-50 transition-colors">
                                <td className="px-4 py-3 font-mono font-bold text-surface-700">{q.question_no}</td>
                                <td className="px-4 py-3">
                                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_BADGE[q.question_type] || 'bg-surface-100 text-surface-600'}`}>
                                        {q.question_type}
                                    </span>
                                </td>
                                <td className="px-4 py-3 max-w-xs">
                                    <p className="truncate text-surface-800">
                                        {q.text_en || q.text_mr || '(image only)'}
                                    </p>
                                </td>
                                <td className="px-4 py-3">
                                    <span className="w-7 h-7 flex items-center justify-center bg-green-100 text-green-700 font-bold rounded-full text-xs">
                                        {q.correct_option}
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
                            </tr>
                        ))}
                        {sorted.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-4 py-12 text-center text-surface-400">
                                    No questions match the selected filters.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
