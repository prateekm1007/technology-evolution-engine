"""
V1.13 GATE 2 — Evaluator (DETERMINISTIC, no LLM)
==================================================

Evaluates the 40 leakage-controlled receipts (10 cases × 4 configs) under
the Gate 2 forensic criteria:

  - Information-content test (deterministic entailment) → RECONSTRUCTION
    vs GENUINE_NOVEL_PREDICTION
  - Stricter quantitative accuracy (point estimate + tight tolerance,
    NO broad ranges)
  - Calibration error: |predicted - observed| / |observed|
  - Final classification per receipt:
        RECONSTRUCTION
        GENUINE_NOVEL_PREDICTION
        CORRECT
        INCORRECT
        INDETERMINATE

  The classification is computed as follows:
    1. Run the deterministic entailment test.
       → If RECONSTRUCTION: final = RECONSTRUCTION (regardless of correctness)
       → If PARTIALLY_NOVEL: final = RECONSTRUCTION (treat as not genuinely novel)
       → If GENUINE_NOVEL_PREDICTION: proceed to step 2.
    2. For GENUINE_NOVEL_PREDICTION, evaluate quantitative accuracy:
       → If BINARY: exact YES/NO match → CORRECT / INCORRECT
       → If numeric: observed value within [predicted * tol_lower, predicted * tol_upper]
         AND calibration_error ≤ 0.50 → CORRECT
       → Else → INCORRECT
    3. If gen_success = False → INDETERMINATE (no prediction to evaluate)

  Reports per-config:
    - count of each classification
    - mean calibration_error (over numeric CORRECT cases)
    - mean information_content_score
    - DPS=1 rate (genuine novel AND correct)

  Exit gate: if fewer than MEANINGFUL_MIN (default 3) GENUINE_NOVEL_PREDICTION
  across all 40 receipts, OR if no config achieves DPS=1 rate materially
  above the random control, ACCEPT THE NEGATIVE RESULT.
"""
from __future__ import annotations

import json
import re
import math
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
import sys
sys.path.insert(0, str(REPO))

from discovery_fabric.v1_13.prediction_receipt import verify_receipt  # noqa: E402
from discovery_fabric.v1_13_gate2.deterministic_entailment_test import classify_prediction  # noqa: E402

GATE2_DIR = REPO / "discovery_fabric/v1_13_gate2"
RECEIPTS_DIR = GATE2_DIR / "receipts"
EVIDENCE_DIR = GATE2_DIR / "evidence_objects"
BENCHMARK = REPO / "discovery_fabric/v1_13/benchmark_dataset.json"
RESULTS_OUT = GATE2_DIR / "results.json"
REPORT_OUT = GATE2_DIR / "V1_13_GATE2_REPORT.md"

# Stricter calibration threshold (multiplicative)
# If predicted=100 and observed=180, calibration_error = 0.80 (FAILS)
# If predicted=100 and observed=140, calibration_error = 0.40 (PASSES)
STRICT_CALIBRATION_THRESHOLD = 0.50

# Meaningful minimum for exit gate
MEANINGFUL_MIN_NOVEL = 3
MATERIAL_ADVANTAGE_PP = 15.0  # treatment must beat control by >= 15pp


def load_benchmark() -> dict:
    with open(BENCHMARK) as f:
        return {c["id"]: c for c in json.load(f)}


def evaluate_numeric(receipt: dict, outcome: dict) -> dict:
    """Stricter numeric evaluation: point estimate + tight multiplicative tolerance."""
    predicted = receipt.get("gate2_predicted_value")
    tl = receipt.get("gate2_tolerance_lower")
    tu = receipt.get("gate2_tolerance_upper")
    obs_val = outcome.get("value")

    if not isinstance(predicted, (int, float)) or not isinstance(obs_val, (int, float)):
        return {"verdict": "INDETERMINATE", "calibration_error": None,
                "predicted": predicted, "observed": obs_val,
                "tolerance_bounds": None}

    if not isinstance(tl, (int, float)) or not isinstance(tu, (int, float)):
        return {"verdict": "INDETERMINATE", "calibration_error": None,
                "predicted": predicted, "observed": obs_val,
                "tolerance_bounds": None}

    low = predicted * tl
    high = predicted * tu
    in_range = low <= float(obs_val) <= high
    cal_err = abs(predicted - float(obs_val)) / max(abs(float(obs_val)), 1e-9)

    verdict = "CORRECT" if (in_range and cal_err <= STRICT_CALIBRATION_THRESHOLD) else "INCORRECT"
    return {
        "verdict": verdict,
        "calibration_error": round(cal_err, 4),
        "predicted": predicted,
        "observed": obs_val,
        "tolerance_bounds": [round(low, 4), round(high, 4)],
        "in_range": in_range,
        "strict_calibration_threshold": STRICT_CALIBRATION_THRESHOLD,
    }


