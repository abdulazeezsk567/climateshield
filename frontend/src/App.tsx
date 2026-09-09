import React, { useState } from 'react';
import { AuthProvider, useAuth } from './services/authContext.js';
import { Navbar, ActiveNavTab } from './components/Navbar.js';
import { LoginView } from './components/LoginView.js';
import { PortfolioDashboard } from './views/PortfolioDashboard.js';
import { TriggerSimulator } from './views/TriggerSimulator.js';
import { InterventionLog } from './views/InterventionLog.js';
import { AuditLedgerView } from './views/AuditLedgerView.js';
import { DesignSystemShowcase } from './design-system/Showcase.js';

const MainShell: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveNavTab>('portfolio');
  const [simulatorDistrict, setSimulatorDistrict] = useState<string>('Varanasi');
  const [targetCorrelationId, setTargetCorrelationId] = useState<string>('');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#080D17] text-slate-100 flex flex-col items-center justify-center font-mono">
        <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mb-3" />
        <span className="text-xs text-slate-400 tracking-wider">INITIALIZING CLIMATESHIELD GATEWAY...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const handleNavigateToSimulator = (districtName?: string) => {
    if (districtName) {
      setSimulatorDistrict(districtName);
    }
    setActiveTab('simulator');
  };

  const handleNavigateToInterventions = (correlationId?: string) => {
    if (correlationId) {
      setTargetCorrelationId(correlationId);
    }
    setActiveTab('interventions');
  };

  return (
    <div className="min-h-screen bg-[#080D17] text-slate-100 flex flex-col selection:bg-teal-500/30 selection:text-white">
      {/* Top Institutional Navbar */}
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Viewport */}
      <main className="flex-1 pb-16">
        {activeTab === 'portfolio' && (
          <PortfolioDashboard onNavigateToSimulator={handleNavigateToSimulator} />
        )}
        {activeTab === 'simulator' && (
          <TriggerSimulator
            initialDistrict={simulatorDistrict}
            onNavigateToInterventions={handleNavigateToInterventions}
          />
        )}
        {activeTab === 'interventions' && (
          <InterventionLog
            initialCorrelationId={targetCorrelationId}
            onNavigateToAudit={() => setActiveTab('audit')}
          />
        )}
        {activeTab === 'audit' && <AuditLedgerView />}
        {activeTab === 'tokens' && <DesignSystemShowcase />}
      </main>

      {/* Global Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 px-6 py-4 text-xs font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>Satin Finserv Ltd • ClimateShield V2.4 Enterprise Production Track</span>
        </div>
        <div>
          <span>ISO 27001 Certified • Parametric MSME Protection Layer</span>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainShell />
    </AuthProvider>
  );
};

export default App;
