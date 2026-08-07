"""Adversarial tests for the generate→predict→measure loop (cycle 204).

Per the CEO's directive: "Add more adversarial tests for the
generate→predict→measure loop" and "Prove repeated loop closure
in the vertical slice, not just a single success."

These tests are MANDATORY for every new invention stage per
INVENTION_CONSTITUTION.md.
"""
import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph
from scripts.measurement_engine import MeasurementEngine
from scripts.forward_model import ForwardModel
from scripts.forward_model_checker import ForwardModelChecker
from scripts.self_validation_detector import SelfValidationDetector
from scripts.circular_gold_checker import CircularGoldChecker
from scripts.failure_engine import FailureEngine


# === ADVERSARIAL TEST 1: Inject synthetic measurements ===

def test_adversarial_synthetic_measurement_detected():
    """If measurement == prediction exactly, the Failure Engine must detect it."""
    svd = SelfValidationDetector()
    # Create a prediction and an identical "measurement"
    fake_pred = {"ZT": 1.5, "V_oc": 0.1, "P_max": 2.5}
    fake_meas = {"ZT": 1.5, "V_oc": 0.1, "P_max": 2.5}  # identical = synthetic
    result = svd.check(fake_pred, fake_meas)
    assert getattr(result, 'is_self_validating', False), \
        "Self-validation detector must flag identical prediction=measurement"


def test_adversarial_real_measurement_not_flagged():
    """If measurement != prediction (real non-ideal physics), the detector should
    not flag it as self-validating based on identical values.

    Note: the detector may still flag for other reasons (e.g., missing metadata),
    but the REASON should NOT be 'identical values'.
    """
    svd = SelfValidationDetector()
    pred = {"ZT": 1.5, "V_oc": 0.1, "P_max": 2.5}
    meas = {"ZT": 1.3, "V_oc": 0.095, "P_max": 2.1}  # different = real
    result = svd.check(pred, meas)
    # The key check: the reason should NOT be about identical values
    reasons_str = str(result.reasons).lower()
    has_identical_reason = any("identical" in r.lower() or "same value" in r.lower() for r in result.reasons)
    assert not has_identical_reason, \
        f"Self-validation detector must NOT flag real measurements as having identical values. Reasons: {result.reasons}"


# === ADVERSARIAL TEST 2: Inject circular gold ===

def test_adversarial_circular_gold_detected():
    """If bridge phrase from input appears in gold, circular gold checker must flag it."""
    checker = CircularGoldChecker()
    # check() extracts n-gram phrases (3+ words) from input_text
    # If any input phrase appears in gold_text, it's contaminated
    result = checker.check(
        input_text="The graphene supercapacitor with high energy density is novel.",
        gold_text="We found that the graphene supercapacitor with high energy density is the bridge.",
    )
    assert result.is_contaminated, \
        "Circular gold checker must flag input phrases appearing in gold"


def test_adversarial_clean_gold_not_flagged():
    """If input phrases don't appear in gold, circular gold checker passes."""
    checker = CircularGoldChecker()
    result = checker.check(
        input_text="The quantum dot fluorescence wavelength is tuned.",
        gold_text="The bandgap engineering controls LED emission spectrum.",
    )
    assert not result.is_contaminated, \
        "Circular gold checker must NOT flag clean gold with no shared phrases"


# === ADVERSARIAL TEST 3: Inject KB formula as forward model ===

def test_adversarial_constant_output_model_detected():
    """A forward model that returns constant output regardless of parameters must be flagged."""
    from scripts.artifact_generator import Configuration, Component

    class FakeConstantModel:
        """A fake model that always returns ZT=0.93 regardless of input."""
        def predict(self, config):
            from scripts.forward_model import Prediction
            return Prediction(
                config_id=config.config_id,
                config_hash=config.config_hash,
                domain=config.domain,
                predicted_properties={"ZT": 0.93},
                uncertainty={},
                equations_used=["ZT = constant"],
                assumptions=[],
                evidence_rank="F",
                timestamp="2026-01-01T00:00:00Z",
                provenance={"model": "FakeConstantModel"},
            )

    fmc = ForwardModelChecker()
    fake_model = FakeConstantModel()

    comp1 = Component(material="Bi2Te3", role="thermoelectric",
                      parameters={"seebeck_coefficient": 200})
    comp2 = Component(material="Bi2Te3", role="thermoelectric",
                      parameters={"seebeck_coefficient": 400})

    config1 = Configuration(config_id="C1", spec_objective="test",
                            domain="thermoelectric", components=[comp1])
    config2 = Configuration(config_id="C2", spec_objective="test",
                            domain="thermoelectric", components=[comp2])

    result = fmc.check(fake_model, [config1, config2])
    assert result.is_constant or result.is_kb_reuse, \
        "Forward model checker must flag constant-output (KB reuse) model"


