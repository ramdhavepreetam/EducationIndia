import apiClient from '@/config/apiClient'

export const teacherApi = {
    getDashboard: () =>
        apiClient.get('/api/teacher/dashboard').then(r => r.data),

    listStudents: (params = {}) =>
        apiClient.get('/api/teacher/students', { params }).then(r => r.data),

    lookupStudentByEmail: (email) =>
        apiClient.get('/api/teacher/students/lookup', { params: { email } }).then(r => r.data),

    getStudentDetail: (studentId) =>
        apiClient.get(`/api/teacher/students/${studentId}`).then(r => r.data),

    assignExam: (data) =>
        apiClient.post('/api/teacher/assign', data).then(r => r.data),
}
