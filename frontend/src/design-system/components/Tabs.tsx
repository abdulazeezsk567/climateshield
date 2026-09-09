import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  size?: 'sm' | 'md';
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  className = '',
  size = 'md',
}) => {
  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1 gap-1.5',
    md: 'text-sm px-3.5 py-1.5 gap-2',
  };

  return (
    <div
      className={`inline-flex items-center bg-slate-950/80 border border-slate-800 p-0.5 rounded-cs ${className}`}
      role="tablist"
    >
      {items.map((item) => {
        const isActive = item.id === activeId;
        return (
          <button
            key={item.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(item.id)}
            className={`inline-flex items-center justify-center font-mono font-medium rounded-cs transition-all duration-150 focus:outline-none select-none ${
              sizeStyles[size]
            } ${
              isActive
                ? 'bg-slate-800 text-amber-400 border border-slate-700 shadow-cs-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 border border-transparent'
            }`}
          >
            {item.icon}
            <span>{item.label}</span>
            {item.badge !== undefined && (
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded-cs-xs ${
                  isActive
                    ? 'bg-amber-950/70 text-amber-300 border border-amber-800/60'
                    : 'bg-slate-800/80 text-slate-400 border border-slate-700/60'
                }`}
              >
                {item.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
