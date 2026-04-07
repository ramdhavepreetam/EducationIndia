/**
 * PasswordChangeForm — change password for email-authenticated users.
 *
 * Includes password strength indicator (weak/medium/strong).
 * Shows inline success/error messages. Clears form on success.
 */
import { useState } from 'react'

const getStrength = (pwd) => {
  if (pwd.length < 8)  return { level: 'weak',   color: 'bg-red-400',    text: 'text-red-500' }
  if (pwd.length < 12) return { level: 'medium', color: 'bg-yellow-400', text: 'text-yellow-600' }
  return { level: 'strong', color: 'bg-green-500', text: 'text-green-600' }
}

export default function PasswordChangeForm({ onSubmit }) {
  const [form, setForm] = useState({
    current_password: '', new_password: '', confirm_password: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError]   = useState(null)
  const [success, setSuccess] = useState(false)

  const strength = getStrength(form.new_password)

  const handleSubmit = async () => {
    if (form.new_password !== form.confirm_password) {
      setError('Passwords do not match')
      return
    }

    if (form.new_password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsSubmitting(true)
    setError(null)
    const result = await onSubmit(form)
    setIsSubmitting(false)

    if (result.success) {
      setSuccess(true)
      setForm({ current_password: '', new_password: '', confirm_password: '' })
      setTimeout(() => setSuccess(false), 4000)
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="space-y-4 max-w-md">
      {/* Current password */}
      <div>
        <label className="block text-sm font-medium text-surface-700 mb-1">
          Current Password
        </label>
        <input type="password" value={form.current_password}
               onChange={e => setForm(p => ({...p, current_password: e.target.value}))}
               className="w-full border border-surface-200 rounded-xl
                          px-4 py-3 text-sm focus:outline-none
                          focus:ring-2 focus:ring-brand-500"
               autoComplete="current-password" />
      </div>

      {/* New password + strength */}
      <div>
        <label className="block text-sm font-medium text-surface-700 mb-1">
          New Password
        </label>
        <input type="password" value={form.new_password}
               onChange={e => setForm(p => ({...p, new_password: e.target.value}))}
               className="w-full border border-surface-200 rounded-xl
                          px-4 py-3 text-sm focus:outline-none
                          focus:ring-2 focus:ring-brand-500"
               placeholder="Min 8 characters"
               autoComplete="new-password" />
        {form.new_password.length > 0 && (
          <div className="mt-1.5 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-surface-200 rounded-full overflow-hidden">
              <div className={`h-full ${strength.color} transition-all`}
                   style={{ width:
                     strength.level === 'weak'   ? '33%' :
                     strength.level === 'medium' ? '66%' : '100%'
                   }} />
            </div>
            <span className={`text-xs capitalize font-medium ${strength.text}`}>
              {strength.level}
            </span>
          </div>
        )}
      </div>

      {/* Confirm password */}
      <div>
        <label className="block text-sm font-medium text-surface-700 mb-1">
          Confirm New Password
        </label>
        <input type="password" value={form.confirm_password}
               onChange={e => setForm(p => ({...p, confirm_password: e.target.value}))}
               className={`w-full border rounded-xl px-4 py-3 text-sm
                           focus:outline-none focus:ring-2 focus:ring-brand-500
                           ${form.confirm_password &&
                             form.confirm_password !== form.new_password
                               ? 'border-red-300' : 'border-surface-200'}`}
               autoComplete="new-password" />
        {form.confirm_password &&
         form.confirm_password !== form.new_password && (
          <p className="mt-1 text-xs text-red-500">Passwords do not match</p>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-3">
          <p className="text-sm text-green-700">
            ✓ Password changed successfully.
          </p>
        </div>
      )}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={isSubmitting || !form.current_password ||
                  !form.new_password || !form.confirm_password}
        className="w-full bg-surface-900 text-white py-3 rounded-xl
                   text-sm font-semibold hover:bg-surface-800
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors"
      >
        {isSubmitting ? 'Changing...' : 'Change Password'}
      </button>
    </div>
  )
}
