/**
 * Programmatic Design Tokens Dictionary for ClimateShield.
 * Useful for Chart.js / Canvas renderers, geospatial heatmap layers, and styled components.
 */

export const CS_COLORS = {
  surface: {
    ground: '#080D17',
    card: '#0F172A',
    elevated: '#182238',
    border: '#23324E',
    subtle: '#162033',
  },
  navy: {
    950: '#080D17',
    900: '#0B111E',
    800: '#0F172A',
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
    muted: 'rgba(13, 148, 136, 0.15)',
    glow: 'rgba(13, 148, 136, 0.25)',
  },
  gold: {
    600: '#D97706',
    500: '#F59E0B',
    400: '#FBBF24',
    300: '#FDE68A',
    muted: 'rgba(245, 158, 11, 0.15)',
    glow: 'rgba(245, 158, 11, 0.25)',
  },
  status: {
    low: '#10B981',
    moderate: '#F59E0B',
    high: '#F97316',
    severe: '#EF4444',
    info: '#0284C7',
  },
  text: {
    primary: '#F8FAFC',
    secondary: '#94A3B8',
    muted: '#64748B',
  },
} as const;

export const CS_TYPOGRAPHY = {
  fontFamilies: {
    serif: "'Newsreader', 'Fraunces', Georgia, serif",
    sans: "'Plus Jakarta Sans', Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
  },
  scale: {
    display: { fontSize: '2.5rem', lineHeight: '1.15', letterSpacing: '-0.02em', fontWeight: '600' },
    h1: { fontSize: '2rem', lineHeight: '1.2', letterSpacing: '-0.015em', fontWeight: '600' },
    h2: { fontSize: '1.5rem', lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' },
    h3: { fontSize: '1.25rem', lineHeight: '1.3', letterSpacing: '0em', fontWeight: '600' },
    h4: { fontSize: '1rem', lineHeight: '1.4', letterSpacing: '0.04em', textTransform: 'uppercase', fontWeight: '600' },
    bodyLg: { fontSize: '1.125rem', lineHeight: '1.5', letterSpacing: '0em', fontWeight: '400' },
    body: { fontSize: '0.875rem', lineHeight: '1.5', letterSpacing: '0em', fontWeight: '400' },
    bodySm: { fontSize: '0.75rem', lineHeight: '1.4', letterSpacing: '0em', fontWeight: '400' },
    caption: { fontSize: '0.6875rem', lineHeight: '1.3', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: '600' },
    monoMetric: { fontSize: '1.75rem', lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '600', fontVariantNumeric: 'tabular-nums' },
  },
} as const;

export const CS_RISK_COLORS: Record<string, { hex: string; bg: string; border: string; label: string }> = {
  LOW: { hex: CS_COLORS.status.low, bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)', label: 'Low Risk' },
  MODERATE: { hex: CS_COLORS.status.moderate, bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)', label: 'Moderate' },
  HIGH: { hex: CS_COLORS.status.high, bg: 'rgba(249, 115, 22, 0.12)', border: 'rgba(249, 115, 22, 0.3)', label: 'High Alert' },
  SEVERE: { hex: CS_COLORS.status.severe, bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.3)', label: 'Severe Breach' },
};

export const CS_INTERVENTION_COLORS: Record<string, { hex: string; bg: string; label: string }> = {
  TRIGGERED: { hex: '#F97316', bg: 'rgba(249, 115, 22, 0.12)', label: '1. Triggered' },
  NOTIFIED: { hex: '#0284C7', bg: 'rgba(2, 132, 199, 0.12)', label: '2. Notified' },
  APPLIED: { hex: '#D97706', bg: 'rgba(217, 119, 6, 0.12)', label: '3. Applied (LMS)' },
  CONFIRMED: { hex: '#10B981', bg: 'rgba(16, 185, 129, 0.12)', label: '4. Confirmed' },
  FAILED: { hex: '#EF4444', bg: 'rgba(239, 68, 68, 0.12)', label: 'Failed' },
  CANCELLED: { hex: '#64748B', bg: 'rgba(100, 116, 139, 0.12)', label: 'Cancelled' },
};
