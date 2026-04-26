import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Play } from 'lucide-react'

const EXAM_PILLS = [
  { label: 'MSCE Scholarship', emoji: '🎓', live: true },
  { label: 'Banking', emoji: '🏦', live: false },
  { label: 'UPSC/MPSC', emoji: '📋', live: false },
  { label: 'SSC', emoji: '⚡', live: false },
  { label: 'NEET', emoji: '🔬', live: false },
  { label: 'JEE', emoji: '📐', live: false },
]

const TRUST_BADGES = [
  { value: '2', label: 'MSCE Papers (2025)' },
  { value: '150', label: 'Questions per Paper' },
  { value: 'EN + MR', label: 'Bilingual' },
]

const stagger = {
  animate: { transition: { staggerChildren: 0.12 } },
}
const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
}

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center pt-16 overflow-hidden"
             style={{ background: 'linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 50%, #FFF7F4 100%)' }}>

      {/* Background decorative blobs */}
      <div className="absolute top-20 right-0 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none"
           style={{ background: '#1B3A6B' }} />
      <div className="absolute bottom-10 left-0 w-80 h-80 rounded-full opacity-10 blur-3xl pointer-events-none"
           style={{ background: '#FF6B35' }} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-16 lg:py-0">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* Left content */}
          <motion.div variants={stagger} initial="initial" animate="animate">
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 text-sm font-semibold px-4 py-1.5 rounded-full mb-6"
                    style={{ background: '#FFF0EA', color: '#FF6B35' }}>
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Live: MSCE Scholarship Exam
              </span>
            </motion.div>

            <motion.h1
              variants={fadeUp}
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight mb-6"
              style={{ color: '#1B3A6B' }}
            >
              Your Shortcut to{' '}
              <span className="relative inline-block">
                <span style={{ color: '#FF6B35' }}>Exam Success</span>
                <svg className="absolute -bottom-2 left-0 w-full" height="8" viewBox="0 0 200 8" fill="none">
                  <path d="M0 6 Q50 1 100 6 Q150 11 200 6" stroke="#FF6B35" strokeWidth="2.5"
                        fill="none" strokeLinecap="round" />
                </svg>
              </span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="text-lg text-gray-600 leading-relaxed mb-8 max-w-xl"
            >
              Adaptive mock tests, real-time analytics, and smart revision — for every exam that matters.
              <br />
              <span className="text-sm text-gray-400 mt-1 block">
                परीक्षेची तयारी करा, यश मिळवा
              </span>
            </motion.p>

            {/* Exam pills */}
            <motion.div variants={fadeUp} className="mb-8">
              <div className="flex flex-wrap gap-2">
                {EXAM_PILLS.map((pill) => (
                  <span
                    key={pill.label}
                    className="inline-flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-full border transition-all cursor-default"
                    style={
                      pill.live
                        ? { background: '#FF6B35', color: 'white', borderColor: '#FF6B35' }
                        : { background: 'white', color: '#374151', borderColor: '#E5E7EB' }
                    }
                  >
                    <span>{pill.emoji}</span>
                    {pill.label}
                    {pill.live && (
                      <span className="text-xs font-bold ml-0.5">LIVE</span>
                    )}
                  </span>
                ))}
              </div>
            </motion.div>

            {/* CTAs */}
            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-4 mb-10">
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl text-white font-semibold text-base shadow-lg hover:shadow-xl transition-all hover:scale-[1.02] cursor-pointer"
                style={{ background: '#FF6B35' }}
              >
                Start Free Trial
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#exams"
                onClick={(e) => {
                  e.preventDefault()
                  document.querySelector('#exams')?.scrollIntoView({ behavior: 'smooth' })
                }}
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-base border-2 transition-all hover:bg-[#1B3A6B] hover:text-white hover:border-[#1B3A6B] cursor-pointer"
                style={{ color: '#1B3A6B', borderColor: '#1B3A6B' }}
              >
                <Play className="w-4 h-4 fill-current" />
                Explore Exams
              </a>
            </motion.div>

            {/* Trust badges */}
            <motion.div variants={fadeUp} className="flex flex-wrap gap-6">
              {TRUST_BADGES.map((b) => (
                <div key={b.label} className="flex flex-col">
                  <span className="text-2xl font-extrabold" style={{ color: '#1B3A6B' }}>
                    {b.value}
                  </span>
                  <span className="text-sm text-gray-500">{b.label}</span>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: illustration */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="relative flex items-center justify-center"
          >
            <div className="relative w-full max-w-md mx-auto">
              {/* Main illustration card */}
              <div className="rounded-3xl shadow-2xl overflow-hidden"
                   style={{ background: 'linear-gradient(135deg, #1B3A6B 0%, #2351A0 100%)' }}>
                <img
                  src="https://storage.googleapis.com/proudcity/mebanenc/uploads/2021/03/placeholder-image.png"
                  alt="Student studying with ScholarPath"
                  className="w-full h-64 object-cover opacity-20"
                />
                <div className="px-8 py-10 text-white -mt-32 relative z-10">
                  <div className="text-5xl mb-4">📚</div>
                  <div className="text-2xl font-bold mb-2">Start Practicing</div>
                  <div className="text-blue-200 text-sm mb-6">
                    1,00,000+ questions across all exam patterns
                  </div>
                  {/* Preview progress card */}
                  <div className="text-xs text-blue-300 mb-1.5 opacity-70">Preview</div>
                  <div className="bg-white/10 backdrop-blur rounded-xl p-4 mb-3">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Mathematics Progress</span>
                      <span className="font-semibold text-green-300">78%</span>
                    </div>
                    <div className="h-2 bg-white/20 rounded-full">
                      <div className="h-2 rounded-full" style={{ width: '78%', background: '#10B981' }} />
                    </div>
                  </div>
                  <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Intelligence Test</span>
                      <span className="font-semibold text-yellow-300">64%</span>
                    </div>
                    <div className="h-2 bg-white/20 rounded-full">
                      <div className="h-2 rounded-full bg-yellow-400" style={{ width: '64%' }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating badge — top right */}
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute -top-4 -right-4 bg-white rounded-2xl shadow-lg px-4 py-3 flex items-center gap-2"
              >
                <span className="text-2xl">🏆</span>
                <div>
                  <div className="text-xs text-gray-500">Example Score</div>
                  <div className="text-sm font-bold" style={{ color: '#1B3A6B' }}>148 / 150</div>
                </div>
              </motion.div>

              {/* Floating badge — bottom left */}
              <motion.div
                animate={{ y: [0, 8, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                className="absolute -bottom-4 -left-4 bg-white rounded-2xl shadow-lg px-4 py-3 flex items-center gap-2"
              >
                <span className="text-2xl">✅</span>
                <div>
                  <div className="text-xs text-gray-500">Example Activity</div>
                  <div className="text-sm font-bold" style={{ color: '#FF6B35' }}>23 this month</div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
