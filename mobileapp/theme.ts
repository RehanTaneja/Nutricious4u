// Design tokens for the "Green Diet" visual theme.
// Purely cosmetic: colors, typography, spacing, radii, shadows.
// COLORS keeps every key the legacy palette had (values updated) so all
// existing references keep resolving; new keys are additive.

export const COLORS = {
  // — core (legacy keys, updated values) —
  background: '#F6FAF7',   // soft off-white with a whisper of green
  primary: '#10B981',      // deep vibrant emerald
  primaryDark: '#059669',  // pressed/active states
  white: '#FFFFFF',
  text: '#1E293B',         // deep slate for primary text
  placeholder: '#94A3B8',
  error: '#DC2626',
  lightGreen: '#E7F6EF',   // bot messages / soft tints

  // — macro & activity accents (legacy keys, harmonized values) —
  energy: '#F97316',       // calories — warm orange
  protein: '#0D9488',      // teal, sits naturally next to emerald
  fat: '#EAB308',          // amber
  logFood: '#10B981',
  logWorkout: '#F97316',
  streakRed: '#FECACA',
  streakActive: '#F59E0B',
  streakInactive: '#94A3B8',
  streakYellow: '#FBBF24',
  streakVibrant: '#F97316',
  chartBars: [
    '#6EE7B7',
    '#A7F3D0',
    '#FDE68A',
    '#FDBA74',
    '#F9A8D4',
    '#6EE7B7',
    '#A7F3D0',
  ],

  // — new tokens —
  primarySoft: '#D1FAE5',   // tint fills: selected chips, icon badges
  surface: '#FFFFFF',       // cards, modals, inputs
  border: '#E2ECE6',        // hairline borders, dividers
  textSecondary: '#64748B', // labels, captions
  textMuted: '#94A3B8',
  success: '#16A34A',
  overlay: 'rgba(15, 23, 42, 0.45)', // modal scrim
};

export const TYPE = {
  display: { fontSize: 32, fontWeight: '800' as const, letterSpacing: -0.5 },
  title: { fontSize: 24, fontWeight: '700' as const, letterSpacing: -0.3 },
  heading: { fontSize: 19, fontWeight: '700' as const },
  subhead: { fontSize: 16, fontWeight: '600' as const },
  body: { fontSize: 15, fontWeight: '400' as const, lineHeight: 22 },
  label: { fontSize: 13, fontWeight: '600' as const, letterSpacing: 0.2 },
  caption: { fontSize: 12, fontWeight: '500' as const },
  micro: { fontSize: 10, fontWeight: '600' as const, letterSpacing: 0.4 },
};

export const SPACING = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24, xxxl: 32 };

export const RADII = { sm: 10, md: 14, lg: 20, xl: 28, pill: 999 };

// Forest-ink editorial layer: deep green hero panels and display accents.
export const INK = {
  deep: '#0B3B2E',
  mid: '#14532D',
  onInk: '#ECFDF5',
  onInkMuted: 'rgba(236, 253, 245, 0.64)',
};

export const GRADIENTS = {
  primary: ['#10B981', '#0D9488'],   // buttons, active fills (emerald -> teal)
  hero: ['#0B3B2E', '#14532D'],      // dashboard hero panel
  cardSheen: ['#FFFFFF', '#F0FDF4'], // subtle card sheen
};

// Faux-glass surfaces: translucent fills + hairline light borders (no blur dep).
export const GLASS = {
  fill: 'rgba(255, 255, 255, 0.72)',
  fillStrong: 'rgba(255, 255, 255, 0.86)',
  border: 'rgba(255, 255, 255, 0.55)',
  tintFill: 'rgba(209, 250, 229, 0.35)',
};

// Micro-interaction timings; visual feedback only.
export const ANIM = {
  pressScale: 0.97,
  spring: { friction: 6, tension: 140 },
  fadeMs: 180,
  popMs: 220,
  barMs: 600,
};

export const SHADOWS = {
  subtle: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  card: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
  },
  floating: {
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 24,
    elevation: 8,
  },
};
