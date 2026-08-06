#!/usr/bin/env python3
"""
verify_benchmarks.py — Independent Recomputation Verifier for Benchmarks.

Per F-044 (FAILURES.md): the one full benchmark run in
data/ledger/predictions.jsonl (composite 0.3677, 26/26 grade F) is
honestly graded BUT self-graded. The same module that generated the
predictions also scored them. No architecturally separate verifier
exists that re-derives the score from raw inputs.

This is Law 13 (independent recomputation) extended from the package
layer (BOM, mass, cost) to the benchmark layer. The same fix that
closes the desal BOM error closes the benchmark self-grading bias:
mechanical enforcement by an architecturally separate verifier.

WHAT THIS SCRIPT DOES:
1. Reads the RAW benchmark report at
   evidence/reports/compiler_benchmark_report.json
   (NOT the ledger entry — the ledger contains the self-reported
   headline number; the report contains the per-case raw data).
2. Recomputes the headline numbers from scratch:
   - overall_composite_mean = mean(cases[*].composite_feasibility)
   - expectations_satisfied_count = count where bucket_distance <= 1
   - grade_distribution = verdict-bucket histogram
3. Emits a diff between self-reported and independently-derived values.
4. Exit code 0 if all diffs == 0 (PASS); exit 1 if any diff > 0 (FAIL).

WHAT THIS SCRIPT DOES NOT DO:
- It does NOT run the compiler. It reads the report that
  run_compiler_benchmarks.py already produced.
- It does NOT see the ledger's self-reported `overall_composite_mean`
  field. It reads ONLY the raw `cases[*].composite_feasibility` values
  from the report.
- It does NOT modify the report or the ledger. It emits a diff and
  exits non-zero on disagreement.

ARCHITECTURAL SEPARATION (per PR-22):
- Generation path: scripts/run_compiler_benchmarks.py → produces
  evidence/reports/compiler_benchmark_report.json (with
  self-reported summary fields).
- Verification path: THIS SCRIPT (scripts/verify_benchmarks.py) →
  reads ONLY cases[*].composite_feasibility, recomputes summary,
  emits diff.
- The two paths share NO scoring code. The verifier imports
  verdict_from_composite and bucket_distance from benchmarks.compiler
  (the published scoring function), but recomputes the summary
  statistics (mean, count, histogram) independently.

Usage:
    python scripts/verify_benchmarks.py
    python scripts/verify_benchmarks.py --report path/to/report.json
    python scripts/verify_benchmarks.py --strict  # exit 1 on any diff

Exit codes:
    0 = all headline numbers verified (PASS)
    1 = one or more numbers fail independent recomputation (FAIL)
    2 = report file not found or invalid

Definition of done (per F-044): feed it
evidence/reports/compiler_benchmark_report.json. It must independently
recompute overall_composite_mean, expectations_satisfied count, and
grade_distribution from the per-case raw data. If the recomputed
values disagree with the report's self-reported summary, the diff is
printed and the script exits 1.
"""
import argparse
import json
import statistics
import sys
import pathlib
from collections import Counter
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import the PUBLISHED scoring functions. These are the canonical
# mapping from composite → verdict bucket. The verifier uses them to
# re-derive the verdict for each case from its raw composite_feasibility
# value, then recomputes the summary statistics from scratch.
from benchmarks.compiler import (
    verdict_from_composite,
    bucket_distance,
    BUCKET_ORDER,
    CASES,
)

DEFAULT_REPORT_PATH = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"


def load_report(report_path: pathlib.Path) -> dict:
    """Load the benchmark report JSON."""
    if not report_path.exists():
        print(f"ERROR: report not found: {report_path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {report_path}: {e}", file=sys.stderr)
        sys.exit(2)


def extract_raw_cases(report: dict) -> list[dict]:
    """Extract the raw per-case data from the report.

    The verifier reads ONLY:
      - cases[*].composite_feasibility  (the raw score)
      - cases[*].expected_verdict      (from the CASES spec, not the report)
      - cases[*].case_id                (for matching)

    The verifier does NOT read:
      - summary.expectations_satisfied   (self-reported)
      - summary.passed                  (self-reported)
      - summary.verdict                 (self-reported)
      - cases[*].expectations_satisfied (self-reported per-case)
      - cases[*].actual_verdict         (self-reported per-case)
    """
    cases = report.get("cases", [])
    if not cases:
        print("ERROR: report has no cases[] array", file=sys.stderr)
        sys.exit(2)
    return cases


