import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAttemptStore } from '../store/attemptStore'

export function ExamStartPage() {
    const { t } = useTranslation()
    const { examId } = useParams()
    const navigate = useNavigate()
    const [isChecking, setIsChecking] = useState(true)

    const startExam = useAttemptStore(s => s.startExam)
    const currentAttempt = useAttemptStore(s => s.currentAttempt)
    const isLoading = useAttemptStore(s => s.isLoading)
    const error = useAttemptStore(s => s.error)

    useEffect(() => {
        // Here we could check if an ongoing attempt exists via API before allowing start.
        // For now we just let the user see the start screen.
        setIsChecking(false)
    }, [examId])

    const handleStart = async () => {
        if (!examId) return
        try {
            await startExam(examId)
            navigate(`/exam/${examId}/attempt`)
        } catch (err) {
            // Error is handled by store and displayed below
            if (err.response?.status === 409) {
                // If 409 Conflict, an ongoing attempt exists. Resume it.
                // Assuming the API returned the ongoing attempt id in the error, or we fetch it.
                // For simplicity, we just route them into the attempt page which will try to resume.
                navigate(`/exam/${examId}/attempt`)
            }
        }
    }

    if (isChecking) {
        return (
            <div className="flex h-screen items-center justify-center bg-surface-50">
                <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
            <div className="max-w-xl w-full bg-white rounded-2xl shadow-sm border border-surface-200 overflow-hidden">
                <div className="bg-brand-600 p-8 text-center">
                    <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
                        {t('exam.scholarshipExam')}
                    </h1>
                    <p className="text-brand-100 font-medium">
                        {t('exam.paper1')} • {t('exam.totalMarks', { marks: 150 })}
                    </p>
                </div>

                <div className="p-8 space-y-8">
                    {error && (
                        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm w-full">
                            {error}
                        </div>
                    )}

                    <div className="space-y-4">
                        <h3 className="text-lg font-bold text-surface-900 border-b pb-2">
                            {t('exam.instructions')}
                        </h3>
                        <ul className="space-y-3 text-surface-600 text-sm">
                            <li className="flex gap-3">
                                <span className="text-brand-500 font-bold">•</span>
                                {t('exam.instruction1', 'This exam contains 75 questions to be answered in 90 minutes.')}
                            </li>
                            <li className="flex gap-3">
                                <span className="text-brand-500 font-bold">•</span>
                                {t('exam.instruction2', 'Each correct answer carries 2 marks. There is no negative marking.')}
                            </li>
                            <li className="flex gap-3">
                                <span className="text-brand-500 font-bold">•</span>
                                {t('exam.instruction3', 'The timer cannot be paused once started.')}
                            </li>
                            <li className="flex gap-3">
                                <span className="text-orange-500 font-bold">⚠️</span>
                                <span className="font-medium text-surface-800">
                                    {t('exam.instruction4', 'Make sure you have a stable internet connection.')}
                                </span>
                            </li>
                        </ul>
                    </div>

                    <button
                        onClick={handleStart}
                        disabled={isLoading}
                        className="w-full py-4 px-6 bg-brand-600 text-white font-bold rounded-xl shadow-sm hover:bg-brand-700 active:bg-brand-800 active:shadow-inner disabled:bg-surface-300 disabled:cursor-not-allowed transition-all flex justify-center items-center gap-2 text-lg"
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                {t('exam.startExam')}
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
