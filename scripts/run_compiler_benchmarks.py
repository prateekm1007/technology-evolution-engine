#!/usr/bin/env python3
"""
Run the 5-benchmark compiler suite.

For each case in benchmarks/compiler/__init__.py, this script:
  1. Loads the civilization graph.
  2. Compiles the case through all 11 layers of the invention compiler.
  3. Reads the composite feasibility from the simulation step (Layer 5).
  4. Maps the composite to a verdict bucket per INVENTION_COMPILER.md.
  5. Compares the verdict to the expected verdict.
  6. Reports PASS if verdict matches OR is within one bucket; FAIL otherwise.

Output: evidence/reports/compiler_benchmark_report.json

Usage:
    python scripts/run_compiler_benchmarks.py
"""
import json
import sys
import time
import traceback
from datetime import datetime, timezone
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.compiler import CASES, verdict_from_composite, bucket_distance
from invention_compiler.orchestrator import InventionCompiler


REPORT_PATH = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"


def run_one_case(compiler, case):
    """Compile a single case and compare to expected verdict."""
    start = time.time()
    try:
        result = compiler.compile(case["problem"])
        duration = round(time.time() - start, 3)
        # The composite feasibility is in the chain_summary.
        chain = result.get("chain_summary", {})
        composite = chain.get("composite_feasibility_baseline")
        # If None, try the simulation layer's baseline.
        if composite is None:
            sim = result.get("layers", {}).get(5, {})
            composite = sim.get("evidence", {}).get("baseline_composite")
        if composite is None:
            return {
                "case_id": case["id"],
                "case_name": case["name"],
                "expected_verdict": case["expected_verdict"],
                "actual_verdict": "unknown",
                "composite_feasibility": None,
                "duration_s": duration,
                "pass": False,
                "reason": "composite_feasibility_baseline is None — "
                          "compiler did not produce a feasibility score",
                "chain_summary": chain,
            }
        actual = verdict_from_composite(composite)
        dist = bucket_distance(actual, case["expected_verdict"])
        passed = dist <= 1  # exact match OR adjacent bucket
        return {
            "case_id": case["id"],
            "case_name": case["name"],
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": actual,
            "composite_feasibility": round(composite, 4),
            "bucket_distance_from_expected": dist,
            "duration_s": duration,
            "pass": passed,
            "rationale": case.get("rationale"),
            "chain_summary": chain,
            # Include the full layer 0 + layer 10 for inspection
            "layer_0": result["layers"][0],
            "layer_10_blueprint": result["layers"][10].get("blueprint"),
            "layer_10_technical_risks": result["layers"][10].get("technical_risks"),
            "layer_10_commercial_risks": result["layers"][10].get("commercial_risks"),
        }
    except Exception as e:
        duration = round(time.time() - start, 3)
        return {
            "case_id": case["id"],
            "case_name": case["name"],
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": "error",
            "composite_feasibility": None,
            "duration_s": duration,
            "pass": False,
            "reason": f"{type(e).__name__}: {e}",
            "trace": traceback.format_exc(),
        }


def main():
    print("=" * 60)
    print("INVENTION COMPILER — 5-BENCHMARK SUITE")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Load graph.
    graph_path = ROOT / "data" / "civilization_graph.json"
    with open(graph_path) as f:
        graph = json.load(f)

    compiler = InventionCompiler(graph=graph)
    print(f"Compiler ready. Graph: {len(graph.get('nodes', []))} nodes")
    print()

    results = []
    passes = 0
    fails = 0
    for case in CASES:
        print(f"--- {case['name']} (expected: {case['expected_verdict']}) ---")
        r = run_one_case(compiler, case)
        results.append(r)
        if r["pass"]:
            passes += 1
            print(f"  PASS — actual: {r['actual_verdict']} "
                  f"(composite={r.get('composite_feasibility')}, "
                  f"distance={r.get('bucket_distance_from_expected', '?')})")
        else:
            fails += 1
            print(f"  FAIL — actual: {r['actual_verdict']}, "
                  f"expected: {r['expected_verdict']}, "
                  f"reason: {r.get('reason', 'bucket_distance > 1')}")
        print()

    # Build the report.
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": (
            "Live end-to-end compile of 5 reference problems through the "
            "11-layer invention compiler. For each case, the composite "
            "feasibility score from Layer 5 (simulation) is mapped to a "
            "verdict bucket per INVENTION_COMPILER.md. PASS = verdict "
            "matches expected OR is within one bucket; FAIL = more than "
            "one bucket apart."
        ),
        "verdict_buckets": {
            "feasible": ">=0.75",
            "potentially_feasible": "0.55-0.75",
            "partially_feasible": "0.40-0.55",
            "uncertain": "0.25-0.40",
            "unknown": "<0.25",
        },
        "summary": {
            "total_cases": len(results),
            "passed": passes,
            "failed": fails,
            "verdict": "PASS" if fails == 0 else "FAIL",
        },
        "cases": results,
        "honesty_note": (
            "The composite feasibility score is produced by keyword-"
            "matching modules, NOT by scientific engines (per the CTO "
            "review of commit a3d167d). Until the domain modules are "
            "upgraded to true scientific engines with explicit models "
            "+ empirical validation + reproducible results, these "
            "verdicts should be treated as architectural smoke tests, "
            "not as scientific assessments. A PASS means 'the compiler "
            "ran end-to-end and produced a defensible chain of "
            "reasoning', NOT 'the compiler has determined whether the "
            "invention is feasible in the real world.'"
        ),
        "next_actions": [
            "Upgrade physics_module to a real physics_engine with "
            "conservation laws, thermodynamics, fluid mechanics, EM, "
            "optics, mechanics, materials science, differential "
            "equations, optimization, and dimensional analysis.",
            "Upgrade chemistry_module to a real chemistry_engine with "
            "reaction pathways, molecular structure models, kinetics, "
            "thermodynamics, equilibrium models, electrochemistry, "
            "materials properties.",
            "Upgrade biology_module, economics_module, mathematics_module "
            "to real engines.",
            "Implement information_theory_module, thermodynamics_module, "
            "control_theory_module (currently stubbed in Layer 1).",
            "After each upgrade, re-run this benchmark suite and verify "
            "the verdict for the affected cases moves CLOSER to the "
            "expected verdict, not further away.",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print("=" * 60)
    print(f"BENCHMARK SUITE COMPLETE: {passes}/{len(results)} PASS, "
          f"{fails} FAIL")
    print(f"Report: {REPORT_PATH}")
    print("=" * 60)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
