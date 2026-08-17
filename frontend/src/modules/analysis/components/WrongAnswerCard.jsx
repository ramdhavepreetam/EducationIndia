import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/modules/auth/store/authStore'
import OptionItem from './OptionItem'

/**
 * Renders one wrong question with:
 *  - Question number + text
 *  - 4 OptionItems with correct/wrong highlighting
 *  - Explanation (if available)
 *
 * Reused by: RecentMistakesCard, AttemptMistakesDrawer, ResultPage
 */
const WrongAnswerCard = ({ item, index }) => {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const lang = user?.preferred_language || 'en'

  const questionText = lang === 'mr' && item.question_text_mr
    ? item.question_text_mr
    : item.question_text_en

  const explanation = lang === 'mr' && item.explanation_mr
    ? item.explanation_mr
    : item.explanation_en

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm
                    overflow-hidden">
      {/* Question header */}
      <div className="px-4 py-3 bg-gradient-to-r from-red-50 to-orange-50
                      border-b border-red-100/50">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7
                          rounded-full bg-red-100 text-red-600 text-xs
                          font-bold flex-shrink-0">
            Q{item.question_no}
          </span>
          <div className="flex-1 min-w-0">
            {item.section_subject_en && (
              <span className="text-xs text-gray-400 font-medium">
                {item.section_subject_en}
                {item.topic_name_en && ` · ${item.topic_name_en}`}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Question body */}
      <div className="p-4 space-y-3">
        {/* Question text */}
        {questionText && (
          /* whitespace-pre-wrap preserves symbol-figure alignment — see QuestionCard */
          <p className="text-sm text-gray-800 font-medium leading-relaxed whitespace-pre-wrap">
            {questionText}
          </p>
        )}

        {/* Question image */}
        {item.question_image_url && (
          <img
            src={item.question_image_url}
            alt={`Question ${item.question_no}`}
            className="max-h-40 rounded-lg border border-gray-100"
          />
        )}

        {/* Options */}
        {item.options && item.options.length > 0 && (
          <div className="space-y-1.5">
            {item.options.map(opt => (
              <OptionItem
                key={opt.option_no}
                option={opt}
                selectedOption={item.selected_option}
                correctOption={item.correct_option}
                language={lang}
              />
            ))}
          </div>
        )}

        {/* Explanation */}
        {explanation && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-xs font-semibold text-blue-700 mb-1">
              💡 {t('analysis.explanation', 'Explanation')}
            </p>
            <p className="text-sm text-blue-800 leading-relaxed">
              {explanation}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default WrongAnswerCard
