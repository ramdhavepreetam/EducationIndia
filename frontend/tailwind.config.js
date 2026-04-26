/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        // ScholarPath landing page colors
        sp: {
          blue:    '#1B3A6B',
          'blue-light': '#2351A0',
          'blue-dark':  '#0F2347',
          saffron: '#FF6B35',
          'saffron-light': '#FF8A5B',
          'saffron-dark':  '#E5501A',
          emerald: '#10B981',
          gray:    '#F8FAFC',
          navy:    '#0F2040',
        },
        brand: {
          50:  '#eff5ff',
          100: '#ddeaff',
          200: '#b3cfff',
          300: '#7aaaff',
          400: '#3d80f0',
          500: '#2351A0',   // sp.blue-light
          600: '#1B3A6B',   // sp.blue — primary
          700: '#163060',
          800: '#102346',
          900: '#0d1a35',
          950: '#0F2347',   // sp.blue-dark
        },
        accent: {
          50:  '#fff8f5',
          100: '#fff0e8',
          200: '#ffd9c0',
          300: '#ffb896',
          400: '#FF8A5B',   // sp.saffron-light
          500: '#FF6B35',   // sp.saffron — CTA
          600: '#E5501A',   // sp.saffron-dark
          700: '#c44018',
          800: '#9d3214',
          900: '#7d280f',
        },
        surface: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      boxShadow: {
        'glass':    '0 8px 32px rgba(27, 58, 107, 0.12)',
        'glass-lg': '0 16px 48px rgba(27, 58, 107, 0.18)',
        'glow':     '0 0 24px rgba(255, 107, 53, 0.25)',
      },
      animation: {
        'fade-in':  'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'float':    'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
}
