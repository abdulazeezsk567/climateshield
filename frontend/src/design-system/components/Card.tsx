import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  eyebrow?: string;
  description?: string;
  headerAction?: React.ReactNode;
  accent?: 'none' | 'teal' | 'gold' | 'rose' | 'emerald';
  density?: 'compact' | 'normal' | 'spacious';
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  eyebrow,
  description,
  headerAction,
  accent = 'none',
  density = 'normal',
  className = '',
}) => {
  const accentStyles = {
    none: '',
    teal: 'border-t-2 border-t-teal-500',
    gold: 'border-t-2 border-t-amber-500',
    rose: 'border-t-2 border-t-rose-500',
    emerald: 'border-t-2 border-t-emerald-500',
  };

  const paddingStyles = {
    compact: 'p-3',
    normal: 'p-5',
    spacious: 'p-6',
  };

  const hasHeader = Boolean(title || eyebrow || description || headerAction);

  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-cs shadow-cs-sm transition-colors duration-150 ${accentStyles[accent]} ${className}`}
    >
      {hasHeader && (
        <div className={`border-b border-slate-800/80 ${density === 'compact' ? 'px-3 py-2.5' : 'px-5 py-3.5'} flex items-start justify-between gap-4`}>
          <div>
            {eyebrow && (
              <p className="text-[11px] font-mono tracking-wider uppercase text-slate-400 font-semibold mb-0.5">
                {eyebrow}
              </p>
            )}
            {title && (
              <h3 className="font-serif text-lg font-medium text-slate-100 leading-snug">
                {title}
              </h3>
            )}
            {description && (
              <p className="text-xs font-sans text-slate-400 mt-0.5 leading-relaxed">
                {description}
              </p>
            )}
          </div>
          {headerAction && <div className="shrink-0">{headerAction}</div>}
        </div>
      )}
      <div className={paddingStyles[density]}>{children}</div>
    </div>
  );
};
