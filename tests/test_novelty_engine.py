"""Tests for novelty_engine.py — Stage V."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.novelty_engine import NoveltyEngine, NoveltyReport
from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
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
        ("lead telluride", "generates", "voltage"),
    ])
    return cg


def _config(material="bismuth_telluride", role="active",
            structure="monolithic",
            params=None, config_id="X",
            objective="improve thermoelectric efficiency"):
    """Build a minimal Configuration for testing."""
    c = Configuration(
        config_id=config_id,
        spec_objective=objective,
        domain="thermoelectric",
        components=[Component(material=material, role=role,
                              parameters=dict(MATERIAL_PARAMS.get(material, {})))],
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
def test_check_returns_novelty_report():
    """check() returns a NoveltyReport."""
    engine = NoveltyEngine()
    r = engine.check(_config())
    assert isinstance(r, NoveltyReport)
    assert r.is_novel is True
    assert r.config_hash != ""


def test_fresh_registry_everything_is_novel():
    """An empty registry means everything is novel."""
    engine = NoveltyEngine()
    assert engine.check(_config(config_id="A")).is_novel
    assert engine.check(_config(config_id="B")).is_novel


def test_register_then_check_known():
    """After registering, the same config is not novel."""
    engine = NoveltyEngine()
    c = _config(config_id="A")
    engine.register(c)
    r = engine.check(c)
    assert not r.is_novel
    assert r.known_match == "A"
    assert r.known_match_hash == c.config_hash


def test_is_novel_convenience():
    """is_novel() is a convenience wrapper."""
    engine = NoveltyEngine()
    c = _config(config_id="A")
    assert engine.is_novel(c)
    engine.register(c)
    assert not engine.is_novel(c)


def test_registry_size_grows():
    """registry_size increases as we register distinct configs."""
    engine = NoveltyEngine()
    assert engine.registry_size() == 0
    engine.register(_config(material="bismuth_telluride", config_id="A"))
    assert engine.registry_size() == 1
    engine.register(_config(material="lead_telluride", config_id="B"))
    assert engine.registry_size() == 2


# ---------------------------------------------------------------------------
# Core invariant: same configuration, different wording → NOT novel
# ---------------------------------------------------------------------------
def test_same_config_different_wording_not_novel():
    """Same configuration with different spec_objective → same hash → NOT novel."""
    c1 = _config(objective="improve thermoelectric efficiency",
                  config_id="A")
    c2 = _config(objective="boost ZT — totally different wording",
                  config_id="B")
    assert c1.config_hash == c2.config_hash, (
        "rewriting spec_objective must not change config_hash")

    engine = NoveltyEngine()
    engine.register(c1)
    r = engine.check(c2)
    assert not r.is_novel, (
        "different wording, same configuration → must NOT be novel")


def test_same_config_different_chain_not_novel():
    """Same configuration reached by a different operator chain → NOT novel."""
    c1 = Configuration(
        config_id="A", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init", "amplify", "layer"],
    )
    c2 = Configuration(
        config_id="B", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init", "substitute", "modulate", "stabilize"],
    )
    c1.config_hash = c1.compute_hash()
    c2.config_hash = c2.compute_hash()
    assert c1.config_hash == c2.config_hash, (
        "different operator chain must not change config_hash")

    engine = NoveltyEngine()
    engine.register(c1)
    assert not engine.is_novel(c2)


def test_same_config_different_provenance_not_novel():
    """Same configuration with different provenance → NOT novel."""
    c1 = Configuration(
        config_id="A", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        provenance={"generator": "X", "seed": 1, "timestamp": "2024-01-01"},
    )
    c2 = Configuration(
        config_id="B", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3},
        provenance={"generator": "Y", "seed": 999, "timestamp": "2025-12-31"},
    )
    c1.config_hash = c1.compute_hash()
    c2.config_hash = c2.compute_hash()
    assert c1.config_hash == c2.config_hash

    engine = NoveltyEngine()
    engine.register(c1)
    assert not engine.is_novel(c2)


def test_same_config_different_id_not_novel():
    """Same configuration with different config_id → NOT novel."""
    c1 = _config(config_id="CONFIG-0001-001")
    c2 = _config(config_id="CONFIG-9999-999")
    assert c1.config_hash == c2.config_hash

    engine = NoveltyEngine()
    engine.register(c1)
    r = engine.check(c2)
    assert not r.is_novel
    # The known_match should be the original config_id ("CONFIG-0001-001")
    assert r.known_match == "CONFIG-0001-001"


# ---------------------------------------------------------------------------
# New configuration of known parts → NOVEL
# ---------------------------------------------------------------------------
def test_different_material_is_novel():
    """Different material → different hash → novel."""
    engine = NoveltyEngine()
    engine.register(_config(material="bismuth_telluride", config_id="A"))
    c2 = _config(material="lead_telluride", config_id="B")
    assert engine.is_novel(c2)


def test_different_structure_is_novel():
    """Different structure (monolithic vs layered_3) → different hash → novel."""
    engine = NoveltyEngine()
    engine.register(_config(structure="monolithic", config_id="A"))
    c2 = _config(structure="layered_3", config_id="B")
    assert engine.is_novel(c2)


def test_different_parameter_is_novel():
    """Different parameter value → different hash → novel."""
    engine = NoveltyEngine()
    engine.register(_config(params={"thickness_m": 1e-3, "area_m2": 1e-4,
                                    "T_hot_K": 400.0, "T_cold_K": 300.0},
                              config_id="A"))
    c2 = _config(params={"thickness_m": 5e-4, "area_m2": 1e-4,
                         "T_hot_K": 400.0, "T_cold_K": 300.0},
                  config_id="B")
    assert engine.is_novel(c2)


def test_extra_component_is_novel():
    """Adding a second component → different hash → novel."""
    engine = NoveltyEngine()
    engine.register(_config(config_id="A"))
    c2 = _config(config_id="B")
    c2.components.append(Component(material="copper", role="electrode",
                                   parameters=dict(MATERIAL_PARAMS["copper"])))
    c2.config_hash = c2.compute_hash()
    assert engine.is_novel(c2)


# ---------------------------------------------------------------------------
# Independence of retrieval phrasing
# ---------------------------------------------------------------------------
def test_novelty_independent_of_retrieval_phrasing():
    """Novelty does not depend on the wording of the spec_objective.

    This is the auditor's key requirement: novelty is at the configuration
    level, not the prose level.
    """
    engine = NoveltyEngine()

    # Config A — registered with one phrasing
    c_a = _config(objective="improve thermoelectric efficiency",
                  config_id="A")
    engine.register(c_a)

    # Config B — IDENTICAL configuration, DIFFERENT phrasing
    c_b = _config(objective="boost the figure of merit",
                  config_id="B")
    assert c_a.config_hash == c_b.config_hash
    assert not engine.is_novel(c_b), (
        "Same configuration, different phrasing must NOT be novel")

    # Config C — DIFFERENT configuration (different material)
    c_c = _config(material="lead_telluride",
                  objective="improve thermoelectric efficiency",  # same phrasing as A!
                  config_id="C")
    assert c_a.config_hash != c_c.config_hash
    assert engine.is_novel(c_c), (
        "Different configuration, same phrasing MUST be novel")


# ---------------------------------------------------------------------------
# run() batch processing
# ---------------------------------------------------------------------------
def test_run_processes_batch():
    """run() processes a batch of Configurations."""
    engine = NoveltyEngine()
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=5)
    reports = engine.run(configs, register_novel=True)
    assert len(reports) == 5
    # First one is novel (registry was empty)
    assert reports[0].is_novel
    # All should be novel if hashes are distinct (they should be)
    n_novel = sum(1 for r in reports if r.is_novel)
    assert n_novel >= 1


def test_run_registers_novel_configs():
    """run() with register_novel=True adds novel configs to the registry."""
    engine = NoveltyEngine()
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=5)
    engine.run(configs, register_novel=True)
    # Registry should now contain at least 1 hash
    assert engine.registry_size() >= 1


def test_run_same_batch_twice_second_all_known():
    """run() twice with the same batch → second run is all KNOWN."""
    engine = NoveltyEngine()
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=5)
    reports1 = engine.run(configs, register_novel=True)
    reports2 = engine.run(configs, register_novel=True)
    n_known_2 = sum(1 for r in reports2 if not r.is_novel)
    assert n_known_2 == len(configs), (
        f"second run should be all known, got {n_known_2}/{len(configs)}")


def test_generate_alias_works():
    """generate() is an alias for run(register_novel=False)."""
    engine = NoveltyEngine()
    configs = ArtifactGenerator(seed=42).generate(_spec(), _cg(), n=3)
    reports = engine.generate(configs)
    assert len(reports) == 3
    # generate() doesn't register, so registry should still be empty
    assert engine.registry_size() == 0


# ---------------------------------------------------------------------------
# Nearest neighbor
# ---------------------------------------------------------------------------
def test_nearest_neighbor_empty_registry():
    """If registry is empty, nearest neighbor is None."""
    engine = NoveltyEngine()
    r = engine.check(_config())
    assert r.nearest_neighbor_hash is None
    assert r.nearest_neighbor_distance == 0


def test_nearest_neighbor_exact_match_distance_zero():
    """An exact match has nearest-neighbor distance 0."""
    engine = NoveltyEngine()
    c = _config(config_id="A")
    engine.register(c)
    r = engine.check(c)
    assert r.nearest_neighbor_distance == 0
    assert r.nearest_neighbor_hash == c.config_hash


def test_nearest_neighbor_different_config_nonzero_distance():
    """A different config has nearest-neighbor distance > 0."""
    engine = NoveltyEngine()
    engine.register(_config(material="bismuth_telluride", config_id="A"))
    c2 = _config(material="lead_telluride", config_id="B")
    r = engine.check(c2)
    assert r.nearest_neighbor_distance > 0


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------
def test_report_to_dict_serializable():
    """NoveltyReport.to_dict produces a JSON-serializable dict."""
    import json
    engine = NoveltyEngine()
    r = engine.check(_config())
    d = r.to_dict()
    json.dumps(d)
    assert "is_novel" in d
    assert "config_hash" in d


def test_reset_clears_registry():
    """reset() clears the registry."""
    engine = NoveltyEngine()
    engine.register(_config(config_id="A"))
    assert engine.registry_size() == 1
    engine.reset()
    assert engine.registry_size() == 0
    assert engine.is_novel(_config(config_id="A"))


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------
def test_generated_batch_novelty_dedup():
    """Two generators with the same seed produce the same hashes."""
    spec, cg = _spec(), _cg()
    batch1 = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    batch2 = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    h1 = [c.config_hash for c in batch1]
    h2 = [c.config_hash for c in batch2]
    assert h1 == h2

    engine = NoveltyEngine()
    engine.run(batch1, register_novel=True)
    # Now batch2 — same hashes — should all be known
    reports2 = engine.run(batch2, register_novel=True)
    n_known = sum(1 for r in reports2 if not r.is_novel)
    assert n_known == len(batch2)


def test_known_configs_in_constructor():
    """Constructor accepts a list of known Configurations."""
    c1 = _config(material="bismuth_telluride", config_id="A")
    c2 = _config(material="lead_telluride", config_id="B")
    engine = NoveltyEngine(known_configs=[c1, c2])
    assert engine.registry_size() == 2
    assert not engine.is_novel(c1)
    assert not engine.is_novel(c2)
    # A third, different config should be novel
    c3 = _config(material="graphene", config_id="C")
    assert engine.is_novel(c3)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
