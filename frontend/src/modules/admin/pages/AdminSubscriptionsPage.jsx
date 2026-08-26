import React, { useState, useEffect, useCallback } from 'react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { settingsApi } from '../api/settingsApi'

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'
const fmtINR  = (n) => `₹${Number(n || 0).toLocaleString('en-IN')}`

const SUB_STATUS_BADGE = {
    active:    'bg-green-100 text-green-800 border-green-200',
    free:      'bg-blue-100 text-blue-800 border-blue-200',
    expired:   'bg-red-100 text-red-800 border-red-200',
    pending:   'bg-yellow-100 text-yellow-800 border-yellow-200',
    cancelled: 'bg-surface-100 text-surface-800 border-surface-200',
}

const TXN_STATUS_BADGE = {
    captured: 'bg-green-100 text-green-800',
    failed:   'bg-red-100 text-red-800',
    refunded: 'bg-orange-100 text-orange-800',
    created:  'bg-surface-100 text-surface-600',
}

const TXN_STATUS_LABEL = { captured: 'Paid', failed: 'Failed', refunded: 'Refunded', created: 'Pending' }
const SCOPE_TARGET_KEY = {
    board: 'board_id',
    category: 'category_id',
    std_class: 'std_class',
    event: 'event_id',
    exam: 'exam_id',
}

