import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  GraduationCap, Landmark, Building2, Zap, Microscope, Calculator,
  ArrowRight, Bell
} from 'lucide-react'
import { exams } from '@/data/examData'
import FadeInSection from './FadeInSection'

const ICON_MAP = {
  GraduationCap, Landmark, Building2, Zap, Microscope, Calculator,
}

export default function ExamCategories() {
  const [hoveredId, setHoveredId] = useState(null)
  const [notifyId, setNotifyId] = useState(null)

  const handleNotify = (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    setNotifyId(id)
    setTimeout(() => setNotifyId(null), 2000)
  }

  const scrollToSpotlight = () => {
    document.querySelector('#exam-spotlight')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section id="exams" className="py-20 lg:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-14">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#EEF2FF', color: '#1B3A6B' }}>
            Exam Categories
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            One Platform. Every Exam.
          </h2>
          <p className="text-gray-500 text-lg max-w-2xl mx-auto">
            From school scholarships to government exams — ScholarPath covers them all.
          </p>
        </FadeInSection>

        {/* Cards grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {exams.map((exam, i) => {
            const Icon = ICON_MAP[exam.icon] ?? GraduationCap
            const isLive = exam.status === 'live'
            const isHovered = hoveredId === exam.id
            const didNotify = notifyId === exam.id

            return (
              <FadeInSection key={exam.id} delay={i * 0.08}>
                <motion.div
                  onHoverStart={() => setHoveredId(exam.id)}
                  onHoverEnd={() => setHoveredId(null)}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.2 }}
                  className="relative rounded-2xl border p-6 cursor-pointer h-full flex flex-col"
                  style={{
                    borderColor: isHovered ? exam.color : '#E5E7EB',
                    boxShadow: isHovered
                      ? `0 8px 24px ${exam.color}22`
                      : '0 1px 3px rgba(0,0,0,0.06)',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                >
                  {/* Status badge */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center"
                         style={{ background: `${exam.color}18` }}>
                      <Icon className="w-6 h-6" style={{ color: exam.color }} />
                    </div>
                    {isLive ? (
                      <span className="flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full text-white"
                            style={{ background: '#FF6B35' }}>
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                        LIVE
                      </span>
                    ) : (
                      <span className="text-xs font-medium px-2.5 py-1 rounded-full"
                            style={{ background: '#F3F4F6', color: '#6B7280' }}>
                        Coming Soon
                      </span>
                    )}
                  </div>

                  <h3 className="font-bold text-lg mb-1" style={{ color: '#1B3A6B' }}>
                    {exam.name}
                  </h3>
                  <p className="text-sm text-gray-500 mb-4 flex-1">
                    {exam.tagline}
                  </p>

                  {isLive && (
                    <p className="text-xs font-medium text-gray-400 mb-4">
                      {exam.testsAvailable} Tests Available
                    </p>
                  )}

                  {/* Action */}
                  {isLive ? (
                    <button
                      onClick={scrollToSpotlight}
                      className="flex items-center gap-1.5 text-sm font-semibold cursor-pointer group"
                      style={{ color: exam.color }}
                    >
                      Explore
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                  ) : (
                    <button
                      onClick={(e) => handleNotify(e, exam.id)}
                      className="flex items-center gap-1.5 text-sm font-medium cursor-pointer text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <Bell className="w-3.5 h-3.5" />
                      {didNotify ? '✓ You\'ll be notified!' : 'Notify Me'}
                    </button>
                  )}
                </motion.div>
              </FadeInSection>
            )
          })}
        </div>
      </div>
    </section>
  )
}
