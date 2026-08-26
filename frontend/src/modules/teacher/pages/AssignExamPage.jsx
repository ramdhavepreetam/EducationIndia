import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTeacherStore } from '../store/teacherStore'
import { useAdminStore } from '@/modules/admin/store/adminStore'

function StepIndicator({ step }) {
    const steps = ['Find Student', 'Select Exam', 'Confirm']
    return (
        <div className="flex items-center gap-2 mb-8">
            {steps.map((label, i) => {
                const num = i + 1
                const active = step === num
                const done = step > num
                return (
                    <div key={label} className="flex items-center gap-2">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                            ${done ? 'bg-green-500 text-white' : active ? 'bg-brand-600 text-white' : 'bg-surface-200 text-surface-500'}`}>
                            {done ? '✓' : num}
                        </div>
                        <span className={`text-sm ${active ? 'font-semibold text-surface-900' : 'text-surface-400'}`}>
                            {label}
                        </span>
                        {i < steps.length - 1 && (
                            <div className={`w-8 h-0.5 mx-1 ${done ? 'bg-green-300' : 'bg-surface-200'}`} />
                        )}
                    </div>
                )
            })}
        </div>
    )
}

export function AssignExamPage() {
    const navigate = useNavigate()
    const { lookupResult, isLookingUp, isAssigning, assignSuccess, error, lookupStudent, assignExam, clearError, clearAssignSuccess } = useTeacherStore()
    const { exams, fetchAllExams } = useAdminStore()

    const [step, setStep] = useState(1)
    const [email, setEmail] = useState('')
    const [selectedExamId, setSelectedExamId] = useState('')
    const [maxAttempts, setMaxAttempts] = useState(10)

    useEffect(() => {
        if (exams.length === 0) fetchAllExams()
    }, [exams.length, fetchAllExams])

    useEffect(() => {
        if (assignSuccess) {
            const t = setTimeout(() => {
                clearAssignSuccess()
                navigate('/teacher/students')
            }, 2500)
            return () => clearTimeout(t)
        }
    }, [assignSuccess, clearAssignSuccess, navigate])

    const handleLookup = async (e) => {
        e.preventDefault()
        clearError()
        const student = await lookupStudent(email.trim())
        if (student) setStep(2)
    }

    const handleAssign = async (e) => {
        e.preventDefault()
        if (!lookupResult || !selectedExamId) return
        const result = await assignExam({
            student_id: lookupResult.id,
            exam_id: Number(selectedExamId),
            max_attempts: maxAttempts,
        })
        if (result) setStep(3)
    }

    if (assignSuccess) {
        return (
            <div className="max-w-lg mx-auto px-4 py-16 text-center">
                <div className="text-5xl mb-4">✅</div>
                <h2 className="text-xl font-bold text-surface-900 mb-2">Exam Assigned!</h2>
                <p className="text-surface-500 text-sm mb-1">
                    <strong>{assignSuccess.student_name}</strong> can now take{' '}
                    <strong>{assignSuccess.exam_title}</strong>.
                </p>
                <p className="text-surface-400 text-xs">Redirecting to students list…</p>
            </div>
        )
    }

    return (
        <div className="max-w-2xl mx-auto px-4 py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">Assign Exam</h1>
                <p className="text-surface-500 mt-1 text-sm">
                    Find a student by their registered email, then choose which exam to assign.
                </p>
            </div>

            <StepIndicator step={step} />

            {error && (
                <div className="mb-5 bg-red-50 text-red-700 p-4 rounded-xl border border-red-100 text-sm flex justify-between items-center">
                    {error}
                    <button onClick={clearError} className="text-red-400 hover:text-red-600 ml-3">✕</button>
                </div>
            )}

            {/* Step 1: Find Student */}
            {step === 1 && (
                <div className="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
                    <h2 className="text-base font-semibold text-surface-800 mb-4">Find Student by Email</h2>
                    <form onSubmit={handleLookup}>
                        <label className="block text-sm font-medium text-surface-700 mb-1.5">
                            Student's Email Address
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            placeholder="student@example.com"
                            required
                            className="w-full text-sm border border-surface-200 rounded-xl px-4 py-2.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                        />
                        <p className="text-xs text-surface-400 mt-1.5">
                            The student must have a registered ScholarPath account.
                        </p>
                        <button
                            type="submit"
                            disabled={isLookingUp || !email.trim()}
                            className="mt-5 w-full py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors"
                        >
                            {isLookingUp ? 'Searching…' : 'Find Student →'}
                        </button>
                    </form>
                </div>
            )}

            {/* Step 2: Select Exam */}
            {step === 2 && lookupResult && (
                <div className="space-y-4">
                    {/* Student confirmation card */}
                    <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-green-200 text-green-800 font-bold flex items-center justify-center text-sm flex-shrink-0">
                            {lookupResult.full_name?.slice(0, 2).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-semibold text-green-900">{lookupResult.full_name}</p>
                            <p className="text-xs text-green-700">{lookupResult.email}</p>
                            {lookupResult.std_class && (
                                <p className="text-xs text-green-600 mt-0.5">Std {lookupResult.std_class} · {lookupResult.school_name || 'Unknown school'}</p>
                            )}
                        </div>
                        <button
                            onClick={() => { setStep(1); clearError() }}
                            className="text-xs text-green-700 hover:text-green-900 underline flex-shrink-0"
                        >
                            Change
                        </button>
                    </div>

                    <div className="bg-white rounded-2xl border border-surface-100 shadow-sm p-6">
                        <h2 className="text-base font-semibold text-surface-800 mb-4">Select Exam</h2>
                        <form onSubmit={handleAssign}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-surface-700 mb-1.5">
                                    Exam
                                </label>
                                <select
                                    value={selectedExamId}
                                    onChange={e => setSelectedExamId(e.target.value)}
                                    required
                                    className="w-full text-sm border border-surface-200 rounded-xl px-4 py-2.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400 bg-white"
                                >
                                    <option value="">— Choose an exam —</option>
                                    {exams.map(ex => (
                                        <option key={ex.id} value={ex.id}>
                                            {ex.title_en || `${ex.paper_code}-${ex.set_code}`}
                                            {!ex.is_active ? ' (inactive)' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="mb-5">
                                <label className="block text-sm font-medium text-surface-700 mb-1.5">
                                    Max Attempts
                                </label>
                                <input
                                    type="number"
                                    value={maxAttempts}
                                    onChange={e => setMaxAttempts(Number(e.target.value))}
                                    min={1}
                                    max={50}
                                    className="w-32 text-sm border border-surface-200 rounded-xl px-4 py-2.5 text-surface-700 focus:outline-none focus:ring-2 focus:ring-brand-400"
                                />
                                <p className="text-xs text-surface-400 mt-1">How many times the student can take this exam.</p>
                            </div>

                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setStep(1)}
                                    className="flex-1 py-2.5 border border-surface-200 text-surface-600 text-sm font-semibold rounded-xl hover:bg-surface-50 transition-colors"
                                >
                                    ← Back
                                </button>
                                <button
                                    type="submit"
                                    disabled={isAssigning || !selectedExamId}
                                    className="flex-1 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors"
                                >
                                    {isAssigning ? 'Assigning…' : 'Assign Exam →'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
