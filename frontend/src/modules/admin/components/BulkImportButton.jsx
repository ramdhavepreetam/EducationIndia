import { useRef, useState } from 'react'
import { useAdminStore } from '../store/adminStore'

/**
 * BulkImportButton — file picker that reads a JSON file and posts it to bulk-import.
 * JSON must match BulkImportSchema: { exam_id, contexts: [...], questions: [...] }
 */
export function BulkImportButton({ examId }) {
    const fileRef = useRef(null)
    const runBulkImport = useAdminStore(s => s.runBulkImport)
    const bulkImporting = useAdminStore(s => s.bulkImporting)
    const bulkImportResult = useAdminStore(s => s.bulkImportResult)
    const [error, setError] = useState(null)

    const handleFile = async (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        setError(null)

        try {
            const text = await file.text()
            const payload = JSON.parse(text)
            // Override exam_id with the currently selected exam
            payload.exam_id = examId
            await runBulkImport(payload)
        } catch (err) {
            if (err.name === 'SyntaxError') {
                setError('Invalid JSON file. Check the file format.')
            } else {
                setError(err.response?.data?.detail || err.message || 'Import failed')
            }
        }
        // Reset file input so the same file can be re-selected
        if (fileRef.current) fileRef.current.value = ''
    }

    return (
        <div className="flex flex-col gap-2">
            <input
                ref={fileRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFile}
            />
            <button
                onClick={() => fileRef.current?.click()}
                disabled={bulkImporting || !examId}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-accent-500 text-white rounded-xl hover:bg-accent-600 disabled:opacity-50 transition-colors"
            >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {bulkImporting ? 'Importing…' : 'Bulk Import JSON'}
            </button>

            {error && (
                <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-200">{error}</p>
            )}

            {bulkImportResult && (
                <div className="text-xs bg-green-50 border border-green-200 px-3 py-2 rounded-lg text-green-800 space-y-1">
                    <p className="font-semibold">Import complete</p>
                    <p>Inserted: {bulkImportResult.inserted} | Skipped: {bulkImportResult.skipped}</p>
                    {bulkImportResult.errors?.length > 0 && (
                        <ul className="mt-1 list-disc pl-4 text-red-700 space-y-0.5">
                            {bulkImportResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                        </ul>
                    )}
                </div>
            )}
        </div>
    )
}
