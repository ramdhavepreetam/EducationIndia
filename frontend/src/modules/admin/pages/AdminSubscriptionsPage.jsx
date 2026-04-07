import React, { useState, useEffect } from 'react'
import { settingsApi } from '../api/settingsApi'

export const AdminSubscriptionsPage = () => {
    const [subscriptions, setSubscriptions] = useState([])
    const [plans, setPlans] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    const [activeTab, setActiveTab] = useState('All')
    const [searchQuery, setSearchQuery] = useState('')
    const [actionLoadingId, setActionLoadingId] = useState(null)

    // Grant form state
    const [showGrant, setShowGrant] = useState(false)
    const [grantEmail, setGrantEmail] = useState('')
    const [grantPlanId, setGrantPlanId] = useState('')
    const [grantMonths, setGrantMonths] = useState(5)
    const [grantLoading, setGrantLoading] = useState(false)
    const [grantError, setGrantError] = useState(null)
    const [grantSuccess, setGrantSuccess] = useState(null)

    useEffect(() => {
        loadSubscriptions()
        loadPlans()
    }, [])

    const loadSubscriptions = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await settingsApi.fetchSubscriptions()
            setSubscriptions(data)
        } catch (err) {
            setError('Failed to load subscriptions.')
        } finally {
            setIsLoading(false)
        }
    }

    const loadPlans = async () => {
        try {
            const data = await settingsApi.fetchPlans()
            setPlans(Array.isArray(data) ? data : data?.plans ? data.plans : [data])
            if (data?.id) setGrantPlanId(data.id)
            else if (Array.isArray(data) && data.length > 0) setGrantPlanId(data[0].id)
            else if (data?.plans?.length > 0) setGrantPlanId(data.plans[0].id)
        } catch (_) {
            // Plans may not load if no active plans
        }
    }

    const handleGrant = async (e) => {
        e.preventDefault()
        setGrantLoading(true)
        setGrantError(null)
        setGrantSuccess(null)
        try {
            const result = await settingsApi.grantSubscription(grantEmail, grantPlanId, grantMonths)
            setGrantSuccess(`Granted to ${result.parent_name || result.parent_email}. Expires: ${new Date(result.expires_at).toLocaleDateString()}`)
            setGrantEmail('')
            await loadSubscriptions()
        } catch (err) {
            setGrantError(err.response?.data?.detail || 'Failed to grant subscription')
        } finally {
            setGrantLoading(false)
        }
    }

    const handleExtend = async (id, months) => {
        setActionLoadingId(id)
        try {
            const result = await settingsApi.extendSubscription(id, months)
            await loadSubscriptions()
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to extend subscription')
        } finally {
            setActionLoadingId(null)
        }
    }

    const handleCancel = async (id) => {
        if (!window.confirm('Are you sure you want to cancel this subscription? The parent will lose access instantly.')) return

        setActionLoadingId(id)
        try {
            await settingsApi.cancelSubscription(id)
            await loadSubscriptions()
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to cancel subscription')
        } finally {
            setActionLoadingId(null)
        }
    }

    const getStatusBadge = (status) => {
        switch (status) {
            case 'active':
                return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 border border-green-200">Active</span>
            case 'expired':
                return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 border border-red-200">Expired</span>
            case 'pending':
                return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 border border-yellow-200">Pending</span>
            case 'cancelled':
            default:
                return <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 border border-gray-200">Cancelled</span>
        }
    }

    // Filter and Search logic
    const filteredSubs = subscriptions.filter((sub) => {
        if (activeTab === 'Active' && sub.status !== 'active') return false
        if (activeTab === 'Expired' && sub.status !== 'expired') return false
        if (activeTab === 'Pending' && sub.status !== 'pending') return false

        if (searchQuery) {
            const query = searchQuery.toLowerCase()
            const nameMatch = (sub.parent_name || '').toLowerCase().includes(query)
            return nameMatch
        }

        return true
    })

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Subscription Management</h1>
                    <p className="text-sm text-gray-500 mt-1">View and manage parent access. {subscriptions.length} total subscription{subscriptions.length !== 1 ? 's' : ''}.</p>
                </div>

                <div className="flex gap-3">
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"></path></svg>
                        </div>
                        <input
                            type="text"
                            placeholder="Search parent..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:w-64"
                        />
                    </div>
                    <button
                        onClick={() => setShowGrant(!showGrant)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
                        Grant Access
                    </button>
                    <button
                        onClick={loadSubscriptions}
                        className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {/* Grant Access Form */}
            {showGrant && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-4">Grant Subscription Access</h3>
                    <form onSubmit={handleGrant} className="flex flex-wrap items-end gap-4">
                        <div className="flex-1 min-w-[200px]">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Parent Email</label>
                            <input
                                type="email"
                                required
                                value={grantEmail}
                                onChange={(e) => setGrantEmail(e.target.value)}
                                placeholder="parent@email.com"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                        <div className="w-48">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                            <select
                                value={grantPlanId}
                                onChange={(e) => setGrantPlanId(Number(e.target.value))}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500 bg-white"
                            >
                                {plans.map(p => (
                                    <option key={p.id} value={p.id}>{p.name} — ₹{p.price_inr}</option>
                                ))}
                                {plans.length === 0 && <option value="">No plans</option>}
                            </select>
                        </div>
                        <div className="w-32">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
                            <div className="flex items-center gap-1">
                                <input
                                    type="number"
                                    min={1}
                                    max={24}
                                    value={grantMonths}
                                    onChange={(e) => setGrantMonths(Number(e.target.value))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
                                />
                                <span className="text-sm text-gray-500 whitespace-nowrap">months</span>
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={grantLoading || !grantEmail || !grantPlanId}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {grantLoading ? 'Granting...' : 'Grant Access'}
                        </button>
                    </form>
                    {grantError && (
                        <div className="mt-3 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{grantError}</div>
                    )}
                    {grantSuccess && (
                        <div className="mt-3 text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">✅ {grantSuccess}</div>
                    )}
                </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    {['All', 'Active', 'Expired', 'Pending'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`
                whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }
              `}
                        >
                            {tab}
                            {tab === 'All' && subscriptions.length > 0 && (
                                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">{subscriptions.length}</span>
                            )}
                            {tab === 'Active' && (
                                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-600">
                                    {subscriptions.filter(s => s.status === 'active').length}
                                </span>
                            )}
                        </button>
                    ))}
                </nav>
            </div>

            {error ? (
                <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
                    {error}
                </div>
            ) : isLoading ? (
                <div className="flex justify-center items-center py-20">
                    <div className="animate-spin flex-shrink-0 h-8 w-8 text-blue-600 border-4 border-current border-t-transparent rounded-full" role="status"></div>
                </div>
            ) : filteredSubs.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-xl border border-gray-200 border-dashed">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No subscriptions</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        {subscriptions.length === 0
                            ? 'No parent has subscribed yet. Use "Grant Access" to create one manually.'
                            : 'No records found matching your current filters.'}
                    </p>
                    {subscriptions.length === 0 && (
                        <button
                            onClick={() => setShowGrant(true)}
                            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
                        >
                            Grant First Subscription
                        </button>
                    )}
                </div>
            ) : (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Parent</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expiry</th>
                                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredSubs.map((sub) => (
                                    <tr key={sub.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">{sub.parent_name || 'Unknown'}</div>
                                            <div className="text-sm text-gray-500 font-mono text-xs">{sub.parent_id?.split('-')[0]}...</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{sub.plan_name || 'Standard'}</div>
                                            <div className="text-sm text-gray-500">₹{sub.amount_paid_inr || 0}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(sub.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {sub.started_at ? new Date(sub.started_at).toLocaleDateString() : 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {sub.expires_at ? new Date(sub.expires_at).toLocaleDateString() : 'N/A'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">

                                            {actionLoadingId === sub.id ? (
                                                <span className="text-gray-400">Processing...</span>
                                            ) : (
                                                <div className="flex justify-end gap-2">
                                                    {(sub.status === 'active' || sub.status === 'expired') && (
                                                        <>
                                                            <button onClick={() => handleExtend(sub.id, 1)} className="text-blue-600 hover:text-blue-900 bg-blue-50 px-2 py-1 rounded text-xs font-medium">
                                                                +1M
                                                            </button>
                                                            <button onClick={() => handleExtend(sub.id, 3)} className="text-blue-600 hover:text-blue-900 bg-blue-50 px-2 py-1 rounded text-xs font-medium">
                                                                +3M
                                                            </button>
                                                        </>
                                                    )}
                                                    {sub.status === 'active' && (
                                                        <button onClick={() => handleCancel(sub.id)} className="text-red-600 hover:text-red-900 bg-red-50 px-2 py-1 rounded text-xs font-medium ml-2">
                                                            Cancel
                                                        </button>
                                                    )}
                                                </div>
                                            )}

                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
