/**
 * Borrower and Loan Domain Interfaces.
 */

export enum BorrowerSector {
  AGRI_ALLIED = 'AGRI_ALLIED',
  DAIRY_LIVESTOCK = 'DAIRY_LIVESTOCK',
  HANDLOOMS_TEXTILES = 'HANDLOOMS_TEXTILES',
  FOOD_PROCESSING = 'FOOD_PROCESSING',
  RETAIL_MICRO_ENTERPRISE = 'RETAIL_MICRO_ENTERPRISE',
  SERVICES_LIGHT_MANUFACTURING = 'SERVICES_LIGHT_MANUFACTURING',
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  district: string;
  state: string;
  pin_code: string;
}

export interface LoanSummary {
  loan_id: string;
  disbursed_principal: number;
  current_outstanding_balance: number;
  monthly_emi_amount: number;
  tenure_months_remaining: number;
  currency: string;
}

export interface Borrower {
  borrower_id: string;
  anonymized_alias: string;
  sector: BorrowerSector;
  location: GeoLocation;
  active_loans: LoanSummary[];
  total_active_exposure: number;
  contact_token?: string;
}
