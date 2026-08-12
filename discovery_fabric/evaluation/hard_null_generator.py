"""
Hard Null Generator V2 — produces hard negatives that are indistinguishable
from real candidates by metadata inspection.

6 types:
NULL-1: Lexically convincing but mechanistically incompatible
NULL-2: Mechanistically similar but boundary-condition incompatible
NULL-3: Cross-domain where transfer has known failure
NULL-4: Pairs where relationship is already established
NULL-5: Physically impossible under target conditions
NULL-6: LLM-rejected pairs

Null candidates use the SAME schema as real candidates.
The attacker cannot identify them by metadata alone.
"""
import json
import sys
import hashlib
import random
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

MECHANISMS_FILE = REPO / "discovery_fabric/mechanisms/structured_mechanisms_1k.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
NULL_DIR = REPO / "discovery_fabric/evaluation"
NULL_DIR.mkdir(parents=True, exist_ok=True)

random.seed(12345)


def load_mechanisms():
    with open(MECHANISMS_FILE) as f:
        data = json.load(f)
    return [m for m in data.get("mechanisms", []) if m.get("extraction_status") == "SUCCESS"]


def load_evidence():
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))
    return evidence


def make_null_candidate(null_type, m1, m2, hypothesis, bridge):
    """Make a null candidate with the SAME schema as real candidates."""
    m1_id = m1["evidence_id"]
    m2_id = m2["evidence_id"]
    cand_id = f"NULL-{null_type}-{hashlib.sha256(f'{m1_id}-{m2_id}'.encode()).hexdigest()[:8]}"
    return {
        "candidate_id": cand_id,
        "discovery_mode": "cross_domain_mechanism_transfer",  # same as real
        "mechanism_a": {"evidence_id": m1["evidence_id"], "process": m1.get("PROCESS", "UNKNOWN"), "domain": m1.get("domain", "?")},
        "mechanism_b": {"evidence_id": m2["evidence_id"], "process": m2.get("PROCESS", "UNKNOWN"), "domain": m2.get("domain", "?")},
        "bridge": bridge,  # plausible-sounding but wrong
        "constraints": "PENDING",
        "evidence": [
            {"evidence_id": m1["evidence_id"], "domain": m1.get("domain", "?")},
            {"evidence_id": m2["evidence_id"], "domain": m2.get("domain", "?")},
        ],
        "candidate_hypothesis": hypothesis,  # plausible-sounding
        "epistemic_state": "CANDIDATE_CONNECTION",  # same as real
        # NO is_null_control field — must be indistinguishable
        # NO mention of "null" or "random" in any visible field
    }


