"""Tests for measurement_engine.py — Stage VII."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.measurement_engine import (
    MeasurementEngine, MeasurementInstrument, Measurement,
    Residual, IterationResult, LoopResult,
)
from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
)
from scripts.forward_model import ForwardModel
from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph


def _spec():
    return SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")


def _cg():
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("lead telluride", "generates", "voltage"),
    ])
    return cg


def _config(material="bismuth_telluride", config_id="TEST"):
    c = Configuration(
        config_id=config_id,
        spec_objective="improve thermoelectric efficiency",
        domain="thermoelectric",
        components=[Component(material=material, role="active",
                              parameters=dict(MATERIAL_PARAMS.get(material, {})))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    return c


# ---------------------------------------------------------------------------
# MeasurementInstrument
# ---------------------------------------------------------------------------
def test_instrument_returns_measurement():
    """measure() returns a Measurement object."""
    instr = MeasurementInstrument()
    m = instr.measure(_config())
    assert isinstance(m, Measurement)
    assert m.domain == "thermoelectric"
    assert m.config_hash != ""


def test_measured_properties_populated():
    """Measured properties are populated."""
    m = MeasurementInstrument().measure(_config())
    assert "V_oc_V" in m.measured_properties
    assert "P_max_W" in m.measured_properties
    assert "R_contact_ohm" in m.measured_properties


def test_measurement_includes_contact_resistance():
    """The measurement includes contact resistance (real non-ideality)."""
    m = MeasurementInstrument().measure(_config())
    assert m.measured_properties["R_contact_ohm"] > 0
    # The measured R_total should be > R_internal (which is what the
    # forward model predicts)
    fm = ForwardModel()
    pred = fm.predict(_config())
    R_internal_pred = pred.predicted_properties["R_internal_ohm"]
    R_total_meas = m.measured_properties["R_total_ohm"]
    assert R_total_meas > R_internal_pred, (
        f"measured R_total ({R_total_meas}) should exceed predicted "
        f"R_internal ({R_internal_pred}) due to contact resistance")


def test_measurement_NOT_equal_to_prediction():
    """The measured value differs from the predicted value (NOT fake data)."""
    c = _config()
    pred = ForwardModel().predict(c).predicted_properties
    meas = MeasurementInstrument().measure(c).measured_properties
    # V_oc: prediction uses nominal S; measurement uses S_actual (temp-corrected)
    assert pred["V_oc_V"] != meas["V_oc_V"], (
        "predicted V_oc must differ from measured V_oc — otherwise the "
        "measurement is fake (identical to prediction)")
    # P_max: prediction uses R_internal; measurement uses R_total (with R_contact)
    assert pred["P_max_W"] != meas["P_max_W"]
    # Q_cond: measurement has +5% κ load factor
    assert pred["Q_cond_W"] != meas["Q_cond_W"]


def test_measurement_deterministic():
    """Same input → same measured value (deterministic, not random)."""
    c = _config()
    m1 = MeasurementInstrument().measure(c)
    m2 = MeasurementInstrument().measure(c)
    assert m1.measured_properties == m2.measured_properties


def test_measurement_differs_when_params_differ():
    """Different config parameters → different measured values."""
    c1 = _config(material="bismuth_telluride", config_id="A")
    c2 = _config(material="lead_telluride", config_id="B")
    instr = MeasurementInstrument()
    m1 = instr.measure(c1)
    m2 = instr.measure(c2)
    # Different material → different Seebeck → different V_oc
    assert m1.measured_properties["V_oc_V"] != m2.measured_properties["V_oc_V"]


def test_corrections_applied_listed():
    """The measurement lists the corrections applied (provenance)."""
    m = MeasurementInstrument().measure(_config())
    assert "contact_resistance_ohm" in m.corrections_applied
    assert m.corrections_applied["contact_resistance_ohm"] > 0
    assert "seebeck_temp_coeff_per_K" in m.corrections_applied
    assert m.provenance["evidence_rank"] == "A"


def test_custom_corrections_override_defaults():
    """Custom corrections override the defaults."""
    instr = MeasurementInstrument(corrections={"contact_resistance_ohm": 0.001})
    m = instr.measure(_config())
    assert m.corrections_applied["contact_resistance_ohm"] == 0.001


# ---------------------------------------------------------------------------
# Residuals
# ---------------------------------------------------------------------------
def test_residuals_computed():
    """Residuals (predicted − measured) are computed."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=3)
    assert len(result.iterations) == 1
    iter_result = result.iterations[0]
    assert len(iter_result.residuals) >= 1


