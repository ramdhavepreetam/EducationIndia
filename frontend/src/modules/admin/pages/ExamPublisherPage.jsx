import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'

/**
 * ExamPublisherPage — hierarchical view of exams with publish/unpublish toggles.
 * Publish button only enabled when question_count equals total_questions (default 75).
 */
export function ExamPublisherPage() {
    const { t } = useTranslation()
    const { exams, examsLoading, examsError, fetchAllExams, publishExam, unpublishExam, updateExam } = useAdminStore()
    const [loadingId, setLoadingId] = useState(null)
    const [actionError, setActionError] = useState(null)
    const [actionSuccess, setActionSuccess] = useState(null)
    const [editingExam, setEditingExam] = useState(null)
    const [editForm, setEditForm] = useState({})

    useEffect(() => {
        fetchAllExams()
    }, [fetchAllExams])

    const handleToggle = async (exam) => {
        setLoadingId(exam.id)
        setActionError(null)
        setActionSuccess(null)
        try {
            if (exam.is_active) {
                await unpublishExam(exam.id)
                setActionSuccess(`"${exam.title_en}" has been unpublished.`)
            } else {
                await publishExam(exam.id)
                setActionSuccess(`"${exam.title_en}" is now live for students.`)
            }
        } catch (e) {
            setActionError(e.response?.data?.detail || 'Action failed')
        } finally {
            setLoadingId(null)
        }
    }

    const openEdit = (exam) => {
        setEditingExam(exam)
        setEditForm({
            title_en: exam.title_en || '',
            title_mr: exam.title_mr || '',
            total_questions: exam.total_questions || 75,
            total_marks: exam.total_marks || 150,
            marks_per_question: exam.marks_per_question || 2,
            duration_minutes: exam.duration_minutes || 90,
        })
        setActionError(null)
        setActionSuccess(null)
    }

    const handleEditSave = async (e) => {
        e.preventDefault()
        if (!editingExam) return
        setLoadingId(editingExam.id)
        setActionError(null)
        setActionSuccess(null)
        try {
            await updateExam(editingExam.id, {
                title_en: editForm.title_en,
                title_mr: editForm.title_mr || null,
                total_questions: Number(editForm.total_questions),
                total_marks: Number(editForm.total_marks),
                marks_per_question: Number(editForm.marks_per_question),
                duration_minutes: Number(editForm.duration_minutes),
            })
            setActionSuccess(`"${editForm.title_en}" settings saved.`)
            setEditingExam(null)
        } catch (err) {
            setActionError(err.response?.data?.detail || 'Failed to save exam settings')
        } finally {
            setLoadingId(null)
        }
    }

    // Group by std_class -> event_title
    const groups = exams.reduce((acc, ex) => {
        const clsName = ex.std_class ? `Class ${ex.std_class}` : 'Other'
        const key = ex.event_title || 'Unknown Event'
        
        if (!acc[clsName]) acc[clsName] = {}
        if (!acc[clsName][key]) acc[clsName][key] = []
        
        acc[clsName][key].push(ex)
        return acc
    }, {})

    return (
        <div className="p-4 sm:p-8 max-w-4xl mx-auto pb-24">
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">
                        {t('admin.examPublisher', 'Exam Publisher')}
                    </h1>
                    <p className="text-surface-500 mt-1">
                        {t('admin.examPublisherSub', 'Publish exams when 75 questions are ready. Unpublish to hide from students.')}
                    </p>
                </div>
                <Link
                    to="/admin/publish/create"
                    className="px-4 py-2 bg-brand-600 text-white font-semibold rounded-lg hover:bg-brand-700 transition"
                >
                    + {t('admin.createTest', 'Create Test Set')}
                </Link>
            </div>

            {actionError && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">{actionError}</div>
            )}
            {actionSuccess && (
                <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-xl border border-green-200 text-sm">{actionSuccess}</div>
            )}

            {examsLoading && (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            )}

            {examsError && !examsLoading && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200">{examsError}</div>
            )}

            {!examsLoading && !examsError && (
                <div className="space-y-10">
                    {Object.entries(groups).map(([className, eventGroups]) => (
                        <div key={className}>
                            <h2 className="text-xl font-bold text-surface-800 mb-4 pb-2 border-b border-surface-200">
                                {className}
                            </h2>
                            <div className="space-y-6">
                                {Object.entries(eventGroups).map(([eventTitle, eventExams]) => (
                                    <div key={eventTitle} className="bg-white rounded-xl border border-surface-100 shadow-sm overflow-hidden">
                                        {/* Event header */}
                                        <div className="px-6 py-4 border-b border-surface-100 bg-surface-50">
                                            <h3 className="text-base font-bold text-surface-800">{eventTitle}</h3>
                                            {eventExams[0]?.event_year && (
                                                <p className="text-xs text-surface-400 mt-0.5">Year: {eventExams[0].event_year}</p>
                                            )}
                                        </div>

                                        {/* Exam rows */}
                                        <div className="divide-y divide-surface-100">
                                            {eventExams.map(exam => {
                                                const isReady = exam.question_count >= exam.total_questions
                                                const canPublish = isReady && !exam.is_active
                                                const isLoading = loadingId === exam.id

                                                return (
                                                    <div key={exam.id} className="px-6 py-4 flex items-center gap-4 hover:bg-surface-50/50 transition">
                                                        {/* Status dot */}
                                                        <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${exam.is_active ? 'bg-green-500' : 'bg-surface-300'}`} />

                                                        {/* Info */}
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-semibold text-surface-800">{exam.title_en}</p>
                                                            <p className="text-xs text-surface-400 mt-0.5">
                                                                Code: {exam.paper_code}-{exam.set_code} &nbsp;|&nbsp;
                                                                Duration: {exam.duration_minutes} min &nbsp;|&nbsp;
                                                                <span className={isReady ? 'text-green-600 font-medium' : 'text-orange-600 font-medium'}>
                                                                    {exam.question_count} / {exam.total_questions} questions
                                                                </span>
                                                            </p>
                                                        </div>

                                                        {/* Status badge */}
                                                        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${exam.is_active ? 'bg-green-100 text-green-700' : 'bg-surface-100 text-surface-500'}`}>
                                                            {exam.is_active ? 'Live' : 'Draft'}
                                                        </span>

                                                        {/* Action button */}
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={() => openEdit(exam)}
                                                                disabled={isLoading}
                                                                className="text-sm px-3 py-2 rounded-xl font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-100"
                                                            >
                                                                Edit
                                                            </button>
                                                            <button
                                                                onClick={() => handleToggle(exam)}
                                                                disabled={isLoading || (!exam.is_active && !isReady)}
                                                                title={!isReady && !exam.is_active ? `Need ${exam.total_questions - exam.question_count} more questions` : ''}
                                                                className={`text-sm px-4 py-2 rounded-xl font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                                                                    exam.is_active
                                                                        ? 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200'
                                                                        : 'bg-green-600 text-white hover:bg-green-700'
                                                                }`}
                                                            >
                                                                {isLoading ? '…' : exam.is_active ? 'Unpublish' : 'Publish'}
                                                            </button>
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}

                    {exams.length === 0 && (
                        <div className="text-center py-20 text-surface-400">No exams found.</div>
                    )}
                </div>
            )}

            {editingExam && (
                <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
                    <form onSubmit={handleEditSave} className="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6">
                        <div className="flex items-start justify-between mb-5">
                            <div>
                                <h2 className="text-xl font-bold text-surface-900">Edit Exam Settings</h2>
                                <p className="text-sm text-surface-500">{editingExam.paper_code}-{editingExam.set_code}</p>
                            </div>
                            <button type="button" onClick={() => setEditingExam(null)} className="text-surface-400 hover:text-surface-700">×</button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <label className="md:col-span-2">
                                <span className="block text-sm font-medium text-surface-700 mb-1">Title (English)</span>
                                <input required value={editForm.title_en} onChange={e => setEditForm(f => ({ ...f, title_en: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                            <label className="md:col-span-2">
                                <span className="block text-sm font-medium text-surface-700 mb-1">Title (Marathi)</span>
                                <input value={editForm.title_mr} onChange={e => setEditForm(f => ({ ...f, title_mr: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                            <label>
                                <span className="block text-sm font-medium text-surface-700 mb-1">Duration (minutes)</span>
                                <input type="number" min="1" max="360" required value={editForm.duration_minutes}
                                    onChange={e => setEditForm(f => ({ ...f, duration_minutes: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                            <label>
                                <span className="block text-sm font-medium text-surface-700 mb-1">Total Questions</span>
                                <input type="number" min="1" max="300" required value={editForm.total_questions}
                                    onChange={e => setEditForm(f => ({ ...f, total_questions: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                            <label>
                                <span className="block text-sm font-medium text-surface-700 mb-1">Total Marks</span>
                                <input type="number" min="1" max="1000" required value={editForm.total_marks}
                                    onChange={e => setEditForm(f => ({ ...f, total_marks: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                            <label>
                                <span className="block text-sm font-medium text-surface-700 mb-1">Marks Per Question</span>
                                <input type="number" min="1" max="20" required value={editForm.marks_per_question}
                                    onChange={e => setEditForm(f => ({ ...f, marks_per_question: e.target.value }))}
                                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                            </label>
                        </div>
                        <div className="mt-6 flex justify-end gap-3">
                            <button type="button" onClick={() => setEditingExam(null)} className="px-4 py-2 text-sm text-surface-600">Cancel</button>
                            <button disabled={loadingId === editingExam.id} className="px-5 py-2 bg-brand-600 text-white rounded-lg text-sm font-semibold disabled:opacity-50">
                                {loadingId === editingExam.id ? 'Saving…' : 'Save Settings'}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    )
}
