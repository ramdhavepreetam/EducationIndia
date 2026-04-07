import { useEffect } from 'react'
import { useParentStore } from '../store/parentStore'
import WrongAnswerCard from '@/modules/analysis/components/WrongAnswerCard'
import UpgradePrompt from '@/shared/components/UpgradePrompt'

/**
 * Inline expansion panel below an attempt row in ChildAttemptHistory.
 * Shows ALL wrong answers for that attempt, grouped by section.
 * Reuses WrongAnswerCard from analysis module.
 *
 * Free tier: shows wrong/skipped counts + UpgradePrompt.
 * Paid tier: shows all WrongAnswerCards grouped by section.
 */
const AttemptMistakesDrawer = ({
  childId,
  attemptId,
  isPaid,
  language,
  onUpgrade,
  onClose,
}) => {
  const {
    wrongAnswersCache,
    loadingWrongAnswers,
    loadAttemptWrongAnswers,
  } = useParentStore()

  const summary   = wrongAnswersCache[attemptId]
  const isLoading = loadingWrongAnswers[attemptId]

  // Fetch on mount if not cached
  useEffect(() => {
    if (!summary && !isLoading) {
      loadAttemptWrongAnswers(childId, attemptId)
    }
  }, [attemptId])

  // ── LOADING ──────────────────────────────────────
  if (isLoading || !summary) {
    return (
      <div className="bg-gray-50 border-t border-gray-100 p-6">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-blue-600
                         border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-gray-500">Loading wrong answers...</span>
        </div>
      </div>
    )
  }

  // ── FREE TIER ─────────────────────────────────────
  if (!isPaid) {
    return (
      <div className="bg-gray-50 border-t border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex gap-4 text-sm">
            <span className="text-red-500 font-semibold">
              {summary.total_wrong} wrong
            </span>
            <span className="text-gray-400">
              {summary.total_skipped} skipped
            </span>
          </div>
          <button onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 text-sm">
            ✕ Close
          </button>
        </div>
        <UpgradePrompt reason="analysis_locked" onUpgrade={onUpgrade} />
      </div>
    )
  }

  // ── ALL CORRECT ───────────────────────────────────
  if (summary.items?.length === 0 && summary.total_skipped === 0) {
    return (
      <div className="bg-green-50 border-t border-green-100 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🎉</span>
            <span className="text-sm font-semibold text-green-700">
              All questions answered correctly!
            </span>
          </div>
          <button onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 text-sm">
            ✕ Close
          </button>
        </div>
      </div>
    )
  }

  // ── PAID FULL REVIEW ──────────────────────────────
  // Group by section
  const bySection = (summary.items ?? []).reduce((acc, item) => {
    const key = item.section_label || '_'
    if (!acc[key]) acc[key] = {
      label: item.section_label,
      subject_en: item.section_subject_en,
      subject_mr: item.subject_mr,
      items: [],
    }
    acc[key].items.push(item)
    return acc
  }, {})

  return (
    <div className="bg-gray-50 border-t border-gray-100">
      {/* Drawer header */}
      <div className="flex items-center justify-between px-6 py-4
                       border-b border-gray-100 bg-white">
        <div className="flex items-center gap-4 text-sm">
          <span className="font-semibold text-gray-800">
            Wrong Answer Review
          </span>
          <span className="text-red-500">
            {summary.total_wrong} wrong
          </span>
          <span className="text-gray-400">
            {summary.total_skipped} skipped
          </span>
        </div>
        <button onClick={onClose}
                className="text-gray-400 hover:text-gray-600
                           text-sm flex items-center gap-1">
          ✕ Close
        </button>
      </div>

      {/* Section groups */}
      <div className="p-6 space-y-6">
        {Object.values(bySection).map(section => {
          const subjectName = language === 'mr' && section.subject_mr
            ? section.subject_mr : section.subject_en
          return (
            <div key={section.label}>
              {/* Section label */}
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 rounded-full bg-blue-100
                                 text-blue-700 text-xs font-bold
                                 flex items-center justify-center">
                  {section.label}
                </span>
                <span className="text-sm font-semibold text-gray-700">
                  {subjectName}
                </span>
                <span className="text-xs text-red-400">
                  {section.items.length} wrong
                </span>
              </div>

              {/* WrongAnswerCard — REUSED from analysis module */}
              <div className="space-y-4">
                {section.items.map(item => (
                  <WrongAnswerCard
                    key={item.question_no}
                    item={item}
                    index={item.question_no}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default AttemptMistakesDrawer
