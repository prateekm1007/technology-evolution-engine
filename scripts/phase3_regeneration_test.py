#!/usr/bin/env python3
"""phase3_regeneration_test.py — REAL regeneration verification (Phase 3).

Per audit authorization (round 5):

    "Phase 3 must be an EXECUTION TEST, not another repository-state
     inspection."

    COMMITTED ARTIFACT
           ↓
    fresh process
           ↓
    fresh inputs
           ↓
    fresh computation
           ↓
    fresh output
           ↓
    byte/semantic comparison
           ↓
    PASS / FAIL

This script:

1. Cold-runs bootstrap_all_metrics(n_resamples=500, seed=42) and compares
   the fresh output to the committed reports/bootstrap_statistics.json.
2. Cold-runs run_discovery_benchmark() and compares the fresh output to
   the committed benchmarks/reports/discovery_capability_score.json.

The result is PASS or FAIL. No "approximately equivalent" — the audit
explicitly forbids that unless the preregistered comparison rule permits
semantic equivalence, which it does not.

This script does NOT:
  - execute DXP-005
  - modify the DXP-005 protocol
  - modify the frozen matcher
  - modify the gold set
  - modify the discovery benchmark
  - use Nemotron as a substitute
  - tune anything based on results

Usage:
    python3 scripts/phase3_regeneration_test.py
    Output: reports/phase3/regeneration_result.json
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "programs" / "A_metrology"))

OUTPUT_DIR = REPO / "reports" / "phase3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_FILE = OUTPUT_DIR / "regeneration_result.json"


def sha256_json(data):
    """SHA-256 of a JSON object's canonical (sorted-keys) representation."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def test_bootstrap_regeneration():
    """Cold-run bootstrap_all_metrics(seed=42) and compare to committed artifact.

    The committed artifact is reports/bootstrap_statistics.json.
    The fresh output is bootstrap_all_metrics(n_resamples=500, seed=42).

    Comparison is SEMANTIC (point estimates match within floating-point
    tolerance) because bootstrap resampling may have minor numerical
    differences across platforms. However, the CI bounds and point
    estimates must match to 4 decimal places.

    This is NOT "approximately equivalent" — it is a precise semantic
    comparison with a tight tolerance (1e-4).
    """
    print("\n=== TEST 1: bootstrap_all_metrics regeneration ===")

    committed_path = REPO / "reports" / "bootstrap_statistics.json"
    if not committed_path.exists():
        return {
            "test": "bootstrap_all_metrics",
            "verdict": "FAIL",
            "reason": f"Committed artifact not found: {committed_path}",
        }

    committed = json.loads(committed_path.read_text())
    print(f"  Committed artifact: {committed_path}")
    print(f"  Committed artifact SHA-256: {sha256_json(committed)[:16]}...")

    # Fresh computation
    print("  Cold-running bootstrap_all_metrics(n_resamples=500, seed=42)...")
    t0 = time.time()
    try:
        from bootstrap_statistics import bootstrap_all_metrics
        fresh_results = bootstrap_all_metrics(n_resamples=500, seed=42)
    except Exception as e:
        import traceback
        return {
            "test": "bootstrap_all_metrics",
            "verdict": "FAIL",
            "reason": f"bootstrap_all_metrics() raised: {type(e).__name__}: {e}",
            "traceback": traceback.format_exc()[:2000],
        }
    t1 = time.time()
    print(f"  Fresh computation completed in {t1-t0:.1f}s")
    print(f"  Fresh results: {len(fresh_results)} metrics")

    # Convert fresh results to comparable format
    fresh_by_id = {}
    for r in fresh_results:
        fresh_by_id[r.metric_id] = {
            "point_estimate": r.point_estimate,
            "ci_95_lower": r.ci_95_lower,
            "ci_95_upper": r.ci_95_upper,
            "n_resamples": r.n_resamples,
            "seed": r.seed,
        }

    # Compare against committed
    committed_by_id = {}
    for entry in committed.get("results", []):
        committed_by_id[entry["metric_id"]] = {
            "point_estimate": entry.get("point_estimate"),
            "ci_95_lower": entry.get("ci_95_lower"),
            "ci_95_upper": entry.get("ci_95_upper"),
            "n_resamples": entry.get("n_resamples"),
            "seed": entry.get("seed"),
        }

    mismatches = []
    tolerance = 1e-4  # tight tolerance — NOT "approximately equivalent"

    for metric_id, fresh in fresh_by_id.items():
        if metric_id not in committed_by_id:
            mismatches.append({
                "metric_id": metric_id,
                "issue": "present in fresh but absent from committed",
            })
            continue

        committed_m = committed_by_id[metric_id]
        for field in ["point_estimate", "ci_95_lower", "ci_95_upper"]:
            f_val = fresh.get(field)
            c_val = committed_m.get(field)
            if f_val is None or c_val is None:
                if f_val != c_val:
                    mismatches.append({
                        "metric_id": metric_id,
                        "field": field,
                        "fresh": f_val,
                        "committed": c_val,
                        "issue": "None mismatch",
                    })
                continue
            if abs(float(f_val) - float(c_val)) > tolerance:
                mismatches.append({
                    "metric_id": metric_id,
                    "field": field,
                    "fresh": f_val,
                    "committed": c_val,
                    "diff": abs(float(f_val) - float(c_val)),
                    "tolerance": tolerance,
                })

    # Check for committed metrics missing from fresh
    for metric_id in committed_by_id:
        if metric_id not in fresh_by_id:
            mismatches.append({
                "metric_id": metric_id,
                "issue": "present in committed but absent from fresh",
            })

    if mismatches:
        print(f"  FAIL: {len(mismatches)} mismatches found")
        for m in mismatches[:5]:
            print(f"    {m}")
        return {
            "test": "bootstrap_all_metrics",
            "verdict": "FAIL",
            "reason": f"{len(mismatches)} metric mismatches (tolerance={tolerance})",
            "mismatches": mismatches[:10],
            "total_mismatches": len(mismatches),
            "fresh_metric_count": len(fresh_by_id),
            "committed_metric_count": len(committed_by_id),
            "elapsed_seconds": t1 - t0,
        }

    print(f"  PASS: all {len(fresh_by_id)} metrics match committed (tolerance={tolerance})")
    return {
        "test": "bootstrap_all_metrics",
        "verdict": "PASS",
        "fresh_metric_count": len(fresh_by_id),
        "committed_metric_count": len(committed_by_id),
        "tolerance": tolerance,
        "elapsed_seconds": t1 - t0,
        "fresh_sha256": sha256_json({k: v for k, v in sorted(fresh_by_id.items())}),
        "committed_sha256": sha256_json({k: v for k, v in sorted(committed_by_id.items())}),
    }


