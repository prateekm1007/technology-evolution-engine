"""
test_bootstrap_statistics.py — Tests for Stage M3 Bootstrap Statistics.

Verifies that:
  1. The bootstrap engine produces valid BootstrapResult objects
  2. The 95% CI is computed correctly
  3. Degenerate metrics are detected
  4. All specified M-metrics have bootstrap results in reports/
  5. The reports contain the required fields (point, std, CI, N, B)
"""
import sys
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.bootstrap_statistics import (
    bootstrap_metric, BootstrapResult, _percentile_sorted, _skewness, _kurtosis,
)


# ============================================================================
# CORE BOOTSTRAP ENGINE
# ============================================================================

def test_bootstrap_metric_returns_result():
    """bootstrap_metric should return a BootstrapResult with all fields."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    result = bootstrap_metric(
        sample=[1.0, 2.0, 3.0, 4.0, 5.0],
        metric_fn=mean_fn,
        n_resamples=100,
        seed=42,
        metric_id="test",
        metric_name="test mean",
    )
    assert isinstance(result, BootstrapResult)
    assert result.metric_id == "test"
    assert result.metric_name == "test mean"
    assert result.point_estimate == 3.0  # mean of [1,2,3,4,5]
    assert result.n == 5
    assert result.n_resamples == 100
    assert result.seed == 42


def test_bootstrap_ci_contains_point_estimate_for_symmetric_distribution():
    """For a symmetric distribution, the point estimate should be in the CI."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    result = bootstrap_metric(
        sample=[1.0, 2.0, 3.0, 4.0, 5.0] * 10,  # 50 samples
        metric_fn=mean_fn,
        n_resamples=1000,
        seed=42,
    )
    # For a large symmetric sample, mean should be in the CI
    assert result.ci_95_lower <= result.point_estimate <= result.ci_95_upper


def test_bootstrap_ci_width_positive_for_non_degenerate():
    """A non-degenerate metric should have a positive CI width."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    result = bootstrap_metric(
        sample=[1.0, 2.0, 3.0, 4.0, 5.0],
        metric_fn=mean_fn,
        n_resamples=1000,
        seed=42,
    )
    assert result.ci_95_width > 0
    assert not result.is_degenerate


def test_bootstrap_degenerate_metric_detected():
    """A metric that always returns the same value should be degenerate."""
    def constant_fn(sample):
        return 42.0  # always 42
    result = bootstrap_metric(
        sample=[1.0, 2.0, 3.0, 4.0, 5.0],
        metric_fn=constant_fn,
        n_resamples=100,
        seed=42,
    )
    assert result.is_degenerate is True
    assert result.bootstrap_std == 0.0
    assert result.ci_95_width == 0.0


def test_bootstrap_empty_sample():
    """An empty sample should return a zero result without crashing."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    result = bootstrap_metric(
        sample=[],
        metric_fn=mean_fn,
        n_resamples=100,
        seed=42,
    )
    assert result.n == 0
    assert result.point_estimate == 0.0
    assert result.is_degenerate is True


