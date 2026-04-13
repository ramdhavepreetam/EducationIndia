import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

const STATUS_STYLES = {
    captured: 'bg-green-100 text-green-800',
    failed:   'bg-red-100 text-red-800',
    refunded: 'bg-orange-100 text-orange-800',
    created:  'bg-gray-100 text-gray-600',
}

const STATUS_LABELS = {
    captured: 'Paid',
    failed:   'Failed',
    refunded: 'Refunded',
    created:  'Pending',
}

function CopyButton({ text }) {
    const [copied, setCopied] = useState(false)
    const handleCopy = () => {
        navigator.clipboard.writeText(text).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }
    return (
        <button
            onClick={handleCopy}
            className="ml-1.5 text-gray-400 hover:text-gray-600 transition-colors"
            title="Copy transaction ID"
        >
            {copied
                ? <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                : <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            }
        </button>
    )
}

export const PaymentHistoryPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { history, status, isLoadingHistory, loadHistory, loadStatus } = usePaymentStore()

    useEffect(() => {
        loadHistory()
        loadStatus()
    }, [loadHistory, loadStatus])

    const dateStr = status?.expires_at
        ? new Date(status.expires_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
        : null

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

            {/* Header */}
            <div className="mb-8">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                    {t('common.back', 'Back')}
                </button>
                <h1 className="text-2xl font-bold text-gray-900">
                    {t('payment.history_title', 'Payment History')}
                </h1>
                <p className="text-gray-500 mt-1 text-sm">
                    {t('payment.history_subtitle', 'All your ScholarPath subscription payments')}
                </p>
            </div>

            {/* Active subscription summary card */}
            {status?.is_active && dateStr && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-green-100 rounded-full flex items-center justify-center">
                            <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-green-900">
                                {status.plan_name || t('payment.standard_access', 'Standard Access')} — {t('payment.active', 'Active')}
                            </p>
                            <p className="text-xs text-green-700">
                                {t('payment.expires_on', 'Expires on {{date}}', { date: dateStr })}
                                {status.days_remaining != null && status.days_remaining <= 30 && (
                                    <span className="ml-2 font-medium text-orange-600">
                                        ({status.days_remaining === 0
                                            ? t('payment.expires_today', 'Expires today')
                                            : t('payment.days_left', '{{count}} days left', { count: status.days_remaining })})
                                    </span>
                                )}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => navigate('/upgrade')}
                        className="text-xs font-semibold text-green-700 hover:text-green-900 border border-green-300 px-3 py-1.5 rounded-lg hover:bg-green-100 transition-colors"
                    >
                        {t('payment.renew', 'Renew Early')}
                    </button>
                </div>
            )}

            {/* Transaction table */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100">
                    <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                        {t('payment.transactions', 'Transactions')}
                    </h2>
                </div>

                {isLoadingHistory ? (
                    <div className="flex justify-center items-center py-16">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-16 px-4">
                        <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-gray-500 font-medium">
                            {t('payment.no_payments', 'No payments yet')}
                        </p>
                        <p className="text-gray-400 text-sm mt-1">
                            {t('payment.no_payments_sub', 'Your transactions will appear here after your first payment.')}
                        </p>
                        <button
                            onClick={() => navigate('/upgrade')}
                            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
                        >
                            {t('payment.upgrade_now', 'Upgrade Now')}
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Desktop table */}
                        <div className="hidden md:block overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                                        <th className="px-6 py-3 text-left">{t('payment.col_date', 'Date')}</th>
                                        <th className="px-6 py-3 text-left">{t('payment.col_amount', 'Amount')}</th>
                                        <th className="px-6 py-3 text-left">{t('payment.col_transaction', 'Transaction ID')}</th>
                                        <th className="px-6 py-3 text-left">{t('payment.col_status', 'Status')}</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {history.map((row) => (
                                        <tr key={row.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 text-gray-700 whitespace-nowrap">
                                                {row.paid_at
                                                    ? new Date(row.paid_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                                                    : new Date(row.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                                                }
                                                <span className="block text-xs text-gray-400">
                                                    {row.paid_at
                                                        ? new Date(row.paid_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
                                                        : ''
                                                    }
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                                                ₹{row.amount_inr}
                                                <span className="ml-1 text-xs font-normal text-gray-400">{row.currency}</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                {row.razorpay_payment_id ? (
                                                    <span className="flex items-center font-mono text-xs text-gray-600">
                                                        {row.razorpay_payment_id}
                                                        <CopyButton text={row.razorpay_payment_id} />
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-400 text-xs">—</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[row.status] || STATUS_STYLES.created}`}>
                                                    {STATUS_LABELS[row.status] || row.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile cards */}
                        <div className="md:hidden divide-y divide-gray-100">
                            {history.map((row) => (
                                <div key={row.id} className="px-4 py-4 space-y-2">
                                    <div className="flex justify-between items-start">
                                        <span className="font-semibold text-gray-900">₹{row.amount_inr}</span>
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[row.status] || STATUS_STYLES.created}`}>
                                            {STATUS_LABELS[row.status] || row.status}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500">
                                        {row.paid_at
                                            ? new Date(row.paid_at).toLocaleString('en-IN')
                                            : new Date(row.created_at).toLocaleDateString('en-IN')}
                                    </p>
                                    {row.razorpay_payment_id && (
                                        <div className="flex items-center gap-1">
                                            <span className="text-xs text-gray-400">Txn:</span>
                                            <span className="font-mono text-xs text-gray-600 truncate max-w-[200px]">
                                                {row.razorpay_payment_id}
                                            </span>
                                            <CopyButton text={row.razorpay_payment_id} />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Legal / refund policy note */}
            <div className="mt-6 bg-gray-50 border border-gray-200 rounded-xl p-5 text-sm text-gray-600 space-y-2">
                <p className="font-semibold text-gray-700">{t('payment.refund_policy_heading', 'Refund Policy')}</p>
                <p>
                    {t('payment.refund_policy_text',
                        'All payments are final and non-refundable once the subscription is activated. If you experienced a technical error during payment (e.g., amount was deducted but access was not activated), please contact us within 7 days and we will resolve it promptly.'
                    )}
                </p>
                <p>
                    {t('payment.support_contact', 'For payment issues, email us at')}{' '}
                    <a href="mailto:support@scholarpath.in" className="text-blue-600 hover:underline font-medium">
                        support@scholarpath.in
                    </a>
                    {' '}{t('payment.with_txn_id', 'with your Transaction ID.')}
                </p>
            </div>

        </div>
    )
}
