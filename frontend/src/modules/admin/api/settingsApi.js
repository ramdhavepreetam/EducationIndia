import apiClient from '@/config/apiClient'

export const settingsApi = {
    fetchSettings: () => apiClient.get('/api/admin/settings').then(r => r.data),
    updateSetting: (key, value) => apiClient.put(`/api/admin/settings/${key}`, { value }).then(r => r.data),

    fetchSubscriptions: (status = 'all', page = 1) =>
        apiClient.get(`/api/admin/subscriptions?status=${status}&page=${page}`).then(r => r.data),

    extendSubscription: (id, months) =>
        apiClient.post(`/api/admin/subscriptions/${id}/extend`, { months }).then(r => r.data),

    cancelSubscription: (id) =>
        apiClient.post(`/api/admin/subscriptions/${id}/cancel`).then(r => r.data),

    grantSubscription: (email, planId, months) =>
        apiClient.post('/api/admin/subscriptions/grant', { email, plan_id: planId, months }).then(r => r.data),

    fetchPlans: () =>
        apiClient.get('/api/payment/plans').then(r => r.data),
}
