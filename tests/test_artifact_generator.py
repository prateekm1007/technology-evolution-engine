"""Tests for artifact_generator.py — Stage II."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    ArtifactGenerator,
    Configuration,
    Component,
    MATERIAL_PARAMS,
    DESIGN_OPERATORS,
)
from scripts.specification import SpecificationEngine, Specification
from scripts.capability_graph import CapabilityGraph


def _spec():
    return SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")


def _cg():
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("bismuth telluride", "conducts", "heat"),
        ("lead telluride", "generates", "voltage"),
        ("graphene", "conducts", "electricity"),
        ("copper", "conducts", "electricity"),
    ])
    return cg


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------
def test_generator_produces_configurations():
    """generate() returns a list of Configuration objects."""
    gen = ArtifactGenerator(seed=42)
    configs = gen.generate(_spec(), _cg(), n=5)
    assert len(configs) == 5
    for c in configs:
        assert isinstance(c, Configuration)
        assert len(c.components) >= 1
        assert c.config_id.startswith("CONFIG-")
        assert c.domain == "thermoelectric"


def test_generator_deterministic_under_seed():
    """Same seed → identical config hashes (byte-exact)."""
    spec, cg = _spec(), _cg()
    run1 = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    run2 = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    h1 = [c.config_hash for c in run1]
    h2 = [c.config_hash for c in run2]
    assert h1 == h2, f"hashes differ under same seed:\n  {h1}\n  {h2}"


def test_generator_different_seed_different_hashes():
    """Different seeds → at least one different config hash."""
    spec, cg = _spec(), _cg()
    run_a = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    run_b = ArtifactGenerator(seed=43).generate(spec, cg, n=5)
    h_a = {c.config_hash for c in run_a}
    h_b = {c.config_hash for c in run_b}
    assert h_a != h_b, "different seeds should produce different configurations"


def test_each_config_has_operator_chain():
    """Every Configuration has a design_operator_chain starting with 'init'."""
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=5)
    for c in configs:
        assert c.design_operator_chain[0] == "init"
        assert len(c.design_operator_chain) >= 2  # init + at least one operator


def test_only_known_operators_in_chain():
    """Every operator in the chain is one of the 12 design operators or 'init'."""
    allowed = set(DESIGN_OPERATORS) | {"init"}
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=10)
    for c in configs:
        for op in c.design_operator_chain:
            assert op in allowed, f"unknown operator '{op}' in chain {c.design_operator_chain}"


def test_config_hash_is_16_hex_chars():
    """config_hash is a 16-char hex string."""
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=3)
    for c in configs:
        assert len(c.config_hash) == 16
        int(c.config_hash, 16)  # parses as hex


# ---------------------------------------------------------------------------
# Canonicality / hash invariants
# ---------------------------------------------------------------------------
def test_hash_excludes_spec_objective_prose():
    """Rewording the spec_objective does NOT change the config_hash."""
    spec_a = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    spec_b = SpecificationEngine().compile(
        "boost ZT of bismuth telluride")  # different wording
    cg = _cg()
    gen = ArtifactGenerator(seed=42)
    # Build the same configuration manually using the same operator chain
    # on the same base material — only the spec_objective differs.
    c1 = Configuration(
        config_id="X1",
        spec_objective=spec_a.objective,
        domain="thermoelectric",
        components=[Component(
            material="bismuth_telluride",
            role="active",
            parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c2 = Configuration(
        config_id="X2",
        spec_objective=spec_b.objective,
        domain="thermoelectric",
        components=[Component(
            material="bismuth_telluride",
            role="active",
            parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    assert c1.compute_hash() == c2.compute_hash(), (
        "rewriting spec_objective should not change config_hash")


def test_hash_excludes_provenance_and_chain():
    """The config_hash depends only on structure+components+params."""
    base_params = dict(MATERIAL_PARAMS["bismuth_telluride"])
    base_component = Component(material="bismuth_telluride", role="active",
                               parameters=base_params)
    base_params2 = dict(MATERIAL_PARAMS["bismuth_telluride"])

    c1 = Configuration(
        config_id="A",
        spec_objective="x",
        domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=base_params)],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        design_operator_chain=["init", "layer", "amplify"],
        provenance={"generator": "X", "seed": 1},
    )
    c2 = Configuration(
        config_id="B",
        spec_objective="completely different",
        domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=base_params2)],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        design_operator_chain=["init", "substitute", "modulate", "parameterize"],
        provenance={"generator": "Y", "seed": 999},
    )
    assert c1.compute_hash() == c2.compute_hash()


def test_hash_changes_with_component_material():
    """Different material → different hash."""
    c1 = Configuration(
        config_id="A",
        spec_objective="x",
        domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
    )
    c2 = Configuration(
        config_id="B",
        spec_objective="x",
        domain="thermoelectric",
        components=[Component(material="lead_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["lead_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
    )
    assert c1.compute_hash() != c2.compute_hash()


def test_hash_changes_with_parameter_value():
    """Different parameter value → different hash."""
    p1 = dict(MATERIAL_PARAMS["bismuth_telluride"])
    p2 = dict(MATERIAL_PARAMS["bismuth_telluride"])
    p2["seebeck_coefficient"] = p2["seebeck_coefficient"] * 2.0
    c1 = Configuration(
        config_id="A", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active", parameters=p1)],
        structure="monolithic", parameters={"thickness_m": 1e-3},
    )
    c2 = Configuration(
        config_id="B", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active", parameters=p2)],
        structure="monolithic", parameters={"thickness_m": 1e-3},
    )
    assert c1.compute_hash() != c2.compute_hash()


# ---------------------------------------------------------------------------
# Design operator semantics
# ---------------------------------------------------------------------------
def test_combine_adds_component():
    """combine operator adds a second component."""
    gen = ArtifactGenerator(seed=42)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    n_before = len(config.components)
    config = gen.apply_operator(config, "combine",
                                materials=["copper", "graphene"])
    assert len(config.components) == n_before + 1
    assert "combine" in config.design_operator_chain


def test_layer_sets_layered_structure():
    """layer operator sets structure to layered_N."""
    gen = ArtifactGenerator(seed=7)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    config = gen.apply_operator(config, "layer")
    assert config.structure.startswith("layered_")
    assert config.parameters["n_layers"] >= 2


def test_invert_reduces_thermal_conductivity():
    """invert operator introduces porosity and reduces thermal_conductivity."""
    gen = ArtifactGenerator(seed=3)
    k_before = MATERIAL_PARAMS["bismuth_telluride"]["thermal_conductivity"]
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    config = gen.apply_operator(config, "invert")
    k_after = config.components[0].parameters["thermal_conductivity"]
    assert k_after < k_before, (
        f"invert should reduce thermal_conductivity: {k_before} -> {k_after}")
    assert config.components[0].parameters.get("porosity", 0) > 0


def test_amplify_increases_seebeck():
    """amplify operator increases seebeck_coefficient."""
    gen = ArtifactGenerator(seed=3)
    s_before = MATERIAL_PARAMS["bismuth_telluride"]["seebeck_coefficient"]
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    config = gen.apply_operator(config, "amplify")
    s_after = config.components[0].parameters["seebeck_coefficient"]
    assert s_after > s_before


def test_attenuate_decreases_thermal_conductivity():
    """attenuate operator decreases thermal_conductivity."""
    gen = ArtifactGenerator(seed=3)
    k_before = MATERIAL_PARAMS["bismuth_telluride"]["thermal_conductivity"]
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    config = gen.apply_operator(config, "attenuate")
    k_after = config.components[0].parameters["thermal_conductivity"]
    assert k_after < k_before


def test_split_sets_segmented_structure():
    """split operator sets structure to segmented_N."""
    gen = ArtifactGenerator(seed=3)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    config = gen.apply_operator(config, "split")
    assert config.structure.startswith("segmented_")
    assert config.parameters["n_segments"] >= 2


def test_substitute_blends_parameters():
    """substitute blends two materials' parameters by fraction x (Vegard's law)."""
    gen = ArtifactGenerator(seed=3)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    s_before = config.components[0].parameters["seebeck_coefficient"]
    config = gen.apply_operator(config, "substitute",
                                materials=["lead_telluride"])
    s_after = config.components[0].parameters["seebeck_coefficient"]
    assert s_after != s_before, "substitute should change parameters"
    assert config.components[0].parameters["substitution_fraction"] > 0


def test_parameterize_sets_thickness():
    """parameterize sets the thickness global parameter."""
    gen = ArtifactGenerator(seed=3)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    t_before = config.parameters["thickness_m"]
    config = gen.apply_operator(config, "parameterize")
    t_after = config.parameters["thickness_m"]
    assert t_after != t_before


def test_stabilize_adds_stabilizer_component():
    """stabilize adds a stabilizer-role component."""
    gen = ArtifactGenerator(seed=3)
    config = Configuration(
        config_id="X", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic", parameters={"thickness_m": 1e-3},
        design_operator_chain=["init"],
    )
    n_before = len(config.components)
    config = gen.apply_operator(config, "stabilize")
    assert len(config.components) == n_before + 1
    assert any(c.role == "stabilizer" for c in config.components)


def test_all_twelve_operators_callable():
    """Every one of the 12 design operators is callable without raising."""
    gen = ArtifactGenerator(seed=3)
    expected = {"combine", "replace", "invert", "amplify", "attenuate",
                "split", "merge", "layer", "stabilize", "modulate",
                "substitute", "parameterize"}
    assert set(DESIGN_OPERATORS) == expected
    for op in DESIGN_OPERATORS:
        config = Configuration(
            config_id="X", spec_objective="x", domain="thermoelectric",
            components=[Component(material="bismuth_telluride", role="active",
                                  parameters=dict(MATERIAL_PARAMS["bismuth_telluride"])),
                        Component(material="copper", role="secondary",
                                  parameters=dict(MATERIAL_PARAMS["copper"]))],
            structure="monolithic",
            parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                        "T_hot_K": 400.0, "T_cold_K": 300.0},
            design_operator_chain=["init"],
        )
        # Should not raise
        config2 = gen.apply_operator(config, op,
                                     materials=["copper", "graphene", "lead_telluride"])
        assert op in config2.design_operator_chain


# ---------------------------------------------------------------------------
# Capability-graph-driven material selection
# ---------------------------------------------------------------------------
def test_generator_uses_capability_graph_to_select_materials():
    """The generator selects materials whose capabilities match the spec."""
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("graphene", "conducts", "electricity"),
        ("aerogel", "prevents", "heat transfer"),
    ])
    spec = _spec()
    gen = ArtifactGenerator(seed=42)
    configs = gen.generate(spec, cg, n=5)
    # The candidate materials in provenance should include bismuth_telluride
    candidates = set()
    for c in configs:
        candidates.update(c.provenance.get("candidate_materials", []))
    assert "bismuth_telluride" in candidates
    # Aerogel doesn't have generates_voltage or conducts_electricity, so
    # it should NOT be a candidate for a thermoelectric spec.
    assert "aerogel" not in candidates


def test_generator_falls_back_when_no_capability_match():
    """When no materials match the capability graph, fall back to bismuth_telluride."""
    cg = CapabilityGraph()  # empty
    spec = _spec()
    gen = ArtifactGenerator(seed=42)
    configs = gen.generate(spec, cg, n=2)
    assert len(configs) == 2
    # At least the first config should use a known material
    for c in configs:
        assert len(c.components) >= 1
        assert c.components[0].material in MATERIAL_PARAMS


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
def test_provenance_recorded():
    """Each Configuration records its provenance (seed, generator, timestamp)."""
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=3)
    for c in configs:
        assert c.provenance["generator"] == "ArtifactGenerator"
        assert c.provenance["seed"] == 42
        assert "timestamp" in c.provenance
        assert "base_material" in c.provenance
        assert "candidate_materials" in c.provenance


def test_to_dict_serializable():
    """Configuration.to_dict produces a JSON-serializable dict."""
    import json
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=2)
    for c in configs:
        d = c.to_dict()
        json.dumps(d)  # raises if not serializable
        assert "config_hash" in d
        assert "components" in d


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
