import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, FileText, UploadCloud } from 'lucide-react'
import { useAdminStore } from '../store/adminStore'

const STRATEGIES = [
    { value: 'auto', label: 'Auto' },
    { value: 'english', label: 'English only' },
    { value: 'marathi', label: 'Marathi only' },
    { value: 'bilingual', label: 'Bilingual merge' },
]

function FileField({ label, file, onChange, required = false }) {
    return (
        <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-surface-500">{label}</span>
            <div className="mt-1 flex min-h-[44px] items-center gap-3 rounded-lg border border-surface-200 bg-white px-3 py-2">
                <FileText className="h-4 w-4 flex-none text-surface-400" />
                <span className="min-w-0 flex-1 truncate text-sm text-surface-700">
                    {file?.name || (required ? 'Required PDF' : 'Optional PDF')}
                </span>
                <input
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={(event) => onChange(event.target.files?.[0] || null)}
                    className="text-xs text-surface-500 file:mr-3 file:rounded-md file:border-0 file:bg-surface-100 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-surface-700 hover:file:bg-surface-200"
                />
            </div>
        </label>
    )
}

export function PdfExamImporter() {
    const {
        exams,
        fetchAllExams,
        runPdfImport,
        pdfImporting,
        pdfImportResult,
    } = useAdminStore()

    const [examId, setExamId] = useState('')
    const [strategy, setStrategy] = useState('auto')
    const [answerSet, setAnswerSet] = useState('A')
    const [englishPdf, setEnglishPdf] = useState(null)
    const [marathiPdf, setMarathiPdf] = useState(null)
    const [answerKeyPdf, setAnswerKeyPdf] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchAllExams()
    }, [fetchAllExams])

    const selectedExam = useMemo(
        () => exams.find(exam => String(exam.id) === String(examId)),
        [exams, examId]
    )

    const buildFormData = (mode) => {
        const form = new FormData()
        form.append('exam_id', examId)
        form.append('mode', mode)
        form.append('language_strategy', strategy)
        form.append('answer_set', answerSet)
        if (englishPdf) form.append('english_question_pdf', englishPdf)
        if (marathiPdf) form.append('marathi_question_pdf', marathiPdf)
        if (answerKeyPdf) form.append('answer_key_pdf', answerKeyPdf)
        return form
    }

    const run = async (mode) => {
        setError(null)
        if (!examId || !answerKeyPdf) {
            setError('Select an exam and upload the answer key PDF.')
            return
        }
        if (!englishPdf && !marathiPdf) {
            setError('Upload at least one question paper PDF.')
            return
        }
        try {
            await runPdfImport(buildFormData(mode))
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'PDF import failed')
        }
    }

    return (
        <section className="mb-8 rounded-lg border border-surface-200 bg-surface-50 p-4 sm:p-5">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-base font-bold text-surface-900">PDF Exam Import</h2>
                    <p className="mt-0.5 text-sm text-surface-500">Question papers plus answer key, with preview before write.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        type="button"
                        disabled={pdfImporting}
                        onClick={() => run('preview')}
                        className="inline-flex items-center gap-2 rounded-lg border border-surface-300 bg-white px-4 py-2 text-sm font-semibold text-surface-800 hover:bg-surface-100 disabled:opacity-50"
                    >
                        <FileText className="h-4 w-4" />
                        Preview
                    </button>
                    <button
                        type="button"
                        disabled={pdfImporting || !pdfImportResult || pdfImportResult.errors?.length > 0}
                        onClick={() => run('apply')}
                        className="inline-flex items-center gap-2 rounded-lg bg-accent-500 px-4 py-2 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50"
                    >
                        <UploadCloud className="h-4 w-4" />
                        {pdfImporting ? 'Working...' : 'Apply'}
                    </button>
                </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-4">
                <label className="block lg:col-span-2">
                    <span className="text-xs font-semibold uppercase tracking-wide text-surface-500">Target exam</span>
                    <select
                        value={examId}
                        onChange={(event) => setExamId(event.target.value)}
                        className="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-surface-800"
                    >
                        <option value="">Select exam</option>
                        {exams.map(exam => (
                            <option key={exam.id} value={exam.id}>
                                #{exam.id} {exam.event_year || ''} Std {exam.std_class || '-'} {exam.paper_code} {exam.title_en}
                            </option>
                        ))}
                    </select>
                    {selectedExam && (
                        <p className="mt-1 text-xs text-surface-500">
                            Existing questions: {selectedExam.question_count} / {selectedExam.total_questions}
                        </p>
                    )}
                </label>

                <label className="block">
                    <span className="text-xs font-semibold uppercase tracking-wide text-surface-500">Import mode</span>
                    <select
                        value={strategy}
                        onChange={(event) => setStrategy(event.target.value)}
                        className="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-surface-800"
                    >
                        {STRATEGIES.map(item => (
                            <option key={item.value} value={item.value}>{item.label}</option>
                        ))}
                    </select>
                </label>

                <label className="block">
                    <span className="text-xs font-semibold uppercase tracking-wide text-surface-500">Answer set</span>
                    <select
                        value={answerSet}
                        onChange={(event) => setAnswerSet(event.target.value)}
                        className="mt-1 w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm text-surface-800"
                    >
                        {['A', 'B', 'C', 'D'].map(value => <option key={value} value={value}>{value}</option>)}
                    </select>
                </label>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <FileField label="English question paper" file={englishPdf} onChange={setEnglishPdf} />
                <FileField label="Marathi question paper" file={marathiPdf} onChange={setMarathiPdf} />
                <FileField label="Answer key" file={answerKeyPdf} onChange={setAnswerKeyPdf} required />
            </div>

            {error && (
                <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
                    <span>{error}</span>
                </div>
            )}

            {pdfImportResult && (
                <div className="mt-5 space-y-3">
                    <div className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${
                        pdfImportResult.errors?.length
                            ? 'border-amber-200 bg-amber-50 text-amber-800'
                            : 'border-green-200 bg-green-50 text-green-800'
                    }`}>
                        {pdfImportResult.errors?.length ? (
                            <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
                        ) : (
                            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none" />
                        )}
                        <div>
                            <p className="font-semibold">
                                {pdfImportResult.mode === 'apply' ? 'Applied' : 'Preview'}:
                                {' '}{pdfImportResult.importable_count} importable / {pdfImportResult.question_count} extracted
                            </p>
                            <p className="text-xs opacity-80">
                                Keys read: {pdfImportResult.key_count}
                                {pdfImportResult.cancelled_questions?.length ? ` | Cancelled: ${pdfImportResult.cancelled_questions.join(', ')}` : ''}
                                {pdfImportResult.inserted ? ` | Inserted: ${pdfImportResult.inserted}` : ''}
                            </p>
                        </div>
                    </div>

                    {pdfImportResult.errors?.length > 0 && (
                        <div className="max-h-40 overflow-auto rounded-lg border border-amber-200 bg-white p-3 text-xs text-amber-900">
                            {pdfImportResult.errors.slice(0, 30).map((item, index) => (
                                <p key={index}>{item}</p>
                            ))}
                        </div>
                    )}

                    <div className="overflow-x-auto rounded-lg border border-surface-200 bg-white">
                        <table className="min-w-full divide-y divide-surface-200 text-sm">
                            <thead className="bg-surface-100 text-left text-xs uppercase tracking-wide text-surface-500">
                                <tr>
                                    <th className="px-3 py-2">Q</th>
                                    <th className="px-3 py-2">Key</th>
                                    <th className="px-3 py-2">Text</th>
                                    <th className="px-3 py-2">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {pdfImportResult.preview?.slice(0, 15).map(row => (
                                    <tr key={row.question_no}>
                                        <td className="px-3 py-2 font-semibold text-surface-800">{row.question_no}</td>
                                        <td className="px-3 py-2 text-surface-700">
                                            {row.is_cancelled ? 'Cancelled' : (row.correct_option || '-')}
                                        </td>
                                        <td className="max-w-xl px-3 py-2 text-surface-700">
                                            <span className="block max-h-10 overflow-hidden">{row.text_en || row.text_mr || '-'}</span>
                                        </td>
                                        <td className="px-3 py-2 text-xs">
                                            {row.is_cancelled ? (
                                                <span className="text-surface-600">{row.cancelled_reason || 'Cancelled'}</span>
                                            ) : row.warnings?.length ? (
                                                <span className="text-amber-700">{row.warnings[0]}</span>
                                            ) : (
                                                <span className="text-green-700">Ready</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </section>
    )
}