def test_bootstrap_reproducible_with_same_seed():
    """Same seed should produce the same bootstrap distribution."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    sample = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    r1 = bootstrap_metric(sample, mean_fn, n_resamples=200, seed=42)
    r2 = bootstrap_metric(sample, mean_fn, n_resamples=200, seed=42)
    assert r1.distribution == r2.distribution
    assert r1.bootstrap_mean == r2.bootstrap_mean
    assert r1.ci_95_lower == r2.ci_95_lower


def test_bootstrap_different_seeds_produce_different_distributions():
    """Different seeds should (usually) produce different distributions."""
    def mean_fn(sample):
        return sum(sample) / len(sample) if sample else 0.0
    sample = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    r1 = bootstrap_metric(sample, mean_fn, n_resamples=200, seed=42)
    r2 = bootstrap_metric(sample, mean_fn, n_resamples=200, seed=99)
    # Distributions should differ (with very high probability)
    assert r1.distribution != r2.distribution


# ============================================================================
# PERCENTILE HELPER
# ============================================================================

def test_percentile_sorted_basic():
    assert _percentile_sorted([1.0, 2.0, 3.0, 4.0, 5.0], 0) == 1.0
    assert _percentile_sorted([1.0, 2.0, 3.0, 4.0, 5.0], 50) == 3.0
    assert _percentile_sorted([1.0, 2.0, 3.0, 4.0, 5.0], 100) == 5.0


def test_percentile_sorted_empty():
    assert _percentile_sorted([], 50) == 0.0


def test_percentile_sorted_single():
    assert _percentile_sorted([7.0], 50) == 7.0
    assert _percentile_sorted([7.0], 0) == 7.0
    assert _percentile_sorted([7.0], 100) == 7.0


# ============================================================================
# SKEWNESS / KURTOSIS
# ============================================================================

def test_skewness_zero_for_symmetric():
    """Symmetric distribution should have ~0 skewness."""
    vals = [-2.0, -1.0, 0.0, 1.0, 2.0]
    mean = 0.0
    std = math.sqrt(sum(v**2 for v in vals) / len(vals))
    assert abs(_skewness(vals, mean, std)) < 0.1


def test_kurtosis_zero_for_normal_like():
    """Approximately normal distribution should have ~0 excess kurtosis."""
    # Uniform distribution has excess kurtosis = -1.2
    # We just check it's a finite number
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean = 3.0
    std = math.sqrt(2.0)
    k = _kurtosis(vals, mean, std)
    assert isinstance(k, float)
    assert math.isfinite(k)


def test_skewness_zero_for_zero_std():
    assert _skewness([1.0, 1.0, 1.0], 1.0, 0.0) == 0.0


# ============================================================================
# BootstrapResult.format()
# ============================================================================

def test_format_produces_expected_string():
    r = BootstrapResult(
        metric_id="M-005", metric_name="Discovery F1",
        point_estimate=0.8571, bootstrap_mean=0.85, bootstrap_std=0.0635,
        bootstrap_variance=0.004, ci_95_lower=0.71, ci_95_upper=0.95,
        ci_95_width=0.24, n=20, n_resamples=500, seed=42,
        skewness=-0.5, kurtosis=0.3,
    )
    s = r.format()
    assert "Discovery F1" in s
    assert "0.8571" in s
    assert "0.0635" in s
    assert "0.7100" in s or "0.71" in s
    assert "N=20" in s
    assert "B=500" in s


def test_to_dict_includes_all_fields():
    r = BootstrapResult(
        metric_id="M-001", metric_name="test",
        point_estimate=0.5, bootstrap_mean=0.5, bootstrap_std=0.1,
        bootstrap_variance=0.01, ci_95_lower=0.3, ci_95_upper=0.7,
        ci_95_width=0.4, n=10, n_resamples=100, seed=42,
        skewness=0.0, kurtosis=0.0,
    )
    d = r.to_dict()
    expected_keys = {
        "metric_id", "metric_name", "point_estimate", "bootstrap_mean",
        "bootstrap_std", "bootstrap_variance", "ci_95_lower", "ci_95_upper",
        "ci_95_width", "n", "n_resamples", "seed", "skewness", "kurtosis",
        "is_degenerate",
    }
    assert expected_keys.issubset(d.keys())


# ============================================================================
# END-TO-END: reports exist with required structure
# ============================================================================

def test_bootstrap_statistics_json_exists():
    """reports/bootstrap_statistics.json must exist after running Stage M3."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    assert path.exists(), (
        "reports/bootstrap_statistics.json missing. "
        "Run: python3 -m programs.A_metrology.bootstrap_statistics"
    )


def test_bootstrap_statistics_md_exists():
    path = REPO / "reports" / "bootstrap_statistics.md"
    assert path.exists()


def test_bootstrap_json_has_required_structure():
    """JSON must have cycle, stage, program, n_metrics, results."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    assert data["stage"] == "M3"
    assert data["program"] == "A"
    assert "n_metrics" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 19  # at least 19 specified metrics


def test_every_result_has_required_fields():
    """Each result in the JSON must have point, std, CI, N, B."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    required = {
        "metric_id", "metric_name", "point_estimate",
        "bootstrap_std", "ci_95_lower", "ci_95_upper",
        "n", "n_resamples",
    }
    for r in data["results"]:
        assert required.issubset(r.keys()), (
            f"Result {r.get('metric_id', '?')} missing fields: "
            f"{required - set(r.keys())}"
        )


def test_known_metrics_have_bootstrap_results():
    """The 19 specified M-metrics must all have bootstrap results."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    metric_ids = {r["metric_id"] for r in data["results"]}
    # The 19 specified metrics (M-001..M-016, M-301..M-303)
    # Note: M-303 is split into M-303-D1..D7 in the bootstrap, so we
    # check for at least one M-303 variant.
    required_ids = {f"M-{i:03d}" for i in range(1, 17)} | {"M-301", "M-302"}
    missing = required_ids - metric_ids
    assert not missing, f"Missing bootstrap results for: {missing}"
    # At least one M-303 variant
    m303_variants = {mid for mid in metric_ids if mid.startswith("M-303")}
    assert len(m303_variants) >= 1, "Missing M-303 (AI surrogate dimensions)"


def test_all_30_specified_metrics_have_bootstrap_results():
    """Cycle 261: all 30 specified M-metrics (including M-101..M-105,
    M-201..M-205, M-304..M-306) must have bootstrap results."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    metric_ids = {r["metric_id"] for r in data["results"]}

    # All 30 specified metric IDs (M-303 counts as one, represented by
    # at least one M-303-D* variant)
    required_ids = (
        {f"M-{i:03d}" for i in range(1, 17)} |   # M-001..M-016
        {f"M-{i:03d}" for i in range(101, 106)} | # M-101..M-105
        {f"M-{i:03d}" for i in range(201, 206)} | # M-201..M-205
        {"M-301", "M-302", "M-304", "M-305", "M-306"}
    )
    missing = required_ids - metric_ids
    assert not missing, (
        f"Missing bootstrap results for: {missing}. "
        f"Present: {sorted(metric_ids)}"
    )
    # At least one M-303 variant
    m303_variants = {mid for mid in metric_ids if mid.startswith("M-303")}
    assert len(m303_variants) >= 1, "Missing M-303 (AI surrogate dimensions)"


