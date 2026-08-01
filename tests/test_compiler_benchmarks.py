"""
Tests for the 5-benchmark compiler suite (CTO-mandated).

Per ANTI_ENTROPY.md rule 1 (tests first), these tests lock the
benchmark contract:
  - The suite has exactly 5 cases.
  - Each case has the required fields (id, name, expected_verdict,
    rationale, problem).
  - The verdict bucket mapping is correct.
  - The bucket_distance function is correct.
  - The benchmark runner exists and produces the report.
  - The report's honesty_note is present and explicit about the
    keyword-matching limitation.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.compiler import (
    CASES, verdict_from_composite, bucket_distance, BUCKET_ORDER,
)


def test_suite_has_5_cases():
    """CTO-mandated: exactly 5 cases."""
    assert len(CASES) == 5


def test_each_case_has_required_fields():
    """Each case must carry id, name, expected_verdict, rationale,
    and a problem dict with the Layer 0 schema."""
    required_case_fields = {"id", "name", "expected_verdict", "rationale",
                            "problem"}
    required_problem_fields = {"problem", "domain", "motivation",
                               "market", "constraints", "time_horizon"}
    for case in CASES:
        for f in required_case_fields:
            assert f in case, f"case {case.get('id')} missing field {f}"
        for f in required_problem_fields:
            assert f in case["problem"], \
                f"case {case['id']} problem missing field {f}"


def test_expected_verdicts_are_valid_buckets():
    """Each case's expected_verdict must be one of the 5 buckets."""
    for case in CASES:
        assert case["expected_verdict"] in BUCKET_ORDER, \
            f"case {case['id']} has invalid expected_verdict " \
            f"{case['expected_verdict']!r}"


def test_each_expected_verdict_is_distinct():
    """The 5 cases should cover the 5 different verdict buckets —
    that's the point of having 5 cases."""
    verdicts = [c["expected_verdict"] for c in CASES]
    assert len(set(verdicts)) == 5, \
        f"expected 5 distinct verdicts, got {verdicts}"


def test_verdict_from_composite_buckets():
    """The composite-to-verdict mapping must match INVENTION_COMPILER.md."""
    assert verdict_from_composite(0.80) == "feasible"
    assert verdict_from_composite(0.75) == "feasible"
    assert verdict_from_composite(0.74) == "potentially_feasible"
    assert verdict_from_composite(0.55) == "potentially_feasible"
    assert verdict_from_composite(0.54) == "partially_feasible"
    assert verdict_from_composite(0.40) == "partially_feasible"
    assert verdict_from_composite(0.39) == "uncertain"
    assert verdict_from_composite(0.25) == "uncertain"
    assert verdict_from_composite(0.24) == "unknown"
    assert verdict_from_composite(0.0) == "unknown"


def test_bucket_distance_zero_for_same():
    assert bucket_distance("feasible", "feasible") == 0
    assert bucket_distance("unknown", "unknown") == 0


def test_bucket_distance_one_for_adjacent():
    assert bucket_distance("feasible", "potentially_feasible") == 1
    assert bucket_distance("potentially_feasible", "partially_feasible") == 1
    assert bucket_distance("partially_feasible", "uncertain") == 1
    assert bucket_distance("uncertain", "unknown") == 1


def test_bucket_distance_two_for_two_apart():
    assert bucket_distance("feasible", "partially_feasible") == 2
    assert bucket_distance("potentially_feasible", "uncertain") == 2


def test_bucket_distance_max_for_extremes():
    assert bucket_distance("feasible", "unknown") == 4


def test_benchmark_runner_exists():
    """scripts/run_compiler_benchmarks.py must exist and be executable."""
    p = ROOT / "scripts" / "run_compiler_benchmarks.py"
    assert p.exists(), "benchmark runner script missing"


def test_benchmark_report_honesty_note_present():
    """The benchmark report MUST carry the honesty_note that explains
    the keyword-matching limitation. Per INVENTION_COMPILER.md, the
    CTO has explicitly NOT approved the scientific claims — the report
    must say so explicitly, not bury the caveat."""
    # Run the suite if the report doesn't exist.
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    assert "honesty_note" in report, \
        "benchmark report missing honesty_note — CTO review requires it"
    note = report["honesty_note"].lower()
    assert "keyword" in note or "module" in note, \
        "honesty_note must explicitly say the modules are keyword-matching, " \
        "not scientific engines"
    assert "smoke test" in note or "not as scientific" in note, \
        "honesty_note must explicitly say PASS means 'smoke test', not " \
        "'scientific assessment'"


def test_benchmark_report_carries_next_actions():
    """The benchmark report MUST carry next_actions, per the CTO's
    directive that the engineering team knows what to upgrade next."""
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    assert "next_actions" in report
    assert len(report["next_actions"]) >= 3, \
        "next_actions must list at least 3 upgrades"


def test_benchmark_report_cases_match_suite():
    """The benchmark report's cases must match the suite's cases."""
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/run_compiler_benchmarks.py"],
            cwd=str(ROOT), check=True,
        )
    report = json.loads(report_path.read_text())
    assert len(report["cases"]) == 5
    for i, case in enumerate(CASES):
        assert report["cases"][i]["case_id"] == case["id"]
        assert report["cases"][i]["expected_verdict"] == case["expected_verdict"]
