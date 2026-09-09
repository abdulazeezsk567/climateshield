import React, { useEffect, useState, useMemo } from 'react';
import {
  PortfolioSummary,
  DistrictHeatmapNode,
  BorrowerRiskSummary,
} from '../types/index.js';
import { apiClient } from '../services/apiClient.js';
import { MaskedField } from '../components/MaskedField.js';
import { DistrictModal } from '../components/DistrictModal.js';
import {
  Button,
  Card,
  MetricCard,
  RiskTierBadge,
  HazardBadge,
} from '../design-system/index.js';
import {
  IconRupee,
  IconSatellite,
  IconFilter,
  IconRefresh,
  IconPulse,
} from '../design-system/icons/index.js';

interface PortfolioDashboardProps {
  onNavigateToSimulator: (districtName?: string) => void;
}

export const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({
  onNavigateToSimulator,
}) => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [heatmapNodes, setHeatmapNodes] = useState<DistrictHeatmapNode[]>([]);
  const [borrowers, setBorrowers] = useState<BorrowerRiskSummary[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictHeatmapNode | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [tierFilter, setTierFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, heatRes, borrRes] = await Promise.all([
        apiClient.getPortfolioSummary(),
        apiClient.getPortfolioHeatmap(),
        apiClient.listBorrowers({ page_size: 50 }),
      ]);
      setSummary(sumRes);
      setHeatmapNodes(heatRes);
      setBorrowers(borrRes.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio telemetry data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Filtered Borrowers
  const filteredBorrowers = useMemo(() => {
    return borrowers.filter((b) => {
      if (sectorFilter !== 'ALL' && b.sector !== sectorFilter) return false;
      if (tierFilter !== 'ALL' && b.risk_tier !== tierFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = b.anonymized_alias.toLowerCase().includes(q);
        const matchesDist = b.district.toLowerCase().includes(q);
        const matchesId = b.borrower_id.toLowerCase().includes(q);
        if (!matchesName && !matchesDist && !matchesId) return false;
      }
      return true;
    });
  }, [borrowers, sectorFilter, tierFilter, searchQuery]);

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-teal-950/70 border border-teal-800/80 text-teal-400">
              <IconSatellite size={16} />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-teal-400">
              Spatial Telemetry Layer
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100">
            MSME Portfolio Climate Risk
          </h1>
          <p className="text-xs sm:text-sm font-sans text-slate-400 mt-1">
            Continuous weather & NDVI monitoring across Satin Finserv target lending districts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadDashboardData}
            isLoading={isLoading}
            iconLeft={<IconRefresh size={14} />}
          >
            Sync Feeds
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onNavigateToSimulator()}
            iconLeft={<IconPulse size={14} />}
          >
            Simulate Climate Shock
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-cs text-rose-200 text-xs flex items-center justify-between">
          <span>{error}</span>
          <Button size="sm" variant="danger" onClick={loadDashboardData}>
            Retry
          </Button>
        </div>
      )}

      {/* 4 High-Density KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Monitored Exposure"
          value={summary ? (summary.total_credit_exposure / 10000000).toFixed(2) : '—'}
          prefix="₹"
          suffix="Cr"
          delta={summary ? `${summary.total_active_borrowers} MSMEs` : undefined}
          deltaType="positive"
          deltaLabel="Active Portfolio"
          icon={<IconRupee size={18} />}
          accent="gold"
        />

        <MetricCard
          label="High-Risk Exposure"
          value={summary ? summary.high_risk_exposure_percentage.toFixed(1) : '—'}
          suffix="%"
          delta="Tier 3 & 4"
          deltaType="alert"
          deltaLabel="Severe & High Vulnerability"
          badge={<RiskTierBadge tier="HIGH" size="xs" />}
          accent="rose"
        />

        <MetricCard
          label="Operational Districts"
          value={summary ? summary.districts_monitored : '—'}
          suffix="Districts"
          delta="NASA POWER + NDVI"
          deltaType="neutral"
          deltaLabel="Precipitation & Soil Feeds"
          icon={<IconSatellite size={18} />}
          accent="teal"
        />

        <MetricCard
          label="Active Parametric Triggers"
          value={borrowers.filter((b) => b.trigger_fired).length}
          suffix="MSMEs"
          delta="4-Stage LMS Ready"
          deltaType="alert"
          deltaLabel="Moratorium / Top-up Eligible"
          badge={<RiskTierBadge tier="SEVERE" size="xs" />}
          accent="emerald"
        />
      </div>

      {/* District Climate Risk Geospatial Heatmap Grid */}
      <Card
        accent="teal"
        eyebrow="District Vulnerability Clusters"
        title="Geospatial Risk Heatmap Grid"
        description="District clusters mapped with NASA POWER weather anomalies, Sentinel-2 NDVI deficits, and total loan exposure."
        headerAction={
          <span className="text-[11px] font-mono text-slate-400">
            {heatmapNodes.length} Operational Clusters Monitored
          </span>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {heatmapNodes.map((node) => (
            <div
              key={node.district}
              onClick={() => setSelectedDistrict(node)}
              className="group p-4 bg-slate-950/70 hover:bg-slate-800/60 border border-slate-800 hover:border-teal-500/60 rounded-cs transition-all duration-150 cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h4 className="font-serif text-base font-bold text-slate-100 group-hover:text-teal-300 transition-colors">
                      {node.district}
                    </h4>
                    <span className="text-[11px] font-mono text-slate-400">
                      {node.state}
                    </span>
                  </div>
                  <RiskTierBadge tier={node.risk_tier} score={node.average_risk_score} size="xs" />
                </div>

                <div className="space-y-1.5 font-mono text-xs my-3 pt-2 border-t border-slate-800/70">
                  <div className="flex justify-between text-slate-400">
                    <span>Active Exposure:</span>
                    <span className="text-slate-100 font-semibold tabular-nums">
                      ₹{(node.total_exposure / 100000).toFixed(1)} L
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Borrower Base:</span>
                    <span className="text-slate-300 tabular-nums">{node.borrower_count} accounts</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>GPS Centroid:</span>
                    <span className="text-slate-400 text-[10px] tabular-nums">
                      {node.latitude.toFixed(2)}°N, {node.longitude.toFixed(2)}°E
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/70">
                <HazardBadge hazard={node.primary_hazard} size="xs" />
                <span className="text-[10px] font-mono text-teal-400 group-hover:underline">
                  Inspect Drill-Down →
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Filter Bar & Borrower Risk Table */}
      <Card
        eyebrow="Portfolio Risk Ledger"
        title="Borrower Climate-Risk Vulnerability Scorecards"
        description="Filterable ledger displaying computed logistic vulnerability scores, basis risk flags, and sensitive field masking with audit logging."
        headerAction={
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">
              {filteredBorrowers.length} of {borrowers.length} Accounts
            </span>
          </div>
        }
      >
        {/* Filter Controls */}
        <div className="p-3 bg-slate-950/80 rounded-cs border border-slate-800 mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <IconFilter size={14} />
            <span>Filters:</span>
          </div>

          {/* Sector Filter */}
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-cs px-2.5 py-1.5 font-mono focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All Industry Sectors</option>
            <option value="Agri-Processing">Agri-Processing</option>
            <option value="Textiles">Textiles</option>
            <option value="Cold Chain">Cold Chain</option>
            <option value="Food Milling">Food Milling</option>
            <option value="Metal Fabrication">Metal Fabrication</option>
            <option value="Dairy & Livestock">Dairy & Livestock</option>
            <option value="Retail Trade">Retail Trade</option>
          </select>

          {/* Tier Filter */}
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-cs px-2.5 py-1.5 font-mono focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All Risk Tiers</option>
            <option value="LOW">Tier 1 • Low</option>
            <option value="MODERATE">Tier 2 • Moderate</option>
            <option value="HIGH">Tier 3 • High</option>
            <option value="SEVERE">Tier 4 • Severe</option>
          </select>

          {/* Search Input */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, enterprise name, or district..."
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-cs px-3 py-1.5 font-mono placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>

          {(sectorFilter !== 'ALL' || tierFilter !== 'ALL' || searchQuery) && (
            <button
              type="button"
              onClick={() => {
                setSectorFilter('ALL');
                setTierFilter('ALL');
                setSearchQuery('');
              }}
              className="text-xs font-mono text-slate-400 hover:text-amber-400 underline transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>

        {/* Dense Table */}
        {filteredBorrowers.length === 0 ? (
          <div className="py-12 text-center text-xs font-mono text-slate-400">
            No borrowers found matching active filters.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-cs border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Borrower ID</th>
                  <th className="py-2.5 px-3">MSME Enterprise</th>
                  <th className="py-2.5 px-3">District</th>
                  <th className="py-2.5 px-3">Sector</th>
                  <th className="py-2.5 px-3 text-right">Active Debt (₹)</th>
                  <th className="py-2.5 px-3">ML Risk Tier</th>
                  <th className="py-2.5 px-3">Anomaly Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredBorrowers.map((b) => (
                  <tr key={b.borrower_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 text-slate-200 font-semibold">{b.borrower_id}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <MaskedField
                        value={b.anonymized_alias}
                        fieldName="BORROWER_ENTERPRISE"
                        targetId={b.borrower_id}
                      />
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{b.district}</td>
                    <td className="py-2.5 px-3 text-slate-400">{b.sector}</td>
                    <td className="py-2.5 px-3 text-right text-slate-100 tabular-nums">
                      ₹{(b.total_active_exposure / 100000).toFixed(2)} L
                    </td>
                    <td className="py-2.5 px-3">
                      <RiskTierBadge tier={b.risk_tier} score={b.risk_score} size="xs" />
                    </td>
                    <td className="py-2.5 px-3">
                      {b.trigger_fired ? (
                        <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
                          <span>{b.trigger_reason || 'TRIGGER ACTIVE'}</span>
                        </span>
                      ) : (
                        <span className="text-slate-500">Nominal</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* District Drill-Down Modal */}
      <DistrictModal
        district={selectedDistrict}
        onClose={() => setSelectedDistrict(null)}
        onSimulateInDistrict={(distName) => onNavigateToSimulator(distName)}
      />
    </div>
  );
};
