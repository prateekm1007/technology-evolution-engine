"""
Test for PAR-STR migration (Law 28 compliance, cycle 39).

Verifies that:
  1. CausalGraph.to_discovery_graph() produces a valid DiscoveryGraph
  2. The simulator accepts DiscoveryGraph
  3. The promoter accepts DiscoveryGraph
  4. Edge extractor can produce DiscoveryGraph directly
  5. CausalGraph is marked DEPRECATED
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import (
    CausalGraph, CausalEdge, CausalNode, EdgeTier, MechanismStatus,
)
from invention_compiler.discovery_graph import (
    DiscoveryGraph, Evidence, RelationType,
)
from invention_compiler.causal_simulator import CausalSimulator
from invention_compiler.formula_promoter import promote_edges_from_formula_results
from invention_compiler.edge_extractor import EdgeExtractor


@pytest.fixture
def sample_causal_graph():
    """Build a small CausalGraph for testing."""
    graph = CausalGraph()
    graph.add_node(CausalNode(
        node_id="A", node_type="material", label="Material A",
        properties={}, what_does_this_change=["property_B"],
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=["test"], provenance={},
    ))
    graph.add_node(CausalNode(
        node_id="B", node_type="property", label="Property B",
        properties={}, what_does_this_change=["application_C"],
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=["test"], provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test mechanism",
        mechanism_status=MechanismStatus.ASSERTED,
        evidence=["test"], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="property_B",
        intervention=None, counterfactual=None,
        created_at="", provenance={},
    ))
    return graph


class TestPARSTRMigration:
    """Test the PAR-STR migration from CausalGraph to DiscoveryGraph."""

    def test_causal_graph_is_thin_wrapper(self):
        """CausalGraph docstring must mention THIN WRAPPER (Law 28 cycle 40)."""
        assert "THIN WRAPPER" in CausalGraph.__doc__, (
            "CausalGraph must be marked as THIN WRAPPER per Law 28 (cycle 40)"
        )

    def test_causal_graph_has_to_discovery_graph(self, sample_causal_graph):
        """CausalGraph must have to_discovery_graph() migration method."""
        assert hasattr(sample_causal_graph, 'to_discovery_graph'), (
            "CausalGraph must have to_discovery_graph() method for migration"
        )

    def test_to_discovery_graph_produces_valid_graph(self, sample_causal_graph):
        """to_discovery_graph() returns a DiscoveryGraph with the right edges."""
        dg = sample_causal_graph.to_discovery_graph()
        assert isinstance(dg, DiscoveryGraph)
        # The ASSERTED edge should be in the mechanism layer
        assert len(dg.mechanism.edges) > 0 or len(dg.causal.edges) > 0, (
            "DiscoveryGraph should have edges from the CausalGraph"
        )

    def test_simulator_accepts_discovery_graph(self, sample_causal_graph):
        """CausalSimulator accepts DiscoveryGraph (Law 28 compliance)."""
        dg = sample_causal_graph.to_discovery_graph()
        sim = CausalSimulator(dg)
        # Should be able to propagate
        results = sim.propagate("A", start_value=1.0, auto_promote=False)
        assert len(results) > 0, "Simulator should produce results with DiscoveryGraph"

    def test_simulator_accepts_causal_graph(self, sample_causal_graph):
        """CausalSimulator still accepts CausalGraph (backward compatible)."""
        sim = CausalSimulator(sample_causal_graph)
        results = sim.propagate("A", start_value=1.0, auto_promote=False)
        assert len(results) > 0, "Simulator should produce results with CausalGraph"

    def test_promoter_accepts_discovery_graph(self, sample_causal_graph):
        """Formula promoter accepts DiscoveryGraph (Law 28 compliance)."""
        dg = sample_causal_graph.to_discovery_graph()
        result = promote_edges_from_formula_results(dg)
        assert "total_edges" in result, "Promoter should return results for DiscoveryGraph"

    def test_promoter_accepts_causal_graph(self, sample_causal_graph):
        """Formula promoter still accepts CausalGraph (backward compatible)."""
        result = promote_edges_from_formula_results(sample_causal_graph)
        assert "total_edges" in result, "Promoter should return results for CausalGraph"

    def test_edge_extractor_can_produce_discovery_graph(self):
        """EdgeExtractor.extract_from_corpus(use_discovery_graph=True) produces DiscoveryGraph."""
        extractor = EdgeExtractor()
        dg = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "papers"),
            use_discovery_graph=True,
        )
        assert isinstance(dg, DiscoveryGraph), (
            "extract_from_corpus(use_discovery_graph=True) should return DiscoveryGraph"
        )

    def test_edge_extractor_default_produces_discovery_graph(self):
        """EdgeExtractor.extract_from_corpus() default now produces DiscoveryGraph (Law 28 canonical)."""
        extractor = EdgeExtractor()
        dg = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "papers"),
        )
        # Default is now DiscoveryGraph (canonical per Law 28 cycle 40)
        # CausalGraph is still accessible via use_discovery_graph=False
        from invention_compiler.discovery_graph import DiscoveryGraph
        assert isinstance(dg, DiscoveryGraph), (
            f"Default should return DiscoveryGraph (canonical). Got {type(dg)}"
        )
