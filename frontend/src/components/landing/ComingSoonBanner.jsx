import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, CheckCircle2 } from 'lucide-react'
import FadeInSection from './FadeInSection'

export default function ComingSoonBanner() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (email.trim()) setSubmitted(true)
  }

  return (
    <section className="py-16 overflow-hidden"
             style={{ background: 'linear-gradient(135deg, #FF6B35 0%, #E5501A 100%)' }}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <FadeInSection>
          <div className="text-4xl mb-4">🚀</div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">
            Banking & Government Exams Launching Q3 2026
          </h2>
          <p className="text-orange-100 mb-2">
            IBPS PO, SBI Clerk, MPSC, UPSC, SSC CGL — all coming to ScholarPath.
          </p>
          <div className="flex items-center justify-center gap-1.5 text-orange-200 text-sm mb-8">
            <Bell className="w-3.5 h-3.5" />
            847 people already waiting
          </div>

          {submitted ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center gap-2 bg-white/20 backdrop-blur rounded-2xl px-7 py-4 text-white font-semibold"
            >
              <CheckCircle2 className="w-5 h-5" />
              You're on the list! We'll email you when it goes live.
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                required
                className="flex-1 px-5 py-3.5 rounded-xl text-sm text-gray-800 placeholder-gray-400 border-0 focus:outline-none focus:ring-2 focus:ring-white"
              />
              <button
                type="submit"
                className="px-6 py-3.5 rounded-xl font-bold text-sm cursor-pointer transition-all hover:scale-[1.02]"
                style={{ background: '#1B3A6B', color: 'white' }}
              >
                Notify Me When Live
              </button>
            </form>
          )}
        </FadeInSection>
      </div>
    </section>
  )
}
