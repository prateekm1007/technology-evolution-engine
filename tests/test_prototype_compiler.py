"""Tests for prototype_compiler.py — Stage VI."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.prototype_compiler import (
    PrototypeCompiler, Prototype,
    MaterialSpec, ParameterSpec, AssemblyStep, FailureMode,
    ConstraintViolation, DEFAULT_CONSTRAINTS, FAILURE_MODES,
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
    ])
    return cg


def _config(material="bismuth_telluride", structure="monolithic",
            params=None, config_id="TEST", extra_components=None):
    c = Configuration(
        config_id=config_id,
        spec_objective="improve thermoelectric efficiency",
        domain="thermoelectric",
        components=[Component(material=material, role="active",
                              parameters=dict(MATERIAL_PARAMS.get(material, {})))]
                  + (extra_components or []),
        structure=structure,
        parameters=params or {"thickness_m": 1e-3, "area_m2": 1e-4,
                              "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    return c


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------
def test_compile_returns_prototype():
    """compile() returns a Prototype."""
    proto = PrototypeCompiler().compile(_config())
    assert isinstance(proto, Prototype)
    assert proto.config_id == "TEST"
    assert proto.config_hash != ""


def test_prototype_has_materials():
    """Prototype has a non-empty materials list."""
    proto = PrototypeCompiler().compile(_config())
    assert len(proto.materials) >= 1
    for m in proto.materials:
        assert isinstance(m, MaterialSpec)
        assert m.material != ""
        assert m.cost_usd >= 0


def test_prototype_has_parameters():
    """Prototype has a non-empty parameters list with tolerances."""
    proto = PrototypeCompiler().compile(_config())
    assert len(proto.parameters) >= 1
    for p in proto.parameters:
        assert isinstance(p, ParameterSpec)
        assert p.name != ""
        assert p.units != ""


def test_prototype_has_assembly_steps():
    """Prototype has ordered assembly steps."""
    proto = PrototypeCompiler().compile(_config())
    assert len(proto.assembly_steps) >= 3
    for s in proto.assembly_steps:
        assert isinstance(s, AssemblyStep)
    # Steps should be numbered 1..N
    step_nums = [s.step for s in proto.assembly_steps]
    assert step_nums == list(range(1, len(step_nums) + 1))


def test_prototype_has_predicted_behavior():
    """Prototype includes the forward model's prediction."""
    proto = PrototypeCompiler().compile(_config())
    assert "predicted_properties" in proto.predicted_behavior
    assert "ZT" in proto.predicted_behavior["predicted_properties"]


def test_prototype_has_failure_modes():
    """Prototype lists failure modes with mitigations."""
    proto = PrototypeCompiler().compile(_config())
    assert len(proto.failure_modes) >= 1
    for fm in proto.failure_modes:
        assert isinstance(fm, FailureMode)
        assert 0.0 <= fm.likelihood <= 1.0
        assert fm.mitigation != ""
        assert fm.evidence_rank in "ABCDEFGHI"


def test_prototype_has_bom():
    """Prototype has a BOM with total cost."""
    proto = PrototypeCompiler().compile(_config())
    assert len(proto.bom) >= 1
    expected_total = sum(m.cost_usd for m in proto.bom)
    assert abs(proto.bom_total_cost_usd - round(expected_total, 2)) < 0.01


# ---------------------------------------------------------------------------
# Manufacturing constraint checks
# ---------------------------------------------------------------------------
def test_default_constraints_pass():
    """A standard thermoelectric config passes manufacturing constraints."""
    proto = PrototypeCompiler().compile(_config())
    assert proto.manufacturing_pass, (
        f"Expected pass, got violations: {[v.constraint for v in proto.constraint_violations]}")


def test_violation_below_min_feature_size():
    """Too-thin config is flagged."""
    c = _config(params={"thickness_m": 1e-9,  # way below 1e-5
                        "area_m2": 1e-4, "T_hot_K": 400.0, "T_cold_K": 300.0})
    proto = PrototypeCompiler().compile(c)
    assert not proto.manufacturing_pass
    assert any(v.constraint == "min_feature_size_m" for v in proto.constraint_violations)


