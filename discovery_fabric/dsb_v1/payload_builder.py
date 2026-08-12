"""
DSB V1 — Payload Builder
=========================

Builds the BLIND payload the generator receives. The payload contains ONLY:
  - exposed_facts (as an unordered bullet list)
  - a neutral instruction (no domain hint, no name hint, no year hint)

The payload NEVER contains:
  - case_id
  - name_internal
  - breakthrough_relationship
  - withheld_facts
  - forbidden_terms
  - future_terminology
  - answer_mechanism
  - constraint_release
  - historical_source
  - cutoff_date (the generator is told "current state of knowledge", not a year)

The payload is hash-sealed so any modification after building is detectable.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.case_schema import load_case


PAYLOAD_SCHEMA_VERSION = "1.0.0"


def build_payload(case: dict, arm: str) -> dict:
    """Build the blind payload for one (case, arm) pair.

    Args:
        case: case dict (with exposed_facts, withheld_facts, etc.)
        arm: one of "LLM_only", "mechanism_only", "combination", "full_system"

    Returns:
        Sealed payload dict with:
          - payload_id
          - arm
          - exposed_facts (shuffled deterministically by sorted() to remove any order cue)
          - instruction (arm-specific, neutral)
          - payload_hash (SHA-256 of canonical form)
    """
    # Sort exposed_facts alphabetically to remove any "the most important fact is first" cue
    exposed_sorted = sorted(case["exposed_facts"])

    arm_instructions = {
        "LLM_only": (
            "You are a scientific analyst. Below is the current state of knowledge on a topic.\n"
            "Based ONLY on the facts below, propose ONE specific scientific relationship or combination "
            "that is NOT explicitly stated but follows from combining these facts.\n\n"
            "Output JSON:\n"
            '{"proposed_relationship": "one sentence", "mechanism": "one paragraph", '
            '"constraint_released": "one sentence", "predicted_quantitative_outcome": "value with units"}'
        ),
        "mechanism_only": (
            "You are a scientific analyst. Below is the current state of knowledge on a topic.\n"
            "Identify the CORE MECHANISM shared across the facts below. Then propose ONE specific "
            "scientific relationship that combines this mechanism with one of the facts in a way "
            "NOT explicitly stated.\n\n"
            "Output JSON:\n"
            '{"proposed_relationship": "one sentence", "mechanism": "one paragraph", '
            '"constraint_released": "one sentence", "predicted_quantitative_outcome": "value with units"}'
        ),
        "combination": (
            "You are a scientific analyst. Below is the current state of knowledge on a topic.\n"
            "Identify TWO facts below that could be COMBINED to produce a novel capability or "
            "outcome not explicit in the input. Describe the combination and its consequence.\n\n"
            "Output JSON:\n"
            '{"proposed_relationship": "one sentence combining two facts", "mechanism": "one paragraph", '
            '"constraint_released": "one sentence", "predicted_quantitative_outcome": "value with units"}'
        ),
        "full_system": (
            "You are a scientific analyst. Below is the current state of knowledge on a topic.\n"
            "Identify (a) invariant principles, (b) operational constraints, and (c) mechanism "
            "interactions across the facts below. Then propose ONE specific scientific relationship "
            "that releases a constraint by combining the facts in a way NOT explicitly stated.\n\n"
            "Output JSON:\n"
            '{"proposed_relationship": "one sentence", "mechanism": "one paragraph", '
            '"constraint_released": "one sentence", "predicted_quantitative_outcome": "value with units"}'
        ),
    }

    if arm not in arm_instructions:
        raise ValueError(f"unknown arm: {arm}")

    payload = {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "payload_id": f"PAYLOAD-{case['case_id']}-{arm}",
        "arm": arm,
        "case_id": case["case_id"],  # internal — used for bookkeeping but NOT shown to generator
        "exposed_facts": exposed_sorted,
        "instruction": arm_instructions[arm],
        "built_at": datetime.now(timezone.utc).isoformat(),
    }

    # Seal the payload
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["payload_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload


def build_payload_text(payload: dict) -> str:
    """Build the actual text prompt sent to the LLM.

    This is the ONLY part the generator sees. It does NOT include case_id,
    payload_hash, built_at, or any other metadata.
    """
    facts_block = "\n".join(f"- {f}" for f in payload["exposed_facts"])
    return f"CURRENT STATE OF KNOWLEDGE:\n{facts_block}\n\n---\n\n{payload['instruction']}"


def verify_payload(payload: dict) -> bool:
    """Verify that a payload's hash matches its contents."""
    stored = payload.get("payload_hash")
    if not stored:
        return False
    p = {k: v for k, v in payload.items() if k != "payload_hash"}
    canonical = json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed = hashlib.sha256(canonical.encode()).hexdigest()
    return computed == stored


def main():
    """Build payloads for all cases × all arms and verify."""
    REPO = Path(__file__).resolve().parents[2]
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"
    arms = ["LLM_only", "mechanism_only", "combination", "full_system"]

    n_total = 0
    n_verified = 0
    for d in [real_dir, fab_dir]:
        for case_path in sorted(d.glob("DSB-*.json")):
            case = load_case(case_path)
            for arm in arms:
                payload = build_payload(case, arm)
                n_total += 1
                if verify_payload(payload):
                    n_verified += 1

    print(f"Built {n_total} payloads ({n_verified} verified)")
    print(f"  20 cases × 4 arms = 80 payloads expected")

    # Show one sample payload text
    sample_case = load_case(sorted(real_dir.glob("DSB-R-001.json"))[0])
    sample_payload = build_payload(sample_case, "LLM_only")
    print(f"\nSample payload text for {sample_payload['payload_id']}:")
    print("=" * 60)
    print(build_payload_text(sample_payload))
    print("=" * 60)


if __name__ == "__main__":
    main()
