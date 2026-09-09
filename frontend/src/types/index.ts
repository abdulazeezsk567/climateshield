/**
 * ClimateShield Presentation Layer Type Definitions.
 * Comprehensive typed contracts matching backend API schemas and presentation models.
 */

export type UserRole = 'credit_team' | 'viewer';

export interface UserProfile {
  username: string;
  role: UserRole;
  full_name: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  role: UserRole;
  full_name: string;
}

export type ClimateHazardType = 'FLOOD' | 'DROUGHT' | 'CYCLONE' | 'HEATWAVE';

export type RiskTier = 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE';

export type InterventionStatus = 'TRIGGERED' | 'NOTIFIED' | 'APPLIED' | 'CONFIRMED';

export type BorrowerSector =
  | 'Agri-Processing'
  | 'Textiles'
  | 'Cold Chain'
  | 'Food Milling'
  | 'Metal Fabrication'
  | 'Dairy & Livestock'
  | 'Retail Trade'
  | 'Handicrafts';

export interface PortfolioSummary {
  total_active_borrowers: number;
  total_credit_exposure: number;
  districts_monitored: number;
  high_risk_exposure_percentage: number;
  active_districts: string[];
}

export interface DistrictHeatmapNode {
  district: string;
  state: string;
  latitude: float;
  longitude: float;
  borrower_count: number;
  total_exposure: number;
  average_risk_score: number;
  risk_tier: RiskTier;
  primary_hazard: ClimateHazardType;
  last_monitored: string;
}

type float = number;

export interface BorrowerRiskSummary {
  borrower_id: string;
  anonymized_alias: string;
  district: string;
  sector: BorrowerSector;
  total_active_exposure: number;
  risk_score: number;
  risk_tier: RiskTier;
  trigger_fired: boolean;
  trigger_reason?: string;
  basis_risk_flags: string[];
}

export interface DetailedBorrowerRiskScorecard {
  borrower: {
    borrower_id: string;
    name: string;
    tax_identifier: string;
    contact_phone?: string;
    location: {
      district: string;
      state: string;
      latitude: number;
      longitude: number;
    };
    sector: BorrowerSector;
    total_active_exposure: number;
    active_loans: Array<{
      loan_id: string;
      principal_amount: number;
      current_balance: number;
      monthly_emi: number;
      tenor_months: number;
    }>;
  };
  risk_assessment: {
    borrower_id: string;
    risk_score: number;
    risk_tier: RiskTier;
    trigger_fired: boolean;
    confidence_interval: [number, number];
    model_version: string;
    trigger_reason?: string;
  };
  district_monthly_baseline: Record<string, number>;
  latest_telemetry: Record<string, number>;
  model_feature_contributions: Record<string, number>;
}

export interface SimulationRequest {
  district: string;
  hazard_type: ClimateHazardType;
  intensity_multiplier?: number;
  custom_rainfall_mm?: number;
  custom_temperature_celsius?: number;
  custom_ndvi_vegetation_index?: number;
}

export interface TriggerActionProposal {
  proposal_id?: string;
  action_type: string;
  recommended_relief_days?: number;
  liquidity_top_up_percentage?: number;
  precautionary_notes?: string;
}

export interface TriggerEvent {
  trigger_id: string;
  triggered_at: string;
  district: string;
  hazard_type: ClimateHazardType;
  severity: RiskTier;
  affected_borrower_ids: string[];
  recommended_action: TriggerActionProposal;
  execution_status: string;
}

export interface SimulationResultResponse {
  district: string;
  hazard_type: ClimateHazardType;
  total_borrowers_evaluated: number;
  triggers_activated: number;
  affected_borrower_ids: string[];
  generated_lms_actions_count: number;
  total_relief_exposure: number;
  sample_trigger_event?: TriggerEvent;
  simulation_timestamp: string;
}

export interface LoanInterventionRecord {
  intervention_id: string;
  borrower_id: string;
  loan_id: string;
  trigger_id: string;
  correlation_id: string;
  action_type: string;
  status: InterventionStatus;
  dispatched_at: string;
  acknowledged_at?: string;
  applied_at?: string;
  confirmed_at?: string;
  payload: Record<string, unknown>;
  lms_reference_id?: string;
  notes?: string;
}

export interface AuditLogEntry {
  audit_id: string;
  timestamp: string;
  event_type: string;
  actor: string;
  correlation_id: string;
  details: Record<string, unknown>;
  current_hash: string;
  parent_hash: string;
}

export interface AuditVerificationResponse {
  chain_valid: boolean;
  total_entries: number;
  latest_hash?: string;
  verified_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}
