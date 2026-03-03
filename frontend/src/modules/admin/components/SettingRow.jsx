import React, { useState, useEffect } from 'react'

export const SettingRow = ({ setting, onSave, isSaving }) => {
    const [value, setValue] = useState(setting.value)
    const isChanged = value !== setting.value

    // Synchronize local state if parent re-fetches
    useEffect(() => {
        setValue(setting.value)
    }, [setting.value])

    const handleSave = () => {
        if (isChanged && !isSaving) {
            onSave(setting.key, value)
        }
    }

    const renderInput = () => {
        if (setting.type === 'boolean') {
            const isChecked = value === 'true' || value === '1'
            return (
                <label className="relative inline-flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={isChecked}
                        onChange={(e) => {
                            const newValue = e.target.checked ? 'true' : 'false'
                            setValue(newValue)
                            // Auto-save booleans as requested: "Maintenance Mode [toggle] (auto-saves)"
                            onSave(setting.key, newValue)
                        }}
                        disabled={isSaving}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
            )
        }

        if (setting.type === 'int') {
            return (
                <input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    disabled={isSaving}
                    className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                />
            )
        }

        // Default string
        return (
            <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={isSaving}
                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
            />
        )
    }

    const dateStr = setting.updated_at ? new Date(setting.updated_at).toLocaleString() : 'Never'

    return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between py-4 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors px-4 -mx-4 rounded-lg">
            <div className="mb-4 sm:mb-0 flex-1 pr-4">
                <label className="text-sm font-medium text-gray-900 block mb-1">
                    {setting.label || setting.key}
                </label>
                <p className="text-xs text-gray-500 font-mono">{setting.key}</p>
                <p className="text-xs text-gray-400 mt-1">Last updated: {dateStr}</p>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="flex-1 sm:w-64">
                    {renderInput()}
                </div>

                {setting.type !== 'boolean' && (
                    <button
                        onClick={handleSave}
                        disabled={!isChanged || isSaving}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap min-w-[70px]"
                    >
                        {isSaving && isChanged ? 'Saving...' : 'Save'}
                    </button>
                )}
            </div>
        </div>
    )
}
