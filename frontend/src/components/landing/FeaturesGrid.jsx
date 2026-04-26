import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  ClipboardList, Target, XCircle, BarChart3, Users, WifiOff
} from 'lucide-react'
import FadeInSection from './FadeInSection'

const FEATURES = [
  {
    icon: ClipboardList,
    title: 'Exam-Specific Mock Tests',
    desc: 'Curated tests matching the exact exam pattern, marks, and time limits.',
    color: '#1B3A6B',
  },
  {
    icon: Target,
    title: 'Adaptive Difficulty',
    desc: 'Gets harder as you improve. Our AI ensures you\'re always challenged at the right level.',
    color: '#FF6B35',
  },
  {
    icon: XCircle,
    title: 'Wrong Answer Review',
    desc: 'Learn exactly where and why you went wrong — with explanations in English and Marathi.',
    color: '#EF4444',
  },
  {
    icon: BarChart3,
    title: 'Deep Analytics',
    desc: 'Subject, chapter, and time-based performance breakdown. See what to study next.',
    color: '#8B5CF6',
  },
  {
    icon: Users,
    title: 'Parent/Guardian Dashboard',
    desc: 'For school exam categories — monitor your child\'s progress, scores, and weak areas.',
    color: '#10B981',
  },
  {
    icon: WifiOff,
    title: 'Works Offline',
    desc: 'Download tests and attempt them anywhere — on the train, at school, no internet needed.',
    color: '#F59E0B',
  },
]

export default function FeaturesGrid() {
  const [hovered, setHovered] = useState(null)

  return (
    <section id="features" className="py-20 lg:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-14">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#EEF2FF', color: '#1B3A6B' }}>
            Features
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            Everything You Need to Succeed
          </h2>
          <p className="text-gray-500 text-lg max-w-2xl mx-auto">
            Built specifically for Indian competitive exams, with features that actually make a difference.
          </p>
        </FadeInSection>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => {
            const Icon = f.icon
            const isHovered = hovered === i
            return (
              <FadeInSection key={f.title} delay={i * 0.07}>
                <motion.div
                  onHoverStart={() => setHovered(i)}
                  onHoverEnd={() => setHovered(null)}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.2 }}
                  className="p-6 rounded-2xl border-l-4 border-t border-r border-b transition-all h-full"
                  style={{
                    borderLeftColor: isHovered ? f.color : '#E5E7EB',
                    borderTopColor: '#E5E7EB',
                    borderRightColor: '#E5E7EB',
                    borderBottomColor: '#E5E7EB',
                    boxShadow: isHovered
                      ? `0 8px 24px ${f.color}18`
                      : '0 1px 3px rgba(0,0,0,0.05)',
                    background: isHovered ? `${f.color}06` : 'white',
                    transition: 'all 0.25s',
                  }}
                >
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center mb-4"
                    style={{ background: `${f.color}14` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: f.color }} />
                  </div>
                  <h3 className="font-bold text-base mb-2" style={{ color: '#1B3A6B' }}>
                    {f.title}
                  </h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
                </motion.div>
              </FadeInSection>
            )
          })}
        </div>
      </div>
    </section>
  )
}
