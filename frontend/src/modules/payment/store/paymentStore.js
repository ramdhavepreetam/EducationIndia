import { create } from 'zustand'
import { paymentApi } from '../api/paymentApi'
import { useAuthStore } from '@/modules/auth/store/authStore'

/**
 * Global store for Payment module (ADR-014).
 * Handles fetching plans, checking user subscription status,
 * and completely encapsulating the Razorpay checkout flow.
 */
export const usePaymentStore = create((set, get) => ({
    plans: [],
    plan: null,
    status: null,
    lastPayment: null,   // populated after successful payment for receipt display
    history: [],
    isLoading: false,
    isLoadingHistory: false,
    isProcessing: false,
    error: null,

    loadPlan: async () => {
        set({ isLoading: true, error: null })
        try {
            const plans = await paymentApi.getPlans()
            const planList = Array.isArray(plans) ? plans : [plans].filter(Boolean)
            set({ plans: planList, plan: planList[0] || null, isLoading: false })
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

    loadHistory: async () => {
        set({ isLoadingHistory: true })
        try {
            const history = await paymentApi.getHistory()
            set({ history, isLoadingHistory: false })
        } catch {
            set({ isLoadingHistory: false })
        }
    },

    initiatePayment: async (navigate, planId) => {
        set({ isProcessing: true, error: null })
        try {
            const selectedPlan = get().plans.find(p => p.id === planId) || get().plan
            if (!selectedPlan?.id) {
                throw new Error('Please select a subscription plan.')
            }
            // 1. Create order on backend
            const order = await paymentApi.createOrder(selectedPlan.id)

            // 2. Get user details for prefill
            const { user } = useAuthStore.getState()

            // 3. Open Razorpay modal
            const options = {
                key: order.key_id,
                amount: order.amount,
                currency: order.currency,
                name: 'ScholarPath',
                description: selectedPlan.name,
                order_id: order.order_id,
                prefill: {
                    name: user?.full_name || '',
                    email: user?.email || '',
                    contact: user?.phone || '',
                },
                handler: async (response) => {
                    try {
                        // 4. Verify payment on backend
                        const result = await paymentApi.verifyPayment({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                        })
                        set({
                            status: result,
                            isProcessing: false,
                            lastPayment: {
                                razorpay_payment_id: response.razorpay_payment_id,
                                amount_inr: selectedPlan.price_inr,
                                plan_id: selectedPlan.id,
                                plan_name: result.plan_name,
                                paid_at: new Date().toISOString(),
                            },
                        })

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

    reset: () => set({ plans: [], plan: null, status: null, lastPayment: null, history: [], error: null, isLoading: false, isLoadingHistory: false, isProcessing: false }),
}))