def recompute_summary(cases: list[dict]) -> dict:
    """Independently recompute the summary statistics from raw case data.

    For each case:
      1. Read the raw composite_feasibility (the float the compiler produced).
      2. Re-derive the verdict using verdict_from_composite() (the published
         scoring function).
      3. Look up the expected_verdict from the CASES spec (the benchmark
         definition, NOT the report's self-reported expected_verdict).
      4. Compute bucket_distance(actual, expected) — re-derive whether
         expectations_satisfied is True (distance <= 1) or False.
      5. Aggregate: mean composite, satisfied count, grade distribution.
    """
    # Build a lookup from case_id → expected_verdict from the canonical CASES
    # spec. This ensures the verifier uses the BENCHMARK DEFINITION, not the
    # report's self-reported expected_verdict (which could have been tampered
    # with after the fact).
    expected_by_id = {c["id"]: c["expected_verdict"] for c in CASES}

    recomputed_cases = []
    composites = []
    satisfied_count = 0
    grade_counter = Counter()

    for case in cases:
        case_id = case.get("case_id") or case.get("id")
        composite = case.get("composite_feasibility")

        if composite is None:
            # The compiler failed to produce a score for this case.
            # Per the original run_one_case() logic, this counts as
            # expectations_not_satisfied.
            recomputed_cases.append({
                "case_id": case_id,
                "composite_feasibility": None,
                "recomputed_verdict": "unknown",
                "expected_verdict": expected_by_id.get(case_id, "unknown"),
                "recomputed_bucket_distance": 99,
                "recomputed_expectations_satisfied": False,
                "self_reported_verdict": case.get("actual_verdict"),
                "self_reported_expectations_satisfied": case.get("expectations_satisfied"),
            })
            grade_counter["unknown"] += 1
            continue

        # Re-derive the verdict from the raw composite using the published
        # scoring function.
        recomputed_verdict = verdict_from_composite(composite)

        # Look up the expected verdict from the canonical CASES spec.
        expected = expected_by_id.get(case_id, case.get("expected_verdict", "unknown"))

        # Re-derive the bucket distance.
        distance = bucket_distance(recomputed_verdict, expected)

        # Re-derive expectations_satisfied (per the original logic:
        # satisfied = distance <= 1).
        recomputed_satisfied = (distance <= 1)

        recomputed_cases.append({
            "case_id": case_id,
            "composite_feasibility": composite,
            "recomputed_verdict": recomputed_verdict,
            "expected_verdict": expected,
            "recomputed_bucket_distance": distance,
            "recomputed_expectations_satisfied": recomputed_satisfied,
            "self_reported_verdict": case.get("actual_verdict"),
            "self_reported_expectations_satisfied": case.get("expectations_satisfied"),
        })

        composites.append(composite)
        grade_counter[recomputed_verdict] += 1
        if recomputed_satisfied:
            satisfied_count += 1

    # Compute the headline statistics from scratch.
    overall_composite_mean = (
        round(statistics.mean(composites), 4) if composites else 0.0
    )

    return {
        "total_cases": len(cases),
        "overall_composite_mean": overall_composite_mean,
        "expectations_satisfied": satisfied_count,
        "expectations_not_satisfied": len(cases) - satisfied_count,
        "grade_distribution": dict(grade_counter),
        "cases": recomputed_cases,
    }


