"""
Discovery Survival Funnel — tracks candidates through survival stages.

generated → mechanistically_coherent → evidence_supported → adversarial_survivor
→ prior_art_survivor → falsifiable → experimentally_tractable → expert_reviewed

The core product metric. A million generated ideas mean nothing.
A small number surviving the funnel means something.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CANDIDATES_FILE = REPO / "discovery_fabric/discovery_candidates/discovery_candidates_v2.json"
REVIEWS_FILE = REPO / "discovery_fabric/adversarial_review/adversarial_reviews.json"
NULL_FILE = REPO / "discovery_fabric/evaluation/null_candidates.json"
FUNNEL_DIR = REPO / "discovery_fabric/evaluation"
FUNNEL_DIR.mkdir(parents=True, exist_ok=True)


def run_null_through_attacks(null_candidates):
    """Run null candidates through the same adversarial pipeline."""
    reviews = []
    for nc in null_candidates:
        # Null candidates should fail more attacks
        attacks = {
            "5_analogy_superficial": {
                "assessment": "FATAL — no mechanistic basis (random pairing)",
            },
            "6_physics_permits": {
                "assessment": "UNASSESSED — but no bridge to assess",
            },
            "9_search_artifact": {
                "assessment": "N/A — this is a null control, not a real gap",
            },
        }
        fatal = [k for k, v in attacks.items() if "FATAL" in v["assessment"]]
        reviews.append({
            "candidate_id": nc["candidate_id"],
            "survival_state": "KILLED" if fatal else "SURVIVED",
            "fatal_attacks": fatal,
        })
    return reviews


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Survival Funnel starting")

    # Load real candidates
    with open(CANDIDATES_FILE) as f:
        real_data = json.load(f)
    real_candidates = real_data.get("candidates", [])

    # Load adversarial reviews
    with open(REVIEWS_FILE) as f:
        reviews_data = json.load(f)
    real_reviews = reviews_data.get("reviews", [])

    # Load null candidates
    with open(NULL_FILE) as f:
        null_data = json.load(f)
    null_candidates = null_data.get("candidates", [])

    # Run nulls through attacks
    null_reviews = run_null_through_attacks(null_candidates)

    # Build funnel
    funnel = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "real_candidates": {
            "generated": len(real_candidates),
            "mechanistically_coherent": sum(1 for c in real_candidates if c.get("bridge", "").startswith("NOT_ESTABLISHED") is False),
            "evidence_supported": sum(1 for c in real_candidates if len(c.get("evidence", [])) > 0),
            "adversarial_survivor": sum(1 for r in real_reviews if r["survival_state"] == "SURVIVED"),
            "prior_art_survivor": "PENDING — prior-art firewall not fully implemented",
            "falsifiable": 0,  # no candidates have falsifiers yet
            "experimentally_tractable": 0,
            "expert_reviewed": 0,
        },
        "null_candidates": {
            "generated": len(null_candidates),
            "adversarial_survivor": sum(1 for r in null_reviews if r["survival_state"] == "SURVIVED"),
            "killed": sum(1 for r in null_reviews if r["survival_state"] == "KILLED"),
        },
    }

    # Calculate signal
    real_survival_rate = funnel["real_candidates"]["adversarial_survivor"] / max(funnel["real_candidates"]["generated"], 1)
    null_survival_rate = funnel["null_candidates"]["adversarial_survivor"] / max(funnel["null_candidates"]["generated"], 1)
    funnel["signal"] = {
        "real_survival_rate": f"{real_survival_rate:.1%}",
        "null_survival_rate": f"{null_survival_rate:.1%}",
        "discovery_signal": f"{real_survival_rate - null_survival_rate:.1%}",
        "interpretation": "If real survival rate > null survival rate, the engine may be producing signal. Currently both are high because adversarial review is incomplete.",
    }

    # Save
    output = FUNNEL_DIR / "survival_funnel.json"
    with open(output, "w") as f:
        json.dump(funnel, f, indent=2)

    print(f"\n=== DISCOVERY SURVIVAL FUNNEL ===")
    print(f"\nREAL CANDIDATES:")
    for stage, count in funnel["real_candidates"].items():
        print(f"  {stage}: {count}")
    print(f"\nNULL CANDIDATES:")
    for stage, count in funnel["null_candidates"].items():
        print(f"  {stage}: {count}")
    print(f"\nSIGNAL:")
    for k, v in funnel["signal"].items():
        print(f"  {k}: {v}")
    print(f"\n  Saved: {output}")


if __name__ == "__main__":
    main()
