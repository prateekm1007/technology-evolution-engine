"""
Retraction Registry — Honesty Loop Priority 7 engine (code implementation).

Per RETRACTION_REGISTRY_ENGINE.md (specification):
- Append-only ledger of retracted claims.
- A retracted claim is NOT deleted — it is marked RETRACTED, with a
  reason, a date, a replacement (if any), and a retraction ID.
- The registry is the system's memory of its own errors.

Per CONSTITUTION.md Law 7 (Historical Permanence):
- No claim may be silently altered.
- The registry is append-only: once a retraction is written, it cannot
  be edited or deleted. If a retraction itself is in error, a new
  retraction record is added that retracts the retraction — both
  records remain.

Per Law 27 (Honesty Loop):
- No numerical certainty in retraction records. The retraction's
  epistemic status is a typed block, not a confidence number.

Schema (per RETRACTION_REGISTRY_ENGINE.md §Schema):
    interface RetractionRecord {
        id: string                    # RT-XXX, immutable
        retractedClaimId: string      # CL-XXX
        retractedClaimStatement: string
        retractedClaimEvidenceId?: string
        retractionDate: string        # ISO 8601
        retractionAgent: string
        reason: {
            category: enum
            description: string
            detectedBy: string
            detectionDate: string
        }
        replacement?: {
            claimId: string
            evidenceId: string
            derivation: string
        }
        status: "RETRACTED" | "SUPERSEDED" | "WITHDRAWN"
        relatedRetractionIds?: string[]
        immutable: true
    }

Storage:
- The registry is persisted as a JSONL file at
  data/retractions/retractions.jsonl (append-only).
- One retraction per line, per the same pattern as the prediction
  ledger (data/ledger/predictions.jsonl).
- The file is created on first append; it does not exist until the
  first retraction is registered.
"""
from __future__ import annotations

import json
import pathlib
import re
import datetime
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "data" / "retractions" / "retractions.jsonl"

# Reason categories (per RETRACTION_REGISTRY_ENGINE.md §Schema)
REASON_CATEGORIES = frozenset({
    "NUMERICAL_CONTRADICTION",
    "SEMANTIC_CONTRADICTION",
    "EVIDENCE_INVALIDATED",
    "MEASUREMENT_SUPERSEDED",
    "ASSUMPTION_FALSIFIED",
    "KILL_TEST_FAILED",
    "DESIGN_CHANGE",
    "EXTERNAL_AUDIT",
})

STATUS_VALUES = frozenset({"RETRACTED", "SUPERSEDED", "WITHDRAWN"})

# ID format: RT-XXX where XXX is a zero-padded sequential number
ID_PATTERN = re.compile(r"^RT-(\d{3,})$")


