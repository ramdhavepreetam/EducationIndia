import { create } from 'zustand'
import { teacherApi } from '../api/teacherApi'

export const useTeacherStore = create((set, get) => ({
    // Dashboard
    dashboard: null,
    isDashboardLoading: false,

    // Students list
    students: [],
    studentsPage: 1,
    studentsHasMore: false,
    isStudentsLoading: false,

    // Selected student detail
    selectedStudent: null,
    isDetailLoading: false,

    // Lookup (assign flow)
    lookupResult: null,
    isLookingUp: false,

    // Assignment
    isAssigning: false,
    assignSuccess: null,

    error: null,

    loadDashboard: async () => {
        set({ isDashboardLoading: true, error: null })
        try {
            const data = await teacherApi.getDashboard()
            set({ dashboard: data })
        } catch (e) {
            set({ error: e.response?.data?.detail || 'Failed to load dashboard' })
        } finally {
            set({ isDashboardLoading: false })
        }
    },

    loadStudents: async (params = {}) => {
        set({ isStudentsLoading: true, error: null })
        try {
            const data = await teacherApi.listStudents({ page: 1, page_size: 20, ...params })
            set({
                students: data.items,
                studentsPage: data.page,
                studentsHasMore: data.has_more,
            })
        } catch (e) {
            set({ error: e.response?.data?.detail || 'Failed to load students' })
        } finally {
            set({ isStudentsLoading: false })
        }
    },

    loadStudentDetail: async (studentId) => {
        set({ isDetailLoading: true, error: null, selectedStudent: null })
        try {
            const data = await teacherApi.getStudentDetail(studentId)
            set({ selectedStudent: data })
        } catch (e) {
            set({ error: e.response?.data?.detail || 'Failed to load student' })
        } finally {
            set({ isDetailLoading: false })
        }
    },

    lookupStudent: async (email) => {
        set({ isLookingUp: true, lookupResult: null, error: null })
        try {
            const data = await teacherApi.lookupStudentByEmail(email)
            set({ lookupResult: data })
            return data
        } catch (e) {
            const msg = e.response?.data?.detail || 'Student not found'
            set({ error: msg })
            return null
        } finally {
            set({ isLookingUp: false })
        }
    },

    assignExam: async (payload) => {
        set({ isAssigning: true, assignSuccess: null, error: null })
        try {
            const data = await teacherApi.assignExam(payload)
            set({ assignSuccess: data })
            // Refresh dashboard stats
            get().loadDashboard()
            return data
        } catch (e) {
            const msg = e.response?.data?.detail || 'Failed to assign exam'
            set({ error: msg })
            return null
        } finally {
            set({ isAssigning: false })
        }
    },

    clearError: () => set({ error: null }),
    clearAssignSuccess: () => set({ assignSuccess: null, lookupResult: null }),

    reset: () => set({
        dashboard: null,
        isDashboardLoading: false,
        students: [],
        studentsPage: 1,
        studentsHasMore: false,
        isStudentsLoading: false,
        selectedStudent: null,
        isDetailLoading: false,
        lookupResult: null,
        isLookingUp: false,
        isAssigning: false,
        assignSuccess: null,
        error: null,
    }),
}))
