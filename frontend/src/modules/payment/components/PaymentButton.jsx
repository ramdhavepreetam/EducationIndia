import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePaymentStore } from '../store/paymentStore'

export const PaymentButton = ({ planId }) => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { initiatePayment, isProcessing } = usePaymentStore()

    const handlePay = () => {
        initiatePayment(navigate)
    }

    return (
        <button
            onClick={handlePay}
            disabled={isProcessing}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-4 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
        >
            {isProcessing ? (
                <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>{t('payment.processing', 'Processing...')}</span>
                </>
            ) : (
                <span>{t('payment.pay_with_razorpay', 'Pay Securely with Razorpay')}</span>
            )}
        </button>
    )
}
