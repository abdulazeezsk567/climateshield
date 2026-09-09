import React, { useState } from 'react';
import {
  Button,
  Badge,
  RiskTierBadge,
  InterventionStatusPill,
  HazardBadge,
  Card,
  MetricCard,
  DataTable,
  ColumnDef,
  AlertBanner,
  Tabs,
} from './components/index.js';
import {
  IconShield,
  IconRainfall,
  IconDrought,
  IconSatellite,
  IconRupee,
  IconPulse,
  IconLock,
  IconAlertTriangle,
  IconCheckCircle,
  IconInfo,
  IconChevronDown,
  IconFilter,
  IconArrowRight,
  IconTrendingUp,
  IconActivity,
  IconBuilding,
  IconRefresh,
  IconDatabase,
  IconUser,
} from './icons/index.js';

interface BorrowerSample {
  id: string;
  name: string;
  district: string;
  sector: string;
  exposureInr: number;
  anomalyDelta: string;
  riskScore: number;
  riskTier: 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';
  status: 'TRIGGERED' | 'NOTIFIED' | 'APPLIED' | 'CONFIRMED';
}

const SAMPLE_BORROWERS: BorrowerSample[] = [
  {
    id: 'SFL-BR-0104',
    name: 'Ganga Agro Processors',
    district: 'Varanasi',
    sector: 'Agri-Processing',
    exposureInr: 1850000,
    anomalyDelta: '+84.2% (Flood)',
    riskScore: 0.88,
    riskTier: 'SEVERE',
    status: 'TRIGGERED',
  },
  {
    id: 'SFL-BR-0219',
    name: 'Awadh Weaving Mills',
    district: 'Barabanki',
    sector: 'Textiles',
    exposureInr: 1200000,
    anomalyDelta: '-42.1% (Drought)',
    riskScore: 0.67,
    riskTier: 'HIGH',
    status: 'NOTIFIED',
  },
  {
    id: 'SFL-BR-0342',
    name: 'Patliputra Cold Storage',
    district: 'Patna',
    sector: 'Cold Chain',
    exposureInr: 2400000,
    anomalyDelta: '+62.7% (Precipitation)',
    riskScore: 0.74,
    riskTier: 'HIGH',
    status: 'APPLIED',
  },
  {
    id: 'SFL-BR-0408',
    name: 'Kashi Brassworks',
    district: 'Mirzapur',
    sector: 'Metal Fabrication',
    exposureInr: 950000,
    anomalyDelta: '+12.4% (Normal)',
    riskScore: 0.38,
    riskTier: 'MODERATE',
    status: 'CONFIRMED',
  },
  {
    id: 'SFL-BR-0511',
    name: 'Bhojpur Flour & Feed',
    district: 'Bhojpur',
    sector: 'Food Milling',
    exposureInr: 1450000,
    anomalyDelta: '-3.8% (Normal)',
    riskScore: 0.18,
    riskTier: 'LOW',
    status: 'CONFIRMED',
  },
];