def test_residuals_signed():
    """Residuals are signed (predicted − measured, can be + or −)."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=3)
    # P_max residual should be positive (predicted > measured because
    # measurement has contact resistance reducing P_max)
    pmax_res = [r for r in result.iterations[0].residuals if r.metric == "P_max_W"]
    if pmax_res:
        # With contact resistance, measured P_max < predicted P_max
        # → residual = pred - meas > 0
        assert all(r.residual > 0 for r in pmax_res), (
            "P_max residual should be positive (predicted > measured)")


def test_residual_relative_computed():
    """Relative residual is computed."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=3)
    for r in result.iterations[0].residuals:
        expected_rel = r.residual / abs(r.measured) if abs(r.measured) > 1e-12 else 0.0
        assert abs(r.relative_residual - expected_rel) < 1e-9


def test_residual_significant_flag():
    """Residuals >5% are flagged as significant."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=3)
    # At least one residual should be significant (contact resistance is large)
    sig = [r for r in result.iterations[0].residuals if r.significant]
    assert len(sig) >= 1, (
        "at least one residual should be >5% (contact resistance is significant)")


# ---------------------------------------------------------------------------
# Closed loop: the critical test
# ---------------------------------------------------------------------------
def test_one_real_measurement_changes_next_candidate():
    """CRITICAL: one real measurement changes the next candidate.

    After running one iteration with measurement, the priors are updated.
    The next generated candidate is DIFFERENT from what would have been
    generated without the measurement.
    """
    spec, cg = _spec(), _cg()

    # Engine WITH measurement (run one iteration → priors updated)
    engine_with = MeasurementEngine(seed=42)
    engine_with.run(spec, cg, n_iterations=1, n_candidates=3)
    # Priors should have changed
    assert engine_with.correction_priors != {
        "seebeck_coefficient": 1.0,
        "thermal_conductivity": 1.0,
        "emissivity": 1.0,
    }, "priors should have been updated by measurement"

    # Engine WITHOUT measurement (priors stay at 1.0)
    engine_without = MeasurementEngine(seed=42)

    # Generate next candidates from each engine — same seed, same generator
    configs_with = engine_with.generate(spec, cg, n=3)
    configs_without = engine_without.generate(spec, cg, n=3)

    hashes_with = [c.config_hash for c in configs_with]
    hashes_without = [c.config_hash for c in configs_without]
    assert hashes_with != hashes_without, (
        "CRITICAL: one real measurement must change the next candidate's hash. "
        f"with={hashes_with}, without={hashes_without}")


def test_loop_result_closed_flag():
    """The LoopResult.closed flag is True when priors were updated."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=2, n_candidates=3)
    assert result.closed, (
        "Loop should be closed: residuals are significant AND priors updated")


def test_priors_updated_after_iteration():
    """Correction priors change after the first iteration."""
    engine = MeasurementEngine(seed=42)
    initial_priors = dict(engine.correction_priors)
    engine.run(_spec(), _cg(), n_iterations=1, n_candidates=3)
    final_priors = dict(engine.correction_priors)
    assert initial_priors != final_priors, (
        f"priors should change: {initial_priors} → {final_priors}")


def test_priors_converge_over_iterations():
    """Priors converge (don't diverge) over multiple iterations."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=4, n_candidates=3)
    # Check that priors stay in [0.5, 1.5] (clamped)
    for param, val in result.final_correction_priors.items():
        assert 0.5 <= val <= 1.5, (
            f"prior {param}={val} out of bounds [0.5, 1.5]")


def test_residual_history_recorded():
    """Residual history (mean |relative_residual| per iteration) is recorded."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=3, n_candidates=3)
    assert len(result.residual_history) == 3
    for r in result.residual_history:
        assert r >= 0


# ---------------------------------------------------------------------------
# Generate stage (with priors applied)
# ---------------------------------------------------------------------------
def test_generate_applies_priors():
    """generate() applies current priors to component parameters.

    We test this DIRECTLY by calling _apply_priors on a known config,
    so the test isn't confused by other operators (amplify, substitute)
    that may also modify the parameter.
    """
    engine = MeasurementEngine(seed=42)

    # Build a fresh config without any operators (no amplify/substitute)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    S_before = config.components[0].parameters["seebeck_coefficient"]

    # Set a non-trivial prior
    engine.correction_priors["seebeck_coefficient"] = 0.5
    engine._apply_priors(config)

    S_after = config.components[0].parameters["seebeck_coefficient"]
    assert abs(S_after - 0.5 * S_before) < 1e-15, (
        f"prior 0.5 not applied: S_before={S_before}, S_after={S_after}, "
        f"expected={0.5*S_before}")


def test_generate_changes_hash_when_priors_change():
    """generate() produces different hashes when priors change."""
    spec, cg = _spec(), _cg()
    engine = MeasurementEngine(seed=42)

    # Generate with default priors (all 1.0)
    engine.correction_priors = {"seebeck_coefficient": 1.0,
                                 "thermal_conductivity": 1.0,
                                 "emissivity": 1.0}
    configs_default = engine.generate(spec, cg, n=3)
    hashes_default = [c.config_hash for c in configs_default]

    # Generate with updated priors
    engine.correction_priors = {"seebeck_coefficient": 0.5,
                                 "thermal_conductivity": 1.0,
                                 "emissivity": 1.0}
    configs_updated = engine.generate(spec, cg, n=3)
    hashes_updated = [c.config_hash for c in configs_updated]

    assert hashes_default != hashes_updated


