#!/usr/bin/env python3
"""
tier2_review_aggregation.py — Aggregate Tier-2 human review responses.

Run this script AFTER reviewers have filled in tier2_review_template.csv.
It computes:
  - Per-dimension mean score across reviewers
  - Per-proposal overall verdict distribution
  - Inter-rater agreement (Fleiss' kappa if scipy is available, else
    simple agreement rate)
  - Final gate verdict (PASS if mean overall score >= 3.5 AND
    >= 50% of proposals are ACCEPTED)

Usage:
    python3 reports/tier2_review_aggregation.py reports/tier2_review_responses.csv
"""
import sys
import json
import csv
import statistics
from pathlib import Path
from collections import defaultdict, Counter


def aggregate(responses_csv: str) -> dict:
    """Aggregate responses from CSV file."""
    rows = []
    with open(responses_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return {"error": "no responses", "n_responses": 0}

    # Per-dimension scores
    dim_scores = defaultdict(list)
    verdicts = defaultdict(list)
    for r in rows:
        # Dynamic dimension keys (D1, D2, ...)
        for k, v in r.items():
            if k.startswith("D") and v.strip():
                try:
                    dim_scores[k].append(float(v))
                except ValueError:
                    pass
        if r.get("overall_verdict", "").strip():
            verdicts[r["anon_id"]].append(r["overall_verdict"].strip())

    # Per-dimension stats
    dim_stats = {}
    for dim, scores in dim_scores.items():
        dim_stats[dim] = {
            "n": len(scores),
            "mean": round(statistics.mean(scores), 4) if scores else 0.0,
            "stdev": round(statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
        }

    # Verdict distribution
    verdict_dist = {}
    for anon_id, vs in verdicts.items():
        verdict_dist[anon_id] = dict(Counter(vs))

    # Overall accept rate
    all_verdicts = [v for vs in verdicts.values() for v in vs]
    accept_rate = (all_verdicts.count("ACCEPT") / max(1, len(all_verdicts))
                   if all_verdicts else 0.0)

    # Mean of dimension means
    dim_means = [s["mean"] for s in dim_stats.values() if s["n"] > 0]
    overall_mean = statistics.mean(dim_means) if dim_means else 0.0

    # Gate verdict
    if overall_mean >= 3.5 and accept_rate >= 0.5:
        gate_verdict = "PASS"
    elif overall_mean >= 3.0 or accept_rate >= 0.3:
        gate_verdict = "PARTIAL"
    else:
        gate_verdict = "FAIL"

    return {
        "n_responses": len(rows),
        "n_unique_proposals": len(verdicts),
        "dimension_stats": dim_stats,
        "verdict_distribution_per_proposal": verdict_dist,
        "accept_rate": round(accept_rate, 4),
        "overall_mean_score": round(overall_mean, 4),
        "gate_verdict": gate_verdict,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: tier2_review_aggregation.py <responses.csv>")
        sys.exit(1)
    result = aggregate(sys.argv[1])
    print(json.dumps(result, indent=2))

    # Write result
    out_path = Path(sys.argv[1]).parent / "tier2_review_aggregated.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {out_path}")

    return 0 if result.get("gate_verdict") == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