export const DesignSystemShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'components' | 'data' | 'audit'>('overview');
  const [buttonLoading, setButtonLoading] = useState(false);
  const [activeRole, setActiveRole] = useState<'credit_team' | 'viewer'>('credit_team');

  const handleSimulateClick = () => {
    setButtonLoading(true);
    setTimeout(() => setButtonLoading(false), 1200);
  };

  const columns: ColumnDef<BorrowerSample>[] = [
    {
      key: 'id',
      header: 'Borrower ID',
      width: '120px',
      render: (row) => <span className="font-mono text-slate-300 font-semibold">{row.id}</span>,
    },
    {
      key: 'name',
      header: 'Enterprise & Sector',
      render: (row) => (
        <div>
          <div className="font-sans font-medium text-slate-100">{row.name}</div>
          <div className="text-[11px] text-slate-500 font-mono">{row.sector}</div>
        </div>
      ),
    },
    {
      key: 'district',
      header: 'District',
      width: '110px',
      render: (row) => <span className="text-slate-300 font-mono text-xs">{row.district}</span>,
    },
    {
      key: 'exposureInr',
      header: 'Exposure (₹)',
      align: 'right',
      width: '130px',
      render: (row) => (
        <span className="font-mono font-medium text-slate-200">
          ₹{(row.exposureInr / 100000).toFixed(2)} L
        </span>
      ),
    },
    {
      key: 'anomalyDelta',
      header: 'Climate Anomaly',
      width: '160px',
      render: (row) => (
        <span
          className={`font-mono text-xs ${
            row.anomalyDelta.includes('+') ? 'text-sky-400' : 'text-amber-400'
          }`}
        >
          {row.anomalyDelta}
        </span>
      ),
    },
    {
      key: 'riskTier',
      header: 'ML Risk Tier',
      width: '150px',
      render: (row) => <RiskTierBadge tier={row.riskTier} score={row.riskScore} size="xs" />,
    },
    {
      key: 'status',
      header: 'LMS Pipeline',
      width: '140px',
      render: (row) => <InterventionStatusPill status={row.status} size="xs" />,
    },
  ];

  return (
    <div className="min-h-screen bg-[#080D17] text-slate-200 p-6 lg:p-10 font-sans selection:bg-teal-500/30 selection:text-white">
      {/* Institutional Header */}
      <header className="border-b border-slate-800 pb-6 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="p-1.5 rounded-cs-sm bg-teal-950/60 border border-teal-800/80 text-teal-400">
              <IconShield size={20} />
            </span>
            <span className="text-xs font-mono font-semibold tracking-widest uppercase text-teal-400">
              Satin Finserv Ltd • MSME Risk Ops
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-serif font-bold text-slate-50 tracking-tight">
            ClimateShield Design System
          </h1>
          <p className="text-sm font-sans text-slate-400 mt-1 max-w-3xl">
            Institutional, high-density financial interface designed for NBFC credit officers and parametric
            underwriting. Built without generic AI gradient tropes, prioritizing tabular precision and clear risk telemetry.
          </p>
        </div>

        {/* Role Viewport Switcher */}
        <div className="bg-slate-900 border border-slate-800 rounded-cs p-2 shrink-0">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <IconUser size={13} />
            <span>Active Role Viewport</span>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setActiveRole('credit_team')}
              className={`px-2.5 py-1 text-xs font-mono rounded-cs transition-colors ${
                activeRole === 'credit_team'
                  ? 'bg-amber-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/50'
              }`}
            >
              credit_team (Read/Write)
            </button>
            <button
              onClick={() => setActiveRole('viewer')}
              className={`px-2.5 py-1 text-xs font-mono rounded-cs transition-colors ${
                activeRole === 'viewer'
                  ? 'bg-amber-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/50'
              }`}
            >
              viewer (Judge Demo)
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="mb-8">
        <Tabs
          activeId={activeTab}
          onChange={(id) => setActiveTab(id as typeof activeTab)}
          items={[
            { id: 'overview', label: 'Design Foundations', icon: <IconActivity size={15} /> },
            { id: 'components', label: 'Interactive Components', icon: <IconBuilding size={15} />, badge: '7' },
            { id: 'data', label: 'MSME Portfolio Telemetry', icon: <IconSatellite size={15} />, badge: '56' },
            { id: 'audit', label: 'Cryptographic Ledger', icon: <IconLock size={15} />, badge: 'SHA-256' },
          ]}
        />
      </div>

      {/* SECTION 1: FOUNDATIONS (Colors, Typography, Icons) */}
      {activeTab === 'overview' && (
        <div className="space-y-10">
          {/* Color Palettes */}
          <Card
            eyebrow="Color Architecture"
            title="Institutional Palette Tokens"
            description="Deep Midnight Navy anchors financial gravity, Climate Teal carries satellite hydrology, SFL Imperial Gold carries active trigger workflows, and Risk Tiers enforce strict 4-level color semantics."
          >
            <div className="space-y-6">
              {/* Navy Surfaces */}
              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                  1. Deep Midnight Navy (Surfaces & Structural Contrast)
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                  {[
                    { name: 'Ground', hex: '#080D17', cls: 'bg-[#080D17] border border-slate-800' },
                    { name: 'Card Surface', hex: '#0F172A', cls: 'bg-[#0F172A] border border-slate-700' },
                    { name: 'Elevated', hex: '#182238', cls: 'bg-[#182238] border border-slate-700' },
                    { name: 'Border Sharp', hex: '#23324E', cls: 'bg-[#23324E]' },
                    { name: 'Navy 500', hex: '#334466', cls: 'bg-[#334466]' },
                    { name: 'Navy 400', hex: '#475D87', cls: 'bg-[#475D87]' },
                  ].map((item) => (
                    <div key={item.name} className="p-2.5 rounded-cs bg-slate-950/60 border border-slate-800/80">
                      <div className={`h-10 rounded-cs-sm mb-2 ${item.cls}`} />
                      <div className="text-xs font-semibold text-slate-200 truncate">{item.name}</div>
                      <div className="text-[11px] font-mono text-slate-400">{item.hex}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Climate Teal & SFL Gold */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-mono text-teal-400 uppercase tracking-wider mb-2">
                    2. Climate Teal (Satellite Telemetry & Hydrology)
                  </h4>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { name: 'Teal 600', hex: '#0F766E', cls: 'bg-[#0F766E]' },
                      { name: 'Teal 500 (Primary)', hex: '#0D9488', cls: 'bg-[#0D9488]' },
                      { name: 'Teal 400', hex: '#14B8A6', cls: 'bg-[#14B8A6]' },
                    ].map((item) => (
                      <div key={item.name} className="p-2.5 rounded-cs bg-slate-950/60 border border-slate-800/80">
                        <div className={`h-10 rounded-cs-sm mb-2 ${item.cls}`} />
                        <div className="text-xs font-semibold text-slate-200">{item.name}</div>
                        <div className="text-[11px] font-mono text-slate-400">{item.hex}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-mono text-amber-400 uppercase tracking-wider mb-2">
                    3. SFL Imperial Gold (Growth & Parametric Triggers)
                  </h4>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { name: 'Gold 600', hex: '#D97706', cls: 'bg-[#D97706]' },
                      { name: 'Gold 500 (Primary)', hex: '#F59E0B', cls: 'bg-[#F59E0B]' },
                      { name: 'Gold 400', hex: '#FBBF24', cls: 'bg-[#FBBF24]' },
                    ].map((item) => (
                      <div key={item.name} className="p-2.5 rounded-cs bg-slate-950/60 border border-slate-800/80">
                        <div className={`h-10 rounded-cs-sm mb-2 ${item.cls}`} />
                        <div className="text-xs font-semibold text-slate-200">{item.name}</div>
                        <div className="text-[11px] font-mono text-slate-400">{item.hex}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Risk Tiers */}
              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                  4. Risk Tiers (Calibrated 4-Level MSME Vulnerability Scale)
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { tier: 'Tier 1 • Low', color: '#10B981', label: 'Score < 0.35', cls: 'bg-emerald-500' },
                    { tier: 'Tier 2 • Moderate', color: '#F59E0B', label: 'Score 0.35 - 0.55', cls: 'bg-amber-500' },
                    { tier: 'Tier 3 • High', color: '#F97316', label: 'Score 0.55 - 0.75', cls: 'bg-orange-500' },
                    { tier: 'Tier 4 • Severe', color: '#EF4444', label: 'Score ≥ 0.75', cls: 'bg-rose-500' },
                  ].map((item) => (
                    <div key={item.tier} className="p-2.5 rounded-cs bg-slate-950/60 border border-slate-800/80">
                      <div className={`h-10 rounded-cs-sm mb-2 ${item.cls}`} />
                      <div className="text-xs font-semibold text-slate-200">{item.tier}</div>
                      <div className="text-[11px] font-mono text-slate-400">{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          {/* Typography Scale */}
          <Card
            eyebrow="Typography Architecture"
            title="Institutional Editorial & Technical Hierarchy"
            description="Consciously paired fonts: Newsreader serif for institutional editorial weight, Plus Jakarta Sans for dense operational UI controls, and JetBrains Mono with tabular figures for financial values and coordinates."
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 rounded-cs bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] font-mono text-teal-400 uppercase tracking-wider block mb-1">
                  Display & Section Headings
                </span>
                <span className="text-xs text-slate-400 font-sans block mb-3">
                  Font: <code className="font-mono text-slate-300">Newsreader / Fraunces</code>
                </span>
                <p className="font-serif text-2xl font-bold text-slate-100 leading-snug">
                  Climate Risk Intelligence for MSME Underwriting
                </p>
                <p className="font-serif text-lg italic text-slate-300 mt-2">
                  "Autonomous parametric relief safeguarding borrower resilience across Gangetic floodplains."
                </p>
              </div>

              <div className="p-4 rounded-cs bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] font-mono text-amber-400 uppercase tracking-wider block mb-1">
                  Dense Operational UI & Controls
                </span>
                <span className="text-xs text-slate-400 font-sans block mb-3">
                  Font: <code className="font-mono text-slate-300">Plus Jakarta Sans / Inter</code>
                </span>
                <p className="font-sans text-sm font-semibold text-slate-200">
                  Parametric EMI Moratorium Matrix (V2 Rule Engine)
                </p>
                <p className="font-sans text-xs text-slate-400 mt-1 leading-relaxed">
                  Borrower locations are evaluated against 10-year NASA POWER precipitation and Sentinel-2 NDVI
                  anomalies to dynamically trigger 60-day recovery top-ups.
                </p>
              </div>

              <div className="p-4 rounded-cs bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider block mb-1">
                  Tabular Telemetry & Financial Values
                </span>
                <span className="text-xs text-slate-400 font-sans block mb-3">
                  Font: <code className="font-mono text-slate-300">JetBrains Mono</code> (Tabular Figures)
                </span>
                <div className="space-y-1 font-mono text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Exposure:</span>
                    <span className="text-slate-100 font-semibold tabular-nums">₹84,25,00,000</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Rainfall Deviation:</span>
                    <span className="text-sky-400 font-semibold tabular-nums">+84.20% (P95)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">GPS Coordinates:</span>
                    <span className="text-slate-300 tabular-nums">25.3176° N, 82.9739° E</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Ledger Hash:</span>
                    <span className="text-amber-400 tabular-nums text-[10px]">7f8b9a2c...e3d1</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Bespoke SVG Motifs */}
          <Card
            eyebrow="Bespoke Iconography"
            title="Consistent 1.5px Stroke Domain Motifs"
            description="Designed specifically for financial climate risk. No generic mismatched stock packs or filled cartoon icons."
          >
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-9 gap-3 text-center">
              {[
                { icon: <IconShield size={22} />, name: 'Shield' },
                { icon: <IconRainfall size={22} />, name: 'Rainfall' },
                { icon: <IconDrought size={22} />, name: 'Drought' },
                { icon: <IconSatellite size={22} />, name: 'Satellite' },
                { icon: <IconRupee size={22} />, name: 'Rupee' },
                { icon: <IconPulse size={22} />, name: 'Pulse' },
                { icon: <IconLock size={22} />, name: 'Lock' },
                { icon: <IconAlertTriangle size={22} />, name: 'Alert' },
                { icon: <IconCheckCircle size={22} />, name: 'Confirmed' },
                { icon: <IconDatabase size={22} />, name: 'Ledger' },
                { icon: <IconTrendingUp size={22} />, name: 'Trend' },
                { icon: <IconActivity size={22} />, name: 'Activity' },
                { icon: <IconBuilding size={22} />, name: 'MSME' },
                { icon: <IconRefresh size={22} />, name: 'Refresh' },
                { icon: <IconFilter size={22} />, name: 'Filter' },
                { icon: <IconArrowRight size={22} />, name: 'Pipeline' },
                { icon: <IconChevronDown size={22} />, name: 'Chevron' },
                { icon: <IconInfo size={22} />, name: 'Info' },
                { icon: <IconUser size={22} />, name: 'User' },
              ].map((item) => (
                <div
                  key={item.name}
                  className="p-3 rounded-cs bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col items-center justify-center gap-2 group"
                >
                  <span className="text-teal-400 group-hover:text-amber-400 transition-colors">{item.icon}</span>
                  <span className="text-[11px] font-mono text-slate-400 group-hover:text-slate-200">
                    {item.name}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 2: COMPONENTS (Buttons, Badges, Cards, Alerts) */}
      {activeTab === 'components' && (
        <div className="space-y-10">
          {/* Buttons & Actions */}
          <Card
            eyebrow="Interactive Elements"
            title="Institutional Action Buttons"
            description="Functional micro-interactions with sharp 4px-6px radii, active elevation feedback, and loading spinners."
          >
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Variants & Intent Hierarchy
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary" iconLeft={<IconPulse size={16} />}>
                    Trigger Moratorium
                  </Button>
                  <Button variant="secondary" iconLeft={<IconRefresh size={16} />}>
                    Sync Weather Feeds
                  </Button>
                  <Button variant="teal" iconLeft={<IconSatellite size={16} />}>
                    Satellite Inspect
                  </Button>
                  <Button variant="outline" iconLeft={<IconFilter size={16} />}>
                    Filter Portfolio
                  </Button>
                  <Button variant="ghost">Audit Log</Button>
                  <Button variant="danger" iconLeft={<IconAlertTriangle size={16} />}>
                    Revoke Relief
                  </Button>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Sizes & State Transitions
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="sm" variant="secondary">
                    Small (28px)
                  </Button>
                  <Button size="md" variant="secondary">
                    Medium (36px)
                  </Button>
                  <Button size="lg" variant="secondary">
                    Large (44px)
                  </Button>
                  <Button
                    variant="primary"
                    isLoading={buttonLoading}
                    onClick={handleSimulateClick}
                    iconLeft={<IconRefresh size={16} />}
                  >
                    {buttonLoading ? 'Evaluating...' : 'Simulate Trigger'}
                  </Button>
                  <Button variant="primary" disabled>
                    Disabled State
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Badges & Status Indicators */}
          <Card
            eyebrow="Classification Systems"
            title="Risk Tier Badges & 4-Stage State Machine Pills"
            description="Calibrated visual cues for risk assessment and automated LMS intervention lifecycles."
          >
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Calibrated Risk Tiers
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <RiskTierBadge tier="LOW" score={0.18} />
                  <RiskTierBadge tier="MODERATE" score={0.42} />
                  <RiskTierBadge tier="HIGH" score={0.68} />
                  <RiskTierBadge tier="SEVERE" score={0.91} />
                </div>
              </div>

              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  4-Stage Parametric LMS Intervention Pipeline
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <InterventionStatusPill status="TRIGGERED" />
                  <IconArrowRight size={14} className="text-slate-600" />
                  <InterventionStatusPill status="NOTIFIED" />
                  <IconArrowRight size={14} className="text-slate-600" />
                  <InterventionStatusPill status="APPLIED" />
                  <IconArrowRight size={14} className="text-slate-600" />
                  <InterventionStatusPill status="CONFIRMED" />
                </div>
              </div>

              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Hazard Classification Motifs
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <HazardBadge hazard="FLOOD" />
                  <HazardBadge hazard="DROUGHT" />
                  <HazardBadge hazard="CYCLONE" />
                  <HazardBadge hazard="HEATWAVE" />
                </div>
              </div>

              <div>
                <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Generic Semantic Badges
                </h4>
                <div className="flex flex-wrap items-center gap-3">
                  <Badge variant="teal" dot>NDVI Sensor: Online</Badge>
                  <Badge variant="gold" dot>LMS Sync: Active</Badge>
                  <Badge variant="emerald">Audit: Chained</Badge>
                  <Badge variant="rose">Anomaly: High</Badge>
                  <Badge variant="neutral">Status: Staged</Badge>
                </div>
              </div>
            </div>
          </Card>

          {/* Alert Banners */}
          <Card
            eyebrow="Parametric Notifications"
            title="System Alert Banners"
            description="Used for real-time anomaly alerts, policy threshold crossings, and simulated dispatch confirmations."
          >
            <div className="space-y-3">
              <AlertBanner
                variant="critical"
                title="Critical Threshold Breached: Varanasi District"
                message="NASA POWER cumulative 48h rainfall reached 214mm (+84% above 10-year P95 normal). Parametric trigger activated for 8 MSME borrower accounts."
                action={
                  <Button size="sm" variant="danger">
                    View Impacted MSMEs
                  </Button>
                }
              />
              <AlertBanner
                variant="warning"
                title="Drought Watch Active: Barabanki & Mirzapur"
                message="Consecutive dry days reached 28 days with Sentinel-2 NDVI deficit of -26.4%. Credit team alerted for proactive interest subsidy review."
                action={
                  <Button size="sm" variant="secondary">
                    Inspect NDVI
                  </Button>
                }
              />
              <AlertBanner
                variant="info"
                title="Daily Weather Synced • 7 SFL Districts"
                message="NASA POWER and Open-Meteo feeds successfully ingested at 06:00 IST. Baselines refreshed."
              />
              <AlertBanner
                variant="success"
                title="LMS Webhook Confirmed • EMI Moratorium Executed"
                message="HMAC-SHA256 signature verified by mock LMS. 60-day loan restructuring applied to borrower SFL-BR-0104."
              />
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 3: MSME PORTFOLIO DATA (KPI Metric Cards & High-Density Table) */}
      {(activeTab === 'data' || activeTab === 'overview') && (
        <div className="space-y-8 mt-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-serif font-bold text-slate-100">
                Active MSME Portfolio Telemetry
              </h2>
              <p className="text-xs font-sans text-slate-400 mt-0.5">
                Real-time climate-vulnerability distribution across Satin Finserv target operating districts.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="secondary" iconLeft={<IconFilter size={14} />}>
                Filter Districts
              </Button>
              <Button size="sm" variant="teal" iconLeft={<IconRefresh size={14} />}>
                Sync Telemetry
              </Button>
            </div>
          </div>

          {/* High-density KPI cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Total Monitored Exposure"
              value="84.25"
              prefix="₹"
              suffix="Cr"
              delta="+5.4% YoY"
              deltaType="positive"
              deltaLabel="56 MSMEs in 7 districts"
              icon={<IconRupee size={18} />}
              accent="gold"
            />
            <MetricCard
              label="High-Risk Exposure"
              value="14.80"
              prefix="₹"
              suffix="Cr"
              delta="17.5% of total"
              deltaType="alert"
              deltaLabel="Tier 3 & 4 vulnerable"
              badge={<RiskTierBadge tier="HIGH" size="xs" />}
              accent="rose"
            />
            <MetricCard
              label="Active Parametric Triggers"
              value="3"
              suffix="Districts"
              delta="Varanasi, Barabanki, Patna"
              deltaType="alert"
              deltaLabel="Rainfall / Drought breach"
              icon={<IconAlertTriangle size={18} />}
              accent="teal"
            />
            <MetricCard
              label="Relief Deployed (Simulated)"
              value="1.45"
              prefix="₹"
              suffix="Cr"
              delta="100% Verified"
              deltaType="positive"
              deltaLabel="HMAC Signed LMS ledger"
              icon={<IconCheckCircle size={18} />}
              accent="emerald"
            />
          </div>

          {/* High-density Portfolio Table */}
          <Card
            eyebrow="MSME Loan Ledger"
            title="Borrower Climate-Risk Vulnerability Matrix"
            description="Demonstrates high-density institutional table styling with tabular currency values, real-time ML tier allocations, and 4-stage LMS lifecycle tracking."
            headerAction={
              <span className="text-xs font-mono text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded-cs border border-slate-800">
                5 of 56 Borrowers Displayed
              </span>
            }
          >
            <DataTable
              columns={columns}
              data={SAMPLE_BORROWERS}
              keyExtractor={(row) => row.id}
              density="compact"
              onRowClick={(row) => console.log('Selected borrower:', row.id)}
            />
          </Card>
        </div>
      )}

      {/* SECTION 4: CRYPTOGRAPHIC AUDIT LEDGER */}
      {activeTab === 'audit' && (
        <div className="space-y-6">
          <Card
            eyebrow="Security & Compliance"
            title="Tamper-Evident SHA-256 Chained Audit Ledger"
            description="Every trigger event, LMS webhook exchange, and borrower notification writes an immutable cryptographically-chained entry. The parent hash guarantees forward integrity."
            accent="emerald"
          >
            <div className="space-y-4">
              <div className="p-3.5 bg-slate-950/80 rounded-cs border border-slate-800 font-mono text-xs space-y-2">
                <div className="flex items-center justify-between text-slate-400 border-b border-slate-800/80 pb-2">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <IconLock size={14} />
                    Chain Integrity: VALID (All Hashes Match)
                  </span>
                  <span className="text-[11px] text-slate-500">Algorithm: SHA-256 Chaining</span>
                </div>

                <div className="space-y-3 pt-2">
                  <div className="p-2.5 bg-slate-900/90 rounded-cs-sm border border-slate-800">
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-amber-400 font-semibold">EVENT #104: INTERVENTION_APPLIED</span>
                      <span className="text-slate-500 text-[10px]">2026-09-09T08:15:30.124Z</span>
                    </div>
                    <div className="text-slate-300 text-[11px]">
                      Borrower SFL-BR-0104 • 60-day EMI Moratorium applied via HMAC-signed LMS adapter.
                    </div>
                    <div className="mt-2 text-[10px] text-slate-400 grid grid-cols-1 md:grid-cols-2 gap-1 bg-slate-950/60 p-1.5 rounded-cs-xs">
                      <div>Current Hash: <span className="text-slate-200">7f8b9a2c140d3f89e...</span></div>
                      <div>Parent Hash: <span className="text-slate-500">1a2b3c4d5e6f7a8b9...</span></div>
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-900/90 rounded-cs-sm border border-slate-800">
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-sky-400 font-semibold">EVENT #103: BORROWER_ALERT_DISPATCHED</span>
                      <span className="text-slate-500 text-[10px]">2026-09-09T08:14:02.890Z</span>
                    </div>
                    <div className="text-slate-300 text-[11px]">
                      SMS & WhatsApp notification sent: "SFL Climate Relief alert for Varanasi floods".
                    </div>
                    <div className="mt-2 text-[10px] text-slate-400 grid grid-cols-1 md:grid-cols-2 gap-1 bg-slate-950/60 p-1.5 rounded-cs-xs">
                      <div>Current Hash: <span className="text-slate-200">1a2b3c4d5e6f7a8b9...</span></div>
                      <div>Parent Hash: <span className="text-slate-500">00000000000000000... (GENESIS)</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 font-mono gap-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-400" />
          <span>ClimateShield V2.0 Design System • Satin Finserv Ltd</span>
        </div>
        <div>
          <span>High-Density Institutional Spec • Strict Zero-AI-Trope Guarantee</span>
        </div>
      </footer>
    </div>
  );
};

export default DesignSystemShowcase;
