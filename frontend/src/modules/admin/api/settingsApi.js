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
        apiClient.get('/api/admin/plans').then(r => r.data),

    createPlan: (data) =>
        apiClient.post('/api/admin/plans', data).then(r => r.data),

    updatePlan: (planId, data) =>
        apiClient.put(`/api/admin/plans/${planId}`, data).then(r => r.data),

    addPlanEntitlement: (planId, data) =>
        apiClient.post(`/api/admin/plans/${planId}/entitlements`, data).then(r => r.data),

    deletePlanEntitlement: (planId, entitlementId) =>
        apiClient.delete(`/api/admin/plans/${planId}/entitlements/${entitlementId}`).then(r => r.data),

    fetchPlanScopeOptions: () =>
        apiClient.get('/api/admin/plans/scope-options').then(r => r.data),

    // Payment analytics
    fetchPaymentStats: () =>
        apiClient.get('/api/admin/payments/stats').then(r => r.data),

    fetchAllPayments: ({ status, search, page = 1, limit = 50 } = {}) => {
        const params = new URLSearchParams()
        if (status && status !== 'all') params.set('status', status)
        if (search) params.set('search', search)
        params.set('page', page)
        params.set('limit', limit)
        return apiClient.get(`/api/admin/payments?${params}`).then(r => r.data)
    },

    fetchMonthlyRevenue: (months = 6) =>
        apiClient.get(`/api/admin/payments/monthly?months=${months}`).then(r => r.data),

    fetchPaymentsByParent: (parentId) =>
        apiClient.get(`/api/admin/payments/user/${parentId}`).then(r => r.data),
}
