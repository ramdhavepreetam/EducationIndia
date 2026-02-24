import { useState } from 'react'

const ChildProfileCard = ({
  profile, stats, onViewDetail,
  onEditNickname, onUnlink, isSaving
}) => {
  const [editingNickname, setEditingNickname] = useState(false)
  const [nicknameInput, setNicknameInput]     = useState(
    profile.child_nickname || ''
  )
  const [unlinkConfirm, setUnlinkConfirm]     = useState(false)
  const [saveError, setSaveError]             = useState(null)

  const displayName = profile.child_nickname || profile.full_name

  const handleNicknameSave = async () => {
    if (!nicknameInput.trim()) return
    const result = await onEditNickname(nicknameInput.trim())
    if (result.success) {
      setEditingNickname(false)
      setSaveError(null)
    } else {
      setSaveError(result.error)
    }
  }

  const statBoxes = [
    { label: 'Attempts',
      value: stats.total_attempts,
      icon: '📝' },
    { label: 'Avg Score',
      value: stats.avg_percentage ? `${stats.avg_percentage}%` : '—',
      icon: '📊' },
    { label: 'Best Score',
      value: stats.best_score ? `${stats.best_score}/150` : '—',
      icon: '🏆' },
    { label: 'Last Active',
      value: stats.last_active
        ? new Date(stats.last_active).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short'
          })
        : '—',
      icon: '🕒' },
  ]

  return (
    <div className="bg-white rounded-2xl border border-gray-100
                    shadow-sm overflow-hidden">

      {/* Profile header */}
      <div className="p-6">
        <div className="flex items-start justify-between">

          {/* Avatar + name */}
          <div className="flex items-center gap-4">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt={displayName}
                className="w-16 h-16 rounded-full object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-gradient-to-br
                              from-blue-400 to-blue-600 flex items-center
                              justify-center text-2xl font-bold text-white">
                {displayName[0].toUpperCase()}
              </div>
            )}

            <div>
              {/* Name / nickname edit */}
              {editingNickname ? (
                <div className="flex items-center gap-2">
                  <input
                    value={nicknameInput}
                    onChange={e => setNicknameInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleNicknameSave()}
                    placeholder="Nickname"
                    maxLength={50}
                    autoFocus
                    className="border border-blue-300 rounded-lg px-3 py-1
                               text-sm w-36 focus:outline-none focus:ring-2
                               focus:ring-blue-300"
                  />
                  <button
                    onClick={handleNicknameSave}
                    disabled={isSaving}
                    className="text-xs px-2 py-1 bg-blue-600 text-white
                               rounded-lg disabled:opacity-50"
                  >
                    {isSaving ? '...' : 'Save'}
                  </button>
                  <button
                    onClick={() => {
                      setEditingNickname(false)
                      setSaveError(null)
                    }}
                    className="text-xs px-2 py-1 bg-gray-100
                               text-gray-600 rounded-lg"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-gray-900">
                    {displayName}
                  </h2>
                  <button
                    onClick={() => setEditingNickname(true)}
                    title="Edit nickname"
                    className="text-gray-300 hover:text-gray-500
                               transition-colors text-sm"
                  >
                    ✏️
                  </button>
                </div>
              )}

              {saveError && (
                <p className="text-xs text-red-500 mt-1">{saveError}</p>
              )}

              {/* Sub-details */}
              <p className="text-sm text-gray-400 mt-0.5">
                {[
                  profile.std_class && `${profile.std_class}th Std`,
                  profile.medium    && `${profile.medium} medium`,
                  profile.school_name,
                  profile.district
                ].filter(Boolean).join(' · ')}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={onViewDetail}
              className="text-sm px-3 py-1.5 border border-blue-200
                         text-blue-600 rounded-lg hover:bg-blue-50
                         transition-colors"
            >
              Full Detail →
            </button>
            <button
              onClick={() => setUnlinkConfirm(true)}
              title="Unlink child"
              className="text-gray-300 hover:text-red-400
                         transition-colors text-lg"
            >
              🔗
            </button>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 divide-x divide-gray-100
                      border-t border-gray-100">
        {statBoxes.map(stat => (
          <div key={stat.label} className="p-4 text-center">
            <p className="text-lg mb-0.5">{stat.icon}</p>
            <p className="text-lg font-bold text-gray-900">{stat.value}</p>
            <p className="text-xs text-gray-400">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Unlink confirmation dialog */}
      {unlinkConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center
                        justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm
                          mx-4 shadow-2xl">
            <h3 className="font-semibold text-gray-900 mb-2">
              Unlink {displayName}?
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              This removes your monitoring access for {displayName}.
              Their account and all exam data will NOT be deleted.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setUnlinkConfirm(false)}
                className="flex-1 py-2 bg-gray-100 text-gray-700
                           rounded-xl text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setUnlinkConfirm(false)
                  onUnlink()
                }}
                className="flex-1 py-2 bg-red-500 text-white
                           rounded-xl text-sm font-medium
                           hover:bg-red-600 transition-colors"
              >
                Yes, Unlink
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChildProfileCard
