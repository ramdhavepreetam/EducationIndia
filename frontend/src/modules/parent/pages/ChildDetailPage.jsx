import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useParentStore } from '../store/parentStore'
import { useAuthStore } from '@/modules/auth/store/authStore'
import ChildWeakTopics from '../components/ChildWeakTopics'
import ChildProgressChart from '../components/ChildProgressChart'
import ChildAttemptHistory from '../components/ChildAttemptHistory'

export default function ChildDetailPage() {
  const { studentId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const {
    childDetail, selectedChildId,
    isLoadingDetail, error,
    selectChild
  } = useParentStore()

  useEffect(() => {
    if (studentId && studentId !== selectedChildId) {
      selectChild(studentId)
    }
  }, [studentId])

  if (isLoadingDetail) {
    return (
      <div className="max-w-3xl mx-auto p-6 space-y-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-40 bg-gray-200 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => navigate('/parent')}
            className="mt-4 px-4 py-2 bg-gray-100 rounded-lg text-sm"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  if (!childDetail) return null

  return (
    <div className="max-w-3xl mx-auto p-6">

      {/* Header with back + start exam */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/parent')}
          className="flex items-center gap-2 text-gray-500
                     hover:text-gray-700 text-sm"
        >
          ← Back to Dashboard
        </button>
        <button
          onClick={() => navigate(`/dashboard?childId=${studentId}`)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg
                     hover:bg-green-700 transition-colors font-medium
                     text-sm flex items-center gap-2"
        >
          📝 Start Exam
        </button>
      </div>

      <div className="space-y-6">

        {/* Profile header */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br
                            from-blue-400 to-blue-600 flex items-center
                            justify-center text-2xl font-bold text-white">
              {childDetail.profile?.full_name ? childDetail.profile.full_name[0].toUpperCase() : '?'}
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {childDetail.profile.child_nickname
                  || childDetail.profile.full_name}
              </h1>
              <p className="text-gray-500 text-sm">
                {[
                  childDetail.profile.std_class && `${childDetail.profile.std_class}th Std`,
                  childDetail.profile.medium && `${childDetail.profile.medium} medium`,
                  childDetail.profile.school_name,
                  childDetail.profile.district
                ].filter(Boolean).join(' · ')}
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: 'Total Attempts', value: childDetail.stats.total_attempts },
            {
              label: 'Avg Score',
              value: childDetail.stats.avg_percentage
                ? `${childDetail.stats.avg_percentage}%` : '—'
            },
            {
              label: 'Best Score',
              value: childDetail.stats.best_score
                ? `${childDetail.stats.best_score}/150` : '—'
            },
            { label: 'Exams Completed', value: childDetail.stats.exams_completed },
          ].map(stat => (
            <div key={stat.label}
              className="bg-white rounded-xl border border-gray-100
                            p-4 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>

        <ChildWeakTopics
          weakTopics={childDetail.weak_topics}
          strongTopics={childDetail.strong_topics}
          language={user?.preferred_language || 'en'}
        />

        <ChildProgressChart attempts={childDetail.recent_attempts} />

        <ChildAttemptHistory
          attempts={childDetail.recent_attempts}
          onViewResult={(id) => navigate(`/attempts/${id}/result`)}
          pageSize={10}
          showPagination={true}
        />

      </div>
    </div>
  )
}
