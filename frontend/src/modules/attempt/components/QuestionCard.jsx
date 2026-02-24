import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import OptionButton from './OptionButton'
import ContextPanel from './ContextPanel'

export default function QuestionCard({
    question,
    response,
    onAnswer,
    onMarkReview,
    onNavigate,
    isFirst,
    isLast,
    language
}) {
    const { t } = useTranslation()

    if (!question) return null

    const hasContext = !!question.context
    const isBilingual = question.question_type === 'bilingual'
    const isMarathiOnly = question.question_type === 'marathi_only'

    // Determine primary texts based on type and language
    const showEn = isBilingual || (language === 'en' && !isMarathiOnly)
    const showMr = isBilingual || language === 'mr' || isMarathiOnly

    const textEn = question.text_en
    const textMr = question.text_mr
    const imgUrl = question.question_image_url
    const imgAltEn = question.question_image_alt_en
    const imgAltMr = question.question_image_alt_mr

    const selectedOption = response?.selectedOption || null
    const isMarkedReview = response?.isMarkedReview || false

    const handleOptionSelect = (optNumber) => {
        onAnswer(question.question_no, question.question_id, optNumber)
    }

    const handleSaveAndNext = () => {
        if (!isLast) onNavigate(question.question_no + 1)
    }

    const questionContent = (
        <div className="flex-1 flex flex-col h-full bg-white rounded-xl shadow-sm border border-surface-200 overflow-hidden">
            <div className="p-6 flex-1 overflow-y-auto">
                <div className="flex justify-between items-start mb-6">
                    <h2 className="text-xl font-bold tracking-tight text-surface-900 border-b-2 border-brand-500 pb-1 inline-block">
                        {t('exam.questionNumber', { number: question.question_no })}
                    </h2>

                    <button
                        type="button"
                        onClick={() => onMarkReview(question.question_no, question.question_id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors shrink-0 whitespace-nowrap ${isMarkedReview
                            ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                            : 'bg-surface-100 text-surface-600 hover:bg-surface-200'
                            }`}
                        aria-pressed={isMarkedReview}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M3 6a3 3 0 013-3h10a1 1 0 01.8 1.6L14.25 8l2.55 3.4A1 1 0 0116 13H6a1 1 0 00-1 1v3a1 1 0 11-2 0V6z" clipRule="evenodd" />
                        </svg>
                        {isMarkedReview ? t('exam.markedForReview') : t('exam.markForReview')}
                    </button>
                </div>

                {/* Question Text & Media */}
                <div className="mb-8 space-y-4">
                    {showEn && textEn && (
                        <p className={`text-lg text-surface-800 leading-relaxed ${isBilingual ? 'font-medium' : ''}`}>
                            {textEn}
                        </p>
                    )}
                    {showMr && textMr && (
                        <p className={`text-lg text-surface-800 leading-relaxed ${isBilingual ? 'text-surface-600 mt-2' : ''}`}>
                            {textMr}
                        </p>
                    )}

                    {imgUrl && (
                        <div className="my-6 p-4 bg-surface-50 rounded-lg border border-surface-200 flex justify-center">
                            <img
                                src={imgUrl}
                                alt={(language === 'mr' ? imgAltMr : imgAltEn) || 'Question figure'}
                                className="max-w-full max-h-80 object-contain"
                            />
                        </div>
                    )}
                </div>

                {/* Options */}
                <div className="space-y-3">
                    {question.options?.slice().sort((a, b) => a.option_no - b.option_no).map((opt) => (
                        <OptionButton
                            key={opt.id}
                            option={opt}
                            language={isMarathiOnly ? 'mr' : language}
                            isSelected={selectedOption === opt.option_no}
                            onClick={() => handleOptionSelect(opt.option_no)}
                        />
                    ))}
                </div>
            </div>

            {/* Navigation Footer */}
            <div className="p-4 bg-surface-50 border-t border-surface-200 flex items-center justify-between shrink-0 gap-4">
                <button
                    onClick={() => onNavigate(question.question_no - 1)}
                    disabled={isFirst}
                    className="px-4 md:px-5 py-2.5 rounded-lg text-sm font-medium text-surface-700 bg-white border border-surface-300 hover:bg-surface-50 hover:text-surface-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 whitespace-nowrap min-w-[100px]"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {t('exam.previous')}
                </button>

                <button
                    onClick={handleSaveAndNext}
                    disabled={isLast}
                    className="px-4 md:px-6 py-2.5 rounded-lg text-sm font-bold text-white bg-brand-600 hover:bg-brand-700 active:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm flex items-center justify-center gap-2 whitespace-nowrap flex-1 md:flex-none"
                >
                    {t('exam.saveAndNext')}
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                </button>
            </div>
        </div>
    )

    // Layout wrapping (split if context exists)
    if (hasContext) {
        return (
            <div className="flex flex-col lg:flex-row gap-6 h-full max-h-full w-full">
                <div className="w-full lg:w-2/5 flex flex-col h-[40vh] lg:h-full shrink-0">
                    <ContextPanel context={question.context} language={language} />
                </div>
                <div className="w-full lg:w-3/5 flex flex-col h-[60vh] lg:h-full">
                    {questionContent}
                </div>
            </div>
        )
    }

    return (
        <div className="h-full flex flex-col max-w-4xl mx-auto w-full">
            {questionContent}
        </div>
    )
}
