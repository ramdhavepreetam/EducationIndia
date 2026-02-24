import { create } from 'zustand'
import { attemptApi } from '../api/attemptApi'

export const useAttemptStore = create((set, get) => ({
    // State shape
    currentAttempt: null,
    questions: [],
    responses: {}, // { [questionNo]: { selectedOption, isMarkedReview, visitCount, questionId } }
    currentQuestionNo: 1,
    timeRemaining: null,
    isLoading: false,
    isSaving: false,
    error: null,
    isSubmitting: false,

    // Actions
    setSavingState: (isSaving) => set({ isSaving }),

    startExam: async (examId) => {
        set({ isLoading: true, error: null })
        try {
            // Fetch questions (metadata/content)
            const examData = await attemptApi.getQuestions(examId)
            const deliveryQuestions = await attemptApi.getExamDeliveryQuestions(examId)

            // Start attempt
            const attempt = await attemptApi.start(examId)

            set({
                currentAttempt: attempt,
                questions: deliveryQuestions || examData.questions || [],
                responses: {},
                currentQuestionNo: 1,
                timeRemaining: attempt.time_remaining_seconds,
                isLoading: false
            })

            // Mark question 1 as visited
            if (deliveryQuestions?.length > 0 || examData?.questions?.length > 0) {
                get().navigateTo(1)
            }
        } catch (err) {
            if (err.response?.status === 409) {
                // If an ongoing attempt exists (409 Conflict), find it and resume it automatically
                try {
                    const list = await attemptApi.listAttempts(examId)
                    const ongoing = list.find(a => a.status === 'ongoing')
                    if (ongoing) {
                        await get().resumeExam(ongoing.attempt_id, examId)
                        return // Store will be populated by resumeExam
                    }
                } catch (resumeErr) {
                    set({ error: resumeErr.message || 'Failed to resume ongoing exam', isLoading: false })
                    throw resumeErr
                }
            }
            // Otherwise it's a real error
            const detail = err.response?.data?.detail ? JSON.stringify(err.response.data.detail) : err.message
            set({ error: detail || 'Failed to start exam', isLoading: false })
            throw err
        }
    },

    resumeExam: async (attemptId, examId) => {
        set({ isLoading: true, error: null })
        try {
            const deliveryQuestions = await attemptApi.getExamDeliveryQuestions(examId)
            const state = await attemptApi.getState(attemptId)

            // Reconstruct responses dictionary from array
            const responsesMap = {}
            if (state.responses) {
                state.responses.forEach(r => {
                    responsesMap[r.question_no] = {
                        selectedOption: r.selected_option,
                        isMarkedReview: r.is_marked_review,
                        visitCount: r.visit_count,
                        questionId: r.question_id
                    }
                })
            }

            set({
                currentAttempt: state,
                questions: deliveryQuestions,
                responses: responsesMap,
                timeRemaining: state.time_remaining_seconds,
                currentQuestionNo: 1, // Start at 1 or maybe find first unanswered
                isLoading: false
            })

            // Mark question 1 as visited if we haven't already
            if (!responsesMap[1] || !responsesMap[1].visitCount) {
                get().navigateTo(1)
            }

        } catch (err) {
            const detail = err.response?.data?.detail ? JSON.stringify(err.response.data.detail) : err.message
            set({ error: detail || 'Failed to resume exam state', isLoading: false })
            throw err
        }
    },

    selectOption: (questionNo, questionId, selectedOption) => {
        // Optimistic update
        set(state => {
            const existing = state.responses[questionNo] || {}
            return {
                responses: {
                    ...state.responses,
                    [questionNo]: {
                        ...existing,
                        selectedOption,
                        questionId
                    }
                }
            }
        })
    },

    toggleMarkReview: (questionNo, questionId) => {
        set(state => {
            const existing = state.responses[questionNo] || {}
            return {
                responses: {
                    ...state.responses,
                    [questionNo]: {
                        ...existing,
                        isMarkedReview: !existing.isMarkedReview,
                        questionId
                    }
                }
            }
        })
    },

    navigateTo: (questionNo) => {
        set(state => {
            const existing = state.responses[questionNo] || {}
            return {
                currentQuestionNo: questionNo,
                responses: {
                    ...state.responses,
                    [questionNo]: {
                        ...existing,
                        // Increment visit count immediately on client
                        visitCount: (existing.visitCount || 0) + 1
                    }
                }
            }
        })
    },

    setTimeRemaining: (seconds) => {
        set({ timeRemaining: seconds })
    },

    autoExpire: async () => {
        const { currentAttempt, submitExam } = get()
        if (currentAttempt) {
            console.log("Timer expired! Auto-submitting...")
            if (currentAttempt.id) {
                await submitExam(currentAttempt.id)
            }
        }
    },

    submitExam: async (attemptId) => {
        set({ isSubmitting: true, error: null })
        try {
            const result = await attemptApi.submit(attemptId)
            set({ isSubmitting: false })
            return result
        } catch (err) {
            set({ error: err.message || 'Failed to submit exam', isSubmitting: false })
            throw err
        }
    },

    reset: () => {
        set({
            currentAttempt: null,
            questions: [],
            responses: {},
            currentQuestionNo: 1,
            timeRemaining: null,
            isLoading: false,
            isSaving: false,
            error: null,
            isSubmitting: false
        })
    }
}))
