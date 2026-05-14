import { create } from 'zustand'
import { adminApi } from '../api/adminApi'

export const useAdminStore = create((set, get) => ({
    // ── Overview ──────────────────────────────────────────────────────────────
    overview: null,
    recentAttempts: [],
    overviewLoading: false,
    overviewError: null,

    fetchOverview: async () => {
        set({ overviewLoading: true, overviewError: null })
        try {
            const [overview, recentAttempts] = await Promise.all([
                adminApi.getOverview(),
                adminApi.getRecentAttempts(),
            ])
            set({ overview, recentAttempts, overviewLoading: false })
        } catch (e) {
            set({ overviewError: e.response?.data?.detail || 'Failed to load overview', overviewLoading: false })
        }
    },

    // ── Exams (publisher) ─────────────────────────────────────────────────────
    exams: [],
    examsLoading: false,
    examsError: null,

    fetchAllExams: async () => {
        set({ examsLoading: true, examsError: null })
        try {
            const exams = await adminApi.listAllExams()
            set({ exams, examsLoading: false })
        } catch (e) {
            set({ examsError: e.response?.data?.detail || 'Failed to load exams', examsLoading: false })
        }
    },

    publishExam: async (examId) => {
        try {
            await adminApi.publishExam(examId)
            set(state => ({
                exams: state.exams.map(ex => ex.id === examId ? { ...ex, is_active: true } : ex)
            }))
        } catch (e) {
            throw e
        }
    },

    unpublishExam: async (examId) => {
        try {
            await adminApi.unpublishExam(examId)
            set(state => ({
                exams: state.exams.map(ex => ex.id === examId ? { ...ex, is_active: false } : ex)
            }))
        } catch (e) {
            throw e
        }
    },

    updateExam: async (examId, data) => {
        const updated = await adminApi.updateExam(examId, data)
        set(state => ({
            exams: state.exams.map(ex => ex.id === examId ? updated : ex)
        }))
        return updated
    },

    // ── Create Test (Event) ───────────────────────────────────────────────────
    createTestLoading: false,
    createTestError: null,

    createTest: async (data) => {
        set({ createTestLoading: true, createTestError: null })
        try {
            const result = await adminApi.createEvent(data)
            set({ createTestLoading: false })
            // Re-fetch exams so the new ones show in the publisher
            get().fetchAllExams()
            return result
        } catch (e) {
            set({ createTestError: e.response?.data?.detail || 'Failed to create test', createTestLoading: false })
            throw e
        }
    },

    // ── Boards (for CreateTestPage) ───────────────────────────────────────────
    boards: [],
    boardsLoading: false,

    fetchBoards: async () => {
        if (get().boards.length > 0) return // already loaded
        set({ boardsLoading: true })
        try {
            const boards = await adminApi.listBoards()
            set({ boards, boardsLoading: false })
        } catch (e) {
            set({ boardsLoading: false })
        }
    },

    // ── Questions ─────────────────────────────────────────────────────────────
    questions: [],
    selectedExamId: null,
    questionsLoading: false,
    questionsError: null,

    fetchQuestions: async (examId) => {
        set({ questionsLoading: true, questionsError: null, selectedExamId: examId })
        try {
            const questions = await adminApi.listQuestionsAdmin(examId)
            set({ questions, questionsLoading: false })
        } catch (e) {
            set({ questionsError: e.response?.data?.detail || 'Failed to load questions', questionsLoading: false })
        }
    },

    updateQuestion: async (questionId, data) => {
        const updated = await adminApi.updateQuestion(questionId, data)
        set(state => ({
            questions: state.questions.map(q => q.id === questionId ? updated : q)
        }))
        return updated
    },

    deleteQuestion: async (questionId) => {
        await adminApi.deleteQuestion(questionId)
        set(state => ({
            questions: state.questions.filter(q => q.id !== questionId)
        }))
    },

    bulkImportResult: null,
    bulkImporting: false,

    runBulkImport: async (payload) => {
        set({ bulkImporting: true, bulkImportResult: null })
        try {
            const result = await adminApi.bulkImport(payload)
            set({ bulkImportResult: result, bulkImporting: false })
            // Refresh questions list if same exam
            if (get().selectedExamId === payload.exam_id) {
                await get().fetchQuestions(payload.exam_id)
            }
            return result
        } catch (e) {
            set({ bulkImporting: false })
            throw e
        }
    },

    // ── Question stats ────────────────────────────────────────────────────────
    questionStats: [],
    statsLoading: false,
    statsError: null,
    statsExamId: null,

    fetchQuestionStats: async (examId) => {
        set({ statsLoading: true, statsError: null, statsExamId: examId })
        try {
            const questionStats = await adminApi.getQuestionStats(examId)
            set({ questionStats, statsLoading: false })
        } catch (e) {
            set({ statsError: e.response?.data?.detail || 'Failed to load stats', statsLoading: false })
        }
    },

    // ── Reset ─────────────────────────────────────────────────────────────────
    reset: () => set({
        overview: null, recentAttempts: [], overviewLoading: false, overviewError: null,
        exams: [], examsLoading: false, examsError: null,
        questions: [], selectedExamId: null, questionsLoading: false, questionsError: null,
        bulkImportResult: null, bulkImporting: false,
        questionStats: [], statsLoading: false, statsError: null, statsExamId: null,
        boards: [], boardsLoading: false,
        createTestLoading: false, createTestError: null,
    }),
}))
