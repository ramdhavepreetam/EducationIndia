import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAdminStore } from '../store/adminStore'

/**
 * CreateTestPage — Admin form to create a new exam event.
 *
 * Calls POST /api/admin/catalog/events which auto-creates:
 *   - One exam_events row (the "test")
 *   - Paper I (501) and Paper II (502) under it
 *   - Clones sections + topics from existing papers of the same board
 *
 * Fields required by CreateEventRequest (backend):
 *   title_en, title_mr (optional), std_class, year, board_id, category_id
 */

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 6 }, (_, i) => CURRENT_YEAR - 2 + i)

export function CreateTestPage() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { boards, fetchBoards, createTest, createTestLoading, createTestError } = useAdminStore()

    const [form, setForm] = useState({
        title_en: '',
        title_mr: '',
        std_class: 5,
        year: CURRENT_YEAR,
        board_id: '',
        category_id: 1,
    })
    const [successMsg, setSuccessMsg] = useState(null)

    useEffect(() => {
        fetchBoards()
    }, [fetchBoards])

    // Auto-set board_id once boards load
    useEffect(() => {
        if (boards?.length > 0 && !form.board_id) {
            setForm(f => ({ ...f, board_id: boards[0].id }))
        }
    }, [boards, form.board_id])

    const handleChange = (e) => {
        const { name, value, type } = e.target
        setForm(f => ({ ...f, [name]: type === 'number' ? parseInt(value, 10) : value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSuccessMsg(null)
        try {
            const result = await createTest({
                ...form,
                board_id: parseInt(form.board_id, 10),
                category_id: parseInt(form.category_id, 10),
            })
            setSuccessMsg(
                `Test "${result.title_en}" created with ${result.exams?.length ?? 2} papers. ` +
                `Event ID: ${result.id}`
            )
            // Redirect to publisher after 2s so admin can publish questions
            setTimeout(() => navigate('/admin/publish'), 2000)
        } catch (_) {
            // error displayed from store
        }
    }

    return (
        <div className="p-4 sm:p-8 max-w-2xl mx-auto pb-24">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-surface-900">
                    {t('admin.createTest', 'Create New Test Set')}
                </h1>
                <p className="text-surface-500 mt-1">
                    {t('admin.createTestSub', 'Creates an exam event with Paper I and Paper II automatically. You can then upload questions and publish.')}
                </p>
            </div>

            {successMsg && (
                <div className="mb-6 p-4 bg-green-50 text-green-700 rounded-xl border border-green-200 text-sm font-medium">
                    ✓ {successMsg}
                    <p className="text-green-600 text-xs mt-1 font-normal">Redirecting to Exam Publisher…</p>
                </div>
            )}

            {createTestError && (
                <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
                    {createTestError}
                </div>
            )}

            <form
                id="create-test-form"
                onSubmit={handleSubmit}
                className="bg-white rounded-2xl border border-surface-100 shadow-sm overflow-hidden"
            >
                {/* Board */}
                <div className="px-6 py-5 border-b border-surface-100">
                    <label className="block text-sm font-semibold text-surface-700 mb-2">
                        {t('admin.board', 'Exam Board')} <span className="text-red-500">*</span>
                    </label>
                    <select
                        id="board_id"
                        name="board_id"
                        value={form.board_id}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-300 text-sm"
                    >
                        <option value="">— Select board —</option>
                        {(boards || []).map(b => (
                            <option key={b.id} value={b.id}>{b.name_en} ({b.short_code})</option>
                        ))}
                    </select>
                </div>

                {/* Title EN */}
                <div className="px-6 py-5 border-b border-surface-100">
                    <label className="block text-sm font-semibold text-surface-700 mb-2">
                        {t('admin.titleEn', 'Title (English)')} <span className="text-red-500">*</span>
                    </label>
                    <input
                        id="title_en"
                        name="title_en"
                        type="text"
                        value={form.title_en}
                        onChange={handleChange}
                        required
                        placeholder="e.g. MSCE Class 5 Scholarship Exam 2025"
                        className="w-full px-3 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-300 text-sm placeholder:text-surface-300"
                    />
                </div>

                {/* Title MR */}
                <div className="px-6 py-5 border-b border-surface-100">
                    <label className="block text-sm font-semibold text-surface-700 mb-2">
                        {t('admin.titleMr', 'Title (Marathi)')}
                        <span className="ml-2 text-xs text-surface-400 font-normal">{t('admin.optional', 'optional')}</span>
                    </label>
                    <input
                        id="title_mr"
                        name="title_mr"
                        type="text"
                        value={form.title_mr}
                        onChange={handleChange}
                        placeholder="मराठी शीर्षक (पर्यायी)"
                        className="w-full px-3 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-300 text-sm placeholder:text-surface-300 font-[Noto_Sans_Devanagari,sans-serif]"
                    />
                </div>

                {/* Std Class + Year */}
                <div className="px-6 py-5 border-b border-surface-100 grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-semibold text-surface-700 mb-2">
                            {t('admin.stdClass', 'Standard (Class)')} <span className="text-red-500">*</span>
                        </label>
                        <select
                            id="std_class"
                            name="std_class"
                            value={form.std_class}
                            onChange={handleChange}
                            required
                            className="w-full px-3 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-300 text-sm"
                        >
                            <option value={5}>Class 5</option>
                            <option value={8}>Class 8</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-surface-700 mb-2">
                            {t('admin.year', 'Year')} <span className="text-red-500">*</span>
                        </label>
                        <select
                            id="year"
                            name="year"
                            value={form.year}
                            onChange={handleChange}
                            required
                            className="w-full px-3 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-300 text-sm"
                        >
                            {YEAR_OPTIONS.map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Preview helper */}
                <div className="px-6 py-4 bg-surface-50 border-b border-surface-100">
                    <p className="text-xs text-surface-500">
                        <span className="font-semibold">Preview: </span>
                        This will create papers with codes{' '}
                        <code className="bg-surface-200 text-surface-700 px-1.5 py-0.5 rounded text-xs">501-{form.year}</code>
                        {' '}and{' '}
                        <code className="bg-surface-200 text-surface-700 px-1.5 py-0.5 rounded text-xs">502-{form.year}</code>,
                        each with 75 questions and 150 marks for Class {form.std_class}.
                    </p>
                </div>

                {/* Submit */}
                <div className="px-6 py-5 flex items-center justify-between">
                    <button
                        type="button"
                        onClick={() => navigate('/admin/publish')}
                        className="px-4 py-2 text-sm font-medium text-surface-600 hover:text-surface-800 transition"
                    >
                        ← {t('common.cancel', 'Cancel')}
                    </button>
                    <button
                        id="create-test-submit"
                        type="submit"
                        disabled={createTestLoading || !form.board_id || !form.title_en}
                        className="px-6 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {createTestLoading ? (
                            <><div className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" /> Creating…</>
                        ) : (
                            <>✚ {t('admin.createTest', 'Create Test Set')}</>
                        )}
                    </button>
                </div>
            </form>
        </div>
    )
}
