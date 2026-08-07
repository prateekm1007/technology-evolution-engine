"""Tests for DR-72: operator library — the canonical 14-operator registry."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    Configuration, Component, MATERIAL_PARAMS,
)
from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph
from scripts.operator_library import (
    OPERATOR_LIBRARY, OperatorLibrary, OperatorMeta,
    apply_operator, list_operators, generate_with_library,
)


def _base_config(config_id: str = "BASE") -> Configuration:
    """Build a minimal thermoelectric configuration for tests."""
    c = Configuration(
        config_id=config_id,
        spec_objective="improve TE",
        domain="thermoelectric",
        components=[Component(
            material="bismuth_telluride", role="active",
            parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]),
        )],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    return c


# ---------------------------------------------------------------------------
# Registry shape
# ---------------------------------------------------------------------------
def test_library_has_exactly_14_operators():
    """The library MUST contain exactly 14 operators."""
    names = OPERATOR_LIBRARY.names
    assert len(names) == 14, f"expected 14 operators, got {len(names)}: {names}"


def test_library_has_required_operator_names():
    """All 14 required operator names are present."""
    required = {"combine", "replace", "invert", "amplify", "attenuate",
                "split", "merge", "layer", "stabilize", "modulate",
                "substitute", "parameterize",
                # new in DR-72:
                "generalize", "instantiate"}
    actual = set(OPERATOR_LIBRARY.names)
    missing = required - actual
    assert not missing, f"missing operators: {missing}"


def test_list_operators_returns_sorted_names():
    """list_operators() returns the sorted operator names."""
    names = list_operators()
    assert names == sorted(names)
    assert "combine" in names
    assert "instantiate" in names


# ---------------------------------------------------------------------------
# Operator behavior: each returns a NEW config (input not mutated)
# ---------------------------------------------------------------------------
def test_combine_adds_component():
    """combine adds a secondary component."""
    base = _base_config()
    n_before = len(base.components)
    new = OPERATOR_LIBRARY.apply(base, "combine",
                                 materials=["graphene"])
    assert len(new.components) == n_before + 1
    # Input is not mutated
    assert len(base.components) == n_before


def test_replace_changes_material():
    """replace swaps a component's material."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "replace",
                                 materials=["lead_telluride"])
    assert new.components[0].material == "lead_telluride"
    assert base.components[0].material == "bismuth_telluride"


def test_invert_introduces_porosity():
    """invert adds porosity and lowers thermal conductivity."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "invert", porosity=0.3)
    assert "porosity" in new.components[0].parameters
    k0 = base.components[0].parameters["thermal_conductivity"]
    k1 = new.components[0].parameters["thermal_conductivity"]
    assert k1 < k0


def test_amplify_scales_up():
    """amplify scales a parameter UP."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "amplify", factor=2.0,
                                 params=["seebeck_coefficient"])
    s0 = base.components[0].parameters["seebeck_coefficient"]
    s1 = new.components[0].parameters["seebeck_coefficient"]
    assert abs(s1 - 2.0 * s0) < 1e-12


def test_attenuate_scales_down():
    """attenuate scales a parameter DOWN."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "attenuate", factor=0.5,
                                 params=["thermal_conductivity"])
    k0 = base.components[0].parameters["thermal_conductivity"]
    k1 = new.components[0].parameters["thermal_conductivity"]
    assert abs(k1 - 0.5 * k0) < 1e-12


def test_split_changes_structure():
    """split changes structure to segmented_N."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "split", n_segments=4)
    assert new.structure == "segmented_4"
    assert new.parameters["n_segments"] == 4.0


def test_merge_reduces_component_count():
    """merge reduces component count by one (after a combine)."""
    base = _base_config()
    combined = OPERATOR_LIBRARY.apply(base, "combine", materials=["graphene"])
    assert len(combined.components) == 2
    merged = OPERATOR_LIBRARY.apply(combined, "merge")
    assert len(merged.components) == 1


def test_layer_changes_structure():
    """layer changes structure to layered_N."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "layer", n_layers=3)
    assert new.structure == "layered_3"


def test_stabilize_adds_stabilizer():
    """stabilize adds a stabilizer component."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "stabilize")
    assert any(c.role == "stabilizer" for c in new.components)


def test_modulate_sets_frequency():
    """modulate sets a modulation_freq parameter."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "modulate", frequency=0.7)
    assert new.parameters["modulation_freq"] == 0.7


def test_substitute_blends_parameters():
    """substitute blends two materials' parameters."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "substitute",
                                 materials=["graphene"], fraction=0.3)
    assert "substitution_fraction" in new.components[0].parameters
    assert new.components[0].parameters["substitution_fraction"] == 0.3


def test_parameterize_sets_value():
    """parameterize sets a global parameter."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "parameterize",
                                 parameter="thickness_m", value=2e-3)
    assert new.parameters["thickness_m"] == 2e-3


def test_generalize_creates_range():
    """generalize abstracts a parameter into a range."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "generalize",
                                 parameter="thickness_m",
                                 low=0.5e-3, high=5e-3)
    assert "thickness_m_range" in new.parameters
    assert new.parameters["thickness_m_range"] == [0.5e-3, 5e-3]
    # The pinned value should be removed
    assert "thickness_m" not in new.parameters


