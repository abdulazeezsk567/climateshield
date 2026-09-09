import { IconAlertTriangle, IconCheckCircle, IconInfo } from '../icons/Icons.js';

export type AlertVariant = 'critical' | 'warning' | 'info' | 'success';

export interface AlertBannerProps {
  variant?: AlertVariant;
  title: string;
  message?: React.ReactNode;
  action?: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  variant = 'warning',
  title,
  message,
  action,
  onClose,
  className = '',
}) => {
  const variantStyles: Record<
    AlertVariant,
    { container: string; icon: React.ReactNode; titleColor: string }
  > = {
    critical: {
      container: 'bg-rose-950/40 border-rose-800/80 text-rose-200',
      icon: <IconAlertTriangle size={18} className="text-rose-400 shrink-0 mt-0.5" />,
      titleColor: 'text-rose-300',
    },
    warning: {
      container: 'bg-amber-950/40 border-amber-800/80 text-amber-200',
      icon: <IconAlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />,
      titleColor: 'text-amber-300',
    },
    info: {
      container: 'bg-teal-950/40 border-teal-800/80 text-teal-200',
      icon: <IconInfo size={18} className="text-teal-400 shrink-0 mt-0.5" />,
      titleColor: 'text-teal-300',
    },
    success: {
      container: 'bg-emerald-950/40 border-emerald-800/80 text-emerald-200',
      icon: <IconCheckCircle size={18} className="text-emerald-400 shrink-0 mt-0.5" />,
      titleColor: 'text-emerald-300',
    },
  };

  const current = variantStyles[variant];

  return (
    <div
      className={`rounded-cs border p-3.5 flex items-start justify-between gap-3 text-sm transition-all duration-150 ${current.container} ${className}`}
    >
      <div className="flex items-start gap-2.5">
        {current.icon}
        <div>
          <h4 className={`font-semibold text-xs tracking-wide uppercase font-mono ${current.titleColor}`}>
            {title}
          </h4>
          {message && (
            <div className="mt-1 text-xs text-slate-300 font-sans leading-relaxed">
              {message}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {action}
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-xs p-1 focus:outline-none"
            aria-label="Dismiss alert"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
