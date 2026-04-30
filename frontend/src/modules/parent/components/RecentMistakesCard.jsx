import { useTranslation } from 'react-i18next'

/**
 * Compact wrong-answer row for the dashboard card.
 * Shows question number, topic, question text,
 * and the two key options (selected wrong + correct).
 */
const MiniWrongAnswerRow = ({ item, language }) => {
  const qText     = language === 'mr' && item.question_text_mr
    ? item.question_text_mr : item.question_text_en
  const topicName = language === 'mr' && item.topic_name_mr
    ? item.topic_name_mr : item.topic_name_en
  const explanation = language === 'mr' && item.explanation_mr
    ? item.explanation_mr : item.explanation_en

  // Find selected (wrong) and correct options
  const selectedOpt = item.options?.find(o => o.option_no === item.selected_option)
  const correctOpt  = item.options?.find(o => o.is_correct)

  const optText = (opt) =>
    language === 'mr' && opt?.text_mr ? opt.text_mr : opt?.text_en

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">
      {/* Question header */}
      <div className="px-4 pt-3 pb-2 bg-gray-50">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-6 h-6 rounded-full bg-red-100 text-red-600
                           text-xs font-bold flex items-center justify-center">
            {item.question_no}
          </span>
          {topicName && (
            <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600
                             rounded-full">
              {topicName}
            </span>
          )}
        </div>

        {/* Question text (truncated to 2 lines) */}
        {qText && (
          <p className="text-sm text-gray-800 line-clamp-2 leading-snug">
            {qText}
          </p>
        )}

        {/* Question image if no text */}
        {!qText && item.question_image_url &&
         !item.question_image_url.startsWith('PLACEHOLDER') && (
          <img src={item.question_image_url}
               alt=""
               className="mt-1 max-h-20 rounded object-contain" />
        )}
      </div>

      {/* Two-option compact display */}
      <div className="px-4 py-3 grid grid-cols-2 gap-2">

        {/* Wrong option (what was chosen) */}
        <div className="flex items-start gap-2 bg-red-50
                        border border-red-200 rounded-lg p-2">
          <span className="text-red-500 font-bold text-sm mt-0.5">✗</span>
          <div className="min-w-0">
            <p className="text-xs text-red-400 font-medium mb-0.5">
              Your answer
            </p>
            <p className="text-xs text-red-700 leading-snug line-clamp-2">
              {optText(selectedOpt) ?? `Option ${selectedOpt?.option_no ?? item.selected_option}`}
            </p>
          </div>
        </div>

        {/* Correct option */}
        <div className="flex items-start gap-2 bg-green-50
                        border border-green-200 rounded-lg p-2">
          <span className="text-green-600 font-bold text-sm mt-0.5">✓</span>
          <div className="min-w-0">
            <p className="text-xs text-green-500 font-medium mb-0.5">
              Correct
            </p>
            <p className="text-xs text-green-800 leading-snug line-clamp-2">
              {optText(correctOpt) ?? `Option ${correctOpt?.option_no ?? item.correct_option}`}
            </p>
          </div>
        </div>
      </div>

      {/* Explanation (collapsed, expandable) */}
      {explanation && (
        <details className="px-4 pb-3 group">
          <summary className="text-xs text-blue-600 cursor-pointer
                               list-none flex items-center gap-1
                               select-none font-medium">
            <span className="group-open:hidden">💡 Show explanation</span>
            <span className="hidden group-open:inline">💡 Hide explanation</span>
          </summary>
          <p className="mt-2 text-xs text-gray-600 leading-relaxed
                        bg-blue-50 rounded-lg p-2.5">
            {explanation}
          </p>
        </details>
      )}
    </div>
  )
}


/**
 * Dashboard card — shows last 5 wrong questions from the child's
 * most recent submitted attempt.
 *
 * States:
 *   A — No attempts yet
 *   B — Free tier (blurred preview + upgrade overlay)
 *   C — Paid tier, has wrong answers (MiniWrongAnswerRow list)
 *   D — Paid tier, all correct
 */
