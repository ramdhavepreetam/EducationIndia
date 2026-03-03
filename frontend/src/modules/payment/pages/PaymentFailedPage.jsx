import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

export const PaymentFailedPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { error } = usePaymentStore()

    return (
        <div className="min-h-[70vh] flex flex-col items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-8 text-center border-t-8 border-red-500">
                <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </div>

                <h1 className="text-3xl font-extrabold text-gray-900 mb-2">
                    {t('payment.failed_title', 'Payment Failed')}
                </h1>

                <p className="text-lg text-gray-600 mb-6">
                    {t('payment.failed_subtitle', 'We could not process your payment. Your account was not charged.')}
                </p>

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded p-4 mb-8 text-left overflow-hidden">
                        <p className="text-sm font-semibold text-red-800 mb-1">Error Details:</p>
                        <p className="text-sm text-red-700 break-words">{error}</p>
                    </div>
                )}

                <div className="flex flex-col sm:flex-row justify-center gap-4">
                    <button
                        onClick={() => navigate('/upgrade')}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                    >
                        {t('common.try_again', 'Try Again')}
                    </button>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded-lg transition-colors"
                    >
                        {t('common.cancel', 'Cancel')}
                    </button>
                </div>
            </div>
        </div>
    )
}
