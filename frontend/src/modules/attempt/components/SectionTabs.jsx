import React from 'react'

export default function SectionTabs({ sections, activeSectionId, onTabChange }) {
    if (!sections || sections.length === 0) return null

    return (
        <div className="flex w-full mb-4 space-x-1 bg-surface-100 p-1 rounded-lg">
            {sections.map(section => {
                const isActive = activeSectionId === section.id
                return (
                    <button
                        key={section.id}
                        onClick={() => onTabChange(section.id)}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${isActive
                                ? 'bg-white text-brand-700 shadow-sm ring-1 ring-black ring-opacity-5'
                                : 'text-surface-600 hover:text-surface-900 hover:bg-surface-200'
                            }`}
                    >
                        {section.label}
                    </button>
                )
            })}
        </div>
    )
}
