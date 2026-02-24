import React from 'react'
import { useTranslation } from 'react-i18next'
import { useExamTimer } from '../hooks/useExamTimer'

export default function ExamTimer() {
    const { t } = useTranslation()
    const { timeRemaining, isWarning, isUrgent } = useExamTimer()

    if (timeRemaining === null) return null

    // Format MM:SS
    const minutes = Math.floor(timeRemaining / 60)
    const seconds = timeRemaining % 60
    const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`

    let colorClass = 'text-surface-700 bg-surface-100 border-surface-200'
    if (isUrgent) {
        colorClass = 'text-red-600 bg-red-50 border-red-200 animate-pulse font-bold'
    } else if (isWarning) {
        colorClass = 'text-orange-600 bg-orange-50 border-orange-200 font-bold'
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${colorClass} transition-colors`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            <span className="font-mono text-lg tracking-wider">
                {formatted}
            </span>
        </div>
    )
}
