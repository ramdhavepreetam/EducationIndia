import { useState } from 'react'

const TopicBar = ({ topic, language, colorClass, bgClass }) => {
  const name = language === 'mr' && topic.topic_name_mr
    ? topic.topic_name_mr
    : topic.topic_name_en

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-700 font-medium">{name}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {topic.attempts_count} attempt{topic.attempts_count !== 1 ? 's' : ''}
          </span>
          <span className={`font-semibold ${colorClass}`}>
            {topic.avg_percentage}%
          </span>
        </div>
      </div>
      <div className={`w-full ${bgClass} rounded-full h-2`}>
        <div
          className={`${colorClass.replace('text', 'bg')} h-2 rounded-full
                      transition-all duration-500`}
          style={{ width: `${Math.min(topic.avg_percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

const ChildWeakTopics = ({ weakTopics, strongTopics, language = 'en' }) => {
  const [showStrong, setShowStrong] = useState(false)

  if (weakTopics.length === 0 && strongTopics.length === 0) {
    return (
      <div className="bg-gray-50 rounded-2xl p-6 text-center">
        <p className="text-gray-400 text-sm">
          Topic data will appear after exams are taken.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">

      {/* Weak topics */}
      {weakTopics.length > 0 ? (
        <div className="bg-orange-50 border border-orange-100
                        rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-orange-500">⚠</span>
            <h3 className="font-semibold text-orange-800">
              Needs Attention
            </h3>
            <span className="ml-auto text-xs bg-orange-100 text-orange-600
                             px-2 py-0.5 rounded-full">
              {weakTopics.length} topic{weakTopics.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="space-y-4">
            {weakTopics.map(topic => (
              <TopicBar
                key={topic.topic_id}
                topic={topic}
                language={language}
                colorClass="text-orange-500"
                bgClass="bg-orange-100"
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-green-50 border border-green-100
                        rounded-2xl p-4 flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <p className="text-green-700 text-sm font-medium">
            No weak topics — great performance!
          </p>
        </div>
      )}

      {/* Strong topics — collapsed by default */}
      {strongTopics.length > 0 && (
        <div className="bg-green-50 border border-green-100 rounded-2xl">
          <button
            onClick={() => setShowStrong(prev => !prev)}
            className="w-full flex items-center justify-between p-4
                       text-green-800 font-medium text-sm"
          >
            <div className="flex items-center gap-2">
              <span>✓</span>
              <span>Strong Areas</span>
              <span className="text-xs bg-green-100 text-green-600
                               px-2 py-0.5 rounded-full">
                {strongTopics.length}
              </span>
            </div>
            <span className="text-green-400">
              {showStrong ? '▲' : '▼'}
            </span>
          </button>

          {showStrong && (
            <div className="px-6 pb-6 space-y-4">
              {strongTopics.map(topic => (
                <TopicBar
                  key={topic.topic_id}
                  topic={topic}
                  language={language}
                  colorClass="text-green-600"
                  bgClass="bg-green-100"
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ChildWeakTopics