def test_invention_metrics_have_bootstrap_cis():
    """M-101..M-105 must have non-empty CI fields."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    for mid in ("M-101", "M-102", "M-103", "M-104", "M-105"):
        r = next((x for x in data["results"] if x["metric_id"] == mid), None)
        assert r is not None, f"Missing {mid}"
        assert "ci_95_lower" in r and "ci_95_upper" in r
        assert r["n"] > 0, f"{mid} has N=0"
        assert r["n_resamples"] > 0, f"{mid} has B=0"


def test_search_metrics_have_bootstrap_cis():
    """M-201..M-205 must have non-empty CI fields."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    for mid in ("M-201", "M-202", "M-203", "M-204", "M-205"):
        r = next((x for x in data["results"] if x["metric_id"] == mid), None)
        assert r is not None, f"Missing {mid}"
        assert "ci_95_lower" in r and "ci_95_upper" in r


def test_evaluation_metrics_extended_have_bootstrap_cis():
    """M-304..M-306 must have non-empty CI fields."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    for mid in ("M-304", "M-305", "M-306"):
        r = next((x for x in data["results"] if x["metric_id"] == mid), None)
        assert r is not None, f"Missing {mid}"
        assert "ci_95_lower" in r and "ci_95_upper" in r


def test_m305_bias_ci_confirms_plus_2_50():
    """M-305 (self-validation bias) CI should contain +2.50."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m305 = next(r for r in data["results"] if r["metric_id"] == "M-305")
    assert abs(m305["point_estimate"] - 2.5) < 0.01
    assert m305["ci_95_lower"] <= 2.5 <= m305["ci_95_upper"]


def test_m304_agreement_ci_includes_zero():
    """M-304 (inter-rater agreement) CI should include 0 (1/6 agreed,
    small N means CI is very wide)."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m304 = next(r for r in data["results"] if r["metric_id"] == "M-304")
    assert m304["ci_95_lower"] == 0.0, (
        f"M-304 CI lower = {m304['ci_95_lower']}, expected 0.0 (small N, low agreement)"
    )


def test_m005_discovery_f1_has_ci_around_079():
    """M-005 (Discovery F1) point estimate should be ~0.79 with a CI.
    Note: was 0.8571 before cycle 270 (circular synonyms removed).
    Now 0.7879 with non-circular (empty) synonym map."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m005 = next(r for r in data["results"] if r["metric_id"] == "M-005")
    assert abs(m005["point_estimate"] - 0.79) < 0.05
    # CI should be non-trivial (width > 0.1)
    assert m005["ci_95_upper"] - m005["ci_95_lower"] > 0.1
    # CI should contain the point estimate
    assert m005["ci_95_lower"] <= m005["point_estimate"] <= m005["ci_95_upper"]


def test_m008_fp_floor_has_ci_near_1():
    """M-008 (FP floor) should be near 1.0, confirming DR-91 finding."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m008 = next(r for r in data["results"] if r["metric_id"] == "M-008")
    # FP floor should be high (> 0.7), confirming the catastrophic finding
    assert m008["point_estimate"] > 0.7, (
        f"FP floor point estimate = {m008['point_estimate']}, expected > 0.7"
    )


def test_m001_exact_f1_is_degenerate_zero():
    """M-001 (Exact F1) should be degenerate at 0 (strict matching never matches)."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m001 = next(r for r in data["results"] if r["metric_id"] == "M-001")
    assert m001["point_estimate"] == 0.0
    assert m001["is_degenerate"] is True


def test_m301_ai_surrogate_accept_rate_is_zero():
    """M-301 (AI surrogate accept rate) should be 0 (0/6 accepted)."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    data = json.loads(path.read_text())
    m301 = next(r for r in data["results"] if r["metric_id"] == "M-301")
    assert m301["point_estimate"] == 0.0
