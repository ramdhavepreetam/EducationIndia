import { create } from 'zustand';
import { analysisApi } from '../api/analysisApi';

export const useAnalysisStore = create((set, get) => ({
    report: null,
    isLoading: false,
    error: null,

    fetchReport: async (attemptId) => {
        set({ isLoading: true, error: null });
        try {
            const data = await analysisApi.getAttemptReport(attemptId);
            set({ report: data, isLoading: false });
            return data;
        } catch (err) {
            const message = err.response?.data?.detail || 'Failed to fetch analysis report';
            set({ error: message, isLoading: false });
            throw err;
        }
    },

    reset: () => {
        set({ report: null, isLoading: false, error: null });
    }
}));
