import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'
import { ImageUploadGrid } from '../components/ImageUploadGrid'

const EXAM_OPTIONS = [
    { id: 1, label: 'Paper I (501) — English + Maths' },
    { id: 2, label: 'Paper II (502) — Marathi + Intelligence Test' },
]

/**
 * ImageUploaderPage — upload images for Intelligence Test / image-type questions.
 * Filters questions that need images (image_only, text_image, or PLACEHOLDER_ urls).
 */
export function ImageUploaderPage() {
    const { t } = useTranslation()
    const { questions, questionsLoading, questionsError, fetchQuestions } = useAdminStore()
    const [examId, setExamId] = useState(EXAM_OPTIONS[0].id)

    useEffect(() => {
        fetchQuestions(examId)
    }, [examId, fetchQuestions])

    return (
        <div className="p-4 sm:p-8 max-w-5xl mx-auto pb-24">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('admin.imageUploader', 'Image Uploader')}
                </h1>
                <p className="text-surface-500 mt-1">
                    {t('admin.imageUploaderSub', 'Upload images for Intelligence Test questions. Max 5 MB per image (JPEG, PNG, WebP).')}
                </p>
            </div>

            {/* Exam picker */}
            <div className="mb-6">
                <select
                    value={examId}
                    onChange={e => setExamId(Number(e.target.value))}
                    className="text-sm border border-surface-200 rounded-xl px-4 py-2 text-surface-700 font-medium focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
                >
                    {EXAM_OPTIONS.map(ex => (
                        <option key={ex.id} value={ex.id}>{ex.label}</option>
                    ))}
                </select>
            </div>

            {questionsLoading && (
                <div className="flex items-center justify-center py-20">
                    <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                </div>
            )}

            {questionsError && !questionsLoading && (
                <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-200">{questionsError}</div>
            )}

            {!questionsLoading && !questionsError && (
                <ImageUploadGrid questions={questions} />
            )}
        </div>
    )
}
