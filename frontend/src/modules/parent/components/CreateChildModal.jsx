import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParentStore } from '../store/parentStore'

export default function CreateChildModal({ isOpen, onClose, onSuccess }) {
    const { t } = useTranslation()
    const { createChild, saveError } = useParentStore()

    const [formData, setFormData] = useState({
        name: '',
        std_class: '5',
        medium: 'english',
        school_name: '',
        district: '',
        avatar_color: '#3B82F6'
    })
    const [error, setError] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)

    // Clear errors when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            setError(null)
            setFormData({
                name: '',
                std_class: '5',
                medium: 'english',
                school_name: '',
                district: '',
                avatar_color: '#3B82F6'
            })
        }
    }, [isOpen])

    if (!isOpen) return null

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
        setError(null)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(null)
        setIsSubmitting(true)

        if (!formData.name.trim()) {
            setError("Child's name is required")
            setIsSubmitting(false)
            return
        }

        const payload = {
            ...formData,
            std_class: parseInt(formData.std_class, 10)
        }

        const result = await createChild(payload)
        if (result.success) {
            onSuccess(result.child)
        } else {
            setError(result.error || saveError || "Failed to create child profile")
        }
        setIsSubmitting(false)
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden">

                {/* Header */}
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-xl font-semibold text-gray-900">
                        {t('parent.createChild.title', 'Add Child Profile')}
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Form area */}
                <div className="p-6">
                    <form onSubmit={handleSubmit} className="space-y-4">

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('parent.createChild.name', "Child's Name")} <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder={t('parent.createChild.namePlaceholder', 'e.g. Rohan Sharma')}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('parent.createChild.class', 'Class')} <span className="text-red-500">*</span>
                            </label>
                            <select
                                name="std_class"
                                value={formData.std_class}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="5">5th Standard (Pre-Upper Primary)</option>
                                <option value="8">8th Standard (Pre-Secondary)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('parent.createChild.medium', 'Medium')}
                            </label>
                            <select
                                name="medium"
                                value={formData.medium}
                                onChange={handleChange}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="english">English</option>
                                <option value="marathi">Marathi</option>
                                <option value="hindi">Hindi</option>
                                <option value="semi_english">Semi-English</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('parent.createChild.schoolName', 'School Name')}
                            </label>
                            <input
                                type="text"
                                name="school_name"
                                value={formData.school_name}
                                onChange={handleChange}
                                placeholder={t('common.optional', 'Optional')}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('parent.createChild.district', 'District')}
                            </label>
                            <input
                                type="text"
                                name="district"
                                value={formData.district}
                                onChange={handleChange}
                                placeholder={t('common.optional', 'Optional')}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors disabled:opacity-50 mt-2"
                        >
                            {isSubmitting ? t('parent.createChild.creating', 'Creating...') : t('parent.createChild.submit', 'Create Profile')}
                        </button>
                    </form>
                </div>

            </div>
        </div>
    )
}