def diff_self_reported_vs_independent(report: dict, recomputed: dict) -> dict:
    """Compute the diff between self-reported and independently-derived values."""
    self_reported_summary = report.get("summary", {})

    self_mean = self_reported_summary.get("overall_composite_mean")
    # The original report doesn't put overall_composite_mean in summary;
    # it's in the ledger entry. We compare against the recomputed value
    # and emit a diff regardless.
    if self_mean is None:
        # Try the ledger-style field
        self_mean = report.get("overall_composite_mean")

    self_satisfied = self_reported_summary.get("expectations_satisfied")
    self_passed = self_reported_summary.get("passed")
    self_verdict = self_reported_summary.get("verdict")

    indep_mean = recomputed["overall_composite_mean"]
    indep_satisfied = recomputed["expectations_satisfied"]
    indep_not_satisfied = recomputed["expectations_not_satisfied"]
    indep_grade = recomputed["grade_distribution"]

    # Compute diffs
    mean_diff = None
    if self_mean is not None:
        mean_diff = round(indep_mean - self_mean, 4)

    satisfied_diff = None
    if self_satisfied is not None:
        satisfied_diff = indep_satisfied - self_satisfied

    # Per-case diffs: did the re-derivation disagree with the report's
    # self-reported expectations_satisfied for any case?
    per_case_disagreements = []
    for rc in recomputed["cases"]:
        if rc["self_reported_expectations_satisfied"] is not None:
            if rc["recomputed_expectations_satisfied"] != rc["self_reported_expectations_satisfied"]:
                per_case_disagreements.append({
                    "case_id": rc["case_id"],
                    "self_reported": rc["self_reported_expectations_satisfied"],
                    "independently_derived": rc["recomputed_expectations_satisfied"],
                    "self_reported_verdict": rc["self_reported_verdict"],
                    "recomputed_verdict": rc["recomputed_verdict"],
                    "expected_verdict": rc["expected_verdict"],
                })

    # Verdict-bucket disagreements: did the re-derivation produce a
    # different verdict than the report for any case?
    verdict_disagreements = []
    for rc in recomputed["cases"]:
        if rc["self_reported_verdict"] is not None:
            if rc["recomputed_verdict"] != rc["self_reported_verdict"]:
                verdict_disagreements.append({
                    "case_id": rc["case_id"],
                    "composite_feasibility": rc["composite_feasibility"],
                    "self_reported_verdict": rc["self_reported_verdict"],
                    "recomputed_verdict": rc["recomputed_verdict"],
                })

    return {
        "overall_composite_mean": {
            "self_reported": self_mean,
            "independently_derived": indep_mean,
            "diff": mean_diff,
            "match": (mean_diff == 0) if mean_diff is not None else None,
        },
        "expectations_satisfied_count": {
            "self_reported": self_satisfied,
            "independently_derived": indep_satisfied,
            "diff": satisfied_diff,
            "match": (satisfied_diff == 0) if satisfied_diff is not None else None,
        },
        "grade_distribution": {
            "self_reported": self_reported_summary.get("grade_distribution", "(not in summary)"),
            "independently_derived": indep_grade,
        },
        "per_case_disagreements": per_case_disagreements,
        "verdict_disagreements": verdict_disagreements,
        "total_disagreements": len(per_case_disagreements) + len(verdict_disagreements),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Independent recomputation verifier for benchmark scores."
    )
    parser.add_argument(
        "--report",
        type=pathlib.Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Path to benchmark report JSON (default: {DEFAULT_REPORT_PATH})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any diff (default behavior; flag is for explicitness).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of human-readable.",
    )
    args = parser.parse_args()

    report = load_report(args.report)
    cases = extract_raw_cases(report)
    recomputed = recompute_summary(cases)
    diff = diff_self_reported_vs_independent(report, recomputed)

    # Determine pass/fail
    # PASS requires:
    #   1. overall_composite_mean matches (diff == 0)
    #   2. expectations_satisfied count matches (diff == 0)
    #   3. No per-case disagreements (re-derivation didn't flip any verdict)
    #   4. No verdict-bucket disagreements
    mean_match = diff["overall_composite_mean"]["match"]
    count_match = diff["expectations_satisfied_count"]["match"]
    no_per_case_disagree = (len(diff["per_case_disagreements"]) == 0)
    no_verdict_disagree = (len(diff["verdict_disagreements"]) == 0)

    overall_pass = (
        (mean_match is True) and
        (count_match is True) and
        no_per_case_disagree and
        no_verdict_disagree
    )

    if args.json:
        output = {
            "verifier": "scripts/verify_benchmarks.py",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_path": str(args.report),
            "recomputed_summary": recomputed,
            "diff": diff,
            "overall_status": "PASS" if overall_pass else "FAIL",
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print("=" * 70)
        print("INDEPENDENT BENCHMARK RECOMPUTATION VERIFIER (PR-22 / F-044)")
        print("=" * 70)
        print(f"Report: {args.report}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print()
        print("--- Recomputed Summary (from raw cases[*].composite_feasibility) ---")
        print(f"  Total cases:              {recomputed['total_cases']}")
        print(f"  Overall composite mean:    {recomputed['overall_composite_mean']}")
        print(f"  Expectations satisfied:    {recomputed['expectations_satisfied']}")
        print(f"  Expectations not satisfied:{recomputed['expectations_not_satisfied']}")
        print(f"  Grade distribution:        {recomputed['grade_distribution']}")
        print()
        print("--- Diff: Self-Reported vs Independently-Derived ---")
        print(f"  Overall composite mean:")
        print(f"    self-reported:           {diff['overall_composite_mean']['self_reported']}")
        print(f"    independently derived:   {diff['overall_composite_mean']['independently_derived']}")
        print(f"    diff:                    {diff['overall_composite_mean']['diff']}")
        print(f"    match:                   {diff['overall_composite_mean']['match']}")
        print(f"  Expectations satisfied count:")
        print(f"    self-reported:           {diff['expectations_satisfied_count']['self_reported']}")
        print(f"    independently derived:   {diff['expectations_satisfied_count']['independently_derived']}")
        print(f"    diff:                    {diff['expectations_satisfied_count']['diff']}")
        print(f"    match:                   {diff['expectations_satisfied_count']['match']}")
        print()
        print(f"  Per-case disagreements:    {len(diff['per_case_disagreements'])}")
        for d in diff["per_case_disagreements"]:
            print(f"    - {d['case_id']}: self={d['self_reported']}, indep={d['independently_derived']}")
        print(f"  Verdict-bucket disagreements: {len(diff['verdict_disagreements'])}")
        for d in diff["verdict_disagreements"]:
            print(f"    - {d['case_id']}: composite={d['composite_feasibility']}, "
                  f"self={d['self_reported_verdict']}, indep={d['recomputed_verdict']}")
        print()
        print("=" * 70)
        if overall_pass:
            print("OVERALL STATUS: PASS")
            print("  All headline numbers verified by independent recomputation.")
            print("  The benchmark report's self-reported summary matches the")
            print("  independently-derived summary. The benchmark is not self-graded")
            print("  in any way that biases the headline numbers.")
        else:
            print("OVERALL STATUS: FAIL")
            print("  One or more headline numbers fail independent recomputation.")
            print("  The benchmark report's self-reported summary DISAGREES with")
            print("  the independently-derived summary. Per PR-22, the benchmark_run")
            print("  entry MUST NOT enter the ledger until this is resolved.")
        print("=" * 70)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
