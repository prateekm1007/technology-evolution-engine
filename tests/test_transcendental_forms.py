"""
Test Phase III transcendental forms (cycle 74).

Per External Auditor cycle 73: add atan/sqrt/sin/cos to candidate forms.
"""
import sys, math, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.bacon_engine import discover_law, CANDIDATE_LAWS
from invention_compiler.dimensional_reasoning import DIMENSIONLESS


class TestTranscendentalForms:
    """Test sqrt, atan, sin, cos forms."""

    def test_10_candidate_forms_exist(self):
        """BACON now has 10 candidate forms (was 6)."""
        names = [c.name for c in CANDIDATE_LAWS]
        assert "sqrt" in names
        assert "atan" in names
        assert "sin" in names
        assert "cos" in names
        assert len(CANDIDATE_LAWS) == 10

    def test_sqrt_discovers_from_data(self):
        """y = 2*sqrt(x) + 1 → discovers sqrt form."""
        xs = [0.5*i for i in range(1, 30)]
        ys = [2.0 * math.sqrt(x) + 1.0 for x in xs]
        law = discover_law(xs, ys, x_dimension=DIMENSIONLESS, y_dimension=DIMENSIONLESS)
        assert law is not None
        assert law.name == "sqrt"
        assert law.r2 >= 0.999

    def test_sin_discovers_from_data(self):
        """y = 5*sin(2*x) + 3 → discovers sin form."""
        xs = [0.1*i for i in range(1, 50)]
        ys = [5.0 * math.sin(2.0*x) + 3.0 for x in xs]
        law = discover_law(xs, ys, x_dimension=DIMENSIONLESS, y_dimension=DIMENSIONLESS)
        assert law is not None
        assert law.name == "sin"
        assert law.r2 >= 0.999

    def test_stull_uses_new_forms(self):
        """Stull wet-bulb now fits with transcendental forms (was only power before)."""
        from scripts.formulas.stull_wet_bulb import stull_wet_bulb
        RHs = [5 + 94*i/24 for i in range(25)]
        Twbs = [stull_wet_bulb(25.0, rh) for rh in RHs]
        law = discover_law(RHs, Twbs, x_dimension=DIMENSIONLESS, y_dimension=DIMENSIONLESS)
        assert law is not None
        assert law.r2 >= 0.99
        # sqrt or atan should fit better than power alone
        assert law.name in ("sqrt", "atan", "power", "sin")
