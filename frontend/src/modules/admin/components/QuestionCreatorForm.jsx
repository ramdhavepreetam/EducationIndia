import { useState, useEffect } from 'react'
import { useAdminStore } from '../store/adminStore'
import { adminApi } from '../api/adminApi'

const QUESTION_TYPES = [
    { value: 'text', label: 'Text — plain text question + text options' },
    { value: 'text_image', label: 'Text + Image — text question with an image' },
    { value: 'image_only', label: 'Image Only — image IS the question' },
    { value: 'context_text', label: 'Context Text — belongs to a passage/poem' },
    { value: 'context_image', label: 'Context Image — belongs to a pictograph/figure' },
    { value: 'marathi_only', label: 'Marathi Only — no English version' },
    { value: 'bilingual', label: 'Bilingual — shown EN + MR side by side' },
]

const OPTION_LABELS = ['A', 'B', 'C', 'D']

const emptyForm = () => ({
    examId: '',
    sectionId: '',
    topicId: '',
    questionNo: '',
    questionType: 'text',
    textEn: '',
    textMr: '',
    questionImageUrl: '',
    correctOption: 1,
    difficulty: 'medium',
    tags: '',
    explanationEn: '',
    explanationMr: '',
    hintEn: '',
    hintMr: '',
    options: [
        { text_en: '', text_mr: '' },
        { text_en: '', text_mr: '' },
        { text_en: '', text_mr: '' },
        { text_en: '', text_mr: '' },
    ],
})

/**
 * QuestionCreatorForm — Add Question tab for QuestionManagerPage.
 * Creates a single question by wrapping it in a BulkImportSchema payload.
 * Calls adminApi.bulkImport() under the hood.
 */
