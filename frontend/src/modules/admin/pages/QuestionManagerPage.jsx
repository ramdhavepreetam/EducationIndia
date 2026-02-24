import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'
import { QuestionTable } from '../components/QuestionTable'
import { QuestionEditForm } from '../components/QuestionEditForm'
import { BulkImportButton } from '../components/BulkImportButton'

const EXAM_OPTIONS = [
    { id: 1, label: 'Paper I (501)' },
    { id: 2, label: 'Paper II (502)' },
]

/**
 * QuestionManagerPage — browse, edit, delete, and bulk import questions.
 * Admin only. Fetches all questions with correct_option visible (QuestionAdminSchema).
 */
export function QuestionManagerPage() {
    const { t } = useTranslation()
    const {
        questions, selectedExamId, questionsLoading, questionsError,
        fetchQuestions,
    } = useAdminStore()
    const [examId, setExamId] = useState(EXAM_OPTIONS[0].id)
    const [editingQuestion, setEditingQuestion] = useState(null)

    useEffect(() => {
        fetchQuestions(examId)
    }, [examId, fetchQuestions])

    const handleExamChange = (e) => {
        setExamId(Number(e.target.value))
    }

    return (
        <div className="p-4 sm:p-8 max-w-7xl mx-auto pb-24">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('admin.questionManager', 'Question Manager')}
                </h1>
                <p className="text-surface-500 mt-1">{t('admin.questionManagerSub', 'Browse and edit all questions. Correct answers visible.')}</p>
            </div>

            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
                <select
                    value={examId}
                    onChange={handleExamChange}
                    className="text-sm border border-surface-200 rounded-xl px-4 py-2 text-surface-700 font-medium focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
                >
                    {EXAM_OPTIONS.map(ex => (
                        <option key={ex.id} value={ex.id}>{ex.label}</option>
                    ))}
                </select>

                <div className="flex items-center gap-2 bg-surface-100 px-3 py-2 rounded-xl text-sm text-surface-600">
                    <span className="font-bold text-surface-900">{questions.length}</span> questions
                </div>

                <div className="ml-auto">
                    <BulkImportButton examId={examId} />
                </div>
            </div>

            {/* State */}
            {questionsLoading && (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            )}

            {questionsError && !questionsLoading && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200">{questionsError}</div>
            )}

            {!questionsLoading && !questionsError && (
                <div className="bg-white rounded-xl border border-surface-100 shadow-sm p-4">
                    <QuestionTable
                        questions={questions}
                        onEdit={setEditingQuestion}
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
        </div>
    )
}