def test_violation_too_many_layers():
    """Too many layers is flagged."""
    c = _config(structure="layered_20",
                params={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0, "n_layers": 20.0})
    proto = PrototypeCompiler().compile(c)
    assert not proto.manufacturing_pass
    assert any(v.constraint == "max_layers" for v in proto.constraint_violations)


def test_violation_too_high_temperature():
    """T_hot above material max_temp is flagged."""
    c = _config(params={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 999.0,  # bismuth_telluride max_temp = 600
                        "T_cold_K": 300.0})
    proto = PrototypeCompiler().compile(c)
    assert not proto.manufacturing_pass
    # Should mention material_max_temp
    assert any("max_temp" in v.constraint for v in proto.constraint_violations)


def test_violation_disallowed_material():
    """Disallowed material is flagged."""
    # 'unobtainium' is not in MATERIAL_PARAMS
    c = _config(material="unobtainium")
    proto = PrototypeCompiler().compile(c)
    assert not proto.manufacturing_pass
    assert any(v.constraint == "allowed_materials" for v in proto.constraint_violations)


def test_violation_cost_ceiling_warning():
    """BOM over cost ceiling is flagged as a warning (not error)."""
    # Build a huge-area config — mass * cost_per_kg will exceed $1000
    c = _config(params={"thickness_m": 1e-2, "area_m2": 1.0,  # 10000 cm^2
                        "T_hot_K": 400.0, "T_cold_K": 300.0})
    proto = PrototypeCompiler().compile(c)
    # bismuth_telluride costs $200/kg, density 7700 kg/m^3
    # mass = 7700 * 1.0 * 1e-2 = 77 kg, cost = 77 * 200 = $15400
    assert proto.bom_total_cost_usd > DEFAULT_CONSTRAINTS["cost_ceiling_usd"]
    cost_violations = [v for v in proto.constraint_violations
                       if v.constraint == "cost_ceiling_usd"]
    assert len(cost_violations) >= 1
    assert cost_violations[0].severity == "warning"


def test_custom_constraints_override_defaults():
    """Custom constraints can be passed in."""
    c = _config(structure="layered_3",
                params={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0, "n_layers": 3.0})
    # Set max_layers = 2 — layered_3 should now violate
    compiler = PrototypeCompiler(constraints={"max_layers": 2})
    proto = compiler.compile(c)
    assert not proto.manufacturing_pass
    assert any(v.constraint == "max_layers" for v in proto.constraint_violations)


def test_constraint_violation_records_expected_and_actual():
    """Each ConstraintViolation records expected and actual values."""
    c = _config(params={"thickness_m": 1e-9, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0})
    proto = PrototypeCompiler().compile(c)
    v = next(v for v in proto.constraint_violations
             if v.constraint == "min_feature_size_m")
    assert isinstance(v, ConstraintViolation)
    assert v.expected != ""
    assert v.actual != ""
    assert v.severity in ("error", "warning")
    assert v.message != ""


# ---------------------------------------------------------------------------
# Assembly steps for different structures
# ---------------------------------------------------------------------------
def test_layered_structure_adds_stack_step():
    """A layered structure triggers an additional stack step."""
    c = _config(structure="layered_3",
                params={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0, "n_layers": 3.0})
    proto = PrototypeCompiler().compile(c)
    ops = [s.operation for s in proto.assembly_steps]
    assert "stack" in ops


def test_segmented_structure_adds_dice_step():
    """A segmented structure triggers an additional dice step."""
    c = _config(structure="segmented_4",
                params={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0, "n_segments": 4.0})
    proto = PrototypeCompiler().compile(c)
    ops = [s.operation for s in proto.assembly_steps]
    assert "dice" in ops


def test_assembly_steps_include_encapsulate():
    """Every prototype ends with an encapsulation step."""
    proto = PrototypeCompiler().compile(_config())
    last_step = proto.assembly_steps[-1]
    assert last_step.operation == "encapsulate"


