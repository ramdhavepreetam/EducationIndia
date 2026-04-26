import apiClient from '@/config/apiClient'

export const attemptApi = {
    /** Start a new attempt or resume an ongoing one */
    start: async (examId, childProfileId) => {
        const response = await apiClient.post('/api/attempts/start', {
            exam_id: Number(examId),
            child_profile_id: childProfileId
        })
        return response.data
    },

    /** Fetch the exact state of an attempt to resume (timer, responses) */
    getState: async (attemptId) => {
        const response = await apiClient.get(`/api/attempts/${attemptId}/state`)
        return response.data
    },

    /** List attempts for a specific exam */
    listAttempts: async (examId) => {
        const response = await apiClient.get(`/api/attempts/?exam_id=${examId}`)
        return response.data
    },

    /** Autosave a single response interactively */
    saveResponse: async (attemptId, questionId, questionNo, selectedOption, selectedOptions, isMarkedReview, timeTakenSeconds = 0) => {
        const response = await apiClient.post(`/api/attempts/${attemptId}/responses`, {
            question_id: questionId,
            question_no: questionNo,
            selected_option: selectedOption,
            selected_options: selectedOptions,
            is_marked_review: isMarkedReview,
            time_taken_seconds: timeTakenSeconds
        })
        return response.data
    },

    /** Submit the attempt for grading */
    submit: async (attemptId) => {
        const response = await apiClient.post(`/api/attempts/${attemptId}/submit`)
        return response.data
    },

    /** Fetch all details and questions for an exam delivery view */
    getQuestions: async (examId) => {
        // We fetch exam structure using catalog API
        const response = await apiClient.get(`/api/catalog/exams/${Number(examId)}`)
        return response.data
    },

    /** Fetch exam delivery questions (without correct options) */
    getExamDeliveryQuestions: async (examId) => {
        // Requires question module proxy or direct access via catalog if wired
        // As per ADR, question fetching for delivery goes here or question API.
        const response = await apiClient.get(`/api/questions/?exam_id=${Number(examId)}`)
        return response.data
    }
}
