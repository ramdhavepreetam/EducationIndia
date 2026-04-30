import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'
import { adminApi } from '../api/adminApi'

const QUESTION_TYPES = [
    { value: 'text',          label: 'Text' },
    { value: 'text_image',    label: 'Text + Image' },
    { value: 'image_only',    label: 'Image Only' },
    { value: 'context_text',  label: 'Context (Text)' },
    { value: 'context_image', label: 'Context (Image)' },
    { value: 'marathi_only',  label: 'Marathi Only' },
    { value: 'bilingual',     label: 'Bilingual' },
]

const IMAGE_TYPES = new Set(['text_image', 'image_only', 'context_image'])

export function QuestionEditForm({ question, onClose }) {
    const { t } = useTranslation()
    const updateQuestion = useAdminStore(s => s.updateQuestion)

    const [form, setForm] = useState({
        question_type: 'text',
        text_en: '',
        text_mr: '',
        question_image_url: '',
        question_image_alt_en: '',
        question_image_alt_mr: '',
        correct_option: 1,
        correct_options: [],
        is_multi_select: false,
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

    // Image upload state — file stored locally, uploaded only when Save is clicked
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState(null)  // blob URL
    const fileInputRef = useRef(null)

    const clearImageFile = () => {
        if (imagePreview) URL.revokeObjectURL(imagePreview)
        setImageFile(null)
        setImagePreview(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const handleFileSelect = (e) => {
        const file = e.target.files[0]
        if (!file) return
        clearImageFile()
        setImageFile(file)
        setImagePreview(URL.createObjectURL(file))
    }

    useEffect(() => {
        // Reset file selection when modal opens for a different question
        clearImageFile()
        if (question) {
            const correctOptions = question.correct_options?.length
                ? question.correct_options
                : (question.correct_option ? [question.correct_option] : [])
            setForm({
                question_type: question.question_type || 'text',
                text_en: question.text_en || '',
                text_mr: question.text_mr || '',
                question_image_url: question.question_image_url || '',
                question_image_alt_en: question.question_image_alt_en || '',
                question_image_alt_mr: question.question_image_alt_mr || '',
                correct_option: question.correct_option || 1,
                correct_options: correctOptions,
                is_multi_select: Boolean(question.is_multi_select),
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
            if (form.is_multi_select && form.correct_options.length === 0) {
                setError('Select at least one correct option for multi-select questions')
                setSaving(false)
                return
            }

            const showImage = IMAGE_TYPES.has(form.question_type)

            // Upload image to R2 now (only on Save, never on file pick)
            let imageUrl = form.question_image_url
            if (showImage && imageFile) {
                try {
                    const result = await adminApi.uploadImage(imageFile, 'question', question.id)
                    imageUrl = result.file_url
                } catch (uploadErr) {
                    setError('Image upload failed: ' + (uploadErr.response?.data?.detail || uploadErr.message || 'Unknown error'))
                    setSaving(false)
                    return
                }
            }

            await updateQuestion(question.id, {
                question_type: form.question_type,
                text_en: form.text_en || null,
                text_mr: form.text_mr || null,
                question_image_url: showImage ? (imageUrl || null) : null,
                question_image_alt_en: showImage ? (form.question_image_alt_en || null) : null,
                question_image_alt_mr: showImage ? (form.question_image_alt_mr || null) : null,
                is_multi_select: form.is_multi_select,
                correct_option: form.is_multi_select ? null : Number(form.correct_option),
                correct_options: form.is_multi_select
                    ? [...form.correct_options].sort((a, b) => a - b)
                    : null,
                explanation_en: form.explanation_en || null,
                explanation_mr: form.explanation_mr || null,
                hint_en: form.hint_en || null,
                hint_mr: form.hint_mr || null,
                difficulty: form.difficulty,
                tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
            })

            clearImageFile()
            setSuccess(true)
            setTimeout(onClose, 800)
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to save question')
        } finally {
            setSaving(false)
        }
    }

    const toggleCorrectOption = (optionNo) => {
        setForm(f => {
            const next = f.correct_options.includes(optionNo)
                ? f.correct_options.filter(n => n !== optionNo)
                : [...f.correct_options, optionNo].sort((a, b) => a - b)
            return { ...f, correct_options: next }
        })
    }

    const setAnswerMode = (isMulti) => {
        setForm(f => {
            if (isMulti) {
                return {
                    ...f,
                    is_multi_select: true,
                    correct_options: f.correct_options.length > 0
                        ? f.correct_options
                        : [Number(f.correct_option)],
                }
            }
            const first = f.correct_options[0] || f.correct_option || 1
            return {
                ...f,
                is_multi_select: false,
                correct_option: Number(first),
                correct_options: [Number(first)],
            }
        })
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

    const showImageFields = IMAGE_TYPES.has(form.question_type)

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

                    {/* Question Type */}
                    <div>
                        <label className="block text-xs font-semibold text-surface-600 mb-1">Question Type</label>
                        <select
                            value={form.question_type}
                            onChange={e => setForm(f => ({ ...f, question_type: e.target.value }))}
                            className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400"
                        >
                            {QUESTION_TYPES.map(qt => (
                                <option key={qt.value} value={qt.value}>{qt.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Field label="Question Text (English)" name="text_en" textarea rows={5} />
                        <Field label="Question Text (Marathi मराठी)" name="text_mr" textarea rows={5} />
                    </div>

                    {/* Image fields — shown only for image-bearing types */}
                    {showImageFields && (
                        <div className="space-y-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                            <p className="text-xs font-semibold text-amber-700">Image Fields</p>

                            {/* File picker — upload fires on Save, not here */}
                            <div>
                                <label className="block text-xs font-semibold text-surface-600 mb-1">
                                    Question Image
                                </label>
                                <div className="flex items-center gap-2 flex-wrap">
                                    <label className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium bg-white border border-surface-200 rounded-lg hover:bg-surface-50 text-surface-700 transition-colors">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                                        </svg>
                                        {imageFile ? 'Change Image' : 'Choose Image'}
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="image/jpeg,image/png,image/webp,image/gif"
                                            onChange={handleFileSelect}
                                            className="hidden"
                                        />
                                    </label>

                                    {imageFile ? (
                                        <>
                                            <span className="text-xs text-surface-600 font-medium truncate max-w-[180px]">
                                                {imageFile.name}
                                            </span>
                                            <span className="text-xs text-surface-400">
                                                ({(imageFile.size / 1024).toFixed(0)} KB)
                                            </span>
                                            <button
                                                type="button"
                                                onClick={clearImageFile}
                                                className="text-xs text-red-500 hover:text-red-700 font-medium"
                                            >
                                                ✕ Remove
                                            </button>
                                        </>
                                    ) : form.question_image_url ? (
                                        <span className="text-xs text-surface-400 truncate max-w-[240px]" title={form.question_image_url}>
                                            Current: {form.question_image_url.split('/').pop()}
                                        </span>
                                    ) : (
                                        <span className="text-xs text-surface-400">No image set</span>
                                    )}
                                </div>
                                <p className="text-xs text-amber-600 mt-1.5">
                                    JPEG · PNG · WebP · GIF &nbsp;·&nbsp; max 5 MB &nbsp;·&nbsp; uploaded when you click Save
                                </p>
                            </div>

                            {/* Alt text */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <Field label="Image Alt Text (English)" name="question_image_alt_en" />
                                <Field label="Image Alt Text (Marathi)" name="question_image_alt_mr" />
                            </div>

                            {/* Preview — local blob takes priority over stored URL */}
                            {(imagePreview || form.question_image_url) && (
                                <div>
                                    <p className="text-xs text-amber-600 mb-1">
                                        {imagePreview ? 'New image (not yet saved)' : 'Current image'}
                                    </p>
                                    <img
                                        src={imagePreview || form.question_image_url}
                                        alt="question preview"
                                        className="max-h-48 rounded-lg border border-amber-200 object-contain bg-white"
                                        onError={e => { e.target.style.display = 'none' }}
                                    />
                                </div>
                            )}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-semibold text-surface-600 mb-1">Answer Type</label>
                            <div className="inline-flex w-full rounded-lg border border-surface-200 bg-surface-50 p-1">
                                <button
                                    type="button"
                                    onClick={() => setAnswerMode(false)}
                                    className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                                        !form.is_multi_select
                                            ? 'bg-white text-brand-700 shadow-sm'
                                            : 'text-surface-500 hover:text-surface-700'
                                    }`}
                                >
                                    Single
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setAnswerMode(true)}
                                    className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                                        form.is_multi_select
                                            ? 'bg-white text-brand-700 shadow-sm'
                                            : 'text-surface-500 hover:text-surface-700'
                                    }`}
                                >
                                    Multi-select
                                </button>
                            </div>
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

                    <div>
                        <label className="block text-xs font-semibold text-surface-600 mb-2">
                            {form.is_multi_select ? 'Correct Options' : 'Correct Option'}
                        </label>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {[1, 2, 3, 4].map(n => {
                                const selected = form.is_multi_select
                                    ? form.correct_options.includes(n)
                                    : Number(form.correct_option) === n
                                return (
                                    <button
                                        key={n}
                                        type="button"
                                        onClick={() => {
                                            if (form.is_multi_select) toggleCorrectOption(n)
                                            else setForm(f => ({ ...f, correct_option: n, correct_options: [n] }))
                                        }}
                                        className={`px-3 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                                            selected
                                                ? 'bg-green-50 border-green-300 text-green-700'
                                                : 'bg-white border-surface-200 text-surface-600 hover:border-brand-300'
                                        }`}
                                    >
                                        Option {n}
                                    </button>
                                )
                            })}
                        </div>
                        {form.is_multi_select && (
                            <p className="mt-1 text-xs text-surface-400">
                                Select every correct answer. Student selection must exactly match this set.
                            </p>
                        )}
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
                                    const isCorrect = form.is_multi_select
                                        ? form.correct_options.includes(opt.option_no)
                                        : opt.option_no === Number(form.correct_option)
                                    return (
                                        <div key={opt.option_no} className={`flex items-start gap-2 px-3 py-2 rounded-lg text-sm ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-surface-50 border border-surface-100'}`}>
                                            <span className={`w-5 h-5 flex-shrink-0 flex items-center justify-center rounded-full text-xs font-bold ${isCorrect ? 'bg-green-500 text-white' : 'bg-surface-200 text-surface-600'}`}>
                                                {label}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                {opt.text_en && <p className="text-surface-700 truncate">{opt.text_en}</p>}
                                                {opt.text_mr && <p className="text-surface-500 text-xs truncate">{opt.text_mr}</p>}
                                                {opt.image_url && (
                                                    <img src={opt.image_url} alt={opt.image_alt_en || ''} className="mt-1 max-h-16 object-contain rounded" />
                                                )}
                                                {!opt.text_en && !opt.text_mr && !opt.image_url && <p className="text-surface-400 italic">(empty option)</p>}
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
                        {saving ? (imageFile ? 'Uploading…' : 'Saving…') : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    )
}
