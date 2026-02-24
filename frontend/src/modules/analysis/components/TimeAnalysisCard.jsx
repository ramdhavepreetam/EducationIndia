import React from 'react';
import { useTranslation } from 'react-i18next';

export const TimeAnalysisCard = ({ timeAnalysis }) => {
    const { t } = useTranslation();

    if (!timeAnalysis) return null;

    const formatSeconds = (seconds) => {
        if (!seconds && seconds !== 0) return '-';
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return m > 0 ? `${m}m ${s}s` : `${s}s`;
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                {t('analysis.timeAnalysis', 'Time Analysis')}
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-100 flex flex-col items-center justify-center text-center">
                    <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-1">
                        {t('analysis.totalTime', 'Total Time')}
                    </span>
                    <span className="text-xl font-bold text-indigo-900">
                        {formatSeconds(timeAnalysis.total_time_seconds)}
                    </span>
                </div>

                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-col items-center justify-center text-center">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                        {t('analysis.avgTime', 'Average Time')}
                    </span>
                    <span className="text-xl font-bold text-slate-800">
                        {formatSeconds(timeAnalysis.avg_per_question)}
                    </span>
                </div>

                <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-100 flex flex-col items-center justify-center text-center">
                    <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">
                        {t('analysis.fastest', 'Fastest')}
                    </span>
                    {timeAnalysis.fastest ? (
                        <div className="flex flex-col items-center">
                            <span className="text-lg font-bold text-emerald-900">{timeAnalysis.fastest.seconds}s</span>
                            <span className="text-xs text-emerald-700">Q{timeAnalysis.fastest.question_no}</span>
                        </div>
                    ) : (
                        <span className="text-lg font-bold text-emerald-900">-</span>
                    )}
                </div>

                <div className="p-4 rounded-lg bg-amber-50 border border-amber-100 flex flex-col items-center justify-center text-center">
                    <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-1">
                        {t('analysis.slowest', 'Slowest')}
                    </span>
                    {timeAnalysis.slowest ? (
                        <div className="flex flex-col items-center">
                            <span className="text-lg font-bold text-amber-900">
                                {formatSeconds(timeAnalysis.slowest.seconds)}
                            </span>
                            <span className="text-xs text-amber-700">Q{timeAnalysis.slowest.question_no}</span>
                        </div>
                    ) : (
                        <span className="text-lg font-bold text-amber-900">-</span>
                    )}
                </div>
            </div>

            {timeAnalysis.overtime_questions?.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 rounded-lg text-sm text-red-800 border border-red-100 flex items-start gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500 mt-0.5 shrink-0">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <div>
                        <span className="font-semibold block mb-1">
                            {t('analysis.overtimeWarning', 'Significant time spent on specific questions:')}
                        </span>
                        <span className="text-red-700">
                            {t('analysis.questionsList', 'Questions')}: {timeAnalysis.overtime_questions.join(', ')}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
};
