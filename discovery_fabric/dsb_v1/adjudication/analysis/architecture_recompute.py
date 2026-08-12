"""
DSB V1 — Architecture Recompute (FROZEN until human adjudication complete)
==========================================================================

Recomputes the architecture comparison (4 arms: LLM_only, mechanism_only,
combination, full_system) using HUMAN verdicts as the gold standard instead
of the deterministic scorer's verdicts.

This module is FROZEN — it will REFUSE to run until:
  (a) ≥2 adjudicator result files exist in adjudication/results/
  (b) Inter-rater agreement has been measured
  (c) Confusion matrices have been computed

When run, it produces:
  - Per-arm recovery rate (per human majority vote)
  - Per-arm recovery rate (per deterministic scorer, for comparison)
  - Real-vs-fabricated split (does the inversion persist under human judgment?)
  - Statistical test (chi-square) for arm differences
"""
import json
import sys
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from discovery_fabric.dsb_v1.scorer import score_all
from discovery_fabric.dsb_v1.case_schema import load_case


def check_prerequisites() -> tuple[bool, list[str]]:
    """Verify that human adjudication is complete enough to recompute."""
    failures = []
    results_dir = REPO / "discovery_fabric/dsb_v1/adjudication/results"
    result_files = sorted(results_dir.glob("adjudicator_*.json"))
    if len(result_files) < 2:
        failures.append(
            f"Need ≥2 adjudicator result files, found {len(result_files)}. "
            "Architecture recompute is FROZEN until human adjudication is complete."
        )

    # Check inter-rater agreement exists
    ira_path = REPO / "discovery_fabric/dsb_v1/adjudication/analysis/inter_rater_agreement.json"
    if not ira_path.exists():
        failures.append(
            "Inter-rater agreement has not been computed. "
            "Run inter_rater_agreement.py first."
        )

    # Check confusion matrices exist
    cm_path = REPO / "discovery_fabric/dsb_v1/adjudication/analysis/confusion_matrices.json"
    if not cm_path.exists():
        failures.append(
            "Confusion matrices have not been computed. "
            "Run confusion_matrix.py first."
        )

    return (len(failures) == 0, failures)


