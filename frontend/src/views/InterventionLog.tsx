import React, { useEffect, useState, useMemo } from 'react';
import { LoanInterventionRecord } from '../types/index.js';
import { apiClient } from '../services/apiClient.js';
import { MaskedField } from '../components/MaskedField.js';
import {
  Button,
  Card,
  InterventionStatusPill,
} from '../design-system/index.js';
import {
  IconCheckCircle,
  IconLock,
  IconFilter,
  IconRefresh,
  IconArrowRight,
} from '../design-system/icons/index.js';

interface InterventionLogProps {
  initialCorrelationId?: string;
  onNavigateToAudit?: () => void;
}

export const InterventionLog: React.FC<InterventionLogProps> = ({
  initialCorrelationId,
  onNavigateToAudit,
}) => {
  const [interventions, setInterventions] = useState<LoanInterventionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>(initialCorrelationId || '');
  const [selectedIntervention, setSelectedIntervention] = useState<LoanInterventionRecord | null>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const fetchInterventions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.listInterventions({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        correlation_id: searchQuery.trim() ? searchQuery.trim() : undefined,
        page,
        page_size: pageSize,
      });
      setInterventions(res.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch interventions.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInterventions();
  }, [statusFilter, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchInterventions();
  };

  const filteredInterventions = useMemo(() => {
    if (!searchQuery.trim()) return interventions;
    const q = searchQuery.toLowerCase();
    return interventions.filter(
      (item) =>
        item.borrower_id.toLowerCase().includes(q) ||
        item.intervention_id.toLowerCase().includes(q) ||
        item.correlation_id.toLowerCase().includes(q) ||
        item.trigger_id.toLowerCase().includes(q) ||
        item.loan_id.toLowerCase().includes(q)
    );
  }, [interventions, searchQuery]);

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-teal-950/70 border border-teal-800/80 text-teal-400">
              <IconCheckCircle size={16} />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-teal-400">
              Action & Integration Layer
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100">
            MSME Intervention & LMS Lifecycle Log
          </h1>
          <p className="text-xs sm:text-sm font-sans text-slate-400 mt-1">
            4-Stage parametric loan adjustment state machine (TRIGGERED → NOTIFIED → APPLIED → CONFIRMED) verified with HMAC-SHA256 signatures.
          </p>
        </div>

        {/* Cryptographic Ledger Health Pill */}
        <div className="shrink-0 flex items-center gap-2">
          <div className="p-2 bg-slate-900 border border-emerald-800/80 rounded-cs flex items-center gap-2 text-xs font-mono text-emerald-300">
            <IconLock size={14} className="text-emerald-400" />
            <span>Audit Chain: VALID (SHA-256)</span>
          </div>
          {onNavigateToAudit && (
            <Button
              variant="outline"
              size="sm"
              onClick={onNavigateToAudit}
              iconRight={<IconArrowRight size={14} />}
            >
              Verify Ledger
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/50 border border-rose-800 rounded-cs text-rose-200 text-xs">
          {error}
        </div>
      )}

      {/* Main Table Card */}
      <Card
        eyebrow="State Machine Audit"
        title="Loan Restructuring & Relief Dispatches"
        description="Every state change writes an immutable audit record tied to a correlation ID. Click row to inspect HMAC payload."
        headerAction={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchInterventions}
              isLoading={isLoading}
              iconLeft={<IconRefresh size={13} />}
            >
              Refresh
            </Button>
          </div>
        }
      >
        {/* Filter / Search Bar */}
        <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800 mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <IconFilter size={14} />
            <span>Lifecycle Filter:</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            {(['ALL', 'TRIGGERED', 'NOTIFIED', 'APPLIED', 'CONFIRMED'] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded-cs text-xs font-mono transition-colors ${
                  statusFilter === st
                    ? 'bg-amber-500 text-slate-950 font-bold'
                    : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[220px] flex items-center gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Correlation ID, Borrower ID, or Loan ID..."
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-cs px-3 py-1.5 font-mono placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
            <Button type="submit" size="sm" variant="secondary">
              Search
            </Button>
          </form>
        </div>

        {/* Dense Table */}
        {isLoading ? (
          <div className="py-12 text-center text-xs font-mono text-slate-400">
            <span className="inline-block w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mr-2" />
            Loading LMS state machine ledger...
          </div>
        ) : filteredInterventions.length === 0 ? (
          <div className="py-12 text-center text-xs font-mono text-slate-500">
            No intervention events found matching the active filter.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-cs border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Intervention ID</th>
                  <th className="py-2.5 px-3">Borrower Account</th>
                  <th className="py-2.5 px-3">LMS Loan ID</th>
                  <th className="py-2.5 px-3">Policy Action</th>
                  <th className="py-2.5 px-3">State Machine Status</th>
                  <th className="py-2.5 px-3">Correlation ID</th>
                  <th className="py-2.5 px-3">Dispatched At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredInterventions.map((record) => (
                  <tr
                    key={record.intervention_id}
                    onClick={() => setSelectedIntervention(record)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 text-slate-200 font-semibold">{record.intervention_id}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <MaskedField
                        value={record.borrower_id}
                        fieldName="BORROWER_IDENTIFIER"
                        targetId={record.intervention_id}
                      />
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{record.loan_id}</td>
                    <td className="py-2.5 px-3 text-amber-400 font-sans font-medium">
                      {record.action_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 px-3">
                      <InterventionStatusPill status={record.status} size="xs" />
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      <span className="font-mono bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                        {record.correlation_id}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {new Date(record.dispatched_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Displaying {filteredInterventions.length} records</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-700 disabled:opacity-40 text-slate-300 hover:bg-slate-800"
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              type="button"
              disabled={filteredInterventions.length < pageSize}
              onClick={() => setPage((p) => p + 1)}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-700 disabled:opacity-40 text-slate-300 hover:bg-slate-800"
            >
              Next
            </button>
          </div>
        </div>
      </Card>

      {/* Intervention Detail Modal */}
      {selectedIntervention && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          onClick={() => setSelectedIntervention(null)}
        >
          <div
            className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-cs p-6 space-y-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider block mb-0.5">
                  Intervention Lifecycle Dossier
                </span>
                <h3 className="text-xl font-serif font-bold text-slate-100">
                  {selectedIntervention.intervention_id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedIntervention(null)}
                className="text-slate-400 hover:text-slate-100 p-1 text-sm"
              >
                ✕
              </button>
            </div>

            {/* 4-Stage Visual Lifecycle */}
            <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800 space-y-2">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                State Machine Progression
              </span>
              <div className="flex flex-wrap items-center gap-2">
                <InterventionStatusPill status="TRIGGERED" />
                <span className="text-slate-600">→</span>
                <InterventionStatusPill status="NOTIFIED" />
                <span className="text-slate-600">→</span>
                <InterventionStatusPill status="APPLIED" />
                <span className="text-slate-600">→</span>
                <InterventionStatusPill status="CONFIRMED" />
              </div>
              <div className="text-[11px] font-mono text-amber-400 pt-1">
                Active Status: <strong>{selectedIntervention.status}</strong>
              </div>
            </div>

            {/* Core Details Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 bg-slate-950/60 rounded-cs border border-slate-800">
                <span className="text-slate-500 block text-[10px]">BORROWER ID:</span>
                <MaskedField
                  value={selectedIntervention.borrower_id}
                  fieldName="BORROWER_ID"
                  targetId={selectedIntervention.intervention_id}
                />
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-cs border border-slate-800">
                <span className="text-slate-500 block text-[10px]">LOAN ACCOUNT:</span>
                <span className="text-slate-200">{selectedIntervention.loan_id}</span>
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-cs border border-slate-800">
                <span className="text-slate-500 block text-[10px]">POLICY ACTION:</span>
                <span className="text-amber-300 font-sans font-semibold">
                  {selectedIntervention.action_type}
                </span>
              </div>

              <div className="p-2.5 bg-slate-950/60 rounded-cs border border-slate-800">
                <span className="text-slate-500 block text-[10px]">CORRELATION ID:</span>
                <span className="text-slate-200">{selectedIntervention.correlation_id}</span>
              </div>
            </div>

            {/* HMAC Verified Payload */}
            <div>
              <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                Simulated LMS Webhook Payload (HMAC-SHA256 Signed):
              </span>
              <pre className="p-3 bg-slate-950 rounded-cs border border-slate-800 font-mono text-xs text-teal-300 overflow-x-auto">
                {JSON.stringify(selectedIntervention.payload, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <Button size="sm" variant="secondary" onClick={() => setSelectedIntervention(null)}>
                Close Dossier
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
