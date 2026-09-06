/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['Poppins', 'system-ui', 'sans-serif'],
        sans: ['Poppins', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: '#0f172a',
          soft: '#334155',
          dim: '#64748b',
        },
        line: '#e2e8f0',
        paper: '#ffffff',
        mist: '#f8fafc',
        brand: {
          DEFAULT: '#0d9488',
          ink: '#0f766e',
          soft: '#ccfbf1',
          glow: '#5eead4',
        },
        risk: {
          high: '#e11d48',
          med: '#d97706',
          low: '#059669',
        },
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,23,42,.04), 0 12px 40px -12px rgba(15,23,42,.12)',
        lift: '0 2px 8px rgba(15,23,42,.06), 0 24px 60px -20px rgba(13,148,136,.25)',
      },
      keyframes: {
        drift: {
          '0%,100%': { transform: 'translate3d(0,0,0) scale(1)' },
          '33%': { transform: 'translate3d(4%, -6%, 0) scale(1.08)' },
          '66%': { transform: 'translate3d(-5%, 3%, 0) scale(0.96)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'drift-slow': 'drift 22s ease-in-out infinite',
        shimmer: 'shimmer 3s linear infinite',
      },
    },
  },
  plugins: [],
};
