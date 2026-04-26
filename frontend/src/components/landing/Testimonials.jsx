import FadeInSection from './FadeInSection'
import { Link } from 'react-router-dom'

export default function Testimonials() {
  return (
    <section className="py-20 lg:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <FadeInSection className="text-center mb-14">
          <div className="inline-block text-sm font-semibold px-4 py-1.5 rounded-full mb-4"
               style={{ background: '#FFF0EA', color: '#FF6B35' }}>
            Early Access
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold" style={{ color: '#1B3A6B' }}>
            Be Among the First
          </h2>
          <p className="mt-4 text-gray-500 max-w-xl mx-auto text-base">
            ScholarPath is newly launched. We're looking for early students and parents
            to practice with us and share their experience.
          </p>
        </FadeInSection>

        <FadeInSection className="flex flex-col sm:flex-row gap-6 justify-center items-center">
          <div className="rounded-3xl border-2 border-dashed border-gray-200 p-8 text-center max-w-sm w-full">
            <div className="text-4xl mb-4">🎓</div>
            <div className="font-semibold text-gray-700 mb-2">Students &amp; Parents</div>
            <p className="text-sm text-gray-500 mb-5">
              Try a free practice test and tell us how it went. Your feedback shapes the platform.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-white font-semibold text-sm"
              style={{ background: '#FF6B35' }}
            >
              Start Free Practice
            </Link>
          </div>

          <div className="rounded-3xl border-2 border-dashed border-gray-200 p-8 text-center max-w-sm w-full">
            <div className="text-4xl mb-4">📝</div>
            <div className="font-semibold text-gray-700 mb-2">Your story here</div>
            <p className="text-sm text-gray-500">
              After your first practice test, we'd love to hear your experience.
              Real results from real students — coming soon.
            </p>
          </div>
        </FadeInSection>
      </div>
    </section>
  )
}
