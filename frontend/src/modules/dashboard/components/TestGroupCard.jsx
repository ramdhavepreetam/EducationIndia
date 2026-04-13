import { PaperRow } from './PaperRow'
import { useTranslation } from 'react-i18next'

/**
 * TestGroupCard — groups a set of exam papers under a single test event header.
 *
 * The dashboard backend returns a flat list of exams. The parent groups them
 * by event_id (or a derived key) and passes each cluster to this component.
 *
 * Props:
 *   eventTitle    — displayed as the card heading (e.g. "MSCE 2024 — Class 5")
 *   year          — optional year badge
 *   stdClass      — optional class badge (5 or 8)
 *   exams         — array of ExamSummaryResponse / ExamAccessResponse
 */
export const TestGroupCard = ({ eventTitle, year, stdClass, exams = [] }) => {
    const { t } = useTranslation()

    const allLive = exams.every(e => e.is_accessible !== false)
    const anyLocked = exams.some(e => e.is_accessible === false)

    return (
        <div className="bg-white rounded-2xl border border-surface-100 shadow-sm overflow-hidden">
            {/* Card header */}
            <div className="flex items-start justify-between px-5 py-4 border-b border-surface-100 bg-gradient-to-r from-surface-50 to-white">
                <div>
                    <h3 className="font-bold text-surface-800 text-base leading-tight">
                        {eventTitle}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                        {year && (
                            <span className="text-xs text-surface-400 font-medium">
                                {year}
                            </span>
                        )}
                        {stdClass && (
                            <span className="text-xs px-2 py-0.5 bg-brand-50 text-brand-700 rounded-full font-semibold border border-brand-100">
                                {t('dashboard.class', 'Class')} {stdClass}
                            </span>
                        )}
                    </div>
                </div>

                {/* Status chip */}
                {anyLocked ? (
                    <span className="flex-shrink-0 text-xs px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                        🔒 {t('dashboard.locked', 'Locked')}
                    </span>
                ) : (
                    <span className="flex-shrink-0 text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-100 font-medium">
                        ✓ {t('dashboard.available', 'Available')}
                    </span>
                )}
            </div>

            {/* Paper rows */}
            <div className="divide-y divide-surface-50 px-1 py-1">
                {exams.map((exam) => (
                    <PaperRow key={exam.id} exam={exam} />
                ))}
                {exams.length === 0 && (
                    <p className="text-sm text-surface-400 text-center py-5">
                        {t('dashboard.noPapers', 'No papers in this test set.')}
                    </p>
                )}
            </div>
        </div>
    )
}
