import { Link } from 'react-router-dom'
import { BookOpen, Globe } from 'lucide-react'

const FOOTER_LINKS = {
  Exams: [
    { label: 'Scholarship (MSCE)', to: '#exams', badge: 'LIVE' },
    { label: 'Banking & Finance', to: '#', badge: 'Soon' },
    { label: 'SSC Exams', to: '#', badge: 'Soon' },
    { label: 'NEET UG', to: '#', badge: 'Soon' },
    { label: 'JEE / MHT-CET', to: '#', badge: 'Soon' },
  ],
  Product: [
    { label: 'Features', to: '#features' },
    { label: 'Pricing', to: '#pricing' },
    { label: 'Blog', to: '#' },
    { label: 'Changelog', to: '#' },
  ],
  Company: [
    { label: 'About', to: '#about' },
    { label: 'Contact', to: '#' },
    { label: 'Privacy Policy', to: '#' },
    { label: 'Terms of Service', to: '#' },
  ],
}

// Social icons as SVG paths (lucide v12 removed Twitter/Instagram etc.)
const SOCIALS = [
  {
    href: '#', label: 'X / Twitter',
    path: 'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z',
  },
  {
    href: '#', label: 'Instagram',
    path: 'M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z',
  },
  {
    href: '#', label: 'YouTube',
    path: 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z',
  },
  {
    href: '#', label: 'LinkedIn',
    path: 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z',
  },
]

export default function LandingFooter() {
  const handleAnchor = (e, href) => {
    if (href.startsWith('#') && href.length > 1) {
      e.preventDefault()
      document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <>
      {/* Footer CTA Banner */}
      <section className="py-16 text-center" style={{ background: '#1B3A6B' }}>
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">
            Start your exam journey today
          </h2>
          <p className="text-blue-200 mb-8">
            Free forever, upgrade when ready. No credit card required.
          </p>
          <Link
            to="/register"
            className="inline-block px-10 py-4 rounded-xl font-bold text-base cursor-pointer hover:opacity-90 transition-opacity"
            style={{ background: '#FF6B35', color: 'white' }}
          >
            Start Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-14" style={{ background: '#0F2040' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12 mb-12">
            {/* Brand column */}
            <div className="col-span-2 lg:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                     style={{ background: '#FF6B35' }}>
                  <BookOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="font-bold text-white text-lg leading-none">ScholarPath</div>
                  <div className="text-xs" style={{ color: '#FF6B35' }}>Crack Any Exam</div>
                </div>
              </div>
              <p className="text-blue-200 text-sm leading-relaxed mb-5 max-w-xs">
                Adaptive mock tests, real-time analytics, and smart revision — for every exam that matters.
              </p>
              <div className="flex gap-3">
                {SOCIALS.map(({ path, href, label }) => (
                  <a
                    key={label}
                    href={href}
                    aria-label={label}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-blue-300 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
                  >
                    <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor">
                      <path d={path} />
                    </svg>
                  </a>
                ))}
              </div>
            </div>

            {/* Link columns */}
            {Object.entries(FOOTER_LINKS).map(([col, links]) => (
              <div key={col}>
                <h4 className="text-white font-semibold text-sm mb-4">{col}</h4>
                <ul className="space-y-2.5">
                  {links.map((l) => (
                    <li key={l.label} className="flex items-center gap-2">
                      <a
                        href={l.to}
                        onClick={(e) => handleAnchor(e, l.to)}
                        className="text-blue-200 text-sm hover:text-white transition-colors cursor-pointer"
                      >
                        {l.label}
                      </a>
                      {l.badge === 'LIVE' && (
                        <span className="text-xs font-bold px-1.5 py-0.5 rounded-full"
                              style={{ background: '#FF6B35', color: 'white' }}>
                          LIVE
                        </span>
                      )}
                      {l.badge === 'Soon' && (
                        <span className="text-xs font-medium px-1.5 py-0.5 rounded-full"
                              style={{ background: 'rgba(255,255,255,0.1)', color: '#93C5FD' }}>
                          Soon
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Disclaimer */}
          <div className="border-t border-white/10 pt-7 mb-4">
            <p className="text-xs text-blue-300/70 leading-relaxed text-center max-w-3xl mx-auto">
              <strong className="text-blue-200">Disclaimer:</strong> ScholarPath is a practice preparation platform only.
              It does not guarantee selection, scores, ranks, or any specific outcome in any examination.
              All practice results are for self-assessment purposes only and have no official standing.
              ScholarPath is not affiliated with MSCE, any government body, or any examination authority.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-blue-300">
            <span>© 2026 ScholarPath. All rights reserved.</span>
            <span>Made with ❤️ for Indian students</span>
          </div>
        </div>
      </footer>
    </>
  )
}
