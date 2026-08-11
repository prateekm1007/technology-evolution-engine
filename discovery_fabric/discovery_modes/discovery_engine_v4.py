"""
Discovery Engine V4 — Constraint-Aware Generation Pipeline.

New pipeline:
  mechanism extraction → constraint extraction → mechanism transfer test
  → prediction generation → self-attack → ONLY THEN candidate

A candidate only exists if it contains:
  - Source mechanism
  - Target domain
  - Transferred principle
  - Required conditions
  - Expected measurable effect
  - Failure condition
"""
import json
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/extraction_checkpoint_v4.json"
CONSTRAINTS_FILE = REPO / "discovery_fabric/mechanisms/constraints_v4.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
CANDIDATES_DIR = REPO / "discovery_fabric/discovery_candidates"

UNKNOWN = "UNKNOWN"

TRANSFER_SYSTEM = """You are a mechanism transfer evaluator for a scientific discovery engine.

Given:
- Source mechanism (from domain A) with its constraints
- Target domain B

Your job: Determine if the mechanism can genuinely transfer, and if so, produce a falsifiable prediction.

CRITICAL RULES:
1. Only propose transfer if constraints are COMPATIBLE.
2. If energy/timescale/temperature/pressure/material requirements conflict, REJECT.
3. Every prediction must be MEASURABLE and FALSIFIABLE.
4. If you cannot produce a falsifiable prediction, REJECT.
5. Do NOT propose superficial analogies based on word similarity.

Output JSON:
{
  "transfer_possible": true/false,
  "transfer_reason": "why constraints are compatible or not",
  "source_mechanism": "brief description",
  "target_domain": "domain B",
  "transferred_principle": "what specifically transfers",
  "required_conditions": "what conditions are needed in target",
  "expected_measurable_effect": "specific measurable prediction",
  "measurement_method": "how to measure it",
  "falsification_condition": "what result would falsify this",
  "failure_condition": "when would this not work",
  "constraint_conflicts": ["list of any constraint conflicts"],
  "quality_assessment": "STRONG/MODERATE/WEAK/REJECT"
}

If transfer is not possible, set transfer_possible=false and explain why."""


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        data = json.load(f)
    return [m for m in data.get("mechanisms", []) if m.get("extraction_status") == "SUCCESS"]


def load_constraints():
    with open(CONSTRAINTS_FILE) as f:
        data = json.load(f)
    # Index by evidence_id
    return {c["evidence_id"]: c for c in data.get("constraints", []) if "extraction_status" not in c}


def load_evidence():
    evidence = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                evidence[e["id"]] = e
    return evidence


def find_transfer_candidates(mechanisms, constraints, evidence):
    """Find mechanism pairs across domains that might transfer."""
    # Group by domain
    by_domain = {}
    for m in mechanisms:
        domain = m.get("domain", "?")
        eid = m.get("evidence_id", "")
        if eid in constraints:
            by_domain.setdefault(domain, []).append((m, constraints[eid]))

    # For each pair of domains, try one transfer
    candidates = []
    domains = list(by_domain.keys())

    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            if not by_domain[d1] or not by_domain[d2]:
                continue
            m1, c1 = by_domain[d1][0]
            m2, _ = by_domain[d2][0]

            # Build mechanism + constraint summary
            mech_summary = "\n".join(f"  {f}: {m1.get(f, UNKNOWN)}" for f in [
                "OBJECTIVE", "INPUT", "PROCESS", "OUTPUT", "MEASURED_EFFECT"
            ])
            constraint_summary = "\n".join(f"  {f}: {c1.get(f, UNKNOWN)}" for f in [
                "ENERGY_SOURCE", "TIMESCALE", "TEMPERATURE", "PRESSURE",
                "MATERIAL_REQUIREMENTS", "BIOLOGICAL_REQUIREMENTS", "KNOWN_LIMITATIONS"
            ])

            prompt = f"""Source mechanism (from domain {d1}):
{mech_summary}

Source constraints:
{constraint_summary}

Target domain: {d2}

Evaluate whether this mechanism can transfer to {d2}. Output the transfer evaluation JSON."""

            result = chat_json(prompt, system=TRANSFER_SYSTEM, max_tokens=800)

            if result and result.get("transfer_possible") and result.get("quality_assessment") != "REJECT":
                cand_id = f"V4-{hashlib.sha256(f'{m1['evidence_id']}-{d2}'.encode()).hexdigest()[:8]}"
                candidates.append({
                    "candidate_id": cand_id,
                    "source_evidence_id": m1["evidence_id"],
                    "source_domain": d1,
                    "target_domain": d2,
                    "source_mechanism": result.get("source_mechanism", UNKNOWN),
                    "transferred_principle": result.get("transferred_principle", UNKNOWN),
                    "required_conditions": result.get("required_conditions", UNKNOWN),
                    "expected_measurable_effect": result.get("expected_measurable_effect", UNKNOWN),
                    "measurement_method": result.get("measurement_method", UNKNOWN),
                    "falsification_condition": result.get("falsification_condition", UNKNOWN),
                    "failure_condition": result.get("failure_condition", UNKNOWN),
                    "constraint_conflicts": result.get("constraint_conflicts", []),
                    "quality_assessment": result.get("quality_assessment", UNKNOWN),
                    "transfer_reason": result.get("transfer_reason", UNKNOWN),
                    "epistemic_state": "MECHANISTIC_HYPOTHESIS",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                })
                print(f"  {d1}→{d2}: {result.get('quality_assessment','?')} — {result.get('expected_measurable_effect','')[:60]}")
            else:
                quality = result.get("quality_assessment", "FAILED") if result else "FAILED"
                reason = result.get("transfer_reason", "LLM failed")[:60] if result else "LLM failed"
                print(f"  {d1}→{d2}: {quality} — {reason}")

            time.sleep(1)

    return candidates


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery Engine V4 — Constraint-Aware Pipeline")

    mechanisms = load_mechanisms()
    constraints = load_constraints()
    evidence = load_evidence()
    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Constraints: {len(constraints)}")

    print("\n  Running constraint-aware transfer evaluation...")
    candidates = find_transfer_candidates(mechanisms, constraints, evidence)

    # Save
    output = CANDIDATES_DIR / "discovery_candidates_v4.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline": "constraint_aware_v4",
            "total_candidates": len(candidates),
            "candidates": candidates,
        }, f, indent=2, ensure_ascii=False)

    by_quality = Counter(c.get("quality_assessment", "?") for c in candidates)
    print(f"\n[{datetime.now(timezone.utc).isoformat()}] COMPLETE")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  By quality: {dict(by_quality)}")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
