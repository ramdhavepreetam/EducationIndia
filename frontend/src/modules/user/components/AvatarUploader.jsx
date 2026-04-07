/**
 * AvatarUploader — click-to-upload avatar component.
 *
 * Displays current avatar or two-letter initials in colored circle.
 * Click opens file picker. Shows preview immediately, then uploads.
 * Max 2 MB, JPEG/PNG/WebP only.
 */
import { useRef, useState } from 'react'

export default function AvatarUploader({ currentAvatarUrl, fullName, onUpload }) {
  const [preview, setPreview] = useState(currentAvatarUrl)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (file.size > 2 * 1024 * 1024) {
      setError('Image must be under 2MB')
      return
    }

    // Show preview immediately
    const reader = new FileReader()
    reader.onload = (ev) => setPreview(ev.target.result)
    reader.readAsDataURL(file)

    setIsUploading(true)
    setError(null)
    await onUpload(file)
    setIsUploading(false)
  }

  // Two-letter initials fallback
  const initials = fullName
    ? fullName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className="relative cursor-pointer group"
        onClick={() => inputRef.current?.click()}
      >
        {/* Avatar or initials */}
        {preview
          ? <img src={preview} alt="Avatar"
                 className="w-24 h-24 rounded-full object-cover
                            ring-4 ring-white shadow-md" />
          : <div className="w-24 h-24 rounded-full bg-gradient-to-br from-brand-500 to-brand-700
                            flex items-center justify-center
                            text-white text-2xl font-bold
                            ring-4 ring-white shadow-md">
              {initials}
            </div>
        }

        {/* Hover overlay */}
        <div className="absolute inset-0 rounded-full bg-black/40
                        opacity-0 group-hover:opacity-100 transition
                        flex items-center justify-center">
          <span className="text-white text-xs font-medium">
            {isUploading ? '...' : 'Change'}
          </span>
        </div>

        {/* Uploading spinner */}
        {isUploading && (
          <div className="absolute inset-0 rounded-full bg-black/60
                          flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-white
                            border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      <input ref={inputRef} type="file"
             accept="image/jpeg,image/png,image/webp"
             className="hidden" onChange={handleFile} />

      <button type="button"
              onClick={() => inputRef.current?.click()}
              className="text-sm text-brand-600 hover:underline">
        Change Photo
      </button>

      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  )
}
