"""
DSB V1 — Inter-Rater Agreement
================================

Measures agreement among 2-3 independent expert adjudicators.

For 2 adjudicators: Cohen's kappa (per question Q1, Q2, Q3).
For 3+ adjudicators: Fleiss' kappa (per question).

Also reports:
  - Raw percentage agreement
  - Per-question agreement
  - Per-case-type agreement (real vs fabricated)

This module is RUN AFTER human adjudication results are submitted.
"""
import json
import sys
import math
import os
from pathlib import Path
from collections import defaultdict, Counter

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
os.chdir(REPO)


def load_adjudicator_results() -> list[dict]:
    """Load all adjudicator result files."""
    results_dir = REPO / "discovery_fabric/dsb_v1/adjudication/results"
    adjudicators = []
    for rp in sorted(results_dir.glob("adjudicator_*.json")):
        with open(rp) as f:
            adjudicators.append(json.load(f))
    return adjudicators


def cohen_kappa(rater1: list[str], rater2: list[str]) -> dict:
    """Compute Cohen's kappa for two raters on a list of items.

    Both raters must have rated the same items in the same order.
    """
    assert len(rater1) == len(rater2), f"length mismatch: {len(rater1)} vs {len(rater2)}"
    n = len(rater1)
    if n == 0:
        return {"kappa": None, "reason": "no items"}

    # Get all categories
    categories = sorted(set(rater1) | set(rater2))

    # Build confusion matrix
    matrix = defaultdict(lambda: defaultdict(int))
    for a, b in zip(rater1, rater2):
        matrix[a][b] += 1

    # Observed agreement
    p_o = sum(matrix[c][c] for c in categories) / n

    # Expected agreement (by chance)
    marginals_a = Counter(rater1)
    marginals_b = Counter(rater2)
    p_e = sum((marginals_a[c] / n) * (marginals_b[c] / n) for c in categories)

    if p_e == 1.0:
        return {"kappa": 1.0, "p_o": 1.0, "p_e": 1.0, "n": n, "categories": categories,
                "reason": "perfect agreement (all same category)"}

    kappa = (p_o - p_e) / (1 - p_e)
    return {
        "kappa": round(kappa, 4),
        "p_o": round(p_o, 4),
        "p_e": round(p_e, 4),
        "n": n,
        "categories": categories,
    }


def fleiss_kappa(ratings: list[list[str]]) -> dict:
    """Compute Fleiss' kappa for ≥2 raters.

    Args:
        ratings: list of items, each item is a list of ratings from all raters.
                 e.g., [["YES", "YES", "NO"], ["NO", "NO", "PARTIAL"], ...]

    Returns:
        dict with kappa, p_o, p_e, n, k (number of raters), categories.
    """
    if not ratings:
        return {"kappa": None, "reason": "no items"}
    n = len(ratings)
    k = len(ratings[0])
    if k < 2:
        return {"kappa": None, "reason": "need at least 2 raters"}

    categories = sorted(set(c for item in ratings for c in item))

    # Build count matrix: n_items × n_categories
    # counts[i][c] = number of raters who assigned category c to item i
    counts = []
    for item in ratings:
        c = Counter(item)
        counts.append([c.get(cat, 0) for cat in categories])

    # P_i (per-item agreement): (1/(k(k-1))) * sum_j n_ij^2 - k
    P_i = []
    for row in counts:
        sum_sq = sum(x * x for x in row)
        P_i.append((sum_sq - k) / (k * (k - 1)))
    P_bar = sum(P_i) / n  # mean P_i = observed agreement

    # p_j (marginal prob of category j)
    p_j = []
    for j, cat in enumerate(categories):
        total = sum(counts[i][j] for i in range(n))
        p_j.append(total / (n * k))

    # P_e = sum_j p_j^2
    P_e = sum(p * p for p in p_j)

    if P_e == 1.0:
        return {"kappa": 1.0, "p_o": 1.0, "p_e": 1.0, "n": n, "k": k,
                "categories": categories, "reason": "perfect agreement"}

    kappa = (P_bar - P_e) / (1 - P_e)
    return {
        "kappa": round(kappa, 4),
        "p_o": round(P_bar, 4),
        "p_e": round(P_e, 4),
        "n": n,
        "k": k,
        "categories": categories,
    }


