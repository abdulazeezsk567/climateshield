import React from 'react';
import { useAuth } from '../services/authContext.js';
import {
  IconShield,
  IconActivity,
  IconSatellite,
  IconCheckCircle,
  IconLock,
  IconUser,
  IconRefresh,
} from '../design-system/icons/index.js';
import { UserRole } from '../types/index.js';

export type ActiveNavTab = 'portfolio' | 'simulator' | 'interventions' | 'audit' | 'tokens';

export interface NavbarProps {
  activeTab: ActiveNavTab;
  onTabChange: (tab: ActiveNavTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  const { user, role, switchDemoRole, logout } = useAuth();

  const navItems: { id: ActiveNavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'portfolio', label: 'Portfolio Risk', icon: <IconSatellite size={16} /> },
    { id: 'simulator', label: 'Trigger Simulator', icon: <IconActivity size={16} /> },
    { id: 'interventions', label: 'Intervention Log', icon: <IconCheckCircle size={16} /> },
    { id: 'audit', label: 'Audit Ledger', icon: <IconLock size={16} /> },
    { id: 'tokens', label: 'Design Tokens', icon: <IconShield size={16} /> },
  ];

  const handleRoleToggle = () => {
    const nextRole: UserRole = role === 'credit_team' ? 'viewer' : 'credit_team';
    switchDemoRole(nextRole);
  };

  return (
    <header className="sticky top-0 z-40 bg-[#080D17]/95 backdrop-blur border-b border-slate-800 select-none">
      {/* Top Status Bar */}
      <div className="bg-slate-950 border-b border-slate-800/80 px-4 sm:px-6 py-1.5 flex flex-wrap items-center justify-between text-[11px] font-mono">
        <div className="flex items-center gap-3">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-300 font-semibold tracking-wide">
            SFL-GATEWAY : ONLINE
          </span>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-slate-400 hidden sm:inline">SATIN FINSERV MSME RISK OPS</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 uppercase tracking-wider">Active Role:</span>
            <span
              className={`px-2 py-0.5 rounded-cs text-[10px] font-bold uppercase tracking-wider border ${
                role === 'credit_team'
                  ? 'bg-amber-950/70 text-amber-300 border-amber-800/80'
                  : 'bg-teal-950/70 text-teal-300 border-teal-800/80'
              }`}
            >
              {role === 'credit_team' ? 'Credit Team (Full)' : 'Viewer (Judge Mode)'}
            </span>
            <button
              type="button"
              onClick={handleRoleToggle}
              title="Toggle role between credit_team and viewer for live evaluation"
              className="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600 text-[10px] inline-flex items-center gap-1 transition-colors"
            >
              <IconRefresh size={11} />
              <span>Switch Role</span>
            </button>
          </div>

          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <span className="text-slate-400 flex items-center gap-1">
              <IconUser size={12} />
              <span>{user?.username}</span>
            </span>
            <button
              type="button"
              onClick={logout}
              className="text-slate-500 hover:text-rose-400 text-[11px] font-mono transition-colors ml-1"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="px-4 sm:px-6 py-2.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-cs-sm bg-teal-950/70 border border-teal-800/80 text-teal-400 shrink-0">
            <IconShield size={20} />
          </div>
          <div>
            <div className="text-xs font-mono font-bold tracking-widest text-teal-400 uppercase">
              Satin Finserv Ltd
            </div>
            <div className="text-lg font-serif font-bold text-slate-100 tracking-tight leading-none">
              ClimateShield
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0" role="tablist">
          {navItems.map((item) => {
            const isActive = item.id === activeTab;
            return (
              <button
                key={item.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => onTabChange(item.id)}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-cs text-xs font-mono font-medium whitespace-nowrap transition-all duration-150 focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                  isActive
                    ? 'bg-slate-800 text-amber-400 border border-slate-700 shadow-cs-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
