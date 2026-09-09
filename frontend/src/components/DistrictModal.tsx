import React, { useEffect, useState } from 'react';
import { DistrictHeatmapNode, BorrowerRiskSummary } from '../types/index.js';
import { apiClient } from '../services/apiClient.js';
import { MaskedField } from './MaskedField.js';
import {
  Button,
  Card,
  RiskTierBadge,
  HazardBadge,
} from '../design-system/index.js';
import {
  IconActivity,
  IconPulse,
} from '../design-system/icons/index.js';

export interface DistrictModalProps {
  district: DistrictHeatmapNode | null;
  onClose: () => void;
  onSimulateInDistrict: (districtName: string) => void;
}

export const DistrictModal: React.FC<DistrictModalProps> = ({
  district,
  onClose,
  onSimulateInDistrict,
}) => {
  const [borrowers, setBorrowers] = useState<BorrowerRiskSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!district) return;
    const fetchBorrowers = async () => {
      setIsLoading(true);
      try {
        const res = await apiClient.listBorrowers({ district: district.district, page_size: 10 });
        setBorrowers(res.items);
      } catch (e) {
        console.error('Failed to fetch district borrowers:', e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchBorrowers();
  }, [district]);

  if (!district) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-cs shadow-2xl p-6 space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono uppercase tracking-wider text-teal-400 font-semibold">
                {district.state} • District Operational Cluster
              </span>
              <RiskTierBadge tier={district.risk_tier} size="xs" score={district.average_risk_score} />
              <HazardBadge hazard={district.primary_hazard} size="xs" />
            </div>
            <h2 className="text-2xl font-serif font-bold text-slate-100">
              {district.district} District Telemetry
            </h2>
            <p className="text-xs font-mono text-slate-400 mt-1">
              Centroid Coordinates: {district.latitude.toFixed(4)}° N, {district.longitude.toFixed(4)}° E
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-800 focus:outline-none"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Quick KPI Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Active MSME Debt
            </span>
            <span className="text-xl font-mono font-bold text-slate-100 tabular-nums">
              ₹{(district.total_exposure / 100000).toFixed(2)} Lakhs
            </span>
          </div>

          <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Monitored Borrowers
            </span>
            <span className="text-xl font-mono font-bold text-slate-100 tabular-nums">
              {district.borrower_count} Accounts
            </span>
          </div>

          <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Average Vulnerability
            </span>
            <span className="text-xl font-mono font-bold text-amber-400 tabular-nums">
              {district.average_risk_score.toFixed(1)} / 100
            </span>
          </div>
        </div>

        {/* Active Borrowers in this District */}
        <Card
          eyebrow="MSME Account Roster"
          title={`Active Lending Portfolio in ${district.district}`}
          description="Click the eye icon to reveal masked sensitive borrower names (logged to tamper-evident audit ledger)."
        >
          {isLoading ? (
            <div className="py-8 text-center text-xs font-mono text-slate-400">
              <span className="inline-block w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mr-2" />
              Loading district loan accounts...
            </div>
          ) : borrowers.length === 0 ? (
            <div className="py-6 text-center text-xs font-mono text-slate-500">
              No active borrowers found matching filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
                    <th className="py-2 px-2">Borrower ID</th>
                    <th className="py-2 px-2">Enterprise Name</th>
                    <th className="py-2 px-2">Sector</th>
                    <th className="py-2 px-2 text-right">Exposure (₹)</th>
                    <th className="py-2 px-2">Risk Score</th>
                    <th className="py-2 px-2">Trigger Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {borrowers.map((b) => (
                    <tr key={b.borrower_id} className="hover:bg-slate-800/30">
                      <td className="py-2 px-2 text-slate-300 font-semibold">{b.borrower_id}</td>
                      <td className="py-2 px-2 font-sans">
                        <MaskedField
                          value={b.anonymized_alias}
                          fieldName="ENTERPRISE_NAME"
                          targetId={b.borrower_id}
                        />
                      </td>
                      <td className="py-2 px-2 text-slate-400">{b.sector}</td>
                      <td className="py-2 px-2 text-right text-slate-200 tabular-nums">
                        ₹{(b.total_active_exposure / 100000).toFixed(2)} L
                      </td>
                      <td className="py-2 px-2">
                        <RiskTierBadge tier={b.risk_tier} score={b.risk_score} size="xs" />
                      </td>
                      <td className="py-2 px-2">
                        {b.trigger_fired ? (
                          <span className="text-amber-400 font-semibold flex items-center gap-1">
                            <IconPulse size={12} className="animate-ping" />
                            <span>TRIGGERED</span>
                          </span>
                        ) : (
                          <span className="text-slate-500">NOMINAL</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close Inspection
          </Button>

          <Button
            variant="primary"
            size="sm"
            iconLeft={<IconActivity size={15} />}
            onClick={() => {
              onClose();
              onSimulateInDistrict(district.district);
            }}
          >
            Simulate Climate Shock in {district.district}
          </Button>
        </div>
      </div>
    </div>
  );
};
