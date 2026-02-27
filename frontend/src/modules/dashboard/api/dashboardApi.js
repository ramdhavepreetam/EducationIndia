import apiClient from '@/config/apiClient'

export const dashboardApi = {
    /**
     * Fetch the student dashboard data
     * @returns {Promise<Object>} Dashboard data containing available_exams, recent_attempts, stats
     */
    getStudentDashboard: async () => {
        const response = await apiClient.get('/api/admin/dashboard/student')
        return response.data
    }
}
