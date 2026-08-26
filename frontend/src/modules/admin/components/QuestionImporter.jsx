import { useState, useRef, useCallback } from 'react'
import { useAdminStore } from '../store/adminStore'
import { PdfExamImporter } from './PdfExamImporter'

// ── CSV utilities ─────────────────────────────────────────────────────────────

function parseCSVRow(line) {
    const result = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
        if (line[i] === '"') {
            inQuotes = !inQuotes
        } else if (line[i] === ',' && !inQuotes) {
            result.push(current.trim())
            current = ''
        } else {
            current += line[i]
        }
    }
    result.push(current.trim())
    return result
}

function parseCSV(text) {
    const lines = text.trim().split('\n').filter(l => l.trim())
    if (lines.length < 2) return []
    const headers = parseCSVRow(lines[0]).map(h => h.trim())
    return lines.slice(1).map(line => {
        const values = parseCSVRow(line)
        return Object.fromEntries(headers.map((h, i) => [h, values[i] || '']))
    })
}

function csvRowsToPayload(rows, overrideExamId) {
    const examId = overrideExamId || Number(rows[0]?.exam_id)
    const questions = rows.map(row => ({
        section_id: Number(row.section_id),
        topic_id: Number(row.topic_id),
        question_no: Number(row.q_no),
        question_type: row.type || 'text',
        text_en: row.text_en || null,
        text_mr: row.text_mr || null,
        question_image_url: row.image_url || null,
        correct_option: Number(row.correct),
        difficulty: row.difficulty || 'medium',
        marks: 2,
        tags: row.tags ? row.tags.split(';').map(t => t.trim()).filter(Boolean) : [],
        explanation_en: row.explanation_en || null,
        explanation_mr: row.explanation_mr || null,
        hint_en: null,
        hint_mr: null,
        options: [
            { option_no: 1, text_en: row.opt_a_en || null, text_mr: row.opt_a_mr || null, image_url: null, image_alt_en: null, image_alt_mr: null },
            { option_no: 2, text_en: row.opt_b_en || null, text_mr: row.opt_b_mr || null, image_url: null, image_alt_en: null, image_alt_mr: null },
            { option_no: 3, text_en: row.opt_c_en || null, text_mr: row.opt_c_mr || null, image_url: null, image_alt_en: null, image_alt_mr: null },
            { option_no: 4, text_en: row.opt_d_en || null, text_mr: row.opt_d_mr || null, image_url: null, image_alt_en: null, image_alt_mr: null },
        ],
    }))
    return { exam_id: examId, contexts: [], questions }
}

// ── JSON validation ───────────────────────────────────────────────────────────

function validateJSONPayload(payload) {
    const errors = []
    if (!payload.exam_id || typeof payload.exam_id !== 'number') {
        errors.push('Missing or invalid "exam_id" (must be a number)')
    }
    if (!Array.isArray(payload.questions) || payload.questions.length === 0) {
        errors.push('Missing or empty "questions" array')
        return errors
    }
    payload.questions.forEach((q, i) => {
        const n = i + 1
        if (!q.section_id) errors.push(`Q${n}: missing section_id`)
        if (!q.topic_id) errors.push(`Q${n}: missing topic_id`)
        if (!q.question_no) errors.push(`Q${n}: missing question_no`)
        if (!q.correct_option || q.correct_option < 1 || q.correct_option > 4) {
            errors.push(`Q${n}: correct_option must be 1–4`)
        }
        if (!Array.isArray(q.options) || q.options.length !== 4) {
            errors.push(`Q${n}: must have exactly 4 options`)
        }
    })
    return errors
}

function validateCSVRows(rows) {
    const errors = []
    const requiredCols = ['section_id', 'topic_id', 'q_no', 'correct']
    if (rows.length === 0) {
        errors.push('CSV file has no data rows')
        return errors
    }
    const cols = Object.keys(rows[0])
    requiredCols.forEach(col => {
        if (!cols.includes(col)) errors.push(`Missing required column: "${col}"`)
    })
    if (errors.length > 0) return errors

    rows.forEach((row, i) => {
        const n = i + 1
        const correct = Number(row.correct)
        if (isNaN(correct) || correct < 1 || correct > 4) {
            errors.push(`Row ${n}: "correct" must be 1–4`)
        }
        if (!row.section_id || isNaN(Number(row.section_id))) {
            errors.push(`Row ${n}: invalid section_id`)
        }
        if (!row.q_no || isNaN(Number(row.q_no))) {
            errors.push(`Row ${n}: invalid q_no`)
        }
        const hasAnyOption = row.opt_a_en || row.opt_a_mr || row.opt_b_en || row.opt_b_mr
        if (!hasAnyOption) {
            errors.push(`Row ${n}: no option text found (need opt_a_en, opt_b_en, etc.)`)
        }
    })
    return errors
}

