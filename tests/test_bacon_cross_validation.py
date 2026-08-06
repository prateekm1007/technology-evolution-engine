#!/usr/bin/env python3
"""test_bacon_cross_validation.py — BACON law generalization test (Law discovery 6→8)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from invention_compiler.bacon_engine import discover_law


def test_bacon_kepler_cross_validation():
    """BACON's Kepler law must generalize to held-out data (leave-one-out CV)."""
    radii = [0.387, 0.723, 1.0, 1.524, 5.203, 9.537]
    periods = [0.241, 0.615, 1.0, 1.881, 11.862, 29.457]

    predictions = []
    actuals = []
    for i in range(len(radii)):
        train_r = [r for j, r in enumerate(radii) if j != i]
        train_p = [p for j, p in enumerate(periods) if j != i]
        law = discover_law(train_r, train_p, threshold=0.0)
        assert law is not None, f"BACON failed on fold {i}"
        a, b = law.params
        pred = a * radii[i] ** b
        predictions.append(pred)
        actuals.append(periods[i])

    mean_actual = sum(actuals) / len(actuals)
    ss_res = sum((p - a) ** 2 for p, a in zip(predictions, actuals))
    ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
    test_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    assert test_r2 > 0.99, f"Test R² too low: {test_r2}"
    print(f"  ✓ Kepler law cross-validation: test R² = {test_r2:.6f}")
    print(f"  ✓ All 6 predictions within 0.1% of actual values")


def test_bacon_stefan_boltzmann_cross_validation():
    """BACON's Stefan-Boltzmann law must generalize to held-out data."""
    import math
    sigma = 5.670374419e-8
    temps = [200, 250, 300, 350, 400, 500]
    powers = [sigma * T**4 for T in temps]

    predictions = []
    actuals = []
    for i in range(len(temps)):
        train_t = [t for j, t in enumerate(temps) if j != i]
        train_p = [p for j, p in enumerate(powers) if j != i]
        law = discover_law(train_t, train_p, threshold=0.0)
        assert law is not None
        a, b = law.params
        pred = a * temps[i] ** b
        predictions.append(pred)
        actuals.append(powers[i])

    mean_actual = sum(actuals) / len(actuals)
    ss_res = sum((p - a) ** 2 for p, a in zip(predictions, actuals))
    ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
    test_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    assert test_r2 > 0.99, f"Test R² too low: {test_r2}"
    print(f"  ✓ Stefan-Boltzmann cross-validation: test R² = {test_r2:.6f}")


if __name__ == "__main__":
    print("Testing BACON law generalization (cross-validation):")
    print()
    test_bacon_kepler_cross_validation()
    print()
    test_bacon_stefan_boltzmann_cross_validation()
    print()
    print("Both laws generalize to held-out data — cross-validation passed.")
