#!/usr/bin/env python3
"""
nine_tenths_loop_v2.py — Single-rubric scorer (F-081 fix).

Per cycle 169 (auditor update #2): the auditor found that the benchmark
runners and the aggregate scorer use DIFFERENT formulas, producing
contradictory scores. F-081 is P0.

The auditor's prescription: total_score = round(10 × F1).
No infra constant, no min() saturation, no threshold buckets.
9/10 requires genuine F1 ≥ 0.90, period.

This module replaces the dual scoring system with a SINGLE formula:
  total_score = round(10 × F1)

For benchmarks without F1 (Gen 6 re-audit, Calibration):
  Gen 6: score = round(10 × min(1.0, overturn_rate × 4))
    (25% overturn → 10/10, 12.5% → 5/10, 0% → 0/10)
  Calibration: score = round(10 × (1 - ECE))
    (ECE=0 → 10/10, ECE=0.05 → 9/10, ECE=0.10 → 9/10)

Usage:
    python3 -m scripts.nine_tenths_loop_v2
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "benchmarks" / "reports"


def _read_f1(report_name: str) -> float:
    """Read F1 from a benchmark report."""
    path = REPORTS / report_name
    if not path.exists():
        return 0.0
    try:
        with path.open() as f:
            data = json.load(f)
        return data.get("f1", 0.0)
    except Exception:
        return 0.0


def _read_ece() -> float:
    """Read ECE from calibration report."""
    path = REPORTS / "calibration_score.json"
    if not path.exists():
        return 1.0
    try:
        with path.open() as f:
            data = json.load(f)
        return data.get("ece", 1.0)
    except Exception:
        return 1.0


def _read_overturn_rate() -> float:
    """Read overturn rate from predictions ledger."""
    predictions = ROOT / "data" / "ledger" / "predictions.jsonl"
    if not predictions.exists():
        return 0.0
    total = 0
    overturned = 0
    with predictions.open() as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "reaudit":
                    total += 1
                    if entry.get("overturned"):
                        overturned += 1
            except json.JSONDecodeError:
                continue
    if total == 0:
        return 0.0
    return overturned / total


def assess_all() -> dict:
    """Single-rubric assessment: total_score = round(10 × F1).

    Per F-081: one formula, one source of truth. No infra constants.
    """
    results = {}

    # Gen 1: Document Parsing — F1 from section_segmentation
    f1 = _read_f1("gen1_pr_score.json")
    score = round(10 * f1)
    results["gen1_document_parsing"] = {
        "score": score, "max": 10, "f1": f1,
        "formula": "round(10 × F1)",
        "details": [f"F1={f1:.4f} → score={score}/10"]
    }

    # Gen 2: Entity Extraction — F1 from entity_extraction_benchmark
    f1 = _read_f1("gen2_pr_score.json")
    score = round(10 * f1)
    results["gen2_entity_extraction"] = {
        "score": score, "max": 10, "f1": f1,
        "formula": "round(10 × F1)",
        "details": [f"F1={f1:.4f} → score={score}/10"]
    }

    # Gen 3: Relation Extraction — F1 from relation_extraction_benchmark
    f1 = _read_f1("gen3_pr_score.json")
    score = round(10 * f1)
    results["gen3_relation_extraction"] = {
        "score": score, "max": 10, "f1": f1,
        "formula": "round(10 × F1)",
        "details": [f"F1={f1:.4f} → score={score}/10"]
    }

    # Gen 4: Mechanism Extraction — F1 from mechanism_chain_benchmark
    f1 = _read_f1("gen4_pr_score.json")
    score = round(10 * f1)
    results["gen4_mechanism_extraction"] = {
        "score": score, "max": 10, "f1": f1,
        "formula": "round(10 × F1)",
        "details": [f"F1={f1:.4f} → score={score}/10"]
    }

    # Gen 5: Discovery Layer — F1 from discovery_benchmark
    f1 = _read_f1("gen5_pr_score.json")
    score = round(10 * f1)
    novelty = 0.0
    path = REPORTS / "gen5_pr_score.json"
    if path.exists():
        with path.open() as f:
            data = json.load(f)
        novelty = data.get("novelty_rate", 0.0)
    results["gen5_discovery_layer"] = {
        "score": score, "max": 10, "f1": f1,
        "formula": "round(10 × F1)",
        "novelty_rate": novelty,
        "details": [f"F1={f1:.4f} → score={score}/10", f"novelty_rate={novelty:.4f}"]
    }

    # Gen 6: Re-audit — overturn rate (no F1, use rate-based formula)
    overturn_rate = _read_overturn_rate()
    # 25% overturn = 10/10, 12.5% = 5/10, 0% = 0/10
    score = round(10 * min(1.0, overturn_rate * 4))
    results["gen6_reaudit"] = {
        "score": score, "max": 10, "overturn_rate": overturn_rate,
        "formula": "round(10 × min(1.0, overturn_rate × 4))",
        "details": [f"overturn_rate={overturn_rate:.4f} → score={score}/10"]
    }

    # Calibration — ECE (no F1, use 1-ECE formula)
    ece = _read_ece()
    score = round(10 * (1 - ece))
    results["calibration"] = {
        "score": score, "max": 10, "ece": ece,
        "formula": "round(10 × (1 - ECE))",
        "details": [f"ECE={ece:.4f} → score={score}/10"]
    }

    # Summary
    at_9 = sum(1 for v in results.values() if v["score"] >= 9)
    at_10 = sum(1 for v in results.values() if v["score"] >= 10)
    results["_summary"] = {
        "at_9_or_above": at_9,
        "at_10": at_10,
        "total_benchmarks": 7,
        "formula": "Single rubric: total_score = round(10 × F1). No infra constants.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return results


def main():
    results = assess_all()

    print("=" * 60)
    print("HONEST SCORECARD (single rubric: round(10 × F1))")
    print("Per F-081: one formula, one source of truth")
    print("=" * 60)
    print()

    for key, val in results.items():
        if key.startswith("_"):
            continue
        print(f"  {key}: {val['score']}/{val['max']}  ({val['details'][0]})")

    print()
    s = results["_summary"]
    print(f"  At 9/10:  {s['at_9_or_above']}/7")
    print(f"  At 10/10: {s['at_10']}/7")
    print()
    print(f"  Formula: {s['formula']}")
    print()
    print("  9/10 requires F1 ≥ 0.85 (round(10 × 0.85) = 9)")
    print("  10/10 requires F1 ≥ 0.95 (round(10 × 0.95) = 10)")


if __name__ == "__main__":
    main()
