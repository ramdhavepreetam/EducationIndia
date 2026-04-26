import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, BookOpen } from 'lucide-react'

const NAV_LINKS = [
  { label: 'Exams', href: '#exams' },
  { label: 'Features', href: '#features' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'About', href: '#about' },
]

export default function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const handleAnchor = (e, href) => {
    e.preventDefault()
    setMenuOpen(false)
    if (href.startsWith('#')) {
      document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 backdrop-blur-md shadow-sm border-b border-gray-100'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                 style={{ background: '#1B3A6B' }}>
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div className="leading-none">
              <div className="font-bold text-lg" style={{ color: '#1B3A6B' }}>
                ScholarPath
              </div>
              <div className="text-xs font-medium" style={{ color: '#FF6B35' }}>
                Crack Any Exam
              </div>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((l) => (
              <a
                key={l.label}
                href={l.href}
                onClick={(e) => handleAnchor(e, l.href)}
                className="text-sm font-medium text-gray-600 hover:text-[#1B3A6B] transition-colors cursor-pointer"
              >
                {l.label}
              </a>
            ))}
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium px-4 py-2 rounded-lg border transition-colors cursor-pointer"
              style={{ color: '#1B3A6B', borderColor: '#1B3A6B' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#1B3A6B'
                e.currentTarget.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = '#1B3A6B'
              }}
            >
              Login
            </Link>
            <Link
              to="/register"
              className="text-sm font-semibold px-5 py-2 rounded-lg text-white transition-all hover:opacity-90 cursor-pointer"
              style={{ background: '#FF6B35' }}
            >
              Start Free
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 cursor-pointer"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white border-t border-gray-100 overflow-hidden"
          >
            <div className="px-4 py-4 flex flex-col gap-3">
              {NAV_LINKS.map((l) => (
                <a
                  key={l.label}
                  href={l.href}
                  onClick={(e) => handleAnchor(e, l.href)}
                  className="text-sm font-medium text-gray-700 py-2 cursor-pointer"
                >
                  {l.label}
                </a>
              ))}
              <div className="flex gap-3 pt-2 border-t border-gray-100">
                <Link
                  to="/login"
                  className="flex-1 text-center text-sm font-medium py-2.5 rounded-lg border cursor-pointer"
                  style={{ color: '#1B3A6B', borderColor: '#1B3A6B' }}
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="flex-1 text-center text-sm font-semibold py-2.5 rounded-lg text-white cursor-pointer"
                  style={{ background: '#FF6B35' }}
                >
                  Start Free
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
