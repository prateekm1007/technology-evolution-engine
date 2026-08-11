"""
test_measurement_provenance.py — Tests for Stage M2 (Measurement Provenance).

Verifies:
  1. ScoredValue dataclass has all 14+ required provenance fields
  2. ProvenanceRegistry loads bootstrap data correctly
  3. @with_provenance decorator wraps functions correctly
  4. format_score produces the canonical string
  5. is_naked_number detects bare floats
  6. Unquantified metrics are flagged correctly
  7. The registry has data for all 30 specified metrics
"""
import sys
import json
from pathlib import Path
from dataclasses import fields as dataclass_fields

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.measurement_provenance import (
    ScoredValue, ProvenanceRegistry, with_provenance,
    format_score, format_score_short, is_naked_number, _get_registry,
)


# ============================================================================
# ScoredValue dataclass
# ============================================================================

def test_scored_value_has_all_required_fields():
    """ScoredValue must have all 14 provenance fields + value + chain."""
    field_names = {f.name for f in dataclass_fields(ScoredValue)}
    required = {
        "value", "metric_id", "metric_name", "uncertainty_std",
        "ci_95_lower", "ci_95_upper", "n", "n_resamples",
        "evidence_tier", "calibration_version", "evaluator_version",
        "prompt_version", "judge_version", "timestamp",
        "benchmark_version", "is_degenerate", "provenance_chain",
    }
    missing = required - field_names
    assert not missing, f"ScoredValue missing fields: {missing}"


def test_scored_value_to_dict_roundtrip():
    sv = ScoredValue(
        value=0.8571, metric_id="M-005", metric_name="Discovery F1",
        uncertainty_std=0.0635, ci_95_lower=0.7097, ci_95_upper=0.9474,
        n=20, n_resamples=500, evidence_tier="B",
        calibration_version="dr91-cycle-243", evaluator_version="dr91-v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="2026-08-09T00:00:00Z", benchmark_version="discovery-v1",
        is_degenerate=False, provenance_chain=["mod.fn"],
    )
    d = sv.to_dict()
    assert d["value"] == 0.8571
    assert d["metric_id"] == "M-005"
    assert d["uncertainty_std"] == 0.0635
    assert d["evidence_tier"] == "B"
    assert d["provenance_chain"] == ["mod.fn"]


def test_scored_value_format_includes_all_key_info():
    sv = ScoredValue(
        value=0.8571, metric_id="M-005", metric_name="Discovery F1",
        uncertainty_std=0.0635, ci_95_lower=0.7097, ci_95_upper=0.9474,
        n=20, n_resamples=500, evidence_tier="B",
        calibration_version="dr91-cycle-243", evaluator_version="dr91-v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="2026-08-09T00:00:00Z", benchmark_version="discovery-v1",
    )
    s = sv.format()
    assert "M-005" in s
    assert "0.8571" in s
    assert "0.0635" in s
    assert "0.7097" in s
    assert "0.9474" in s
    assert "N=20" in s
    assert "B=500" in s
    assert "tier=B" in s
    assert "cal=dr91-cycle-243" in s


def test_scored_value_format_short():
    sv = ScoredValue(
        value=0.5, metric_id="M-001", metric_name="test",
        uncertainty_std=0.1, ci_95_lower=0.3, ci_95_upper=0.7,
        n=10, n_resamples=100, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
    )
    s = sv.format_short()
    assert "M-001 = 0.5000 ± 0.1000 [0.3000, 0.7000]" == s


def test_scored_value_format_degenerate_flag():
    sv = ScoredValue(
        value=0.0, metric_id="M-001", metric_name="test",
        uncertainty_std=0.0, ci_95_lower=0.0, ci_95_upper=0.0,
        n=20, n_resamples=500, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
        is_degenerate=True,
    )
    s = sv.format()
    assert "DEGENERATE" in s


# ============================================================================
# ProvenanceRegistry
# ============================================================================

@pytest.fixture
def registry():
    return ProvenanceRegistry()


def test_registry_loads_bootstrap_data(registry):
    """Registry must load bootstrap_statistics.json."""
    metrics = registry.list_metrics()
    assert len(metrics) >= 30, (
        f"Registry should have ≥30 metrics, got {len(metrics)}"
    )


def test_registry_has_m005(registry):
    """M-005 (Discovery F1) must be in the registry."""
    assert registry.has_metric("M-005")
    boot = registry.get_bootstrap("M-005")
    assert boot is not None
    assert "ci_95_lower" in boot
    assert "ci_95_upper" in boot


def test_registry_has_all_30_specified_metrics(registry):
    """All 30 specified M-metrics must have bootstrap data in the registry."""
    required = (
        {f"M-{i:03d}" for i in range(1, 17)} |
        {f"M-{i:03d}" for i in range(101, 106)} |
        {f"M-{i:03d}" for i in range(201, 206)} |
        {"M-301", "M-302", "M-304", "M-305", "M-306"}
    )
    for mid in required:
        assert registry.has_metric(mid), (
            f"Registry missing {mid}"
        )


def test_registry_wrap_attaches_ci(registry):
    """wrap() must attach the bootstrap CI to the ScoredValue."""
    sv = registry.wrap(
        value=0.8571, metric_id="M-005", metric_name="Discovery F1",
        evidence_tier="B", calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1", benchmark_version="discovery-v1",
    )
    assert sv.value == 0.8571
    assert sv.uncertainty_std > 0  # M-005 is non-degenerate
    assert sv.ci_95_lower < sv.value < sv.ci_95_upper
    assert sv.n == 20
    assert sv.n_resamples == 500
    assert sv.evidence_tier == "B"


