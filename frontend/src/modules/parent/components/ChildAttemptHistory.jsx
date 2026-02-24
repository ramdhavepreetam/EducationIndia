import { useState } from 'react'

const gradeColor = (grade) => ({
  'Excellent':    'text-green-600 bg-green-50',
  'Good':         'text-blue-600 bg-blue-50',
  'Average':      'text-orange-500 bg-orange-50',
  'Below Average':'text-red-500 bg-red-50',
}[grade] || 'text-gray-500 bg-gray-50')

const statusBadge = (status) => ({
  submitted: null,
  expired:   { label: 'Time Expired',  cls: 'text-gray-500 bg-gray-100' },
  abandoned: { label: 'Incomplete',    cls: 'text-yellow-600 bg-yellow-50' },
  ongoing:   { label: 'In Progress',   cls: 'text-blue-600 bg-blue-50' },
}[status])

const ChildAttemptHistory = ({
  attempts,
  onViewResult,
  pageSize = 5,
  showPagination = false
}) => {
  const [page, setPage] = useState(1)

  const totalPages = Math.ceil(attempts.length / pageSize)
  const start      = (page - 1) * pageSize
  const visible    = attempts.slice(start, start + pageSize)

  if (attempts.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100
                      shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">
          Recent Attempts
        </h3>
        <div className="text-center py-8">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-gray-400 text-sm">No exams taken yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100
                    shadow-sm overflow-hidden">
      <div className="p-6 pb-3">
        <h3 className="font-semibold text-gray-900">
          {showPagination ? 'All Attempts' : 'Recent Attempts'}
        </h3>
      </div>

      {/* Table header */}
      <div className="px-6 pb-2 grid grid-cols-12 gap-2
                      text-xs text-gray-400 font-medium uppercase
                      tracking-wide border-b border-gray-50">
        <div className="col-span-5">Exam</div>
        <div className="col-span-2 text-center">Score</div>
        <div className="col-span-2 text-center">Grade</div>
        <div className="col-span-2 text-right">Date</div>
        <div className="col-span-1" />
      </div>

      {/* Rows */}
      <div className="divide-y divide-gray-50">
        {visible.map(attempt => {
          const badge  = statusBadge(attempt.status)
          const dateStr = attempt.submitted_at
            ? new Date(attempt.submitted_at).toLocaleDateString('en-IN', {
                day: 'numeric', month: 'short', year: '2-digit'
              })
            : '—'

          return (
            <div key={attempt.attempt_id}
                 className="px-6 py-4 grid grid-cols-12 gap-2
                            items-center hover:bg-gray-50/50
                            transition-colors">

              {/* Exam name */}
              <div className="col-span-5">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {attempt.exam_title_en}
                </p>
                <p className="text-xs text-gray-400">
                  Attempt #{attempt.attempt_number}
                </p>
              </div>

              {/* Score */}
              <div className="col-span-2 text-center">
                {attempt.status === 'submitted' ? (
                  <span className="text-sm font-bold text-gray-800">
                    {attempt.total_score}/{attempt.total_marks}
                  </span>
                ) : (
                  <span className="text-sm text-gray-300">—</span>
                )}
              </div>

              {/* Grade / status */}
              <div className="col-span-2 text-center">
                {badge ? (
                  <span className={`text-xs px-2 py-0.5 rounded-full
                                   font-medium ${badge.cls}`}>
                    {badge.label}
                  </span>
                ) : attempt.grade ? (
                  <span className={`text-xs px-2 py-0.5 rounded-full
                                   font-medium ${gradeColor(attempt.grade)}`}>
                    {attempt.grade}
                  </span>
                ) : (
                  <span className="text-gray-300 text-xs">—</span>
                )}
              </div>

              {/* Date */}
              <div className="col-span-2 text-right">
                <span className="text-xs text-gray-400">{dateStr}</span>
              </div>

              {/* View button */}
              <div className="col-span-1 text-right">
                {attempt.status === 'submitted' && (
                  <button
                    onClick={() => onViewResult(attempt.attempt_id)}
                    className="text-xs px-2 py-1 bg-blue-50 text-blue-600
                               rounded-lg hover:bg-blue-100 transition-colors
                               whitespace-nowrap"
                  >
                    View
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-50
                        flex items-center justify-between">
          <p className="text-xs text-gray-400">
            Showing {start + 1}–{Math.min(start + pageSize, attempts.length)}
            {' '}of {attempts.length}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600
                         rounded-lg disabled:opacity-40 hover:bg-gray-200"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-600
                         rounded-lg disabled:opacity-40 hover:bg-gray-200"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChildAttemptHistory
