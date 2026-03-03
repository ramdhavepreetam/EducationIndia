import apiClient from '@/config/apiClient'

export const parentApi = {

  getDashboard: () =>
    apiClient.get('/api/parent/dashboard')
      .then(r => r.data),

  getChildren: () =>
    apiClient.get('/api/parent/children')
      .then(r => r.data),

  getChildDetail: (studentId) =>
    apiClient.get(`/api/parent/children/${studentId}`)
      .then(r => r.data),

  getChildAttempts: (studentId, page = 1, size = 10) =>
    apiClient.get(`/api/parent/children/${studentId}/attempts`, {
      params: { page, size }
    }).then(r => r.data),

  getChildTopics: (studentId) =>
    apiClient.get(`/api/parent/children/${studentId}/topics`)
      .then(r => r.data),

  createChild: (formData) =>
    apiClient.post('/api/children', formData).then(r => r.data),

  updateChild: (childId, formData) =>
    apiClient.put(`/api/children/${childId}`, formData).then(r => r.data),

  deleteChild: (childId) =>
    apiClient.delete(`/api/children/${childId}`).then(r => r.data),
}
