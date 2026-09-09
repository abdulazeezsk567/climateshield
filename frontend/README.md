# ClimateShield Presentation Layer (`/frontend`)

The presentation layer is an institutional, high-density React 18 + TypeScript single-page application tailored for Satin Finserv Ltd (SFL) credit/risk officers and hackathon evaluation. Built strictly upon the ClimateShield design system (`src/design-system`), it completely rejects generic SaaS/AI tropes in favor of deep midnight surfaces, tabular monospace figures, and crisp 1.5px stroke domain iconography.

---

## 1. Capabilities & Delivered Views

- **Secure In-Memory Auth & Role Switching**:
  - Tokens are held strictly in memory in `authContext.tsx` and `apiClient.ts` (never raw unencrypted `localStorage`).
  - Pre-seeded evaluator credentials:
    - **SFL Credit Risk Officer**: `officer_sfl` / `SFLCreditRisk@2026!` (role: `credit_team`, full dispatch authority).
    - **Hackathon Judge / Auditor**: `judge_auditor` / `ViewerJudge@2026!` (role: `viewer`, read-only demo mode).
  - Quick-switch toggle in the top status bar allows instant role toggling during demos.

- **Portfolio Climate-Risk Dashboard (`PortfolioDashboard.tsx`)**:
  - 4 High-density KPI cards: Monitored Debt Exposure, High-Risk Exposure %, Districts Monitored, Active Parametric Triggers.
  - Interactive Geospatial Heatmap Grid covering 7 SFL operational districts (Varanasi, Barabanki, Patna, Bhojpur, Mirzapur, Muzaffarpur, Gorakhpur) with GPS coordinates and dominant hazard badges.
  - Filterable MSME borrower roster table with sector and risk tier dropdowns.
  - Deep-dive `DistrictModal.tsx` for district-level borrower inspection.

- **Interactive Trigger Simulator (`TriggerSimulator.tsx`)**:
  - Live demo console allowing users to pick a district and hazard (`FLOOD`, `DROUGHT`, `HEATWAVE`).
  - **3-Point Visual Deviation Calculation**: Visualizes 10-year NASA POWER baseline vs extreme P95 threshold vs simulated observation, calculating exact deviation percentage ($\Delta\%$) and trigger firing status.
  - Dispatches `POST /api/v1/triggers/simulate` and displays automated LMS loan restructuring actions (e.g. 60-day EMI moratorium signed via HMAC-SHA256).
  - Enforces role permissions (`viewer` role sees informative lock banner).

- **Borrower Alerts & Intervention Log (`InterventionLog.tsx`)**:
  - Table tracking the 4-stage LMS state machine: `TRIGGERED` $\rightarrow$ `NOTIFIED` $\rightarrow$ `APPLIED` $\rightarrow$ `CONFIRMED`.
  - Correlation ID and Borrower ID search with pagination.
  - Detail inspection modal displaying verified HMAC payload and stage timestamps.

- **Sensitive Field Masking & Audit Surveillance (`MaskedField.tsx` & `AuditLedgerView.tsx`)**:
  - Borrower identifiers and enterprise names are masked by default (`••••••••••••`).
  - Eye icon unmasks the value and emits a `SENSITIVE_FIELD_REVEALED` event logged in real-time to the audit trail.
  - `AuditLedgerView.tsx` renders the live session reveal audit feed and verifies the cryptographic SHA-256 parent-hash chain.

- **Design System Showcase (`design-system/Showcase.tsx`)**:
  - Live inspection harness for tokens, typography hierarchy, 18 bespoke SVG icons, buttons, badges, and components.

---

## 2. Local Development & Verification

```bash
cd frontend
npm install
npm run build
npm run dev
```

Production build verifies clean TypeScript compilation and bundling:
```text
✓ 54 modules transformed in 884ms.
dist/index.html                   1.08 kB
dist/assets/index-DSfrtfe3.css   34.07 kB
dist/assets/index-Db4D46kP.js   254.59 kB
```
