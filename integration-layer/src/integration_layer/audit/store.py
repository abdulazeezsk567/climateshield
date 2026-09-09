"""Tamper-evident append-only audit log store with SHA-256 cryptographic chaining and correlation IDs."""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid

from climateshield_shared.schemas.audit import AuditEventType, AuditLogEntry
from integration_layer.audit.interfaces import AuditLogStore

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class InMemoryAuditLogStore(AuditLogStore):
    """Tamper-evident, cryptographically chained audit log ledger."""

    def __init__(self):
        self._entries: List[AuditLogEntry] = []

    def _compute_hash(
        self,
        previous_hash: str,
        timestamp: datetime,
        event_type: AuditEventType,
        origin_service: str,
        actor: str,
        correlation_id: Optional[str],
        payload_snapshot: Dict[str, Any],
    ) -> str:
        """Deterministically calculate SHA-256 hash over chained block preimage."""
        serialized_payload = json.dumps(payload_snapshot, sort_keys=True, default=str)
        corr_str = correlation_id or ""
        hash_preimage = (
            f"{previous_hash}|{timestamp.isoformat()}|{event_type.value}|"
            f"{origin_service}|{actor}|{corr_str}|{serialized_payload}"
        )
        return hashlib.sha256(hash_preimage.encode("utf-8")).hexdigest()

    async def append_entry(
        self,
        event_type: AuditEventType,
        origin_service: str,
        actor: str,
        payload_snapshot: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> AuditLogEntry:
        """Append a new audit log record with cryptographic parent hash linking."""
        now = datetime.now(timezone.utc)
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"

        previous_hash = self._entries[-1].event_hash if self._entries else GENESIS_HASH
        event_hash = self._compute_hash(
            previous_hash=previous_hash,
            timestamp=now,
            event_type=event_type,
            origin_service=origin_service,
            actor=actor,
            correlation_id=correlation_id,
            payload_snapshot=payload_snapshot,
        )

        entry = AuditLogEntry(
            audit_id=audit_id,
            correlation_id=correlation_id,
            timestamp=now,
            event_type=event_type,
            origin_service=origin_service,
            actor=actor,
            payload_snapshot=payload_snapshot,
            event_hash=event_hash,
            previous_hash=previous_hash,
        )

        self._entries.append(entry)
        return entry

    async def list_recent_entries(
        self,
        limit: int = 50,
        event_type: Optional[AuditEventType] = None,
        correlation_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Fetch chronological log entries in reverse order (newest first)."""
        filtered = self._entries
        if event_type is not None:
            filtered = [e for e in filtered if e.event_type == event_type]
        if correlation_id is not None:
            filtered = [e for e in filtered if e.correlation_id == correlation_id]

        return list(reversed(filtered))[:limit]

    async def list_all_entries(self) -> List[AuditLogEntry]:
        """Return all entries in chronological sequence."""
        return list(self._entries)

    async def verify_chain_integrity(self) -> bool:
        """Verify the cryptographic hash linkage across the entire audit trail."""
        if not self._entries:
            return True

        expected_prev = GENESIS_HASH
        for entry in self._entries:
            # 1. Verify parent linkage
            if entry.previous_hash != expected_prev:
                return False

            # 2. Recompute hash
            computed_hash = self._compute_hash(
                previous_hash=entry.previous_hash,
                timestamp=entry.timestamp,
                event_type=entry.event_type,
                origin_service=entry.origin_service,
                actor=entry.actor,
                correlation_id=entry.correlation_id,
                payload_snapshot=entry.payload_snapshot,
            )

            if computed_hash != entry.event_hash:
                return False

            expected_prev = entry.event_hash

        return True
