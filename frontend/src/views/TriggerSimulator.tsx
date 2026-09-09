import React, { useState, useMemo } from 'react';
import { useAuth } from '../services/authContext.js';
import { apiClient } from '../services/apiClient.js';
import {
  ClimateHazardType,
  SimulationRequest,
  SimulationResultResponse,
} from '../types/index.js';
import {
  Button,
  Card,
  MetricCard,
  AlertBanner,
} from '../design-system/index.js';
import {
  IconActivity,
  IconRainfall,
  IconDrought,
  IconPulse,
  IconCheckCircle,
  IconAlertTriangle,
  IconArrowRight,
  IconLock,
} from '../design-system/icons/index.js';

interface TriggerSimulatorProps {
  initialDistrict?: string;
  onNavigateToInterventions: (correlationId?: string) => void;
}

const DISTRICT_BASELINES: Record<
  string,
  {
    rainfallNormalMm: number;
    rainfallP95ThresholdMm: number;
    droughtDryDaysNormal: number;
    droughtThresholdDays: number;
    temperatureNormalC: number;
    temperatureP95ThresholdC: number;
  }
> = {
  Varanasi: {
    rainfallNormalMm: 120.0,
    rainfallP95ThresholdMm: 180.0,
    droughtDryDaysNormal: 6,
    droughtThresholdDays: 21,
    temperatureNormalC: 31.0,
    temperatureP95ThresholdC: 42.0,
  },
  Barabanki: {
    rainfallNormalMm: 110.0,
    rainfallP95ThresholdMm: 165.0,
    droughtDryDaysNormal: 8,
    droughtThresholdDays: 20,
    temperatureNormalC: 30.5,
    temperatureP95ThresholdC: 41.5,
  },
  Patna: {
    rainfallNormalMm: 135.0,
    rainfallP95ThresholdMm: 195.0,
    droughtDryDaysNormal: 5,
    droughtThresholdDays: 22,
    temperatureNormalC: 31.5,
    temperatureP95ThresholdC: 42.5,
  },
  Bhojpur: {
    rainfallNormalMm: 115.0,
    rainfallP95ThresholdMm: 170.0,
    droughtDryDaysNormal: 7,
    droughtThresholdDays: 21,
    temperatureNormalC: 31.0,
    temperatureP95ThresholdC: 42.0,
  },
  Mirzapur: {
    rainfallNormalMm: 105.0,
    rainfallP95ThresholdMm: 160.0,
    droughtDryDaysNormal: 9,
    droughtThresholdDays: 19,
    temperatureNormalC: 32.0,
    temperatureP95ThresholdC: 43.5,
  },
  Muzaffarpur: {
    rainfallNormalMm: 140.0,
    rainfallP95ThresholdMm: 205.0,
    droughtDryDaysNormal: 5,
    droughtThresholdDays: 23,
    temperatureNormalC: 30.0,
    temperatureP95ThresholdC: 41.0,
  },
  Gorakhpur: {
    rainfallNormalMm: 145.0,
    rainfallP95ThresholdMm: 210.0,
    droughtDryDaysNormal: 6,
    droughtThresholdDays: 22,
    temperatureNormalC: 30.5,
    temperatureP95ThresholdC: 41.5,
  },
};

