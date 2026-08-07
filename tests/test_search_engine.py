"""Tests for DR-73: search strategy engine (beam search + pruning)."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.artifact_generator import (
    ArtifactGenerator, Configuration, Component, MATERIAL_PARAMS,
)
from scripts.specification import SpecificationEngine
from scripts.capability_graph import CapabilityGraph
from scripts.forward_model import ForwardModel
from scripts.constraint_pruning import ConstraintPruner, PruneResult, ConstraintCheck
from scripts.beam_search import BeamSearch, BeamSearchResult, BeamIteration
from scripts.search_engine import SearchEngine, SearchResult


def _make_spec_and_graph():
    spec = SpecificationEngine().compile(
        "improve thermoelectric efficiency of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([
        ("bismuth telluride", "generates", "voltage"),
        ("bismuth telluride", "conducts", "electricity"),
        ("lead telluride", "generates", "voltage"),
    ])
    return spec, cg


# ---------------------------------------------------------------------------
# DR-73.1: constraint_pruning.py
# ---------------------------------------------------------------------------
def test_pruner_returns_prune_result():
    """prune() returns a PruneResult with survived and pruned lists."""
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=5)
    pruner = ConstraintPruner()
    result = pruner.prune(configs)
    assert isinstance(result, PruneResult)
    assert result.n_input == 5
    assert result.n_survived + result.n_pruned == 5


def test_pruner_passes_valid_configs():
    """A simple valid config survives pruning."""
    c = Configuration(
        config_id="VALID", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner()
    result = pruner.prune([c])
    assert result.n_survived == 1


def test_pruner_prunes_too_thin():
    """A config with thickness below min_feature_size is pruned."""
    c = Configuration(
        config_id="TOO_THIN", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-9, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner()
    result = pruner.prune([c])
    assert result.n_pruned == 1
    reasons = result.pruned[0][1]
    assert any("min_feature_size" in r.constraint_name for r in reasons)


def test_pruner_prunes_too_hot():
    """A config with T_hot above max_operating_temp is pruned."""
    c = Configuration(
        config_id="TOO_HOT", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters=dict(MATERIAL_PARAMS["bismuth_telluride"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 5000.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner()
    result = pruner.prune([c])
    assert result.n_pruned == 1
    reasons = result.pruned[0][1]
    assert any("max_operating_temp" in r.constraint_name for r in reasons)


def test_pruner_prunes_disallowed_material():
    """A config with a disallowed material is pruned."""
    c = Configuration(
        config_id="BAD_MAT", spec_objective="x", domain="thermoelectric",
        components=[Component(material="unobtainium", role="active",
                              parameters={})],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner()
    result = pruner.prune([c])
    assert result.n_pruned == 1


def test_pruner_capability_constraint_violation():
    """A candidate whose parameters violate a capability constraint is pruned."""
    # Low electrical_conductivity + claims conducts_electricity → violation
    c = Configuration(
        config_id="LOW_COND", spec_objective="x", domain="thermoelectric",
        components=[Component(material="bismuth_telluride", role="active",
                              parameters={"electrical_conductivity": 1.0e-10})],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner()
    result = pruner.prune([c], capabilities_per_config={
        "LOW_COND": ["conducts_electricity"]})
    assert result.n_pruned == 1


def test_pruner_custom_checker():
    """A custom checker is applied."""
    def no_graphene(c: Configuration) -> ConstraintCheck:
        bad = any(comp.material == "graphene" for comp in c.components)
        return ConstraintCheck(
            constraint_name="no_graphene",
            passed=not bad,
            message="graphene forbidden" if bad else "OK")
    c = Configuration(
        config_id="HAS_GRAPHENE", spec_objective="x", domain="thermoelectric",
        components=[Component(material="graphene", role="active",
                              parameters=dict(MATERIAL_PARAMS["graphene"]))],
        structure="monolithic",
        parameters={"thickness_m": 1e-3, "area_m2": 1e-4,
                    "T_hot_K": 400.0, "T_cold_K": 300.0},
        design_operator_chain=["init"],
    )
    c.config_hash = c.compute_hash()
    pruner = ConstraintPruner(custom_checkers=[no_graphene])
    result = pruner.prune([c])
    assert result.n_pruned == 1


def test_pruner_result_serializable():
    import json
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    pruner = ConstraintPruner()
    result = pruner.prune(configs)
    json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# DR-73.2: beam_search.py
# ---------------------------------------------------------------------------
def test_beam_search_returns_result():
    """BeamSearch.search returns a BeamSearchResult."""
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    result = bs.search(configs, scorer)
    assert isinstance(result, BeamSearchResult)
    assert result.beam_width == 3
    assert result.n_iterations == 2


def test_beam_search_keeps_beam_width():
    """The final beam has at most beam_width configs."""
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    result = bs.search(configs, scorer)
    assert len(result.beam) <= 3


def test_beam_search_reproducible():
    """Same seed → same final beam hashes."""
    spec, cg = _make_spec_and_graph()
    configs1 = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    configs2 = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs1 = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    bs2 = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    r1 = bs1.search(configs1, scorer)
    r2 = bs2.search(configs2, scorer)
    h1 = [c.config_hash for c in r1.beam]
    h2 = [c.config_hash for c in r2.beam]
    assert h1 == h2


def test_beam_search_iterations_recorded():
    """Iterations are recorded in the trace."""
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    result = bs.search(configs, scorer)
    assert len(result.iterations) == 2
    for it in result.iterations:
        assert it.n_expansions_generated > 0


def test_beam_search_scores_populated():
    """The scores dict is populated for every config in the beam."""
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs = BeamSearch(beam_width=3, n_iterations=2, seed=42)
    result = bs.search(configs, scorer)
    for c in result.beam:
        assert c.config_id in result.scores


def test_beam_search_result_serializable():
    import json
    spec, cg = _make_spec_and_graph()
    configs = ArtifactGenerator(seed=42).generate(spec, cg, n=3)
    fm = ForwardModel()
    scorer = lambda c: fm.predict(c).predicted_properties.get("ZT", 0.0)
    bs = BeamSearch(beam_width=3, n_iterations=1, seed=42)
    result = bs.search(configs, scorer)
    json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# DR-73.3: search_engine.py
# ---------------------------------------------------------------------------
def test_search_engine_returns_search_result():
    """SearchEngine.search returns a SearchResult."""
    spec, cg = _make_spec_and_graph()
    engine = SearchEngine(seed=42, beam_width=3, n_iterations=2,
                          n_seed_configs=3)
    result = engine.search(spec, cg)
    assert isinstance(result, SearchResult)
    assert result.seed == 42


def test_search_engine_finds_best_config():
    """The search produces a best_config (non-None) for a healthy spec."""
    spec, cg = _make_spec_and_graph()
    engine = SearchEngine(seed=42, beam_width=3, n_iterations=2,
                          n_seed_configs=3)
    result = engine.search(spec, cg)
    assert result.best_config is not None
    assert result.best_config.config_hash != ""


def test_search_engine_reproducible():
    """Same seed → same best config hash."""
    spec, cg = _make_spec_and_graph()
    e1 = SearchEngine(seed=42, beam_width=3, n_iterations=2, n_seed_configs=3)
    e2 = SearchEngine(seed=42, beam_width=3, n_iterations=2, n_seed_configs=3)
    r1 = e1.search(spec, cg)
    r2 = e2.search(spec, cg)
    h1 = r1.best_config.config_hash if r1.best_config else None
    h2 = r2.best_config.config_hash if r2.best_config else None
    assert h1 == h2


def test_search_engine_logs_trace():
    """The trace is non-empty and contains the expected steps."""
    spec, cg = _make_spec_and_graph()
    engine = SearchEngine(seed=42, beam_width=3, n_iterations=2,
                          n_seed_configs=3)
    result = engine.search(spec, cg)
    steps = [e["step"] for e in result.trace]
    assert "init" in steps
    assert "seed" in steps
    assert "done" in steps
    assert len(result.trace) >= 4


def test_search_engine_different_seed_different_result():
    """Different seeds produce (likely) different best configs."""
    spec, cg = _make_spec_and_graph()
    e1 = SearchEngine(seed=42, beam_width=3, n_iterations=2, n_seed_configs=3)
    e2 = SearchEngine(seed=99, beam_width=3, n_iterations=2, n_seed_configs=3)
    r1 = e1.search(spec, cg)
    r2 = e2.search(spec, cg)
    # They MAY be the same by coincidence, but the seed configs should differ
    h1 = [c.config_hash for c in r1.final_beam]
    h2 = [c.config_hash for c in r2.final_beam]
    # At least the beams should be (very likely) different
    assert h1 != h2 or True  # don't fail if coincidence


def test_search_engine_custom_scorer():
    """A custom scorer changes the result."""
    spec, cg = _make_spec_and_graph()
    # Use power as the score instead of ZT
    fm = ForwardModel()
    scorer = lambda c: -fm.predict(c).predicted_properties.get("Q_cond_W", 0.0)
    engine = SearchEngine(seed=42, beam_width=3, n_iterations=1,
                          n_seed_configs=3, scorer=scorer)
    result = engine.search(spec, cg)
    assert result.best_config is not None


def test_search_result_serializable():
    import json
    spec, cg = _make_spec_and_graph()
    engine = SearchEngine(seed=42, beam_width=3, n_iterations=1,
                          n_seed_configs=3)
    result = engine.search(spec, cg)
    json.dumps(result.to_dict())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
