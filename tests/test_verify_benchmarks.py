"""
Tests for the independent benchmark recomputation verifier (PR-22 / F-044).

Per ANTI_ENTROPY.md rule 1 (tests first), these tests lock the
benchmark verifier contract:
  1. It can load a valid benchmark report.
  2. It independently recomputes overall_composite_mean from raw cases.
  3. It independently recomputes expectations_satisfied count from raw cases.
  4. It detects when self-reported mean differs from independent mean.
  5. It detects when self-reported satisfied count differs from independent.
  6. It detects per-case verdict disagreements.
  7. It returns exit 0 on PASS, exit 1 on FAIL.
  8. It does NOT see the ledger's self-reported overall_composite_mean
     field — only the report's raw per-case data.

Per F-044 / PR-22: a benchmark score computed by the generation path
is forbidden from being the headline score. The headline score MUST
come from an architecturally separate verifier.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import the verifier functions directly so we can test them in-process
from scripts.verify_benchmarks import (
    load_report,
    extract_raw_cases,
    recompute_summary,
    diff_self_reported_vs_independent,
)


# ----------------------------------------------------------------------
# Fixtures: synthetic benchmark reports for testing
# ----------------------------------------------------------------------

def _make_case(case_id, composite, expected="feasible", actual=None, satisfied=None):
    """Build a synthetic benchmark case dict."""
    if actual is None:
        from benchmarks.compiler import verdict_from_composite
        actual = verdict_from_composite(composite)
    if satisfied is None:
        from benchmarks.compiler import bucket_distance
        satisfied = bucket_distance(actual, expected) <= 1
    return {
        "case_id": case_id,
        "case_name": case_id.replace("_", " ").title(),
        "category": "reconstruction",
        "expected_verdict": expected,
        "actual_verdict": actual,
        "composite_feasibility": composite,
        "bucket_distance_from_expected": 0 if satisfied else 2,
        "duration_s": 0.1,
        "expectations_satisfied": satisfied,
    }


def _make_report(cases, summary_overrides=None):
    """Build a synthetic benchmark report."""
    from benchmarks.compiler import verdict_from_composite
    from collections import Counter
    import statistics

    satisfied = sum(1 for c in cases if c.get("expectations_satisfied"))
    composites = [c["composite_feasibility"] for c in cases
                  if c.get("composite_feasibility") is not None]
    summary = {
        "total_cases": len(cases),
        "expectations_satisfied": satisfied,
        "expectations_not_satisfied": len(cases) - satisfied,
        "passed": satisfied,
        "overall_composite_mean": round(statistics.mean(composites), 4) if composites else 0.0,
        "grade_distribution": dict(Counter(
            verdict_from_composite(c) for c in composites
        )),
        "verdict": "EXPECTATIONS_SATISFIED" if satisfied == len(cases)
                   else "EXPECTATIONS_NOT_SATISFIED",
    }
    if summary_overrides:
        summary.update(summary_overrides)
    return {
        "generated_at": "2026-08-04T00:00:00+00:00",
        "method": "synthetic test report",
        "summary": summary,
        "cases": cases,
    }


# ----------------------------------------------------------------------
# 1. Loading and extraction
# ----------------------------------------------------------------------

def test_load_report_valid_json(tmp_path):
    """The verifier can load a valid benchmark report JSON."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_make_report([])))
    report = load_report(report_path)
    assert isinstance(report, dict)
    assert "cases" in report


def test_load_report_missing_file_exits_2(tmp_path):
    """A missing report file causes exit code 2."""
    with pytest.raises(SystemExit) as exc_info:
        load_report(tmp_path / "nonexistent.json")
    assert exc_info.value.code == 2


def test_extract_raw_cases_returns_cases_list():
    """extract_raw_cases returns the cases[] array from the report."""
    cases = [_make_case("case_001", 0.8), _make_case("case_002", 0.5)]
    report = _make_report(cases)
    raw = extract_raw_cases(report)
    assert len(raw) == 2
    assert raw[0]["case_id"] == "case_001"


def test_extract_raw_cases_empty_exits_2():
    """A report with no cases[] causes exit code 2."""
    with pytest.raises(SystemExit) as exc_info:
        extract_raw_cases({"summary": {}})
    assert exc_info.value.code == 2


# ----------------------------------------------------------------------
# 2. Independent recomputation
# ----------------------------------------------------------------------

def test_recompute_summary_mean_matches():
    """The recomputed mean matches the manual computation."""
    cases = [
        _make_case("test_001", 0.80, expected="feasible"),
        _make_case("test_002", 0.30, expected="uncertain"),
        _make_case("test_003", 0.60, expected="potentially_feasible"),
    ]
    recomputed = recompute_summary(cases)
    # Mean of [0.80, 0.30, 0.60] = 0.5666... → rounded to 0.5667
    assert recomputed["overall_composite_mean"] == 0.5667
    assert recomputed["total_cases"] == 3


