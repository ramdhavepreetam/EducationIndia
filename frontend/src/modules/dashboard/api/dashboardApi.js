import apiClient from '@/config/apiClient'

export const dashboardApi = {
    /**
     * Fetch the student dashboard data
     * @returns {Promise<Object>} Dashboard data containing available_exams, recent_attempts, stats
     */
    getStudentDashboard: async (childId = null) => {
        const url = childId ? `/api/admin/dashboard/student?child_id=${childId}` : '/api/admin/dashboard/student'
        const response = await apiClient.get(url)
        return response.data
    }
}
