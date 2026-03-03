import { create } from 'zustand'
import { paymentApi } from '../api/paymentApi'

/**
 * Global store for Payment module (ADR-014).
 * Handles fetching plans, checking user subscription status,
 * and completely encapsulating the Razorpay checkout flow.
 */
export const usePaymentStore = create((set, get) => ({
    plan: null,
    status: null,
    isLoading: false,
    isProcessing: false,
    error: null,

    loadPlan: async () => {
        set({ isLoading: true, error: null })
        try {
            const plan = await paymentApi.getPlans()
            set({ plan, isLoading: false })
        } catch (err) {
            set({ error: err.response?.data?.detail || 'Failed to load plan', isLoading: false })
        }
    },

    loadStatus: async () => {
        set({ isLoading: true, error: null })
        try {
            const status = await paymentApi.getStatus()
            set({ status, isLoading: false })
        } catch (err) {
            set({ error: err.response?.data?.detail || 'Failed to check status', isLoading: false })
        }
    },

    initiatePayment: async (navigate) => {
        set({ isProcessing: true, error: null })
        try {
            // 1. Create order on backend
            const order = await paymentApi.createOrder()

            // 2. Open Razorpay modal
            const options = {
                key: order.key_id,
                amount: order.amount,
                currency: order.currency,
                name: 'ScholarPath',
                description: 'Standard Access Subscription',
                order_id: order.order_id,
                handler: async (response) => {
                    try {
                        // 3. Verify payment on backend
                        const result = await paymentApi.verifyPayment({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                        })
                        set({ status: result, isProcessing: false })

                        if (result.is_active) {
                            navigate('/payment/success', { replace: true })
                        } else {
                            navigate('/payment/failed', { replace: true })
                        }
                    } catch (verifyErr) {
                        set({ error: verifyErr.response?.data?.detail || 'Verification failed', isProcessing: false })
                        navigate('/payment/failed', { replace: true })
                    }
                },
                modal: {
                    ondismiss: () => {
                        set({ isProcessing: false })
                    },
                },
                theme: {
                    color: '#2563EB', // blue-600
                },
            }

            if (!window.Razorpay) {
                throw new Error('Razorpay SDK failed to load. Are you offline?')
            }

            const rzp = new window.Razorpay(options)
            rzp.on('payment.failed', function (response) {
                set({ error: response.error.description, isProcessing: false })
                navigate('/payment/failed', { replace: true })
            })
            rzp.open()
        } catch (err) {
            set({ error: err.message || err.response?.data?.detail || 'Payment initiation failed', isProcessing: false })
        }
    },

    reset: () => set({ plan: null, status: null, error: null, isLoading: false, isProcessing: false }),
}))
