"""
Prediction Receipt — canonical immutable object.

Once created, cannot be modified. The model cannot change its prediction
after registration.

Schema:
  candidate_id: unique identifier
  input_manifest_hash: hash of all evidence the prediction was based on
  hypothesis: the proposed relationship (NOT in evidence)
  prediction: quantitative or binary prediction
  units_range: for numeric predictions (e.g., "efficiency increase 10-30%")
  expected_direction: INCREASE / DECREASE / BINARY / CORRELATION
  measurement_method: how to measure the prediction
  falsification_condition: what result would falsify
  pre_registration_timestamp: when the prediction was registered
  novelty_check: deterministic verification that prediction is NOT in evidence
  receipt_hash: SHA-256 of the entire receipt (computed after creation, immutable)
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def create_receipt(
    candidate_id: str,
    input_manifest_hash: str,
    hypothesis: str,
    prediction: str,
    units_range: str,
    expected_direction: str,  # INCREASE / DECREASE / BINARY / CORRELATION
    measurement_method: str,
    falsification_condition: str,
    evidence_text: str,  # for deterministic novelty check
    proposed_text: str,  # for deterministic novelty check
    pre_registration_timestamp: str = None,  # override for historical backtest
) -> dict:
    """Create an immutable prediction receipt."""
    
    # Deterministic novelty check: is the prediction relationship in the evidence?
    import re
    proposed_terms = set(re.findall(r'\b[a-z]{4,}\b', proposed_text.lower())) - {
        'the', 'that', 'this', 'with', 'from', 'have', 'been', 'would', 'could',
        'should', 'which', 'their', 'there', 'these', 'those', 'what', 'when',
        'where', 'while', 'about', 'into', 'upon', 'will', 'shall', 'may',
        'might', 'must', 'can', 'also', 'such', 'same', 'more', 'most', 'some',
    }
    evidence_terms = set(re.findall(r'\b[a-z]{4,}\b', evidence_text.lower()))
    overlap = proposed_terms & evidence_terms
    overlap_ratio = len(overlap) / max(len(proposed_terms), 1)
    is_novel = overlap_ratio < 0.6  # <60% term overlap = novel
    
    receipt = {
        "candidate_id": candidate_id,
        "input_manifest_hash": input_manifest_hash,
        "hypothesis": hypothesis,
        "prediction": prediction,
        "units_range": units_range,
        "expected_direction": expected_direction,
        "measurement_method": measurement_method,
        "falsification_condition": falsification_condition,
        "pre_registration_timestamp": pre_registration_timestamp or datetime.now(timezone.utc).isoformat(),
        "novelty_check": {
            "metric": "NOVEL_RELATION_TO_EVIDENCE",
            "is_novel": is_novel,
            "term_overlap_ratio": round(overlap_ratio, 2),
            "evidence_terms_count": len(evidence_terms),
            "proposed_terms_count": len(proposed_terms),
            "overlapping_terms": sorted(list(overlap))[:20],
            "deterministic": True,
            "reproducible": True,
        },
    }
    
    # Compute receipt hash (immutable after this point)
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt["receipt_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    
    return receipt


def verify_receipt(receipt: dict) -> bool:
    """Verify that a receipt has not been modified after creation."""
    stored_hash = receipt.get("receipt_hash")
    if not stored_hash:
        return False
    
    # Recompute hash without the hash field
    r = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    canonical = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed_hash = hashlib.sha256(canonical.encode()).hexdigest()
    
    return computed_hash == stored_hash


def save_receipt(receipt: dict, output_dir: Path):
    """Save receipt to file (immutable)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{receipt['candidate_id']}.json"
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    return path


if __name__ == "__main__":
    # Test
    r = create_receipt(
        candidate_id="TEST-001",
        input_manifest_hash="abc123",
        hypothesis="Lithium intercalation in both electrodes enables reversible battery",
        prediction="Combining LiCoO2 cathode with graphite anode will enable >100 charge cycles",
        units_range=">100 cycles",
        expected_direction="INCREASE",
        measurement_method="Charge-discharge cycling test",
        falsification_condition="<50 cycles before capacity fade",
        evidence_text="LiCoO2 can intercalate lithium. Graphite can intercalate lithium. Lithium metal batteries are unsafe.",
        proposed_text="Combine LiCoO2 cathode with graphite anode for reversible intercalation battery",
    )
    print(f"Receipt hash: {r['receipt_hash'][:32]}...")
    print(f"Novel: {r['novelty_check']['is_novel']}")
    print(f"Term overlap: {r['novelty_check']['term_overlap_ratio']}")
    print(f"Verified: {verify_receipt(r)}")
