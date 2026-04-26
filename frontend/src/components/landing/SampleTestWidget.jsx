import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { CheckCircle2, XCircle, ArrowRight } from 'lucide-react'
import { sampleQuestions } from '@/data/examData'
import FadeInSection from './FadeInSection'

const TABS = [
  { id: 'scholarship', label: 'Scholarship' },
  { id: 'banking', label: 'Banking' },
  { id: 'ssc', label: 'SSC' },
]

const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function SampleTestWidget() {
  const [activeTab, setActiveTab] = useState('scholarship')
  const [selected, setSelected] = useState(null)

  const q = sampleQuestions[activeTab]

  const handleTabChange = (id) => {
    setActiveTab(id)
    setSelected(null)
  }

  const handleSelect = (idx) => {
    if (selected !== null) return // already answered
    setSelected(idx)
  }

  const getOptionStyle = (idx) => {
    if (selected === null) {
      return {
        border: '1.5px solid #E5E7EB',
        background: 'white',
        color: '#374151',
      }
    }
    if (idx === q.correct) {
      return { border: '1.5px solid #10B981', background: '#F0FDF4', color: '#065F46' }
    }
    if (idx === selected && idx !== q.correct) {
      return { border: '1.5px solid #EF4444', background: '#FEF2F2', color: '#991B1B' }
    }
    return { border: '1.5px solid #E5E7EB', background: 'white', color: '#9CA3AF' }
  }

  return (
    <section className="py-20 lg:py-28 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-12">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#EEF2FF', color: '#1B3A6B' }}>
            Try It Free
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            Try a Free Question Right Now
          </h2>
          <p className="text-gray-500">
            No signup needed. Pick an exam category and attempt a sample question.
          </p>
        </FadeInSection>

        <FadeInSection delay={0.1}>
          <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
            {/* Tab bar */}
            <div className="flex border-b border-gray-100">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleTabChange(t.id)}
                  className="flex-1 py-4 text-sm font-semibold transition-all cursor-pointer relative"
                  style={{
                    color: activeTab === t.id ? '#1B3A6B' : '#9CA3AF',
                    background: activeTab === t.id ? '#F8FAFC' : 'white',
                  }}
                >
                  {t.label}
                  {activeTab === t.id && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5"
                      style={{ background: '#FF6B35' }}
                    />
                  )}
                </button>
              ))}
            </div>

            <div className="p-6 sm:p-8">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.25 }}
                >
                  {/* Question */}
                  <div className="mb-6">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                      Question
                    </div>
                    <p className="text-base sm:text-lg font-medium text-gray-800 leading-relaxed">
                      {q.question}
                    </p>
                  </div>

                  {/* Options */}
                  <div className="space-y-3 mb-6">
                    {q.options.map((opt, idx) => {
                      const style = getOptionStyle(idx)
                      return (
                        <motion.button
                          key={idx}
                          onClick={() => handleSelect(idx)}
                          whileHover={selected === null ? { scale: 1.01 } : {}}
                          whileTap={selected === null ? { scale: 0.99 } : {}}
                          className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-left transition-all cursor-pointer"
                          style={style}
                        >
                          <span
                            className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
                            style={{
                              background: idx === q.correct && selected !== null
                                ? '#10B981'
                                : idx === selected && idx !== q.correct
                                ? '#EF4444'
                                : '#F3F4F6',
                              color: (idx === q.correct && selected !== null) || (idx === selected && idx !== q.correct)
                                ? 'white'
                                : '#374151',
                            }}
                          >
                            {OPTION_LABELS[idx]}
                          </span>
                          <span className="text-sm font-medium">{opt}</span>
                          {selected !== null && idx === q.correct && (
                            <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto flex-shrink-0" />
                          )}
                          {selected !== null && idx === selected && idx !== q.correct && (
                            <XCircle className="w-4 h-4 text-red-400 ml-auto flex-shrink-0" />
                          )}
                        </motion.button>
                      )
                    })}
                  </div>

                  {/* Explanation */}
                  <AnimatePresence>
                    {selected !== null && (
                      <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 8 }}
                        className="rounded-xl p-4 mb-6"
                        style={{ background: '#F0FDF4', borderLeft: '3px solid #10B981' }}
                      >
                        <div className="text-xs font-bold text-green-700 mb-1 uppercase tracking-wide">
                          Explanation
                        </div>
                        <p className="text-sm text-green-800 leading-relaxed">{q.explanation}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </AnimatePresence>

              {/* CTA */}
              <div className="text-center">
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-white text-sm font-semibold cursor-pointer hover:opacity-90 transition-opacity"
                  style={{ background: '#1B3A6B' }}
                >
                  Attempt Full Free Test
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </FadeInSection>
      </div>
    </section>
  )
}
