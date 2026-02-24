import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

import { useAnalysisStore } from '../store/analysisStore';
import { useAuthStore } from '@/modules/auth';
import { ScoreSummaryCard } from '../components/ScoreSummaryCard';
import { SectionBreakdown } from '../components/SectionBreakdown';
import { TopicPerformanceGrid } from '../components/TopicPerformanceGrid';
import { TimeAnalysisCard } from '../components/TimeAnalysisCard';
import { RecommendationsList } from '../components/RecommendationsList';
import { ReportCardPDF } from '../components/ReportCardPDF';

export const ResultPage = () => {
    const { attemptId } = useParams();
    const navigate = useNavigate();
    const { t } = useTranslation();

    const { report, isLoading, error, fetchReport, reset } = useAnalysisStore();
    const { user } = useAuthStore();

    const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
    const pdfRef = useRef(null);

    useEffect(() => {
        if (attemptId) {
            fetchReport(attemptId);
        }
        return () => reset();
    }, [attemptId, fetchReport, reset]);

    const handleDownloadPDF = async () => {
        if (!pdfRef.current || isGeneratingPDF) return;

        setIsGeneratingPDF(true);
        try {
            // Small timeout to ensure DOM is ready and styled
            await new Promise(r => setTimeout(r, 100));

            const element = pdfRef.current;
            const canvas = await html2canvas(element, {
                scale: 2, // Higher density for better text rendering
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff'
            });

            const imgData = canvas.toDataURL('image/png');

            // A4 portrait dimensions
            const pdf = new jsPDF({
                orientation: 'portrait',
                unit: 'mm',
                format: 'a4'
            });

            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

            pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);

            const dateStr = new Date().toISOString().split('T')[0];
            pdf.save(`ScholarPath_Report_${dateStr}.pdf`);
        } catch (err) {
            console.error('Error generating PDF:', err);
            // In a real app we'd probably want to show a toast error here
        } finally {
            setIsGeneratingPDF(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500 mx-auto mb-4">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <h2 className="text-xl font-bold text-red-800 mb-2">{t('analysis.errorLoading', 'Error Loading Report')}</h2>
                    <p className="text-red-600 mb-6">{error}</p>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition"
                    >
                        {t('common.backToDashboard', 'Back to Dashboard')}
                    </button>
                </div>
            </div>
        );
    }

    if (!report) return null;

    return (
        <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 pb-24">

            {/* Header Actions */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                <div>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="text-slate-500 hover:text-slate-800 flex items-center gap-2 mb-2 transition"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="19" y1="12" x2="5" y2="12"></line>
                            <polyline points="12 19 5 12 12 5"></polyline>
                        </svg>
                        {t('common.backToDashboard', 'Back to Dashboard')}
                    </button>
                    <h1 className="text-3xl font-black text-slate-800 tracking-tight">
                        {t('analysis.examResult', 'Exam Result')}
                    </h1>
                </div>

                <button
                    onClick={handleDownloadPDF}
                    disabled={isGeneratingPDF}
                    className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    {isGeneratingPDF ? (
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    )}
                    {t('analysis.downloadPdf', 'Download PDF')}
                </button>
            </div>

            {/* Main Content Dashboard */}
            <div className="space-y-6">
                <ScoreSummaryCard report={report} />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-1">
                        <SectionBreakdown sections={report.section_scores} />
                    </div>
                    <div className="lg:col-span-2">
                        <TopicPerformanceGrid topics={report.topic_scores} />
                    </div>
                </div>

                <TimeAnalysisCard timeAnalysis={report.time_analysis} />

                <RecommendationsList recommendations={report.recommendations} />
            </div>

            {/* Hidden PDF Canvas rendering area */}
            <div className="fixed overflow-hidden pointer-events-none" style={{ left: '-9999px', top: 0 }}>
                <ReportCardPDF
                    ref={pdfRef}
                    report={report}
                    studentInfo={user}
                    examInfo={{ title_en: "Mock Exam Title", medium: user?.medium || 'English' }} // We'd ideally fetch real exam details from catalog
                />
            </div>

        </div>
    );
};
