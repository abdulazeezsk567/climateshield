import React from 'react';

export interface MetricCardProps {
  label: string;
  value: string | number;
  prefix?: string;
  suffix?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral' | 'alert';
  deltaLabel?: string;
  subtext?: string;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
  accent?: 'none' | 'teal' | 'gold' | 'rose' | 'emerald';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  prefix,
  suffix,
  delta,
  deltaType = 'neutral',
  deltaLabel,
  subtext,
  badge,
  icon,
  className = '',
  accent = 'none',
}) => {
  const accentStyles = {
    none: '',
    teal: 'border-l-2 border-l-teal-500',
    gold: 'border-l-2 border-l-amber-500',
    rose: 'border-l-2 border-l-rose-500',
    emerald: 'border-l-2 border-l-emerald-500',
  };

  const deltaColors = {
    positive: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
    negative: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
    alert: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
    neutral: 'text-slate-400 bg-slate-800/40 border-slate-700/40',
  };

  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-cs p-4 shadow-cs-sm transition-colors duration-150 ${accentStyles[accent]} ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-medium truncate">
          {label}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          {badge}
          {icon && <span className="text-slate-500">{icon}</span>}
        </div>
      </div>

      <div className="flex items-baseline gap-1 my-1">
        {prefix && (
          <span className="text-lg font-mono font-normal text-slate-400 select-none">
            {prefix}
          </span>
        )}
        <span className="text-2xl lg:text-3xl font-mono font-bold text-slate-50 tabular-nums tracking-tight">
          {value}
        </span>
        {suffix && (
          <span className="text-sm font-mono text-slate-400 ml-1 select-none">
            {suffix}
          </span>
        )}
      </div>

      {(delta || deltaLabel || subtext) && (
        <div className="mt-2.5 pt-2 border-t border-slate-800/70 flex items-center justify-between text-xs gap-2">
          {delta && (
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded-cs-xs border font-mono text-[11px] font-medium tabular-nums ${deltaColors[deltaType]}`}
            >
              {delta}
            </span>
          )}
          <span className="text-[11px] font-sans text-slate-400 truncate text-right">
            {deltaLabel || subtext}
          </span>
        </div>
      )}
    </div>
  );
};
