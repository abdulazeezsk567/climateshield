/**
 * Trigger and Risk Assessment Interfaces.
 */

export enum RiskTier {
  LOW = 'LOW',
  MODERATE = 'MODERATE',
  HIGH = 'HIGH',
  SEVERE = 'SEVERE',
}

export enum ClimateHazardType {
  EXCESS_RAINFALL = 'EXCESS_RAINFALL',
  DROUGHT_DEFICIT = 'DROUGHT_DEFICIT',
  HEATWAVE_EXTREME = 'HEATWAVE_EXTREME',
  CYCLONIC_WIND = 'CYCLONIC_WIND',
  VEGETATION_STRESS = 'VEGETATION_STRESS',
}

export enum TriggerActionType {
  EMI_DEFERRAL = 'EMI_DEFERRAL',
  RECOVERY_TOPUP = 'RECOVERY_TOPUP',
  TENURE_EXTENSION = 'TENURE_EXTENSION',
  MANUAL_INSPECTION_HOLD = 'MANUAL_INSPECTION_HOLD',
}

export enum LMSExecutionStatus {
  PENDING = 'PENDING',
  ACCEPTED = 'ACCEPTED',
  REJECTED = 'REJECTED',
  SIMULATED_SUCCESS = 'SIMULATED_SUCCESS',
}

export interface TriggerActionProposal {
  action_type: TriggerActionType;
  relief_period_days?: number;
  topup_amount?: number;
  reasoning: string;
  policy_code: string;
}

export interface RiskAssessment {
  assessment_id: string;
  subject_id: string;
  risk_score: number;
  risk_tier: RiskTier;
  primary_hazard: ClimateHazardType;
  hazard_scores: Record<string, number>;
  ml_zoning_classification?: string;
  assessed_at: string;
  model_version: string;
}

export interface TriggerEvent {
  trigger_id: string;
  triggered_at: string;
  district: string;
  hazard_type: ClimateHazardType;
  severity: RiskTier;
  affected_borrower_ids: string[];
  recommended_action: TriggerActionProposal;
  execution_status: LMSExecutionStatus;
  audit_hash?: string;
}

export interface BorrowerRiskOutput {
  borrower_id: string;
  risk_score: number;
  trigger_fired: boolean;
  trigger_reason?: string;
  recommended_action?: TriggerActionProposal;
  basis_risk_flags: string[];
  evaluated_at: string;
}
