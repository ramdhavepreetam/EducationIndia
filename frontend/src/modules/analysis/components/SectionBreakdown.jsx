import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/modules/auth';

export const SectionBreakdown = ({ sections }) => {
    const { t } = useTranslation();
    const { user } = useAuthStore();
    const currentLang = user?.preferred_language || 'en';

    if (!sections || sections.length === 0) return null;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
                {t('analysis.sectionPerformance', 'Section Performance')}
            </h3>

            <div className="space-y-6">
                {sections.map((section) => {
                    // Choose subject name based on language
                    const subjectName = currentLang === 'mr' && section.subject_mr
                        ? section.subject_mr
                        : section.subject_en;

                    return (
                        <div key={section.section_id} className="space-y-2">
                            <div className="flex justify-between items-end">
                                <div>
                                    <span className="font-semibold text-slate-700 mr-2">
                                        {t('analysis.section', 'Section')} {section.label}:
                                    </span>
                                    <span className="text-slate-600">{subjectName}</span>
                                </div>
                                <div className="text-right">
                                    <span className="font-bold text-slate-800">{section.percentage}%</span>
                                    <span className="text-xs text-slate-500 ml-2">
                                        ({section.score} / {section.total_marks} {t('analysis.marks', 'marks')})
                                    </span>
                                </div>
                            </div>

                            {/* Progress Bar background */}
                            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
                                {/* Progress Bar fill */}
                                <div
                                    className={`h-full rounded-full transition-all duration-1000 ease-out ${section.percentage >= 75 ? 'bg-green-500' :
                                            section.percentage >= 50 ? 'bg-blue-500' :
                                                section.percentage >= 35 ? 'bg-yellow-500' : 'bg-red-500'
                                        }`}
                                    style={{ width: `${Math.max(section.percentage, 2)}%` }}
                                ></div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
