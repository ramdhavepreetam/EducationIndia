import React from 'react'

export default function OptionButton({
    option,
    isSelected,
    onClick,
    language,
    disabled = false
}) {
    if (!option) return null

    // Fallback to EN if MR requested but missing
    let text = null
    if (language === 'mr' && option.text_mr) text = option.text_mr
    else if (option.text_en) text = option.text_en

    const imgAlt = language === 'mr' ? (option.image_alt_mr || '') : (option.image_alt_en || '')

    // Styling based on selection 
    const baseClasses = "relative flex items-center w-full p-4 mb-3 border-2 rounded-xl transition-all duration-200 text-left cursor-pointer outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500"

    let stateClasses = "border-surface-200 bg-white hover:border-brand-300 hover:bg-brand-50"
    if (isSelected) {
        stateClasses = "border-brand-500 bg-brand-50 shadow-sm ring-1 ring-brand-500"
    } else if (disabled) {
        stateClasses = "border-surface-200 bg-surface-50 cursor-not-allowed opacity-75"
    }

    const numberBubble = (
        <span className={`shrink-0 flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-bold mr-4 ${isSelected
                ? 'bg-brand-500 border-brand-500 text-white'
                : 'bg-surface-100 border-surface-300 text-surface-500'
            }`}>
            {option.option_no}
        </span>
    )

    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className={`${baseClasses} ${stateClasses}`}
            aria-pressed={isSelected}
        >
            {numberBubble}

            <div className="flex-1">
                {text && (
                    <span className={`text-base ${isSelected ? 'text-brand-900 font-medium' : 'text-surface-700'}`}>
                        {text}
                    </span>
                )}

                {option.image_url && (
                    <div className={`mt-2 ${text ? 'ml-0' : ''}`}>
                        <img
                            src={option.image_url}
                            alt={imgAlt || `Option ${option.option_no}`}
                            className="max-h-32 object-contain rounded"
                        />
                    </div>
                )}
            </div>

            {/* Selection checkmark indication */}
            {isSelected && (
                <div className="absolute right-4 text-brand-500 animate-in fade-in zoom-in duration-200">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                </div>
            )}
        </button>
    )
}
