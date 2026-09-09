import React from 'react';

export type RiskTier = 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';
export type InterventionStatus = 'TRIGGERED' | 'NOTIFIED' | 'APPLIED' | 'CONFIRMED';
export type HazardType = 'FLOOD' | 'DROUGHT' | 'CYCLONE' | 'HEATWAVE';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'neutral' | 'teal' | 'gold' | 'emerald' | 'amber' | 'orange' | 'rose' | 'sky';
  size?: 'xs' | 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  className = '',
}) => {
  const sizeStyles = {
    xs: 'text-[10px] px-1.5 py-0.5 tracking-wider',
    sm: 'text-xs px-2 py-0.5 tracking-wide',
    md: 'text-sm px-2.5 py-1 tracking-normal',
  };

  const variantStyles = {
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
    teal: 'bg-teal-950/70 text-teal-300 border-teal-800/80',
    gold: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
    emerald: 'bg-emerald-950/70 text-emerald-300 border-emerald-800/80',
    amber: 'bg-amber-950/70 text-amber-300 border-amber-800/80',
    orange: 'bg-orange-950/70 text-orange-300 border-orange-800/80',
    rose: 'bg-rose-950/70 text-rose-300 border-rose-800/80',
    sky: 'bg-sky-950/70 text-sky-300 border-sky-800/80',
  };

  const dotColors = {
    neutral: 'bg-slate-400',
    teal: 'bg-teal-400',
    gold: 'bg-amber-400',
    emerald: 'bg-emerald-400',
    amber: 'bg-amber-400',
    orange: 'bg-orange-400',
    rose: 'bg-rose-400',
    sky: 'bg-sky-400',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium uppercase border rounded-cs ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};

export interface RiskTierBadgeProps {
  tier: RiskTier;
  size?: 'xs' | 'sm' | 'md';
  score?: number;
  className?: string;
}

export const RiskTierBadge: React.FC<RiskTierBadgeProps> = ({ tier, size = 'sm', score, className = '' }) => {
  const tierConfig: Record<
    RiskTier,
    { variant: BadgeProps['variant']; label: string; scoreRange?: string }
  > = {
    LOW: { variant: 'emerald', label: 'Tier 1 • Low Risk' },
    MODERATE: { variant: 'amber', label: 'Tier 2 • Moderate' },
    HIGH: { variant: 'orange', label: 'Tier 3 • High Risk' },
    SEVERE: { variant: 'rose', label: 'Tier 4 • Severe' },
  };

  const config = tierConfig[tier] || tierConfig.LOW;

  return (
    <Badge variant={config.variant} size={size} dot className={className}>
      <span>{config.label}</span>
      {score !== undefined && (
        <span className="opacity-75 tabular-nums font-semibold">({score.toFixed(1)})</span>
      )}
    </Badge>
  );
};

export interface InterventionStatusPillProps {
  status: InterventionStatus;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

export const InterventionStatusPill: React.FC<InterventionStatusPillProps> = ({
  status,
  size = 'sm',
  className = '',
}) => {
  const statusConfig: Record<
    InterventionStatus,
    { variant: BadgeProps['variant']; label: string; pulse?: boolean }
  > = {
    TRIGGERED: { variant: 'gold', label: '1. TRIGGERED', pulse: true },
    NOTIFIED: { variant: 'sky', label: '2. NOTIFIED', pulse: false },
    APPLIED: { variant: 'teal', label: '3. APPLIED', pulse: false },
    CONFIRMED: { variant: 'emerald', label: '4. CONFIRMED', pulse: false },
  };

  const config = statusConfig[status] || { variant: 'neutral', label: status };

  return (
    <Badge variant={config.variant} size={size} className={className}>
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          config.pulse ? 'bg-amber-400 animate-ping inline-block' : 'bg-current'
        }`}
      />
      <span>{config.label}</span>
    </Badge>
  );
};

export interface HazardBadgeProps {
  hazard: HazardType;
  size?: 'xs' | 'sm';
  className?: string;
}

export const HazardBadge: React.FC<HazardBadgeProps> = ({ hazard, size = 'xs', className = '' }) => {
  const hazardConfig: Record<HazardType, { variant: BadgeProps['variant']; label: string }> = {
    FLOOD: { variant: 'sky', label: 'Flood Surge' },
    DROUGHT: { variant: 'amber', label: 'Agricultural Drought' },
    CYCLONE: { variant: 'rose', label: 'Tropical Cyclone' },
    HEATWAVE: { variant: 'orange', label: 'Extreme Heat' },
  };

  const config = hazardConfig[hazard] || { variant: 'neutral', label: hazard };

  return (
    <Badge variant={config.variant} size={size} className={className}>
      {config.label}
    </Badge>
  );
};
