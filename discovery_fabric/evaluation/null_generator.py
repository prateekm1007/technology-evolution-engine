"""
Null Generator — control baseline for discovery engine.

Generates control candidates using:
- Random mechanism pairing
- Random domain pairing
- Lexical pairing without mechanism constraint

Runs the exact same adversarial pipeline. We need to know:
> Does the Discovery Engine produce more meaningful survivors than structured noise?
"""
import json
import sys
import hashlib
import random
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/structured_mechanisms_v2.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
NULL_DIR = REPO / "discovery_fabric/evaluation"
NULL_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)  # deterministic


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        return json.load(f).get("mechanisms", [])


def load_evidence():
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))
    return evidence


def generate_null_candidates(mechanisms, evidence, count=50):
    """Generate random pairing candidates as null baseline."""
    if len(mechanisms) < 2:
        return []

    null_candidates = []
    domains = list(set(e.get("domain", "?") for e in evidence))

    for i in range(count):
        # Random pair of mechanisms
        m1 = random.choice(mechanisms)
        m2 = random.choice(mechanisms)
        if m1["evidence_id"] == m2["evidence_id"]:
            continue

        # Random domain pair
        d1 = random.choice(domains)
        d2 = random.choice(domains)

        cand_id = f"NULL-{hashlib.sha256(f'null-{i}'.encode()).hexdigest()[:8]}"
        null_candidates.append({
            "candidate_id": cand_id,
            "discovery_mode": "null_random_pairing",
            "mechanism_a": {"evidence_id": m1["evidence_id"], "process": m1.get("PROCESS", "UNKNOWN")},
            "mechanism_b": {"evidence_id": m2["evidence_id"], "process": m2.get("PROCESS", "UNKNOWN")},
            "bridge": "NONE — randomly paired, no mechanistic basis",
            "constraints": "NONE — random",
            "evidence": [
                {"evidence_id": m1["evidence_id"], "source": "random"},
                {"evidence_id": m2["evidence_id"], "source": "random"},
            ],
            "candidate_hypothesis": f"Random pairing: {d1} ↔ {d2} (no mechanistic basis)",
            "epistemic_state": "NULL_CONTROL",
            "is_null_control": True,
        })

    return null_candidates


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Null Generator starting")

    mechanisms = load_mechanisms()
    evidence = load_evidence()
    print(f"  Mechanisms: {len(mechanisms)}")
    print(f"  Evidence: {len(evidence)}")

    null_candidates = generate_null_candidates(mechanisms, evidence, count=50)
    print(f"  Null candidates generated: {len(null_candidates)}")

    # Save
    output = NULL_DIR / "null_candidates.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generator": "null_random_pairing",
            "seed": 42,
            "total_null_candidates": len(null_candidates),
            "candidates": null_candidates,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output}")
    print(f"  These null candidates will be run through the same adversarial pipeline.")
    print(f"  Discovery engine signal = (real survivor rate) - (null survivor rate)")


if __name__ == "__main__":
    main()
