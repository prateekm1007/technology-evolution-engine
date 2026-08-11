"""Tests for contradiction_solver.py — Stage III."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.contradiction_solver import (
    ContradictionSolver, Contradiction, Resolution, ResolutionStep,
    TRIZ_TO_OPERATORS, PARAM_TO_OPERATOR_HINT,
)
from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
    DESIGN_OPERATORS,
)
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


def _base_config():
    """Build a known base configuration."""
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=1)
    return configs[0]


# ---------------------------------------------------------------------------
# TRIZ → operator mapping table
# ---------------------------------------------------------------------------
def test_all_40_triz_principles_mapped():
    """Every TRIZ principle (1-40) is mapped to at least one design operator."""
    for pnum in range(1, 41):
        assert pnum in TRIZ_TO_OPERATORS, f"Principle {pnum} not mapped"
        assert len(TRIZ_TO_OPERATORS[pnum]) >= 1
        assert all(op in DESIGN_OPERATORS for op in TRIZ_TO_OPERATORS[pnum]), (
            f"Principle {pnum} maps to unknown operator: {TRIZ_TO_OPERATORS[pnum]}")


def test_only_canonical_design_operators_used():
    """Every mapped operator is one of the 12 canonical design operators."""
    allowed = set(DESIGN_OPERATORS)
    for pnum, ops in TRIZ_TO_OPERATORS.items():
        for op in ops:
            assert op in allowed, (
                f"Principle {pnum} maps to non-canonical operator '{op}'")


def test_segmentation_maps_to_split():
    """Principle 1 (Segmentation) maps to 'split'."""
    assert TRIZ_TO_OPERATORS[1] == ["split"]


def test_composite_materials_maps_to_combine():
    """Principle 40 (Composite materials) maps to 'combine'."""
    assert TRIZ_TO_OPERATORS[40] == ["combine"]


def test_porous_materials_maps_to_invert():
    """Principle 31 (Porous materials) maps to 'invert' (porosity slashes κ)."""
    assert TRIZ_TO_OPERATORS[31] == ["invert"]


def test_other_way_round_maps_to_invert():
    """Principle 13 (Other way round) maps to 'invert'."""
    assert TRIZ_TO_OPERATORS[13] == ["invert"]


def test_get_operators_for_principle():
    """get_operators_for_principle returns the mapped operators."""
    ops = ContradictionSolver.get_operators_for_principle(40)
    assert ops == ["combine"]
    ops = ContradictionSolver.get_operators_for_principle(1)
    assert ops == ["split"]


def test_get_principles_for_operator():
    """get_principles_for_operator returns all principles mapping to an operator."""
    principles = ContradictionSolver.get_principles_for_operator("layer")
    # Principles that map to layer include: 3, 7, 17, 30
    assert 3 in principles
    assert 17 in principles


def test_all_principles_mapped_static():
    """all_principles_mapped() returns True."""
    assert ContradictionSolver.all_principles_mapped()


# ---------------------------------------------------------------------------
# Solver core: produces new Configuration(s)
# ---------------------------------------------------------------------------
def test_solve_returns_resolution():
    """solve() returns a Resolution object."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    assert isinstance(r, Resolution)
    assert r.base_config_id == base.config_id
    assert r.base_config_hash == base.config_hash


def test_solve_produces_at_least_one_new_config():
    """solve() produces at least one new Configuration."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    assert len(r.new_configurations) >= 1


def test_new_configs_are_distinct_from_base():
    """Each new Configuration has a different config_hash from the base."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    for new_c in r.new_configurations:
        assert new_c.config_hash != base.config_hash, (
            "new config should differ from base")


def test_base_config_not_mutated():
    """The base Configuration is not mutated by the solver."""
    base = _base_config()
    base_hash_before = base.config_hash
    base_chain_before = list(base.design_operator_chain)
    base_components_before = len(base.components)
    base_params_before = dict(base.parameters)

    solver = ContradictionSolver(seed=42, top_k=3)
    solver.solve(base, improve="conductivity", worsen="stability")

    assert base.config_hash == base_hash_before
    assert base.design_operator_chain == base_chain_before
    assert len(base.components) == base_components_before
    assert base.parameters == base_params_before


def test_steps_record_triz_principle_and_operators():
    """Each ResolutionStep records the TRIZ principle and the mapped operators."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    assert len(r.steps) >= 1
    for step in r.steps:
        assert isinstance(step, ResolutionStep)
        assert 1 <= step.principle_number <= 40
        assert step.principle_name != ""
        assert 0.0 <= step.compatibility_score <= 1.0
        assert len(step.design_operators) >= 1
        # The applied operators must be a superset of the mapped operators
        for op in step.design_operators:
            assert op in step.applied_operators


def test_new_chain_records_triz_principle():
    """The new Configuration's operator chain records the TRIZ principle."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    for step, new_c in zip(r.steps, r.new_configurations):
        # The last chain element should be "triz:N(name)"
        assert any(elem.startswith("triz:") for elem in new_c.design_operator_chain)
        assert f"triz:{step.principle_number}" in new_c.design_operator_chain[-1]


# ---------------------------------------------------------------------------
# Domain-driven principle selection
# ---------------------------------------------------------------------------
def test_mechanical_contradiction_favors_mechanical_principles():
    """A mechanical contradiction favors mechanical-domain principles."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=5)
    r = solver.solve(base, improve="strength", worsen="weight")
    # At least one of the top-5 should be a mechanical-domain principle
    # (those that map to split, layer, merge, etc.)
    from scripts.contradiction_resolver_v2 import PRINCIPLE_DOMAINS, PhysicalDomain
    has_mechanical = False
    for step in r.steps:
        if PhysicalDomain.MECHANICAL in PRINCIPLE_DOMAINS.get(step.principle_number, set()):
            has_mechanical = True
            break
    assert has_mechanical


def test_thermal_contradiction_favors_thermal_principles():
    """A thermal contradiction favors thermal-domain principles."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=10)
    r = solver.solve(base, improve="temperature", worsen="energy")
    from scripts.contradiction_resolver_v2 import PRINCIPLE_DOMAINS, PhysicalDomain
    has_thermal = False
    for step in r.steps:
        if PhysicalDomain.THERMAL in PRINCIPLE_DOMAINS.get(step.principle_number, set()):
            has_thermal = True
            break
    assert has_thermal


