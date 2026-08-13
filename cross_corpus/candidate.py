"""
Candidate pipeline: seal -> freeze -> outcome -> score (Issue #4).

Mirrors PSCD-1's prediction-freeze protocol:
  1. At freeze time, candidates are committed (hash-sealed, immutable).
  2. Outcomes are released only AFTER the freeze timestamp.
  3. Scoring is deterministic: a candidate is CONFIRMED iff a document in
     the prediction window matches its predicted_outcome signature; otherwise
     NOT_CONFIRMED. UNKNOWN (no documents in window) is never CONFIRMED.

The pipeline is fail-closed: any tamper with the freeze invalidates scoring.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .schema import Candidate


@dataclass
class PredictionFreeze:
    freeze_id: str
    candidates: list[dict]            # list of candidate canonical dicts
    candidate_hashes: list[str]       # sha256 of each candidate
    root_hash: str                    # sha256 of all candidate_hashes joined
    frozen_at: str                    # ISO timestamp
    cutoff: str                       # temporal cutoff used for the freeze

    @classmethod
    def from_candidates(cls, candidates: list[Candidate], cutoff: str) -> "PredictionFreeze":
        now = datetime.now(timezone.utc)
        canonical = [c.canonical_dict() for c in candidates]
        hashes = [c.content_hash() for c in candidates]
        root = hashlib.sha256("|".join(hashes).encode()).hexdigest()
        return cls(
            freeze_id=f"freeze:{root[:12]}",
            candidates=canonical,
            candidate_hashes=hashes,
            root_hash=root,
            frozen_at=now.isoformat(),
            cutoff=cutoff,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def from_json(cls, s: str) -> "PredictionFreeze":
        d = json.loads(s)
        return cls(**d)


@dataclass
class OutcomeRecord:
    candidate_id: str
    decision: str          # CONFIRMED | NOT_CONFIRMED | UNKNOWN
    evidence_id: Optional[str] = None    # the document id that confirmed
    evidence_date: Optional[str] = None
    released_at: str = ""

    def canonical_dict(self) -> dict:
        return asdict(self)


@dataclass
class OutcomeRelease:
    release_id: str
    outcomes: list[dict]
    released_at: str
    freeze_root_hash: str    # links back to the freeze

    @classmethod
    def from_outcomes(cls, outcomes: list[OutcomeRecord], freeze: PredictionFreeze) -> "OutcomeRelease":
        return cls(
            release_id=f"release:{hashlib.sha256(str(datetime.now(timezone.utc)).encode()).hexdigest()[:12]}",
            outcomes=[o.canonical_dict() for o in outcomes],
            released_at=datetime.now(timezone.utc).isoformat(),
            freeze_root_hash=freeze.root_hash,
        )


def deterministic_score(candidate: Candidate, outcome: OutcomeRecord) -> str:
    """Return CONFIRMED / NOT_CONFIRMED / UNKNOWN. Deterministic, no LLM.

    The outcome record already carries the decision (computed against the
    real prediction-window corpus by the orchestrator). We only validate that
    the decision is from the controlled vocabulary.
    """
    if outcome.decision not in ("CONFIRMED", "NOT_CONFIRMED", "UNKNOWN"):
        return "INVALID"
    # UNKNOWN is never CONFIRMED — the candidate's prediction window has not
    # yet produced checkable evidence. We return UNKNOWN honestly.
    return outcome.decision


def write_freeze(freeze: PredictionFreeze, dirpath: Path):
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "freeze.json").write_text(freeze.to_json())
    # also write a hash sidecar for tamper detection
    h = hashlib.sha256(freeze.to_json().encode()).hexdigest()
    (dirpath / "freeze.json.sha256").write_text(h)


def verify_freeze(dirpath: Path) -> dict:
    freeze_path = dirpath / "freeze.json"
    hash_path = dirpath / "freeze.json.sha256"
    if not freeze_path.exists() or not hash_path.exists():
        return {"valid": False, "reason": "freeze files missing"}
    content = freeze_path.read_text()
    expected = hash_path.read_text().strip()
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != expected:
        return {"valid": False, "reason": "freeze hash mismatch (tampered)"}
    freeze = PredictionFreeze.from_json(content)
    # re-derive root hash and check
    recomputed = hashlib.sha256(
        "|".join(freeze.candidate_hashes).encode()
    ).hexdigest()
    if recomputed != freeze.root_hash:
        return {"valid": False, "reason": "root hash mismatch"}
    return {"valid": True, "freeze": freeze}
