/**
 * Immutable Audit Log Interfaces.
 */

export enum AuditEventType {
  DATA_INGESTION_COMPLETED = 'DATA_INGESTION_COMPLETED',
  TRIGGER_FIRED = 'TRIGGER_FIRED',
  LMS_WEBHOOK_DISPATCHED = 'LMS_WEBHOOK_DISPATCHED',
  LMS_RESPONSE_RECORDED = 'LMS_RESPONSE_RECORDED',
  BORROWER_ALERT_SENT = 'BORROWER_ALERT_SENT',
  MANUAL_OVERRIDE_APPLIED = 'MANUAL_OVERRIDE_APPLIED',
}

export interface AuditLogEntry {
  audit_id: string;
  timestamp: string;
  event_type: AuditEventType;
  origin_service: string;
  actor: string;
  payload_snapshot: Record<string, unknown>;
  event_hash: string;
  previous_hash?: string;
}
