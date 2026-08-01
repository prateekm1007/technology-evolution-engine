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
    """Compile a single case and compare to expected verdict.

    Per CTO review #3: the result key is 'expectations_satisfied', NOT
    'pass'. 'PASS' would imply correctness; 'expectations_satisfied'
    is honest about what was actually tested (did the output match
    what the benchmarker expected?).
    """
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
                "category": case.get("category"),
                "expected_verdict": case["expected_verdict"],
                "actual_verdict": "unknown",
                "composite_feasibility": None,
                "duration_s": duration,
                "expectations_satisfied": False,
                "reason": "composite_feasibility_baseline is None — "
                          "compiler did not produce a feasibility score",
                "chain_summary": chain,
            }
        actual = verdict_from_composite(composite)
        dist = bucket_distance(actual, case["expected_verdict"])
        satisfied = dist <= 1  # exact match OR adjacent bucket
        return {
            "case_id": case["id"],
            "case_name": case["name"],
            "category": case.get("category"),
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": actual,
            "composite_feasibility": round(composite, 4),
            "bucket_distance_from_expected": dist,
            "duration_s": duration,
            "expectations_satisfied": satisfied,
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
            "category": case.get("category"),
            "expected_verdict": case["expected_verdict"],
            "actual_verdict": "error",
            "composite_feasibility": None,
            "duration_s": duration,
            "expectations_satisfied": False,
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
    satisfied = 0
    not_satisfied = 0
    for case in CASES:
        print(f"--- {case['name']} (category: {case.get('category','?')}, expected: {case['expected_verdict']}) ---")
        r = run_one_case(compiler, case)
        results.append(r)
        if r["expectations_satisfied"]:
            satisfied += 1
            print(f"  EXPECTATIONS_SATISFIED — actual: {r['actual_verdict']} "
                  f"(composite={r.get('composite_feasibility')}, "
                  f"distance={r.get('bucket_distance_from_expected', '?')})")
        else:
            not_satisfied += 1
            print(f"  EXPECTATIONS_NOT_SATISFIED — actual: {r['actual_verdict']}, "
                  f"expected: {r['expected_verdict']}, "
                  f"reason: {r.get('reason', 'bucket_distance > 1')}")
        print()

    # Build the report.
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": (
            "Live end-to-end compile of reference problems through the "
            "11-layer invention compiler. For each case, the composite "
            "feasibility score from Layer 5 (simulation) is mapped to a "
            "verdict bucket per INVENTION_COMPILER.md. "
            "expectations_satisfied = verdict matches expected OR is within "
            "one bucket; otherwise expectations_not_satisfied."
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
            "expectations_satisfied": satisfied,
            "expectations_not_satisfied": not_satisfied,
            # Keep 'passed' as an alias for backwards-compat with
            # tests that read it, but the canonical field is
            # expectations_satisfied.
            "passed": satisfied,
            "verdict": "EXPECTATIONS_SATISFIED" if not_satisfied == 0
                       else "EXPECTATIONS_NOT_SATISFIED",
        },
        "epistemic_caveat": (
            "EXPECTATIONS SATISFIED IS NOT THE SAME AS CORRECTNESS. "
            "This benchmark suite tests whether the compiler produced the "
            "verdict the benchmarker expected. It does NOT test whether "
            "the compiler produced a verdict that matches reality. If we "
            "repeatedly tune the scoring system until it produces the "
            "answers we expected all along, we risk building a machine "
            "that reproduces our beliefs rather than discovers new truths. "
            "Real correctness requires the Experimentation layer to close "
            "the loop: predict -> build -> observe -> learn. Until that "
            "loop exists on at least one real invention, every "
            "'expectations_satisfied' verdict here is provisional. "
            "Furthermore, the composite feasibility score is produced by "
            "knowledge modules at the 'encode' stage of the "
            "encode->reason->simulate->discover spectrum — they store "
            "laws and pathways as structured data but do NOT reason over "
            "them, simulate them, or discover new ones."
        ),
        "honesty_note": (
            "A expectations_satisfied verdict means the compiler ran "
            "end-to-end and produced a defensible chain of reasoning, "
            "not that the compiler has determined whether the invention "
            "is feasible in the real world. See epistemic_caveat above."
        ),
        "cases": results,
        "next_actions": [
            "Move domain modules up the encode->reason->simulate->discover "
            "spectrum. Currently all at 'encode' — they store laws but "
            "do not reason over them.",
            "Implement the Experimentation layer (predict -> build -> "
            "observe -> learn) on at least one real invention. Until "
            "that loop exists, every verdict is provisional.",
            "Add a Creation-category benchmark case (a complete 11-layer "
            "blueprint verified by an actual build). The system does not "
            "honestly claim to be an invention compiler until at least "
            "one Creation case exists.",
            "Resist the temptation to tune complexity penalties to flip "
            "failing cases to expectations_satisfied without a "
            "corresponding scientific justification (a real law encoded, "
            "a real pathway added, a real counterfactual documented).",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print("=" * 60)
    print(f"BENCHMARK SUITE COMPLETE: {satisfied}/{len(results)} expectations_satisfied, "
          f"{not_satisfied} not_satisfied")
    print(f"  (Note: expectations_satisfied ≠ correctness. See epistemic_caveat in report.)")
    print(f"Report: {REPORT_PATH}")
    print("=" * 60)
    return 0 if not_satisfied == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
