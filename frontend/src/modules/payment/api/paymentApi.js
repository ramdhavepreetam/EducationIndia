import apiClient from '@/config/apiClient'

export const paymentApi = {
    getPlans: () => apiClient.get('/api/payment/plans').then(r => r.data),
    getStatus: () => apiClient.get('/api/payment/subscription').then(r => r.data),
    createOrder: () => apiClient.post('/api/payment/create-order').then(r => r.data),
    verifyPayment: (data) => apiClient.post('/api/payment/verify', data).then(r => r.data),
    getHistory: () => apiClient.get('/api/payment/history').then(r => r.data),
}
