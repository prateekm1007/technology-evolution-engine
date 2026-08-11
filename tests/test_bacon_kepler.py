#!/usr/bin/env python3
"""
test_bacon_kepler.py — Verify BACON can discover Kepler's Third Law.

Per cycle 145: the external auditor stated "a high-order multi-variable law
(Kepler's T²∝R³) is NOT discoverable." This test proves it IS discoverable.

BACON discovers T = a * R^b with a≈1.0, b≈1.5, R²≈1.0 — which IS Kepler's
Third Law (T² ∝ R³ is equivalent to T ∝ R^1.5).

The auditor's critique about multivariate discovery is valid for laws that
REQUIRE combining multiple independent variables (e.g., F = G*m1*m2/r²).
But Kepler's Third Law is a single-variable power law and BACON finds it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from invention_compiler.bacon_engine import discover_law


def test_bacon_discovers_kepler_third_law():
    """BACON should discover T ∝ R^1.5 from planetary data."""
    # Real planetary data (AU for radius, years for period)
    radii = [0.387, 0.723, 1.0, 1.524, 5.203, 9.537]
    periods = [0.241, 0.615, 1.0, 1.881, 11.862, 29.457]

    law = discover_law(radii, periods)

    assert law is not None, "BACON failed to discover any law from Kepler data"
    assert law.name == "power", f"Expected power law, got {law.name}"
    assert law.r2 > 0.99, f"R² too low: {law.r2}"

    # Kepler's Third Law: T = R^1.5 (i.e., T² = R³)
    a, b = law.params
    assert abs(a - 1.0) < 0.01, f"Coefficient a should be ~1.0, got {a}"
    assert abs(b - 1.5) < 0.01, f"Exponent b should be ~1.5, got {b}"

    print(f"  ✓ BACON discovered: T = {a:.4f} * R^{b:.4f} (R²={law.r2:.6f})")
    print(f"  ✓ Kepler's Third Law: T ∝ R^1.5 (equivalent to T² ∝ R³)")


def test_bacon_discovers_stefan_boltzmann():
    """BACON should discover Q ∝ T^4 from Stefan-Boltzmann data."""
    # Stefan-Boltzmann: Q = σ * T^4
    import math
    sigma = 5.670374419e-8
    temps = [200, 250, 300, 350, 400, 500]  # Kelvin
    powers = [sigma * T**4 for T in temps]  # W/m²

    law = discover_law(temps, powers)

    assert law is not None, "BACON failed to discover Stefan-Boltzmann"
    assert law.name == "power", f"Expected power law, got {law.name}"
    assert law.r2 > 0.99, f"R² too low: {law.r2}"

    a, b = law.params
    assert abs(b - 4.0) < 0.01, f"Exponent b should be ~4.0, got {b}"

    print(f"  ✓ BACON discovered: Q = {a:.4e} * T^{b:.4f} (R²={law.r2:.6f})")
    print(f"  ✓ Stefan-Boltzmann Law: Q ∝ T^4")


if __name__ == "__main__":
    print("Testing BACON law discovery on real physics:")
    print()
    test_bacon_discovers_kepler_third_law()
    print()
    test_bacon_discovers_stefan_boltzmann()
    print()
    print("Both tests passed — BACON CAN discover real physics laws.")
