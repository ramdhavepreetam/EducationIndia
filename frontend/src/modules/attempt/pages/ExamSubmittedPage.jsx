import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAttemptStore } from '../store/attemptStore'

export function ExamSubmittedPage() {
    const { t } = useTranslation()
    const { id } = useParams() // attempt object / result ID passed in
    const navigate = useNavigate()

    // We assume the submission result rests in currentAttempt or was stored after submit
    const currentAttempt = useAttemptStore(s => s.currentAttempt)
    const reset = useAttemptStore(s => s.reset)

    // A real app might fetch attempt result via GET /api/attempts/:id if loaded directly
    // but here we just render from store assuming a linear flow.
    const result = currentAttempt?.status === 'submitted' ? currentAttempt : null

    useEffect(() => {
        // Cleanup store on unmount so next exam starts fresh
        return () => {
            reset()
        }
    }, [reset])

    return (
        <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
            <div className="max-w-xl w-full bg-white rounded-2xl shadow-sm border border-surface-200 overflow-hidden text-center">

                <div className="bg-green-500 p-8">
                    <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow text-green-500 inline-block p-1">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {t('exam.submittedSuccessfully', 'Exam Submitted Successfully!')}
                    </h1>
                </div>

                <div className="p-8">
                    {result ? (
                        <div className="grid grid-cols-2 gap-4 mb-8">
                            <div className="p-4 bg-surface-50 rounded-xl border border-surface-100">
                                <p className="text-sm font-semibold tracking-wider text-surface-500 uppercase mb-1">Score</p>
                                <p className="text-3xl font-black text-brand-600">
                                    {result.total_score} <span className="text-lg text-surface-400 font-medium">/ 150</span>
                                </p>
                            </div>
                            <div className="p-4 bg-surface-50 rounded-xl border border-surface-100">
                                <p className="text-sm font-semibold tracking-wider text-surface-500 uppercase mb-1">Percentage</p>
                                <p className="text-3xl font-black text-surface-900">
                                    {result.percentage}%
                                </p>
                            </div>
                            <div className="col-span-2 p-4 bg-surface-50 rounded-xl border border-surface-100">
                                <p className="text-sm font-semibold tracking-wider text-surface-500 uppercase mb-1">Grade</p>
                                <p className="text-xl font-bold text-surface-800">
                                    {result.grade}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <p className="text-surface-500 mb-8 italic">Score details will be available shortly or via the Analysis dashboard.</p>
                    )}

                    <div className="flex flex-col gap-3">
                        <button
                            onClick={() => navigate(`/analysis/${id}`)}
                            className="w-full py-4 text-brand-700 bg-brand-50 border border-brand-200 font-bold rounded-xl hover:bg-brand-100 transition-colors"
                        >
                            {t('exam.viewAnalysis', 'View Detailed Analysis (Day 9)')}
                        </button>

                        <button
                            onClick={() => navigate('/dashboard')}
                            className="w-full py-3 text-surface-600 bg-transparent font-medium rounded-xl hover:bg-surface-50 transition-colors"
                        >
                            {t('exam.backToDashboard', 'Back to Dashboard')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