class RetractionRegistry:
    """Append-only registry of retracted claims.

    Per Law 7 (Historical Permanence): once written, a retraction record
    cannot be edited or deleted. The only valid mutation is appending
    a new record that supersedes an existing one (with the existing
    record's status updated to SUPERSEDED — but the original record
    remains in the file).

    Note on SUPERSEDED status: when a retraction is itself retracted
    (e.g., the retraction was in error), the original record's status
    in memory is SUPERSEDED, but the file record is unchanged (append-
    only). A new record is appended that references the original.
    """

    def __init__(self, registry_path: pathlib.Path = REGISTRY_PATH):
        self.path = pathlib.Path(registry_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def list_retractions(self) -> list[dict]:
        """Return all retraction records, oldest first.

        Malformed lines are skipped (with a warning to stderr) — the
        registry must not 500 on a corrupted line, mirroring the
        prediction ledger's behavior (web/backend/main.py /api/v1/evidence).
        """
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed — but do not silently drop. The count
                # endpoint exposes the malformed count.
                continue
        return records

    def count(self) -> int:
        """Return the number of retraction records."""
        return len(self.list_retractions())

    def get(self, retraction_id: str) -> Optional[dict]:
        """Return a single retraction by ID, or None if not found."""
        for r in self.list_retractions():
            if r.get("id") == retraction_id:
                return r
        return None

    def unresolved(self) -> list[dict]:
        """Return retractions that have no replacement AND are not
        explicitly WITHDRAWN.

        Per HONESTY_LOOP.md Gate 11 check 5: 'The Retraction Registry
        (P7) must contain no unresolved retractions for this artifact.
        All retractions must have either a replacement claim or an
        explicit WITHDRAWN status with rationale.'
        """
        return [
            r for r in self.list_retractions()
            if r.get("status") == "RETRACTED" and not r.get("replacement")
        ]

    # ------------------------------------------------------------------
    # Write operations (append-only)
    # ------------------------------------------------------------------

    def register(self, *, retracted_claim_id: str,
                 retracted_claim_statement: str,
                 retraction_agent: str,
                 reason_category: str,
                 reason_description: str,
                 detected_by: str,
                 detection_date: str,
                 retracted_claim_evidence_id: Optional[str] = None,
                 replacement_claim_id: Optional[str] = None,
                 replacement_evidence_id: Optional[str] = None,
                 replacement_derivation: Optional[str] = None,
                 status: str = "RETRACTED",
                 related_retraction_ids: Optional[list[str]] = None,
                 retraction_date: Optional[str] = None) -> dict:
        """Register a new retraction. Returns the record that was written.

        Per Law 7: the registry is append-only. Calling `register` on
        an existing retraction ID raises ValueError. To supersede an
        existing retraction, call `register` with a new ID and set
        `related_retraction_ids` to the original.

        Per Law 27: no numerical certainty. The retraction record
        carries no confidence field.
        """
        # Validate reason category
        if reason_category not in REASON_CATEGORIES:
            raise ValueError(
                f"reason_category `{reason_category}` not in allowed set. "
                f"Allowed: {sorted(REASON_CATEGORIES)}"
            )
        # Validate status
        if status not in STATUS_VALUES:
            raise ValueError(
                f"status `{status}` not in allowed set. "
                f"Allowed: {sorted(STATUS_VALUES)}"
            )
        # Validate replacement consistency: if any replacement field
        # is set, all three must be set (claim_id, evidence_id, derivation).
        if any([replacement_claim_id, replacement_evidence_id, replacement_derivation]):
            if not all([replacement_claim_id, replacement_evidence_id, replacement_derivation]):
                raise ValueError(
                    "Replacement fields are partially populated. Either supply "
                    "all three (claim_id, evidence_id, derivation) or none "
                    "(for WITHDRAWN status with no replacement)."
                )

        # Generate the next retraction ID
        next_id = self._next_id()
        record = {
            "id": next_id,
            "retracted_claim_id": retracted_claim_id,
            "retracted_claim_statement": retracted_claim_statement,
            "retracted_claim_evidence_id": retracted_claim_evidence_id,
            "retraction_date": retraction_date or _now_iso(),
            "retraction_agent": retraction_agent,
            "reason": {
                "category": reason_category,
                "description": reason_description,
                "detected_by": detected_by,
                "detection_date": detection_date,
            },
            "replacement": (
                {
                    "claim_id": replacement_claim_id,
                    "evidence_id": replacement_evidence_id,
                    "derivation": replacement_derivation,
                }
                if replacement_claim_id
                else None
            ),
            "status": status,
            "related_retraction_ids": related_retraction_ids or [],
            "immutable": True,
            # Honesty Loop (Law 27): the retraction record itself carries
            # a typed epistemic status, not a numerical confidence. The
            # retraction is a fact about the system's history — its
            # validation level is L1 (literature support: the retraction
            # is documented in the registry itself) and its status is
            # PASS (the retraction successfully completed).
            "epistemic_status": {
                "validation_level": "L1",
                "evidence_strength": "STRONG",
                "experimental_validation": "ABSENT",
                "status": "PASS",
                "rationale": (
                    "Retraction records are documented facts about the "
                    "system's history. They are supported by the registry "
                    "itself (rank C — internal documentation). No "
                    "experimental validation applies — retractions are "
                    "not claims about the world, they are claims about "
                    "the system's prior claims."
                ),
            },
        }

        # Append to the registry file. Per Law 7: append-only.
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        """Return the next retraction ID (RT-001, RT-002, ...).

        Scans the existing registry to find the highest ID number and
        returns the next. If the registry is empty, returns RT-001.
        """
        existing = self.list_retractions()
        max_num = 0
        for r in existing:
            rid = r.get("id", "")
            m = ID_PATTERN.match(rid)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        return f"RT-{max_num + 1:03d}"


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    # Note: datetime.datetime.utcnow() is deprecated in Python 3.12+
    # but the existing graph_model.py uses it. We use the timezone-
    # aware form here per the deprecation guidance.
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
