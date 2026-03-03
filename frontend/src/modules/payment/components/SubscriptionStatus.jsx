import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

export const SubscriptionStatus = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { status, isLoading } = usePaymentStore()

    if (isLoading) {
        return <div className="animate-pulse bg-gray-200 h-6 w-24 rounded-full"></div>
    }

    if (!status) return null

    if (status.is_active) {
        // Determine days remaining string
        let remainingText = ''
        if (status.days_remaining !== null) {
            if (status.days_remaining === 0) {
                remainingText = t('payment.expires_today', 'Expires today')
            } else if (status.days_remaining <= 30) {
                remainingText = t('payment.days_left', '{{count}} days left', { count: status.days_remaining })
            }
        }

        const dateStr = status.expires_at ? new Date(status.expires_at).toLocaleDateString() : ''

        return (
            <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <span className="w-2 h-2 mr-1.5 bg-green-500 rounded-full"></span>
                    {t('payment.active_until', 'Active until {{date}}', { date: dateStr })}
                </span>
                {remainingText && (
                    <span className="text-xs text-orange-600 font-medium">{remainingText}</span>
                )}
            </div>
        )
    }

    // Handle expired state vs never subscribed
    const isExpired = status.expires_at !== null && status.expires_at !== undefined

    if (isExpired) {
        return (
            <div className="flex items-center space-x-3">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                    <span className="w-2 h-2 mr-1.5 bg-red-500 rounded-full"></span>
                    {t('payment.expired', 'Expired')}
                </span>
                <button
                    onClick={() => navigate('/upgrade')}
                    className="text-sm font-semibold text-blue-600 hover:text-blue-800 underline decoration-blue-300 underline-offset-2 transition-colors"
                >
                    {t('payment.renew_now', 'Renew')}
                </button>
            </div>
        )
    }

    // Free Plan State
    return (
        <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                <svg className="w-3 h-3 mr-1 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"></path>
                </svg>
                {t('payment.free_plan', 'Free Plan')}
            </span>
            <button
                onClick={() => navigate('/upgrade')}
                className="text-sm font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-3 py-1 rounded-full border border-blue-200 transition-colors"
            >
                {t('payment.upgrade', 'Upgrade')}
            </button>
        </div>
    )
}
