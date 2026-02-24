import { create } from 'zustand'
import { dashboardApi } from '../api/dashboardApi'

export const useDashboardStore = create((set) => ({
    dashboardData: null,
    isLoading: false,
    error: null,

    fetchDashboard: async () => {
        set({ isLoading: true, error: null })
        try {
            const data = await dashboardApi.getStudentDashboard()
            set({ dashboardData: data, isLoading: false })
            return data
        } catch (err) {
            const message = err.response?.data?.detail || 'Failed to fetch dashboard data'
            set({ error: message, isLoading: false })
            throw err
        }
    },

    reset: () => set({ dashboardData: null, isLoading: false, error: null })
}))
