/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0a0e13',
          raised: '#111823',
          panel: '#18212e',
          border: '#26313f',
        },
        accent: {
          DEFAULT: '#f5a623',
          muted: '#8a6414',
        },
        brand: {
          DEFAULT: '#22d3ee',
          deep: '#0891b2',
          glow: '#67e8f9',
        },
        status: {
          healthy: '#10b981',
          watch: '#f5a623',
          risk: '#f97316',
          defect: '#ef4444',
        },
        ink: {
          DEFAULT: '#e6edf3',
          muted: '#8b98a9',
          faint: '#5b6675',
        },
      },
      fontFamily: {
        mono: [
          "'JetBrains Mono'",
          "'Fira Code'",
          'ui-monospace',
          'SFMono-Regular',
          'monospace',
        ],
      },
      keyframes: {
        floaty: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
      },
      animation: {
        floaty: 'floaty 5s ease-in-out infinite',
        scan: 'scan 2.6s linear infinite',
        shimmer: 'shimmer 3s linear infinite',
        pulseGlow: 'pulseGlow 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