export function QuestionCreatorForm({ onSuccess }) {
    const { exams, examsLoading, fetchAllExams, questions, fetchQuestions, runBulkImport, bulkImporting } = useAdminStore()

    const [form, setForm] = useState(emptyForm())
    const [sections, setSections] = useState([]) // [{id, section_label, subject_en, topics:[]}]
    const [loadingSections, setLoadingSections] = useState(false)
    const [sectionsManual, setSectionsManual] = useState(false) // fallback: manual ID entry
    const [showExplanation, setShowExplanation] = useState(false)
    const [showHints, setShowHints] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)

    // Load exam list on mount
    useEffect(() => {
        if (exams.length === 0) fetchAllExams()
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    // Default to first exam
    useEffect(() => {
        if (exams.length > 0 && !form.examId) {
            setForm(f => ({ ...f, examId: exams[0].id }))
        }
    }, [exams]) // eslint-disable-line react-hooks/exhaustive-deps

    // When exam changes: fetch sections and questions (for Q.No suggestion)
    useEffect(() => {
        if (!form.examId) return
        setSections([])
        setSectionsManual(false)
        setForm(f => ({ ...f, sectionId: '', topicId: '', questionNo: '' }))

        // Try to get sections from catalog
        setLoadingSections(true)
        adminApi.getExamDetail(Number(form.examId)).then(detail => {
            if (detail?.sections?.length > 0) {
                setSections(detail.sections)
                setSectionsManual(false)
            } else {
                setSectionsManual(true)
            }
        }).finally(() => setLoadingSections(false))

        // Load questions for Q.No suggestion
        fetchQuestions(Number(form.examId))
    }, [form.examId]) // eslint-disable-line react-hooks/exhaustive-deps

    // Auto-suggest Q.No when section changes
    useEffect(() => {
        if (!form.sectionId || questions.length === 0) return
        const sectionQuestions = questions.filter(q => q.section_id === Number(form.sectionId))
        const maxNo = sectionQuestions.length > 0
            ? Math.max(...sectionQuestions.map(q => q.question_no))
            : 0
        setForm(f => ({ ...f, questionNo: String(maxNo + 1) }))
    }, [form.sectionId]) // eslint-disable-line react-hooks/exhaustive-deps

    const updateOption = (index, field, value) => {
        setForm(f => {
            const opts = [...f.options]
            opts[index] = { ...opts[index], [field]: value }
            return { ...f, options: opts }
        })
    }

    const getTopicsForSection = () => {
        if (!form.sectionId) return []
        const section = sections.find(s => s.id === Number(form.sectionId))
        return section?.topics || []
    }

    const validate = () => {
        if (!form.examId) return 'Select an exam'
        if (!form.sectionId) return 'Enter a section ID'
        if (!form.topicId) return 'Enter a topic ID'
        if (!form.questionNo || isNaN(Number(form.questionNo))) return 'Enter a valid question number'
        if (!form.textEn && !form.textMr && form.questionType !== 'image_only') return 'Enter question text (English or Marathi)'
        const optionsFilled = form.options.filter(o => o.text_en || o.text_mr)
        if (form.questionType !== 'image_only' && optionsFilled.length < 4) return 'Fill in all 4 option texts'
        if (!form.correctOption || form.correctOption < 1 || form.correctOption > 4) return 'Select a correct option (1–4)'
        return null
    }

    const handleSubmit = async () => {
        setError(null)
        setSuccess(null)
        const validationError = validate()
        if (validationError) { setError(validationError); return }

        const payload = {
            exam_id: Number(form.examId),
            contexts: [],
            questions: [{
                section_id: Number(form.sectionId),
                topic_id: Number(form.topicId),
                question_no: Number(form.questionNo),
                question_type: form.questionType,
                text_en: form.textEn || null,
                text_mr: form.textMr || null,
                question_image_url: form.questionImageUrl || null,
                correct_option: Number(form.correctOption),
                difficulty: form.difficulty,
                marks: 2,
                tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
                explanation_en: form.explanationEn || null,
                explanation_mr: form.explanationMr || null,
                hint_en: form.hintEn || null,
                hint_mr: form.hintMr || null,
                options: form.options.map((opt, i) => ({
                    option_no: i + 1,
                    text_en: opt.text_en || null,
                    text_mr: opt.text_mr || null,
                    image_url: null,
                    image_alt_en: null,
                    image_alt_mr: null,
                })),
            }],
        }

        try {
            const result = await runBulkImport(payload)
            if (result.inserted > 0) {
                setSuccess(`Question Q.${form.questionNo} added successfully!`)
                setForm(f => ({ ...emptyForm(), examId: f.examId }))
                setShowExplanation(false)
                setShowHints(false)
            } else if (result.errors?.length > 0) {
                setError(result.errors[0])
            } else {
                setError('Question may already exist (duplicate Q.No). Try a different number.')
            }
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to save question')
        }
    }

    const Label = ({ children, required }) => (
        <label className="block text-xs font-semibold text-surface-600 mb-1">
            {children} {required && <span className="text-red-500">*</span>}
        </label>
    )

    const inputCls = "w-full text-sm border border-surface-200 rounded-lg px-3 py-2 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
    const textareaCls = `${inputCls} resize-none`

    const topics = getTopicsForSection()

    return (
        <div className="max-w-4xl">
            <div className="bg-white rounded-xl border border-surface-100 shadow-sm">
                {/* Header */}
                <div className="px-6 py-4 border-b border-surface-100">
                    <h2 className="text-base font-bold text-surface-900">Add a Single Question</h2>
                    <p className="text-xs text-surface-400 mt-0.5">
                        Fill in the form below. For context questions or image-only questions, use the Import tab with JSON.
                    </p>
                </div>

                <div className="p-6 space-y-6">
                    {/* Success */}
                    {success && (
                        <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl">
                            <span className="text-green-600 text-xl">✓</span>
                            <div>
                                <p className="text-sm font-semibold text-green-800">{success}</p>
                                <button onClick={onSuccess} className="text-xs text-green-600 hover:underline">
                                    Go to Browse tab to see all questions →
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">{error}</div>
                    )}

                    {/* ── Row 1: Exam + Type ── */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label required>Exam</Label>
                            <select
                                value={form.examId}
                                onChange={e => setForm(f => ({ ...f, examId: e.target.value }))}
                                disabled={examsLoading}
                                className={inputCls}
                            >
                                {exams.length === 0 && <option value="">Loading…</option>}
                                {exams.map(ex => (
                                    <option key={ex.id} value={ex.id}>
                                        {ex.title_en} ({ex.paper_code}){!ex.is_active ? ' — unpublished' : ''}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <Label required>Question Type</Label>
                            <select
                                value={form.questionType}
                                onChange={e => setForm(f => ({ ...f, questionType: e.target.value }))}
                                className={inputCls}
                            >
                                {QUESTION_TYPES.map(t => (
                                    <option key={t.value} value={t.value}>{t.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* ── Row 2: Section + Topic + Q.No ── */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <Label required>Section</Label>
                            {loadingSections ? (
                                <div className="h-9 bg-surface-100 rounded-lg animate-pulse" />
                            ) : sectionsManual ? (
                                <>
                                    <input
                                        type="number"
                                        placeholder="Section ID (e.g. 1)"
                                        value={form.sectionId}
                                        onChange={e => setForm(f => ({ ...f, sectionId: e.target.value, topicId: '' }))}
                                        className={inputCls}
                                        min={1}
                                    />
                                    <p className="text-xs text-amber-600 mt-1">
                                        ⚠ Exam inactive — enter ID manually. Paper 501: Sec 1=English, 2=Math. Paper 502: Sec 3=Marathi, 4=Intelligence.
                                    </p>
                                </>
                            ) : (
                                <select
                                    value={form.sectionId}
                                    onChange={e => setForm(f => ({ ...f, sectionId: e.target.value, topicId: '' }))}
                                    className={inputCls}
                                >
                                    <option value="">Select section…</option>
                                    {sections.map(s => (
                                        <option key={s.id} value={s.id}>
                                            Section {s.section_label} — {s.subject_en}
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <div>
                            <Label required>Topic</Label>
                            {sectionsManual || topics.length === 0 ? (
                                <>
                                    <input
                                        type="number"
                                        placeholder="Topic ID (e.g. 3)"
                                        value={form.topicId}
                                        onChange={e => setForm(f => ({ ...f, topicId: e.target.value }))}
                                        className={inputCls}
                                        min={1}
                                    />
                                    {!sectionsManual && form.sectionId && (
                                        <p className="text-xs text-surface-400 mt-1">Select a section first to see topics</p>
                                    )}
                                </>
                            ) : (
                                <select
                                    value={form.topicId}
                                    onChange={e => setForm(f => ({ ...f, topicId: e.target.value }))}
                                    className={inputCls}
                                    disabled={!form.sectionId}
                                >
                                    <option value="">Select topic…</option>
                                    {topics.map(t => (
                                        <option key={t.id} value={t.id}>{t.name_en}</option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <div>
                            <Label required>Question No.</Label>
                            <input
                                type="number"
                                placeholder="e.g. 26"
                                value={form.questionNo}
                                onChange={e => setForm(f => ({ ...f, questionNo: e.target.value }))}
                                className={inputCls}
                                min={1}
                                max={75}
                            />
                            {form.questionNo && (
                                <p className="text-xs text-surface-400 mt-1">Auto-suggested from max existing</p>
                            )}
                        </div>
                    </div>

                    {/* ── Row 3: Question Text ── */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label required={form.questionType !== 'image_only' && form.questionType !== 'marathi_only'}>
                                Question Text (English)
                            </Label>
                            <textarea
                                rows={4}
                                value={form.textEn}
                                onChange={e => setForm(f => ({ ...f, textEn: e.target.value }))}
                                className={textareaCls}
                                placeholder="Enter question in English…"
                                disabled={form.questionType === 'marathi_only' || form.questionType === 'image_only'}
                            />
                        </div>
                        <div>
                            <Label required={form.questionType === 'marathi_only'}>
                                Question Text (मराठी)
                            </Label>
                            <textarea
                                rows={4}
                                value={form.textMr}
                                onChange={e => setForm(f => ({ ...f, textMr: e.target.value }))}
                                className={textareaCls}
                                placeholder="मराठीत प्रश्न लिहा…"
                                disabled={form.questionType === 'image_only'}
                            />
                        </div>
                    </div>

                    {/* Image URL (for text_image / image_only) */}
                    {(form.questionType === 'text_image' || form.questionType === 'image_only') && (
                        <div>
                            <Label>Question Image URL</Label>
                            <input
                                type="url"
                                value={form.questionImageUrl}
                                onChange={e => setForm(f => ({ ...f, questionImageUrl: e.target.value }))}
                                className={inputCls}
                                placeholder="https://… (upload via Image Uploader first)"
                            />
                            <p className="text-xs text-surface-400 mt-1">
                                Upload images in the <strong>Image Uploader</strong> admin page, then paste the URL here.
                            </p>
                        </div>
                    )}

                    {/* ── Options ── */}
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <Label>Options</Label>
                            <span className="text-xs text-surface-400">Correct option is highlighted green</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {form.options.map((opt, i) => (
                                <div
                                    key={i}
                                    className={`p-3 rounded-xl border-2 transition-colors ${
                                        form.correctOption === i + 1
                                            ? 'border-green-400 bg-green-50'
                                            : 'border-surface-200 bg-white'
                                    }`}
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <button
                                            onClick={() => setForm(f => ({ ...f, correctOption: i + 1 }))}
                                            className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                                                form.correctOption === i + 1
                                                    ? 'bg-green-500 text-white'
                                                    : 'bg-surface-200 text-surface-600 hover:bg-surface-300'
                                            }`}
                                            title="Mark as correct answer"
                                        >
                                            {OPTION_LABELS[i]}
                                        </button>
                                        <span className="text-xs font-semibold text-surface-500">
                                            Option {OPTION_LABELS[i]}
                                            {form.correctOption === i + 1 && (
                                                <span className="ml-1 text-green-600">✓ correct</span>
                                            )}
                                        </span>
                                    </div>
                                    <input
                                        type="text"
                                        placeholder={`English…`}
                                        value={opt.text_en}
                                        onChange={e => updateOption(i, 'text_en', e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-1.5 mb-1.5 focus:outline-none focus:ring-2 focus:ring-brand-400"
                                    />
                                    <input
                                        type="text"
                                        placeholder={`मराठी…`}
                                        value={opt.text_mr}
                                        onChange={e => updateOption(i, 'text_mr', e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-400"
                                    />
                                </div>
                            ))}
                        </div>
                        <p className="text-xs text-surface-400 mt-2">
                            Click the letter button (A/B/C/D) to mark that option as the correct answer.
                        </p>
                    </div>

                    {/* ── Difficulty + Tags ── */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label>Difficulty</Label>
                            <select
                                value={form.difficulty}
                                onChange={e => setForm(f => ({ ...f, difficulty: e.target.value }))}
                                className={inputCls}
                            >
                                <option value="easy">Easy</option>
                                <option value="medium">Medium</option>
                                <option value="hard">Hard</option>
                            </select>
                        </div>
                        <div>
                            <Label>Tags (comma-separated)</Label>
                            <input
                                type="text"
                                placeholder="grammar, vocabulary, comprehension"
                                value={form.tags}
                                onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                                className={inputCls}
                            />
                        </div>
                    </div>

                    {/* ── Collapsible: Explanation ── */}
                    <div className="border border-surface-200 rounded-xl overflow-hidden">
                        <button
                            onClick={() => setShowExplanation(v => !v)}
                            className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-surface-700 hover:bg-surface-50 transition-colors"
                        >
                            <span>Explanation (shown after exam)</span>
                            <span className="text-surface-400">{showExplanation ? '▲' : '▼'}</span>
                        </button>
                        {showExplanation && (
                            <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-surface-100">
                                <div className="pt-3">
                                    <Label>Explanation (English)</Label>
                                    <textarea rows={3} value={form.explanationEn}
                                        onChange={e => setForm(f => ({ ...f, explanationEn: e.target.value }))}
                                        className={textareaCls} placeholder="Why is this the correct answer?" />
                                </div>
                                <div className="pt-3">
                                    <Label>Explanation (मराठी)</Label>
                                    <textarea rows={3} value={form.explanationMr}
                                        onChange={e => setForm(f => ({ ...f, explanationMr: e.target.value }))}
                                        className={textareaCls} placeholder="हे उत्तर बरोबर का आहे?" />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Collapsible: Hints ── */}
                    <div className="border border-surface-200 rounded-xl overflow-hidden">
                        <button
                            onClick={() => setShowHints(v => !v)}
                            className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-surface-700 hover:bg-surface-50 transition-colors"
                        >
                            <span>Hints (practice mode only)</span>
                            <span className="text-surface-400">{showHints ? '▲' : '▼'}</span>
                        </button>
                        {showHints && (
                            <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-surface-100">
                                <div className="pt-3">
                                    <Label>Hint (English)</Label>
                                    <input type="text" value={form.hintEn}
                                        onChange={e => setForm(f => ({ ...f, hintEn: e.target.value }))}
                                        className={inputCls} placeholder="A small nudge in the right direction" />
                                </div>
                                <div className="pt-3">
                                    <Label>Hint (मराठी)</Label>
                                    <input type="text" value={form.hintMr}
                                        onChange={e => setForm(f => ({ ...f, hintMr: e.target.value }))}
                                        className={inputCls} placeholder="योग्य दिशेने एक संकेत" />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between gap-4 px-6 py-4 border-t border-surface-100 bg-surface-50 rounded-b-xl">
                    <p className="text-xs text-surface-400">
                        For context questions (passages, poems) or image options, use the <strong>Import</strong> tab with a JSON file.
                    </p>
                    <button
                        onClick={handleSubmit}
                        disabled={bulkImporting}
                        className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-50 transition-colors whitespace-nowrap"
                    >
                        {bulkImporting ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Saving…
                            </>
                        ) : '+ Save Question'}
                    </button>
                </div>
            </div>
        </div>
    )
}
