"""
Contract loader and validator (CTO V17 #5, #6).

Per CTO: "Wire CLAIM_CONTRACT_V10.json into the validator. The contract must
be consumed, not merely stored. Hash-pin the active contract and record its
hash in every Claim/artifact."
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Optional

CONTRACT_PATH = Path(__file__).parent / "CLAIM_CONTRACT_V10.json"

# Active contract hash — computed at load time, recorded in every Claim
_ACTIVE_CONTRACT_HASH: Optional[str] = None
_ACTIVE_CONTRACT: Optional[dict] = None


def load_contract() -> dict:
    """Load the active CLAIM_CONTRACT_V10.json."""
    global _ACTIVE_CONTRACT, _ACTIVE_CONTRACT_HASH
    if _ACTIVE_CONTRACT is None:
        with open(CONTRACT_PATH) as f:
            _ACTIVE_CONTRACT = json.load(f)
        content = json.dumps(_ACTIVE_CONTRACT, sort_keys=True)
        _ACTIVE_CONTRACT_HASH = hashlib.sha256(content.encode()).hexdigest()
    return _ACTIVE_CONTRACT


def get_contract_hash() -> str:
    """Get the hash of the active contract."""
    load_contract()
    return _ACTIVE_CONTRACT_HASH


def get_contract_short_hash() -> str:
    """Get the short hash of the active contract (for display in Claims)."""
    return get_contract_hash()[:16]


def validate_claim_against_contract(claim) -> tuple[bool, str]:
    """Validate a Claim against the frozen contract.

    Per CTO V17 #5: "validate_claim_against_contract(claim)"
    """
    contract = load_contract()
    fields = contract.get("fields", {})

    # Check required fields exist
    for field_name, field_spec in fields.items():
        if field_spec.get("required") and not hasattr(claim, field_name):
            return False, f"missing required field: {field_name}"

    # Check schema version
    if claim.claim_schema_version != contract.get("schema_version"):
        return False, f"schema_version mismatch: claim={claim.claim_schema_version}, contract={contract.get('schema_version')}"

    # Check validator version
    if claim.validator_version != contract.get("validator_version"):
        return False, f"validator_version mismatch: claim={claim.validator_version}, contract={contract.get('validator_version')}"

    # Check extraction version
    if claim.extraction_version != contract.get("extraction_version"):
        return False, f"extraction_version mismatch: claim={claim.extraction_version}, contract={contract.get('extraction_version')}"

    # Check claim_type is in allowed enum
    allowed_types = fields.get("claim_type", {}).get("enum", [])
    if allowed_types and claim.claim_type not in allowed_types:
        return False, f"claim_type '{claim.claim_type}' not in allowed enum"

    # Check status is in allowed enum
    allowed_statuses = fields.get("status", {}).get("enum", [])
    if allowed_statuses and claim.status not in allowed_statuses:
        return False, f"status '{claim.status}' not in allowed enum"

    # Check mechanism_status is in allowed enum
    allowed_mech_statuses = fields.get("mechanism_status", {}).get("enum", [])
    if allowed_mech_statuses and claim.mechanism_status not in allowed_mech_statuses:
        return False, f"mechanism_status '{claim.mechanism_status}' not in allowed enum"

    # Check failure_mode_source is in allowed enum
    allowed_fm_sources = fields.get("failure_mode_source", {}).get("enum", [])
    if allowed_fm_sources and claim.failure_mode_source not in allowed_fm_sources:
        return False, f"failure_mode_source '{claim.failure_mode_source}' not in allowed enum"

    # Check mechanism_evidence_rule (P0-7)
    mech_rule = contract.get("mechanism_evidence_rule", {})
    if claim.mechanism_status == "EXPLICIT":
        if len(claim.mechanism_evidence) == 0:
            return False, "mechanism_status=EXPLICIT requires mechanism_evidence"
    elif claim.mechanism_status == "UNKNOWN_NOT_STATED":
        if len(claim.mechanism_evidence) > 0:
            return False, "mechanism_status=UNKNOWN_NOT_STATED forbids mechanism_evidence"
    elif claim.mechanism_status == "UNKNOWN_NOT_RESOLVED":
        if claim.status == "EVIDENCE_BACKED":
            return False, "mechanism_status=UNKNOWN_NOT_RESOLVED cannot become EVIDENCE_BACKED"

    return True, "validated against contract"
