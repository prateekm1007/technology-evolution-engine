"""
custodian.src.audit_trail — Audit trail for custody transitions.

Every important custody transition is recorded:
    SOURCE_REGISTERED
    CANDIDATES_GENERATED
    BENCHMARK_CONSTRUCTED
    BENCHMARK_VALIDATED
    FIXTURE_GENERATED
    HASH_COMPUTED
    BENCHMARK_SEALED
    BENCHMARK_EXPORTED

Each event includes:
    timestamp
    event_type
    benchmark_id
    actor / process
    software version
    relevant hash

Canonical audit events must be deterministic where the existing architecture
requires deterministic replay. This module does NOT use Date.now() in
canonical proof material — timestamps are provided externally or recorded
in non-canonical metadata only.
"""
from dataclasses import dataclass, field
from typing import List, Optional

# Event types
SOURCE_REGISTERED = "SOURCE_REGISTERED"
CANDIDATES_GENERATED = "CANDIDATES_GENERATED"
BENCHMARK_CONSTRUCTED = "BENCHMARK_CONSTRUCTED"
BENCHMARK_VALIDATED = "BENCHMARK_VALIDATED"
FIXTURE_GENERATED = "FIXTURE_GENERATED"
HASH_COMPUTED = "HASH_COMPUTED"
BENCHMARK_SEALED = "BENCHMARK_SEALED"
BENCHMARK_EXPORTED = "BENCHMARK_EXPORTED"


@dataclass
class AuditEvent:
    timestamp: str
    event_type: str
    benchmark_id: str
    actor: str
    software_version: str
    relevant_hash: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "benchmark_id": self.benchmark_id,
            "actor": self.actor,
            "software_version": self.software_version,
            "relevant_hash": self.relevant_hash,
            "details": self.details,
        }


class AuditTrail:
    """Append-only audit trail."""

    def __init__(self):
        self._events: List[AuditEvent] = []

    def record(
        self,
        event_type: str,
        benchmark_id: str,
        actor: str,
        software_version: str = "1.0.0",
        relevant_hash: str = "",
        details: Optional[dict] = None,
        timestamp: Optional[str] = None,
    ):
        """Record an audit event. Timestamp must be provided externally
        for canonical proof material, or defaults to empty for non-canonical use."""
        event = AuditEvent(
            timestamp=timestamp or "",
            event_type=event_type,
            benchmark_id=benchmark_id,
            actor=actor,
            software_version=software_version,
            relevant_hash=relevant_hash,
            details=details or {},
        )
        self._events.append(event)

    def get_events(self) -> List[AuditEvent]:
        return list(self._events)

    def to_dict(self) -> dict:
        return {
            "events": [e.to_dict() for e in self._events],
            "event_count": len(self._events),
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2)