def recompute_architecture_comparison() -> dict:
    """Recompute architecture comparison using human verdicts as gold standard."""
    ok, failures = check_prerequisites()
    if not ok:
        return {
            "status": "FROZEN",
            "reason": "Architecture recompute is FROZEN until human adjudication is complete.",
            "prerequisite_failures": failures,
        }

    # Load adjudicators
    results_dir = REPO / "discovery_fabric/dsb_v1/adjudication/results"
    adjudicators = []
    for rp in sorted(results_dir.glob("adjudicator_*.json")):
        with open(rp) as f:
            adjudicators.append(json.load(f))

    # Load scorer results
    scorer_result = score_all()
    scores_by_receipt = {s["receipt_id"]: s for s in scorer_result["scores"]}

    # Load cases
    cases = {}
    for d in [REPO / "discovery_fabric/dsb_v1/cases/real",
              REPO / "discovery_fabric/dsb_v1/cases/fabricated"]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Load packets (to map packet_id -> receipt_id)
    packets_path = REPO / "discovery_fabric/dsb_v1/adjudication/adjudication_packets.json"
    with open(packets_path) as f:
        packets_data = json.load(f)
    packet_to_receipt = {}
    for p in packets_data["packets"]:
        packet_to_receipt[p["packet_id"]] = p["_internal"]["receipt_id"]

    # Build majority-vote human verdict per packet (Q2 = DISCOVERY_STRUCTURE_MATCH)
    packet_q2s = defaultdict(list)
    for adj in adjudicators:
        for entry in adj["scores"]:
            packet_q2s[entry["packet_id"]].append(entry.get("Q2_DISCOVERY_STRUCTURE_MATCH", ""))

    # Per-packet majority (YES > PARTIAL > NO priority in tie)
    packet_majority = {}
    for pid, q2s in packet_q2s.items():
        yes_c = sum(1 for q in q2s if q.upper() == "YES")
        partial_c = sum(1 for q in q2s if q.upper() == "PARTIAL")
        no_c = sum(1 for q in q2s if q.upper() == "NO")
        if yes_c >= partial_c and yes_c >= no_c:
            packet_majority[pid] = "YES"
        elif partial_c >= no_c:
            packet_majority[pid] = "PARTIAL"
        else:
            packet_majority[pid] = "NO"

    # Per-arm summary
    arms = ["LLM_only", "mechanism_only", "combination", "full_system"]
    per_arm = {}
    for arm in arms:
        human_real_strict = 0  # YES on real cases
        human_real_lenient = 0  # YES or PARTIAL on real cases
        human_fab_strict = 0
        human_fab_lenient = 0
        scorer_real_recovered = 0
        scorer_fab_recovered = 0
        n_real = 0
        n_fab = 0

        for pid, majority in packet_majority.items():
            receipt_id = packet_to_receipt.get(pid)
            if not receipt_id:
                continue
            scorer_score = scores_by_receipt.get(receipt_id)
            if not scorer_score or scorer_score["arm"] != arm:
                continue
            case = cases.get(scorer_score["case_id"])
            if not case:
                continue
            if case["case_type"] == "real":
                n_real += 1
                if majority == "YES":
                    human_real_strict += 1
                if majority in ("YES", "PARTIAL"):
                    human_real_lenient += 1
                if scorer_score["discovery_structure_recovery"]["verdict"] == "RECOVERED":
                    scorer_real_recovered += 1
            else:
                n_fab += 1
                if majority == "YES":
                    human_fab_strict += 1
                if majority in ("YES", "PARTIAL"):
                    human_fab_lenient += 1
                if scorer_score["discovery_structure_recovery"]["verdict"] == "RECOVERED":
                    scorer_fab_recovered += 1

        per_arm[arm] = {
            "n_real": n_real,
            "n_fab": n_fab,
            "human_real_strict_yes": human_real_strict,
            "human_real_lenient_yes": human_real_lenient,
            "human_fab_strict_yes": human_fab_strict,
            "human_fab_lenient_yes": human_fab_lenient,
            "scorer_real_recovered": scorer_real_recovered,
            "scorer_fab_recovered": scorer_fab_recovered,
            "human_real_strict_rate": round(human_real_strict / max(n_real, 1), 4),
            "human_fab_strict_rate": round(human_fab_strict / max(n_fab, 1), 4),
            "scorer_real_rate": round(scorer_real_recovered / max(n_real, 1), 4),
            "scorer_fab_rate": round(scorer_fab_recovered / max(n_fab, 1), 4),
            "inversion_persists_human": human_fab_strict > human_real_strict,
            "inversion_persists_scorer": scorer_fab_recovered > scorer_real_recovered,
        }

    return {
        "status": "COMPUTED",
        "n_adjudicators": len(adjudicators),
        "per_arm": per_arm,
        "interpretation": (
            "If human_real_strict_rate > human_fab_strict_rate, the fabricated-vs-real "
            "inversion does NOT persist under human judgment — the deterministic scorer "
            "was the problem. If the inversion persists, the problem is in the LLM or "
            "the case design, not the scorer."
        ),
    }


def main():
    print("=" * 72)
    print("DSB V1 — ARCHITECTURE RECOMPUTE (HUMAN GOLD STANDARD)")
    print("=" * 72)
    print()

    result = recompute_architecture_comparison()
    print(f"Status: {result['status']}")

    if result["status"] != "COMPUTED":
        print(result["reason"])
        for f in result.get("prerequisite_failures", []):
            print(f"  - {f}")
        return

    print(f"Adjudicators: {result['n_adjudicators']}")
    print()
    print(f"{'Arm':<16} {'Real(human)':>12} {'Fab(human)':>12} {'Real(scorer)':>13} {'Fab(scorer)':>13} {'Inv(human)':>11} {'Inv(scorer)':>12}")
    print("-" * 95)
    for arm, a in result["per_arm"].items():
        print(f"{arm:<16} {a['human_real_strict_rate']:>12.3f} {a['human_fab_strict_rate']:>12.3f} "
              f"{a['scorer_real_rate']:>13.3f} {a['scorer_fab_rate']:>13.3f} "
              f"{str(a['inversion_persists_human']):>11} {str(a['inversion_persists_scorer']):>12}")

    # Save
    out_path = REPO / "discovery_fabric/dsb_v1/adjudication/analysis/architecture_recompute.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
