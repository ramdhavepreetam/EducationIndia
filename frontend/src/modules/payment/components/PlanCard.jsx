import React from 'react'

export const PlanCard = ({ plan }) => {
    if (!plan) return null

    return (
        <div className="bg-white border rounded-lg shadow-sm overflow-hidden flex flex-col h-full transform transition hover:-translate-y-1 hover:shadow-md">
            <div className="px-6 py-8 flex-1">
                <h3 className="text-xl font-bold text-gray-900 text-center mb-2">Full Access</h3>
                <p className="text-center text-gray-500 mb-6">Unlock all premium features</p>

                <div className="flex items-baseline justify-center mb-6">
                    <span className="text-4xl font-extrabold text-blue-600">₹{plan.price_inr}</span>
                    <span className="text-xl font-medium text-gray-500 ml-1">/{plan.duration_months} mo</span>
                </div>

                <ul className="space-y-4 mb-8">
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">All available exams & papers</span>
                    </li>
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Unlimited exam attempts</span>
                    </li>
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Detailed section-wise scores</span>
                    </li>
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">In-depth topic breakdown</span>
                    </li>
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Downloadable PDF reports</span>
                    </li>
                    <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700">Personalized recommendations</span>
                    </li>
                </ul>
            </div>

            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                <p className="text-xs text-center text-gray-500">
                    One-time payment. Covers all children in your account.
                </p>
            </div>
        </div>
    )
}