def test_instantiate_pins_value():
    """instantiate pins a parameter to a value (inverse of generalize)."""
    base = _base_config()
    generalized = OPERATOR_LIBRARY.apply(base, "generalize",
                                         parameter="thickness_m",
                                         low=0.5e-3, high=5e-3)
    instantiated = OPERATOR_LIBRARY.apply(generalized, "instantiate",
                                          parameter="thickness_m", value=2e-3)
    assert instantiated.parameters["thickness_m"] == 2e-3
    assert "thickness_m_range" not in instantiated.parameters


# ---------------------------------------------------------------------------
# Hash recomputation
# ---------------------------------------------------------------------------
def test_operator_recomputes_hash():
    """Applying an operator recomputes the config hash."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "amplify", factor=2.0)
    assert new.config_hash != base.config_hash
    # And the hash matches what compute_hash would produce
    assert new.config_hash == new.compute_hash()


def test_operator_chain_records_application():
    """Each operator appends its name to design_operator_chain."""
    base = _base_config()
    new = OPERATOR_LIBRARY.apply(base, "combine", materials=["graphene"])
    assert new.design_operator_chain[-1] == "combine"
    assert "init" in base.design_operator_chain  # original preserved


# ---------------------------------------------------------------------------
# apply_chain
# ---------------------------------------------------------------------------
def test_apply_chain_runs_in_order():
    """apply_chain runs operators in the supplied order."""
    base = _base_config()
    chain = [("combine", {"materials": ["graphene"]}),
             ("amplify", {"factor": 2.0, "params": ["seebeck_coefficient"]}),
             ("layer", {"n_layers": 3})]
    new = OPERATOR_LIBRARY.apply_chain(base, chain)
    assert new.design_operator_chain[-3:] == ["combine", "amplify", "layer"]
    assert new.structure == "layered_3"


# ---------------------------------------------------------------------------
# all_operators_on
# ---------------------------------------------------------------------------
def test_all_operators_on_returns_one_per_operator():
    """all_operators_on applies every operator and returns one config each."""
    base = _base_config()
    results = OPERATOR_LIBRARY.all_operators_on(base)
    assert set(results.keys()) == set(OPERATOR_LIBRARY.names)
    assert len(results) == 14


# ---------------------------------------------------------------------------
# Adversarial test: delete the library → generation MUST fail
# ---------------------------------------------------------------------------
def test_generation_fails_without_library(monkeypatch):
    """If the OPERATOR_LIBRARY is emptied, generate_with_library MUST raise.

    This is the adversarial test required by DR-72.
    """
    # Save the original operators
    original_ops = dict(OPERATOR_LIBRARY.operators)
    try:
        # Empty the library
        OPERATOR_LIBRARY.operators = {}
        with pytest.raises(RuntimeError, match="empty|missing"):
            spec = SpecificationEngine().compile(
                "improve thermoelectric efficiency of bismuth telluride")
            cg = CapabilityGraph()
            cg.from_relations([("bismuth telluride", "generates", "voltage")])
            generate_with_library(spec, cg, n=3, seed=42)
    finally:
        # Restore
        OPERATOR_LIBRARY.operators = original_ops


def test_unknown_operator_raises():
    """Applying an unknown operator raises KeyError."""
    base = _base_config()
    with pytest.raises(KeyError):
        OPERATOR_LIBRARY.apply(base, "nonexistent_op")


# ---------------------------------------------------------------------------
# Integration with the broader pipeline
# ---------------------------------------------------------------------------
def test_generate_with_library_produces_configs():
    """generate_with_library produces non-trivial configurations."""
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])
    configs = generate_with_library(spec, cg, n=5, seed=42)
    assert len(configs) == 5
    # Each config should have at least 1 operator applied beyond "init"
    for c in configs:
        assert len(c.design_operator_chain) >= 2
        assert c.config_hash != ""


def test_generate_with_library_is_deterministic():
    """Same seed → same hashes."""
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth telluride", "generates", "voltage")])
    a = generate_with_library(spec, cg, n=3, seed=42)
    b = generate_with_library(spec, cg, n=3, seed=42)
    assert [c.config_hash for c in a] == [c.config_hash for c in b]


def test_generalize_instantiate_are_inverse():
    """generalize then instantiate restores the parameter (round-trip)."""
    base = _base_config()
    generalized = OPERATOR_LIBRARY.apply(base, "generalize",
                                         parameter="thickness_m",
                                         low=1e-3, high=2e-3)
    instantiated = OPERATOR_LIBRARY.apply(generalized, "instantiate",
                                          parameter="thickness_m", value=1e-3)
    # The thickness is back to a pinned value
    assert instantiated.parameters["thickness_m"] == 1e-3
    # The range is gone
    assert "thickness_m_range" not in instantiated.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