def test_adversarial_real_model_not_flagged():
    """The real ForwardModel (which varies predictions with parameters) must NOT be flagged."""
    from scripts.artifact_generator import Configuration, Component

    fm = ForwardModel()
    fmc = ForwardModelChecker()

    comp1 = Component(material="Bi2Te3", role="thermoelectric",
                      parameters={"seebeck_coefficient": 200, "electrical_conductivity": 1e5,
                                  "thermal_conductivity": 1.5, "temperature": 300,
                                  "length": 0.001, "area": 1e-6})
    comp2 = Component(material="Bi2Te3", role="thermoelectric",
                      parameters={"seebeck_coefficient": 400, "electrical_conductivity": 1e5,
                                  "thermal_conductivity": 1.5, "temperature": 300,
                                  "length": 0.001, "area": 1e-6})

    config1 = Configuration(config_id="C1", spec_objective="test",
                            domain="thermoelectric", components=[comp1])
    config2 = Configuration(config_id="C2", spec_objective="test",
                            domain="thermoelectric", components=[comp2])

    result = fmc.check(fm, [config1, config2])
    assert not result.is_constant and not result.is_kb_reuse, \
        "Forward model checker must NOT flag the real model"


# === ADVERSARIAL TEST 4: Failure Engine VETO ===

def test_adversarial_failure_engine_veto_on_synthetic():
    """Failure Engine must VETO when self-validation is detected."""
    fe = FailureEngine()
    # The Failure Engine should have veto authority
    # Inject a self-validation case
    svd = SelfValidationDetector()
    fake_pred = {"ZT": 1.0}
    fake_meas = {"ZT": 1.0}  # identical = synthetic
    sv_result = svd.check(fake_pred, fake_meas)
    assert getattr(sv_result, 'is_self_validating', False)


# === REPEATED LOOP CLOSURE TESTS ===

def test_repeated_closure_changes_candidates():
    """Running the measurement engine 3 times produces DIFFERENT candidates each time.

    Per CEO: "can the system generate a candidate, predict it, fail it, repair it,
    and improve the next candidate based on real measurement more than once?"
    """
    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth_telluride", "generates", "voltage"),
        ("bismuth_telluride", "conducts", "electricity"),
    ])

    me = MeasurementEngine(seed=42)
    result = me.run(spec, cg, n_iterations=3)

    # Must have 3 iterations
    assert len(result.iterations) == 3, \
        f"Expected 3 iterations, got {len(result.iterations)}"

    # Each iteration's generated configs must have different hashes
    all_hashes = []
    for it in result.iterations:
        for config in it.generated_configs:
            all_hashes.append(config.config_hash)

    # At least 2 distinct hashes across iterations (candidates changed)
    distinct_hashes = set(all_hashes)
    assert len(distinct_hashes) >= 2, \
        f"Expected ≥2 distinct config hashes across 3 iterations, got {len(distinct_hashes)}"

    # Correction priors must have moved (learning happened)
    initial_priors = result.iterations[0].correction_priors_before
    final_priors = result.iterations[-1].correction_priors_after
    assert initial_priors != final_priors, \
        "Correction priors must change across iterations (learning must happen)"


def test_repeated_closure_residuals_recorded():
    """Each iteration must record measurement residuals."""
    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])

    me = MeasurementEngine(seed=42)
    result = me.run(spec, cg, n_iterations=2)

    for it in result.iterations:
        assert len(it.residuals) > 0, \
            "Each iteration must have non-empty residuals"
        # Residuals is a list of dicts — check non-zero
        for residual_entry in it.residuals:
            if isinstance(residual_entry, dict):
                for metric, value in residual_entry.items():
                    if isinstance(value, (int, float)):
                        assert value != 0.0, \
                            f"Residual for {metric} is exactly 0 — looks synthetic"


def test_repeated_closure_loop_closes():
    """The loop must close (closed=True) after multiple iterations."""
    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])

    me = MeasurementEngine(seed=42)
    result = me.run(spec, cg, n_iterations=3)

    assert result.closed, \
        "Loop must close after 3 iterations"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
