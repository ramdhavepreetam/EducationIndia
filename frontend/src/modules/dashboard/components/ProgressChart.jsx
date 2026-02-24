import { useTranslation } from 'react-i18next'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export const ProgressChart = ({ attempts }) => {
    const { t } = useTranslation()

    // Filter to submitted attempts with scores, reverse so it's chronological (oldest to newest)
    const chartData = attempts
        ?.filter(a => a.status === 'submitted' && a.percentage !== null)
        ?.sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at))
        ?.map((a, idx) => ({
            name: `${t('dashboard.attempt', 'Attempt')} ${idx + 1}`,
            score: a.percentage
        })) || []

    if (chartData.length < 2) {
        return (
            <div className="bg-white p-6 rounded-xl border border-surface-200 shadow-sm h-64 flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 bg-surface-100 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                </div>
                <p className="text-surface-600 font-medium">{t('dashboard.notEnoughData', 'Not enough data for chart')}</p>
                <p className="text-surface-400 text-sm mt-1">{t('dashboard.completeMore', 'Complete at least two exams to see your progress trend.')}</p>
            </div>
        )
    }

    return (
        <div className="bg-white p-6 rounded-xl border border-surface-200 shadow-sm h-80">
            <h3 className="font-bold text-surface-900 mb-6">{t('dashboard.progressTrend', 'Progress Trend')}</h3>
            <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis
                            dataKey="name"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748B', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            domain={[0, 100]}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748B', fontSize: 12 }}
                            tickFormatter={(value) => `${value}%`}
                        />
                        <Tooltip
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            formatter={(value) => [`${value}%`, t('dashboard.score', 'Score')]}
                        />
                        <Line
                            type="monotone"
                            dataKey="score"
                            stroke="#2563EB"
                            strokeWidth={3}
                            dot={{ fill: '#2563EB', strokeWidth: 2, r: 4 }}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}
