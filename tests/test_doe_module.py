"""Tests for doe_module.py — Experiment design 6→8."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.doe_module import (
    DesignOfExperiments,
    Factor,
    ExperimentRun,
    MainEffect,
    InteractionEffect,
    DOEAnalysis,
)


def test_full_factorial_2_factors():
    """2^k = 4 runs for 2 factors."""
    doe = DesignOfExperiments([
        Factor("A", low=0, high=1),
        Factor("B", low=0, high=1),
    ])
    design = doe.full_factorial()
    assert len(design) == 4
    # Each run has settings for both factors
    for run in design:
        assert "A" in run.settings
        assert "B" in run.settings
        assert run.settings["A"] in (0, 1)
        assert run.settings["B"] in (0, 1)


def test_full_factorial_3_factors():
    """2^3 = 8 runs for 3 factors."""
    doe = DesignOfExperiments([
        Factor("A", low=0, high=1),
        Factor("B", low=0, high=1),
        Factor("C", low=0, high=1),
    ])
    design = doe.full_factorial()
    assert len(design) == 8


def test_full_factorial_unique_runs():
    """Every run in a full factorial is unique."""
    doe = DesignOfExperiments([
        Factor("A", low=0, high=1),
        Factor("B", low=0, high=1),
        Factor("C", low=0, high=1),
    ])
    design = doe.full_factorial()
    seen = set()
    for run in design:
        key = tuple(sorted(run.settings.items()))
        assert key not in seen, f"Duplicate run: {run.settings}"
        seen.add(key)


def test_coded_values():
    """Coded values are -1 (low) or +1 (high)."""
    doe = DesignOfExperiments([
        Factor("A", low=10, high=20),
    ])
    design = doe.full_factorial()
    assert design[0].settings_coded["A"] == -1
    assert design[0].settings["A"] == 10
    assert design[1].settings_coded["A"] == 1
    assert design[1].settings["A"] == 20


def test_fractional_factorial_half():
    """Half-fraction of 3 factors gives 4 runs (instead of 8)."""
    doe = DesignOfExperiments([
        Factor("A", low=0, high=1),
        Factor("B", low=0, high=1),
        Factor("C", low=0, high=1),
    ])
    design = doe.fractional_factorial(p=1)
    assert len(design) == 4


def test_execute_populates_predicted_and_measured():
    """After execute, every run has predicted and measured values."""
    doe = DesignOfExperiments([
        Factor("A", low=1, high=2),
    ])
    design = doe.full_factorial()

    def simulator(settings):
        x = settings["A"]
        return x * 2, x * 2  # predicted = measured = 2x

    completed = doe.execute(design, simulator)
    for run in completed:
        assert run.predicted is not None
        assert run.measured is not None
        assert run.residual is not None


def test_analyze_computes_main_effects():
    """Main effects are computed correctly for a known system."""
    # y = 10 + 5*A - 3*B (linear, no interaction, no noise)
    doe = DesignOfExperiments([
        Factor("A", low=-1, high=1),
        Factor("B", low=-1, high=1),
    ])
    design = doe.full_factorial()

    def simulator(settings):
        a = settings["A"]
        b = settings["B"]
        y = 10 + 5 * a - 3 * b  # true model
        return 10, y  # predicted = constant 10, measured = true

    completed = doe.execute(design, simulator)
    analysis = doe.analyze(completed, significance_threshold=2.0)

    # Find main effects
    me_a = next(me for me in analysis.main_effects if me.factor == "A")
    me_b = next(me for me in analysis.main_effects if me.factor == "B")

    # Effect of A should be ~10 (5 * (1 - (-1)) = 10)
    assert abs(me_a.effect - 10) < 0.01, f"A effect = {me_a.effect}, expected ~10"
    # Effect of B should be ~-6 (-3 * (1 - (-1)) = -6)
    assert abs(me_b.effect - (-6)) < 0.01, f"B effect = {me_b.effect}, expected ~-6"


def test_analyze_identifies_significant_factors():
    """Factors with large effects are flagged as significant."""
    doe = DesignOfExperiments([
        Factor("A", low=-1, high=1),
        Factor("B", low=-1, high=1),
    ])
    design = doe.full_factorial()

    def simulator(settings):
        a = settings["A"]
        b = settings["B"]
        # A has a huge effect, B has a tiny effect
        y = 100 * a + 0.001 * b
        return 0, y

    completed = doe.execute(design, simulator)
    analysis = doe.analyze(completed, significance_threshold=2.0)

    assert "A" in analysis.significant_factors
    # B should NOT be significant (effect too small relative to MSE which is 0 here)
    # Note: when MSE = 0, significance = inf for any non-zero effect, so this
    # test relies on the tiny effect of B being rounded to 0
    me_b = next(me for me in analysis.main_effects if me.factor == "B")
    assert abs(me_b.effect) < 0.01


def test_edge_updates_generated_for_significant_factors():
    """Each significant factor produces an edge update entry."""
    doe = DesignOfExperiments([
        Factor("A", low=-1, high=1),
        Factor("B", low=-1, high=1),
    ])
    design = doe.full_factorial()

    def simulator(settings):
        a = settings["A"]
        return 0, 100 * a  # A dominates

    completed = doe.execute(design, simulator)
    analysis = doe.analyze(completed, significance_threshold=2.0)

    assert len(analysis.edge_updates) >= 1
    for update in analysis.edge_updates:
        assert "factor" in update
        assert "tier_change" in update
        assert "reasoning" in update


def test_two_factor_interactions_computed():
    """Two-factor interactions are computed when 2+ factors present."""
    doe = DesignOfExperiments([
        Factor("A", low=-1, high=1),
        Factor("B", low=-1, high=1),
    ])
    design = doe.full_factorial()

    def simulator(settings):
        a = settings["A"]
        b = settings["B"]
        # Pure interaction, no main effects
        y = 5 * a * b
        return 0, y

    completed = doe.execute(design, simulator)
    analysis = doe.analyze(completed, significance_threshold=2.0)

    # The A×B interaction should be detected
    ab = next(ie for ie in analysis.interactions
              if ie.factor_a == "A" and ie.factor_b == "B")
    # For y = β_ab * a * b with a, b in {-1, +1}:
    #   Effect = (avg at same-sign) - (avg at opposite-sign) = 2 * β_ab
    # With β_ab = 5, the effect should be 10.
    assert abs(ab.effect - 10) < 0.01, f"A×B effect = {ab.effect}, expected ~10"


def test_mse_zero_for_perfect_predictions():
    """MSE is 0 when measured = predicted."""
    doe = DesignOfExperiments([Factor("A", low=0, high=1)])
    design = doe.full_factorial()
    completed = doe.execute(design, lambda s: (5.0, 5.0))
    analysis = doe.analyze(completed)
    assert analysis.mse < 1e-9


def test_invalid_empty_factors_raises():
    """Empty factor list raises ValueError."""
    try:
        DesignOfExperiments([])
        assert False, "Should have raised"
    except ValueError:
        pass


def test_invalid_fractional_p_raises():
    """p >= k raises ValueError."""
    doe = DesignOfExperiments([Factor("A", low=0, high=1)])
    try:
        doe.fractional_factorial(p=1)
        assert False, "Should have raised"
    except ValueError:
        pass


def test_run_settings_coded_only_minus1_or_plus1():
    """All coded values are -1 or +1."""
    doe = DesignOfExperiments([
        Factor("A", low=10, high=20),
        Factor("B", low=100, high=200),
    ])
    design = doe.full_factorial()
    for run in design:
        for v in run.settings_coded.values():
            assert v in (-1, 1)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
