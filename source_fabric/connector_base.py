"""
Connector base class (Issue #5).

Every connector MUST be:
  - resumable: a failed/partial harvest can be continued
  - idempotent: re-running the same query yields the same canonical records
  - provenance-preserving: every record carries source_id + harvested_at
  - content-addressed: every record is hashed; same content -> same hash

The connector NEVER silently substitutes a secondary source for a primary
source. If a primary source fails, the failure is RECORDED (failure_recorder.py)
and the gap is reported honestly — never papered over with a secondary source.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Iterator
import hashlib
import json
from .source_registry import Source


@dataclass
class HarvestedRecord:
    """A single record harvested from a source.

    THREE distinct hashes (per CTO V3 directive):

    1. raw_content_hash — SHA-256 of the raw bytes received from the source.
       Tamper detection for the wire payload.

    2. normalized_content_hash — SHA-256 of the canonical normalized content
       ONLY (no harvest timestamp, no connector version, no provenance metadata).
       INVARIANT: identical normalized content → identical normalized_content_hash,
       regardless of when/how it was harvested.

    3. record_manifest_hash — SHA-256 of the full record including provenance
       metadata (source_id, harvested_at, connector_version). Used for audit
       trail integrity (detects post-harvest mutation of the record itself).

    The old `content_hash()` method (which conflated these) is DEPRECATED.
    """
    record_id: str               # canonical id, e.g. "openalex:W1234"
    source_id: str               # the Source.source_id
    harvested_at: str            # ISO timestamp
    raw_payload_hash: str        # sha256 of raw_payload bytes
    normalized: dict             # canonical form (CONTENT ONLY)
    normalized_hash: str         # sha256 of normalized content ONLY
    raw_payload: Optional[bytes] = None  # the actual raw bytes (optional)
    language: str = "en"
    original_language: str = "en"
    provenance: dict = field(default_factory=dict)
    connector_version: str = ""  # for manifest hash

    def canonical_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_payload", None)
        return d

    # --- DEPRECATED (conflates content + provenance; use the 3 methods below) ---
    def content_hash(self) -> str:
        """DEPRECATED. Use raw_content_hash / normalized_content_hash / record_manifest_hash."""
        return self.record_manifest_hash()

    # --- V3: three distinct hashes ---

    def raw_content_hash(self) -> str:
        """SHA-256 of the raw payload bytes. Tamper detection for wire data."""
        if self.raw_payload is None:
            return self.raw_payload_hash  # use the stored hash if bytes not retained
        return hashlib.sha256(self.raw_payload).hexdigest()

    def normalized_content_hash(self) -> str:
        """SHA-256 of the normalized CONTENT ONLY.

        INVARIANT: identical normalized content → identical hash, regardless of
        harvest timestamp, connector version, or provenance metadata.

        This is the dedup hash. Two records with the same scientific content
        harvested at different times MUST produce the same normalized_content_hash.
        """
        return hashlib.sha256(
            json.dumps(self.normalized, sort_keys=True, default=str).encode()
        ).hexdigest()

    def record_manifest_hash(self) -> str:
        """SHA-256 of the full record including provenance metadata.

        Used for audit-trail integrity (detects post-harvest mutation).
        Includes: record_id, source_id, harvested_at, connector_version,
        raw_payload_hash, normalized_content_hash, language.
        """
        manifest = {
            "record_id": self.record_id,
            "source_id": self.source_id,
            "harvested_at": self.harvested_at,
            "connector_version": self.connector_version,
            "raw_payload_hash": self.raw_payload_hash,
            "normalized_content_hash": self.normalized_content_hash(),
            "language": self.language,
            "original_language": self.original_language,
        }
        return hashlib.sha256(
            json.dumps(manifest, sort_keys=True, default=str).encode()
        ).hexdigest()


@dataclass
class HarvestState:
    """Resumable harvest state. Persisted between runs."""
    source_id: str
    last_harvested_at: Optional[str] = None
    last_cursor: Optional[str] = None      # source-specific cursor (e.g., page token, date)
    records_harvested: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)


class Connector(ABC):
    """DEPRECATED (CTO V3 directive). Use EvidenceConnector instead.

    This abstract class is retained for historical permanence (Law 7) but
    should NOT be subclassed by new connectors. The sole connector contract
    is now `EvidenceConnector` (see evidence_connector.py), which defines
    8 methods + 8 mandatory properties.

    Existing subclasses in source_validator.py are stubs that raise
    HarvestError in offline mode — they do not perform real harvests.
    """
    source: Source

    def __init__(self, source: Source):
        self.source = source

    @abstractmethod
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        """Harvest up to max_records. Returns (records, updated_state).

        If the source is unavailable, raise HarvestError. Do NOT return
        empty records as a silent success.
        """
        ...

    @abstractmethod
    def validate(self) -> dict:
        """Validate accessibility, schema, license, rate-limit. Returns a
        structured validation report. Does NOT raise — returns status."""
        ...


# =====================================================================
# V3 Connector status vocabulary (per CTO directive)
# =====================================================================
# A connector is OPERATIONAL only after a real network probe AND successful
# sample retrieval. No "healthy" status based solely on object construction.
CONNECTOR_STATUS_VOCAB = {
    "DISCOVERED",    # source identified in the registry, no code yet
    "CATALOGUED",    # source has a full 24-field registry record
    "IMPLEMENTED",   # connector code exists (class defined, not yet probed)
    "PROBED",        # health_check() ran a live network probe (may have failed)
    "OPERATIONAL",   # live probe succeeded + at least 1 real record retrieved
    "FAILED",        # live probe failed (auth/blocked/rate-limited/schema-changed)
}


def is_operational(status: str) -> bool:
    """A connector is operational ONLY if status == 'OPERATIONAL'."""
    return status == "OPERATIONAL"


class HarvestError(Exception):
    """Raised when a primary source fails. NEVER caught silently."""


def hash_payload(raw: bytes | str) -> str:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