export const TriggerSimulator: React.FC<TriggerSimulatorProps> = ({
  initialDistrict = 'Varanasi',
  onNavigateToInterventions,
}) => {
  const { role, switchDemoRole } = useAuth();

  const [selectedDistrict, setSelectedDistrict] = useState<string>(initialDistrict);
  const [selectedHazard, setSelectedHazard] = useState<ClimateHazardType>('FLOOD');
  const [intensityMultiplier, setIntensityMultiplier] = useState<number>(1.75);

  // Manual overrides
  const [useCustomOverride, setUseCustomOverride] = useState<boolean>(false);
  const [overrideValue, setOverrideValue] = useState<number>(214);

  const [isExecuting, setIsExecuting] = useState(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResultResponse | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Current baseline definition for selected district
  const currentBaseline = useMemo(() => {
    return (
      DISTRICT_BASELINES[selectedDistrict] || DISTRICT_BASELINES['Varanasi']
    );
  }, [selectedDistrict]);

  // Derived simulation metrics
  const { baselineValue, simulatedValue, thresholdValue, unit, isTriggerFired, deviationPct } =
    useMemo(() => {
      if (selectedHazard === 'FLOOD') {
        const base = currentBaseline.rainfallNormalMm;
        const thresh = currentBaseline.rainfallP95ThresholdMm;
        const sim = useCustomOverride ? overrideValue : Math.round(base * intensityMultiplier);
        const fired = sim >= thresh;
        const dev = ((sim - base) / base) * 100;
        return {
          baselineValue: base,
          simulatedValue: sim,
          thresholdValue: thresh,
          unit: 'mm',
          isTriggerFired: fired,
          deviationPct: dev,
        };
      } else if (selectedHazard === 'DROUGHT') {
        const base = currentBaseline.droughtDryDaysNormal;
        const thresh = currentBaseline.droughtThresholdDays;
        const sim = useCustomOverride ? overrideValue : Math.round(base * intensityMultiplier * 2.5);
        const fired = sim >= thresh;
        const dev = ((sim - base) / base) * 100;
        return {
          baselineValue: base,
          simulatedValue: sim,
          thresholdValue: thresh,
          unit: 'dry days',
          isTriggerFired: fired,
          deviationPct: dev,
        };
      } else {
        // HEATWAVE
        const base = currentBaseline.temperatureNormalC;
        const thresh = currentBaseline.temperatureP95ThresholdC;
        const sim = useCustomOverride ? overrideValue : Number((base + (intensityMultiplier - 1) * 8).toFixed(1));
        const fired = sim >= thresh;
        const dev = ((sim - base) / base) * 100;
        return {
          baselineValue: base,
          simulatedValue: sim,
          thresholdValue: thresh,
          unit: '°C',
          isTriggerFired: fired,
          deviationPct: dev,
        };
      }
    }, [selectedHazard, currentBaseline, intensityMultiplier, useCustomOverride, overrideValue]);

  const handleExecuteSimulation = async () => {
    if (role !== 'credit_team') {
      setErrorBanner('Permission Denied: Viewer role cannot dispatch live LMS simulations. Switch to Credit Team.');
      return;
    }

    setIsExecuting(true);
    setErrorBanner(null);

    const payload: SimulationRequest = {
      district: selectedDistrict,
      hazard_type: selectedHazard,
      intensity_multiplier: intensityMultiplier,
    };

    if (useCustomOverride) {
      if (selectedHazard === 'FLOOD') payload.custom_rainfall_mm = overrideValue;
      if (selectedHazard === 'DROUGHT') payload.custom_temperature_celsius = overrideValue;
    }

    try {
      const res = await apiClient.simulateTrigger(payload);
      setSimulationResult(res);
    } catch (err: unknown) {
      setErrorBanner(err instanceof Error ? err.message : 'Simulation execution failed.');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* View Header */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded bg-amber-950/70 border border-amber-800/80 text-amber-400">
              <IconPulse size={16} />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Parametric Trigger Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-slate-100">
            Interactive Climate Anomaly Simulator
          </h1>
          <p className="text-xs sm:text-sm font-sans text-slate-400 mt-1">
            Live demonstration harness: evaluate weather deviations against 10-year NASA POWER baselines and observe automated LMS state machine dispatch.
          </p>
        </div>

        {/* Role Enforcement Pill */}
        <div className="shrink-0">
          {role === 'credit_team' ? (
            <div className="p-2.5 bg-slate-900 border border-amber-800/60 rounded-cs flex items-center gap-2 text-xs font-mono text-amber-300">
              <IconLock size={14} className="text-amber-400" />
              <span>Full Simulation Authority (credit_team)</span>
            </div>
          ) : (
            <div className="p-2.5 bg-slate-900 border border-teal-800/60 rounded-cs flex items-center justify-between gap-3 text-xs font-mono text-teal-300">
              <div className="flex items-center gap-1.5">
                <IconLock size={14} className="text-teal-400" />
                <span>Viewer Demo Mode (Read-Only)</span>
              </div>
              <button
                type="button"
                onClick={() => switchDemoRole('credit_team')}
                className="text-[11px] font-bold text-amber-400 hover:underline"
              >
                Switch to Credit Team →
              </button>
            </div>
          )}
        </div>
      </div>

      {errorBanner && (
        <AlertBanner
          variant="warning"
          title="Action Requirement"
          message={errorBanner}
          onClose={() => setErrorBanner(null)}
        />
      )}

      {/* Grid: Simulator Configuration vs Visual Deviation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Configuration Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <Card
            accent="gold"
            eyebrow="Shock Configuration"
            title="Simulation Parameters"
            description="Select an operational district and inject synthetic climate stress."
          >
            <div className="space-y-4">
              {/* Target District */}
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1">
                  Operational District
                </label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => {
                    setSelectedDistrict(e.target.value);
                    setSimulationResult(null);
                  }}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-cs px-3 py-2 font-mono focus:outline-none focus:border-amber-500"
                >
                  {Object.keys(DISTRICT_BASELINES).map((dist) => (
                    <option key={dist} value={dist}>
                      {dist} District (UP/Bihar)
                    </option>
                  ))}
                </select>
              </div>

              {/* Hazard Type */}
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1">
                  Climate Hazard Scenario
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedHazard('FLOOD');
                      setOverrideValue(214);
                      setSimulationResult(null);
                    }}
                    className={`p-2.5 rounded-cs border text-xs font-mono flex flex-col items-center gap-1.5 transition-colors ${
                      selectedHazard === 'FLOOD'
                        ? 'bg-sky-950/80 border-sky-600 text-sky-200 font-semibold'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <IconRainfall size={20} />
                    <span>Flood / Rain</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setSelectedHazard('DROUGHT');
                      setOverrideValue(28);
                      setSimulationResult(null);
                    }}
                    className={`p-2.5 rounded-cs border text-xs font-mono flex flex-col items-center gap-1.5 transition-colors ${
                      selectedHazard === 'DROUGHT'
                        ? 'bg-amber-950/80 border-amber-600 text-amber-200 font-semibold'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <IconDrought size={20} />
                    <span>Drought</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setSelectedHazard('HEATWAVE');
                      setOverrideValue(44.5);
                      setSimulationResult(null);
                    }}
                    className={`p-2.5 rounded-cs border text-xs font-mono flex flex-col items-center gap-1.5 transition-colors ${
                      selectedHazard === 'HEATWAVE'
                        ? 'bg-rose-950/80 border-rose-600 text-rose-200 font-semibold'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <IconAlertTriangle size={20} />
                    <span>Heatwave</span>
                  </button>
                </div>
              </div>

              {/* Intensity Multiplier Slider */}
              <div>
                <div className="flex justify-between items-center text-xs font-mono mb-1">
                  <span className="text-slate-400 uppercase tracking-wider">Shock Intensity:</span>
                  <span className="text-amber-400 font-bold tabular-nums">
                    {intensityMultiplier.toFixed(2)}x Baseline
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.05"
                  value={intensityMultiplier}
                  disabled={useCustomOverride}
                  onChange={(e) => {
                    setIntensityMultiplier(parseFloat(e.target.value));
                    setSimulationResult(null);
                  }}
                  className="w-full accent-amber-500 cursor-pointer disabled:opacity-40"
                />
                <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-0.5">
                  <span>0.5x (Sub-normal)</span>
                  <span>1.0x (Normal)</span>
                  <span>2.0x (Severe)</span>
                  <span>3.0x (Catastrophic)</span>
                </div>
              </div>

              {/* Absolute Override Toggle */}
              <div className="pt-2 border-t border-slate-800/80">
                <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-slate-300">
                  <input
                    type="checkbox"
                    checked={useCustomOverride}
                    onChange={(e) => {
                      setUseCustomOverride(e.target.checked);
                      setSimulationResult(null);
                    }}
                    className="rounded text-amber-500 focus:ring-amber-500 bg-slate-900 border-slate-700"
                  />
                  <span>Specify Absolute Measurement Override</span>
                </label>

                {useCustomOverride && (
                  <div className="mt-2.5">
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        value={overrideValue}
                        onChange={(e) => {
                          setOverrideValue(parseFloat(e.target.value) || 0);
                          setSimulationResult(null);
                        }}
                        className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-cs px-3 py-1.5 font-mono focus:outline-none focus:border-amber-500"
                      />
                      <span className="text-xs font-mono text-slate-400 shrink-0">{unit}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Run Simulation Action Button */}
              <div className="pt-2">
                <Button
                  variant="primary"
                  className="w-full"
                  isLoading={isExecuting}
                  disabled={role !== 'credit_team'}
                  onClick={handleExecuteSimulation}
                  iconLeft={<IconActivity size={16} />}
                >
                  {role === 'credit_team'
                    ? 'Execute Parametric Simulation & Dispatch'
                    : 'Simulation Locked (Requires credit_team)'}
                </Button>
                {role !== 'credit_team' && (
                  <p className="text-[11px] font-mono text-slate-500 text-center mt-1.5">
                    Click "Switch Role" in the top bar to run simulations.
                  </p>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Visual Deviation Calculation Panel (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <Card
            accent={isTriggerFired ? 'rose' : 'teal'}
            eyebrow="Telemetry Assessment"
            title="Deviation Calculation vs Parametric Threshold"
            description="Visual representation of current/simulated weather anomaly against the 10-year NASA POWER baseline and policy trigger boundary."
          >
            {/* Visual Trigger Status Pill */}
            <div className="mb-6 p-4 rounded-cs bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 block">
                  Parametric Trigger Evaluation
                </span>
                <div className="text-lg font-serif font-bold mt-0.5 flex items-center gap-2">
                  {isTriggerFired ? (
                    <span className="text-rose-400 flex items-center gap-2">
                      <IconAlertTriangle size={20} className="animate-bounce" />
                      THRESHOLD BREACHED • TRIGGER ACTIVATED
                    </span>
                  ) : (
                    <span className="text-emerald-400 flex items-center gap-2">
                      <IconCheckCircle size={20} />
                      WITHIN NORMAL BOUNDS • NO TRIGGER
                    </span>
                  )}
                </div>
              </div>

              <div className="text-right font-mono">
                <div className="text-[11px] text-slate-500 uppercase tracking-wider">Historical Deviation</div>
                <div
                  className={`text-2xl font-bold tabular-nums ${
                    deviationPct > 0 ? 'text-amber-400' : 'text-sky-400'
                  }`}
                >
                  {deviationPct >= 0 ? `+${deviationPct.toFixed(1)}%` : `${deviationPct.toFixed(1)}%`}
                </div>
              </div>
            </div>

            {/* 3-Point Comparison Visualizer */}
            <div className="space-y-4 font-mono text-xs">
              {/* 1. Historical Baseline */}
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>1. 10-Year Historical Normal (NASA POWER):</span>
                  <span className="text-slate-200 font-semibold tabular-nums">
                    {baselineValue} {unit}
                  </span>
                </div>
                <div className="h-3 rounded-cs-sm bg-slate-950 border border-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-slate-600 transition-all duration-300"
                    style={{
                      width: `${Math.min(100, (baselineValue / (thresholdValue * 1.3)) * 100)}%`,
                    }}
                  />
                </div>
              </div>

              {/* 2. Parametric Trigger Boundary */}
              <div>
                <div className="flex justify-between text-amber-400 mb-1">
                  <span>2. Extreme P95 Trigger Threshold:</span>
                  <span className="font-bold tabular-nums">
                    {thresholdValue} {unit}
                  </span>
                </div>
                <div className="h-3 rounded-cs-sm bg-slate-950 border border-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-amber-500/80 transition-all duration-300"
                    style={{
                      width: `${Math.min(100, (thresholdValue / (thresholdValue * 1.3)) * 100)}%`,
                    }}
                  />
                </div>
              </div>

              {/* 3. Selected / Simulated Value */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className={isTriggerFired ? 'text-rose-300 font-bold' : 'text-slate-300'}>
                    3. Selected / Injected Observation:
                  </span>
                  <span
                    className={`font-bold tabular-nums text-sm ${
                      isTriggerFired ? 'text-rose-400' : 'text-slate-100'
                    }`}
                  >
                    {simulatedValue} {unit}
                  </span>
                </div>
                <div className="h-4 rounded-cs-sm bg-slate-950 border border-slate-800 overflow-hidden relative">
                  <div
                    className={`h-full transition-all duration-300 ${
                      isTriggerFired ? 'bg-rose-500' : 'bg-teal-500'
                    }`}
                    style={{
                      width: `${Math.min(100, (simulatedValue / (thresholdValue * 1.3)) * 100)}%`,
                    }}
                  />
                  {/* Threshold vertical marker line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-amber-300 z-10"
                    style={{
                      left: `${Math.min(100, (thresholdValue / (thresholdValue * 1.3)) * 100)}%`,
                    }}
                    title={`Threshold: ${thresholdValue} ${unit}`}
                  />
                </div>
              </div>
            </div>

            {/* Explanatory Note */}
            <div className="mt-6 p-3 bg-slate-950/60 rounded-cs border border-slate-800/80 text-[11px] font-sans text-slate-400">
              <span className="font-semibold text-slate-300">Parametric Underwriting Rule: </span>
              When observed weather exceeds the 95th percentile historical deviation, an automated loan restructuring payload is constructed and dispatched to the simulated LMS webhook with HMAC-SHA256 signature verification.
            </div>
          </Card>
        </div>
      </div>

      {/* Simulation Execution Output & LMS Dispatch Result */}
      {simulationResult && (
        <Card
          accent="emerald"
          eyebrow="Automated State Machine Execution"
          title="Parametric Relief Action Dispatched"
          description={`LMS loan restructuring proposals generated for ${simulationResult.triggers_activated} borrower accounts in ${simulationResult.district}.`}
          headerAction={
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigateToInterventions(simulationResult.sample_trigger_event?.trigger_id)}
              iconRight={<IconArrowRight size={14} />}
            >
              Open Intervention Log
            </Button>
          }
        >
          <div className="space-y-6">
            {/* Quick KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <MetricCard
                label="Evaluated Borrowers"
                value={simulationResult.total_borrowers_evaluated}
                suffix="MSMEs"
                delta="District Roster"
                deltaType="neutral"
              />
              <MetricCard
                label="Triggers Activated"
                value={simulationResult.triggers_activated}
                suffix="Accounts"
                delta="P95 Breached"
                deltaType="alert"
                accent="rose"
              />
              <MetricCard
                label="LMS Actions Dispatched"
                value={simulationResult.generated_lms_actions_count}
                suffix="Payloads"
                delta="HMAC-SHA256 Signed"
                deltaType="positive"
                accent="teal"
              />
              <MetricCard
                label="Relief Capital Volume"
                value={(simulationResult.total_relief_exposure / 100000).toFixed(2)}
                prefix="₹"
                suffix="Lakhs"
                delta="Restructured"
                deltaType="positive"
                accent="gold"
              />
            </div>

            {/* Trigger Event & Affected Accounts Summary */}
            <div className="p-4 bg-slate-950/90 rounded-cs border border-slate-800 font-mono text-xs space-y-3">
              <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                  <IconPulse size={14} />
                  <span>TRIGGER EVENT: {simulationResult.sample_trigger_event?.trigger_id || 'TRIG-001'}</span>
                </span>
                <span className="text-slate-500 text-[11px]">
                  Timestamp: {new Date(simulationResult.simulation_timestamp).toLocaleString()}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-400 text-[11px] block mb-1">Recommended LMS Policy Action:</span>
                  <div className="text-slate-100 font-sans font-semibold text-sm">
                    {simulationResult.sample_trigger_event?.recommended_action.action_type || '60_DAY_EMI_MORATORIUM'}
                  </div>
                  <div className="text-slate-400 text-[11px] font-sans mt-0.5">
                    {simulationResult.sample_trigger_event?.recommended_action.precautionary_notes ||
                      'Automated 60-day EMI waiver applied via simulated LMS webhook integration.'}
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 text-[11px] block mb-1">
                    Impacted Borrower IDs ({simulationResult.affected_borrower_ids.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {simulationResult.affected_borrower_ids.map((id) => (
                      <span
                        key={id}
                        className="px-2 py-0.5 rounded-cs-xs bg-slate-900 border border-slate-700 text-slate-300 text-[11px]"
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
