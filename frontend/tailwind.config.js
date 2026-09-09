/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        serif: ['Newsreader', 'Fraunces', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Fira Code', 'Consolas', 'monospace'],
      },
      colors: {
        cs: {
          surface: {
            ground: 'var(--cs-surface-ground)',
            card: 'var(--cs-surface-card)',
            elevated: 'var(--cs-surface-elevated)',
            border: 'var(--cs-surface-border)',
            subtle: 'var(--cs-surface-border-subtle)',
          },
          navy: {
            950: '#080D17',
            900: '#0B111E',
            800: '#111A2E',
            700: '#182238',
            600: '#23324E',
            500: '#334466',
            400: '#475D87',
          },
          teal: {
            600: '#0F766E',
            500: '#0D9488',
            400: '#14B8A6',
            300: '#5EEAD4',
            muted: '#134E4A',
            glow: 'rgba(13, 148, 136, 0.15)',
          },
          gold: {
            600: '#D97706',
            500: '#F59E0B',
            400: '#FBBF24',
            300: '#FDE68A',
            muted: '#78350F',
            glow: 'rgba(245, 158, 11, 0.15)',
          },
          status: {
            low: '#10B981',
            moderate: '#F59E0B',
            high: '#F97316',
            severe: '#EF4444',
            info: '#0284C7',
          },
          text: {
            primary: 'var(--cs-text-primary)',
            secondary: 'var(--cs-text-secondary)',
            muted: 'var(--cs-text-muted)',
          },
        },
      },
      boxShadow: {
        'cs-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.25)',
        'cs-md': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)',
        'cs-glow-teal': '0 0 15px -3px rgba(13, 148, 136, 0.25)',
        'cs-glow-gold': '0 0 15px -3px rgba(245, 158, 11, 0.25)',
        'cs-glow-danger': '0 0 15px -3px rgba(239, 68, 68, 0.25)',
      },
      borderRadius: {
        'cs-xs': '2px',
        'cs-sm': '4px',
        'cs': '6px',
        'cs-md': '8px',
      },
    },
  },
  plugins: [],
};