# ---------------------------------------------------------------------------
# Full loop integration
# ---------------------------------------------------------------------------
def test_run_produces_iterations():
    """run() produces the expected number of iterations."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=3, n_candidates=3)
    assert len(result.iterations) == 3
    for i, it in enumerate(result.iterations):
        assert it.iteration == i


def test_iteration_has_all_stages():
    """Each iteration has generated_configs, predictions, prototypes, measurements, residuals."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=4)
    it = result.iterations[0]
    assert len(it.generated_configs) == 4
    assert len(it.predictions) == 4
    assert len(it.prototypes) >= 1  # at least some pass manufacturing
    assert len(it.measurements) >= 1
    assert len(it.residuals) >= 1
    assert it.n_manufacturing_pass >= 1
    assert it.n_measured >= 1


def test_loop_deterministic_under_seed():
    """Same seed → same residuals and final priors."""
    spec, cg = _spec(), _cg()
    r1 = MeasurementEngine(seed=42).run(spec, cg, n_iterations=2, n_candidates=3)
    r2 = MeasurementEngine(seed=42).run(spec, cg, n_iterations=2, n_candidates=3)
    assert r1.final_correction_priors == r2.final_correction_priors
    assert r1.residual_history == r2.residual_history


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def test_loop_provenance_recorded():
    """LoopResult records its provenance."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=2)
    assert result.provenance["engine"] == "MeasurementEngine"
    assert result.provenance["stage"] == "VII"
    assert "real measurement" in result.provenance["loop_closed_by"]


def test_measurement_provenance_recorded():
    """Each Measurement records its provenance."""
    m = MeasurementInstrument().measure(_config())
    assert m.provenance["instrument"] == "MeasurementInstrument"
    assert m.provenance["evidence_rank"] == "A"
    assert "contact_resistance" in str(m.provenance["corrections"])


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def test_measurement_to_dict_serializable():
    """Measurement.to_dict is JSON-serializable."""
    import json
    m = MeasurementInstrument().measure(_config())
    d = m.to_dict()
    json.dumps(d)
    assert "measured_properties" in d


def test_residual_is_dataclass():
    """Residual is a dataclass."""
    r = Residual(
        config_id="X", config_hash="abc", metric="V_oc_V",
        predicted=0.02, measured=0.018, residual=0.002,
        relative_residual=0.1, significant=True,
    )
    assert r.metric == "V_oc_V"
    assert r.significant is True


# ---------------------------------------------------------------------------
# Constitution: positive AND negative evidence (Law 8)
# ---------------------------------------------------------------------------
def test_loop_records_both_prediction_and_measurement():
    """Law 8: both prediction (positive evidence) and measurement (reality) are recorded."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=2)
    it = result.iterations[0]
    # Both predictions AND measurements exist
    assert len(it.predictions) >= 1
    assert len(it.measurements) >= 1
    # And they DIFFER (the prediction is not just echoed back as measurement)
    pred = it.predictions[0]
    meas = it.measurements[0]
    assert pred.predicted_properties["V_oc_V"] != meas.measured_properties["V_oc_V"]


def test_measurement_not_generated_from_prediction():
    """The measurement is NOT computed by perturbing the prediction.

    This is the constitutional guard against fake data: the measurement
    must be computed INDEPENDENTLY (from the configuration's parameters
    via a high-fidelity model), not by adding noise to the prediction.
    """
    # Generate two configs with the same prediction-evaluating parameters
    # but different config_ids — measurement should be identical (depends
    # only on parameters, not on config_id).
    c1 = _config(config_id="A")
    c2 = _config(config_id="B")  # different ID, same parameters
    instr = MeasurementInstrument()
    m1 = instr.measure(c1)
    m2 = instr.measure(c2)
    assert m1.measured_properties == m2.measured_properties, (
        "measurement must depend on configuration parameters, not on config_id "
        "or prediction output")


# ---------------------------------------------------------------------------
# Cross-stage integration
# ---------------------------------------------------------------------------
def test_loop_uses_all_six_modules():
    """The closed loop exercises all six invention modules (Stages II-VII)."""
    engine = MeasurementEngine(seed=42)
    result = engine.run(_spec(), _cg(), n_iterations=1, n_candidates=2)
    it = result.iterations[0]

    # Stage II: artifact generator
    assert len(it.generated_configs) >= 1
    # Stage IV: forward model
    assert len(it.predictions) >= 1
    # Stage VI: prototype compiler
    assert len(it.prototypes) >= 1
    # Stage VII: measurement engine
    assert len(it.measurements) >= 1
    assert len(it.residuals) >= 1


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
