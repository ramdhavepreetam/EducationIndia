import { useEffect, useState } from 'react'
import { useAdminStore } from '../store/adminStore'
import { QuestionTable } from './QuestionTable'
import { QuestionEditForm } from './QuestionEditForm'

/**
 * QuestionBrowser — Browse tab for QuestionManagerPage.
 * Shows exam selector, text search, filters, and the questions table.
 * Wires up edit modal and delete with confirmation dialog.
 */
export function QuestionBrowser() {
    const {
        exams, examsLoading, fetchAllExams,
        questions, questionsLoading, questionsError,
        fetchQuestions, deleteQuestion,
    } = useAdminStore()

    const [examId, setExamId] = useState(null)
    const [editingQuestion, setEditingQuestion] = useState(null)
    const [deleteConfirmId, setDeleteConfirmId] = useState(null)
    const [deleting, setDeleting] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')

    // Load exam list on mount
    useEffect(() => {
        if (exams.length === 0) fetchAllExams()
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    // Default to first exam once loaded
    useEffect(() => {
        if (exams.length > 0 && examId === null) {
            setExamId(exams[0].id)
        }
    }, [exams, examId])

    // Fetch questions when exam changes
    useEffect(() => {
        if (examId !== null) fetchQuestions(examId)
    }, [examId]) // eslint-disable-line react-hooks/exhaustive-deps

    const handleDelete = async () => {
        if (!deleteConfirmId) return
        setDeleting(true)
        try {
            await deleteQuestion(deleteConfirmId)
        } finally {
            setDeleting(false)
            setDeleteConfirmId(null)
        }
    }

    const examLabel = (ex) => {
        const year = ex.event_year ? ` ${ex.event_year}` : ''
        const std = ex.std_class ? ` Std ${ex.std_class}` : ''
        return `${year}${std} — ${ex.title_en} (${ex.paper_code})`
    }

    return (
        <div>
            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
                {/* Exam selector */}
                <select
                    value={examId || ''}
                    onChange={e => { setExamId(Number(e.target.value)); setSearchTerm('') }}
                    disabled={examsLoading}
                    className="text-sm border border-surface-200 rounded-xl px-4 py-2 text-surface-700 font-medium focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white disabled:opacity-50"
                >
                    {exams.length === 0 && <option value="">Loading exams…</option>}
                    {exams.map(ex => (
                        <option key={ex.id} value={ex.id}>
                            {examLabel(ex)}{!ex.is_active ? ' (unpublished)' : ''}
                        </option>
                    ))}
                </select>

                {/* Search */}
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search questions…"
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="text-sm border border-surface-200 rounded-xl px-4 py-2 pl-9 w-56 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                    />
                    <svg className="absolute left-3 top-2.5 w-4 h-4 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    {searchTerm && (
                        <button
                            onClick={() => setSearchTerm('')}
                            className="absolute right-3 top-2.5 text-surface-400 hover:text-surface-600"
                        >
                            ✕
                        </button>
                    )}
                </div>

                {/* Question count */}
                <div className="flex items-center gap-2 bg-surface-100 px-3 py-2 rounded-xl text-sm text-surface-600">
                    <span className="font-bold text-surface-900">{questions.length}</span> questions
                </div>
            </div>

            {/* Loading */}
            {questionsLoading && (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            )}

            {/* Error */}
            {questionsError && !questionsLoading && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200">{questionsError}</div>
            )}

            {/* Table */}
            {!questionsLoading && !questionsError && (
                <div className="bg-white rounded-xl border border-surface-100 shadow-sm p-4">
                    <QuestionTable
                        questions={questions}
                        searchTerm={searchTerm}
                        onEdit={setEditingQuestion}
                        onDelete={setDeleteConfirmId}
                    />
                </div>
            )}

            {/* Edit modal */}
            {editingQuestion && (
                <QuestionEditForm
                    question={editingQuestion}
                    onClose={() => setEditingQuestion(null)}
                />
            )}

            {/* Delete confirmation dialog */}
            {deleteConfirmId && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                    <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
                        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-surface-900 text-center mb-2">Delete Question?</h3>
                        <p className="text-sm text-surface-500 text-center mb-6">
                            This cannot be undone. All student responses to this question may be affected.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setDeleteConfirmId(null)}
                                disabled={deleting}
                                className="flex-1 px-4 py-2 text-sm font-medium text-surface-600 hover:bg-surface-100 rounded-xl transition-colors border border-surface-200"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={deleting}
                                className="flex-1 px-4 py-2 text-sm font-semibold bg-red-500 text-white rounded-xl hover:bg-red-600 disabled:opacity-50 transition-colors"
                            >
                                {deleting ? 'Deleting…' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
