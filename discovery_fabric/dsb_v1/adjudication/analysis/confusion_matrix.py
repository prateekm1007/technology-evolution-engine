"""
DSB V1 — Human vs Deterministic-Scorer Confusion Matrices
===========================================================

Computes confusion matrices comparing human adjudicator verdicts to the
deterministic scorer's verdicts, SEPARATELY for real and fabricated cases.

This module is RUN AFTER human adjudication results are submitted.
It does NOT run until adjudication/results/ contains ≥2 adjudicator result files.

For Q2 (DISCOVERY_STRUCTURE_MATCH), the deterministic scorer's verdict is
binary (RECOVERED / NOT_RECOVERED). Human verdicts are 3-way (YES / PARTIAL / NO).

We compute two confusion matrices:
  (a) Strict: human YES = positive, human PARTIAL/NO = negative
  (b) Lenient: human YES/PARTIAL = positive, human NO = negative

For each matrix, we report:
  - TP, FP, TN, FN
  - Precision, Recall, F1
  - Accuracy

Separately for real and fabricated cases.

A systematic false-positive pattern (high FP rate on fabricated cases) would
indicate the scorer is too lenient on plausible-sounding combinations.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

# Ensure discovery_fabric is importable
import os
os.chdir(REPO)

from discovery_fabric.dsb_v1.scorer import score_all
from discovery_fabric.dsb_v1.case_schema import load_case


def load_adjudicator_results() -> list[dict]:
    """Load all adjudicator result files from adjudication/results/."""
    results_dir = REPO / "discovery_fabric/dsb_v1/adjudication/results"
    adjudicators = []
    for rp in sorted(results_dir.glob("adjudicator_*.json")):
        with open(rp) as f:
            data = json.load(f)
        adjudicators.append(data)
    return adjudicators


def map_human_to_binary(human_verdict: str, strict: bool) -> bool | None:
    """Map a human verdict (YES/PARTIAL/NO) to a binary positive/negative.

    strict=True: only YES is positive.
    strict=False: YES and PARTIAL are positive.
    """
    v = (human_verdict or "").upper()
    if strict:
        return v == "YES"
    else:
        return v in ("YES", "PARTIAL")


def compute_confusion_matrix(human_positives: list[bool], scorer_positives: list[bool]) -> dict:
    """Compute TP/FP/TN/FN + precision/recall/F1/accuracy."""
    tp = sum(1 for h, s in zip(human_positives, scorer_positives) if h and s)
    fp = sum(1 for h, s in zip(human_positives, scorer_positives) if not h and s)
    tn = sum(1 for h, s in zip(human_positives, scorer_positives) if not h and not s)
    fn = sum(1 for h, s in zip(human_positives, scorer_positives) if h and not s)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    accuracy = (tp + tn) / max(tp + fp + tn + fn, 1)
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "n": tp + fp + tn + fn,
    }


def compute_confusion_matrices() -> dict:
    """Compute confusion matrices for Q2 (DISCOVERY_STRUCTURE_MATCH).

    Returns matrices for:
      - real cases (strict + lenient)
      - fabricated cases (strict + lenient)
      - all cases (strict + lenient)

    For each adjudicator (if multiple), and majority-vote across adjudicators.
    """
    adjudicators = load_adjudicator_results()
    if not adjudicators:
        return {
            "status": "NO_ADJUDICATOR_RESULTS",
            "message": (
                "No adjudicator result files found in adjudication/results/. "
                "This module runs AFTER human adjudication is complete."
            ),
        }

    # Load scorer results
    scorer_result = score_all()
    scores_by_receipt = {s["receipt_id"]: s for s in scorer_result["scores"]}

    # Load cases (to determine real vs fabricated)
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

    # For each adjudicator, compute matrices
    per_adjudicator = {}
    for adj in adjudicators:
        adj_id = adj["adjudicator_id"]
        # Build lists of (human_verdict, scorer_verdict, case_type) per packet
        rows = []
        for score_entry in adj["scores"]:
            packet_id = score_entry["packet_id"]
            receipt_id = packet_to_receipt.get(packet_id)
            if not receipt_id:
                continue
            scorer_score = scores_by_receipt.get(receipt_id)
            if not scorer_score:
                continue
            case_id = scorer_score["case_id"]
            case = cases.get(case_id)
            if not case:
                continue
            case_type = case["case_type"]
            human_q2 = score_entry.get("Q2_DISCOVERY_STRUCTURE_MATCH", "")
            scorer_q2_positive = scorer_score["discovery_structure_recovery"]["verdict"] == "RECOVERED"
            rows.append((human_q2, scorer_q2_positive, case_type))

        # Compute matrices
        matrices = {}
        for case_type in ["real", "fabricated", "all"]:
            subset = [r for r in rows if case_type == "all" or r[2] == case_type]
            for strict in [True, False]:
                human_pos = [map_human_to_binary(r[0], strict) for r in subset]
                scorer_pos = [r[1] for r in subset]
                key = f"{case_type}_{'strict' if strict else 'lenient'}"
                matrices[key] = compute_confusion_matrix(human_pos, scorer_pos)
        per_adjudicator[adj_id] = matrices

    # Majority vote across adjudicators
    # For each packet, take majority Q2 (YES > PARTIAL > NO as priority in tie)
    packet_q2s = defaultdict(list)
    for adj in adjudicators:
        for score_entry in adj["scores"]:
            packet_q2s[score_entry["packet_id"]].append(score_entry.get("Q2_DISCOVERY_STRUCTURE_MATCH", ""))

    majority_rows = []
    for packet_id, q2s in packet_q2s.items():
        receipt_id = packet_to_receipt.get(packet_id)
        if not receipt_id:
            continue
        scorer_score = scores_by_receipt.get(receipt_id)
        if not scorer_score:
            continue
        case_id = scorer_score["case_id"]
        case = cases.get(case_id)
        if not case:
            continue
        case_type = case["case_type"]
        # Majority vote: count YES, PARTIAL, NO
        yes_count = sum(1 for q in q2s if q.upper() == "YES")
        partial_count = sum(1 for q in q2s if q.upper() == "PARTIAL")
        no_count = sum(1 for q in q2s if q.upper() == "NO")
        # Majority is whichever has the most votes; tie goes YES > PARTIAL > NO
        if yes_count >= partial_count and yes_count >= no_count:
            majority_q2 = "YES"
        elif partial_count >= no_count:
            majority_q2 = "PARTIAL"
        else:
            majority_q2 = "NO"
        scorer_q2_positive = scorer_score["discovery_structure_recovery"]["verdict"] == "RECOVERED"
        majority_rows.append((majority_q2, scorer_q2_positive, case_type))

    majority_matrices = {}
    for case_type in ["real", "fabricated", "all"]:
        subset = [r for r in majority_rows if case_type == "all" or r[2] == case_type]
        for strict in [True, False]:
            human_pos = [map_human_to_binary(r[0], strict) for r in subset]
            scorer_pos = [r[1] for r in subset]
            key = f"{case_type}_{'strict' if strict else 'lenient'}"
            majority_matrices[key] = compute_confusion_matrix(human_pos, scorer_pos)

    return {
        "status": "COMPUTED",
        "n_adjudicators": len(adjudicators),
        "adjudicator_ids": [adj["adjudicator_id"] for adj in adjudicators],
        "per_adjudicator": per_adjudicator,
        "majority_vote": majority_matrices,
        "explanation": (
            "Strict: human YES = positive, PARTIAL/NO = negative. "
            "Lenient: human YES/PARTIAL = positive, NO = negative. "
            "Scorer positive = RECOVERED. "
            "High FP rate on fabricated cases = scorer too lenient on plausible-sounding combinations."
        ),
    }


def main():
    print("=" * 72)
    print("DSB V1 — HUMAN vs DETERMINISTIC-SCORER CONFUSION MATRICES")
    print("=" * 72)
    print()

    result = compute_confusion_matrices()
    print(f"Status: {result['status']}")

    if result["status"] != "COMPUTED":
        print(result["message"])
        return

    print(f"Adjudicators: {result['n_adjudicators']}")
    print()

    print("MAJORITY-VOTE CONFUSION MATRICES:")
    print(f"{'Case Type':<14} {'Mode':<10} {'TP':>3} {'FP':>3} {'TN':>3} {'FN':>3} {'Prec':>6} {'Rec':>6} {'F1':>6} {'Acc':>6}")
    print("-" * 75)
    for key, m in result["majority_vote"].items():
        ct, mode = key.rsplit("_", 1)
        print(f"{ct:<14} {mode:<10} {m['tp']:>3} {m['fp']:>3} {m['tn']:>3} {m['fn']:>3} "
              f"{m['precision']:>6.3f} {m['recall']:>6.3f} {m['f1']:>6.3f} {m['accuracy']:>6.3f}")

    # Save
    out_path = REPO / "discovery_fabric/dsb_v1/adjudication/analysis/confusion_matrices.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
