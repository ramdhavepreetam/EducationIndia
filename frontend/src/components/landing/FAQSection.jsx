import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Minus } from 'lucide-react'
import FadeInSection from './FadeInSection'

const FAQS = [
  {
    q: 'What exams does ScholarPath support right now?',
    a: 'Currently, ScholarPath is live for the Maharashtra MSCE Scholarship Examination for Class 5 and Class 8. This includes Paper I (English + Mathematics) and Paper II (Marathi + Intelligence Test). Banking, SSC, UPSC/MPSC, NEET, and JEE are coming in 2026.',
  },
  {
    q: 'How is ScholarPath different from other test platforms?',
    a: 'ScholarPath is built specifically for Indian exam patterns, with adaptive difficulty (tests get harder as you improve), wrong-answer explanations in both English and Marathi, and a parent dashboard for school exam monitoring. Most platforms are one-size-fits-all — we\'re exam-specific.',
  },
  {
    q: 'Is content available in Marathi or Hindi?',
    a: 'Yes! All MSCE Scholarship questions are available in both English and Marathi. You can switch between languages at any point. Hindi support is on our roadmap for government exam content (MPSC/UPSC).',
  },
  {
    q: 'How does the parent dashboard work for school exams?',
    a: 'Parents create an account, add their child\'s profile (name, class, school, medium), and can monitor all progress from a single dashboard. You can see which topics need attention, track score trends over time, and review wrong answers together.',
  },
  {
    q: 'Can I switch exam categories after subscribing?',
    a: 'Yes. Scholar plan includes 3 exam categories. Pro plan includes all categories — current and upcoming. You can switch at any time from your account settings.',
  },
  {
    q: 'Is internet required to take tests?',
    a: 'You need internet to load and start a test, but Pro plan users can download tests and attempt them offline. Responses sync automatically when you\'re back online.',
  },
  {
    q: 'What is the refund policy?',
    a: 'All paid plans come with a 7-day free trial. If you cancel within 7 days, you won\'t be charged. After that, we offer a prorated refund within 30 days if you\'re not satisfied — just email support@scholarpath.in.',
  },
]

function FAQItem({ faq, index }) {
  const [open, setOpen] = useState(false)

  return (
    <FadeInSection delay={index * 0.05}>
      <div className="border-b border-gray-100 last:border-0">
        <button
          onClick={() => setOpen(!open)}
          className="w-full flex items-start justify-between gap-4 py-5 text-left cursor-pointer group"
        >
          <span
            className="font-semibold text-base transition-colors"
            style={{ color: open ? '#FF6B35' : '#1B3A6B' }}
          >
            {faq.q}
          </span>
          <span
            className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 transition-all"
            style={{
              background: open ? '#FF6B35' : '#F3F4F6',
              color: open ? 'white' : '#6B7280',
            }}
          >
            {open ? <Minus className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
          </span>
        </button>

        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              className="overflow-hidden"
            >
              <p className="text-gray-500 text-sm leading-relaxed pb-5">{faq.a}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </FadeInSection>
  )
}

export default function FAQSection() {
  return (
    <section id="about" className="py-20 lg:py-28 bg-white">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-14">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#EEF2FF', color: '#1B3A6B' }}>
            FAQ
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            Questions? Answered.
          </h2>
          <p className="text-gray-500">
            Still need help? Email us at{' '}
            <a href="mailto:support@scholarpath.in" className="underline" style={{ color: '#FF6B35' }}>
              support@scholarpath.in
            </a>
          </p>
        </FadeInSection>

        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm px-6 lg:px-8">
          {FAQS.map((faq, i) => (
            <FAQItem key={faq.q} faq={faq} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