def test_recompute_summary_satisfied_count():
    """The recomputed satisfied count uses the published verdict_from_composite.

    Uses synthetic case IDs (test_*) that are NOT in the canonical
    CASES spec, so the verifier falls back to the case's expected_verdict
    field rather than looking it up in CASES. This isolates the test
    from the real benchmark definitions.
    """
    # Case 1: composite 0.80 → "feasible"; expected "feasible"; distance 0; satisfied
    # Case 2: composite 0.30 → "uncertain"; expected "feasible"; distance 3; not satisfied
    # Case 3: composite 0.60 → "potentially_feasible"; expected "feasible"; distance 1; satisfied
    cases = [
        _make_case("test_case_001", 0.80, expected="feasible"),
        _make_case("test_case_002", 0.30, expected="feasible"),
        _make_case("test_case_003", 0.60, expected="feasible"),
    ]
    recomputed = recompute_summary(cases)
    assert recomputed["expectations_satisfied"] == 2
    assert recomputed["expectations_not_satisfied"] == 1


def test_recompute_summary_grade_distribution():
    """The recomputed grade_distribution is a histogram of verdict buckets."""
    cases = [
        _make_case("case_001", 0.80),  # feasible
        _make_case("case_002", 0.60),  # potentially_feasible
        _make_case("case_003", 0.45),  # partially_feasible
        _make_case("case_004", 0.30),  # uncertain
        _make_case("case_005", 0.10),  # unknown
    ]
    recomputed = recompute_summary(cases)
    assert recomputed["grade_distribution"] == {
        "feasible": 1,
        "potentially_feasible": 1,
        "partially_feasible": 1,
        "uncertain": 1,
        "unknown": 1,
    }


def test_recompute_summary_handles_none_composite():
    """A case with composite_feasibility=None counts as not satisfied."""
    cases = [
        {"case_id": "case_001", "composite_feasibility": None,
         "actual_verdict": "unknown", "expectations_satisfied": False},
        _make_case("case_002", 0.80, expected="feasible"),
    ]
    recomputed = recompute_summary(cases)
    assert recomputed["expectations_satisfied"] == 1
    assert recomputed["expectations_not_satisfied"] == 1
    # Mean is computed only from non-None composites
    assert recomputed["overall_composite_mean"] == 0.8


# ----------------------------------------------------------------------
# 3. Diff detection — the core of PR-22
# ----------------------------------------------------------------------

def test_diff_passes_when_self_reported_matches_independent():
    """When self-reported values match independent recomputation, diff is 0."""
    cases = [_make_case("case_001", 0.80, expected="feasible")]
    report = _make_report(cases)
    recomputed = recompute_summary(extract_raw_cases(report))
    diff = diff_self_reported_vs_independent(report, recomputed)
    assert diff["overall_composite_mean"]["match"] is True
    assert diff["overall_composite_mean"]["diff"] == 0.0
    assert diff["expectations_satisfied_count"]["match"] is True
    assert diff["expectations_satisfied_count"]["diff"] == 0
    assert len(diff["per_case_disagreements"]) == 0
    assert len(diff["verdict_disagreements"]) == 0


def test_diff_detects_inflated_mean():
    """Per PR-22: a self-reported mean HIGHER than independent mean is BLOCKED.

    This is the core anti-self-grading-bias test. If the generation path
    reports a higher mean than the independent recomputation, the verifier
    catches it.
    """
    cases = [_make_case("case_001", 0.50, expected="feasible")]
    report = _make_report(cases, summary_overrides={"overall_composite_mean": 0.90})
    recomputed = recompute_summary(extract_raw_cases(report))
    diff = diff_self_reported_vs_independent(report, recomputed)
    assert diff["overall_composite_mean"]["match"] is False
    # Self-reported (0.90) > independent (0.50) → diff is -0.40
    assert diff["overall_composite_mean"]["diff"] == -0.40


def test_diff_detects_inflated_satisfied_count():
    """Per PR-22: a self-reported satisfied count HIGHER than independent is BLOCKED."""
    # Case 1: composite 0.30 → "uncertain"; expected "feasible"; distance 3; NOT satisfied
    cases = [_make_case("case_001", 0.30, expected="feasible")]
    # Self-report it as satisfied (a lie)
    cases[0]["expectations_satisfied"] = True
    report = _make_report(cases, summary_overrides={"expectations_satisfied": 1})
    recomputed = recompute_summary(extract_raw_cases(report))
    diff = diff_self_reported_vs_independent(report, recomputed)
    # Independent recomputation correctly identifies it as NOT satisfied
    assert recomputed["expectations_satisfied"] == 0
    assert diff["expectations_satisfied_count"]["match"] is False
    assert diff["expectations_satisfied_count"]["diff"] == -1
    # Per-case disagreement is also detected
    assert len(diff["per_case_disagreements"]) == 1
    assert diff["per_case_disagreements"][0]["case_id"] == "case_001"
    assert diff["per_case_disagreements"][0]["self_reported"] is True
    assert diff["per_case_disagreements"][0]["independently_derived"] is False


