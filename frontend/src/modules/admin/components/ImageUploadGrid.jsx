import { useState } from 'react'
import { adminApi } from '../api/adminApi'

/**
 * ImageUploadGrid — per-question image uploader for Intelligence Test questions.
 * Shows questions where question_image_url is missing or starts with PLACEHOLDER_.
 * Each question card has upload buttons for question image + 4 option images.
 */
export function ImageUploadGrid({ questions, onUploaded }) {
    const imageQuestions = questions.filter(q =>
        q.question_type === 'image_only' || q.question_type === 'text_image' ||
        !q.question_image_url || q.question_image_url?.startsWith('PLACEHOLDER')
    )

    if (imageQuestions.length === 0) {
        return (
            <div className="text-center py-12 text-surface-400">
                <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p>No image-type questions found for this exam.</p>
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {imageQuestions.map(q => (
                <QuestionImageCard key={q.id} question={q} onUploaded={onUploaded} />
            ))}
        </div>
    )
}

function QuestionImageCard({ question, onUploaded }) {
    const [uploads, setUploads] = useState({})
    const [errors, setErrors] = useState({})

    const upload = async (file, type, entityId, key) => {
        setUploads(u => ({ ...u, [key]: 'uploading' }))
        setErrors(e => ({ ...e, [key]: null }))
        try {
            const result = await adminApi.uploadImage(file, type, entityId)
            setUploads(u => ({ ...u, [key]: result.file_url }))
            onUploaded?.(question.id, key, result.file_url)
        } catch (err) {
            setErrors(e => ({ ...e, [key]: err.response?.data?.detail || 'Upload failed' }))
            setUploads(u => ({ ...u, [key]: null }))
        }
    }

    return (
        <div className="bg-white rounded-xl border border-surface-200 p-4 space-y-3">
            <div className="flex items-center gap-2">
                <span className="w-8 h-8 flex items-center justify-center rounded-full bg-brand-50 text-brand-700 font-bold text-sm">
                    {question.question_no}
                </span>
                <div>
                    <p className="text-sm font-semibold text-surface-800 line-clamp-1">
                        {question.text_en || question.text_mr || 'Image-only question'}
                    </p>
                    <p className="text-xs text-surface-400">{question.question_type}</p>
                </div>
            </div>

            {/* Question image upload */}
            <ImageUploadSlot
                label="Question Image"
                currentUrl={question.question_image_url}
                uploadKey="question_img"
                uploads={uploads}
                errors={errors}
                onFile={file => upload(file, 'question', question.id, 'question_img')}
            />

            {/* Option images */}
            {question.options?.map(opt => (
                <ImageUploadSlot
                    key={opt.option_no}
                    label={`Option ${opt.option_no} Image`}
                    currentUrl={opt.image_url}
                    uploadKey={`opt_${opt.option_no}`}
                    uploads={uploads}
                    errors={errors}
                    onFile={file => upload(file, 'option', opt.id || 0, `opt_${opt.option_no}`)}
                />
            ))}
        </div>
    )
}

function ImageUploadSlot({ label, currentUrl, uploadKey, uploads, errors, onFile }) {
    const status = uploads[uploadKey]
    const err = errors[uploadKey]
    const effectiveUrl = status && status !== 'uploading' ? status : currentUrl

    return (
        <div className="flex items-center gap-3">
            {/* Thumbnail */}
            <div className="w-12 h-12 flex-shrink-0 rounded-lg bg-surface-100 overflow-hidden border border-surface-200">
                {effectiveUrl && !effectiveUrl.startsWith('PLACEHOLDER') ? (
                    <img src={effectiveUrl} alt={label} className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <svg className="w-5 h-5 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </div>
                )}
            </div>

            <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-surface-600 mb-1">{label}</p>
                {err && <p className="text-xs text-red-500">{err}</p>}
                {status === 'uploading' && <p className="text-xs text-brand-500">Uploading…</p>}
            </div>

            <label className="flex-shrink-0 cursor-pointer">
                <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f) }}
                    disabled={status === 'uploading'}
                />
                <span className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${status && status !== 'uploading' ? 'bg-green-100 text-green-700' : 'bg-brand-50 text-brand-700 hover:bg-brand-100'}`}>
                    {status && status !== 'uploading' ? '✓ Done' : 'Upload'}
                </span>
            </label>
        </div>
    )
}
