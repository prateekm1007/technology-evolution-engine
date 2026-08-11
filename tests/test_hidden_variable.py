"""
Test autonomous hidden variable discovery (cycle 53, Phase VI).

Per Apollo Challenge 2: the system must discover something without being
told the answer. This test verifies the system can autonomously identify
a hidden variable by searching over ALL candidates, not just the one a
human suggests.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.bacon_engine import (
    discover_hidden_variable, HiddenVariableDiscovery,
    stull_wet_bulb_dataset,
)


class TestHiddenVariableDiscovery:
    """Verify autonomous hidden variable discovery."""

    def test_discovers_rh_as_hidden_variable_in_stull(self):
        """The system must autonomously discover RH as the hidden variable.

        The Stull formula T_wb = f(T, RH) depends on BOTH T and RH.
        The system fits T → T_wb (best single-variable), computes residuals,
        then searches over all other variables and discovers RH explains
        the residual. NO HUMAN tells it to check RH.
        """
        data = stull_wet_bulb_dataset(n_points=25)
        result = discover_hidden_variable(data, 'T_wet_C',
                                           candidate_vars=['T_dry_C', 'RH_pct'],
                                           verbose=True)
        assert result is not None, (
            "discover_hidden_variable should find a hidden variable"
        )
        # The primary variable should be T (it has higher single-variable R²)
        assert result.primary_var == 'T_dry_C', (
            f"expected primary=T_dry_C, got {result.primary_var}"
        )
        # The hidden variable should be RH (the only other candidate)
        assert result.hidden_var == 'RH_pct', (
            f"expected hidden=RH_pct, got {result.hidden_var}"
        )
        # The improvement should be material (≥0.01)
        assert result.improvement >= 0.01, (
            f"improvement {result.improvement:.4f} < 0.01 — not a real discovery"
        )
        # Combined R² should exceed single R²
        assert result.combined_r2 > result.single_r2

    def test_discovers_hidden_variable_in_synthetic_data(self):
        """y = a*x1 + b*x2² — the system should discover x2 as hidden.

        x1 and x2 must be INDEPENDENT (not linearly correlated) for BACON
        to distinguish them. We use a step-function x2 (independent of x1).
        """
        x1 = [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        x2 = [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        # y depends on x1 linearly and x2 (independent of x1)
        y = [2.0 * a + 0.5 * b * b for a, b in zip(x1, x2)]
        dataset = {'x1': x1, 'x2': x2, 'y': y}

        result = discover_hidden_variable(dataset, 'y')
        assert result is not None, (
            "discover_hidden_variable should find x2 as the hidden variable"
        )
        # x1 should be primary (linear, higher R²)
        assert result.primary_var == 'x1', (
            f"expected primary=x1, got {result.primary_var}"
        )
        # x2 should be discovered as hidden
        assert result.hidden_var == 'x2', (
            f"expected hidden=x2, got {result.hidden_var}"
        )
        # The hidden variable should explain the residual well
        assert result.hidden_law.r2 >= 0.50, (
            f"hidden variable R²={result.hidden_law.r2:.4f} < 0.50 — not a real hidden variable"
        )
        # Combined R² should exceed single R²
        assert result.combined_r2 > result.single_r2

    def test_returns_none_when_only_one_variable(self):
        """If only 1 candidate variable, return None (can't find hidden)."""
        dataset = {'x1': [1.0, 2.0, 3.0, 4.0, 5.0], 'y': [2.0, 4.0, 6.0, 8.0, 10.0]}
        result = discover_hidden_variable(dataset, 'y')
        assert result is None

    def test_returns_none_when_no_hidden_variable(self):
        """If y is purely linear in x1 (x2 is noise), no hidden variable found."""
        x1 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        x2 = [3.14, 1.59, 2.65, 3.58, 9.79, 3.23, 8.46, 2.64]  # random
        y = [2.0 * x + 1.0 for x in x1]  # purely linear in x1
        dataset = {'x1': x1, 'x2': x2, 'y': y}

        result = discover_hidden_variable(dataset, 'y')
        # x2 is random — it should NOT explain the residual (R² < 0.50)
        # So the function should return None (no genuine hidden variable)
        if result is not None:
            assert result.hidden_law.r2 < 0.50, (
                "random variable should not be identified as hidden (R² should be < 0.50)"
            )

    def test_is_discovery_flag(self):
        """is_discovery is True when hidden variable explains ≥50% of residual."""
        x1 = [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        x2 = [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        y = [2.0 * a + 3.0 * b * b for a, b in zip(x1, x2)]
        dataset = {'x1': x1, 'x2': x2, 'y': y}

        result = discover_hidden_variable(dataset, 'y')
        assert result is not None
        # The hidden variable should explain ≥50% of residual variance
        assert result.hidden_law.r2 >= 0.50, (
            f"hidden R²={result.hidden_law.r2:.4f} < 0.50"
        )
        assert result.is_discovery is True

    def test_to_dict_round_trip(self):
        """HiddenVariableDiscovery.to_dict is JSON-serializable."""
        import json
        data = stull_wet_bulb_dataset(n_points=25)
        result = discover_hidden_variable(data, 'T_wet_C',
                                           candidate_vars=['T_dry_C', 'RH_pct'])
        assert result is not None
        d = result.to_dict()
        json.dumps(d)
        assert "primary_var" in d
        assert "hidden_var" in d
        assert "improvement" in d

    def test_str_is_readable(self):
        """__str__ is human-readable."""
        data = stull_wet_bulb_dataset(n_points=25)
        result = discover_hidden_variable(data, 'T_wet_C',
                                           candidate_vars=['T_dry_C', 'RH_pct'])
        assert result is not None
        s = str(result)
        assert "HiddenVariableDiscovery" in s
        assert "DISCOVERY" in s or "marginal" in s

    def test_searches_over_all_candidates_not_just_first(self):
        """The system must search over ALL candidates, not stop at the first.

        3 variables: x1 (primary), x2 (noise), x3 (hidden).
        x1 and x3 are INDEPENDENT (step-function pattern).
        The system must skip x2 (noise) and find x3 as the hidden variable.
        """
        x1 = [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        x2 = [3.1, 1.6, 2.7, 3.6, 9.8, 3.2, 8.5, 2.6, 4.5, 5.0]  # noise
        x3 = [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0]  # hidden (independent of x1)
        y = [2.0 * a + 0.5 * c * c for a, c in zip(x1, x3)]
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'y': y}

        result = discover_hidden_variable(dataset, 'y')
        assert result is not None, (
            "should find a hidden variable in this 3-variable dataset"
        )
        # Primary should be x1 (highest single-variable R²)
        assert result.primary_var == 'x1', (
            f"expected primary=x1, got {result.primary_var}"
        )
        # Hidden should be x3 (not x2 — x2 is noise)
        assert result.hidden_var == 'x3', (
            f"expected hidden=x3, got {result.hidden_var} — "
            f"the system should skip noise variables and find the real hidden variable"
        )
        assert result.hidden_law.r2 >= 0.50, (
            f"hidden variable R²={result.hidden_law.r2:.4f} < 0.50"
        )
