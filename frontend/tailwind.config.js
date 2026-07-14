/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0b0f14',
          raised: '#121821',
          panel: '#161d28',
          border: '#232c3a',
        },
        accent: {
          DEFAULT: '#f5a623',
          muted: '#8a6414',
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
    },
  },
  plugins: [],
}