// ── Templates ─────────────────────────────────────────────────────────────────

const JSON_TEMPLATE = {
    exam_id: 1,
    contexts: [],
    questions: [
        {
            section_id: 1,
            topic_id: 1,
            question_no: 1,
            question_type: 'text',
            text_en: 'What is the capital of Maharashtra?',
            text_mr: 'महाराष्ट्राची राजधानी कोणती आहे?',
            correct_option: 2,
            difficulty: 'easy',
            marks: 2,
            tags: ['geography', 'maharashtra'],
            explanation_en: 'Mumbai is the financial and administrative capital of Maharashtra.',
            explanation_mr: null,
            hint_en: 'It is on the western coast of India.',
            hint_mr: null,
            options: [
                { option_no: 1, text_en: 'Pune', text_mr: 'पुणे', image_url: null, image_alt_en: null, image_alt_mr: null },
                { option_no: 2, text_en: 'Mumbai', text_mr: 'मुंबई', image_url: null, image_alt_en: null, image_alt_mr: null },
                { option_no: 3, text_en: 'Nagpur', text_mr: 'नागपूर', image_url: null, image_alt_en: null, image_alt_mr: null },
                { option_no: 4, text_en: 'Nashik', text_mr: 'नाशिक', image_url: null, image_alt_en: null, image_alt_mr: null },
            ],
        },
    ],
}

const CSV_TEMPLATE_HEADER = 'exam_id,section_id,topic_id,q_no,type,text_en,text_mr,opt_a_en,opt_a_mr,opt_b_en,opt_b_mr,opt_c_en,opt_c_mr,opt_d_en,opt_d_mr,correct,difficulty,tags,explanation_en,explanation_mr'
const CSV_TEMPLATE_ROW = '1,1,1,1,text,"What is the capital of Maharashtra?","महाराष्ट्राची राजधानी?","Pune","पुणे","Mumbai","मुंबई","Nagpur","नागपूर","Nashik","नाशिक",2,easy,,Mumbai is the capital of Maharashtra.,'

function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * QuestionImporter — Import tab for QuestionManagerPage.
 * Supports JSON and CSV formats with drag-and-drop, validation preview,
 * and exam_id auto-detection vs. manual override.
 */
