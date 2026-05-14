import React, { useState, useEffect } from 'react'
import { settingsApi } from '../api/settingsApi'
import { SettingRow } from '../components/SettingRow'

export const AdminSettingsPage = () => {
    const [settings, setSettings] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)
    const [toastMessage, setToastMessage] = useState(null)
    const [savingKey, setSavingKey] = useState(null)

    useEffect(() => {
        loadSettings()
    }, [])

    const loadSettings = async () => {
        setIsLoading(true)
        try {
            const data = await settingsApi.fetchSettings()
            setSettings(data)
        } catch (err) {
            setError('Failed to load settings.')
        } finally {
            setIsLoading(false)
        }
    }

    const showToast = (message) => {
        setToastMessage(message)
        setTimeout(() => setToastMessage(null), 4000)
    }

    const handleSave = async (key, value) => {
        setSavingKey(key)
        try {
            await settingsApi.updateSetting(key, value)
            setSettings((prev) =>
                prev.map((s) => (s.key === key ? { ...s, value, updated_at: new Date().toISOString() } : s))
            )

            showToast(`Setting ${key} updated successfully.`)
        } catch (err) {
            setError(`Failed to save ${key}`)
        } finally {
            setSavingKey(null)
        }
    }

    // Helper to group settings
    const renderGroup = (title, keys) => {
        const groupSettings = settings.filter((s) => keys.includes(s.key))
        if (groupSettings.length === 0) return null

        return (
            <div className="mb-10 bg-white shadow-sm border border-gray-200 rounded-xl px-6 py-4">
                <h2 className="text-xl font-bold text-gray-900 mb-6 pb-2 border-b border-gray-100">{title}</h2>
                <div className="space-y-2">
                    {groupSettings.map((s) => (
                        <SettingRow key={s.key} setting={s} onSave={handleSave} isSaving={savingKey === s.key} />
                    ))}
                </div>
            </div>
        )
    }

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-8 relative">
            {/* Toast Notification */}
            {toastMessage && (
                <div className="fixed bottom-4 right-4 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-xl z-50 flex items-center gap-3 animate-fade-in-up">
                    <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                    {toastMessage}
                </div>
            )}

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 leading-tight">System Settings</h1>
                    <p className="text-gray-500 mt-1 text-sm">Real-time configuration for the ScholarPath platform.</p>
                </div>
                <button
                    onClick={loadSettings}
                    className="text-sm px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                    Refresh All
                </button>
            </div>

            {error && (
                <div className="mb-8 bg-red-50 text-red-700 p-4 rounded-lg flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={() => setError(null)} className="text-red-500 hover:text-red-800">Dismiss</button>
                </div>
            )}

            {/* Sections based on ADR spec */}
            {renderGroup('Legacy Payment Defaults', ['access_duration_months'])}

            {renderGroup('Free Tier Limits', ['free_tier_exam_id', 'free_tier_max_attempts'])}

            <div className="mb-10 bg-white shadow-sm border border-gray-200 rounded-xl px-6 py-4">
                <div className="flex justify-between items-start mb-6 pb-2 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900">Payment Gateway</h2>
                </div>

                <div className="bg-orange-50 border-l-4 border-orange-400 p-4 mb-6">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path></svg>
                        </div>
                        <div className="ml-3">
                            <p className="text-sm text-orange-700 font-medium">
                                Set RAZORPAY_KEY_SECRET in the server <span className="font-mono bg-orange-100 px-1 rounded">.env</span> file. Never store the secret key here.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="space-y-2">
                    {settings
                        .filter((s) => ['razorpay_key_id'].includes(s.key))
                        .map((s) => (
                            <SettingRow key={s.key} setting={s} onSave={handleSave} isSaving={savingKey === s.key} />
                        ))}
                </div>
            </div>

            {renderGroup('App Configuration', ['app_name', 'support_email', 'maintenance_mode', 'allow_registrations'])}

            <div className="mt-8 text-center text-xs text-gray-400">
                ScholarPath Admin Control Panel
            </div>
        </div>
    )
}