def evaluate_binary(receipt: dict, outcome: dict) -> dict:
    """Binary evaluation: exact YES/NO match."""
    predicted = str(receipt.get("gate2_predicted_value", "")).upper()
    observed = str(outcome.get("value", "")).upper()
    if predicted not in {"YES", "NO"} or observed not in {"YES", "NO"}:
        return {"verdict": "INDETERMINATE", "calibration_error": None,
                "predicted": predicted, "observed": observed}
    verdict = "CORRECT" if predicted == observed else "INCORRECT"
    return {
        "verdict": verdict,
        "calibration_error": 0.0 if verdict == "CORRECT" else 1.0,
        "predicted": predicted,
        "observed": observed,
    }


def evaluate_receipt(receipt: dict, outcome: dict, evidence_obj: dict) -> dict:
    """Full Gate 2 evaluation: entailment + quantitative + final classification."""
    # Verify receipt integrity
    integrity_ok = verify_receipt(receipt)

    # Run deterministic entailment test
    ic_result = classify_prediction(receipt, evidence_obj)

    # Quantitative evaluation
    direction = (receipt.get("expected_direction") or "").upper()
    if direction == "BINARY":
        quant = evaluate_binary(receipt, outcome)
    else:
        quant = evaluate_numeric(receipt, outcome)

    # Determine final classification
    ic_class = ic_result["classification"]
    if ic_class in ("RECONSTRUCTION", "PARTIALLY_NOVEL"):
        final = "RECONSTRUCTION"
    else:  # GENUINE_NOVEL_PREDICTION
        if quant["verdict"] == "CORRECT":
            final = "CORRECT"
        elif quant["verdict"] == "INCORRECT":
            final = "INCORRECT"
        else:
            final = "INDETERMINATE"

    # DPS=1: genuine novel AND correct
    dps = 1.0 if (ic_class == "GENUINE_NOVEL_PREDICTION" and quant["verdict"] == "CORRECT") else 0.0

    return {
        "final_classification": final,
        "information_content": {
            "classification": ic_class,
            "information_content_score": ic_result["information_content_score"],
            "encoded_count": ic_result["encoded_count"],
            "encoded_count_max": ic_result["encoded_count_max"],
            "reason": ic_result["reason"],
            "checks": ic_result["checks"],
        },
        "quantitative_accuracy": quant,
        "DISCOVERY_PREDICTION_SCORE": dps,
        "receipt_integrity_ok": integrity_ok,
    }


