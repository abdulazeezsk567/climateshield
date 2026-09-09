"""Abstract interface for the immutable audit log store."""

from abc import ABC, abstractmethod
from typing import List, Optional
from climateshield_shared.schemas.audit import AuditEventType, AuditLogEntry


class AuditLogStore(ABC):
    """Protocol for tamper-evident append-only audit trail logging."""

    @abstractmethod
    async def append_entry(
        self,
        event_type: AuditEventType,
        origin_service: str,
        actor: str,
        payload_snapshot: dict,
        correlation_id: Optional[str] = None,
    ) -> AuditLogEntry:
        """Append a new audit entry with cryptographic parent hash linking and correlation ID.

        Args:
            event_type: Classification of the event.
            origin_service: Service responsible.
            actor: Initiating user, system, or API key ID.
            payload_snapshot: JSON-serializable snapshot of transaction parameters.
            correlation_id: Optional workflow/trigger correlation identifier.

        Returns:
            Newly created and hashed AuditLogEntry.
        """
        pass

    @abstractmethod
    async def list_recent_entries(
        self,
        limit: int = 50,
        event_type: Optional[AuditEventType] = None,
        correlation_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Fetch chronological log entries for review and inspection.

        Args:
            limit: Maximum count of entries to return.
            event_type: Optional event filter.
            correlation_id: Optional correlation filter.

        Returns:
            List of AuditLogEntry records.
        """
        pass

    @abstractmethod
    async def verify_chain_integrity(self) -> bool:
        """Verify the cryptographic hash linkage across all stored audit entries.

        Returns:
            True if all hashes and parent links are valid, False if tampering detected.
        """
        pass