def test_diff_detects_verdict_bucket_disagreement():
    """Per PR-22: a self-reported verdict that disagrees with the recomputed
    verdict (computed from the same composite) is BLOCKED. This catches
    cases where the report claims a different verdict than the composite
    actually maps to."""
    # composite 0.30 → verdict_from_composite() = "uncertain"
    # But self-report it as "feasible" (a lie)
    cases = [{
        "case_id": "case_001",
        "case_name": "Test",
        "category": "reconstruction",
        "expected_verdict": "feasible",
        "actual_verdict": "feasible",  # lie — composite 0.30 actually maps to "uncertain"
        "composite_feasibility": 0.30,
        "bucket_distance_from_expected": 0,  # lie
        "duration_s": 0.1,
        "expectations_satisfied": True,  # lie
    }]
    report = _make_report(cases, summary_overrides={"expectations_satisfied": 1})
    recomputed = recompute_summary(extract_raw_cases(report))
    diff = diff_self_reported_vs_independent(report, recomputed)
    # The recomputed verdict should be "uncertain" (composite 0.30)
    assert recomputed["cases"][0]["recomputed_verdict"] == "uncertain"
    # And it disagrees with the self-reported "feasible"
    assert len(diff["verdict_disagreements"]) == 1
    assert diff["verdict_disagreements"][0]["self_reported_verdict"] == "feasible"
    assert diff["verdict_disagreements"][0]["recomputed_verdict"] == "uncertain"


# ----------------------------------------------------------------------
# 4. End-to-end CLI test
# ----------------------------------------------------------------------

def test_cli_returns_0_on_pass(tmp_path):
    """The CLI returns exit code 0 when the report passes verification."""
    cases = [_make_case("test_001", 0.80, expected="feasible")]
    report = _make_report(cases)
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))
    result = subprocess.run(
        [sys.executable, "scripts/verify_benchmarks.py",
         "--report", str(report_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}\n{result.stdout}"


def test_cli_returns_1_on_fail(tmp_path):
    """The CLI returns exit code 1 when the report fails verification."""
    cases = [_make_case("test_001", 0.50, expected="feasible")]
    report = _make_report(cases, summary_overrides={"overall_composite_mean": 0.90})
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))
    result = subprocess.run(
        [sys.executable, "scripts/verify_benchmarks.py",
         "--report", str(report_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}\n{result.stdout}"
    assert "FAIL" in result.stdout


def test_cli_json_output(tmp_path):
    """The --json flag emits valid JSON with the expected structure."""
    cases = [_make_case("test_001", 0.80, expected="feasible")]
    report = _make_report(cases)
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report))
    result = subprocess.run(
        [sys.executable, "scripts/verify_benchmarks.py",
         "--report", str(report_path), "--json"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["verifier"] == "scripts/verify_benchmarks.py"
    assert output["overall_status"] == "PASS"
    assert "recomputed_summary" in output
    assert "diff" in output


# ----------------------------------------------------------------------
# 5. Architectural separation — the verifier does NOT see the ledger
# ----------------------------------------------------------------------

def test_verifier_does_not_read_ledger_field():
    """Per PR-22: the verifier reads ONLY the report's raw per-case data,
    NOT the ledger's overall_composite_mean field. This is the
    architectural separation that closes F-044."""
    # The verifier's recompute_summary function only reads:
    #   cases[*].composite_feasibility
    #   cases[*].case_id
    # It does NOT read any ledger field.
    cases = [_make_case("case_001", 0.50, expected="feasible")]
    # Even if we inject a fake ledger-like field, the verifier ignores it
    report = _make_report(cases)
    report["overall_composite_mean"] = 0.99  # ledger-style lie
    recomputed = recompute_summary(extract_raw_cases(report))
    # The recomputed mean is from raw cases, not from the injected field
    assert recomputed["overall_composite_mean"] == 0.50
    assert recomputed["overall_composite_mean"] != 0.99


# ----------------------------------------------------------------------
# 6. Live report verification — the actual repo report
# ----------------------------------------------------------------------

def test_live_report_passes_verification():
    """The actual benchmark report at evidence/reports/compiler_benchmark_report.json
    MUST pass the verifier. If this test fails, either:
    1. The report is stale (regenerate via scripts/run_compiler_benchmarks.py).
    2. The report's self-reported summary disagrees with the per-case raw data
       (F-044 violation — the report is self-graded in a biased way).
    """
    report_path = ROOT / "evidence" / "reports" / "compiler_benchmark_report.json"
    if not report_path.exists():
        pytest.skip("benchmark report not yet generated")
    report = load_report(report_path)
    cases = extract_raw_cases(report)
    recomputed = recompute_summary(cases)
    diff = diff_self_reported_vs_independent(report, recomputed)
    # Per PR-22: all headline numbers must match
    assert diff["overall_composite_mean"]["match"] is True, (
        f"overall_composite_mean: self={diff['overall_composite_mean']['self_reported']}, "
        f"independent={diff['overall_composite_mean']['independently_derived']}"
    )
    assert diff["expectations_satisfied_count"]["match"] is True, (
        f"expectations_satisfied: self={diff['expectations_satisfied_count']['self_reported']}, "
        f"independent={diff['expectations_satisfied_count']['independently_derived']}"
    )
    assert len(diff["per_case_disagreements"]) == 0
    assert len(diff["verdict_disagreements"]) == 0