# ---------------------------------------------------------------------------
# Operator effects on parameters
# ---------------------------------------------------------------------------
def test_invert_operator_reduces_thermal_conductivity():
    """When invert is applied (e.g., via principle 31), κ decreases."""
    base = _base_config()
    base_kappa = base.components[0].parameters.get("thermal_conductivity")
    assert base_kappa is not None

    solver = ContradictionSolver(seed=42, top_k=10)
    # thermal_conductivity → PARAM_TO_OPERATOR_HINT maps it to 'invert'
    r = solver.solve(base, improve="thermal_conductivity", worsen="cost")

    # At least one new config should have lower κ
    found_reduced = False
    for new_c in r.new_configurations:
        new_kappa = new_c.components[0].parameters.get("thermal_conductivity")
        if new_kappa is not None and new_kappa < base_kappa:
            found_reduced = True
            break
    assert found_reduced, (
        "At least one new config should have reduced thermal_conductivity "
        "(via invert/porosity operator)")


def test_amplify_operator_increases_seebeck():
    """When amplify is applied (via principle 9), S increases."""
    # Build a config WITHOUT amplify already in the chain (so the
    # contradiction solver's amplify is the only one applied).
    base = Configuration(
        config_id="BASE", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    base.config_hash = base.compute_hash()
    base_S = base.components[0].parameters["seebeck_coefficient"]

    solver = ContradictionSolver(seed=42, top_k=10)
    # seebeck_coefficient → PARAM_TO_OPERATOR_HINT maps it to 'amplify'
    r = solver.solve(base, improve="seebeck_coefficient", worsen="cost")

    found_increased = False
    for new_c in r.new_configurations:
        new_S = new_c.components[0].parameters.get("seebeck_coefficient")
        if new_S is not None and new_S > base_S:
            found_increased = True
            break
    assert found_increased, (
        "At least one new config should have increased seebeck_coefficient")


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_solve_deterministic_under_seed():
    """Same seed → identical new config hashes."""
    base = _base_config()
    solver_a = ContradictionSolver(seed=42, top_k=3)
    solver_b = ContradictionSolver(seed=42, top_k=3)
    r_a = solver_a.solve(base, improve="conductivity", worsen="stability")
    r_b = solver_b.solve(base, improve="conductivity", worsen="stability")
    hashes_a = [c.config_hash for c in r_a.new_configurations]
    hashes_b = [c.config_hash for c in r_b.new_configurations]
    assert hashes_a == hashes_b


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def test_provenance_records_triz_principle():
    """The new config's provenance records the TRIZ principle that drove it."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    for step, new_c in zip(r.steps, r.new_configurations):
        assert new_c.provenance.get("triz_principle") == step.principle_number
        assert new_c.provenance.get("triz_principle_name") == step.principle_name
        assert new_c.provenance.get("transformed_by") == "ContradictionSolver"
        assert new_c.provenance.get("contradiction_improve") == "conductivity"
        assert new_c.provenance.get("contradiction_worsen") == "stability"


def test_resolution_provenance_records_method():
    """The Resolution's provenance records the method."""
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    assert r.provenance["solver"] == "ContradictionSolver"
    assert r.provenance["stage"] == "III"
    assert "TRIZ_TO_OPERATORS" in r.provenance["triz_mapping_table"]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def test_resolution_to_dict_serializable():
    """Resolution.to_dict produces a JSON-serializable dict."""
    import json
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    d = r.to_dict()
    json.dumps(d)
    assert "new_configurations" in d
    assert "steps" in d


# ---------------------------------------------------------------------------
# Integration with forward model (does the new config still predict?)
# ---------------------------------------------------------------------------
def test_new_config_predictable_by_forward_model():
    """The new Configuration can be predicted by the ForwardModel."""
    from scripts.forward_model import ForwardModel
    base = _base_config()
    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    fm = ForwardModel()
    for new_c in r.new_configurations:
        p = fm.predict(new_c)
        assert p.config_hash == new_c.config_hash
        assert "ZT" in p.predicted_properties


def test_new_config_has_different_prediction_than_base():
    """At least one new config has a different ZT than the base."""
    from scripts.forward_model import ForwardModel
    base = _base_config()
    fm = ForwardModel()
    base_pred = fm.predict(base)
    base_ZT = base_pred.predicted_properties["ZT"]

    solver = ContradictionSolver(seed=42, top_k=3)
    r = solver.solve(base, improve="conductivity", worsen="stability")
    new_ZTs = [fm.predict(c).predicted_properties["ZT"] for c in r.new_configurations]
    assert any(abs(z - base_ZT) > 1e-9 for z in new_ZTs), (
        "at least one new config should have a different ZT than base")


# ---------------------------------------------------------------------------
# Contradiction dataclass
# ---------------------------------------------------------------------------
def test_contradiction_dataclass():
    """Contradiction is a dataclass with improve, worsen, context, base_config."""
    base = _base_config()
    c = Contradiction(improve="conductivity", worsen="stability",
                      context="thermoelectric leg", base_config=base)
    assert c.improve == "conductivity"
    assert c.worsen == "stability"
    assert c.context == "thermoelectric leg"
    assert c.base_config is base


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