def test_registry_wrap_unquantified_metric(registry):
    """wrap() for a metric not in bootstrap data should be flagged."""
    sv = registry.wrap(
        value=0.5, metric_id="M-999", metric_name="Future metric",
        evidence_tier="I", calibration_version="uncalibrated",
        evaluator_version="unknown", benchmark_version="unknown",
    )
    assert sv.value == 0.5
    assert sv.uncertainty_std == 0.0
    assert sv.ci_95_lower == 0.5
    assert sv.ci_95_upper == 0.5
    assert sv.n == 0
    assert sv.n_resamples == 0
    assert sv.is_degenerate is True  # UNQUANTIFIED


def test_registry_wrap_degenerate_metric(registry):
    """wrap() for a degenerate metric (e.g. M-001) should preserve the flag."""
    sv = registry.wrap(
        value=0.0, metric_id="M-001", metric_name="Exact F1",
        evidence_tier="B", calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1", benchmark_version="discovery-v1",
    )
    assert sv.is_degenerate is True
    assert sv.uncertainty_std == 0.0


# ============================================================================
# @with_provenance decorator
# ============================================================================

def test_decorator_wraps_function_returning_float():
    """The decorator should convert a float return to ScoredValue."""
    @with_provenance(
        metric_id="M-005", metric_name="Discovery F1 (test)",
        evidence_tier="B", calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1", benchmark_version="discovery-v1",
    )
    def compute_f1():
        return 0.8571

    result = compute_f1()
    assert isinstance(result, ScoredValue)
    assert result.value == 0.8571
    assert result.metric_id == "M-005"
    assert result.evidence_tier == "B"
    assert result.calibration_version == "dr91-cycle-243"
    assert len(result.provenance_chain) == 1
    assert "compute_f1" in result.provenance_chain[0]


def test_decorator_preserves_function_metadata():
    """The decorator should preserve __name__ and __doc__."""
    @with_provenance(metric_id="M-001", metric_name="test")
    def my_func():
        """My docstring."""
        return 1.0

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "My docstring."


def test_decorator_attaches_raw_fn():
    """The decorator should attach the raw function for testing."""
    @with_provenance(metric_id="M-001", metric_name="test")
    def my_func():
        return 42.0

    assert hasattr(my_func, "_raw_fn")
    assert my_func._raw_fn() == 42.0
    assert my_func._metric_id == "M-001"


def test_decorator_with_arguments():
    """The decorator should work with functions that take arguments."""
    @with_provenance(metric_id="M-005", metric_name="Discovery F1")
    def compute_f1(tp, fp, fn):
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        return 2 * p * r / (p + r) if (p + r) > 0 else 0

    result = compute_f1(tp=17, fp=3, fn=3)
    assert isinstance(result, ScoredValue)
    assert result.value > 0


# ============================================================================
# format_score functions
# ============================================================================

def test_format_score_returns_string():
    sv = ScoredValue(
        value=0.5, metric_id="M-001", metric_name="test",
        uncertainty_std=0.1, ci_95_lower=0.3, ci_95_upper=0.7,
        n=10, n_resamples=100, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
    )
    s = format_score(sv)
    assert isinstance(s, str)
    assert "M-001" in s


def test_format_score_short_returns_string():
    sv = ScoredValue(
        value=0.5, metric_id="M-001", metric_name="test",
        uncertainty_std=0.1, ci_95_lower=0.3, ci_95_upper=0.7,
        n=10, n_resamples=100, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
    )
    s = format_score_short(sv)
    assert isinstance(s, str)
    assert "M-001" in s


# ============================================================================
# is_naked_number
# ============================================================================

def test_is_naked_number_detects_float():
    assert is_naked_number(0.8571) is True
    assert is_naked_number(3.14) is True


def test_is_naked_number_detects_int():
    assert is_naked_number(42) is True
    assert is_naked_number(0) is True


def test_is_naked_number_ignores_scored_value():
    sv = ScoredValue(
        value=0.5, metric_id="M-001", metric_name="test",
        uncertainty_std=0.1, ci_95_lower=0.3, ci_95_upper=0.7,
        n=10, n_resamples=100, evidence_tier="B",
        calibration_version="v1", evaluator_version="v1",
        prompt_version="n/a", judge_version="n/a",
        timestamp="now", benchmark_version="v1",
    )
    assert is_naked_number(sv) is False


def test_is_naked_number_ignores_bool():
    """bool is a subclass of int in Python, but we don't want to flag True/False."""
    assert is_naked_number(True) is False
    assert is_naked_number(False) is False


def test_is_naked_number_ignores_none_and_string():
    assert is_naked_number(None) is False
    assert is_naked_number("hello") is False


# ============================================================================
# Integration: decorator + registry
# ============================================================================

def test_decorator_uses_registry_for_ci():
    """The decorator should look up the CI from the registry."""
    @with_provenance(
        metric_id="M-005", metric_name="Discovery F1",
        evidence_tier="B", calibration_version="dr91-cycle-243",
        evaluator_version="dr91-v1", benchmark_version="discovery-v1",
    )
    def compute():
        return 0.8571

    result = compute()
    # M-005 has bootstrap data, so CI should be non-trivial
    assert result.uncertainty_std > 0
    assert result.ci_95_lower < 0.8571
    assert result.ci_95_upper > 0.8571
    assert result.n == 20
    assert result.n_resamples == 500


def test_module_level_registry_is_shared():
    """The module-level registry should be a singleton."""
    r1 = _get_registry()
    r2 = _get_registry()
    assert r1 is r2


# ============================================================================
# End-to-end: main() runs
# ============================================================================

def test_main_runs():
    from programs.A_metrology.measurement_provenance import main
    rc = main()
    assert rc == 0
