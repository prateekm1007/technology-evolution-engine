"""
Phase 11 — Connector health system (Issue #5).

Emits CONNECTOR_HEALTH.json with 12 metrics per the directive:
  discovered, accepted, rejected, HTTP errors, auth errors, rate limits,
  schema changes, missing fields, duplicate rate, hash collisions,
  latency, last successful probe
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import json


@dataclass
class ConnectorHealth:
    source_id: str
    discovered: int = 0            # records discovered at source
    accepted: int = 0              # records accepted into graph
    rejected: int = 0              # records rejected by integrity firewall
    http_errors: int = 0           # HTTP 4xx/5xx
    auth_errors: int = 0           # 401/403
    rate_limits: int = 0           # 429
    schema_changes: int = 0        # response shape differs from expected
    missing_fields: int = 0        # required fields missing
    duplicate_rate: float = 0.0    # duplicate / total
    hash_collisions: int = 0       # different content, same hash (should be 0)
    latency_ms_avg: float = 0.0    # average latency
    latency_ms_p95: float = 0.0    # p95 latency
    last_successful_probe: Optional[str] = None  # ISO timestamp
    total_records_seen: int = 0    # for duplicate_rate calculation

    def canonical_dict(self) -> dict:
        return asdict(self)


class HealthTracker:
    """Tracks health metrics for all connectors. Emits CONNECTOR_HEALTH.json."""

    def __init__(self):
        self._health: dict[str, ConnectorHealth] = {}

    def get_or_create(self, source_id: str) -> ConnectorHealth:
        if source_id not in self._health:
            self._health[source_id] = ConnectorHealth(source_id=source_id)
        return self._health[source_id]

    def record_discovery(self, source_id: str, count: int):
        h = self.get_or_create(source_id)
        h.discovered += count
        h.total_records_seen += count

    def record_accept(self, source_id: str, count: int):
        h = self.get_or_create(source_id)
        h.accepted += count

    def record_reject(self, source_id: str, count: int):
        h = self.get_or_create(source_id)
        h.rejected += count

    def record_http_error(self, source_id: str, status: int):
        h = self.get_or_create(source_id)
        h.http_errors += 1
        if status in (401, 403):
            h.auth_errors += 1
        elif status == 429:
            h.rate_limits += 1

    def record_schema_change(self, source_id: str):
        h = self.get_or_create(source_id)
        h.schema_changes += 1

    def record_missing_field(self, source_id: str):
        h = self.get_or_create(source_id)
        h.missing_fields += 1

    def record_hash_collision(self, source_id: str):
        h = self.get_or_create(source_id)
        h.hash_collisions += 1

    def record_latency(self, source_id: str, latency_ms: float):
        h = self.get_or_create(source_id)
        # simple running average (production: use a histogram)
        if h.latency_ms_avg == 0:
            h.latency_ms_avg = latency_ms
        else:
            h.latency_ms_avg = 0.95 * h.latency_ms_avg + 0.05 * latency_ms
        if latency_ms > h.latency_ms_p95:
            h.latency_ms_p95 = latency_ms

    def record_successful_probe(self, source_id: str):
        h = self.get_or_create(source_id)
        h.last_successful_probe = datetime.now(timezone.utc).isoformat()

    def update_duplicate_rate(self, source_id: str):
        h = self.get_or_create(source_id)
        if h.total_records_seen > 0:
            h.duplicate_rate = (h.total_records_seen - h.accepted) / h.total_records_seen

    def emit_health_json(self, path) -> dict:
        """Write CONNECTOR_HEALTH.json — the Phase 11 deliverable."""
        import hashlib
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        for sid in self._health:
            self.update_duplicate_rate(sid)
        records = [h.canonical_dict() for h in self._health.values()]
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_connectors_tracked": len(records),
            "summary": {
                "total_discovered": sum(h.discovered for h in self._health.values()),
                "total_accepted": sum(h.accepted for h in self._health.values()),
                "total_rejected": sum(h.rejected for h in self._health.values()),
                "total_http_errors": sum(h.http_errors for h in self._health.values()),
                "total_auth_errors": sum(h.auth_errors for h in self._health.values()),
                "total_rate_limits": sum(h.rate_limits for h in self._health.values()),
                "total_schema_changes": sum(h.schema_changes for h in self._health.values()),
                "total_hash_collisions": sum(h.hash_collisions for h in self._health.values()),
            },
            "connectors": records,
        }
        file_content = json.dumps(payload, sort_keys=True, indent=2, default=str)
        path.write_text(file_content)
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(file_hash)
        return payload

    def summary(self) -> dict:
        return {
            "total_connectors_tracked": len(self._health),
            "total_discovered": sum(h.discovered for h in self._health.values()),
            "total_accepted": sum(h.accepted for h in self._health.values()),
            "total_rejected": sum(h.rejected for h in self._health.values()),
        }
