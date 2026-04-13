import { useState } from 'react'
import { QuestionBrowser } from '../components/QuestionBrowser'
import { QuestionCreatorForm } from '../components/QuestionCreatorForm'
import { QuestionImporter } from '../components/QuestionImporter'

const TABS = [
    {
        id: 'browse',
        label: 'Browse Questions',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
        ),
    },
    {
        id: 'add',
        label: 'Add Question',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 4v16m8-8H4" />
            </svg>
        ),
    },
    {
        id: 'import',
        label: 'Import',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
        ),
    },
]

/**
 * QuestionManagerPage — tabbed admin page for managing questions.
 *
 * Tabs:
 *   Browse   — search, filter, edit, and delete questions
 *   Add      — form UI for creating a single question (no JSON needed)
 *   Import   — JSON and CSV bulk import with validation preview
 */
export function QuestionManagerPage() {
    const [activeTab, setActiveTab] = useState('browse')

    return (
        <div className="p-4 sm:p-8 max-w-7xl mx-auto pb-24">
            {/* Page header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">Question Manager</h1>
                <p className="text-surface-500 mt-1">
                    Browse, edit, and import exam questions. Correct answers are visible to admin.
                </p>
            </div>

            {/* Tab strip */}
            <div className="flex gap-1 bg-surface-100 p-1 rounded-xl mb-6 w-fit">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                            activeTab === tab.id
                                ? 'bg-white text-surface-900 shadow-sm'
                                : 'text-surface-500 hover:text-surface-700'
                        }`}
                    >
                        {tab.icon}
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab content */}
            {activeTab === 'browse' && <QuestionBrowser />}
            {activeTab === 'add' && (
                <QuestionCreatorForm onSuccess={() => setActiveTab('browse')} />
            )}
            {activeTab === 'import' && <QuestionImporter />}
        </div>
    )
}
