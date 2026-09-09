import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'teal';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  iconLeft,
  iconRight,
  disabled,
  className = '',
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-sans font-medium transition-all duration-150 ease-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#080D17] disabled:opacity-45 disabled:cursor-not-allowed select-none rounded-cs';

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5 h-7',
    md: 'text-sm px-3.5 py-2 gap-2 h-9',
    lg: 'text-base px-4.5 py-2.5 gap-2.5 h-11',
  };

  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      'bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold focus:ring-amber-500 shadow-cs-sm active:translate-y-px',
    secondary:
      'bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 focus:ring-slate-500 active:translate-y-px',
    outline:
      'bg-transparent hover:bg-slate-800/60 text-slate-200 border border-slate-700 hover:border-slate-500 focus:ring-slate-400 active:translate-y-px',
    ghost:
      'bg-transparent hover:bg-slate-800/50 text-slate-300 hover:text-slate-100 focus:ring-slate-500',
    danger:
      'bg-rose-900/40 hover:bg-rose-800/60 text-rose-200 border border-rose-700/60 focus:ring-rose-500 active:translate-y-px',
    teal:
      'bg-teal-600 hover:bg-teal-500 text-slate-950 font-semibold focus:ring-teal-400 shadow-cs-sm active:translate-y-px',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        iconLeft
      )}
      <span>{children}</span>
      {!isLoading && iconRight}
    </button>
  );
};
