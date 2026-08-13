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

    The `raw_payload` is the original bytes/string from the source.
    The `normalized` is the canonical dict form used by the graph.
    Both are content-hashed.
    """
    record_id: str               # canonical id, e.g. "openalex:W1234"
    source_id: str               # the Source.source_id
    harvested_at: str            # ISO timestamp
    raw_payload_hash: str        # sha256 of raw_payload (for tamper detection)
    normalized: dict             # canonical form
    normalized_hash: str         # sha256 of normalized (for dedup)
    raw_payload: Optional[bytes] = None  # the actual raw bytes (optional)
    language: str = "en"         # ISO 639-1 language code
    original_language: str = "en"  # if translated, the original language
    provenance: dict = field(default_factory=dict)  # additional provenance

    def canonical_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_payload", None)  # don't hash the bytes again
        return d

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.canonical_dict(), sort_keys=True, default=str).encode()
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
    """Abstract connector. Concrete connectors implement the harvest method.

    Enforced invariants:
      1. Idempotency: harvesting the same (source_id, query) twice yields
         records with the same `normalized_hash` set.
      2. Resumability: if a harvest fails mid-way, the next call with the
         same HarvestState continues from the last cursor.
      3. Provenance: every HarvestedRecord carries source_id + harvested_at
         + raw_payload_hash.
      4. No silent substitution: if the primary source fails, raise
         HarvestError — do NOT fall back to a secondary source. The failure
         recorder captures the error; the gap is reported honestly.
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


class HarvestError(Exception):
    """Raised when a primary source fails. NEVER caught silently."""


def hash_payload(raw: bytes | str) -> str:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