const RecentMistakesCard = ({
  recentMistakes,
  language,
  isPaid,
  isAccessLoading = false,
  onUpgrade,
  onViewAll,
}) => {
  const { t } = useTranslation()

  // STATE A — No attempts yet
  if (!recentMistakes || !recentMistakes.has_attempts) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100
                       shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
          <span>📝</span> Recent Mistakes
        </h3>
        <p className="text-sm text-gray-400 text-center py-4">
          No exams taken yet. Take an exam to see which questions
          need more practice.
        </p>
      </div>
    )
  }

  const { attempt_id, exam_title_en, exam_title_mr, paper_code,
          grade, wrong_answers_summary } = recentMistakes

  const examTitle = language === 'mr' && exam_title_mr
    ? exam_title_mr : exam_title_en
  const hasDetailedItems = wrong_answers_summary?.items?.length > 0
  const canShowDetails = isPaid || hasDetailedItems

  const gradeColors = {
    'Excellent':       'text-green-600 bg-green-50',
    'Good':            'text-blue-600 bg-blue-50',
    'Average':         'text-yellow-600 bg-yellow-50',
    'Below Average':   'text-red-500 bg-red-50',
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm
                     overflow-hidden">
      {/* Card header */}
      <div className="px-6 pt-5 pb-4 border-b border-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <span>📝</span> Recent Mistakes
          </h3>
          {/* Exam badge + grade */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">{paper_code}</span>
            {grade && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                                ${gradeColors[grade] ?? 'bg-gray-100 text-gray-600'}`}>
                {grade}
              </span>
            )}
          </div>
        </div>

        {/* Wrong / skipped count */}
        {wrong_answers_summary && (
          <div className="flex gap-4 mt-3">
            <span className="text-sm text-red-500 font-semibold">
              ✗ {wrong_answers_summary.total_wrong} wrong
            </span>
            <span className="text-sm text-gray-400">
              ○ {wrong_answers_summary.total_skipped} skipped
            </span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-6">

        {/* Access status is still loading — avoid showing a false upgrade gate. */}
        {isAccessLoading && !canShowDetails && (
          <div className="flex items-center justify-center py-8 text-sm text-gray-500">
            Checking access...
          </div>
        )}

        {/* STATE B — FREE TIER */}
        {!isAccessLoading && !canShowDetails && (
          <div className="relative">
            {/* Blurred preview */}
            <div className="filter blur-sm pointer-events-none select-none
                            opacity-50 space-y-3">
              {[1, 2].map(i => (
                <div key={i}
                     className="border border-gray-100 rounded-xl p-4">
                  <div className="h-3 w-24 bg-gray-200 rounded mb-2" />
                  <div className="h-4 w-full bg-gray-100 rounded mb-2" />
                  <div className="flex gap-2">
                    <div className="h-8 flex-1 bg-red-50 rounded-lg" />
                    <div className="h-8 flex-1 bg-green-50 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
            {/* Upgrade overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white/95 backdrop-blur-sm rounded-2xl
                              shadow-lg border border-gray-100 p-5 text-center
                              max-w-[260px]">
                <div className="text-2xl mb-2">🔒</div>
                <p className="text-sm font-semibold text-gray-800 mb-1">
                  See Exactly What Went Wrong
                </p>
                <p className="text-xs text-gray-500 mb-4">
                  Full analysis with explanations unlocked with full access.
                </p>
                <button
                  onClick={onUpgrade}
                  className="w-full bg-blue-600 text-white text-sm
                             font-semibold py-2.5 rounded-xl
                             hover:bg-blue-700 transition-colors"
                >
                  Upgrade to Unlock
                </button>
              </div>
            </div>
          </div>
        )}

        {/* STATE D — PAID TIER, all correct */}
        {canShowDetails &&
         wrong_answers_summary?.items?.length === 0 &&
         wrong_answers_summary?.total_skipped === 0 && (
          <div className="text-center py-4">
            <div className="text-3xl mb-2">🎉</div>
            <p className="text-sm font-semibold text-green-700">
              All questions answered correctly!
            </p>
          </div>
        )}

        {/* STATE C — PAID TIER, wrong answers list (top 5) */}
        {canShowDetails && wrong_answers_summary?.items?.length > 0 && (
          <div className="space-y-4">
            {wrong_answers_summary.items.map(item => (
              <MiniWrongAnswerRow
                key={item.question_no}
                item={item}
                language={language}
              />
            ))}

            {/* "View All" link if more than 5 */}
            {wrong_answers_summary.total_wrong > 5 && (
              <button
                onClick={() => onViewAll(attempt_id)}
                className="w-full mt-2 text-sm text-blue-600
                           font-medium py-2 rounded-xl
                           hover:bg-blue-50 transition-colors
                           flex items-center justify-center gap-1"
              >
                + {wrong_answers_summary.total_wrong - 5} more wrong answers
                <span>▶</span>
              </button>
            )}
          </div>
        )}

      </div>
    </div>
  )
}

export default RecentMistakesCard
