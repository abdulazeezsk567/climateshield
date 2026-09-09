# ClimateShield Design System Specification

## Institutional Climate-Risk Interface Architecture
**Client**: Satin Finserv Ltd (SFL) — MSME Lending Division  
**Package**: `@climateshield/design-system`  
**Location**: `frontend/src/design-system`

---

## 1. Design Philosophy & Anti-Patterns Rejected

Enterprise financial risk applications require **operational clarity, tabular precision, and high-density telemetry**. Generic AI design trends undermine institutional credibility and reduce information density.

### Explicit Anti-Patterns Avoided
| Generic AI Anti-Pattern | Why It Was Rejected | ClimateShield Replacement |
| :--- | :--- | :--- |
| **Purple-to-Blue Gradients** | Conveys generic SaaS marketing fluff; lacks domain specificity. | **Deep Midnight Navy (`#080D17`) + Climate Teal (`#0D9488`) + SFL Imperial Gold (`#F59E0B`)**. |
| **Glassmorphism & Frosted Blur** | Degrades contrast and illegible on dense financial tabular figures. | **Solid opaque dark surfaces (`#0F172A`, `#182238`) with 1px razor-sharp borders (`#23324E`)**. |
| **Oversized Rounded Pills (`rounded-3xl`)** | Consumes vertical density; creates toy-like appearance. | **Disciplined radii: 2px, 4px, and 6px (`rounded-cs`)**. |
| **Floating Decorative Blur Blobs** | Visual noise that distracts from risk alerts and threshold breaches. | **Purposeful telemetry borders and clean status indicators**. |
| **Mismatched Stock Icons** | Inconsistent stroke weights and styles compromise polish. | **Bespoke SVG motif system with unified 1.5px stroke and 24x24 coordinate box**. |
| **Landing Page Whitespace** | Forces excessive scrolling; hides vital multi-district correlations. | **Risk-ops density: compact tables, dense KPI readouts, and immediate filters**. |

---

## 2. Color Palette & Semantic Color Architecture

All colors are defined as CSS variables in `tokens.css` and strongly-typed in `tokens.ts`.

### 1. Deep Midnight Navy (Structural Ground & Contrast)
- `cs-surface-ground`: `#080D17` (Deepest canvas layer, reduces eye strain during shift monitoring)
- `cs-surface-card`: `#0F172A` (Primary container elevation)
- `cs-surface-elevated`: `#182238` (Hover states and modal dialogs)
- `cs-surface-border`: `#23324E` (Crisp structural separator)
- `cs-surface-border-subtle`: `#162033` (Table row divides)

### 2. Climate Teal (Satellite Telemetry & Hydrology)
Carries satellite data streams, precipitation indices, soil moisture telemetry, and Sentinel-2 NDVI vegetative readings:
- `cs-teal-500`: `#0D9488` (Primary telemetry accent)
- `cs-teal-400`: `#14B8A6` (Active telemetry highlight)
- `cs-teal-300`: `#5EEAD4` (Data hover state)
- `cs-teal-muted`: `rgba(13, 148, 136, 0.15)` (Background tint for weather badges)

### 3. SFL Imperial Gold (NBFC Brand & Active Triggers)
Carries Satin Finserv capital growth, active parametric intervention actions, and primary action affordances:
- `cs-gold-500`: `#F59E0B` (Primary button fill and critical alert highlights)
- `cs-gold-400`: `#FBBF24` (Hover fill)
- `cs-gold-muted`: `rgba(245, 158, 11, 0.15)` (Active trigger pill background)

### 4. Calibrated 4-Tier Risk Semantics
| Tier | Score Range | Color Token | Hex Code | Semantic Role |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1 • Low** | `[0.00, 0.35)` | `status-low` | `#10B981` (Emerald) | Standard loan performance; normal precipitation |
| **Tier 2 • Moderate** | `[0.35, 0.55)` | `status-moderate` | `#F59E0B` (Amber) | Emerging anomaly watch; advisory notifications |
| **Tier 3 • High** | `[0.55, 0.75)` | `status-high` | `#F97316` (Orange) | Anomaly breach; credit committee alert |
| **Tier 4 • Severe** | `[0.75, 1.00]` | `status-severe` | `#EF4444` (Rose) | Parametric threshold breached; 60-day EMI relief |

