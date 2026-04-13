import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

export const PaymentSuccessPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { status, lastPayment, loadStatus } = usePaymentStore()

    // Make sure we have the latest status when arriving on this page
    useEffect(() => {
        loadStatus()
    }, [loadStatus])

    const dateStr = status?.expires_at ? new Date(status.expires_at).toLocaleDateString('en-IN') : ''
    const paidAtStr = lastPayment?.paid_at
        ? new Date(lastPayment.paid_at).toLocaleString('en-IN')
        : new Date().toLocaleString('en-IN')

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

                {/* Receipt details */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-left space-y-2">
                    {lastPayment?.plan_name && (
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-500">{t('payment.plan', 'Plan')}</span>
                            <span className="font-medium text-gray-900">{lastPayment.plan_name}</span>
                        </div>
                    )}
                    {lastPayment?.amount_inr && (
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-500">{t('payment.amount_paid', 'Amount Paid')}</span>
                            <span className="font-medium text-gray-900">₹{lastPayment.amount_inr}</span>
                        </div>
                    )}
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">{t('payment.date', 'Date')}</span>
                        <span className="font-medium text-gray-900">{paidAtStr}</span>
                    </div>
                    {lastPayment?.razorpay_payment_id && (
                        <div className="flex justify-between text-sm border-t border-gray-200 pt-2 mt-2">
                            <span className="text-gray-500">{t('payment.transaction_id', 'Transaction ID')}</span>
                            <span className="font-mono text-xs text-gray-700 break-all text-right max-w-[200px]">
                                {lastPayment.razorpay_payment_id}
                            </span>
                        </div>
                    )}
                </div>

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