def evaluate_all() -> dict:
    benchmark = load_benchmark()
    receipts = sorted(RECEIPTS_DIR.glob("PRED2-*.json"))

    results = []
    for rp in receipts:
        with open(rp) as f:
            receipt = json.load(f)
        cid = receipt.get("candidate_id", "")
        m = re.match(r"PRED2-(PB-\d+)-(\w+)", cid)
        if not m:
            continue
        case_id, config = m.group(1), m.group(2)
        case = benchmark.get(case_id)
        if not case:
            continue
        evidence = case["pre_outcome_evidence"]
        outcome = case["outcome"]

        ev_path = EVIDENCE_DIR / f"{case_id}.json"
        if not ev_path.exists():
            continue
        with open(ev_path) as f:
            ev_obj = json.load(f)

        eval_result = evaluate_receipt(receipt, outcome, ev_obj)

        results.append({
            "key": f"{case_id}|{config}",
            "case_id": case_id,
            "case_name": case.get("name", ""),
            "config": config,
            "candidate_id": cid,
            "receipt_integrity_ok": eval_result["receipt_integrity_ok"],
            "simulation_registration_date": receipt.get("pre_registration_timestamp"),
            "evaluation_type": "HISTORICAL_RETROSPECTIVE_BACKTEST_GATE2",
            "leakage_control": receipt.get("gate2_leakage_control"),
            "backend": receipt.get("gate2_backend"),
            "hypothesis": receipt.get("hypothesis", "")[:300],
            "prediction": receipt.get("prediction", "")[:300],
            "predicted_value": receipt.get("gate2_predicted_value"),
            "tolerance_lower": receipt.get("gate2_tolerance_lower"),
            "tolerance_upper": receipt.get("gate2_tolerance_upper"),
            "expected_direction": receipt.get("expected_direction", ""),
            "outcome_source": outcome.get("source", ""),
            "outcome_value": outcome.get("value"),
            "outcome_direction": outcome.get("direction", ""),
            "outcome_measurement_date": outcome.get("measurement_date"),
            "final_classification": eval_result["final_classification"],
            "DISCOVERY_PREDICTION_SCORE": eval_result["DISCOVERY_PREDICTION_SCORE"],
            "information_content": eval_result["information_content"],
            "quantitative_accuracy": eval_result["quantitative_accuracy"],
            "receipt_hash": receipt.get("receipt_hash", ""),
        })

    # ---- Summary by config ----
    configs = sorted({r["config"] for r in results})
    summary = {}
    for cfg in configs:
        cfg_results = [r for r in results if r["config"] == cfg]
        n = len(cfg_results)
        cls_counts = Counter(r["final_classification"] for r in cfg_results)
        dps_1 = sum(1 for r in cfg_results if r["DISCOVERY_PREDICTION_SCORE"] == 1.0)
        # Mean calibration error over numeric CORRECT cases
        cal_errors = [r["quantitative_accuracy"].get("calibration_error")
                      for r in cfg_results
                      if r["quantitative_accuracy"].get("calibration_error") is not None
                      and r["quantitative_accuracy"].get("verdict") == "CORRECT"]
        # Mean IC score
        ic_scores = [r["information_content"]["information_content_score"] for r in cfg_results]
        # Genuine novel count
        genuine_novel = sum(1 for r in cfg_results
                            if r["information_content"]["classification"] == "GENUINE_NOVEL_PREDICTION")
        summary[cfg] = {
            "n": n,
            "classifications": dict(cls_counts),
            "DPS_1_count": dps_1,
            "DPS_1_pct": round(100 * dps_1 / max(n, 1), 1),
            "genuine_novel_count": genuine_novel,
            "genuine_novel_pct": round(100 * genuine_novel / max(n, 1), 1),
            "mean_calibration_error_correct": round(sum(cal_errors) / len(cal_errors), 4) if cal_errors else None,
            "n_numeric_correct": len(cal_errors),
            "mean_information_content_score": round(sum(ic_scores) / len(ic_scores), 4) if ic_scores else 0.0,
        }

    # ---- Overall totals ----
    total = len(results)
    overall_cls = Counter(r["final_classification"] for r in results)
    total_dps = sum(1 for r in results if r["DISCOVERY_PREDICTION_SCORE"] == 1.0)
    total_genuine_novel = sum(1 for r in results
                              if r["information_content"]["classification"] == "GENUINE_NOVEL_PREDICTION")

    # ---- Exit gate decision ----
    # 1. At least MEANINGFUL_MIN_NOVEL GENUINE_NOVEL_PREDICTION across all 40 receipts
    gate1_novel_count = total_genuine_novel >= MEANINGFUL_MIN_NOVEL
    # 2. Best treatment config DPS=1 rate materially > random control
    if "D_random" in summary and len(configs) > 1:
        random_dps_pct = summary["D_random"]["DPS_1_pct"]
        best_treatment = max(
            (s for cfg, s in summary.items() if cfg != "D_random"),
            key=lambda s: s["DPS_1_pct"], default=None
        )
        if best_treatment:
            gate2_material_advantage = (best_treatment["DPS_1_pct"] - random_dps_pct) >= MATERIAL_ADVANTAGE_PP
        else:
            gate2_material_advantage = False
    else:
        random_dps_pct = 0.0
        best_treatment = None
        gate2_material_advantage = False

    exit_gate_pass = gate1_novel_count and gate2_material_advantage

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "HISTORICAL_RETROSPECTIVE_BACKTEST_GATE2",
        "benchmark": "V1.13_PREDICTION_GATE2_LEAKAGE_CONTROLLED",
        "scoring": "DETERMINISTIC (no LLM judge) — Gate 2 forensic re-evaluation",
        "leakage_control": "evidence_only_prompt + point_estimate_requirement",
        "backend": "z-ai-cli-glm-4-plus",
        "strict_calibration_threshold": STRICT_CALIBRATION_THRESHOLD,
        "total_receipts": total,
        "total_cases": len(benchmark),
        "configs": configs,
        "overall_classification_counts": dict(overall_cls),
        "total_DPS_1": total_dps,
        "total_genuine_novel": total_genuine_novel,
        "exit_gate": {
            "meaningful_min_novel": MEANINGFUL_MIN_NOVEL,
            "material_advantage_pp": MATERIAL_ADVANTAGE_PP,
            "gate1_novel_count_pass": gate1_novel_count,
            "gate2_material_advantage_pass": gate2_material_advantage,
            "exit_gate_pass": exit_gate_pass,
            "random_dps_pct": random_dps_pct,
            "best_treatment_dps_pct": best_treatment["DPS_1_pct"] if best_treatment else None,
            "best_treatment_config": max(
                ((cfg, s) for cfg, s in summary.items() if cfg != "D_random"),
                key=lambda x: x[1]["DPS_1_pct"], default=(None, None)
            )[0] if best_treatment else None,
        },
        "summary_by_config": summary,
        "results": results,
    }
    return report