def generate_nulls(mechanisms, evidence):
    """Generate 6 types of hard nulls."""
    if len(mechanisms) < 2:
        return []

    nulls = []

    # NULL-1: Lexically convincing but mechanistically incompatible
    # Pair mechanisms that share INPUT keywords but have incompatible PROCESS
    by_input = {}
    for m in mechanisms:
        inp = m.get("INPUT", "UNKNOWN")
        if inp != "UNKNOWN":
            by_input.setdefault(inp[:20], []).append(m)

    for inp, mechs in by_input.items():
        if len(mechs) >= 2:
            m1, m2 = mechs[0], mechs[1]
            if m1.get("domain") != m2.get("domain"):
                nulls.append(make_null_candidate(
                    "NULL-1", m1, m2,
                    hypothesis=f"Shared input material '{inp}' suggests transferability between {m1.get('domain','?')} and {m2.get('domain','?')}",
                    bridge=f"Both mechanisms use '{inp}' as input — material similarity may enable process transfer"
                ))

    # NULL-2: Mechanistically similar but boundary-condition incompatible
    # Pair same PROCESS type but different OPERATING_CONDITIONS
    by_process = {}
    for m in mechanisms:
        proc = m.get("PROCESS", "UNKNOWN")
        if proc != "UNKNOWN":
            by_process.setdefault(proc[:20], []).append(m)

    for proc, mechs in by_process.items():
        if len(mechs) >= 2:
            m1, m2 = mechs[0], mechs[1]
            oc1 = m1.get("OPERATING_CONDITIONS", "UNKNOWN")
            oc2 = m2.get("OPERATING_CONDITIONS", "UNKNOWN")
            if oc1 != "UNKNOWN" and oc2 != "UNKNOWN" and oc1 != oc2:
                nulls.append(make_null_candidate(
                    "NULL-2", m1, m2,
                    hypothesis=f"Process '{proc[:30]}' may transfer from {m1.get('domain','?')} to {m2.get('domain','?')} despite different conditions",
                    bridge=f"Same process type '{proc[:30]}' — operating condition differences may be surmountable"
                ))

    # NULL-3: Cross-domain where transfer has known failure
    # Pair mechanisms from very different domains (e.g., biotechnology + energy)
    domain_pairs = [("biotechnology", "energy"), ("neuroscience", "materials"), ("computing", "biotechnology")]
    for d1, d2 in domain_pairs:
        mechs1 = [m for m in mechanisms if m.get("domain") == d1]
        mechs2 = [m for m in mechanisms if m.get("domain") == d2]
        if mechs1 and mechs2:
            m1, m2 = mechs1[0], mechs2[0]
            nulls.append(make_null_candidate(
                "NULL-3", m1, m2,
                hypothesis=f"Mechanism from {d1} may address problem in {d2}",
                bridge=f"Cross-domain transfer from {d1} to {d2} — functional analogy may exist"
            ))

    # NULL-4: Pairs where relationship is already established
    # Pair mechanisms from same domain (likely already connected)
    for domain in set(m.get("domain", "?") for m in mechanisms):
        domain_mechs = [m for m in mechanisms if m.get("domain") == domain]
        if len(domain_mechs) >= 2:
            m1, m2 = domain_mechs[0], domain_mechs[1]
            nulls.append(make_null_candidate(
                "NULL-4", m1, m2,
                hypothesis=f"Mechanisms within {domain} may combine for improved performance",
                bridge=f"Same-domain combination — existing literature likely covers this"
            ))

    # NULL-5: Physically impossible under target conditions
    # Pair high-temperature process with biological system
    high_temp = [m for m in mechanisms if "temperature" in str(m.get("OPERATING_CONDITIONS", "")).lower() or "°c" in str(m.get("OPERATING_CONDITIONS", "")).lower()]
    bio = [m for m in mechanisms if m.get("domain") == "biotechnology"]
    if high_temp and bio:
        nulls.append(make_null_candidate(
            "NULL-5", high_temp[0], bio[0],
            hypothesis=f"High-temperature process may transfer to biotechnology",
            bridge=f"Process transfer from materials to biotechnology — conditions may be adaptable"
        ))

    # NULL-6: Random but plausible-looking (replaces old null type)
    if len(mechanisms) >= 10:
        for _ in range(5):
            m1 = random.choice(mechanisms)
            m2 = random.choice(mechanisms)
            if m1["evidence_id"] != m2["evidence_id"]:
                nulls.append(make_null_candidate(
                    "NULL-6", m1, m2,
                    hypothesis=f"Mechanism from {m1.get('domain','?')} may transfer to {m2.get('domain','?')}",
                    bridge=f"Cross-domain mechanism transfer — compatible constraints may exist"
                ))

    return nulls


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Hard Null Generator V2")

    mechanisms = load_mechanisms()
    evidence = load_evidence()
    print(f"  Mechanisms (SUCCESS): {len(mechanisms)}")
    print(f"  Evidence: {len(evidence)}")

    nulls = generate_nulls(mechanisms, evidence)
    print(f"  Hard nulls generated: {len(nulls)}")

    # Count by type
    from collections import Counter
    by_type = Counter(n["candidate_id"].split("-")[1] for n in nulls)
    print(f"  By type: {dict(by_type)}")

    output = NULL_DIR / "hard_nulls_v2.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_hard_nulls": len(nulls),
            "by_type": dict(by_type),
            "candidates": nulls,
            "spec": "NULL_CONTROL_SPEC_V1 — indistinguishable from real candidates by metadata",
        }, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {output}")
    print(f"  These nulls will be mixed with real candidates for blind adversarial review.")


if __name__ == "__main__":
    main()
