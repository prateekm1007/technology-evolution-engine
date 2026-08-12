"""
Canonical Prediction Schema — PSCD-1

Every prediction emitted by any arm (A0, A1, A2, A3) must conform to this schema.
The retrieval_negative_attestation field is machine-checkable, not a text assertion.
"""
import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Prediction:
    prediction_id: str
    claim: str                          # The proposed relationship (one sentence)
    mechanism: str                       # Scientific mechanism behind the claim
    quantitative_forecast: str           # Specific numeric or binary prediction
    tolerance: str                       # Pre-registered tolerance (e.g., "±20%" or "exact YES/NO")
    falsification_condition: str         # What result would falsify this prediction
    measurement_protocol: str            # How to measure the prediction
    evidence_ids: list                   # IDs of evidence sources used
    retrieval_snapshot_hash: str         # SHA-256 of the frozen retrieval corpus
    model_id: str                        # Frozen model identifier
    prompt_hash: str                     # SHA-256 of the prompt template
    generation_timestamp: str            # ISO-8601 UTC
    retrieval_negative_attestation: dict # Machine-checkable: no retrieved source entails the claim
    arm: str                             # A0, A1, A2, A3
    receipt_hash: str = ""               # Computed after creation


def validate_prediction(p: Prediction) -> tuple[bool, list[str]]:
    """Validate a Prediction object. Returns (all_ok, list_of_errors)."""
    errors = []

    # Required fields non-empty
    for field_name in ["prediction_id", "claim", "mechanism", "quantitative_forecast",
                       "tolerance", "falsification_condition", "measurement_protocol",
                       "retrieval_snapshot_hash", "model_id", "prompt_hash",
                       "generation_timestamp", "arm"]:
        val = getattr(p, field_name, "")
        if not val:
            errors.append(f"{field_name} is empty")

    # evidence_ids: A0 may have empty list (no retrieval); A1+ must have non-empty
    if not isinstance(p.evidence_ids, list):
        errors.append("evidence_ids must be a list")
    elif p.arm != "A0" and len(p.evidence_ids) == 0:
        errors.append("evidence_ids must be non-empty for arms with retrieval (A1+)")

    # retrieval_negative_attestation must be machine-checkable
    # A prediction may be sealed ONLY after an actual entailment check has executed.
    # The attestation fields must be populated from the actual frozen snapshot,
    # not hardcoded.
    att = p.retrieval_negative_attestation
    if not isinstance(att, dict):
        errors.append("retrieval_negative_attestation must be a dict")
    else:
        # is_retrieval_negative must NOT be hardcoded True — it must be the result
        # of an actual entailment check. We verify it was populated (not a placeholder).
        if att.get("is_retrieval_negative") is None:
            errors.append("retrieval_negative_attestation.is_retrieval_negative must be set by entailment check, not hardcoded")
        if not att.get("check_method"):
            errors.append("retrieval_negative_attestation.check_method must be specified")
        if att.get("check_method", "").startswith("pending"):
            errors.append("retrieval_negative_attestation.check_method must not be 'pending' — entailment check must have executed")
        # evidence_source_hashes_checked must be populated from actual frozen snapshot
        # For A0 (no retrieval), this may be an empty list (no sources to check)
        if p.arm != "A0":
            if not att.get("evidence_source_hashes_checked"):
                errors.append("retrieval_negative_attestation.evidence_source_hashes_checked must be populated from frozen snapshot")
        if not att.get("entailment_check_result"):
            errors.append("retrieval_negative_attestation.entailment_check_result must be set by entailment check")

    # arm must be one of the pre-registered arms
    if p.arm not in ("A0", "A1", "A2", "A3"):
        errors.append(f"arm must be A0, A1, A2, or A3 — got {p.arm}")

    # generation_timestamp must be ISO-8601
    try:
        datetime.fromisoformat(p.generation_timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        errors.append("generation_timestamp must be valid ISO-8601")

    return (len(errors) == 0, errors)


def seal_prediction(p: Prediction) -> str:
    """Compute receipt_hash for a prediction (immutable after this)."""
    d = asdict(p)
    d.pop("receipt_hash", None)
    canonical = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_prediction(p: Prediction) -> bool:
    """Verify that receipt_hash matches."""
    stored = p.receipt_hash
    if not stored:
        return False
    p_copy = Prediction(**{k: v for k, v in asdict(p).items() if k != "receipt_hash"})
    computed = seal_prediction(p_copy)
    return computed == stored


# Schema definition for documentation
PREDICTION_SCHEMA = {
    "prediction_id": "str — unique identifier",
    "claim": "str — one-sentence proposed relationship",
    "mechanism": "str — scientific mechanism",
    "quantitative_forecast": "str — specific numeric or binary prediction",
    "tolerance": "str — pre-registered tolerance (e.g., '±20%' or 'exact YES/NO')",
    "falsification_condition": "str — what result would falsify",
    "measurement_protocol": "str — how to measure",
    "evidence_ids": "list[str] — IDs of evidence sources used",
    "retrieval_snapshot_hash": "str — SHA-256 of frozen retrieval corpus",
    "model_id": "str — frozen model identifier",
    "prompt_hash": "str — SHA-256 of prompt template",
    "generation_timestamp": "str — ISO-8601 UTC",
    "retrieval_negative_attestation": {
        "is_retrieval_negative": "bool — True if no retrieved source directly entails the claim",
        "check_method": "str — how this was checked (e.g., 'deterministic_entailment_check')",
        "evidence_source_hashes_checked": "list[str] — SHA-256 of each source checked",
        "entailment_check_result": "str — 'NOT_ENTAILED' if no source entails the claim",
    },
    "arm": "str — A0, A1, A2, or A3",
    "receipt_hash": "str — SHA-256 of the prediction (immutable after creation)",
}
