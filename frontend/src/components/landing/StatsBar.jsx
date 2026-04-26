import { useRef, useEffect, useState } from 'react'
import { useInView } from 'framer-motion'

const STATS = [
  { value: 2, suffix: '', label: 'MSCE Papers Available', prefix: '' },
  { value: 150, suffix: '', label: 'Questions per Paper', prefix: '' },
  { value: 90, suffix: ' min', label: 'Full-Length Timed Test', prefix: '' },
  { value: 2, suffix: '', label: 'Languages (EN + MR)', prefix: '' },
]

function CountUp({ target, duration = 2000, prefix = '', suffix = '' }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  const started = useRef(false)

  useEffect(() => {
    if (!inView || started.current) return
    started.current = true

    const startTime = performance.now()
    const step = (now) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(eased * target))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [inView, target, duration])

  const formatted = count >= 1000
    ? count.toLocaleString('en-IN')
    : count.toString()

  return (
    <span ref={ref}>
      {prefix}{formatted}{suffix}
    </span>
  )
}

export default function StatsBar() {
  return (
    <section className="py-14" style={{ background: '#0F2040' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-4">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center">
              <div
                className="text-4xl lg:text-5xl font-extrabold mb-2 tabular-nums"
                style={{ color: '#FF6B35' }}
              >
                <CountUp
                  target={stat.value}
                  prefix={stat.prefix}
                  suffix={stat.suffix}
                />
              </div>
              <div className="text-blue-200 text-sm font-medium">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
