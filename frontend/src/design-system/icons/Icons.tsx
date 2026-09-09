import React from 'react';

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  className?: string;
  strokeWidth?: number;
}

const defaultProps = {
  size: 20,
  strokeWidth: 1.5,
  fill: 'none',
  stroke: 'currentColor',
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export const IconShield: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

export const IconRainfall: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
    <path d="M8 17v4" />
    <path d="M12 19v4" />
    <path d="M16 17v4" />
  </svg>
);

export const IconDrought: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <circle cx="12" cy="7" r="4" />
    <path d="M12 1v2" />
    <path d="M12 11v2" />
    <path d="M4.93 4.93l1.41 1.41" />
    <path d="M17.66 17.66l1.41 1.41" />
    <path d="M2 19h20" />
    <path d="M6 19l4 4" />
    <path d="M14 19l-3 3" />
    <path d="M18 19l2 3" />
  </svg>
);

export const IconSatellite: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M13 7 9 3 5 7l4 4" />
    <path d="m17 11 4 4-4 4-4-4" />
    <path d="m8 12 4 4" />
    <path d="m16 8-4-4" />
    <path d="M12 12l-6 6" />
    <circle cx="5" cy="19" r="2" />
    <path d="M14.5 4.5 19.5 9.5" />
  </svg>
);

export const IconRupee: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M6 3h12" />
    <path d="M6 8h12" />
    <path d="M6 13h4c3 0 5-2 5-5H6" />
    <path d="m9 13 8 8" />
  </svg>
);

export const IconPulse: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

export const IconLock: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

export const IconAlertTriangle: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
    <path d="M12 9v4" />
    <path d="M12 17h.01" />
  </svg>
);

export const IconCheckCircle: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <circle cx="12" cy="12" r="10" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

export const IconInfo: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M12 16v-4" />
    <path d="M12 8h.01" />
  </svg>
);

export const IconChevronDown: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export const IconFilter: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
);

export const IconArrowRight: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M5 12h14" />
    <path d="m12 5 7 7-7 7" />
  </svg>
);

export const IconTrendingUp: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
    <polyline points="16 7 22 7 22 13" />
  </svg>
);

export const IconActivity: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

export const IconBuilding: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
    <path d="M9 22v-4h6v4" />
    <path d="M8 6h.01" />
    <path d="M16 6h.01" />
    <path d="M8 10h.01" />
    <path d="M16 10h.01" />
    <path d="M8 14h.01" />
    <path d="M16 14h.01" />
  </svg>
);

export const IconRefresh: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
    <path d="M21 3v5h-5" />
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
    <path d="M8 16H3v5" />
  </svg>
);

export const IconDatabase: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <ellipse cx="12" cy="5" rx="9" ry="3" />
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" />
  </svg>
);

export const IconUser: React.FC<IconProps> = ({ size = 20, strokeWidth = 1.5, className = '', ...props }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    {...defaultProps}
    strokeWidth={strokeWidth}
    className={className}
    {...props}
  >
    <circle cx="12" cy="7" r="4" />
    <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
  </svg>
);
