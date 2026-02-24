import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/modules/auth';

export const TopicPerformanceGrid = ({ topics }) => {
    const { t } = useTranslation();
    const { user } = useAuthStore();
    const currentLang = user?.preferred_language || 'en';

    if (!topics || topics.length === 0) return null;

    // Separate topics by status for optional sorting (weak first)
    const sortedTopics = [...topics].sort((a, b) => {
        const statusOrder = { weak: 1, average: 2, strong: 3 };
        return statusOrder[a.status] - statusOrder[b.status];
    });

    const getStatusColor = (status) => {
        switch (status) {
            case 'strong': return 'bg-green-100 text-green-800 border-green-200';
            case 'average': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'weak': return 'bg-red-100 text-red-800 border-red-200';
            default: return 'bg-slate-100 text-slate-800 border-slate-200';
        }
    };

    const getDotColor = (status) => {
        switch (status) {
            case 'strong': return 'bg-green-500';
            case 'average': return 'bg-yellow-500';
            case 'weak': return 'bg-red-500';
            default: return 'bg-slate-500';
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-500">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                    </svg>
                    {t('analysis.topicPerformance', 'Topic Performance')}
                </h3>

                {/* Legend */}
                <div className="hidden sm:flex items-center gap-4 text-xs font-medium text-slate-500">
                    <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-green-500"></div> {t('analysis.status.strong', 'Strong')}</div>
                    <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div> {t('analysis.status.average', 'Average')}</div>
                    <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-red-500"></div> {t('analysis.status.weak', 'Weak')}</div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sortedTopics.map((topic) => {
                    const topicName = currentLang === 'mr' && topic.name_mr
                        ? topic.name_mr
                        : topic.name_en;

                    return (
                        <div key={topic.topic_id} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-slate-100 transition-colors">
                            <div className="flex-1 truncate pr-4">
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${getDotColor(topic.status)}`}></div>
                                    <span className="font-medium text-slate-700 truncate" title={topicName}>{topicName}</span>
                                </div>
                            </div>

                            <div className="flex items-center gap-3 flex-shrink-0">
                                <div className="text-xs text-slate-500 w-12 text-right">
                                    {topic.correct}/{topic.total}
                                </div>
                                <div className="font-bold text-slate-700 w-12 text-right">
                                    {topic.percentage}%
                                </div>
                                <div className={`text-[10px] w-16 text-center uppercase tracking-wider font-bold py-1 px-2 rounded border ${getStatusColor(topic.status)}`}>
                                    {t(`analysis.status.${topic.status}`, topic.status)}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
