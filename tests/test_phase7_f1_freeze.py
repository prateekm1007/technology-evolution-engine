"""Tests: Phase 7 F1 optimization freeze enforcement.

Per the 18-phase plan:
    "Phase 7: FREEZE F1 OPTIMIZATION"

Per STOP_BUILDING.md:
    Item 8: Benchmark tuning is forbidden permanently
    Item 9: Score improvements without capability improvement are
            forbidden permanently

These tests verify that F1 optimization is MECHANICALLY IMPOSSIBLE:
    1. The F1 baseline (0.5714) is frozen and cannot be changed
    2. Forbidden optimization patterns raise F1OptimizationForbidden
    3. Zero eligible metrics means there is nothing to optimize against
    4. The freeze is machine-enforced, not just policy
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.f1_optimization_freeze import (
    F1OptimizationForbidden,
    FROZEN_F1_BASELINE,
    FORBIDDEN_OPTIMIZATION_PATTERNS,
    get_frozen_f1_baseline,
    assert_f1_not_optimized,
    assert_f1_baseline_unchanged,
    assert_zero_eligible_metrics_for_optimization,
)


# ===== Test 1: F1 baseline is frozen =====

def test_f1_baseline_is_05714():
    """The frozen F1 baseline must be 0.5714."""
    assert FROZEN_F1_BASELINE == 0.5714


def test_f1_baseline_has_provenance():
    """The frozen F1 baseline must have provenance (source, cycle, SHA-256)."""
    baseline = get_frozen_f1_baseline()
    assert baseline["f1"] == 0.5714
    assert baseline["source"] == "stage-1-measurement-integrity-baseline"
    assert baseline["cycle"] == 134
    assert len(baseline["sha256"]) == 64  # SHA-256 hex
    assert baseline["frozen"] is True


def test_f1_baseline_unchanged_passes():
    """assert_f1_baseline_unchanged passes when the value matches."""
    assert_f1_baseline_unchanged(0.5714)  # should not raise


def test_f1_baseline_modified_raises():
    """assert_f1_baseline_unchanged raises when the value differs."""
    with pytest.raises(F1OptimizationForbidden, match="F1 BASELINE MODIFIED"):
        assert_f1_baseline_unchanged(0.6000)  # attempted improvement


def test_f1_baseline_lowered_raises():
    """Lowering the F1 baseline also raises (it's still a modification)."""
    with pytest.raises(F1OptimizationForbidden, match="F1 BASELINE MODIFIED"):
        assert_f1_baseline_unchanged(0.5000)


# ===== Test 2: Forbidden optimization patterns are machine-enforced =====

@pytest.mark.parametrize("pattern", FORBIDDEN_OPTIMIZATION_PATTERNS)
def test_forbidden_optimization_pattern_raises(pattern):
    """Each forbidden optimization pattern must raise F1OptimizationForbidden."""
    with pytest.raises(F1OptimizationForbidden, match="FORBIDDEN"):
        assert_f1_not_optimized(f"attempting {pattern} on benchmark")


def test_threshold_lowering_raises():
    """Threshold lowering is forbidden (No-Gaming Rule)."""
    with pytest.raises(F1OptimizationForbidden, match="threshold-lowering"):
        assert_f1_not_optimized("lower_threshold to improve F1")


def test_synonym_expansion_for_score_raises():
    """Expanding synonyms to improve scores is forbidden."""
    with pytest.raises(F1OptimizationForbidden, match="FORBIDDEN"):
        assert_f1_not_optimized("synonym_expansion_for_score")


def test_non_optimization_action_passes():
    """A non-optimization action should not raise."""
    assert_f1_not_optimized("running measurement audit")  # should not raise
    assert_f1_not_optimized("regenerating bootstrap statistics")  # should not raise
    assert_f1_not_optimized("investigating M-008 discrepancy")  # should not raise


# ===== Test 3: Zero eligible metrics means optimization is impossible =====

def test_zero_eligible_metrics_confirmed():
    """There must be zero scientifically eligible metrics.

    F1 optimization is not just forbidden by policy — it is impossible
    because the metrics that would measure F1 improvement are themselves
    not scientifically eligible. There is nothing to optimize against.
    """
    # Should not raise (0 eligible metrics)
    assert_zero_eligible_metrics_for_optimization()


# ===== Test 4: The freeze is machine-enforced, not just policy =====

def test_freeze_raises_exception_not_returns_false():
    """The freeze enforcer RAISES exceptions, not returns False.

    This is the key mechanical enforcement: code that attempts
    optimization cannot continue past the assertion.
    """
    with pytest.raises(F1OptimizationForbidden):
        assert_f1_not_optimized("benchmark_tuning")

    # Verify the function returns None when it passes
    result = assert_f1_not_optimized("legitimate measurement work")
    assert result is None


def test_optimization_cannot_proceed_past_gate():
    """A code path that attempts optimization must not reach the next line."""
    def attempt_optimization():
        assert_f1_not_optimized("score_improvement_without_capability")
        return "optimization completed"  # should never reach

    with pytest.raises(F1OptimizationForbidden):
        result = attempt_optimization()
        assert result != "optimization completed"


# ===== Test 5: Structural test — no F1 optimization code exists =====

def test_no_f1_optimization_code_in_engine():
    """The engine/ directory must not contain F1 optimization code.

    Per STOP_BUILDING.md item 9: score improvements without capability
    improvement are forbidden permanently. There should be no code in
    engine/ that attempts to optimize F1.
    """
    engine_dir = Path(__file__).resolve().parents[1] / "engine"
    forbidden_files = []
    for py_file in engine_dir.glob("*.py"):
        content = py_file.read_text().lower()
        # Look for actual optimization code (not the freeze enforcer itself)
        if py_file.name == "f1_optimization_freeze.py":
            continue  # this IS the freeze enforcer
        if any(p in content for p in ["optimize_f1", "improve_f1", "tune_f1",
                                       "boost_f1", "increase_f1"]):
            forbidden_files.append(py_file.name)

    assert len(forbidden_files) == 0, (
        f"engine/ contains F1 optimization code in: {forbidden_files}. "
        f"Per STOP_BUILDING.md item 9: score improvements without capability "
        f"improvement are forbidden permanently."
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
