import React from 'react';
import { useTranslation } from 'react-i18next';

export const ScoreSummaryCard = ({ report }) => {
    const { t } = useTranslation();

    if (!report) return null;

    // Grade color mapping
    const getGradeColor = (grade) => {
        switch (grade) {
            case 'Excellent': return 'text-green-600 bg-green-50 border-green-200';
            case 'Good': return 'text-blue-600 bg-blue-50 border-blue-200';
            case 'Average': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
            default: return 'text-red-600 bg-red-50 border-red-200';
        }
    };

    const gradeColorClass = getGradeColor(report.grade);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col md:flex-row items-center justify-between gap-6">

            {/* Left side: Score and Grade */}
            <div className="flex flex-col items-center md:items-start text-center md:text-left space-y-2">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
                    {t('analysis.overallScore', 'Overall Score')}
                </h2>
                <div className="text-4xl md:text-5xl font-bold text-slate-800">
                    {report.total_score} <span className="text-2xl text-slate-400">/ 150</span>
                </div>
                <div className="flex items-center gap-3 mt-2">
                    <span className="text-lg font-medium text-slate-700">{report.percentage}%</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${gradeColorClass}`}>
                        {t(`analysis.grades.${report.grade}`, report.grade)}
                    </span>
                </div>
            </div>

            {/* Right side: Breakdown Stats */}
            <div className="flex gap-4 md:gap-8 w-full md:w-auto">
                <div className="flex-1 bg-green-50 rounded-lg p-4 text-center border border-green-100">
                    <div className="text-green-600 text-sm font-medium mb-1">{t('analysis.correct', 'Correct')}</div>
                    <div className="text-2xl font-bold text-green-700">{report.total_correct}</div>
                </div>

                <div className="flex-1 bg-red-50 rounded-lg p-4 text-center border border-red-100">
                    <div className="text-red-600 text-sm font-medium mb-1">{t('analysis.wrong', 'Wrong')}</div>
                    <div className="text-2xl font-bold text-red-700">{report.total_wrong}</div>
                </div>

                <div className="flex-1 bg-slate-50 rounded-lg p-4 text-center border border-slate-200">
                    <div className="text-slate-500 text-sm font-medium mb-1">{t('analysis.skipped', 'Skipped')}</div>
                    <div className="text-2xl font-bold text-slate-700">{report.total_skipped}</div>
                </div>
            </div>

        </div>
    );
};
