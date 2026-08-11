"""
Upgraded Self-Attacker V2 — actually attacks candidates.

Key improvements over V1:
1. BLIND — does not look at candidate_id, is_null_control, or generator metadata
2. Produces FATAL/MAJOR/MINOR/SURVIVES/UNASSESSED per attack
3. Does NOT convert UNASSESSED into SURVIVES
4. Uses LLM to evaluate scientific coherence of each candidate

Mixes real candidates and hard nulls for blind evaluation.
"""
import json
import sys
import subprocess
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CANDIDATES_FILE = REPO / "discovery_fabric/discovery_candidates/discovery_candidates_v2.json"
HARD_NULLS_FILE = REPO / "discovery_fabric/evaluation/hard_nulls_v2.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
ATTACKER_DIR = REPO / "discovery_fabric/adversarial_review"

UNKNOWN = "UNKNOWN"


def load_evidence_index():
    """Build evidence ID → evidence item lookup."""
    index = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                index[e["id"]] = e
    return index


def blind_attack(candidate, evidence_index):
    """Blindly attack a candidate using LLM. Does NOT look at candidate_id or metadata."""
    # Get evidence abstracts for the candidate
    abstracts = []
    for ev in candidate.get("evidence", []):
        eid = ev.get("evidence_id", "")
        e = evidence_index.get(eid, {})
        title = e.get("title", "")
        abstract = e.get("abstract", "")
        if abstract and abstract != "UNAVAILABLE":
            abstracts.append(f"Paper {eid}: {title[:100]}\n{abstract[:500]}")

    evidence_text = "\n\n".join(abstracts[:3]) if abstracts else "No abstracts available"

    hypothesis = candidate.get("candidate_hypothesis", "")
    bridge = candidate.get("bridge", "")

    attack_prompt = f"""You are a scientific adversary. Your job is to DESTROY this discovery candidate.

Candidate hypothesis: {hypothesis}

Proposed bridge: {bridge}

Source evidence:
{evidence_text}

Attack this candidate on these dimensions. For each, output a severity: FATAL, MAJOR, MINOR, SURVIVES, or UNASSESSED.

1. Is the mechanism already known?
2. Is the terminology merely different for the same concept?
3. Does the evidence actually support the bridge?
4. Is the cross-domain analogy superficial?
5. Does physics/chemistry/biology permit the transfer?
6. Is there a hidden constraint preventing transfer?
7. Is the proposed connection trivial/obvious?
8. Is the evidence insufficient to support the claim?
9. Is the bridge a semantic false analogy?
10. What observation would falsify this?

Output ONLY JSON:
{{"attacks": {{"1_known": "SEVERITY", "2_terminology": "SEVERITY", "3_evidence_support": "SEVERITY", "4_superficial": "SEVERITY", "5_physics": "SEVERITY", "6_constraint": "SEVERITY", "7_trivial": "SEVERITY", "8_insufficient": "SEVERITY", "9_false_analogy": "SEVERITY", "10_falsifier": "text"}}, "overall": "SURVIVES or KILLED", "reason": "..."}}"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        output_path = f.name

    try:
        result = subprocess.run(
            ["z-ai", "chat", "--prompt", attack_prompt, "--system", "You are a ruthless scientific adversary. Output only JSON."],
            capture_output=True, text=True, timeout=45
        )
        if result.returncode != 0:
            return {"overall": "UNASSESSED", "reason": "LLM call failed"}

        with open(output_path) as f:
            resp = json.load(f)

        content = resp["choices"][0]["message"]["content"].strip().strip("`").strip()
        if content.startswith("json"):
            content = content[4:].strip()

        attack_result = json.loads(content)
        return attack_result

    except Exception as e:
        return {"overall": "UNASSESSED", "reason": f"error: {type(e).__name__}: {str(e)[:80]}"}
    finally:
        Path(output_path).unlink(missing_ok=True)


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Blind Self-Attacker V2 starting")

    # Load real candidates and hard nulls
    with open(CANDIDATES_FILE) as f:
        real_cands = json.load(f).get("candidates", [])
    with open(HARD_NULLS_FILE) as f:
        hard_nulls = json.load(f).get("candidates", [])

    # MIX them — attacker doesn't know which is which
    all_candidates = real_cands + hard_nulls
    print(f"  Real candidates: {len(real_cands)}")
    print(f"  Hard nulls: {len(hard_nulls)}")
    print(f"  Total to attack (blind): {len(all_candidates)}")

    evidence_index = load_evidence_index()
    print(f"  Evidence index: {len(evidence_index)} items")

    reviews = []
    for i, cand in enumerate(all_candidates):
        # BLIND attack — do NOT read candidate_id or is_null_control
        review = blind_attack(cand, evidence_index)
        review["candidate_id"] = cand["candidate_id"]  # record ID but didn't use it for attack
        # Record whether it was a null (for analysis AFTER attack)
        review["_was_null"] = cand["candidate_id"].startswith("NULL-")
        reviews.append(review)

        if (i + 1) % 5 == 0:
            survived = sum(1 for r in reviews if r.get("overall") == "SURVIVES")
            killed = sum(1 for r in reviews if r.get("overall") == "KILLED")
            print(f"  [{i+1}/{len(all_candidates)}] survived={survived} killed={killed}")

    # Analysis
    real_reviews = [r for r in reviews if not r["_was_null"]]
    null_reviews = [r for r in reviews if r["_was_null"]]

    real_survived = sum(1 for r in real_reviews if r.get("overall") == "SURVIVES")
    null_survived = sum(1 for r in null_reviews if r.get("overall") == "SURVIVES")

    output = ATTACKER_DIR / "blind_adversarial_reviews_v2.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_attacked": len(reviews),
            "real_candidates": len(real_reviews),
            "hard_nulls": len(null_reviews),
            "real_survived": real_survived,
            "null_survived": null_survived,
            "reviews": reviews,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] BLIND ATTACK COMPLETE")
    print(f"  Real candidates: {len(real_reviews)} → {real_survived} survived ({100*real_survived/max(len(real_reviews),1):.0f}%)")
    print(f"  Hard nulls: {len(null_reviews)} → {null_survived} survived ({100*null_survived/max(len(null_reviews),1):.0f}%)")
    print(f"  Discovery signal: {real_survived}/{len(real_reviews)} real vs {null_survived}/{len(null_reviews)} null")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
