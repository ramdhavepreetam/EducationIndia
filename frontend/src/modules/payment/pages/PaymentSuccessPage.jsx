import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

export const PaymentSuccessPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { status, loadStatus } = usePaymentStore()

    // Make sure we have the latest status when arriving on this page
    useEffect(() => {
        loadStatus()
    }, [loadStatus])

    const dateStr = status?.expires_at ? new Date(status.expires_at).toLocaleDateString() : ''

    return (
        <div className="min-h-[70vh] flex flex-col items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-8 text-center">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                    </svg>
                </div>

                <h1 className="text-3xl font-extrabold text-gray-900 mb-2">
                    {t('payment.success_title', 'Payment Successful!')}
                </h1>

                <p className="text-lg text-gray-600 mb-6">
                    {t('payment.success_subtitle', 'Thank you. Your premium access is now active.')}
                </p>

                {dateStr && (
                    <div className="bg-green-50 border border-green-200 rounded p-4 mb-8">
                        <p className="text-green-800 font-medium">
                            {t('payment.active_until', 'Full access is activated until {{date}}', { date: dateStr })}
                        </p>
                    </div>
                )}

                <div className="flex flex-col sm:flex-row justify-center gap-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                    >
                        {t('common.go_to_dashboard', 'Go to Dashboard')}
                    </button>
                    <button
                        onClick={() => navigate('/exams')}
                        className="px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded-lg transition-colors"
                    >
                        {t('common.start_exam', 'Browse Exams')}
                    </button>
                </div>
            </div>
        </div>
    )
}
