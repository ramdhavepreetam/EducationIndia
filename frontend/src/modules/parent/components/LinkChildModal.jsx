import { useState } from 'react'
import { useParentStore } from '../store/parentStore'

const STEPS = { EMAIL: 'email', SUCCESS: 'success' }

const LinkChildModal = ({ isOpen, onClose, onSuccess }) => {
  const { linkChild, isSaving } = useParentStore()

  const [step, setStep]               = useState(STEPS.EMAIL)
  const [email, setEmail]             = useState('')
  const [linkedChild, setLinkedChild] = useState(null)
  const [error, setError]             = useState(null)

  if (!isOpen) return null

  const handleClose = () => {
    setStep(STEPS.EMAIL)
    setEmail('')
    setLinkedChild(null)
    setError(null)
    onClose()
  }

  const handleLink = async () => {
    if (!email.trim()) return
    setError(null)

    const result = await linkChild(email.trim().toLowerCase())

    if (result.success) {
      setLinkedChild(result.child)
      setStep(STEPS.SUCCESS)
      onSuccess(result.child)
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center
                    justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md
                      shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {step === STEPS.SUCCESS ? '🎉 Child Linked!' : 'Add Child'}
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-300 hover:text-gray-500
                       transition-colors text-xl leading-none"
          >
            ✕
          </button>
        </div>

        <div className="px-6 pb-6">

          {/* ── Step: Enter email ── */}
          {step === STEPS.EMAIL && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">
                Enter your child's registered email address.
              </p>

              <div>
                <label className="block text-sm font-medium
                                  text-gray-700 mb-1.5">
                  Child's Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => {
                    setEmail(e.target.value)
                    setError(null)
                  }}
                  onKeyDown={e => e.key === 'Enter' && handleLink()}
                  placeholder="child@example.com"
                  autoFocus
                  className="w-full border border-gray-200 rounded-xl
                             px-4 py-3 text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-300
                             focus:border-transparent"
                />
              </div>

              {/* Error message */}
              {error && (
                <div className="bg-red-50 border border-red-100
                                rounded-xl p-3">
                  <p className="text-sm text-red-600">{error}</p>
                  {error.includes('register') && (
                    <p className="text-xs text-red-400 mt-1">
                      Ask your child to create an account at
                      scholarpath.in first.
                    </p>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleClose}
                  className="flex-1 py-3 bg-gray-100 text-gray-700
                             rounded-xl text-sm font-medium
                             hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLink}
                  disabled={!email.trim() || isSaving}
                  className="flex-1 py-3 bg-blue-600 text-white
                             rounded-xl text-sm font-medium
                             hover:bg-blue-700 transition-colors
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSaving
                    ? <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 border-2 border-white/30
                                         border-t-white rounded-full
                                         animate-spin" />
                        Linking...
                      </span>
                    : 'Link Child'
                  }
                </button>
              </div>
            </div>
          )}

          {/* ── Step: Success ── */}
          {step === STEPS.SUCCESS && linkedChild && (
            <div className="space-y-4 text-center">
              <div className="w-20 h-20 rounded-full bg-green-100
                              flex items-center justify-center
                              text-3xl font-bold text-green-600 mx-auto">
                {linkedChild.full_name[0].toUpperCase()}
              </div>

              <div>
                <p className="text-lg font-bold text-gray-900">
                  {linkedChild.full_name}
                </p>
                <p className="text-sm text-gray-400">
                  {[
                    linkedChild.std_class && `${linkedChild.std_class}th Std`,
                    linkedChild.school_name
                  ].filter(Boolean).join(' · ')}
                </p>
              </div>

              <p className="text-sm text-green-600 bg-green-50
                            rounded-xl py-2 px-4">
                ✓ Successfully linked! You can now monitor
                  their exam progress.
              </p>

              <button
                onClick={handleClose}
                className="w-full py-3 bg-blue-600 text-white
                           rounded-xl text-sm font-medium
                           hover:bg-blue-700 transition-colors"
              >
                View Dashboard
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}

export default LinkChildModal