function StatusBadge({ status, map }) {
    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${map[status] || map.cancelled || map.created}`}>
            {status?.charAt(0).toUpperCase() + status?.slice(1)}
        </span>
    )
}

function CopyBtn({ text }) {
    const [copied, setCopied] = useState(false)
    return (
        <button
            onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
            className="ml-1 text-surface-400 hover:text-surface-600"
            title="Copy"
        >
            {copied
                ? <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                : <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            }
        </button>
    )
}

function getScopeOptions(scopeType, scopeOptions) {
    if (scopeType === 'board') return scopeOptions.boards || []
    if (scopeType === 'category') return scopeOptions.categories || []
    if (scopeType === 'event') return scopeOptions.events || []
    if (scopeType === 'exam') return scopeOptions.exams || []
    if (scopeType === 'std_class') return [{ id: 5, label: 'Class 5' }, { id: 8, label: 'Class 8' }]
    return []
}

function optionLabel(scopeType, option) {
    if (scopeType === 'std_class') return option.label
    if (scopeType === 'board') return `${option.name_en} (${option.short_code})`
    if (scopeType === 'category') return option.name_en
    if (scopeType === 'event') return `${option.title_en} · Class ${option.std_class} · ${option.year}`
    if (scopeType === 'exam') return `${option.title_en} · ${option.paper_code}-${option.set_code}`
    return ''
}

function buildEntitlement(scopeType, targetValue) {
    const payload = { scope_type: scopeType }
    if (scopeType !== 'all') payload[SCOPE_TARGET_KEY[scopeType]] = Number(targetValue)
    return payload
}

function PlanManager({ plans, scopeOptions, onReload }) {
    const [planForm, setPlanForm] = useState({
        name: '',
        price_inr: 499,
        duration_months: 5,
        description_en: '',
        display_order: 1,
        scope_type: 'all',
        target: '',
    })
    const [scopeForm, setScopeForm] = useState({
        plan_id: plans[0]?.id || '',
        scope_type: 'all',
        target: '',
    })
    const [busy, setBusy] = useState(false)
    const [message, setMessage] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!scopeForm.plan_id && plans[0]?.id) {
            setScopeForm(f => ({ ...f, plan_id: plans[0].id }))
        }
    }, [plans, scopeForm.plan_id])

    const targetOptions = getScopeOptions(planForm.scope_type, scopeOptions)
    const addTargetOptions = getScopeOptions(scopeForm.scope_type, scopeOptions)

    const createPlan = async (e) => {
        e.preventDefault()
        setBusy(true); setError(null); setMessage(null)
        try {
            const entitlement = buildEntitlement(planForm.scope_type, planForm.target)
            await settingsApi.createPlan({
                name: planForm.name,
                price_inr: Number(planForm.price_inr),
                duration_months: Number(planForm.duration_months),
                description_en: planForm.description_en || null,
                display_order: Number(planForm.display_order),
                features: {},
                entitlements: [entitlement],
            })
            setPlanForm(f => ({ ...f, name: '', description_en: '' }))
            setMessage('Plan created.')
            await onReload()
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create plan')
        } finally {
            setBusy(false)
        }
    }

    const addScope = async (e) => {
        e.preventDefault()
        if (!scopeForm.plan_id) return
        setBusy(true); setError(null); setMessage(null)
        try {
            await settingsApi.addPlanEntitlement(
                scopeForm.plan_id,
                buildEntitlement(scopeForm.scope_type, scopeForm.target)
            )
            setMessage('Scope added.')
            await onReload()
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to add scope')
        } finally {
            setBusy(false)
        }
    }

    const togglePlan = async (plan) => {
        setBusy(true); setError(null); setMessage(null)
        try {
            await settingsApi.updatePlan(plan.id, { is_active: !plan.is_active })
            setMessage(plan.is_active ? 'Plan deactivated.' : 'Plan activated.')
            await onReload()
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to update plan')
        } finally {
            setBusy(false)
        }
    }

    const deleteScope = async (planId, entitlementId) => {
        setBusy(true); setError(null); setMessage(null)
        try {
            await settingsApi.deletePlanEntitlement(planId, entitlementId)
            setMessage('Scope removed.')
            await onReload()
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to remove scope')
        } finally {
            setBusy(false)
        }
    }

    return (
        <div className="space-y-6">
            {message && <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm">{message}</div>}
            {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}

            <form onSubmit={createPlan} className="bg-white border border-surface-200 rounded-xl p-5 grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
                <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-surface-600 mb-1">Plan Name</label>
                    <input required value={planForm.name} onChange={e => setPlanForm(f => ({ ...f, name: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="MSCE 8th Access" />
                </div>
                <div>
                    <label className="block text-xs font-medium text-surface-600 mb-1">Price</label>
                    <input type="number" min="0" value={planForm.price_inr} onChange={e => setPlanForm(f => ({ ...f, price_inr: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                </div>
                <div>
                    <label className="block text-xs font-medium text-surface-600 mb-1">Months</label>
                    <input type="number" min="1" value={planForm.duration_months} onChange={e => setPlanForm(f => ({ ...f, duration_months: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                </div>
                <div>
                    <label className="block text-xs font-medium text-surface-600 mb-1">Scope</label>
                    <select value={planForm.scope_type} onChange={e => setPlanForm(f => ({ ...f, scope_type: e.target.value, target: '' }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                        {['all', 'std_class', 'board', 'category', 'event', 'exam'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
                {planForm.scope_type !== 'all' && (
                    <div>
                        <label className="block text-xs font-medium text-surface-600 mb-1">Target</label>
                        <select required value={planForm.target} onChange={e => setPlanForm(f => ({ ...f, target: e.target.value }))}
                            className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                            <option value="">Select</option>
                            {targetOptions.map(o => <option key={o.id} value={o.id}>{optionLabel(planForm.scope_type, o)}</option>)}
                        </select>
                    </div>
                )}
                <div className="md:col-span-5">
                    <label className="block text-xs font-medium text-surface-600 mb-1">Description</label>
                    <input value={planForm.description_en} onChange={e => setPlanForm(f => ({ ...f, description_en: e.target.value }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="Access for selected exam products" />
                </div>
                <button disabled={busy} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50">Create Plan</button>
            </form>

            <form onSubmit={addScope} className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-wrap gap-3 items-end">
                <div className="w-56">
                    <label className="block text-xs font-medium text-surface-600 mb-1">Add Scope To</label>
                    <select value={scopeForm.plan_id} onChange={e => setScopeForm(f => ({ ...f, plan_id: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                        {plans.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                </div>
                <div className="w-40">
                    <label className="block text-xs font-medium text-surface-600 mb-1">Scope</label>
                    <select value={scopeForm.scope_type} onChange={e => setScopeForm(f => ({ ...f, scope_type: e.target.value, target: '' }))}
                        className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                        {['all', 'std_class', 'board', 'category', 'event', 'exam'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
                {scopeForm.scope_type !== 'all' && (
                    <div className="min-w-64 flex-1">
                        <label className="block text-xs font-medium text-surface-600 mb-1">Target</label>
                        <select required value={scopeForm.target} onChange={e => setScopeForm(f => ({ ...f, target: e.target.value }))}
                            className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                            <option value="">Select</option>
                            {addTargetOptions.map(o => <option key={o.id} value={o.id}>{optionLabel(scopeForm.scope_type, o)}</option>)}
                        </select>
                    </div>
                )}
                <button disabled={busy || !scopeForm.plan_id} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50">Add Scope</button>
            </form>

            <div className="grid gap-4">
                {plans.map(plan => (
                    <div key={plan.id} className="bg-white border border-surface-200 rounded-xl p-5">
                        <div className="flex justify-between gap-4">
                            <div>
                                <h3 className="font-semibold text-surface-900">{plan.name}</h3>
                                <p className="text-sm text-surface-500">{plan.description_en || 'No description'}</p>
                                <p className="text-sm text-surface-700 mt-1">{fmtINR(plan.price_inr)} · {plan.duration_months} months</p>
                            </div>
                            <button onClick={() => togglePlan(plan)} disabled={busy}
                                className={`h-9 px-3 rounded-lg text-sm font-medium ${plan.is_active ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                                {plan.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                        </div>
                        <div className="mt-4 flex flex-wrap gap-2">
                            {(plan.entitlements || []).length === 0 && <span className="text-xs text-surface-400">No scopes configured</span>}
                            {(plan.entitlements || []).map(ent => (
                                <span key={ent.id} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-100 text-surface-700 text-xs">
                                    {ent.label || ent.scope_type}
                                    <button onClick={() => deleteScope(plan.id, ent.id)} className="text-surface-400 hover:text-red-600">×</button>
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, accent }) {
    const colours = {
        blue:   'bg-blue-50 border-blue-200 text-blue-700',
        green:  'bg-green-50 border-green-200 text-green-700',
        purple: 'bg-purple-50 border-purple-200 text-purple-700',
        red:    'bg-red-50 border-red-200 text-red-700',
        gray:   'bg-surface-50 border-surface-200 text-surface-700',
    }
    return (
        <div className={`rounded-xl border p-5 ${colours[accent] || colours.gray}`}>
            <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {sub && <p className="text-xs mt-1 opacity-60">{sub}</p>}
        </div>
    )
}

// ── Per-parent payment drawer ─────────────────────────────────────────────────
function ParentPaymentsDrawer({ parentId, parentName, onClose }) {
    const [rows, setRows]       = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        settingsApi.fetchPaymentsByParent(parentId)
            .then(setRows)
            .finally(() => setLoading(false))
    }, [parentId])

    return (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mt-2">
            <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-semibold text-blue-900">
                    Transaction history — {parentName}
                </h4>
                <button onClick={onClose} className="text-blue-400 hover:text-blue-700 text-xs font-medium">Close</button>
            </div>

            {loading ? (
                <div className="flex justify-center py-6">
                    <div className="animate-spin h-5 w-5 border-b-2 border-blue-600 rounded-full" />
                </div>
            ) : rows.length === 0 ? (
                <p className="text-sm text-blue-600 text-center py-4">No payment records found.</p>
            ) : (
                <div className="overflow-x-auto rounded-lg border border-blue-100">
                    <table className="min-w-full text-xs">
                        <thead className="bg-blue-100 text-blue-700 uppercase tracking-wide">
                            <tr>
                                <th className="px-4 py-2 text-left">Date</th>
                                <th className="px-4 py-2 text-left">Amount</th>
                                <th className="px-4 py-2 text-left">Razorpay Payment ID</th>
                                <th className="px-4 py-2 text-left">Status</th>
                                <th className="px-4 py-2 text-left">Sub Expires</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-blue-100 bg-white">
                            {rows.map(r => (
                                <tr key={r.id} className="hover:bg-blue-50">
                                    <td className="px-4 py-2 whitespace-nowrap">{fmtDate(r.paid_at || r.created_at)}</td>
                                    <td className="px-4 py-2 font-semibold">{fmtINR(r.amount_inr)}</td>
                                    <td className="px-4 py-2">
                                        {r.razorpay_payment_id
                                            ? <span className="flex items-center font-mono">{r.razorpay_payment_id}<CopyBtn text={r.razorpay_payment_id} /></span>
                                            : <span className="text-surface-400">—</span>}
                                    </td>
                                    <td className="px-4 py-2">
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TXN_STATUS_BADGE[r.status] || TXN_STATUS_BADGE.created}`}>
                                            {TXN_STATUS_LABEL[r.status] || r.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap">{fmtDate(r.subscription_expires_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

// ── Transactions tab ──────────────────────────────────────────────────────────
function TransactionsTab() {
    const [rows, setRows]         = useState([])
    const [loading, setLoading]   = useState(true)
    const [statusFilter, setStatusFilter] = useState('all')
    const [search, setSearch]     = useState('')
    const [searchInput, setSearchInput] = useState('')
    const [page, setPage]         = useState(1)
    const LIMIT = 50

    const load = useCallback(() => {
        setLoading(true)
        settingsApi.fetchAllPayments({ status: statusFilter, search, page, limit: LIMIT })
            .then(setRows)
            .catch(() => setRows([]))
            .finally(() => setLoading(false))
    }, [statusFilter, search, page])

    useEffect(() => { load() }, [load])

    const handleSearch = (e) => {
        e.preventDefault()
        setSearch(searchInput)
        setPage(1)
    }

    const exportCSV = () => {
        const header = 'Date,Parent,Email,Amount (INR),Status,Razorpay Payment ID,Order ID'
        const csvRows = rows.map(r => [
            fmtDate(r.paid_at || r.created_at),
            `"${r.parent_name || ''}"`,
            r.parent_email || '',
            r.amount_inr,
            r.status,
            r.razorpay_payment_id || '',
            r.razorpay_order_id || '',
        ].join(','))
        const blob = new Blob([[header, ...csvRows].join('\n')], { type: 'text/csv' })
        const url  = URL.createObjectURL(blob)
        const a    = document.createElement('a')
        a.href = url; a.download = 'transactions.csv'; a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <div>
            {/* Toolbar */}
            <div className="flex flex-wrap gap-3 mb-4 items-center justify-between">
                <div className="flex gap-2 flex-wrap">
                    {['all', 'captured', 'failed', 'refunded', 'created'].map(s => (
                        <button
                            key={s}
                            onClick={() => { setStatusFilter(s); setPage(1) }}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${statusFilter === s ? 'bg-surface-900 text-white border-surface-900' : 'bg-white text-surface-600 border-surface-300 hover:bg-surface-50'}`}
                        >
                            {s === 'all' ? 'All' : TXN_STATUS_LABEL[s] || s}
                        </button>
                    ))}
                </div>
                <div className="flex gap-2">
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <input
                            value={searchInput}
                            onChange={e => setSearchInput(e.target.value)}
                            placeholder="Search parent name / email..."
                            className="pl-3 pr-3 py-1.5 border border-surface-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500 w-56"
                        />
                        <button type="submit" className="px-3 py-1.5 bg-surface-100 border border-surface-300 rounded-lg text-sm hover:bg-surface-200">Search</button>
                    </form>
                    <button
                        onClick={exportCSV}
                        className="px-3 py-1.5 bg-white border border-surface-300 rounded-lg text-sm font-medium text-surface-700 hover:bg-surface-50 flex items-center gap-1.5"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        CSV
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="flex justify-center py-16">
                        <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" />
                    </div>
                ) : rows.length === 0 ? (
                    <div className="text-center py-16 text-surface-400 text-sm">No transactions found.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-sm divide-y divide-surface-100">
                            <thead className="bg-surface-50 text-xs font-semibold text-surface-500 uppercase tracking-wide">
                                <tr>
                                    <th className="px-5 py-3 text-left">Date</th>
                                    <th className="px-5 py-3 text-left">Parent</th>
                                    <th className="px-5 py-3 text-left">Amount</th>
                                    <th className="px-5 py-3 text-left">Razorpay Payment ID</th>
                                    <th className="px-5 py-3 text-left">Order ID</th>
                                    <th className="px-5 py-3 text-left">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {rows.map(r => (
                                    <tr key={r.id} className="hover:bg-surface-50">
                                        <td className="px-5 py-3 whitespace-nowrap text-surface-600">
                                            {fmtDate(r.paid_at || r.created_at)}
                                        </td>
                                        <td className="px-5 py-3">
                                            <p className="font-medium text-surface-900">{r.parent_name || '—'}</p>
                                            <p className="text-xs text-surface-500">{r.parent_email}</p>
                                        </td>
                                        <td className="px-5 py-3 font-semibold text-surface-900 whitespace-nowrap">
                                            {fmtINR(r.amount_inr)}
                                        </td>
                                        <td className="px-5 py-3">
                                            {r.razorpay_payment_id
                                                ? <span className="flex items-center font-mono text-xs text-surface-600">{r.razorpay_payment_id}<CopyBtn text={r.razorpay_payment_id} /></span>
                                                : <span className="text-surface-400">—</span>}
                                        </td>
                                        <td className="px-5 py-3 font-mono text-xs text-surface-500">
                                            {r.razorpay_order_id
                                                ? <span className="flex items-center">{r.razorpay_order_id.slice(0, 18)}…<CopyBtn text={r.razorpay_order_id} /></span>
                                                : '—'}
                                        </td>
                                        <td className="px-5 py-3">
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TXN_STATUS_BADGE[r.status] || TXN_STATUS_BADGE.created}`}>
                                                {TXN_STATUS_LABEL[r.status] || r.status}
                                            </span>
                                            {r.failure_reason && (
                                                <p className="text-xs text-red-500 mt-0.5">{r.failure_reason}</p>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4 text-sm text-surface-500">
                <span>{rows.length} records on this page</span>
                <div className="flex gap-2">
                    <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 border rounded-lg disabled:opacity-40 hover:bg-surface-50">Prev</button>
                    <span className="px-3 py-1">Page {page}</span>
                    <button disabled={rows.length < LIMIT} onClick={() => setPage(p => p + 1)} className="px-3 py-1 border rounded-lg disabled:opacity-40 hover:bg-surface-50">Next</button>
                </div>
            </div>
        </div>
    )
}

// ── Revenue chart ─────────────────────────────────────────────────────────────
function RevenueChart() {
    const [data, setData]     = useState([])
    const [loading, setLoading] = useState(true)
    const [months, setMonths] = useState(6)

    useEffect(() => {
        setLoading(true)
        settingsApi.fetchMonthlyRevenue(months)
            .then(rows => setData(rows.map(r => ({
                month: r.month,
                revenue: Number(r.revenue),
                count: Number(r.count),
            }))))
            .catch(() => setData([]))
            .finally(() => setLoading(false))
    }, [months])

    return (
        <div className="bg-white rounded-xl border border-surface-200 shadow-sm p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-surface-700">Monthly Revenue</h3>
                <select
                    value={months}
                    onChange={e => setMonths(Number(e.target.value))}
                    className="text-xs border border-surface-300 rounded-lg px-2 py-1 bg-white"
                >
                    <option value={3}>Last 3 months</option>
                    <option value={6}>Last 6 months</option>
                    <option value={12}>Last 12 months</option>
                </select>
            </div>
            {loading ? (
                <div className="flex justify-center py-10">
                    <div className="animate-spin h-6 w-6 border-b-2 border-blue-600 rounded-full" />
                </div>
            ) : data.length === 0 ? (
                <p className="text-center text-surface-400 text-sm py-10">No revenue data yet.</p>
            ) : (
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                        <YAxis tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                        <Tooltip
                            formatter={(value, name) => name === 'revenue' ? [fmtINR(value), 'Revenue'] : [value, 'Payments']}
                        />
                        <Bar dataKey="revenue" fill="#2563EB" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            )}
        </div>
    )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export const AdminSubscriptionsPage = () => {
    const [subscriptions, setSubscriptions] = useState([])
    const [plans, setPlans]       = useState([])
    const [scopeOptions, setScopeOptions] = useState({ boards: [], categories: [], events: [], exams: [] })
    const [stats, setStats]       = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError]       = useState(null)

    const [mainTab, setMainTab]   = useState('subscriptions')   // subscriptions | plans | transactions
    const [subFilter, setSubFilter] = useState('All')
    const [searchQuery, setSearchQuery] = useState('')
    const [actionLoadingId, setActionLoadingId] = useState(null)
    const [expandedParentId, setExpandedParentId] = useState(null)

    // Grant form
    const [showGrant, setShowGrant]   = useState(false)
    const [grantEmail, setGrantEmail] = useState('')
    const [grantPlanId, setGrantPlanId] = useState('')
    const [grantMonths, setGrantMonths] = useState(5)
    const [grantLoading, setGrantLoading] = useState(false)
    const [grantError, setGrantError]   = useState(null)
    const [grantSuccess, setGrantSuccess] = useState(null)

    useEffect(() => {
        loadAll()
    }, [])

    const loadAll = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const [subsResult, statsResult, plansResult, scopeOptionsResult] = await Promise.allSettled([
                settingsApi.fetchSubscriptions(),
                settingsApi.fetchPaymentStats(),
                settingsApi.fetchPlans(),
                settingsApi.fetchPlanScopeOptions(),
            ])

            if (subsResult.status === 'fulfilled') {
                setSubscriptions(subsResult.value)
            } else {
                setError('Failed to load subscriptions.')
            }

            if (statsResult.status === 'fulfilled') {
                setStats(statsResult.value)
            }
            // stats silently fails — page still works without it

            if (plansResult.status === 'fulfilled') {
                const plansData = plansResult.value
                const arr = Array.isArray(plansData) ? plansData : plansData?.plans ? plansData.plans : [plansData]
                setPlans(arr.filter(Boolean))
                if (arr[0]?.id) setGrantPlanId(arr[0].id)
            }

            if (scopeOptionsResult.status === 'fulfilled') {
                setScopeOptions(scopeOptionsResult.value)
            }
        } finally {
            setIsLoading(false)
        }
    }

    const handleGrant = async (e) => {
        e.preventDefault()
        setGrantLoading(true); setGrantError(null); setGrantSuccess(null)
        try {
            const result = await settingsApi.grantSubscription(grantEmail, grantPlanId, grantMonths)
            setGrantSuccess(`Granted to ${result.parent_name || result.parent_email}. Expires: ${fmtDate(result.expires_at)}`)
            setGrantEmail('')
            await loadAll()
        } catch (err) {
            setGrantError(err.response?.data?.detail || 'Failed to grant subscription')
        } finally {
            setGrantLoading(false)
        }
    }

    const openGrantForParent = (sub) => {
        setGrantEmail(sub.parent_email || '')
        setGrantError(null)
        setGrantSuccess(null)
        setShowGrant(true)
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const handleExtend = async (id, months) => {
        setActionLoadingId(id)
        try {
            await settingsApi.extendSubscription(id, months)
            await loadAll()
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to extend subscription')
        } finally {
            setActionLoadingId(null)
        }
    }

    const handleCancel = async (id) => {
        if (!window.confirm('Cancel this subscription? The parent will lose access instantly.')) return
        setActionLoadingId(id)
        try {
            await settingsApi.cancelSubscription(id)
            await loadAll()
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to cancel')
        } finally {
            setActionLoadingId(null)
        }
    }

    const filteredSubs = subscriptions.filter(sub => {
        if (subFilter === 'Active'    && sub.status !== 'active')    return false
        if (subFilter === 'Free'      && sub.status !== 'free')      return false
        if (subFilter === 'Expired'   && sub.status !== 'expired')   return false
        if (subFilter === 'Pending'   && sub.status !== 'pending')   return false
        if (subFilter === 'Cancelled' && sub.status !== 'cancelled') return false
        if (searchQuery) {
            const q = searchQuery.toLowerCase()
            return (
                (sub.parent_name || '').toLowerCase().includes(q) ||
                (sub.parent_email || '').toLowerCase().includes(q) ||
                (sub.parent_id || '').toLowerCase().includes(q)
            )
        }
        return true
    })

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

            {/* Page header */}
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-6 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-surface-900">Payments & Subscriptions</h1>
                    <p className="text-sm text-surface-500 mt-1">Revenue overview, transactions, and subscription management.</p>
                </div>
                <button
                    onClick={loadAll}
                    className="px-4 py-2 bg-white border border-surface-300 rounded-lg text-sm font-medium text-surface-700 hover:bg-surface-50 transition self-start"
                >
                    Refresh
                </button>
            </div>

            {/* ── Revenue stat cards ── */}
            {isLoading ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="h-24 bg-surface-100 rounded-xl animate-pulse" />
                    ))}
                </div>
            ) : stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <StatCard
                        label="Total Revenue"
                        value={fmtINR(stats.total_revenue_inr)}
                        sub={`${stats.total_transactions} transactions`}
                        accent="blue"
                    />
                    <StatCard
                        label="Active Subscriptions"
                        value={stats.active_subscriptions ?? 0}
                        sub={`${stats.free_parent_users ?? 0} free parents`}
                        accent="green"
                    />
                    <StatCard
                        label="This Month"
                        value={fmtINR(stats.this_month_revenue)}
                        sub={`Last month: ${fmtINR(stats.last_month_revenue)}`}
                        accent="purple"
                    />
                    <StatCard
                        label="Failed Payments"
                        value={stats.failed_transactions ?? 0}
                        sub={stats.failed_transactions > 0 ? 'Needs attention' : 'All clear'}
                        accent={stats.failed_transactions > 0 ? 'red' : 'gray'}
                    />
                </div>
            )}

            {/* ── Monthly revenue chart ── */}
            <RevenueChart />

            {/* ── Main tab navigation ── */}
            <div className="border-b border-surface-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    {[
                        { key: 'subscriptions', label: 'Subscriptions', count: subscriptions.length },
                        { key: 'plans',          label: 'Plans',          count: plans.length },
                        { key: 'transactions',  label: 'Transactions',  count: null },
                    ].map(t => (
                        <button
                            key={t.key}
                            onClick={() => setMainTab(t.key)}
                            className={`whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                                mainTab === t.key
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-surface-500 hover:text-surface-700 hover:border-surface-300'
                            }`}
                        >
                            {t.label}
                            {t.count != null && (
                                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-surface-100 text-surface-600">{t.count}</span>
                            )}
                        </button>
                    ))}
                </nav>
            </div>

            {/* ── Subscriptions tab ── */}
            {mainTab === 'subscriptions' && (
                <div>
                    {/* Toolbar */}
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
                        <div className="flex gap-2 flex-wrap">
                            {['All', 'Active', 'Free', 'Expired', 'Pending', 'Cancelled'].map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setSubFilter(tab)}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                                        subFilter === tab
                                            ? 'bg-surface-900 text-white border-surface-900'
                                            : 'bg-white text-surface-600 border-surface-300 hover:bg-surface-50'
                                    }`}
                                >
                                    {tab}
                                    {tab === 'Active' && (
                                        <span className="ml-1.5 bg-green-200 text-green-800 px-1.5 rounded-full text-xs">
                                            {subscriptions.filter(s => s.status === 'active').length}
                                        </span>
                                    )}
                                    {tab === 'Free' && (
                                        <span className="ml-1.5 bg-blue-200 text-blue-800 px-1.5 rounded-full text-xs">
                                            {subscriptions.filter(s => s.status === 'free').length}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>
                        <div className="flex gap-2">
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Search parent/email..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    className="pl-8 pr-4 py-1.5 border border-surface-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500 w-56"
                                />
                                <svg className="absolute left-2.5 top-2 h-4 w-4 text-surface-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <button
                                onClick={() => setShowGrant(!showGrant)}
                                className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition flex items-center gap-1.5"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
                                Grant Access
                            </button>
                        </div>
                    </div>

                    {/* Grant Access form */}
                    {showGrant && (
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-4">
                            <h3 className="text-sm font-semibold text-blue-900 mb-4">Grant Subscription Access</h3>
                            <form onSubmit={handleGrant} className="flex flex-wrap items-end gap-4">
                                <div className="flex-1 min-w-[200px]">
                                    <label className="block text-xs font-medium text-surface-700 mb-1">Parent Email</label>
                                    <input
                                        type="email" required value={grantEmail}
                                        onChange={e => setGrantEmail(e.target.value)}
                                        placeholder="parent@email.com"
                                        className="w-full px-3 py-2 border border-surface-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                                <div className="w-48">
                                    <label className="block text-xs font-medium text-surface-700 mb-1">Plan</label>
                                    <select
                                        value={grantPlanId}
                                        onChange={e => setGrantPlanId(Number(e.target.value))}
                                        className="w-full px-3 py-2 border border-surface-300 rounded-lg text-sm bg-white"
                                    >
                                        {plans.map(p => <option key={p.id} value={p.id}>{p.name} — ₹{p.price_inr}</option>)}
                                        {plans.length === 0 && <option>No plans</option>}
                                    </select>
                                </div>
                                <div className="w-32">
                                    <label className="block text-xs font-medium text-surface-700 mb-1">Duration</label>
                                    <div className="flex items-center gap-1">
                                        <input
                                            type="number" min={1} max={24} value={grantMonths}
                                            onChange={e => setGrantMonths(Number(e.target.value))}
                                            className="w-full px-3 py-2 border border-surface-300 rounded-lg text-sm"
                                        />
                                        <span className="text-xs text-surface-500 whitespace-nowrap">months</span>
                                    </div>
                                </div>
                                <button
                                    type="submit"
                                    disabled={grantLoading || !grantEmail || !grantPlanId}
                                    className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {grantLoading ? 'Granting…' : 'Grant Access'}
                                </button>
                            </form>
                            {grantError   && <p className="mt-3 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{grantError}</p>}
                            {grantSuccess && <p className="mt-3 text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">✓ {grantSuccess}</p>}
                        </div>
                    )}

                    {error ? (
                        <div className="bg-red-50 text-red-700 p-4 rounded-lg">{error}</div>
                    ) : isLoading ? (
                        <div className="flex justify-center py-20">
                            <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 rounded-full" />
                        </div>
                    ) : filteredSubs.length === 0 ? (
                        <div className="text-center py-16 bg-white rounded-xl border border-dashed border-surface-200">
                            <p className="text-surface-500 text-sm">
                                {subscriptions.length === 0
                                    ? 'No parent accounts found yet.'
                                    : 'No records matching current filters.'}
                            </p>
                        </div>
                    ) : (
                        <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-surface-200 text-sm">
                                    <thead className="bg-surface-50 text-xs font-semibold text-surface-500 uppercase tracking-wide">
                                        <tr>
                                            <th className="px-5 py-3 text-left">Parent</th>
                                            <th className="px-5 py-3 text-left">Plan</th>
                                            <th className="px-5 py-3 text-left">Amount Paid</th>
                                            <th className="px-5 py-3 text-left">Status</th>
                                            <th className="px-5 py-3 text-left">Started</th>
                                            <th className="px-5 py-3 text-left">Expires</th>
                                            <th className="px-5 py-3 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-surface-100">
                                        {filteredSubs.map(sub => (
                                            <React.Fragment key={sub.id || sub.parent_id}>
                                                <tr className="hover:bg-surface-50">
                                                    <td className="px-5 py-3">
                                                        <p className="font-medium text-surface-900">{sub.parent_name || 'Unknown'}</p>
                                                        <p className="text-xs text-surface-500">{sub.parent_email || 'No email'}</p>
                                                        <p className="text-xs text-surface-400 font-mono">{sub.parent_id?.split('-')[0]}…</p>
                                                    </td>
                                                    <td className="px-5 py-3 text-surface-700">{sub.plan_name || (sub.status === 'free' ? 'Free Tier' : 'Standard')}</td>
                                                    <td className="px-5 py-3 font-semibold text-surface-900">{fmtINR(sub.amount_paid_inr)}</td>
                                                    <td className="px-5 py-3">
                                                        <StatusBadge status={sub.status} map={SUB_STATUS_BADGE} />
                                                    </td>
                                                    <td className="px-5 py-3 text-surface-500 whitespace-nowrap">{fmtDate(sub.started_at)}</td>
                                                    <td className="px-5 py-3 text-surface-500 whitespace-nowrap">{fmtDate(sub.expires_at)}</td>
                                                    <td className="px-5 py-3 text-right">
                                                        {sub.id && actionLoadingId === sub.id ? (
                                                            <span className="text-surface-400 text-xs">Processing…</span>
                                                        ) : (
                                                            <div className="flex justify-end gap-1.5 flex-wrap">
                                                                <button
                                                                    onClick={() => setExpandedParentId(
                                                                        expandedParentId === sub.parent_id ? null : sub.parent_id
                                                                    )}
                                                                    className="text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-2 py-1 rounded text-xs font-medium"
                                                                >
                                                                    {expandedParentId === sub.parent_id ? 'Hide' : 'Payments'}
                                                                </button>
                                                                {(sub.status === 'active' || sub.status === 'expired') && (
                                                                    <>
                                                                        <button onClick={() => handleExtend(sub.id, 1)} className="text-blue-600 hover:text-blue-800 bg-blue-50 px-2 py-1 rounded text-xs font-medium">+1M</button>
                                                                        <button onClick={() => handleExtend(sub.id, 3)} className="text-blue-600 hover:text-blue-800 bg-blue-50 px-2 py-1 rounded text-xs font-medium">+3M</button>
                                                                    </>
                                                                )}
                                                                {sub.status === 'free' && (
                                                                    <button onClick={() => openGrantForParent(sub)} className="text-green-600 hover:text-green-800 bg-green-50 px-2 py-1 rounded text-xs font-medium">Grant</button>
                                                                )}
                                                                {sub.status === 'active' && (
                                                                    <button onClick={() => handleCancel(sub.id)} className="text-red-600 hover:text-red-800 bg-red-50 px-2 py-1 rounded text-xs font-medium">Cancel</button>
                                                                )}
                                                            </div>
                                                        )}
                                                    </td>
                                                </tr>

                                                {/* Per-parent payment drill-down */}
                                                {expandedParentId === sub.parent_id && (
                                                    <tr>
                                                        <td colSpan={7} className="px-5 py-2 bg-blue-50/40">
                                                            <ParentPaymentsDrawer
                                                                parentId={sub.parent_id}
                                                                parentName={sub.parent_name}
                                                                onClose={() => setExpandedParentId(null)}
                                                            />
                                                        </td>
                                                    </tr>
                                                )}
                                            </React.Fragment>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {mainTab === 'plans' && (
                <PlanManager plans={plans} scopeOptions={scopeOptions} onReload={loadAll} />
            )}

            {/* ── Transactions tab ── */}
            {mainTab === 'transactions' && <TransactionsTab />}
        </div>
    )
}
