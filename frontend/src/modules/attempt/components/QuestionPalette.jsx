import React from 'react'
import { useAttemptStore } from '../store/attemptStore'

export default function QuestionPalette({ questions, onNavigate }) {
    const responses = useAttemptStore(s => s.responses)
    const currentQuestionNo = useAttemptStore(s => s.currentQuestionNo)

    // Palette Rules: ADR-005
    // not-visited     → gray bg-surface-200
    // visited         → white border-surface-400
    // answered        → green bg-green-500
    // marked          → orange bg-orange-400
    // marked-answered → purple bg-purple-500
    // current         → add ring-2 ring-brand-600
    const getStatusClasses = (qNo) => {
        const res = responses[qNo]
        const isCurrent = currentQuestionNo === qNo

        let classes = "w-10 h-10 rounded-md font-medium text-sm flex items-center justify-center transition-all shadow-sm "

        if (!res || !res.visitCount) {
            classes += "bg-surface-200 text-surface-600 border border-transparent"
        } else if (res.visitCount > 0 && !res.selectedOption && !res.isMarkedReview) {
            classes += "bg-white text-surface-900 border-2 border-surface-400"
        } else if (res.selectedOption && !res.isMarkedReview) {
            classes += "bg-green-500 text-white border border-transparent"
        } else if (!res.selectedOption && res.isMarkedReview) {
            classes += "bg-orange-400 text-white border border-transparent"
        } else if (res.selectedOption && res.isMarkedReview) {
            classes += "bg-purple-500 text-white border border-transparent"
        }

        if (isCurrent) {
            classes += " ring-2 ring-brand-600 ring-offset-2 scale-110 z-10"
        } else {
            classes += " hover:scale-105 hover:shadow"
        }

        return classes
    }

    if (!questions || questions.length === 0) return null

    return (
        <div className="bg-white rounded-xl shadow-sm border border-surface-200 p-4 h-full flex flex-col">
            <h3 className="text-sm font-semibold text-surface-500 uppercase tracking-wider mb-4">
                Question Palette
            </h3>

            {/* Grid */}
            <div className="flex-1 overflow-y-auto pr-2 pb-4">
                <div className="grid grid-cols-5 gap-3">
                    {questions.map((q) => (
                        <button
                            key={q.question_id}
                            onClick={() => onNavigate(q.question_no)}
                            className={getStatusClasses(q.question_no)}
                            aria-label={`Question ${q.question_no}`}
                            aria-current={currentQuestionNo === q.question_no}
                        >
                            {q.question_no}
                        </button>
                    ))}
                </div>
            </div>

            {/* Legend */}
            <div className="pt-4 border-t border-surface-100 mt-2 text-xs space-y-2">
                <div className="grid grid-cols-2 gap-2">
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-surface-200 border border-transparent"></div>
                        <span className="text-surface-600">Not Visited</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-white border-2 border-surface-400"></div>
                        <span className="text-surface-600">Not Answered</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-green-500 border border-transparent"></div>
                        <span className="text-surface-600">Answered</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-orange-400 border border-transparent"></div>
                        <span className="text-surface-600">Marked Review</span>
                    </div>
                    <div className="flex items-center gap-2 col-span-2">
                        <div className="w-4 h-4 rounded bg-purple-500 border border-transparent"></div>
                        <span className="text-surface-600">Answered & Marked for Review</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
