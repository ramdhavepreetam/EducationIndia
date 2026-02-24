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

  linkChild: (studentEmail) =>
    apiClient.post('/api/parent/children/link', {
      student_email: studentEmail
    }).then(r => r.data),

  updateNickname: (studentId, nickname) =>
    apiClient.put(`/api/parent/children/${studentId}/nickname`, {
      child_nickname: nickname
    }).then(r => r.data),

  unlinkChild: (studentId) =>
    apiClient.delete(`/api/parent/children/${studentId}/unlink`)
             .then(r => r.data),
}