def main():
    report = evaluate_all()

    with open(RESULTS_OUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    h = hashlib.sha256(RESULTS_OUT.read_bytes()).hexdigest()
    print("=" * 76)
    print("V1.13 GATE 2 — LEAKAGE / INFORMATION-CONTENT VALIDATION — COMPLETE")
    print("=" * 76)
    print(f"Total receipts evaluated: {report['total_receipts']}")
    print(f"Backend: {report['backend']}")
    print(f"Leakage control: {report['leakage_control']}")
    print(f"Strict calibration threshold: {report['strict_calibration_threshold']}")
    print()
    print(f"OVERALL CLASSIFICATION COUNTS:")
    for cls, n in report["overall_classification_counts"].items():
        print(f"  {cls:30s}: {n:3d}  ({100*n/report['total_receipts']:.1f}%)")
    print()
    print(f"Total DPS=1: {report['total_DPS_1']}/{report['total_receipts']}")
    print(f"Total GENUINE_NOVEL_PREDICTION: {report['total_genuine_novel']}/{report['total_receipts']}")
    print()
    print(f"SUMMARY BY CONFIG:")
    print(f"  {'config':<14} {'n':>3} {'RECON':>7} {'NOVEL':>6} {'CORR':>5} {'INCR':>5} {'INDT':>5} {'DPS=1':>6} {'DPS%':>6} {'calErr':>7}")
    for cfg, s in report["summary_by_config"].items():
        cls = s["classifications"]
        cal = s["mean_calibration_error_correct"]
        cal_str = f"{cal:.3f}" if cal is not None else "  -"
        print(f"  {cfg:<14} {s['n']:>3} {cls.get('RECONSTRUCTION',0):>7} "
              f"{s['genuine_novel_count']:>6} {cls.get('CORRECT',0):>5} "
              f"{cls.get('INCORRECT',0):>5} {cls.get('INDETERMINATE',0):>5} "
              f"{s['DPS_1_count']:>6} {s['DPS_1_pct']:>5.1f}% {cal_str:>7}")
    print()
    print(f"EXIT GATE:")
    eg = report["exit_gate"]
    print(f"  Gate 1 (>= {eg['meaningful_min_novel']} genuine novel): "
          f"{'PASS' if eg['gate1_novel_count_pass'] else 'FAIL'} "
          f"(observed: {report['total_genuine_novel']})")
    print(f"  Gate 2 (>= {eg['material_advantage_pp']:.0f}pp DPS advantage over random): "
          f"{'PASS' if eg['gate2_material_advantage_pass'] else 'FAIL'}")
    if eg.get("best_treatment_config"):
        print(f"    Best treatment: {eg['best_treatment_config']} "
              f"({eg['best_treatment_dps_pct']:.1f}% DPS=1)")
        print(f"    Random control: D_random ({eg['random_dps_pct']:.1f}% DPS=1)")
    print(f"  EXIT GATE: {'PASS' if eg['exit_gate_pass'] else 'FAIL'}")
    print()
    print(f"Results: {RESULTS_OUT}")
    print(f"Hash: {h[:32]}...")


if __name__ == "__main__":
    main()
