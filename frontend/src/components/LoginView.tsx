import React, { useState } from 'react';
import { useAuth } from '../services/authContext.js';
import { Button, Card } from '../design-system/index.js';
import { IconShield, IconLock, IconUser, IconAlertTriangle } from '../design-system/icons/index.js';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('officer_sfl');
  const [password, setPassword] = useState('SFLCreditRisk@2026!');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    try {
      await login(username, password);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Invalid credentials. Please verify username and password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-[#080D17] text-slate-100 flex flex-col justify-center items-center p-4 sm:p-6 select-none">
      {/* Background Ambience */}
      <div className="w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-cs-sm bg-teal-950/60 border border-teal-800/80 text-teal-400 mb-2">
            <IconShield size={18} />
            <span className="text-[11px] font-mono tracking-widest uppercase font-semibold">
              Satin Finserv Ltd • ClimateShield
            </span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-slate-50 tracking-tight">
            Institutional Gateway
          </h1>
          <p className="text-xs font-sans text-slate-400 max-w-sm mx-auto">
            Parametric Climate-Risk Intelligence & Automated LMS Relief for MSME Lending Portfolios.
          </p>
        </div>

        {/* Login Card */}
        <Card
          accent="gold"
          title="Sign in to Terminal"
          eyebrow="Authentication Required"
          description="Protected by salted bcrypt verification and per-token rate limiting."
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMessage && (
              <div className="p-3 bg-rose-950/50 border border-rose-800/80 rounded-cs text-rose-200 text-xs flex items-start gap-2">
                <IconAlertTriangle size={16} className="text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1">
                Authorized Identifier
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-cs text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500 font-mono"
                  placeholder="e.g. officer_sfl"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1">
                Security Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-cs text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500 font-mono"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              isLoading={isLoading}
              className="w-full"
              iconLeft={<IconLock size={16} />}
            >
              Authenticate Session
            </Button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-4 border-t border-slate-800/80 space-y-2">
            <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
              Quick-Fill Evaluator Credentials
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('officer_sfl', 'SFLCreditRisk@2026!')}
                className="p-2 text-left bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 hover:border-amber-500/60 rounded-cs text-xs transition-colors"
              >
                <div className="font-medium text-amber-400 flex items-center gap-1">
                  <IconUser size={13} />
                  <span>officer_sfl</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                  Role: credit_team (Full)
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill('judge_auditor', 'ViewerJudge@2026!')}
                className="p-2 text-left bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 hover:border-teal-500/60 rounded-cs text-xs transition-colors"
              >
                <div className="font-medium text-teal-400 flex items-center gap-1">
                  <IconUser size={13} />
                  <span>judge_auditor</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                  Role: viewer (Read-Only)
                </div>
              </button>
            </div>
          </div>
        </Card>

        {/* Security Disclaimers */}
        <div className="text-center text-[11px] font-mono text-slate-500">
          <span>Satin Finserv Ltd • Confidential Underwriting System • ISO 27001</span>
        </div>
      </div>
    </div>
  );
};
