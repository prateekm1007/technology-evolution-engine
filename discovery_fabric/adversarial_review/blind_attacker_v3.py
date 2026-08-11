"""
Blind Attacker V3 — uses OpenRouter LLM for real adversarial evaluation.

BLIND: does not read candidate_id or metadata.
Produces FATAL/MAJOR/MINOR/SURVIVES/UNASSESSED per attack.
Does NOT convert UNASSESSED into SURVIVES.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

CANDIDATES_FILE = REPO / "discovery_fabric/discovery_candidates/discovery_candidates_v3.json"
HARD_NULLS_FILE = REPO / "discovery_fabric/evaluation/hard_nulls_v2.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
ATTACKER_DIR = REPO / "discovery_fabric/adversarial_review"

UNKNOWN = "UNKNOWN"

ATTACK_SYSTEM = """You are a ruthless scientific adversary. Your job is to DESTROY discovery candidates. Be skeptical. Find weaknesses. Only let a candidate survive if it is genuinely robust.

For each attack dimension, output a severity:
- FATAL: The candidate is dead — this attack alone kills it
- MAJOR: Serious problem that significantly weakens the candidate
- MINOR: Minor concern worth noting
- SURVIVES: The candidate withstands this attack
- UNASSESSED: Cannot evaluate with available information

Output ONLY valid JSON, no markdown."""

ATTACK_PROMPT_TEMPLATE = """Candidate hypothesis: {hypothesis}

Proposed bridge: {bridge}

Source evidence:
{evidence_text}

Attack this candidate on these 10 dimensions. For each, output a severity (FATAL/MAJOR/MINOR/SURVIVES/UNASSESSED) and a brief reason.

1. Is the mechanism already known in the literature?
2. Is the terminology merely different for the same concept?
3. Does the evidence actually support the proposed bridge?
4. Is the cross-domain analogy superficial (keyword matching, not mechanistic)?
5. Does physics/chemistry/biology permit the transfer?
6. Is there a hidden constraint preventing transfer?
7. Is the proposed connection trivial or obvious?
8. Is the evidence insufficient to support the claim?
9. Is the bridge a semantic false analogy?
10. What specific observation would falsify this candidate?

Output JSON:
{{"attacks": {{
  "1_known": {{"severity": "...", "reason": "..."}},
  "2_terminology": {{"severity": "...", "reason": "..."}},
  "3_evidence_support": {{"severity": "...", "reason": "..."}},
  "4_superficial": {{"severity": "...", "reason": "..."}},
  "5_physics": {{"severity": "...", "reason": "..."}},
  "6_constraint": {{"severity": "...", "reason": "..."}},
  "7_trivial": {{"severity": "...", "reason": "..."}},
  "8_insufficient": {{"severity": "...", "reason": "..."}},
  "9_false_analogy": {{"severity": "...", "reason": "..."}},
  "10_falsifier": {{"severity": "...", "reason": "..."}}
}},
"overall": "SURVIVES or KILLED",
"fatal_attacks": ["list of attack IDs that are FATAL"],
"reason": "overall reasoning"
}}"""


def load_evidence_index():
    index = {}
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                index[e["id"]] = e
    return index


def blind_attack(candidate, evidence_index):
    """Blindly attack a candidate. Does NOT look at candidate_id or metadata."""
    # Get evidence abstracts
    abstracts = []
    for ev in candidate.get("evidence", []):
        eid = ev.get("evidence_id", "")
        e = evidence_index.get(eid, {})
        title = e.get("title", "")
        abstract = e.get("abstract", "")
        if abstract and abstract != "UNAVAILABLE":
            abstracts.append(f"Paper {eid}: {title[:100]}\n{abstract[:400]}")
        else:
            abstracts.append(f"Paper {eid}: {title[:100]}")

    evidence_text = "\n\n".join(abstracts[:3]) if abstracts else "No evidence abstracts available"
    hypothesis = candidate.get("candidate_hypothesis", "")
    bridge = candidate.get("bridge", "")

    prompt = ATTACK_PROMPT_TEMPLATE.format(
        hypothesis=hypothesis,
        bridge=bridge,
        evidence_text=evidence_text,
    )

    result = chat_json(prompt, system=ATTACK_SYSTEM, max_tokens=800)
    if not result:
        return {"overall": "UNASSESSED", "reason": "LLM call failed", "fatal_attacks": []}

    return result


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Blind Attacker V3 (OpenRouter)")

    with open(CANDIDATES_FILE) as f:
        real_cands = json.load(f).get("candidates", [])
    with open(HARD_NULLS_FILE) as f:
        hard_nulls = json.load(f).get("candidates", [])

    # MIX real + nulls (blind — attacker doesn't know which is which)
    all_candidates = real_cands + hard_nulls
    print(f"  Real candidates: {len(real_cands)}")
    print(f"  Hard nulls: {len(hard_nulls)}")
    print(f"  Total to attack (blind): {len(all_candidates)}")

    evidence_index = load_evidence_index()
    print(f"  Evidence index: {len(evidence_index)}")

    reviews = []
    for i, cand in enumerate(all_candidates):
        review = blind_attack(cand, evidence_index)
        # Record ID and null status AFTER attack (for analysis only)
        review["candidate_id"] = cand["candidate_id"]
        review["_was_null"] = cand["candidate_id"].startswith("NULL-")
        reviews.append(review)

        if (i + 1) % 5 == 0:
            survived = sum(1 for r in reviews if r.get("overall") == "SURVIVES")
            killed = sum(1 for r in reviews if r.get("overall") == "KILLED")
            unassessed = sum(1 for r in reviews if r.get("overall") == "UNASSESSED")
            print(f"  [{i+1}/{len(all_candidates)}] survived={survived} killed={killed} unassessed={unassessed}")

        time.sleep(1)  # rate limit

    # Analysis
    real_reviews = [r for r in reviews if not r["_was_null"]]
    null_reviews = [r for r in reviews if r["_was_null"]]

    real_survived = sum(1 for r in real_reviews if r.get("overall") == "SURVIVES")
    real_killed = sum(1 for r in real_reviews if r.get("overall") == "KILLED")
    null_survived = sum(1 for r in null_reviews if r.get("overall") == "SURVIVES")
    null_killed = sum(1 for r in null_reviews if r.get("overall") == "KILLED")

    output = ATTACKER_DIR / "blind_attacks_v3.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_backend": "openrouter/gemma-4-26b-a4b-it:free",
            "total_attacked": len(reviews),
            "real_candidates": len(real_reviews),
            "hard_nulls": len(null_reviews),
            "real_survived": real_survived,
            "real_killed": real_killed,
            "null_survived": null_survived,
            "null_killed": null_killed,
            "reviews": reviews,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] BLIND ATTACK COMPLETE")
    print(f"  Real: {len(real_reviews)} → {real_survived} survived, {real_killed} killed")
    print(f"  Nulls: {len(null_reviews)} → {null_survived} survived, {null_killed} killed")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
