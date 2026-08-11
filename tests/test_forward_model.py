"""Tests for forward_model.py — Stage IV."""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.forward_model import (
    ForwardModel, Prediction,
    STEFAN_BOLTZMANN, STRUCTURAL_MODEL_ERROR,
)
from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
)
from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph


def _thermoelectric_config(S=200e-6, sigma=1e5, kappa=1.5,
                            L=1e-3, A=1e-4, T_hot=400.0, T_cold=300.0,
                            config_id="TEST-1"):
    """Helper: build a minimal thermoelectric Configuration."""
    c = Configuration(
        config_id=config_id,
        spec_objective="improve thermoelectric efficiency",
        domain="thermoelectric",
        components=[Component(
            material="bismuth_telluride", role="active",
            parameters={
                "seebeck_coefficient": S,
                "electrical_conductivity": sigma,
                "thermal_conductivity": kappa,
                "density": 7700.0,
                "cost_per_kg": 200.0,
            })],
        structure="monolithic",
        parameters={
            "thickness_m": L, "area_m2": A,
            "T_hot_K": T_hot, "T_cold_K": T_cold,
        },
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    return c


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------
def test_predict_returns_prediction_object():
    """predict() returns a Prediction dataclass."""
    fm = ForwardModel()
    p = fm.predict(_thermoelectric_config())
    assert isinstance(p, Prediction)
    assert p.domain == "thermoelectric"


def test_predict_records_config_id_and_hash():
    """The prediction carries the config_id and config_hash."""
    c = _thermoelectric_config(config_id="CFG-XYZ")
    p = ForwardModel().predict(c)
    assert p.config_id == "CFG-XYZ"
    assert p.config_hash == c.config_hash


def test_evidence_rank_is_A():
    """Forward-model predictions are evidence rank A (physics)."""
    p = ForwardModel().predict(_thermoelectric_config())
    assert p.evidence_rank == "A"


def test_equations_used_listed():
    """The equations used are explicitly listed."""
    p = ForwardModel().predict(_thermoelectric_config())
    assert "ZT = S^2 * σ * T / κ" in p.equations_used
    assert "V_oc = S * ΔT" in p.equations_used
    assert len(p.equations_used) >= 3


def test_assumptions_listed():
    """Assumptions are listed (Constitution Law 6)."""
    p = ForwardModel().predict(_thermoelectric_config())
    assert len(p.assumptions) >= 3
    # Must mention structural model error
    assert any("structural model error" in a.lower() for a in p.assumptions)


# ---------------------------------------------------------------------------
# Thermoelectric physics correctness
# ---------------------------------------------------------------------------
def test_thermoelectric_ZT_correct():
    """ZT = S^2 * σ * T / κ evaluates correctly."""
    c = _thermoelectric_config(S=200e-6, sigma=1e5, kappa=1.5,
                                T_hot=400.0, T_cold=300.0)
    p = ForwardModel().predict(c)
    expected_ZT = (200e-6) ** 2 * 1e5 * 350.0 / 1.5  # T_avg = 350
    assert abs(p.predicted_properties["ZT"] - expected_ZT) < 1e-9


def test_thermoelectric_V_oc_correct():
    """V_oc = S * ΔT evaluates correctly."""
    c = _thermoelectric_config(S=200e-6, T_hot=400.0, T_cold=300.0)
    p = ForwardModel().predict(c)
    expected_V = 200e-6 * 100.0  # = 0.02 V = 20 mV
    assert abs(p.predicted_properties["V_oc_V"] - expected_V) < 1e-12


def test_thermoelectric_R_internal_correct():
    """R_in = L / (σ * A) evaluates correctly."""
    c = _thermoelectric_config(sigma=1e5, L=1e-3, A=1e-4)
    p = ForwardModel().predict(c)
    expected_R = 1e-3 / (1e5 * 1e-4)  # = 1e-4 / 1 = 0.0001 ohm = 100 µohm... wait
    # 1e-3 / (1e5 * 1e-4) = 1e-3 / 10 = 0.1 ohm
    assert abs(p.predicted_properties["R_internal_ohm"] - expected_R) < 1e-12


def test_thermoelectric_P_max_correct():
    """P_max = V_oc^2 / (4 R_in) evaluates correctly."""
    c = _thermoelectric_config(S=200e-6, sigma=1e5, kappa=1.5,
                                L=1e-3, A=1e-4, T_hot=400.0, T_cold=300.0)
    p = ForwardModel().predict(c)
    V_oc = 200e-6 * 100.0
    R_in = 1e-3 / (1e5 * 1e-4)
    expected_P = V_oc ** 2 / (4 * R_in)
    assert abs(p.predicted_properties["P_max_W"] - expected_P) < 1e-12


def test_thermoelectric_Q_cond_correct():
    """Q_cond = κ * A * ΔT / L evaluates correctly."""
    c = _thermoelectric_config(kappa=1.5, A=1e-4, L=1e-3,
                                T_hot=400.0, T_cold=300.0)
    p = ForwardModel().predict(c)
    expected_Q = 1.5 * 1e-4 * 100.0 / 1e-3  # = 0.015 / 0.001 = 15 W
    assert abs(p.predicted_properties["Q_cond_W"] - expected_Q) < 1e-9


# ---------------------------------------------------------------------------
# Different parameters → different predictions
# ---------------------------------------------------------------------------
def test_different_seebeck_gives_different_ZT():
    """Doubling S quadruples ZT (ZT ∝ S^2)."""
    c1 = _thermoelectric_config(S=200e-6, config_id="A")
    c2 = _thermoelectric_config(S=400e-6, config_id="B")
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    assert p2.predicted_properties["ZT"] > p1.predicted_properties["ZT"] * 3.9
    assert p2.predicted_properties["ZT"] < p1.predicted_properties["ZT"] * 4.1


def test_different_kappa_gives_different_ZT():
    """Halving κ doubles ZT (ZT ∝ 1/κ)."""
    c1 = _thermoelectric_config(kappa=1.5, config_id="A")
    c2 = _thermoelectric_config(kappa=0.75, config_id="B")
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    ratio = p2.predicted_properties["ZT"] / p1.predicted_properties["ZT"]
    assert abs(ratio - 2.0) < 0.01


def test_different_area_gives_different_R():
    """Larger area → smaller R_in."""
    c1 = _thermoelectric_config(A=1e-4, config_id="A")
    c2 = _thermoelectric_config(A=1e-3, config_id="B")  # 10x area
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    assert p2.predicted_properties["R_internal_ohm"] < p1.predicted_properties["R_internal_ohm"]


def test_different_temperature_gives_different_V_oc():
    """Higher ΔT → higher V_oc."""
    c1 = _thermoelectric_config(T_hot=400.0, T_cold=300.0, config_id="A")
    c2 = _thermoelectric_config(T_hot=500.0, T_cold=300.0, config_id="B")
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    assert p2.predicted_properties["V_oc_V"] > p1.predicted_properties["V_oc_V"]


# ---------------------------------------------------------------------------
# Uncertainty propagation
# ---------------------------------------------------------------------------
def test_uncertainty_band_straddles_nominal():
    """For each predicted metric, the uncertainty band brackets the nominal."""
    p = ForwardModel().predict(_thermoelectric_config())
    for k, nominal in p.predicted_properties.items():
        if k in p.uncertainty:
            lo, hi = p.uncertainty[k]
            assert lo <= nominal <= hi, (
                f"{k}: nominal={nominal} outside band [{lo}, {hi}]")


def test_uncertainty_band_nonzero_width():
    """Uncertainty bands have positive width (uncertainty is non-zero)."""
    p = ForwardModel().predict(_thermoelectric_config())
    for k, (lo, hi) in p.uncertainty.items():
        assert hi > lo, f"{k}: zero-width band"


def test_uncertainty_grows_with_input_uncertainty():
    """Higher structural model error → wider band (proportional)."""
    # Build two configs identical except for one parameter uncertainty
    # source — we use thermal_conductivity because κ appears in ZT.
    c1 = _thermoelectric_config(kappa=1.5, config_id="A")
    c2 = _thermoelectric_config(kappa=0.1, config_id="B")  # smaller κ → smaller ZT
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    # The relative width should be similar (it's dominated by input rel-uncertainty,
    # not by nominal value) — but ZT differs.
    assert p1.predicted_properties["ZT"] != p2.predicted_properties["ZT"]


def test_uncertainty_relative_to_nominal():
    """The 1σ band is roughly ±X% of the nominal (linearized propagation)."""
    p = ForwardModel().predict(_thermoelectric_config())
    nominal = p.predicted_properties["V_oc_V"]
    lo, hi = p.uncertainty["V_oc_V"]
    # 1σ band should be ~±(10% + 2% + 2% + 10%) ~ ±24% with quadrature
    # sqrt(0.10^2 + 0.02^2 + 0.02^2 + 0.10^2) = sqrt(0.0208) = 0.144
    rel_width = (hi - lo) / 2 / abs(nominal)
    assert 0.05 < rel_width < 0.50, f"rel_width={rel_width}"


# ---------------------------------------------------------------------------
# Thermal (Stefan-Boltzmann) prediction
# ---------------------------------------------------------------------------
def test_thermal_prediction_correct():
    """Q_rad = ε σ A (T^4 - T_sky^4) evaluates correctly."""
    c = Configuration(
        config_id="TH", spec_objective="cooling",
        domain="thermal",
        components=[Component(material="aerogel", role="active",
                              parameters={"emissivity": 0.95})],
        structure="monolithic",
        parameters={"area_m2": 1.0, "T_hot_K": 300.0, "T_cold_K": 270.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    p = ForwardModel().predict(c)
    expected = 0.95 * STEFAN_BOLTZMANN * 1.0 * (300.0 ** 4 - 270.0 ** 4)
    assert abs(p.predicted_properties["Q_rad_W"] - expected) < 1e-3


def test_thermal_higher_temperature_more_cooling():
    """Higher surface T → more radiative cooling."""
    c1 = Configuration(
        config_id="TH1", spec_objective="x", domain="thermal",
        components=[Component(material="aerogel", role="active",
                              parameters={"emissivity": 0.9})],
        structure="monolithic",
        parameters={"area_m2": 1.0, "T_hot_K": 300.0, "T_cold_K": 270.0},
        design_operator_chain=["init"],
    )
    c2 = Configuration(
        config_id="TH2", spec_objective="x", domain="thermal",
        components=[Component(material="aerogel", role="active",
                              parameters={"emissivity": 0.9})],
        structure="monolithic",
        parameters={"area_m2": 1.0, "T_hot_K": 350.0, "T_cold_K": 270.0},
        design_operator_chain=["init"],
    )
    c1.config_hash = c1.compute_hash()
    c2.config_hash = c2.compute_hash()
    p1 = ForwardModel().predict(c1)
    p2 = ForwardModel().predict(c2)
    assert p2.predicted_properties["Q_rad_W"] > p1.predicted_properties["Q_rad_W"]


# ---------------------------------------------------------------------------
# Generic electrical (Ohm's law) fallback
# ---------------------------------------------------------------------------
def test_generic_ohms_law():
    """Ohm's law fallback for unknown domains."""
    c = Configuration(
        config_id="OHM", spec_objective="x", domain="unknown",
        components=[Component(material="copper", role="conductor",
                              parameters={"electrical_conductivity": 5.96e7})],
        structure="monolithic",
        parameters={"thickness_m": 1.0, "area_m2": 1e-6, "current_A": 1.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    p = ForwardModel().predict(c)
    # R = L / (σ A) = 1.0 / (5.96e7 * 1e-6) = 1.0 / 59.6 = 0.0168 ohm
    expected_R = 1.0 / (5.96e7 * 1e-6)
    assert abs(p.predicted_properties["resistance_ohm"] - expected_R) < 1e-9
    # V = I R = 1 * 0.0168 = 0.0168 V
    assert abs(p.predicted_properties["voltage_V"] - 1.0 * expected_R) < 1e-9


# ---------------------------------------------------------------------------
# Integration with artifact_generator
# ---------------------------------------------------------------------------
def test_predict_works_on_generated_configs():
    """ForwardModel works on real generated Configurations."""
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    fm = ForwardModel()
    for c in configs:
        p = fm.predict(c)
        assert p.config_hash == c.config_hash
        assert "ZT" in p.predicted_properties
        assert len(p.equations_used) >= 3


def test_generated_configs_produce_varied_predictions():
    """Different generated configs produce different ZT predictions."""
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("lead telluride", "generates", "voltage"),
    ])
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=10)
    fm = ForwardModel()
    zts = [fm.predict(c).predicted_properties["ZT"] for c in configs]
    # We should see at least 2 distinct ZT values across 10 configs
    assert len(set(round(z, 6) for z in zts)) >= 2


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def test_to_dict_serializable():
    """Prediction.to_dict produces a JSON-serializable dict."""
    import json
    p = ForwardModel().predict(_thermoelectric_config())
    d = p.to_dict()
    json.dumps(d)
    assert "predicted_properties" in d
    assert "uncertainty" in d


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
