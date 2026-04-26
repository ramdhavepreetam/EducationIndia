import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Calendar, BookOpen, ArrowRight, CheckCircle2 } from 'lucide-react'
import { featuredExam } from '@/data/examData'
import FadeInSection from './FadeInSection'

const SUBJECT_COLORS = {
  Mathematics: '#1B3A6B',
  English: '#FF6B35',
  Marathi: '#8B5CF6',
  'General Knowledge': '#10B981',
  'Intelligence Test': '#F59E0B',
}

// Donut chart segments — MSCE exam pattern breakdown
const DONUT_SEGMENTS = [
  { label: 'Mathematics', pct: 67, color: '#1B3A6B' },   // 50/75 questions
  { label: 'English', pct: 33, color: '#FF6B35' },        // 25/75 questions
]

function DonutChart({ segments }) {
  const size = 160
  const r = 56
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r

  let offset = 0
  const arcs = segments.map((s) => {
    const dash = (s.pct / 100) * circumference
    const arc = { ...s, strokeDasharray: `${dash} ${circumference - dash}`, strokeDashoffset: circumference - offset }
    offset += dash
    return arc
  })

  return (
    <div className="relative flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#F3F4F6" strokeWidth="20" />
        {arcs.map((arc, i) => (
          <circle
            key={i}
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={arc.color}
            strokeWidth="20"
            strokeDasharray={arc.strokeDasharray}
            strokeDashoffset={arc.strokeDashoffset}
            strokeLinecap="round"
          />
        ))}
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-extrabold" style={{ color: '#1B3A6B' }}>75</div>
        <div className="text-xs text-gray-400">Questions</div>
      </div>
    </div>
  )
}

export default function ExamSpotlight() {
  const [activeClass, setActiveClass] = useState('Class 5')
  const exam = featuredExam
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleNotify = (e) => {
    e.preventDefault()
    if (email.trim()) setSubmitted(true)
  }

  return (
    <section id="exam-spotlight" className="py-20 lg:py-28" style={{ background: '#F8FAFC' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="mb-14">
          <div className="inline-flex items-center gap-2 text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#FFF0EA', color: '#FF6B35' }}>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Currently Live
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold" style={{ color: '#1B3A6B' }}>
            Maharashtra Scholarship Exam
          </h2>
        </FadeInSection>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left — content */}
          <FadeInSection>
            {/* Class tabs */}
            <div className="flex gap-2 mb-8">
              {exam.classOptions.map((cls) => (
                <button
                  key={cls}
                  onClick={() => setActiveClass(cls)}
                  className="px-5 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer"
                  style={
                    activeClass === cls
                      ? { background: '#1B3A6B', color: 'white' }
                      : { background: 'white', color: '#6B7280', border: '1px solid #E5E7EB' }
                  }
                >
                  {cls}
                </button>
              ))}
            </div>

            {/* Syllabus pills */}
            <div className="mb-8">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Syllabus Coverage
              </h3>
              <div className="flex flex-wrap gap-2">
                {exam.syllabus.map((sub) => (
                  <span
                    key={sub}
                    className="px-3 py-1.5 rounded-full text-sm font-medium text-white"
                    style={{ background: SUBJECT_COLORS[sub] ?? '#64748B' }}
                  >
                    {sub}
                  </span>
                ))}
              </div>
            </div>

            {/* Key dates */}
            <div className="space-y-3 mb-8">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="text-gray-600">
                  Exam month: <strong>{exam.examMonth}</strong>
                </span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <BookOpen className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="text-gray-600">{exam.registrationInfo}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                <span className="text-gray-600">
                  Content available in <strong>English & Marathi</strong>
                </span>
              </div>
            </div>

            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl text-white font-semibold shadow-lg hover:shadow-xl transition-all hover:scale-[1.02] cursor-pointer"
              style={{ background: '#FF6B35' }}
            >
              Start Practicing Now
              <ArrowRight className="w-4 h-4" />
            </Link>
          </FadeInSection>

          {/* Right — visual */}
          <FadeInSection delay={0.15}>
            <div className="bg-white rounded-3xl p-8 shadow-lg border border-gray-100">
              {/* Donut chart */}
              <div className="flex flex-col sm:flex-row items-center gap-8 mb-8">
                <DonutChart segments={DONUT_SEGMENTS} />
                <div className="flex flex-col gap-3">
                  <div className="text-sm font-semibold text-gray-500 mb-1">Paper I Breakdown</div>
                  {DONUT_SEGMENTS.map((s) => (
                    <div key={s.label} className="flex items-center gap-2 text-sm">
                      <span className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ background: s.color }} />
                      <span className="text-gray-600">{s.label}</span>
                      <span className="font-bold ml-auto" style={{ color: s.color }}>
                        {s.pct}%
                      </span>
                    </div>
                  ))}
                  <div className="text-xs text-gray-400 mt-1">75 Qs · 150 marks · 90 min</div>
                </div>
              </div>

              {/* Exam facts */}
              <div className="rounded-2xl p-5 text-center"
                   style={{ background: 'linear-gradient(135deg, #1B3A6B, #2351A0)' }}>
                <div className="text-4xl font-extrabold text-white mb-1">2025</div>
                <div className="text-blue-200 text-sm">
                  MSCE Scholarship papers available — practice at your own pace
                </div>
              </div>
            </div>
          </FadeInSection>
        </div>

        {/* Email notify form */}
        <FadeInSection delay={0.2} className="mt-16 text-center">
          <p className="text-gray-500 mb-4 text-sm">
            More exams launching soon —
          </p>
          {submitted ? (
            <div className="inline-flex items-center gap-2 text-green-600 font-semibold">
              <CheckCircle2 className="w-5 h-5" />
              You\'re on the list! We\'ll notify you.
            </div>
          ) : (
            <form onSubmit={handleNotify} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:border-transparent"
                style={{ '--tw-ring-color': '#FF6B35' }}
              />
              <button
                type="submit"
                className="px-6 py-3 rounded-xl text-white text-sm font-semibold cursor-pointer hover:opacity-90 transition-opacity"
                style={{ background: '#1B3A6B' }}
              >
                Notify Me
              </button>
            </form>
          )}
        </FadeInSection>
      </div>
    </section>
  )
}
