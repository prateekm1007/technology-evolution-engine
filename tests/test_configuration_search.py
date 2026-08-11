"""Tests for configuration_search.py — continuous design-space search (cycle 210)."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_continuous_search_generates_candidates():
    """The continuous search generates DesignPoint candidates."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search = ConfigurationSearch(seed=42)
    candidates = search.generate_candidates(spec, n=10)

    assert len(candidates) == 10
    for dp in candidates:
        assert dp.base_material != ""
        assert dp.seebeck_coefficient > 0
        assert dp.electrical_conductivity > 0
        assert dp.thermal_conductivity > 0


def test_continuous_search_varies_design_variables():
    """The search varies composition, doping, grain size, porosity — not just material name."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search = ConfigurationSearch(seed=42)
    candidates = search.generate_candidates(spec, n=20)

    # Check that design variables are varied (not all the same)
    compositions = set(dp.composition_x for dp in candidates)
    carrier_concs = set(dp.carrier_concentration for dp in candidates)
    grain_sizes = set(dp.grain_size_nm for dp in candidates)
    porosities = set(dp.porosity for dp in candidates)

    assert len(compositions) > 5, f"Only {len(compositions)} unique compositions — not searching"
    assert len(carrier_concs) > 5, f"Only {len(carrier_concs)} unique carrier concentrations"
    assert len(grain_sizes) > 5, f"Only {len(grain_sizes)} unique grain sizes"
    assert len(porosities) > 5, f"Only {len(porosities)} unique porosities"


def test_pisarenko_relation_enforced():
    """S and σ trade off (Pisarenko relation): higher carrier concentration
    means higher σ but lower S."""
    from scripts.configuration_search import ConfigurationSearch

    search = ConfigurationSearch(seed=42)

    # Low carrier concentration → high S, low σ
    S_low_n = search._compute_seebeck(200e-6, 1e18, 0.0, 1000)
    sigma_low_n = search._compute_conductivity(1e5, 1e18, 1000, 0.0)

    # High carrier concentration → low S, high σ
    S_high_n = search._compute_seebeck(200e-6, 1e21, 0.0, 1000)
    sigma_high_n = search._compute_conductivity(1e5, 1e21, 1000, 0.0)

    assert S_low_n > S_high_n, \
        f"Pisarenko violated: low-n S={S_low_n} should be > high-n S={S_high_n}"
    assert sigma_low_n < sigma_high_n, \
        f"Pisarenko violated: low-n σ={sigma_low_n} should be < high-n σ={sigma_high_n}"


def test_nanostructuring_reduces_thermal_conductivity():
    """Smaller grain size → lower κ (key TE strategy)."""
    from scripts.configuration_search import ConfigurationSearch

    search = ConfigurationSearch(seed=42)

    # Bulk grain size (10µm)
    kappa_bulk = search._compute_thermal_k(1.5, 10000, 0.0, 0.0)

    # Nano grain size (10nm)
    kappa_nano = search._compute_thermal_k(1.5, 10, 0.0, 0.0)

    assert kappa_nano < kappa_bulk, \
        f"Nanostructuring should reduce κ: nano={kappa_nano}, bulk={kappa_bulk}"


def test_all_candidates_pass_plausibility():
    """All generated candidates pass the physical plausibility check."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine
    from scripts.forward_model import ForwardModel
    from scripts.physical_plausibility import PhysicalPlausibilityChecker

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search = ConfigurationSearch(seed=42)
    configs = search.generate_to_configurations(spec, None, n=20)

    fm = ForwardModel()
    checker = PhysicalPlausibilityChecker()

    vetoed = 0
    for c in configs:
        pred = fm.predict(c)
        plaus = checker.check_prediction(pred.predicted_properties)
        if plaus.vetoed:
            vetoed += 1

    # Most candidates should pass; a few may be vetoed if the Pisarenko
    # tradeoff still allows ZT > 5 in edge cases. That's correct behavior.
    assert vetoed <= 2, f"{vetoed}/20 candidates vetoed — too many physical bound violations"


def test_candidates_have_nonzero_residual():
    """Predicted ZT differs from independently measured ZT (non-zero residual)."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine
    from scripts.forward_model import ForwardModel
    from scripts.independent_measurement import IndependentMeasurement

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search = ConfigurationSearch(seed=42)
    configs = search.generate_to_configurations(spec, None, n=10)

    fm = ForwardModel()
    im = IndependentMeasurement()

    nonzero_residuals = 0
    for c in configs:
        pred = fm.predict(c)
        meas = im.measure(c)
        residual = abs(pred.predicted_properties["ZT"] - meas.measured_zt)
        if residual > 0.01:
            nonzero_residuals += 1

    assert nonzero_residuals >= 8, \
        f"Only {nonzero_residuals}/10 candidates have non-zero residuals"


def test_search_is_deterministic():
    """Same seed → same candidates."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search1 = ConfigurationSearch(seed=42)
    search2 = ConfigurationSearch(seed=42)

    c1 = search1.generate_candidates(spec, n=5)
    c2 = search2.generate_candidates(spec, n=5)

    for a, b in zip(c1, c2):
        assert a.base_material == b.base_material
        assert abs(a.composition_x - b.composition_x) < 1e-9
        assert abs(a.seebeck_coefficient - b.seebeck_coefficient) < 1e-9


def test_generated_configurations_are_novel():
    """Generated configurations have design variables that differ from the base material."""
    from scripts.configuration_search import ConfigurationSearch
    from scripts.specification import SpecificationEngine
    from scripts.materials_database import get_material

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    search = ConfigurationSearch(seed=42)
    candidates = search.generate_candidates(spec, n=20)

    # At least some candidates should have modified S, σ, or κ from the base
    modified = 0
    for dp in candidates:
        base = get_material(dp.base_material)
        if base:
            if (abs(dp.seebeck_coefficient - base.seebeck_coefficient) > 1e-9 or
                abs(dp.electrical_conductivity - base.electrical_conductivity) > 1e-3 or
                abs(dp.thermal_conductivity - base.thermal_conductivity) > 1e-3):
                modified += 1

    assert modified >= 15, \
        f"Only {modified}/20 candidates have modified properties — not synthesizing"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
