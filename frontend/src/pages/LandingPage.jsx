import LandingNavbar from '@/components/landing/LandingNavbar'
import HeroSection from '@/components/landing/HeroSection'
import ExamCategories from '@/components/landing/ExamCategories'
import StatsBar from '@/components/landing/StatsBar'
import HowItWorks from '@/components/landing/HowItWorks'
import FeaturesGrid from '@/components/landing/FeaturesGrid'
import ExamSpotlight from '@/components/landing/ExamSpotlight'
import SampleTestWidget from '@/components/landing/SampleTestWidget'
import PricingSection from '@/components/landing/PricingSection'
import Testimonials from '@/components/landing/Testimonials'
import ComingSoonBanner from '@/components/landing/ComingSoonBanner'
import FAQSection from '@/components/landing/FAQSection'
import LandingFooter from '@/components/landing/LandingFooter'

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <LandingNavbar />
      <main>
        <HeroSection />
        <ExamCategories />
        <StatsBar />
        <HowItWorks />
        <FeaturesGrid />
        <ExamSpotlight />
        <SampleTestWidget />
        <PricingSection />
        <Testimonials />
        <ComingSoonBanner />
        <FAQSection />
      </main>
      <LandingFooter />
    </div>
  )
}