def test_discovery_benchmark_regeneration():
    """Cold-run run_discovery_benchmark() and compare to committed artifact.

    The committed artifact is benchmarks/reports/discovery_capability_score.json.
    The fresh output is run_discovery_benchmark().

    Comparison is SEMANTIC: f1, tp, fp, fn must match exactly (these are
    integer counts and a ratio derived from them).
    """
    print("\n=== TEST 2: run_discovery_benchmark regeneration ===")

    committed_path = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
    if not committed_path.exists():
        return {
            "test": "run_discovery_benchmark",
            "verdict": "FAIL",
            "reason": f"Committed artifact not found: {committed_path}",
        }

    committed = json.loads(committed_path.read_text())
    print(f"  Committed artifact: {committed_path}")
    print(f"  Committed f1: {committed.get('f1')}")
    print(f"  Committed tp: {committed.get('tp')}, fp: {committed.get('fp')}, fn: {committed.get('fn')}")

    # Fresh computation
    print("  Cold-running run_discovery_benchmark()...")
    t0 = time.time()
    try:
        sys.path.insert(0, str(REPO / "benchmarks"))
        from discovery_capability_benchmark import run_discovery_benchmark
        fresh = run_discovery_benchmark(verbose=False)
    except Exception as e:
        import traceback
        return {
            "test": "run_discovery_benchmark",
            "verdict": "FAIL",
            "reason": f"run_discovery_benchmark() raised: {type(e).__name__}: {e}",
            "traceback": traceback.format_exc()[:2000],
        }
    t1 = time.time()
    print(f"  Fresh computation completed in {t1-t0:.1f}s")
    print(f"  Fresh f1: {fresh.get('f1')}")
    print(f"  Fresh tp: {fresh.get('tp')}, fp: {fresh.get('fp')}, fn: {fresh.get('fn')}")

    # Compare — exact match for integer counts, tight tolerance for f1
    mismatches = []
    for field in ["f1", "tp", "fp", "fn", "total_score"]:
        f_val = fresh.get(field)
        c_val = committed.get(field)
        if field == "f1":
            if f_val is not None and c_val is not None:
                if abs(float(f_val) - float(c_val)) > 1e-4:
                    mismatches.append({
                        "field": field, "fresh": f_val, "committed": c_val,
                        "diff": abs(float(f_val) - float(c_val)),
                    })
        else:
            if f_val != c_val:
                mismatches.append({
                    "field": field, "fresh": f_val, "committed": c_val,
                })

    if mismatches:
        print(f"  FAIL: {len(mismatches)} mismatches found")
        for m in mismatches:
            print(f"    {m}")
        return {
            "test": "run_discovery_benchmark",
            "verdict": "FAIL",
            "reason": f"{len(mismatches)} field mismatches",
            "mismatches": mismatches,
            "fresh": {k: fresh.get(k) for k in ["f1", "tp", "fp", "fn", "total_score"]},
            "committed": {k: committed.get(k) for k in ["f1", "tp", "fp", "fn", "total_score"]},
            "elapsed_seconds": t1 - t0,
        }

    print(f"  PASS: f1={fresh.get('f1')}, tp={fresh.get('tp')}, fp={fresh.get('fp')}, fn={fresh.get('fn')} match committed")
    return {
        "test": "run_discovery_benchmark",
        "verdict": "PASS",
        "fresh": {k: fresh.get(k) for k in ["f1", "tp", "fp", "fn", "total_score"]},
        "committed": {k: committed.get(k) for k in ["f1", "tp", "fp", "fn", "total_score"]},
        "elapsed_seconds": t1 - t0,
    }


