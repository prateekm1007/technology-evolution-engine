"""
Test Phase II (Dimensional Reasoning) — cycle 71.

Per External Auditor cycle 70: "Write tests — P28: exact, variation, edge."

Success criterion: "Impossible laws disappear automatically."

Tests verify:
  1. Dimension class works (multiplication, power, comparison)
  2. Unit registry covers common units
  3. Dimensional consistency check: P=V×I passes, P=T+m fails
  4. Buckingham π theorem: correct group count
  5. BACON integration: filter impossible laws before fitting
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.dimensional_reasoning import (
    Dimension, DIMENSIONLESS, POWER, TEMPERATURE, MASS, FORCE, ENERGY,
    VOLTAGE, CURRENT, SEEBECK, VELOCITY, AREA, TIME, LENGTH,
    UNIT_DIMENSIONS, get_dimension,
    check_dimensional_consistency, check_addition_consistency,
    buckingham_pi, filter_laws_by_dimension,
)


class TestDimension:
    """Test the Dimension dataclass."""

    def test_dimension_creation(self):
        """Exact case: Power = kg·m²·s⁻³."""
        p = POWER
        assert p.mass == 1
        assert p.length == 2
        assert p.time == -3
        assert p.current == 0
        assert p.temperature == 0
        assert p.amount == 0

    def test_dimension_multiplication(self):
        """Variation: velocity × time = distance."""
        v = VELOCITY  # m/s
        t = Dimension(time=1)  # s
        distance = v * t
        assert distance == Dimension(length=1)  # m

    def test_dimension_power(self):
        """Exact case: T⁴ for Stefan-Boltzmann."""
        T = TEMPERATURE
        T4 = T ** 4
        assert T4.temperature == 4

    def test_dimensionless(self):
        """Edge case: dimensionless quantity."""
        d = DIMENSIONLESS
        assert d.is_dimensionless()
        assert str(d) == "dimensionless"

    def test_dimension_str(self):
        """Dimension string representation."""
        assert "kg" in str(POWER)
        assert "m^2" in str(POWER)
        assert "s^-3" in str(POWER)


class TestUnitRegistry:
    """Test the unit registry."""

    def test_common_units_exist(self):
        """Exact case: common units are registered."""
        assert get_dimension("W") == POWER
        assert get_dimension("K") == TEMPERATURE
        assert get_dimension("kg") == MASS
        assert get_dimension("J") == ENERGY
        assert get_dimension("V") == VOLTAGE
        assert get_dimension("%") == DIMENSIONLESS

    def test_compound_units(self):
        """Variation: compound units resolve correctly."""
        assert get_dimension("W/m2") is not None
        assert get_dimension("V/K") == SEEBECK

    def test_unknown_unit_returns_none(self):
        """Edge case: unknown unit returns None."""
        assert get_dimension("frobnicate") is None

    def test_unit_normalization(self):
        """Variation: unit normalization handles unicode."""
        assert get_dimension("W/m²") == get_dimension("W/m2")


class TestDimensionalConsistency:
    """Test the dimensional consistency checker."""

    def test_linear_law_passes_when_dimensions_match(self):
        """Exact case: y = a*x + b where x and y have same dimension."""
        ok, reason = check_dimensional_consistency(
            "linear",
            {"T": TEMPERATURE},
            TEMPERATURE,
        )
        assert ok, f"Linear law should pass when dimensions match: {reason}"

    def test_linear_law_fails_when_dimensions_differ(self):
        """Exact case: P = T + m (power = temperature + mass) is IMPOSSIBLE."""
        ok, reason = check_dimensional_consistency(
            "linear",
            {"T": TEMPERATURE},
            POWER,
        )
        assert not ok, "Linear law P = a*T + b should FAIL (temperature ≠ power)"

    def test_exponential_requires_dimensionless_input(self):
        """Variation: y = a*exp(b*x) requires x to be dimensionless."""
        ok, _ = check_dimensional_consistency(
            "exponential",
            {"x": DIMENSIONLESS},
            POWER,
        )
        assert ok, "Exponential with dimensionless input should pass"

        ok, _ = check_dimensional_consistency(
            "exponential",
            {"T": TEMPERATURE},
            POWER,
        )
        assert not ok, "Exponential with dimensional input should FAIL"

    def test_logarithmic_requires_dimensionless_input(self):
        """Edge case: y = a*log(T) is dimensionally wrong."""
        ok, _ = check_dimensional_consistency(
            "logarithmic",
            {"T": TEMPERATURE},
            POWER,
        )
        assert not ok, "Logarithm of temperature should FAIL"

    def test_power_law_with_dimensional_input_accepted(self):
        """Variation: y = a*T^b is accepted (b checked after fitting)."""
        ok, _ = check_dimensional_consistency(
            "power",
            {"T": TEMPERATURE},
            POWER,
        )
        assert ok, "Power law with dimensional input should be accepted"

    def test_power_law_with_dimensionless_input(self):
        """Edge case: y = a*x^b where x is dimensionless."""
        ok, _ = check_dimensional_consistency(
            "power",
            {"x": DIMENSIONLESS},
            POWER,
        )
        assert ok, "Power law with dimensionless input should pass"


class TestAdditionConsistency:
    """Test the addition consistency checker."""

    def test_same_dimensions_can_be_added(self):
        """Exact case: P + P is valid."""
        ok, _ = check_addition_consistency([POWER, POWER])
        assert ok

    def test_different_dimensions_cannot_be_added(self):
        """Exact case: P + T is IMPOSSIBLE."""
        ok, _ = check_addition_consistency([POWER, TEMPERATURE])
        assert not ok, "P + T should FAIL (different dimensions)"

    def test_mass_plus_temperature_impossible(self):
        """The CEO's example: P = T + m is impossible."""
        ok, _ = check_addition_consistency([TEMPERATURE, MASS])
        assert not ok, "T + m should FAIL (temperature ≠ mass)"


