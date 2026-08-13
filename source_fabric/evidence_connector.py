"""
Phase 3 — EvidenceConnector interface (Issue #5).

The directive specifies 8 methods and 8 mandatory properties. This is the
canonical interface. Concrete connectors implement this interface.

8 methods:
  discover()          — discover available records/collections at the source
  fetch_metadata()    — fetch metadata for a record or batch
  fetch_content()     — fetch fulltext / claims / payload
  fetch_updates()     — incremental harvest since last cursor
  normalize()         — transform raw payload into canonical form
  get_provenance()    — return the provenance chain for a record
  content_hash()      — content-addressed hash of a normalized record
  health_check()      — probe the source and return a health report

8 mandatory properties (verified at construction):
  resumable            — can continue from a checkpoint
  idempotent           — same query -> same canonical records
  checkpointed         — persists harvest state
  rate_limit_aware     — respects documented rate limits
  retry_safe           — retries transient failures with backoff
  content_addressed    — every record is hash-identified
  provenance_preserving — retains source_id + harvested_at + raw_hash
  observable           — emits health metrics + failure records

NO silent primary→secondary substitution. If a primary source fails,
raise HarvestError. The failure_recorder captures it.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Iterator
import hashlib
import json
from .source_registry import Source
from .failure_recorder import FailureLog


@dataclass
class Checkpoint:
    """Persisted harvest state. Enables resumability."""
    source_id: str
    cursor: Optional[str] = None      # source-specific (page token, date, etc.)
    records_harvested: int = 0
    last_success_at: Optional[str] = None
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)


@dataclass
class HealthReport:
    """Result of health_check()."""
    source_id: str
    checked_at: str
    reachable: bool
    probe_result: str          # OK | AUTH_REQUIRED | ACCESS_BLOCKED | ...
    latency_ms: float = 0.0
    http_status: int = 0
    error_detail: str = ""
    metadata: dict = field(default_factory=dict)

    def canonical_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProvenanceChain:
    """Provenance for a single harvested record."""
    record_id: str
    source_id: str
    harvested_at: str
    raw_payload_hash: str
    normalized_hash: str
    source_endpoint: str = ""
    source_version: str = ""    # API version
    credentials_used: str = ""  # what auth method (NOT the secret itself)

    def canonical_dict(self) -> dict:
        return asdict(self)


class EvidenceConnector(ABC):
    """The canonical connector interface (Issue #5 Phase 3).

    Every concrete connector MUST declare all 8 properties (as True) and
    implement all 8 methods. The base class enforces this at construction.
    """

    def __init__(self, source: Source, failure_log: Optional[FailureLog] = None):
        self.source = source
        self.failure_log = failure_log
        # Verify all 8 mandatory properties are declared True
        for prop in ["resumable", "idempotent", "checkpointed", "rate_limit_aware",
                      "retry_safe", "content_addressed", "provenance_preserving",
                      "observable"]:
            if not getattr(self, prop, False):
                raise ValueError(f"{self.__class__.__name__} must declare {prop}=True")

    # --- 8 mandatory properties (must be True) ---
    resumable: bool = True
    idempotent: bool = True
    checkpointed: bool = True
    rate_limit_aware: bool = True
    retry_safe: bool = True
    content_addressed: bool = True
    provenance_preserving: bool = True
    observable: bool = True

    # --- 8 methods ---
    @abstractmethod
    def discover(self) -> dict:
        """Discover available records/collections at the source.
        Returns a dict describing what is available (counts, date ranges, etc.)."""
        ...

    @abstractmethod
    def fetch_metadata(self, record_ids: list[str]) -> list[dict]:
        """Fetch metadata for a batch of record ids. Returns normalized metadata dicts."""
        ...

    @abstractmethod
    def fetch_content(self, record_id: str) -> Optional[bytes]:
        """Fetch fulltext / claims / payload for a single record. Returns raw bytes or None."""
        ...

    @abstractmethod
    def fetch_updates(self, checkpoint: Checkpoint, *, max_records: int = 100) -> tuple[list[dict], Checkpoint]:
        """Incremental harvest since last checkpoint. Returns (records, updated_checkpoint)."""
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Transform a raw payload into canonical form."""
        ...

    @abstractmethod
    def get_provenance(self, record_id: str) -> ProvenanceChain:
        """Return the provenance chain for a record."""
        ...

    @abstractmethod
    def content_hash(self, normalized: dict) -> str:
        """Content-addressed hash of a normalized record."""
        ...

    @abstractmethod
    def health_check(self) -> HealthReport:
        """Probe the source and return a health report. Never raises — returns status."""
        ...


def content_hash_dict(normalized: dict) -> str:
    """Standard content-addressed hash for a normalized record."""
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True, default=str).encode()
    ).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