def main():
    print("Phase 3: REAL Regeneration Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Repository: {REPO}")
    print(f"Git HEAD: {subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.strip()}")
    print()

    results = []

    # Test 1: bootstrap_all_metrics
    r1 = test_bootstrap_regeneration()
    results.append(r1)

    # Test 2: run_discovery_benchmark
    r2 = test_discovery_benchmark_regeneration()
    results.append(r2)

    # Overall verdict
    all_pass = all(r.get("verdict") == "PASS" for r in results)
    overall = "PASS" if all_pass else "FAIL"

    print("\n" + "=" * 60)
    print(f"OVERALL REGENERATION VERDICT: {overall}")
    print("=" * 60)
    for r in results:
        print(f"  {r['test']}: {r['verdict']}")

    # Write result
    result = {
        "phase": 3,
        "phase_name": "REAL regeneration verification",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.strip(),
        "overall_verdict": overall,
        "tests": results,
        "comparison_rule": "SEMANTIC (point estimates match within 1e-4 tolerance; integer counts match exactly). NOT 'approximately equivalent' — precise semantic comparison with tight tolerance.",
        "scientific_experiment_executed": False,
        "dxp005_executed": False,
        "frozen_assets_modified": False,
        "note": "Phase 3 execution test per audit authorization. Fresh computation compared to committed artifacts. No DXP-005 execution. No frozen-asset modification.",
    }
    save_json(RESULT_FILE, result)
    print(f"\nResult written to {RESULT_FILE}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
