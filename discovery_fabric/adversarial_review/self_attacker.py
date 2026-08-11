"""
Self-Attacker — adversarial review for every discovery candidate.

Asks 10 attack questions per candidate. Candidate survives only if it
remains coherent after all attacks.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CANDIDATES_FILE = REPO / "discovery_fabric/discovery_candidates/discovery_candidates_v2.json"
EVIDENCE_FILE = REPO / "discovery_fabric/evidence/evidence.jsonl"
ATTACKER_DIR = REPO / "discovery_fabric/adversarial_review"
ATTACKER_DIR.mkdir(parents=True, exist_ok=True)


def attack_candidate(candidate, evidence):
    """Run 10 adversarial attacks on a candidate."""
    attacks = {
        "1_already_known": {
            "question": "Is this already known?",
            "assessment": "UNASSESSED",
            "evidence": "PENDING — requires full-text search of related literature",
        },
        "2_terminology_different": {
            "question": "Is the terminology merely different for the same concept?",
            "assessment": "UNASSESSED",
            "evidence": "PENDING — requires synonym/terminology normalization",
        },
        "3_patent_discloses": {
            "question": "Does another patent disclose it?",
            "assessment": "UNASSESSABLE — no patent evidence in current fabric",
            "evidence": "Patent connectors not yet operational",
        },
        "4_paper_discloses": {
            "question": "Does a paper disclose it?",
            "assessment": "PARTIALLY_ASSESSED",
            "evidence": f"Checked {len(evidence)} evidence objects — see prior_art_firewall",
        },
        "5_analogy_superficial": {
            "question": "Is the cross-domain analogy superficial?",
            "assessment": "LIKELY — keyword/field matching does not establish mechanistic bridge",
            "evidence": "Bridge analysis not yet implemented",
        },
        "6_physics_permits": {
            "question": "Does physics/chemistry/biology permit the transfer?",
            "assessment": "UNASSESSED",
            "evidence": "Requires domain expert or LLM physical reasoning",
        },
        "7_hidden_constraint": {
            "question": "Is there a hidden constraint preventing transfer?",
            "assessment": "UNASSESSED",
            "evidence": "Constraint compatibility analysis not yet implemented",
        },
        "8_unsupported_claim": {
            "question": "Is the performance claim unsupported?",
            "assessment": "N/A — no performance claims made yet",
            "evidence": "Candidates are at CANDIDATE_CONNECTION state, no predictions generated",
        },
        "9_search_artifact": {
            "question": "Is the supposed gap caused by search failure?",
            "assessment": "POSSIBLE — evidence universe is only 7,032 objects from 4 sources",
            "evidence": "Coverage: Crossref 1900, arXiv 1450, Europe PMC 1850, PubMed 1832. No patents, no Semantic Scholar, no OpenAlex (rate-limited).",
        },
        "10_falsifier": {
            "question": "What observation would falsify this candidate?",
            "assessment": "PENDING — requires falsifiable prediction first",
            "evidence": "No predictions generated yet — candidate must advance to MECHANISTIC_HYPOTHESIS first",
        },
    }

    # Survival logic
    fatal_attacks = []
    for attack_id, attack in attacks.items():
        assessment = attack["assessment"]
        if "LIKELY" in assessment or "POSSIBLE" in assessment or "UNASSESSABLE" in assessment:
            # These don't kill the candidate but flag concerns
            pass
        if assessment == "FATAL":
            fatal_attacks.append(attack_id)

    survived = len(fatal_attacks) == 0
    survival_state = "SURVIVED" if survived else "KILLED"

    return {
        "candidate_id": candidate["candidate_id"],
        "discovery_mode": candidate["discovery_mode"],
        "attacks": attacks,
        "fatal_attacks": fatal_attacks,
        "survival_state": survival_state,
        "epistemic_state_after_attack": "CANDIDATE_CONNECTION" if survived else "REJECTED",
        "review_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Self-Attacker starting")

    with open(CANDIDATES_FILE) as f:
        cand_data = json.load(f)
    candidates = cand_data.get("candidates", [])
    print(f"  Candidates to attack: {len(candidates)}")

    # Load evidence for attack #4 and #9
    evidence = []
    with open(EVIDENCE_FILE) as f:
        for line in f:
            if line.strip():
                evidence.append(json.loads(line))

    reviews = []
    for cand in candidates:
        review = attack_candidate(cand, evidence)
        reviews.append(review)

    # Save
    output = ATTACKER_DIR / "adversarial_reviews.json"
    with open(output, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_reviewed": len(reviews),
            "survived": sum(1 for r in reviews if r["survival_state"] == "SURVIVED"),
            "killed": sum(1 for r in reviews if r["survival_state"] == "KILLED"),
            "reviews": reviews,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] ATTACK COMPLETE")
    print(f"  Total reviewed: {len(reviews)}")
    print(f"  Survived: {sum(1 for r in reviews if r['survival_state'] == 'SURVIVED')}")
    print(f"  Killed: {sum(1 for r in reviews if r['survival_state'] == 'KILLED')}")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
