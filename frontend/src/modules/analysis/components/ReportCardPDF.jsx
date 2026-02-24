import React, { forwardRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/modules/auth';

/**
 * PDF Template Component
 * This component is rendered off-screen and captured via html2canvas
 */
export const ReportCardPDF = forwardRef(({ report, studentInfo, examInfo }, ref) => {
    const { t } = useTranslation();
    const { user } = useAuthStore();
    const currentLang = user?.preferred_language || 'en';

    if (!report) return null;

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const d = new Date(dateString);
        return isNaN(d) ? '' : d.toLocaleDateString();
    };

    // Weak topics for summary
    const weakTopics = report.topic_scores?.filter((t) => t.status === 'weak') || [];

    return (
        <div
            ref={ref}
            className="bg-white text-slate-900 w-[800px] min-h-[1100px] p-10 flex flex-col relative printable-report"
            style={{
                fontFamily: "'Inter', sans-serif"
            }}
        >
            {/* Header */}
            <div className="flex justify-between items-start border-b-2 border-slate-800 pb-6 items-center">
                <div>
                    <h1 className="text-3xl font-black text-blue-900 tracking-tight m-0">ScholarPath</h1>
                    <p className="text-slate-500 text-sm mt-1">{t('analysis.pdfSub', 'Scholarship Exam Report Card')}</p>
                </div>
                <div className="text-right">
                    <div className="text-sm text-slate-500 mb-1">{t('analysis.examDate', 'Exam Date')}: {formatDate(report.started_at)}</div>
                    <div className="text-sm text-slate-500">ID: {report.attempt_id?.substring(0, 8)}</div>
                </div>
            </div>

            {/* Info Grid */}
            <div className="grid grid-cols-2 gap-8 mt-6">
                <div className="bg-slate-50 p-4 rounded border border-slate-200">
                    <h2 className="text-xs uppercase tracking-wider font-bold text-slate-400 mb-2">{t('analysis.studentDetails', 'Student Details')}</h2>
                    <div className="font-bold text-lg mb-1">{studentInfo?.full_name || 'Student Name'}</div>
                    <div className="text-sm text-slate-600 mb-1">Std {studentInfo?.std_class || 'N/A'}</div>
                    <div className="text-sm text-slate-500">{studentInfo?.school_name || 'School Name Not Provided'}</div>
                </div>
                <div className="bg-slate-50 p-4 rounded border border-slate-200">
                    <h2 className="text-xs uppercase tracking-wider font-bold text-slate-400 mb-2">{t('analysis.examDetails', 'Exam Details')}</h2>
                    <div className="font-bold text-lg mb-1">{examInfo?.title_en || 'Exam Title'}</div>
                    <div className="text-sm text-slate-600 mb-1">{examInfo?.paper_code || 'Paper'}</div>
                    <div className="text-sm text-slate-500">Medium: {examInfo?.medium || 'English'}</div>
                </div>
            </div>

            {/* Main Score Area */}
            <div className="mt-8 flex justify-center py-8 bg-blue-50 border border-blue-100 rounded-lg">
                <div className="text-center px-12 border-r border-blue-200">
                    <div className="text-sm font-bold text-blue-600 tracking-wider uppercase mb-2">{t('analysis.totalScore', 'Total Score')}</div>
                    <div className="text-6xl font-black text-slate-900 tracking-tighter">
                        {report.total_score}<span className="text-3xl text-slate-400">/150</span>
                    </div>
                </div>
                <div className="text-center px-12 border-r border-blue-200">
                    <div className="text-sm font-bold text-blue-600 tracking-wider uppercase mb-2">{t('analysis.percentage', 'Percentage')}</div>
                    <div className="text-5xl font-black text-slate-800 tracking-tighter mt-1">{report.percentage}%</div>
                </div>
                <div className="text-center px-12">
                    <div className="text-sm font-bold text-blue-600 tracking-wider uppercase mb-2">{t('analysis.grade', 'Grade')}</div>
                    <div className="text-4xl font-black text-blue-700 tracking-tight mt-2 uppercase">{report.grade}</div>
                </div>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-8">
                {/* Sections */}
                <div>
                    <h3 className="text-lg font-bold border-b border-slate-200 pb-2 mb-4">{t('analysis.sectionPerformance', 'Section Performance')}</h3>
                    <div className="space-y-4">
                        {report.section_scores?.map((s) => {
                            const subjectName = currentLang === 'mr' && s.subject_mr ? s.subject_mr : s.subject_en;
                            return (
                                <div key={s.section_id}>
                                    <div className="flex justify-between text-sm font-bold mb-1">
                                        <span>{subjectName}</span>
                                        <span>{s.percentage}% ({s.score}/{s.total_marks})</span>
                                    </div>
                                    <div className="w-full bg-slate-200 h-2 rounded-full hidden-print-bg">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full"
                                            style={{ width: `${Math.max(s.percentage, 2)}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Stats Summary */}
                <div>
                    <h3 className="text-lg font-bold border-b border-slate-200 pb-2 mb-4">{t('analysis.summary', 'Summary')}</h3>
                    <table className="w-full text-sm">
                        <tbody>
                            <tr className="border-b border-slate-100">
                                <td className="py-2 text-slate-500">{t('analysis.correct', 'Correct')}</td>
                                <td className="py-2 font-bold text-right text-green-700">{report.total_correct}</td>
                            </tr>
                            <tr className="border-b border-slate-100">
                                <td className="py-2 text-slate-500">{t('analysis.wrong', 'Wrong')}</td>
                                <td className="py-2 font-bold text-right text-red-700">{report.total_wrong}</td>
                            </tr>
                            <tr className="border-b border-slate-100">
                                <td className="py-2 text-slate-500">{t('analysis.skipped', 'Skipped')}</td>
                                <td className="py-2 font-bold text-right text-slate-700">{report.total_skipped}</td>
                            </tr>
                            <tr className="border-b border-slate-100">
                                <td className="py-2 text-slate-500">{t('analysis.avgTime', 'Average Time')}</td>
                                <td className="py-2 font-bold text-right">
                                    {report.time_analysis?.avg_per_question
                                        ? `${Math.round(report.time_analysis.avg_per_question)}s / q`
                                        : 'N/A'}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Weak Topics */}
            {weakTopics.length > 0 && (
                <div className="mt-8">
                    <h3 className="text-lg font-bold border-b border-slate-200 pb-2 mb-4 text-red-700">
                        {t('analysis.weakTopics', 'Topics Needing Attention')}
                    </h3>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                        {weakTopics.map(tData => {
                            const tName = currentLang === 'mr' && tData.name_mr ? tData.name_mr : tData.name_en;
                            return (
                                <div key={tData.topic_id} className="flex justify-between py-1 border-b border-slate-100">
                                    <span className="text-slate-700 truncate pr-2">{tName}</span>
                                    <span className="font-bold text-red-700 whitespace-nowrap">{tData.percentage}% ({tData.correct}/{tData.total})</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Recommendations */}
            {report.recommendations && report.recommendations.length > 0 && (
                <div className="mt-8">
                    <h3 className="text-lg font-bold border-b border-slate-200 pb-2 mb-4">
                        {t('analysis.recommendations', 'Areas for Improvement')}
                    </h3>
                    <ul className="text-sm space-y-2 text-slate-700 list-disc pl-5">
                        {report.recommendations.map((r, i) => (
                            <li key={i}>{r}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Footer */}
            <div className="mt-auto pt-8 border-t border-slate-200 text-center text-xs text-slate-400">
                Generated by ScholarPath • {new Date().toLocaleDateString()} • This is a computer-generated report.
            </div>
        </div>
    );
});

ReportCardPDF.displayName = 'ReportCardPDF';