export function QuestionImporter() {
    const { exams, fetchAllExams, runBulkImport, bulkImporting, bulkImportResult } = useAdminStore()

    const [format, setFormat] = useState('json') // 'json' | 'csv'
    const [examMode, setExamMode] = useState('auto') // 'auto' | 'override'
    const [overrideExamId, setOverrideExamId] = useState('')
    const [dragOver, setDragOver] = useState(false)
    const [fileInfo, setFileInfo] = useState(null) // { name, size }
    const [preview, setPreview] = useState(null)   // { payload, questionCount, examId, errors[] }
    const [parseError, setParseError] = useState(null)
    const [importError, setImportError] = useState(null)
    const fileRef = useRef(null)

    // Load exams for override selector
    const ensureExams = () => {
        if (exams.length === 0) fetchAllExams()
    }

    const processFile = useCallback(async (file) => {
        setParseError(null)
        setPreview(null)
        setImportError(null)
        setFileInfo({ name: file.name, size: (file.size / 1024).toFixed(1) + ' KB' })

        const text = await file.text()

        if (format === 'json') {
            let payload
            try {
                payload = JSON.parse(text)
            } catch {
                setParseError('Invalid JSON — check file syntax')
                return
            }
            const errors = validateJSONPayload(payload)
            const examId = examMode === 'override' && overrideExamId
                ? Number(overrideExamId)
                : payload.exam_id
            setPreview({
                payload: { ...payload, exam_id: examId },
                questionCount: payload.questions?.length || 0,
                contextCount: payload.contexts?.length || 0,
                examId,
                errors,
            })
        } else {
            // CSV
            let rows
            try {
                rows = parseCSV(text)
            } catch {
                setParseError('Could not parse CSV — check the file format')
                return
            }
            const errors = validateCSVRows(rows)
            const examId = examMode === 'override' && overrideExamId
                ? Number(overrideExamId)
                : Number(rows[0]?.exam_id)
            const payload = csvRowsToPayload(rows, examMode === 'override' ? Number(overrideExamId) : null)
            setPreview({
                payload,
                questionCount: rows.length,
                contextCount: 0,
                examId,
                errors,
            })
        }
    }, [format, examMode, overrideExamId])

    const handleFileInput = (e) => {
        const file = e.target.files?.[0]
        if (file) processFile(file)
        if (fileRef.current) fileRef.current.value = ''
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files?.[0]
        if (file) processFile(file)
    }

    const handleImport = async () => {
        if (!preview?.payload || preview.errors?.length > 0) return
        setImportError(null)
        try {
            await runBulkImport(preview.payload)
            setPreview(null)
            setFileInfo(null)
        } catch (e) {
            setImportError(e.response?.data?.detail || 'Import failed. Check the server logs.')
        }
    }

    const examName = (id) => {
        const ex = exams.find(e => e.id === id)
        return ex ? `${ex.title_en} (${ex.paper_code})` : `Exam ID ${id}`
    }

    return (
        <div className="max-w-5xl space-y-6">
            <PdfExamImporter />

            {/* ── Format + Mode selectors ── */}
            <div className="max-w-3xl bg-white rounded-xl border border-surface-100 shadow-sm p-6 space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {/* Format toggle */}
                    <div>
                        <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">File Format</p>
                        <div className="flex gap-1 bg-surface-100 p-1 rounded-xl w-fit">
                            {['json', 'csv'].map(f => (
                                <button
                                    key={f}
                                    onClick={() => { setFormat(f); setPreview(null); setFileInfo(null); setParseError(null) }}
                                    className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                                        format === f
                                            ? 'bg-white text-surface-900 shadow-sm'
                                            : 'text-surface-500 hover:text-surface-700'
                                    }`}
                                >
                                    {f.toUpperCase()}
                                </button>
                            ))}
                        </div>
                        <p className="text-xs text-surface-400 mt-2">
                            {format === 'json'
                                ? 'Full schema: supports context questions, images, Marathi'
                                : 'Simple rows: text questions only, no context passages'}
                        </p>
                    </div>

                    {/* Exam mode */}
                    <div>
                        <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">Exam Assignment</p>
                        <div className="flex gap-1 bg-surface-100 p-1 rounded-xl w-fit mb-2">
                            <button
                                onClick={() => setExamMode('auto')}
                                className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                                    examMode === 'auto'
                                        ? 'bg-white text-surface-900 shadow-sm'
                                        : 'text-surface-500 hover:text-surface-700'
                                }`}
                            >
                                Auto (from file)
                            </button>
                            <button
                                onClick={() => { setExamMode('override'); ensureExams() }}
                                className={`px-3 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                                    examMode === 'override'
                                        ? 'bg-white text-surface-900 shadow-sm'
                                        : 'text-surface-500 hover:text-surface-700'
                                }`}
                            >
                                Override
                            </button>
                        </div>
                        {examMode === 'auto' && (
                            <p className="text-xs text-surface-400">
                                Uses exam_id from the file. Best for multi-exam imports.
                            </p>
                        )}
                        {examMode === 'override' && (
                            <select
                                value={overrideExamId}
                                onChange={e => setOverrideExamId(e.target.value)}
                                className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400 w-full"
                            >
                                <option value="">Select exam to import into…</option>
                                {exams.map(ex => (
                                    <option key={ex.id} value={ex.id}>
                                        {ex.title_en} ({ex.paper_code}){!ex.is_active ? ' — unpublished' : ''}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>
                </div>

                {/* Template downloads */}
                <div className="flex gap-3 pt-2 border-t border-surface-100">
                    <button
                        onClick={() => downloadFile(
                            `question-template.${format}`,
                            format === 'json'
                                ? JSON.stringify(JSON_TEMPLATE, null, 2)
                                : `${CSV_TEMPLATE_HEADER}\n${CSV_TEMPLATE_ROW}`,
                            format === 'json' ? 'application/json' : 'text/csv',
                        )}
                        className="flex items-center gap-2 text-sm font-medium text-brand-600 hover:text-brand-700 hover:bg-brand-50 px-3 py-1.5 rounded-lg transition-colors border border-brand-200"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download {format.toUpperCase()} Template
                    </button>
                    {format === 'csv' && (
                        <p className="text-xs text-surface-400 self-center">
                            Use semicolons (;) to separate multiple tags in one cell
                        </p>
                    )}
                </div>
            </div>

            {/* ── Drop zone ── */}
            <div
                className={`relative border-2 border-dashed rounded-xl transition-colors cursor-pointer ${
                    dragOver
                        ? 'border-brand-400 bg-brand-50'
                        : 'border-surface-300 hover:border-brand-300 hover:bg-surface-50'
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
            >
                <input
                    ref={fileRef}
                    type="file"
                    accept={format === 'json' ? '.json' : '.csv'}
                    className="hidden"
                    onChange={handleFileInput}
                />
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                    <div className="w-12 h-12 bg-surface-100 rounded-full flex items-center justify-center mb-3">
                        <svg className="w-6 h-6 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                    </div>
                    {fileInfo ? (
                        <div>
                            <p className="text-sm font-semibold text-surface-800">{fileInfo.name}</p>
                            <p className="text-xs text-surface-400 mt-0.5">{fileInfo.size} · click to replace</p>
                        </div>
                    ) : (
                        <div>
                            <p className="text-sm font-semibold text-surface-700">
                                Drag & drop your {format.toUpperCase()} file here
                            </p>
                            <p className="text-xs text-surface-400 mt-1">or click to browse</p>
                        </div>
                    )}
                </div>
            </div>

            {/* ── Parse error ── */}
            {parseError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                    <span className="font-semibold">Parse error: </span>{parseError}
                </div>
            )}

            {/* ── Validation preview ── */}
            {preview && (
                <div className="bg-white rounded-xl border border-surface-100 shadow-sm overflow-hidden">
                    <div className="px-5 py-4 border-b border-surface-100">
                        <h3 className="text-sm font-bold text-surface-900">Preview</h3>
                    </div>
                    <div className="px-5 py-4 space-y-3">
                        {/* Summary */}
                        <div className="flex flex-wrap gap-3">
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-50 rounded-lg text-sm">
                                <span className="font-bold text-surface-900">{preview.questionCount}</span>
                                <span className="text-surface-500">question{preview.questionCount !== 1 ? 's' : ''}</span>
                            </div>
                            {preview.contextCount > 0 && (
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-50 rounded-lg text-sm">
                                    <span className="font-bold text-surface-900">{preview.contextCount}</span>
                                    <span className="text-surface-500">context{preview.contextCount !== 1 ? 's' : ''}</span>
                                </div>
                            )}
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-50 rounded-lg text-sm">
                                <span className="text-surface-500">→</span>
                                <span className="font-medium text-surface-700">{examName(preview.examId)}</span>
                                {examMode === 'override' && (
                                    <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-medium">overridden</span>
                                )}
                            </div>
                        </div>

                        {/* Errors */}
                        {preview.errors?.length > 0 ? (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
                                <p className="text-xs font-semibold text-red-700 mb-1.5">
                                    {preview.errors.length} validation error{preview.errors.length !== 1 ? 's' : ''} — fix before importing:
                                </p>
                                <ul className="space-y-0.5">
                                    {preview.errors.slice(0, 8).map((e, i) => (
                                        <li key={i} className="text-xs text-red-600">• {e}</li>
                                    ))}
                                    {preview.errors.length > 8 && (
                                        <li className="text-xs text-red-400">… and {preview.errors.length - 8} more</li>
                                    )}
                                </ul>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-sm text-green-700">
                                <span className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-xs font-bold">✓</span>
                                Validation passed — ready to import
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── Import error ── */}
            {importError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                    <span className="font-semibold">Import failed: </span>{importError}
                </div>
            )}

            {/* ── Import result ── */}
            {bulkImportResult && !importError && !preview && (
                <div className="p-5 bg-green-50 border border-green-200 rounded-xl">
                    <p className="text-sm font-bold text-green-800 mb-2">Import complete ✓</p>
                    <div className="flex gap-4 text-sm text-green-700">
                        <span><strong>{bulkImportResult.inserted}</strong> inserted</span>
                        <span><strong>{bulkImportResult.skipped}</strong> skipped (duplicates)</span>
                    </div>
                    {bulkImportResult.errors?.length > 0 && (
                        <ul className="mt-2 space-y-0.5">
                            {bulkImportResult.errors.map((e, i) => (
                                <li key={i} className="text-xs text-red-700">• {e}</li>
                            ))}
                        </ul>
                    )}
                </div>
            )}

            {/* ── Import button ── */}
            {preview && (
                <button
                    onClick={handleImport}
                    disabled={bulkImporting || preview.errors?.length > 0}
                    className="w-full flex items-center justify-center gap-2 py-3 text-sm font-semibold bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-40 transition-colors"
                >
                    {bulkImporting ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Importing…
                        </>
                    ) : (
                        <>
                            Import {preview.questionCount} Question{preview.questionCount !== 1 ? 's' : ''} →
                        </>
                    )}
                </button>
            )}
        </div>
    )
}
