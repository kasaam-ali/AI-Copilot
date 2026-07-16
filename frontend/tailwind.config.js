/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#f5f6f8',
          raised: '#ffffff',
          panel: '#eef1f4',
          border: '#dce0e6',
        },
        accent: {
          DEFAULT: '#f5a623',
          muted: '#8a6414',
        },
        brand: {
          DEFAULT: '#1a73e8',
          deep: '#1557b0',
          glow: '#4285f4',
        },
        status: {
          healthy: '#188038',
          watch: '#b06000',
          risk: '#c26a1d',
          defect: '#c5221f',
        },
        ink: {
          DEFAULT: '#1f2733',
          muted: '#5b6672',
          faint: '#8a95a1',
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
