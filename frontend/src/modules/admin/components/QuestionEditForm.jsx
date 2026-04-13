import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'

/**
 * QuestionEditForm — modal form for editing a question's core fields.
 * Opens when admin clicks Edit in QuestionTable.
 */
export function QuestionEditForm({ question, onClose }) {
    const { t } = useTranslation()
    const updateQuestion = useAdminStore(s => s.updateQuestion)

    const [form, setForm] = useState({
        text_en: '',
        text_mr: '',
        correct_option: 1,
        explanation_en: '',
        explanation_mr: '',
        hint_en: '',
        hint_mr: '',
        difficulty: 'medium',
        tags: '',
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(false)

    useEffect(() => {
        if (question) {
            setForm({
                text_en: question.text_en || '',
                text_mr: question.text_mr || '',
                correct_option: question.correct_option || 1,
                explanation_en: question.explanation_en || '',
                explanation_mr: question.explanation_mr || '',
                hint_en: question.hint_en || '',
                hint_mr: question.hint_mr || '',
                difficulty: question.difficulty || 'medium',
                tags: (question.tags || []).join(', '),
            })
        }
    }, [question])

    const handleSave = async () => {
        setSaving(true)
        setError(null)
        setSuccess(false)
        try {
            await updateQuestion(question.id, {
                text_en: form.text_en || null,
                text_mr: form.text_mr || null,
                correct_option: Number(form.correct_option),
                explanation_en: form.explanation_en || null,
                explanation_mr: form.explanation_mr || null,
                hint_en: form.hint_en || null,
                hint_mr: form.hint_mr || null,
                difficulty: form.difficulty,
                tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
            })
            setSuccess(true)
            setTimeout(onClose, 800)
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to save question')
        } finally {
            setSaving(false)
        }
    }

    const Field = ({ label, name, textarea, rows = 4, type = 'text' }) => (
        <div>
            <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-surface-600">{label}</label>
                {textarea && form[name] && (
                    <span className="text-xs text-surface-400">{form[name].length} chars</span>
                )}
            </div>
            {textarea ? (
                <textarea
                    rows={rows}
                    value={form[name]}
                    onChange={e => setForm(f => ({ ...f, [name]: e.target.value }))}
                    className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400 resize-y"
                />
            ) : (
                <input
                    type={type}
                    value={form[name]}
                    onChange={e => setForm(f => ({ ...f, [name]: e.target.value }))}
                    className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
            )}
        </div>
    )

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={e => e.target === e.currentTarget && onClose()}>
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-surface-100">
                    <div>
                        <h2 className="text-lg font-bold text-surface-900">
                            {t('admin.editQuestion', 'Edit Question')} Q.{question?.question_no}
                        </h2>
                        <p className="text-xs text-surface-400 mt-0.5">ID: {question?.id}</p>
                    </div>
                    <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-100 text-surface-400">
                        ✕
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
                    )}
                    {success && (
                        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">Saved!</div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Field label="Question Text (English)" name="text_en" textarea rows={5} />
                        <Field label="Question Text (Marathi मराठी)" name="text_mr" textarea rows={5} />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-semibold text-surface-600 mb-1">Correct Option (1–4)</label>
                            <select
                                value={form.correct_option}
                                onChange={e => setForm(f => ({ ...f, correct_option: Number(e.target.value) }))}
                                className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400"
                            >
                                {[1, 2, 3, 4].map(n => <option key={n} value={n}>Option {n}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-surface-600 mb-1">Difficulty</label>
                            <select
                                value={form.difficulty}
                                onChange={e => setForm(f => ({ ...f, difficulty: e.target.value }))}
                                className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400"
                            >
                                {['easy', 'medium', 'hard'].map(d => (
                                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Field label="Explanation (English)" name="explanation_en" textarea />
                        <Field label="Explanation (Marathi)" name="explanation_mr" textarea />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Field label="Hint (English)" name="hint_en" />
                        <Field label="Hint (Marathi)" name="hint_mr" />
                    </div>

                    <Field label="Tags (comma-separated)" name="tags" />

                    {/* Option preview (read-only) */}
                    {question?.options?.length > 0 && (
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-xs font-semibold text-surface-600">Options (read-only)</label>
                                <span className="text-xs text-surface-400">
                                    To edit option text: delete this question and re-import with updated JSON/CSV
                                </span>
                            </div>
                            <div className="grid grid-cols-1 gap-1.5">
                                {question.options.map(opt => {
                                    const label = ['A', 'B', 'C', 'D'][opt.option_no - 1] || String(opt.option_no)
                                    const isCorrect = opt.option_no === question.correct_option
                                    return (
                                        <div key={opt.option_no} className={`flex items-start gap-2 px-3 py-2 rounded-lg text-sm ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-surface-50 border border-surface-100'}`}>
                                            <span className={`w-5 h-5 flex-shrink-0 flex items-center justify-center rounded-full text-xs font-bold ${isCorrect ? 'bg-green-500 text-white' : 'bg-surface-200 text-surface-600'}`}>
                                                {label}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                {opt.text_en && <p className="text-surface-700 truncate">{opt.text_en}</p>}
                                                {opt.text_mr && <p className="text-surface-500 text-xs truncate">{opt.text_mr}</p>}
                                                {!opt.text_en && !opt.text_mr && <p className="text-surface-400 italic">(image option)</p>}
                                            </div>
                                            {isCorrect && <span className="text-xs text-green-600 font-semibold flex-shrink-0">✓ correct</span>}
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-6 border-t border-surface-100">
                    <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-surface-600 hover:bg-surface-100 rounded-xl transition-colors">
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-5 py-2 text-sm font-semibold bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-50 transition-colors"
                    >
                        {saving ? 'Saving…' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    )
}
