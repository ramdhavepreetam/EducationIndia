import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer
} from 'recharts'

const EXAM_COLORS = {
  default: '#3B82F6',
  second:  '#10B981',
  third:   '#F59E0B',
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded-xl
                    shadow-lg p-3 text-sm">
      <p className="font-medium text-gray-700 mb-1">{label}</p>
      {payload.map(entry => (
        <div key={entry.name}
             className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full"
               style={{ backgroundColor: entry.color }} />
          <span className="text-gray-600">{entry.name}:</span>
          <span className="font-semibold">{entry.value}%</span>
        </div>
      ))}
    </div>
  )
}

const ChildProgressChart = ({ attempts }) => {
  const submitted = attempts.filter(a => a.status === 'submitted')

  if (submitted.length < 2) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100
                      shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-3">
          Score Progress
        </h3>
        <div className="h-32 flex items-center justify-center
                        bg-gray-50 rounded-xl">
          <p className="text-gray-400 text-sm text-center">
            Take at least 2 exams to see<br />the progress trend
          </p>
        </div>
      </div>
    )
  }

  // Group by paper_code — each becomes a separate line
  const paperCodes = [...new Set(submitted.map(a => a.paper_code))]

  // Build chart data: one entry per attempt number per paper
  const maxAttempts = Math.max(
    ...paperCodes.map(code =>
      submitted.filter(a => a.paper_code === code).length
    )
  )

  const chartData = Array.from({ length: maxAttempts }, (_, i) => {
    const entry = { name: `Attempt ${i + 1}` }
    paperCodes.forEach(code => {
      const paperAttempts = submitted
        .filter(a => a.paper_code === code)
        .sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at))
      if (paperAttempts[i]) {
        entry[`Paper ${code}`] = parseFloat(paperAttempts[i].percentage) || 0
      }
    })
    return entry
  })

  return (
    <div className="bg-white rounded-2xl border border-gray-100
                    shadow-sm p-6">
      <h3 className="font-semibold text-gray-900 mb-4">
        Score Progress
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}
                   margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12, fill: '#9CA3AF' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {paperCodes.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }}
            />
          )}

          {/* Grade reference lines */}
          <ReferenceLine y={90} stroke="#10B981" strokeDasharray="4 4"
            label={{ value: 'Excellent', position: 'right',
                     fontSize: 10, fill: '#10B981' }} />
          <ReferenceLine y={70} stroke="#3B82F6" strokeDasharray="4 4"
            label={{ value: 'Good', position: 'right',
                     fontSize: 10, fill: '#3B82F6' }} />
          <ReferenceLine y={50} stroke="#F59E0B" strokeDasharray="4 4"
            label={{ value: 'Average', position: 'right',
                     fontSize: 10, fill: '#F59E0B' }} />

          {/* One line per paper */}
          {paperCodes.map((code, idx) => (
            <Line
              key={code}
              type="monotone"
              dataKey={`Paper ${code}`}
              stroke={Object.values(EXAM_COLORS)[idx] || '#6B7280'}
              strokeWidth={2.5}
              dot={{ r: 4, strokeWidth: 2 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ChildProgressChart