---

## 3. Typography Architecture

We deliberately avoid monospaced or sans-serif homogeneity by employing a **three-tier typographic pairing**:

### Tier 1: Display & Section Headings — Editorial Gravitas
- **Fonts**: `Newsreader`, `Fraunces`, `Georgia`, serif
- **Role**: Institutional confidence and authority suitable for a regulated NBFC board.
- **Usage**: Main application title, modal headers, major section intros.

### Tier 2: Operational Body & Controls — Technical Grotesk
- **Fonts**: `Plus Jakarta Sans`, `Inter`, sans-serif
- **Role**: High x-height, neutral tone, legible at dense 11px–13px font sizes.
- **Usage**: Button labels, field annotations, filter chips, narrative alert texts.

### Tier 3: Telemetry, Values & Ledgers — Tabular Monospace
- **Fonts**: `JetBrains Mono`, `Fira Code`, monospace
- **Attributes**: `font-variant-numeric: tabular-nums`
- **Role**: Alignment across numeric columns in INR (`₹`), GPS coordinates (`25.3176° N`), rainfall deviations (`+84.2%`), and SHA-256 parent hash verification strings.

---

## 4. Bespoke SVG Iconography

Located in `src/design-system/icons/Icons.tsx`, all icons share an immutable contract:
- **Stroke Width**: Strict `1.5px`
- **ViewBox**: `0 0 24 24`
- **Fill**: `none`
- **Line Cap / Join**: `round`
- **Domain Motifs**:
  - `IconShield`: Parametric credit protection emblem
  - `IconRainfall`: Discrete multi-droplet rainfall telemetry
  - `IconDrought`: Aridity sun with cracked ground vectors
  - `IconSatellite`: Orbital sensor aperture
  - `IconRupee`: Crisp Indian Rupee currency glyph (`₹`)
  - `IconPulse`: Streaming sensor heartbeat
  - `IconLock`: Cryptographic SHA-256 tamper-evident ledger indicator
  - `IconAlertTriangle`: Threshold breach hazard marker
  - `IconCheckCircle`: LMS confirmed execution stamp

---

## 5. Component Library Standards

### 1. `Button`
- Micro-interactions: `active:translate-y-px`
- Focus rings: 2px offset on dark midnight navy ground
- Loading state: Inline spinner with preserved button width
- Strict variants: `primary` (Imperial Gold), `secondary` (Slate outline), `teal` (Hydrology), `danger` (Crimson), `ghost`.

### 2. `RiskTierBadge` & `InterventionStatusPill`
- 4-Stage Parametric Lifecycle:
  1. `TRIGGERED`: Pulsing amber dot (`animate-ping`)
  2. `NOTIFIED`: Sky blue indicator
  3. `APPLIED`: Teal execution badge
  4. `CONFIRMED`: Solid emerald verified state

### 3. `MetricCard`
- Designed for high-density financial trading terminal screens.
- Eyebrow label in 11px uppercase monospace.
- Hero value in 28px–32px tabular monospace.
- Benchmark delta chip (`+5.4% YoY`) paired with benchmark baseline context.

### 4. `DataTable`
- Compact 8px padding (`density="compact"`).
- Right-aligned numeric columns with tabular font-mono numbers.
- Hover highlight on dark slate elevated surfaces.
- Type-safe column definitions with custom cell renderers.

### 5. `AlertBanner`
- Dismissible or permanent notification bar with clear visual hierarchy.
- Variants: `critical` (flood breach), `warning` (drought watch), `info` (weather sync), `success` (LMS confirmed).

---

## 6. Verification & Hygiene

The design system has been integrated into:
1. `index.css`: Global token variables & CSS resets
2. `tailwind.config.js`: Complete theme token extensions
3. `Showcase.tsx`: Live interactive visual verification harness
4. `App.tsx`: Mounted with active role viewport switcher (`credit_team` vs `viewer`)

All tokens compile with 0 lint errors, 0 runtime dependencies beyond React and Tailwind, and full TypeScript type safety.
