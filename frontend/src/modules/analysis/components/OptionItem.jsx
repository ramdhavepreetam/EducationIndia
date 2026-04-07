import { useTranslation } from 'react-i18next'

const optionLabels = ['A', 'B', 'C', 'D']

/**
 * Renders one option (A/B/C/D) with color coding:
 *  - Green border + bg for the correct answer
 *  - Red border + bg for the selected wrong answer
 *  - Neutral for others
 */
const OptionItem = ({ option, selectedOption, correctOption, language = 'en' }) => {
  const { t } = useTranslation()
  const label = optionLabels[option.option_no - 1] || option.option_no
  const isSelected = option.option_no === selectedOption
  const isCorrect = option.option_no === correctOption

  let borderClass = 'border-gray-200 bg-white'
  let dotClass = 'bg-gray-200 text-gray-600'

  if (isCorrect) {
    borderClass = 'border-green-300 bg-green-50'
    dotClass = 'bg-green-500 text-white'
  } else if (isSelected) {
    borderClass = 'border-red-300 bg-red-50'
    dotClass = 'bg-red-500 text-white'
  }

  const text = language === 'mr' && option.text_mr ? option.text_mr : option.text_en

  return (
    <div className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border
                      ${borderClass} transition-colors`}>
      <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center
                        justify-center text-xs font-bold ${dotClass}`}>
        {label}
      </span>
      <div className="flex-1 min-w-0">
        {text && (
          <p className="text-sm text-gray-800 leading-relaxed">{text}</p>
        )}
        {option.image_url && (
          <img
            src={option.image_url}
            alt={`Option ${label}`}
            className="mt-1 max-h-24 rounded"
          />
        )}
      </div>
      {isCorrect && (
        <span className="text-green-600 text-xs font-medium whitespace-nowrap">
          ✓ {t('analysis.correct', 'Correct')}
        </span>
      )}
      {isSelected && !isCorrect && (
        <span className="text-red-500 text-xs font-medium whitespace-nowrap">
          ✗ {t('analysis.yourAnswer', 'Your answer')}
        </span>
      )}
    </div>
  )
}

export default OptionItem
