import apiClient from '@/config/apiClient';

export const analysisApi = {
    /**
     * Fetch the full analysis report for a submitted attempt.
     * @param {string} attemptId - UUID of the attempt
     * @returns {Promise<Object>} The report data
     */
    getAttemptReport: async (attemptId) => {
        const response = await apiClient.get(`/analysis/attempts/${attemptId}/report`);
        return response.data;
    }
};
