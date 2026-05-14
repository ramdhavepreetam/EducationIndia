import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'
import { PlanCard } from '../components/PlanCard'
import { PaymentButton } from '../components/PaymentButton'

export const UpgradePage = () => {
    const { t } = useTranslation()
    const { plans, plan, loadPlan, isLoading, error } = usePaymentStore()
    const [selectedPlanId, setSelectedPlanId] = useState(null)

    // Make sure we always load the fresh plan pricing
    useEffect(() => {
        loadPlan()
    }, [loadPlan])

    useEffect(() => {
        if (!selectedPlanId && (plans?.length || 0) > 0) {
            setSelectedPlanId(plans[0].id)
        }
    }, [plans, selectedPlanId])

    const selectedPlan = plans.find(p => p.id === selectedPlanId) || plan

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="text-center max-w-3xl mx-auto mb-16">
                <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl mb-4">
                    {t('payment.upgrade_title', 'Unlock Full Access for ScholarPath')}
                </h1>
                <p className="text-xl text-gray-500">
                    {t(
                        'payment.upgrade_subtitle',
                        'Get unlimited access to all exams and comprehensive analysis features to help your child succeed.'
                    )}
                </p>
            </div>

            {isLoading ? (
                <div className="flex justify-center items-center py-24">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            ) : error ? (
                <div className="max-w-3xl mx-auto bg-red-50 p-6 rounded-lg text-red-700 text-center">
                    <p className="text-lg font-medium mb-4">{error}</p>
                    <button
                        onClick={() => loadPlan()}
                        className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-red-800 font-medium"
                    >
                        {t('common.try_again', 'Try Again')}
                    </button>
                </div>
            ) : plans.length > 0 ? (
                <div className="flex flex-col lg:flex-row gap-8 max-w-6xl mx-auto relative align-start">

                    {/* Free Tier Features Box */}
                    <div className="flex-1 bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
                        <h3 className="text-lg font-bold text-gray-900 mb-6 uppercase tracking-wide">
                            {t('payment.free_tier', 'Free Plan')}
                        </h3>
                        <ul className="space-y-4">
                            <li className="flex items-start">
                                <span className="text-green-500 mr-2">✓</span>
                                <span className="text-gray-700">{t('payment.free_paper_1', 'Paper I only (Marathi + Math)')}</span>
                            </li>
                            <li className="flex items-start">
                                <span className="text-green-500 mr-2">✓</span>
                                <span className="text-gray-700">{t('payment.free_attempts', 'Up to 3 free exam attempts')}</span>
                            </li>
                            <li className="flex items-start">
                                <span className="text-green-500 mr-2">✓</span>
                                <span className="text-gray-700">{t('payment.free_score_only', 'Basic score & grade display')}</span>
                            </li>
                            <li className="flex items-start opacity-40">
                                <span className="text-red-500 mr-2">✗</span>
                                <span className="text-gray-700">{t('payment.no_paper_2', 'No access to Paper II (English + Intelligence)')}</span>
                            </li>
                            <li className="flex items-start opacity-40">
                                <span className="text-red-500 mr-2">✗</span>
                                <span className="text-gray-700">{t('payment.no_analysis', 'No detailed topic analysis')}</span>
                            </li>
                            <li className="flex items-start opacity-40">
                                <span className="text-red-500 mr-2">✗</span>
                                <span className="text-gray-700">{t('payment.no_pdf', 'No downloadable PDF reports')}</span>
                            </li>
                        </ul>
                    </div>

                    {/* Premium Plan Card */}
                    <div className="flex-[1.5] grid gap-4 md:grid-cols-2">
                        {plans.map(option => (
                            <button
                                type="button"
                                key={option.id}
                                onClick={() => setSelectedPlanId(option.id)}
                                className={`relative text-left rounded-lg transition ${
                                    selectedPlanId === option.id
                                        ? 'ring-2 ring-blue-600 ring-offset-2'
                                        : 'hover:ring-1 hover:ring-blue-200'
                                }`}
                            >
                                {selectedPlanId === option.id && (
                                    <div className="absolute top-0 inset-x-0 h-2 bg-blue-600 rounded-t-lg z-10"></div>
                                )}
                                <PlanCard plan={option} />
                            </button>
                        ))}
                    </div>

                </div>
            ) : null}

            {/* Checkout Area */}
            {selectedPlan && (
                <div className="max-w-lg mx-auto mt-16 text-center">
                    <PaymentButton planId={selectedPlan.id} />
                    <p className="mt-3 text-sm text-gray-500">
                        Selected plan: <span className="font-semibold text-gray-800">{selectedPlan.name}</span>
                    </p>
                    <div className="mt-6 flex flex-wrap justify-center gap-4 text-gray-400 text-sm">
                        <span className="flex items-center">
                            <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"></path></svg>
                            {t('payment.secure_payment', 'Secure payment by Razorpay')}
                        </span>
                        <span className="flex items-center">
                            <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"></path><path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"></path></svg>
                            {t('payment.instant_activation', 'Instant activation')}
                        </span>
                    </div>
                    <div className="mt-4 text-xs text-gray-400 font-medium">
                        UPI · Credit Cards · Debit Cards · Netbanking
                    </div>

                    {/* Refund policy — legal requirement */}
                    <p className="mt-6 text-xs text-gray-400 leading-relaxed max-w-sm mx-auto">
                        {t('payment.refund_note',
                            'By completing payment you agree to our terms. Payments are non-refundable once access is activated. For payment issues contact'
                        )}{' '}
                        <a href="mailto:support@scholarpath.in" className="underline hover:text-gray-600">
                            support@scholarpath.in
                        </a>.
                    </p>
                </div>
            )}
        </div>
    )
}
