import apiClient from '@/config/apiClient'

export const adminApi = {
    // ── Overview ─────────────────────────────────────────────────────────────
    getOverview: () =>
        apiClient.get('/api/admin/dashboard/overview').then(r => r.data),

    getRecentAttempts: () =>
        apiClient.get('/api/admin/dashboard/attempts/recent').then(r => r.data),

    // ── Exam catalog (admin — includes inactive) ──────────────────────────────
    listAllExams: () =>
        apiClient.get('/api/admin/catalog/exams').then(r => r.data),

    publishExam: (examId) =>
        apiClient.put(`/api/admin/catalog/exams/${examId}/publish`).then(r => r.data),

    unpublishExam: (examId) =>
        apiClient.put(`/api/admin/catalog/exams/${examId}/unpublish`).then(r => r.data),

    // ── Questions ─────────────────────────────────────────────────────────────
    listQuestionsAdmin: (examId) =>
        apiClient.get('/api/admin/questions/', { params: { exam_id: examId } }).then(r => r.data),

    updateQuestion: (questionId, data) =>
        apiClient.put(`/api/admin/questions/${questionId}`, data).then(r => r.data),

    deleteQuestion: (questionId) =>
        apiClient.delete(`/api/admin/questions/${questionId}`),

    bulkImport: (payload) =>
        apiClient.post('/api/admin/questions/bulk-import', payload).then(r => r.data),

    // ── Question stats ─────────────────────────────────────────────────────────
    getQuestionStats: (examId) =>
        apiClient.get('/api/admin/questions/stats', { params: { exam_id: examId } }).then(r => r.data),

    // ── Media upload ───────────────────────────────────────────────────────────
    uploadImage: (file, uploadType, entityId) => {
        const form = new FormData()
        form.append('file', file)
        form.append('upload_type', uploadType)
        form.append('entity_id', String(entityId))
        return apiClient.post('/api/media/upload', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then(r => r.data)
    },
}