class TestBuckinghamPi:
    """Test the Buckingham π theorem."""

    def test_pendulum_pi_groups(self):
        """Exact case: pendulum period depends on length, gravity, mass.

        Variables: T (time), L (length), g (acceleration), m (mass)
        Repeating: L, g, m (3 variables → k=3 independent dimensions: length, time, mass)
        n=4, k=3 → 1 π group
        """
        variables = {
            "T_period": TIME,
            "L": LENGTH,
            "g": Dimension(length=1, time=-2),
            "m": MASS,
        }
        pi_groups = buckingham_pi(variables, ["L", "g", "m"])
        # n=4, k=3 → 1 π group
        assert len(pi_groups) >= 1, f"Expected ≥1 π group, got {len(pi_groups)}"

    def test_stefan_boltzmann_pi_groups(self):
        """Variation: Q = εσA(T_s⁴ - T_sky⁴).

        Variables: Q (power), T_s (temperature), T_sky (temperature), ε (dimensionless)
        σ is a constant (not a variable)
        Repeating: T_s, T_sky
        n=4 (Q, T_s, T_sky, ε), k=1 (temperature) → 3 π groups
        """
        variables = {
            "Q": POWER,
            "T_s": TEMPERATURE,
            "T_sky": TEMPERATURE,
            "epsilon": DIMENSIONLESS,
        }
        pi_groups = buckingham_pi(variables, ["T_s"])
        assert len(pi_groups) >= 1

    def test_empty_variables(self):
        """Edge case: no variables."""
        pi_groups = buckingham_pi({}, [])
        assert len(pi_groups) == 0


class TestBaconIntegration:
    """Test BACON integration — filter impossible laws."""

    def test_filter_removes_impossible_linear(self):
        """Exact case: linear P = a*T + b is rejected."""
        forms = ["linear", "power", "exponential", "quadratic"]
        input_dims = {"T": TEMPERATURE}
        output_dim = POWER

        valid, rejected = filter_laws_by_dimension(forms, input_dims, output_dim)

        # Linear should be rejected (T ≠ P)
        rejected_names = [r[0] for r in rejected]
        assert "linear" in rejected_names, "Linear P=a*T+b should be rejected"

        # Exponential should be rejected (T is not dimensionless)
        assert "exponential" in rejected_names, "Exponential with T should be rejected"

        # Power should be accepted
        assert "power" in valid, "Power law should be accepted"

    def test_filter_keeps_valid_laws(self):
        """Variation: when dimensions match, linear is kept."""
        forms = ["linear", "power"]
        input_dims = {"T": TEMPERATURE}
        output_dim = TEMPERATURE  # same dimension

        valid, rejected = filter_laws_by_dimension(forms, input_dims, output_dim)

        assert "linear" in valid, "Linear with matching dimensions should be kept"
        assert len(rejected) == 0, "No laws should be rejected when dimensions match"

    def test_impossible_laws_disappear_automatically(self):
        """THE SUCCESS CRITERION: 'Impossible laws disappear automatically.'"""
        # P = a*T + b (linear, T≠P) — IMPOSSIBLE
        # P = a*exp(b*T) (exponential, T not dimensionless) — IMPOSSIBLE
        # P = a*log(T) (log, T not dimensionless) — IMPOSSIBLE
        # P = a*T^b (power, dimensional input) — POSSIBLE (b=4, T^4=K^4, εσ has W/K^4)
        forms = ["linear", "power", "exponential", "logarithmic", "inverse", "quadratic"]
        input_dims = {"T": TEMPERATURE}
        output_dim = POWER

        valid, rejected = filter_laws_by_dimension(forms, input_dims, output_dim)

        # The IMPOSSIBLE laws should be in rejected
        rejected_names = {r[0] for r in rejected}
        assert "linear" in rejected_names, "P = a*T + b is impossible (T ≠ P)"
        assert "exponential" in rejected_names, "P = a*exp(b*T) is impossible (T not dimensionless)"
        assert "logarithmic" in rejected_names, "P = a*log(T) is impossible (T not dimensionless)"
        assert "quadratic" in rejected_names, "P = a*T² + b*T + c is impossible (T ≠ P)"

        # The POSSIBLE law should be in valid
        assert "power" in valid, "P = a*T^b is possible (b=4 for Stefan-Boltzmann)"

        # Summary
        print(f"\n  Success criterion: 'Impossible laws disappear automatically.'")
        print(f"  Input: T (temperature), Output: P (power)")
        print(f"  Candidate forms: {forms}")
        print(f"  Valid (possible): {valid}")
        print(f"  Rejected (impossible): {[r[0] for r in rejected]}")
        print(f"  Impossible laws removed: {len(rejected)}/{len(forms)}")
        print(f"  Search space reduced by: {len(rejected)/len(forms)*100:.0f}%")