def test_assembly_steps_include_prepare():
    """Every prototype starts with a prepare step."""
    proto = PrototypeCompiler().compile(_config())
    first_step = proto.assembly_steps[0]
    assert first_step.operation == "prepare"


# ---------------------------------------------------------------------------
# Failure modes per domain
# ---------------------------------------------------------------------------
def test_thermoelectric_has_contact_resistance_failure():
    """Thermoelectric domain includes the contact_resistance failure mode."""
    proto = PrototypeCompiler().compile(_config())
    modes = [fm.mode for fm in proto.failure_modes]
    assert "contact_resistance_at_electrode" in modes


def test_thermal_domain_has_its_own_failure_modes():
    """Thermal domain has its own failure modes."""
    c = Configuration(
        config_id="TH", spec_objective="x", domain="thermal",
        components=[Component(material="aerogel", role="active",
                              parameters={"emissivity": 0.95})],
        structure="monolithic",
        parameters={"area_m2": 1.0, "T_hot_K": 300.0, "T_cold_K": 270.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    proto = PrototypeCompiler().compile(c)
    modes = [fm.mode for fm in proto.failure_modes]
    assert "dust_deposition_on_emissive_surface" in modes


# ---------------------------------------------------------------------------
# BOM cost computation
# ---------------------------------------------------------------------------
def test_bom_cost_is_mass_times_cost_per_kg():
    """BOM cost = mass (kg) × cost_per_kg."""
    c = _config(params={"thickness_m": 1e-3, "area_m2": 1e-4,  # volume = 1e-7 m^3
                        "T_hot_K": 400.0, "T_cold_K": 300.0})
    proto = PrototypeCompiler().compile(c)
    # bismuth_telluride: density=7700, cost=$200/kg
    expected_mass = 7700 * 1e-4 * 1e-3  # 7.7e-4 kg
    expected_cost = expected_mass * 200  # $0.154
    assert abs(proto.bom[0].quantity_kg - round(expected_mass, 6)) < 1e-9
    assert abs(proto.bom[0].cost_usd - round(expected_cost, 2)) < 1e-6


def test_bom_total_sums_all_components():
    """BOM total = sum of all components' costs."""
    c = _config(extra_components=[
        Component(material="copper", role="electrode",
                  parameters=dict(MATERIAL_PARAMS["copper"]))
    ])
    proto = PrototypeCompiler().compile(c)
    expected = sum(m.cost_usd for m in proto.bom)
    assert abs(proto.bom_total_cost_usd - round(expected, 2)) < 0.01


# ---------------------------------------------------------------------------
# Integration with artifact_generator & forward_model
# ---------------------------------------------------------------------------
def test_compile_works_on_generated_configs():
    """PrototypeCompiler works on real generated Configurations."""
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=5)
    compiler = PrototypeCompiler()
    for c in configs:
        proto = compiler.compile(c)
        assert proto.config_hash == c.config_hash
        assert len(proto.materials) >= 1
        assert len(proto.assembly_steps) >= 3


def test_compile_accepts_precomputed_prediction():
    """compile() can accept a pre-computed Prediction."""
    c = _config()
    fm = ForwardModel()
    pred = fm.predict(c)
    proto = PrototypeCompiler(forward_model=fm).compile(c, prediction=pred)
    assert proto.predicted_behavior["config_hash"] == c.config_hash


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def test_to_dict_serializable():
    """Prototype.to_dict produces a JSON-serializable dict."""
    import json
    proto = PrototypeCompiler().compile(_config())
    d = proto.to_dict()
    json.dumps(d)
    assert "materials" in d
    assert "bom" in d
    assert "constraint_violations" in d


def test_provenance_recorded():
    """Prototype records its provenance."""
    proto = PrototypeCompiler().compile(_config())
    assert proto.provenance["compiler"] == "PrototypeCompiler"
    assert proto.provenance["stage"] == "VI"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
