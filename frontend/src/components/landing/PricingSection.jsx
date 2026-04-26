import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Check, Zap } from 'lucide-react'
import FadeInSection from './FadeInSection'

const PLANS = [
  {
    name: 'Free',
    price: { monthly: 0, yearly: 0 },
    badge: null,
    features: [
      '1 exam category',
      '5 mock tests / month',
      'Basic performance report',
      'Mobile app access',
    ],
    cta: 'Get Started Free',
    ctaTo: '/register',
    highlight: false,
    color: '#64748B',
  },
  {
    name: 'Scholar',
    price: { monthly: 299, yearly: 239 },
    badge: 'Most Popular',
    features: [
      '3 exam categories',
      'Unlimited mock tests',
      'Full analytics + wrong answer review',
      'Parent dashboard (school exams)',
      'Content in English & Marathi',
      'Priority email support',
    ],
    cta: 'Start 7-Day Free Trial',
    ctaTo: '/register',
    highlight: true,
    color: '#FF6B35',
  },
  {
    name: 'Pro',
    price: { monthly: 599, yearly: 479 },
    badge: null,
    features: [
      'All exam categories (current + upcoming)',
      'Unlimited everything',
      'Priority support (chat + email)',
      'Early access to new exams',
      'Up to 5 child profiles',
      'Downloadable tests (offline)',
    ],
    cta: 'Go Pro',
    ctaTo: '/register',
    highlight: false,
    color: '#1B3A6B',
  },
]

export default function PricingSection() {
  const [yearly, setYearly] = useState(false)

  return (
    <section id="pricing" className="py-20 lg:py-28" style={{ background: '#F8FAFC' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-10">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#EEF2FF', color: '#1B3A6B' }}>
            Pricing
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4" style={{ color: '#1B3A6B' }}>
            Simple Pricing. No Surprises.
          </h2>
          <p className="text-gray-500 text-lg mb-8">
            All plans include a 7-day free trial. Cancel anytime.
          </p>

          {/* Toggle */}
          <div className="inline-flex items-center gap-3 p-1 rounded-xl bg-white border border-gray-200 shadow-sm">
            <button
              onClick={() => setYearly(false)}
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer"
              style={!yearly ? { background: '#1B3A6B', color: 'white' } : { color: '#6B7280' }}
            >
              Monthly
            </button>
            <button
              onClick={() => setYearly(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer"
              style={yearly ? { background: '#1B3A6B', color: 'white' } : { color: '#6B7280' }}
            >
              Yearly
              <span className="text-xs font-bold px-1.5 py-0.5 rounded-full"
                    style={{ background: '#FFF0EA', color: '#FF6B35' }}>
                -20%
              </span>
            </button>
          </div>
        </FadeInSection>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {PLANS.map((plan, i) => (
            <FadeInSection key={plan.name} delay={i * 0.1}>
              <motion.div
                whileHover={{ y: -4 }}
                transition={{ duration: 0.2 }}
                className="relative rounded-3xl p-7 h-full flex flex-col"
                style={
                  plan.highlight
                    ? {
                        background: 'linear-gradient(135deg, #1B3A6B 0%, #2351A0 100%)',
                        boxShadow: '0 20px 48px rgba(27,58,107,0.3)',
                      }
                    : {
                        background: 'white',
                        border: '1px solid #E5E7EB',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      }
                }
              >
                {plan.badge && (
                  <div
                    className="absolute -top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-4 py-1 rounded-full text-xs font-bold text-white shadow-lg"
                    style={{ background: '#FF6B35' }}
                  >
                    <Zap className="w-3 h-3" />
                    {plan.badge}
                  </div>
                )}

                <div className="mb-6">
                  <div
                    className="text-sm font-semibold mb-3"
                    style={{ color: plan.highlight ? '#93C5FD' : '#9CA3AF' }}
                  >
                    {plan.name.toUpperCase()}
                  </div>
                  <div className="flex items-end gap-1">
                    <span
                      className="text-4xl font-extrabold"
                      style={{ color: plan.highlight ? 'white' : '#1B3A6B' }}
                    >
                      {plan.price[yearly ? 'yearly' : 'monthly'] === 0
                        ? '₹0'
                        : `₹${plan.price[yearly ? 'yearly' : 'monthly']}`}
                    </span>
                    {plan.price.monthly > 0 && (
                      <span
                        className="text-sm mb-1.5"
                        style={{ color: plan.highlight ? '#93C5FD' : '#9CA3AF' }}
                      >
                        /mo
                      </span>
                    )}
                  </div>
                  {yearly && plan.price.monthly > 0 && (
                    <div
                      className="text-xs mt-1"
                      style={{ color: plan.highlight ? '#93C5FD' : '#9CA3AF' }}
                    >
                      Billed ₹{plan.price.yearly * 12}/year
                    </div>
                  )}
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm">
                      <Check
                        className="w-4 h-4 flex-shrink-0 mt-0.5"
                        style={{ color: plan.highlight ? '#10B981' : '#10B981' }}
                      />
                      <span style={{ color: plan.highlight ? '#E2E8F0' : '#374151' }}>
                        {f}
                      </span>
                    </li>
                  ))}
                </ul>

                <Link
                  to={plan.ctaTo}
                  className="block text-center py-3.5 rounded-xl text-sm font-bold transition-all cursor-pointer hover:opacity-90"
                  style={
                    plan.highlight
                      ? { background: '#FF6B35', color: 'white' }
                      : plan.name === 'Free'
                      ? { border: '2px solid #1B3A6B', color: '#1B3A6B' }
                      : { background: '#1B3A6B', color: 'white' }
                  }
                >
                  {plan.cta}
                </Link>
              </motion.div>
            </FadeInSection>
          ))}
        </div>

        <FadeInSection delay={0.3}>
          <p className="text-center text-sm text-gray-400 mt-8">
            All plans include 7-day free trial. Cancel anytime. No credit card required for Free plan.
          </p>
        </FadeInSection>
      </div>
    </section>
  )
}
