"""Tests for DR-75: failure engine and its detectors."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    Configuration, Component, MATERIAL_PARAMS,
)
from scripts.forward_model import ForwardModel, Prediction
from scripts.measurement_engine import Measurement
from scripts.self_validation_detector import (
    SelfValidationDetector, SelfValidationReport,
)
from scripts.circular_gold_checker import (
    CircularGoldChecker, ContaminationReport,
)
from scripts.forward_model_checker import (
    ForwardModelChecker, ForwardModelCheckReport,
)
from scripts.failure_engine import FailureEngine, FailureEngineResult


def _config(S=200e-6, config_id="C"):
    c = Configuration(
        config_id=config_id, spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters={**MATERIAL_PARAMS["bismuth_telluride"],
                                          "seebeck_coefficient": S})],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    return c


# ---------------------------------------------------------------------------
# DR-75.2: self_validation_detector
# ---------------------------------------------------------------------------
def test_self_validation_passes_for_independent_measurement():
    """An independent measurement (different values, explicit corrections) passes."""
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties={
            "ZT": pred.predicted_properties["ZT"] * 0.85,
            "V_oc_V": pred.predicted_properties["V_oc_V"] * 0.92,
        },
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "high-fidelity with contact resistance",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )
    detector = SelfValidationDetector()
    report = detector.check(pred, meas)
    assert report.severity == "pass"
    assert report.is_self_validating is False


def test_self_validation_flags_identical_measurement():
    """Adversarial: measurement identical to prediction is flagged."""
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties=dict(pred.predicted_properties),
        corrections_applied={},
        provenance={"method": "ZT = S^2 σ T / κ formula",
                    "corrections": []},
    )
    detector = SelfValidationDetector()
    report = detector.check(pred, meas)
    assert report.is_self_validating is True
    assert report.severity == "fail"
    # independence should be ~0
    assert report.measurement_independence < 0.01


def test_self_validation_flags_shared_equation():
    """If the measurement method cites the prediction equation, flag it."""
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties={"ZT": 0.5},  # different value
        corrections_applied={},
        provenance={"method": "uses ZT = S^2 σ T / κ formula",
                    "corrections": []},
    )
    detector = SelfValidationDetector()
    report = detector.check(pred, meas)
    assert report.is_self_validating is True
    assert len(report.shared_equations) > 0


def test_self_validation_report_serializable():
    import json
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties={"ZT": 0.5},
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "independent", "corrections": ["x"]},
    )
    report = SelfValidationDetector().check(pred, meas)
    json.dumps(report.to_dict())


# ---------------------------------------------------------------------------
# DR-75.3: circular_gold_checker
# ---------------------------------------------------------------------------
def test_gold_checker_clean_gold_passes():
    """Clean gold data (no overlap) is not flagged."""
    checker = CircularGoldChecker()
    input_text = ("We aim to improve the thermoelectric figure of merit "
                  "ZT of bismuth telluride by nanostructuring.")
    gold_text = ("The reference dataset contains measurements of "
                 "Seebeck coefficient, electrical conductivity, and "
                 "thermal conductivity for various lead alloys.")
    report = checker.check(input_text, gold_text)
    assert report.is_contaminated is False
    assert report.n_hits == 0


def test_gold_checker_dirty_gold_fails_adversarial():
    """Adversarial: bridge phrases from input injected into gold → flagged."""
    checker = CircularGoldChecker()
    input_text = ("We aim to improve the thermoelectric figure of merit "
                  "ZT of bismuth telluride by nanostructuring.")
    gold_text = ("Validation uses the thermoelectric figure of merit ZT "
                 "of bismuth telluride by nanostructuring as ground truth.")
    report = checker.check(input_text, gold_text)
    assert report.is_contaminated is True
    assert report.n_hits > 0
    # The shared phrase should appear in the bridge list
    assert any("thermoelectric" in p for p in report.bridge_phrases_found)


def test_gold_checker_no_overlap_for_unrelated_text():
    """Completely unrelated text has zero overlap."""
    checker = CircularGoldChecker()
    report = checker.check(
        "The quick brown fox jumps over the lazy dog.",
        "PbTe exhibits high ZT at moderate temperatures.")
    assert report.is_contaminated is False


def test_gold_checker_batch():
    """check_batch returns a dict of reports."""
    checker = CircularGoldChecker()
    results = checker.check_batch(
        "improve thermoelectric figure of merit ZT of bismuth telluride",
        {"clean": "PbTe data", "dirty": "thermoelectric figure of merit ZT of bismuth telluride"})
    assert "clean" in results
    assert "dirty" in results
    assert results["dirty"].is_contaminated is True


def test_gold_checker_report_serializable():
    import json
    checker = CircularGoldChecker()
    report = checker.check("foo bar baz", "quux")
    json.dumps(report.to_dict())


# ---------------------------------------------------------------------------
# DR-75.4: forward_model_checker
# ---------------------------------------------------------------------------
def test_forward_model_checker_passes_for_real_model():
    """The real ForwardModel produces varied predictions → passes."""
    fm = ForwardModel()
    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6, 300e-6, 400e-6])]
    checker = ForwardModelChecker(kb_values={"ZT": 0.93})
    report = checker.check(fm, configs, metric="ZT")
    assert report.is_kb_reuse is False
    assert report.severity == "pass"
    assert report.distinct_predictions >= 2


def test_forward_model_checker_fails_for_constant_model_adversarial():
    """Adversarial: a model that returns a constant KB value is flagged."""
    class FakeKBForwardModel:
        def predict(self, config):
            return Prediction(
                config_id=config.config_id,
                config_hash=config.config_hash,
                domain=config.domain,
                predicted_properties={"ZT": 0.93},  # always the same
            )

    fake_fm = FakeKBForwardModel()
    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6, 300e-6, 400e-6])]
    checker = ForwardModelChecker(kb_values={"ZT": 0.93})
    report = checker.check(fake_fm, configs, metric="ZT")
    assert report.is_kb_reuse is True
    assert report.severity == "fail"
    assert report.is_constant is True


def test_forward_model_checker_no_configs_warns():
    """No configs supplied → warn severity."""
    fm = ForwardModel()
    checker = ForwardModelChecker()
    report = checker.check(fm, [], metric="ZT")
    assert report.severity in ("warn", "fail")


def test_forward_model_checker_kb_match_detected():
    """A model that returns a KB-stored value is flagged as KB reuse."""
    class KBMatchModel:
        def predict(self, config):
            return Prediction(
                config_id=config.config_id,
                config_hash=config.config_hash,
                domain=config.domain,
                predicted_properties={"ZT": 0.93},
            )

    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6])]
    checker = ForwardModelChecker(kb_values={"ZT": 0.93})
    report = checker.check(KBMatchModel(), configs, metric="ZT")
    assert report.kb_match is True


def test_forward_model_check_report_serializable():
    import json
    fm = ForwardModel()
    configs = [_config(S=200e-6, config_id="C0"),
               _config(S=400e-6, config_id="C1")]
    checker = ForwardModelChecker()
    report = checker.check(fm, configs, metric="ZT")
    json.dumps(report.to_dict())


# ---------------------------------------------------------------------------
# DR-75.1: failure_engine (orchestrator)
# ---------------------------------------------------------------------------
def test_failure_engine_passes_for_clean_inputs():
    """All-detectors-pass → status PASS."""
    fm = ForwardModel()
    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6, 300e-6, 400e-6])]
    pred = fm.predict(configs[1])
    meas = Measurement(
        config_id=configs[1].config_id,
        config_hash=configs[1].config_hash,
        domain="thermoelectric",
        measured_properties={
            "ZT": pred.predicted_properties["ZT"] * 0.85,
            "V_oc_V": pred.predicted_properties["V_oc_V"] * 0.92,
        },
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "high-fidelity with contact resistance",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )
    engine = FailureEngine()
    result = engine.run(
        prediction=pred, measurement=meas,
        input_text="improve thermoelectric efficiency of bismuth telluride",
        gold_text="The reference contains Seebeck, conductivity, and "
                  "thermal data for various lead alloys.",
        forward_model=fm, sample_configs=configs, metric="ZT")
    assert result.status == "PASS"
    assert result.n_failed == 0


def test_failure_engine_vetoes_for_contaminated_gold():
    """Contaminated gold → VETO."""
    fm = ForwardModel()
    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6, 300e-6, 400e-6])]
    pred = fm.predict(configs[1])
    meas = Measurement(
        config_id=configs[1].config_id,
        config_hash=configs[1].config_hash,
        domain="thermoelectric",
        measured_properties={
            "ZT": pred.predicted_properties["ZT"] * 0.85,
            "V_oc_V": pred.predicted_properties["V_oc_V"] * 0.92,
        },
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "independent",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )
    engine = FailureEngine()
    result = engine.run(
        prediction=pred, measurement=meas,
        input_text="improve thermoelectric figure of merit ZT of bismuth telluride",
        gold_text="Validation uses the thermoelectric figure of merit ZT "
                  "of bismuth telluride as ground truth.",
        forward_model=fm, sample_configs=configs, metric="ZT")
    assert result.status == "VETO"
    assert result.n_failed >= 1


def test_failure_engine_vetoes_for_self_validation():
    """Self-validating measurement → VETO."""
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    # Identical measurement (self-validating)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties=dict(pred.predicted_properties),
        corrections_applied={},
        provenance={"method": "ZT = S^2 σ T / κ formula",
                    "corrections": []},
    )
    engine = FailureEngine()
    result = engine.run(
        prediction=pred, measurement=meas,
        input_text="improve TE",
        gold_text="independent gold",
        forward_model=fm, sample_configs=[c], metric="ZT")
    assert result.status == "VETO"


def test_failure_engine_vetoes_for_kb_reuse_forward_model():
    """KB-reusing forward model → VETO."""
    class FakeKBForwardModel:
        def predict(self, config):
            return Prediction(
                config_id=config.config_id,
                config_hash=config.config_hash,
                domain=config.domain,
                predicted_properties={"ZT": 0.93},
            )

    fake_fm = FakeKBForwardModel()
    configs = [_config(S=S, config_id=f"C{i}")
               for i, S in enumerate([100e-6, 200e-6, 300e-6])]
    pred = fake_fm.predict(configs[0])
    meas = Measurement(
        config_id=configs[0].config_id,
        config_hash=configs[0].config_hash,
        domain="thermoelectric",
        measured_properties={"ZT": 0.5},
        corrections_applied={"contact_resistance_ohm": 5e-3},
        provenance={"method": "independent",
                    "corrections": ["contact_resistance_ohm: 5 mΩ"]},
    )
    engine = FailureEngine(forward_model_checker=ForwardModelChecker(
        kb_values={"ZT": 0.93}))
    result = engine.run(
        prediction=pred, measurement=meas,
        input_text="improve TE",
        gold_text="independent gold",
        forward_model=fake_fm, sample_configs=configs, metric="ZT")
    assert result.status == "VETO"


def test_failure_engine_skips_missing_inputs():
    """Missing inputs are skipped (not failures)."""
    engine = FailureEngine()
    result = engine.run()  # nothing supplied
    assert result.n_detectors_run == 0
    assert result.status == "PASS"  # no failures
    # But reasons should note skips
    assert any("skipped" in r for r in result.reasons)


def test_failure_engine_veto_helper():
    """veto() returns True iff status is VETO."""
    fm = ForwardModel()
    c = _config()
    pred = fm.predict(c)
    meas = Measurement(
        config_id=c.config_id, config_hash=c.config_hash,
        domain="thermoelectric",
        measured_properties=dict(pred.predicted_properties),
        corrections_applied={},
        provenance={"method": "ZT = S^2 σ T / κ", "corrections": []},
    )
    engine = FailureEngine()
    result = engine.run(prediction=pred, measurement=meas)
    assert engine.veto(result) is True


def test_failure_engine_result_serializable():
    import json
    engine = FailureEngine()
    result = engine.run()
    json.dumps(result.to_dict())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
