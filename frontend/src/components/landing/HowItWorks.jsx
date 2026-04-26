import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import { Search, Brain, TrendingUp } from 'lucide-react'
import FadeInSection from './FadeInSection'

const STEPS = [
  {
    step: '01',
    icon: Search,
    title: 'Choose Your Exam',
    desc: 'Browse the catalog and select the exam you\'re preparing for. School exams? A parent creates an account and manages child profiles.',
    color: '#1B3A6B',
  },
  {
    step: '02',
    icon: Brain,
    title: 'Take Adaptive Tests',
    desc: 'Our AI adjusts question difficulty to match your current level — harder when you\'re doing well, targeted review when you need it.',
    color: '#FF6B35',
  },
  {
    step: '03',
    icon: TrendingUp,
    title: 'Track & Improve',
    desc: 'Detailed analytics show exactly which topics to revise. Wrong answer reviews explain every mistake. Watch your score climb.',
    color: '#10B981',
  },
]

export default function HowItWorks() {
  const lineRef = useRef(null)
  const lineInView = useInView(lineRef, { once: true })

  return (
    <section className="py-20 lg:py-28" style={{ background: '#F8FAFC' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-16">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#FFF0EA', color: '#FF6B35' }}>
            How It Works
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            Simple. Smart. Effective.
          </h2>
          <p className="text-gray-500 text-lg max-w-xl mx-auto">
            From signup to your first test in under 3 minutes
          </p>
        </FadeInSection>

        <div className="relative">
          {/* Connecting line — desktop */}
          <div ref={lineRef} className="hidden lg:block absolute top-10 left-[16.66%] right-[16.66%] h-0.5 bg-gray-200 z-0">
            <motion.div
              className="h-full rounded-full"
              style={{ background: 'linear-gradient(90deg, #1B3A6B, #FF6B35, #10B981)' }}
              initial={{ scaleX: 0, originX: 0 }}
              animate={lineInView ? { scaleX: 1 } : { scaleX: 0 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1], delay: 0.4 }}
            />
          </div>

          <div className="grid lg:grid-cols-3 gap-8 lg:gap-6 relative z-10">
            {STEPS.map((s, i) => {
              const Icon = s.icon
              return (
                <FadeInSection key={s.step} delay={i * 0.15}>
                  <div className="text-center">
                    {/* Circle icon */}
                    <div className="flex justify-center mb-6">
                      <div
                        className="w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg relative"
                        style={{ background: s.color }}
                      >
                        <Icon className="w-9 h-9 text-white" />
                        <span
                          className="absolute -top-2 -right-2 w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold text-white"
                          style={{ background: '#0F2040' }}
                        >
                          {s.step}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-xl font-bold mb-3" style={{ color: '#1B3A6B' }}>
                      {s.title}
                    </h3>
                    <p className="text-gray-500 leading-relaxed text-sm max-w-xs mx-auto">
                      {s.desc}
                    </p>
                  </div>
                </FadeInSection>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
