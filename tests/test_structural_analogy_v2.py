"""Tests for structural_analogy_v2.py — Structural analogy 6→8."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.structural_analogy_v2 import (
    Depth2StructureMappingEngine,
    Depth2Analogy,
    MultiChainAnalogy,
)


def _build_test_graph():
    """Build a test graph with 3 analogous depth-2 chains."""
    from invention_compiler.discovery_graph import (
        DiscoveryGraph, DiscoveryNode, DiscoveryEdge, RelationType
    )
    graph = DiscoveryGraph()
    all_nodes = [
        ("sunlight", "biology"), ("photosynthesis", "biology"),
        ("glucose", "biology"), ("atp", "biology"),
        ("photons", "solar"), ("photovoltaic", "solar"),
        ("electricity", "solar"), ("battery", "solar"),
        ("fuel", "thermal"), ("combustion", "thermal"),
        ("heat", "thermal"), ("engine", "thermal"),
    ]
    for nid, domain in all_nodes:
        graph.add_node(DiscoveryNode(
            node_id=nid, node_type="concept", label=nid,
            properties={"domain": domain}, layers=set(), provenance={},
        ))
    edges = [
        ("sunlight", "photosynthesis", "causes"),
        ("photosynthesis", "glucose", "produces"),
        ("glucose", "atp", "enables"),
        ("photons", "photovoltaic", "causes"),
        ("photovoltaic", "electricity", "produces"),
        ("electricity", "battery", "enables"),
        ("fuel", "combustion", "causes"),
        ("combustion", "heat", "produces"),
        ("heat", "engine", "enables"),
    ]
    for src, tgt, pred in edges:
        graph.add_edge(DiscoveryEdge(
            source=src, target=tgt, relation_type=RelationType.MECHANISM,
            evidence=[], metadata={}, direction=pred,
        ))
    return graph


def test_depth2_analogies_found():
    """Depth-2 analogies are found on a graph with 3 analogous chains."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    analogies = engine.find_depth2_analogies()
    # The 3 domains × 2 chain positions should yield ≥3 depth-2 analogies
    assert len(analogies) >= 3, f"Expected ≥3 depth-2 analogies, got {len(analogies)}"


def test_depth2_predicate_pair_aligned():
    """Each depth-2 analogy has aligned predicate pairs."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    analogies = engine.find_depth2_analogies()
    for a in analogies:
        assert len(a.predicate_pair_a) == 2
        assert len(a.predicate_pair_b) == 2
        # Systematicity must be in [0.5, 1.0] for any aligned pair
        assert 0.5 <= a.systematicity <= 1.0, \
            f"Systematicity {a.systematicity} out of range"


def test_depth2_chains_disjoint():
    """Depth-2 analogy chains share no nodes."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    analogies = engine.find_depth2_analogies()
    for a in analogies:
        assert set(a.chain_a).isdisjoint(set(a.chain_b)), \
            f"Chains share nodes: {set(a.chain_a) & set(a.chain_b)}"


def test_depth2_inference_confidence_weighted():
    """Inference confidence is weighted by systematicity."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    analogies = engine.find_depth2_analogies()
    for a in analogies:
        for inf in a.inferences:
            # Confidence must be ≤ systematicity * 0.9 (the high-sys branch)
            assert inf.confidence <= a.systematicity * 0.9 + 1e-6, \
                f"Confidence {inf.confidence} exceeds sys*0.9 = {a.systematicity * 0.9}"


def test_multichain_analogies_found():
    """Multi-chain consensus analogies (≥3 chains) are found."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    multichain = engine.find_multichain_analogies(min_chains=3)
    # The (causes, produces) sequence appears in 3 disjoint chains
    assert len(multichain) >= 1, "Expected ≥1 multi-chain analogy"
    # At least one should have ≥3 chains
    assert any(len(m.chains) >= 3 for m in multichain), \
        f"No multi-chain analogy with ≥3 chains: {[len(m.chains) for m in multichain]}"


def test_multichain_chains_disjoint():
    """All chains in a multi-chain analogy are pairwise disjoint."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    multichain = engine.find_multichain_analogies(min_chains=3)
    for m in multichain:
        for i in range(len(m.chains)):
            for j in range(i + 1, len(m.chains)):
                assert set(m.chains[i]).isdisjoint(set(m.chains[j])), \
                    f"Chains {i} and {j} share nodes"


def test_multichain_systematicity_is_1():
    """Multi-chain analogies have systematicity = 1.0 (exact predicate match)."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    multichain = engine.find_multichain_analogies(min_chains=3)
    for m in multichain:
        assert m.systematicity == 1.0, \
            f"Expected systematicity 1.0, got {m.systematicity}"


def test_no_depth2_analogies_on_empty_graph():
    """An empty graph yields no depth-2 analogies."""
    from invention_compiler.discovery_graph import DiscoveryGraph
    engine = Depth2StructureMappingEngine(DiscoveryGraph())
    assert engine.find_depth2_analogies() == []


def test_depth2_inference_reasoning_mentions_systematicity():
    """Every inference's reasoning string mentions the systematicity."""
    graph = _build_test_graph()
    engine = Depth2StructureMappingEngine(graph)
    analogies = engine.find_depth2_analogies()
    for a in analogies:
        for inf in a.inferences:
            assert "sys=" in inf.reasoning, \
                f"Reasoning missing systematicity: {inf.reasoning}"


def test_predicate_groups_inherited():
    """Depth2StructureMappingEngine inherits PREDICATE_GROUPS from the parent."""
    from scripts.structural_analogy import StructureMappingEngine
    assert Depth2StructureMappingEngine.PREDICATE_GROUPS is \
        StructureMappingEngine.PREDICATE_GROUPS


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
