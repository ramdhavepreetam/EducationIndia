import React, { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAttemptStore } from '../store/attemptStore'
import { useAutoSave } from '../hooks/useAutoSave'
import QuestionCard from '../components/QuestionCard'
import QuestionPalette from '../components/QuestionPalette'
import SectionTabs from '../components/SectionTabs'
import ExamTimer from '../components/ExamTimer'

export function ExamPage() {
    const { t } = useTranslation()
    const { examId } = useParams()
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const attemptId = searchParams.get('attemptId')

    // Global state
    const currentAttempt = useAttemptStore(s => s.currentAttempt)
    const questions = useAttemptStore(s => s.questions)
    const responses = useAttemptStore(s => s.responses)
    const currentQuestionNo = useAttemptStore(s => s.currentQuestionNo)
    const isLoading = useAttemptStore(s => s.isLoading)
    const error = useAttemptStore(s => s.error)
    const isSaving = useAttemptStore(s => s.isSaving)

    // Actions
    const resumeExam = useAttemptStore(s => s.resumeExam)
    const selectOption = useAttemptStore(s => s.selectOption)
    const toggleMarkReview = useAttemptStore(s => s.toggleMarkReview)
    const navigateTo = useAttemptStore(s => s.navigateTo)
    const submitExam = useAttemptStore(s => s.submitExam)
    const isSubmitting = useAttemptStore(s => s.isSubmitting)

    // Local state
    const [language, setLanguage] = useState('en') // Exam displays in EN by default, switchable to MR
    const [activeSectionId, setActiveSectionId] = useState(null)
    const [isSidebarOpen, setIsSidebarOpen] = useState(false) // Mobile tray
    const [showSubmitConfirm, setShowSubmitConfirm] = useState(false)

    const { scheduleSave } = useAutoSave()

    // Resume attempt on mount after refresh if the URL carries attemptId.
    // Zustand state is memory-only, so a browser refresh loses currentAttempt.
    useEffect(() => {
        const load = async () => {
            if (!currentAttempt && examId) {
                if (attemptId) {
                    await resumeExam(attemptId, examId)
                    return
                }
                // No active attempt and no attemptId in URL — redirect to start.
                const childId = searchParams.get('childId')
                const query = childId ? `?childId=${childId}` : ''
                navigate(`/exam/${examId}/start${query}`, { replace: true })
            }
        }
        load().catch(() => {
            // resumeExam stores the API error; render the error state below.
        })
    }, [currentAttempt, examId, attemptId, resumeExam, searchParams, navigate])

    // Derive sections for tabs
    const sections = useMemo(() => {
        if (!questions) return []
        const uniqueSections = new Map()
        questions.forEach(q => {
            if (q.section_id && !uniqueSections.has(q.section_id)) {
                uniqueSections.set(q.section_id, {
                    id: q.section_id,
                    minQuestionNo: q.question_no,
                    maxQuestionNo: q.question_no,
                })
            } else if (q.section_id) {
                const section = uniqueSections.get(q.section_id)
                section.minQuestionNo = Math.min(section.minQuestionNo, q.question_no)
                section.maxQuestionNo = Math.max(section.maxQuestionNo, q.question_no)
            }
        })
        return Array.from(uniqueSections.values())
            .sort((a, b) => a.minQuestionNo - b.minQuestionNo)
            .map((section, index) => ({
                ...section,
                label: index === 0 ? 'Section I' : `Section ${index + 1}`,
            }))
    }, [questions])

    // Set default section tab when questions load
    useEffect(() => {
        if (sections.length > 0 && !activeSectionId) {
            setActiveSectionId(sections[0].id)
        }
    }, [sections, activeSectionId])

    const currentQuestion = useMemo(() => {
        return questions?.find(q => q.question_no === currentQuestionNo)
    }, [questions, currentQuestionNo])

    // Sync active section tab to the current question's section_id (authoritative source)
    useEffect(() => {
        if (currentQuestion?.section_id && currentQuestion.section_id !== activeSectionId) {
            setActiveSectionId(currentQuestion.section_id)
        }
    }, [currentQuestion, activeSectionId])

    // Questions filtered to active section only — drives the palette display
    const sectionQuestions = useMemo(() => {
        if (!questions || !activeSectionId) return questions || []
        return questions.filter(q => q.section_id === activeSectionId)
    }, [questions, activeSectionId])

    // First and last question_no across ALL questions (for Prev/Next disabling)
    const firstQuestionNo = useMemo(() => {
        if (!questions || questions.length === 0) return 1
        return Math.min(...questions.map(q => q.question_no))
    }, [questions])

    const lastQuestionNo = useMemo(() => {
        if (!questions || questions.length === 0) return 1
        return Math.max(...questions.map(q => q.question_no))
    }, [questions])

    const handleSectionChange = (sectionId) => {
        setActiveSectionId(sectionId)
        const firstQ = questions?.find(q => q.section_id === sectionId)
        if (firstQ) {
            navigateTo(firstQ.question_no)
        }
    }

    const handleAnswer = (questionNo, questionId, selectedOption) => {
        const isMulti = !!currentQuestion?.is_multi_select
        selectOption(questionNo, questionId, selectedOption, isMulti)
        
        // Use updated state from store for saving
        const updatedResponse = useAttemptStore.getState().responses[questionNo]
        const isMarked = updatedResponse?.isMarkedReview || false
        const opts = updatedResponse?.selectedOptions || []
        const opt = updatedResponse?.selectedOption || null
        
        scheduleSave(questionNo, questionId, opt, opts, isMarked, 5) // dummy timeTaken
    }

    const handleMarkReview = (questionNo, questionId) => {
        toggleMarkReview(questionNo, questionId)
        const updatedResponse = useAttemptStore.getState().responses[questionNo]
        const isMarked = updatedResponse?.isMarkedReview || false
        const opts = updatedResponse?.selectedOptions || []
        const opt = updatedResponse?.selectedOption || null
        scheduleSave(questionNo, questionId, opt, opts, isMarked, 1)
    }

    const handleSubmit = async () => {
        if (!currentAttempt) return
        try {
            const result = await submitExam(currentAttempt.id || currentAttempt.attempt_id)
            navigate(`/exam/submitted/${result.attempt_id || currentAttempt.attempt_id}`)
        } catch (err) {
            alert('Failed to submit exam: ' + err.message)
            setShowSubmitConfirm(false)
        }
    }

    if (error && !currentAttempt) {
        return (
            <div className="flex h-screen items-center justify-center bg-surface-50 p-4">
                <div className="max-w-md w-full bg-white rounded-xl border border-red-200 p-6 shadow-sm">
                    <h1 className="text-lg font-bold text-surface-900 mb-2">
                        {t('exam.resumeFailed', 'Could not resume exam')}
                    </h1>
                    <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg p-3 mb-4">
                        {error}
                    </p>
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard')}
                        className="px-4 py-2 bg-brand-600 text-white rounded-lg font-semibold"
                    >
                        {t('common.backToDashboard', 'Back to dashboard')}
                    </button>
                </div>
            </div>
        )
    }

    if (isLoading || !currentAttempt) {
        return (
            <div className="flex h-screen items-center justify-center bg-surface-50">
                <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-screen bg-surface-100 overflow-hidden font-sans">
            {/* Header */}
            <header className="flex-none bg-white border-b border-surface-200 shadow-sm z-20 h-16 flex items-center justify-between px-4 lg:px-6">
                <div className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-brand-600 text-white flex items-center justify-center rounded font-bold text-sm">
                        SP
                    </div>
                    <h1 className="text-lg font-bold text-surface-900 hidden md:block">
                        {t('exam.scholarshipExam')}
                    </h1>
                </div>

                <div className="flex items-center gap-4 md:gap-6">
                    {/* Auto-save indicator */}
                    <div className="hidden md:flex items-center gap-2 text-xs font-medium text-surface-500">
                        {isSaving ? (
                            <><div className="w-3 h-3 border-2 border-surface-300 border-t-brand-500 rounded-full animate-spin"></div> Saving...</>
                        ) : (
                            <><svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg> Saved</>
                        )}
                    </div>

                    <ExamTimer />

                    <div className="flex items-center bg-surface-100 p-1 rounded-lg border border-surface-200">
                        <button
                            className={`px-3 py-1 text-sm font-medium rounded-md ${language === 'en' ? 'bg-white shadow-sm text-brand-700' : 'text-surface-600'}`}
                            onClick={() => setLanguage('en')}
                        >
                            EN
                        </button>
                        <button
                            className={`px-3 py-1 text-sm font-medium rounded-md ${language === 'mr' ? 'bg-white shadow-sm text-brand-700' : 'text-surface-600'}`}
                            onClick={() => setLanguage('mr')}
                        >
                            मराठी
                        </button>
                    </div>

                    <button
                        onClick={() => setShowSubmitConfirm(true)}
                        className="px-4 py-2 bg-green-600 text-white text-sm font-bold rounded-lg shadow-sm hover:bg-green-700 transition-colors"
                    >
                        {t('exam.submitExam', 'Submit Exam')}
                    </button>

                    {/* Mobile palette toggle */}
                    <button
                        className="lg:hidden p-2 text-surface-600 hover:bg-surface-100 rounded-md"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                        </svg>
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <div className="flex-1 flex overflow-hidden relative">

                {/* Question Area */}
                <main className="flex-1 p-4 lg:p-6 overflow-hidden flex flex-col items-center max-w-7xl mx-auto w-full">
                    {currentQuestion ? (
                        <QuestionCard
                            question={currentQuestion}
                            response={responses[currentQuestionNo]}
                            onAnswer={handleAnswer}
                            onMarkReview={handleMarkReview}
                            onNavigate={navigateTo}
                            isFirst={currentQuestionNo === firstQuestionNo}
                            isLast={currentQuestionNo === lastQuestionNo}
                            language={language}
                        />
                    ) : (
                        <div className="m-auto text-surface-500">Select a question from the palette</div>
                    )}
                </main>

                {/* Sidebar Palette (Desktop) */}
                <aside className="hidden lg:flex flex-col w-[340px] border-l border-surface-200 bg-surface-50 p-4 shrink-0">
                    <SectionTabs
                        sections={sections}
                        activeSectionId={activeSectionId}
                        onTabChange={handleSectionChange}
                    />
                    <div className="flex-1 min-h-0">
                        <QuestionPalette
                            questions={sectionQuestions}
                            onNavigate={navigateTo}
                        />
                    </div>
                </aside>

                {/* Mobile Palette Drawer */}
                {isSidebarOpen && (
                    <div className="absolute inset-x-0 bottom-0 top-16 bg-white z-10 lg:hidden flex flex-col border-t shadow-[0_-10px_40px_rgba(0,0,0,0.1)] p-4 animate-in slide-in-from-bottom">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="font-bold text-surface-900">Question Palette</h2>
                            <button onClick={() => setIsSidebarOpen(false)} className="p-2 text-surface-500 bg-surface-100 rounded-full">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <SectionTabs
                            sections={sections}
                            activeSectionId={activeSectionId}
                            onTabChange={handleSectionChange}
                        />
                        <div className="flex-1 min-h-0">
                            <QuestionPalette
                                questions={sectionQuestions}
                                onNavigate={(qNo) => {
                                    navigateTo(qNo)
                                    setIsSidebarOpen(false) // auto-close on mobile
                                }}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Submit Confirmation Modal */}
            {showSubmitConfirm && (
                <div className="fixed inset-0 z-50 bg-surface-900/60 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl p-6 md:p-8 max-w-md w-full shadow-xl animate-in zoom-in-95">
                        <h3 className="text-xl font-bold text-surface-900 mb-2">Submit Exam?</h3>
                        <p className="text-surface-600 mb-6 font-medium">
                            Once submitted, you will not be able to change your answers. Are you sure you are completely finished?
                        </p>

                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setShowSubmitConfirm(false)}
                                className="px-5 py-2.5 rounded-xl font-bold text-surface-700 bg-surface-100 hover:bg-surface-200 transition-colors"
                                disabled={isSubmitting}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={isSubmitting}
                                className="px-5 py-2.5 rounded-xl font-bold text-white bg-green-600 hover:bg-green-700 transition-colors shadow-sm flex items-center justify-center min-w-[120px]"
                            >
                                {isSubmitting ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    "Yes, Submit"
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
