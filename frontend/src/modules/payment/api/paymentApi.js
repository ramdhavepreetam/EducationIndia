import apiClient from '@/config/apiClient'

export const paymentApi = {
    getPlans: () => apiClient.get('/api/payment/plans').then(r => r.data),
    getStatus: () => apiClient.get('/api/payment/status').then(r => r.data),
    createOrder: (planId) => apiClient.post('/api/payment/create-order', { plan_id: planId }).then(r => r.data),
    verifyPayment: (data) => apiClient.post('/api/payment/verify', data).then(r => r.data),
    getHistory: () => apiClient.get('/api/payment/history').then(r => r.data),
}