def compute_inter_rater_agreement() -> dict:
    """Compute inter-rater agreement for all questions."""
    adjudicators = load_adjudicator_results()
    if len(adjudicators) < 2:
        return {
            "status": "INSUFFICIENT_ADJUDICATORS",
            "n_adjudicators": len(adjudicators),
            "message": (
                "Need at least 2 adjudicator result files. "
                "This module runs AFTER human adjudication is complete."
            ),
        }

    # Align ratings by packet_id
    packets_by_id = defaultdict(dict)  # packet_id -> {adj_id: score_entry}
    for adj in adjudicators:
        adj_id = adj["adjudicator_id"]
        for entry in adj["scores"]:
            packets_by_id[entry["packet_id"]][adj_id] = entry

    # Only keep packets rated by ALL adjudicators
    n_adj = len(adjudicators)
    adj_ids = [adj["adjudicator_id"] for adj in adjudicators]
    complete_packets = {pid: scores for pid, scores in packets_by_id.items()
                        if len(scores) == n_adj}

    if not complete_packets:
        return {
            "status": "NO_COMPLETE_PACKETS",
            "n_adjudicators": n_adj,
            "message": "No packets were rated by all adjudicators.",
        }

    questions = ["Q1_MECHANISM_MATCH", "Q2_DISCOVERY_STRUCTURE_MATCH", "Q3_SPECIFICITY"]
    agreement = {}

    for q in questions:
        # Build ratings list: items × raters
        ratings = []
        for pid in sorted(complete_packets):
            item_ratings = [complete_packets[pid][adj_id].get(q, "") for adj_id in adj_ids]
            ratings.append(item_ratings)

        if n_adj == 2:
            # Cohen's kappa
            rater1 = [r[0] for r in ratings]
            rater2 = [r[1] for r in ratings]
            kappa_result = cohen_kappa(rater1, rater2)
            agreement[q] = {
                "method": "cohen_kappa",
                "n_raters": 2,
                "n_items": len(ratings),
                **kappa_result,
            }
        else:
            # Fleiss' kappa
            kappa_result = fleiss_kappa(ratings)
            agreement[q] = {
                "method": "fleiss_kappa",
                "n_raters": n_adj,
                "n_items": len(ratings),
                **kappa_result,
            }

        # Raw percentage agreement (pairwise)
        if n_adj == 2:
            n_agree = sum(1 for r in ratings if r[0] == r[1])
            agreement[q]["pct_agreement"] = {"pair_1_2": round(n_agree / len(ratings), 4)}
        else:
            # All-pairs percentage agreement
            pair_agreements = {}
            from itertools import combinations
            for i, j in combinations(range(n_adj), 2):
                n_agree = sum(1 for r in ratings if r[i] == r[j])
                pair_agreements[f"pair_{i+1}_{j+1}"] = round(n_agree / len(ratings), 4)
            agreement[q]["pct_agreements"] = pair_agreements

    # Interpretation
    def interpret_kappa(k):
        if k is None:
            return "N/A"
        if k < 0:
            return "poor (worse than chance)"
        if k < 0.20:
            return "slight"
        if k < 0.40:
            return "fair"
        if k < 0.60:
            return "moderate"
        if k < 0.80:
            return "substantial"
        return "almost perfect"

    for q in agreement:
        k = agreement[q].get("kappa")
        agreement[q]["interpretation"] = interpret_kappa(k)

    return {
        "status": "COMPUTED",
        "n_adjudicators": n_adj,
        "adjudicator_ids": adj_ids,
        "n_complete_packets": len(complete_packets),
        "agreement_by_question": agreement,
    }


def main():
    print("=" * 72)
    print("DSB V1 — INTER-RATER AGREEMENT")
    print("=" * 72)
    print()

    result = compute_inter_rater_agreement()
    print(f"Status: {result['status']}")

    if result["status"] != "COMPUTED":
        print(result.get("message", "Cannot compute."))
        return

    print(f"Adjudicators: {result['n_adjudicators']} ({', '.join(result['adjudicator_ids'])})")
    print(f"Complete packets: {result['n_complete_packets']}")
    print()
    print(f"{'Question':<35} {'Method':<15} {'Kappa':>6} {'P_o':>6} {'P_e':>6} {'Interpretation':<25}")
    print("-" * 100)
    for q, a in result["agreement_by_question"].items():
        kappa = a.get("kappa")
        p_o = a.get("p_o")
        p_e = a.get("p_e")
        interp = a.get("interpretation", "")
        print(f"{q:<35} {a['method']:<15} {kappa:>6} {p_o:>6} {p_e:>6} {interp:<25}")

    # Save
    out_path = REPO / "discovery_fabric/dsb_v1/adjudication/analysis/inter_rater_agreement.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
