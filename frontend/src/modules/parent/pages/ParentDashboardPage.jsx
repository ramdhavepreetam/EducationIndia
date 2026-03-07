import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useParentStore } from '../store/parentStore'
import { useAuthStore } from '@/modules/auth/store/authStore'
import { useTranslation } from 'react-i18next'
import ChildSwitcher from '../components/ChildSwitcher'
import ChildProfileCard from '../components/ChildProfileCard'
import ChildWeakTopics from '../components/ChildWeakTopics'
import ChildProgressChart from '../components/ChildProgressChart'
import ChildAttemptHistory from '../components/ChildAttemptHistory'
import CreateChildModal from '../components/CreateChildModal'

export default function ParentDashboardPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const {
    children, selectedChildId, childDetail,
    isLoading, isLoadingDetail, error,
    isSaving,
    loadDashboard, selectChild, updateChild, deleteChild
  } = useParentStore()

  const [showLinkModal, setShowLinkModal] = useState(false)

  useEffect(() => {
    loadDashboard()
  }, [])

  // ── Loading skeleton ─────────────────────────────
  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-3 mb-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-10 w-28 bg-gray-200 rounded-full animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-gray-200 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-gray-200 rounded-xl animate-pulse" />
          <div className="h-64 bg-gray-200 rounded-xl animate-pulse" />
        </div>
      </div>
    )
  }

  // ── Error state ──────────────────────────────────
  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button
            onClick={loadDashboard}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // ── Empty state — no children linked ─────────────
  if (children.length === 0) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{t('parent.dashboard.title', 'Parent Dashboard')}</h1>
        </div>
        <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center">
          <div className="text-6xl mb-4">👨‍👩‍👧</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            {t('parent.dashboard.noChildren', 'No children added yet')}
          </h2>
          <p className="text-gray-500 mb-6">
            {t('parent.dashboard.noChildrenHint', 'Create a child profile to start monitoring their exam progress.')}
          </p>
          <button
            onClick={() => setShowLinkModal(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl
                       font-medium hover:bg-blue-700 transition-colors"
          >
            {t('parent.dashboard.addChild', '+ Add Your Child')}
          </button>
        </div>

        <CreateChildModal
          isOpen={showLinkModal}
          onClose={() => setShowLinkModal(false)}
          onSuccess={() => { setShowLinkModal(false); loadDashboard() }}
        />
      </div>
    )
  }

  // ── Main dashboard ───────────────────────────────
  return (
    <div className="max-w-6xl mx-auto p-6">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('parent.dashboard.title', 'Parent Dashboard')}</h1>
      </div>

      <ChildSwitcher
        children={children}
        selectedChildId={selectedChildId}
        onSelect={selectChild}
        onAddChild={() => setShowLinkModal(true)}
      />

      {/* Child detail area */}
      {isLoadingDetail ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-48 bg-gray-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : childDetail ? (
        <div className="space-y-6">

          <ChildProfileCard
            profile={childDetail.profile}
            stats={childDetail.stats}
            onViewDetail={() => navigate(`/parent/children/${selectedChildId}`)}
            onStartExam={() => navigate(`/dashboard?childId=${selectedChildId}`)}
            onEditNickname={(nickname) => updateChild(selectedChildId, { name: nickname })}
            onUnlink={() => deleteChild(selectedChildId)}
            isSaving={isSaving}
          />

          <ChildWeakTopics
            weakTopics={childDetail.weak_topics}
            strongTopics={childDetail.strong_topics}
            language={user?.preferred_language || 'en'}
          />

          <ChildProgressChart attempts={childDetail.recent_attempts} />

          <ChildAttemptHistory
            attempts={childDetail.recent_attempts}
            onViewResult={(id) => navigate(`/attempts/${id}/result`)}
            pageSize={5}
            showPagination={false}
          />

        </div>
      ) : null}

      <CreateChildModal
        isOpen={showLinkModal}
        onClose={() => setShowLinkModal(false)}
        onSuccess={() => { setShowLinkModal(false); loadDashboard() }}
      />

    </div>
  )
}
