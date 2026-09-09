import React, { useEffect, useState } from 'react';
import { useAuth } from '../services/authContext.js';
import { apiClient } from '../services/apiClient.js';
import { AuditLogEntry, AuditVerificationResponse } from '../types/index.js';
import {
  Button,
  Card,
  MetricCard,
} from '../design-system/index.js';
import {
  IconLock,
  IconCheckCircle,
  IconAlertTriangle,
  IconRefresh,
  IconActivity,
  IconShield,
} from '../design-system/icons/index.js';

export const AuditLedgerView: React.FC = () => {
  const { auditEvents } = useAuth();

  const [verification, setVerification] = useState<AuditVerificationResponse | null>(null);
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isLoadingEntries, setIsLoadingEntries] = useState(true);

  const runVerification = async () => {
    setIsVerifying(true);
    try {
      const res = await apiClient.verifyAuditLedger();
      setVerification(res);
    } catch (e) {
      console.error('Audit verification error:', e);
    } finally {
      setIsVerifying(false);
    }
  };

  const loadAuditEntries = async () => {
    setIsLoadingEntries(true);
    try {
      const res = await apiClient.listAuditEntries({ page_size: 20 });
      setEntries(res.items);
    } catch (e) {
      console.error('Failed to load audit entries:', e);
    } finally {
      setIsLoadingEntries(false);
    }
  };

  useEffect(() => {
    runVerification();
    loadAuditEntries();
  }, []);

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-emerald-950/70 border border-emerald-800/80 text-emerald-400">
              <IconLock size={16} />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400">
              Governance & Cryptographic Audit
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100">
            Tamper-Evident SHA-256 Ledger
          </h1>
          <p className="text-xs sm:text-sm font-sans text-slate-400 mt-1">
            Every trigger anomaly, LMS restructuring execution, and sensitive borrower reveal is chained with parent-hash verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="teal"
            size="sm"
            onClick={runVerification}
            isLoading={isVerifying}
            iconLeft={<IconRefresh size={14} />}
          >
            Re-verify Chain
          </Button>
        </div>
      </div>

      {/* Verification KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Cryptographic Chain Status"
          value={verification?.chain_valid ? 'INTACT' : 'TAMPERED'}
          delta={verification?.chain_valid ? 'SHA-256 Verified' : 'Integrity Failure'}
          deltaType={verification?.chain_valid ? 'positive' : 'negative'}
          deltaLabel="Genesis to Head"
          icon={
            verification?.chain_valid ? (
              <IconCheckCircle size={18} className="text-emerald-400" />
            ) : (
              <IconAlertTriangle size={18} className="text-rose-400" />
            )
          }
          accent={verification?.chain_valid ? 'emerald' : 'rose'}
        />

        <MetricCard
          label="Chained Audit Records"
          value={verification?.total_entries ?? '—'}
          suffix="Blocks"
          delta="Immutable"
          deltaType="neutral"
          deltaLabel="Forward parent-hash integrity"
          icon={<IconShield size={18} />}
          accent="teal"
        />

        <MetricCard
          label="Session Reveal Audits"
          value={auditEvents.length}
          suffix="Events"
          delta="Access Logged"
          deltaType={auditEvents.length > 0 ? 'alert' : 'neutral'}
          deltaLabel="Sensitive Field Decryptions"
          icon={<IconActivity size={18} />}
          accent="gold"
        />
      </div>

      {/* Session Access Events (Masking Reveals) */}
      {auditEvents.length > 0 && (
        <Card
          accent="gold"
          eyebrow="Active Session Surveillance"
          title="Sensitive Data Reveal Audit Trail"
          description="Monitors and logs every user action that reveals masked borrower identifiers or tax numbers in real-time."
        >
          <div className="space-y-2">
            {auditEvents.map((evt) => (
              <div
                key={evt.id}
                className="p-3 bg-slate-950/80 rounded-cs border border-slate-800 text-xs font-mono flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
              >
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="text-amber-400 font-semibold">{evt.action}</span>
                  <span className="text-slate-400">• Field: <strong className="text-slate-200">{evt.field}</strong></span>
                  <span className="text-slate-500">Target: {evt.targetId}</span>
                </div>
                <div className="text-[11px] text-slate-500">
                  By {evt.actor} at {new Date(evt.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Cryptographic Ledger Feed */}
      <Card
        accent="teal"
        eyebrow="Blockchain-Style Storage"
        title="Chronological Audit Blocks"
        description="Parent hash links guarantee that no historical intervention or trigger activation can be modified without breaking forward hashes."
      >
        {isLoadingEntries ? (
          <div className="py-12 text-center text-xs font-mono text-slate-400">
            <span className="inline-block w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full animate-spin mr-2" />
            Traversing ledger blocks...
          </div>
        ) : entries.length === 0 ? (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            No audit records registered.
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry, idx) => (
              <div
                key={entry.audit_id}
                className="p-4 bg-slate-950/80 rounded-cs border border-slate-800 font-mono text-xs space-y-2.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-cs-xs bg-slate-900 border border-slate-700 text-teal-400 font-bold">
                      #{entries.length - idx} {entry.audit_id}
                    </span>
                    <span className="text-slate-200 font-semibold">{entry.event_type}</span>
                  </div>
                  <span className="text-slate-500 text-[11px]">
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-400">
                  <div>Actor: <span className="text-slate-200">{entry.actor}</span></div>
                  <div>Correlation ID: <span className="text-slate-200">{entry.correlation_id}</span></div>
                </div>

                {/* Hashes */}
                <div className="p-2 bg-slate-900/90 rounded-cs-xs border border-slate-800/80 space-y-1 text-[11px]">
                  <div className="flex justify-between items-center gap-2">
                    <span className="text-slate-500">CURRENT HASH:</span>
                    <span className="text-emerald-400 font-bold truncate max-w-md">
                      {entry.current_hash}
                    </span>
                  </div>
                  <div className="flex justify-between items-center gap-2">
                    <span className="text-slate-500">PARENT HASH:</span>
                    <span className="text-slate-400 truncate max-w-md">
                      {entry.parent_hash}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
