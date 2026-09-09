import React, { useState } from 'react';
import { useAuth } from '../services/authContext.js';

export interface MaskedFieldProps {
  value: string;
  fieldName: string;
  targetId: string;
  maskPattern?: string;
  className?: string;
}

export const MaskedField: React.FC<MaskedFieldProps> = ({
  value,
  fieldName,
  targetId,
  maskPattern = '••••••••••••',
  className = '',
}) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const { logAuditEvent } = useAuth();

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isRevealed) {
      logAuditEvent('SENSITIVE_FIELD_REVEALED', fieldName, targetId);
    }
    setIsRevealed((prev) => !prev);
  };

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono ${className}`}>
      <span className={isRevealed ? 'text-slate-100' : 'text-slate-500 select-none tracking-widest'}>
        {isRevealed ? value : maskPattern}
      </span>
      <button
        type="button"
        onClick={handleToggle}
        title={isRevealed ? 'Mask field' : 'Reveal sensitive value (access logged to audit trail)'}
        className="p-0.5 rounded text-slate-500 hover:text-amber-400 hover:bg-slate-800/80 transition-colors focus:outline-none focus:ring-1 focus:ring-amber-500"
        aria-label={isRevealed ? 'Hide sensitive data' : 'Reveal sensitive data'}
      >
        {isRevealed ? (
          // Eye-off icon
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
            <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
            <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
            <line x1="2" x2="22" y1="2" y2="22" />
          </svg>
        ) : (
          // Eye icon
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </span>
  );
};
