"""
Tests for the formula-to-edge promotion module (Layer 2 → Layer 3).

Per F-061: "VERIFIED tier is empty" — this module fills it by promoting
ASSERTED edges to VERIFIED when the formula verifier confirms the formula
matches.

Tests verify:
  1. Edges with passing formulas get promoted to VERIFIED
  2. Edges with failing formulas stay ASSERTED
  3. Associative edges are never promoted
  4. The causal_density metric increases after promotion
  5. The verify_and_promote() function works end-to-end
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
)
from invention_compiler.formula_promoter import (
    promote_edges_from_formula_results, verify_and_promote,
)


@pytest.fixture
def test_graph():
    """Build a small test graph with edges that reference formulas."""
    graph = CausalGraph()

    # Node: temperature
    graph.add_node(CausalNode(
        node_id="temperature", node_type="property", label="Temperature",
        properties={},
        what_does_this_change=["wet_bulb_temperature"],
        what_changes_this=[],
        inputs=[], constraints=[], outputs=[],
        evidence=["test"],
        provenance={"source": "test"},
    ))

    # Node: wet_bulb_temperature
    graph.add_node(CausalNode(
        node_id="wet_bulb_temperature", node_type="property", label="Wet-bulb temperature",
        properties={},
        what_does_this_change=["passive_cooling_viability"],
        what_changes_this=[],
        inputs=[], constraints=[], outputs=[],
        evidence=["test"],
        provenance={"source": "test"},
    ))

    # Edge: temperature → wet_bulb_temperature (ASSERTED, references stull_wet_bulb)
    graph.add_edge(CausalEdge(
        source="temperature", target="wet_bulb_temperature", direction="causes",
        mechanism="Stull wet-bulb formula converts T and RH to T_wb",
        mechanism_status=MechanismStatus.ASSERTED,
        evidence=["test"], tier=EdgeTier.ASSERTED,
        formula="stull_wet_bulb",
        formula_inputs={"T": 20, "RH": 50},
        formula_output=13.7,
        expected_output=13.7,
        tolerance=0.5,
        falsifiable_by="Execute Stull formula with same inputs",
        what_does_this_change="wet_bulb_temperature",
        intervention=None, counterfactual=None,
        created_at="", provenance={},
    ))

    # Edge: with a FAILING formula (wrong expected output)
    graph.add_edge(CausalEdge(
        source="temperature", target="wet_bulb_temperature", direction="causes",
        mechanism="Stull wet-bulb (wrong expected value)",
        mechanism_status=MechanismStatus.ASSERTED,
        evidence=["test"], tier=EdgeTier.ASSERTED,
        formula="stull_wet_bulb",
        formula_inputs={"T": 42, "RH": 25},
        formula_output=19.0,  # WRONG — actual is 25.8
        expected_output=19.0,
        tolerance=0.5,
        falsifiable_by="Execute Stull formula",
        what_does_this_change="wet_bulb_temperature",
        intervention=None, counterfactual=None,
        created_at="", provenance={},
    ))

    # Edge: ASSOCIATIVE (no formula — should never be promoted)
    graph.add_edge(CausalEdge(
        source="A", target="B", direction="related_to",
        mechanism=None, mechanism_status=None,
        evidence=["test"], tier=EdgeTier.ASSOCIATIVE,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change=None,
        intervention=None, counterfactual=None,
        created_at="", provenance={},
    ))

    return graph


class TestFormulaPromotion:
    def test_passing_formula_edge_gets_promoted(self, test_graph):
        """An edge with a passing formula should be promoted to VERIFIED."""
        result = promote_edges_from_formula_results(test_graph)
        assert result["promoted"] >= 1, (
            f"Expected at least 1 promoted edge, got {result['promoted']}. "
            f"Details: {result['promotion_details']}"
        )

    def test_failing_formula_edge_stays_asserted(self, test_graph):
        """An edge with a failing formula should stay ASSERTED."""
        result = promote_edges_from_formula_results(test_graph)
        # The edge with formula_output=19.0 (wrong) should NOT be promoted
        wrong_edges = [
            d for d in result["promotion_details"]
            if d.get("promotion") == "NOT PROMOTED" and "stull_wet_bulb" in d.get("formula", "")
        ]
        assert len(wrong_edges) >= 1, (
            "Expected at least 1 NOT PROMOTED edge (the one with wrong expected output)"
        )

    def test_associative_edge_never_promoted(self, test_graph):
        """ASSOCIATIVE edges should never be promoted."""
        result = promote_edges_from_formula_results(test_graph)
        assert result["not_promotable"] >= 1, (
            "Expected at least 1 not-promotable edge (the ASSOCIATIVE one)"
        )

    def test_causal_density_increases_after_promotion(self, test_graph):
        """The causal_density metric should increase after promotion."""
        density_before = test_graph.causal_density()
        promote_edges_from_formula_results(test_graph)
        density_after = test_graph.causal_density()
        assert density_after > density_before, (
            f"Causal density should increase: before={density_before}, after={density_after}"
        )

    def test_promoted_edge_is_simulation_capable(self, test_graph):
        """A promoted edge should be simulation-capable (VERIFIED + DERIVED)."""
        promote_edges_from_formula_results(test_graph)
        # Find the promoted edge (the one with T=20, RH=50)
        promoted_edges = [
            e for e in test_graph.edges
            if e.tier == EdgeTier.VERIFIED
            and e.mechanism_status == MechanismStatus.DERIVED
        ]
        assert len(promoted_edges) >= 1, "Expected at least 1 VERIFIED+DERIVED edge"
        for e in promoted_edges:
            assert e.is_simulation_capable(), (
                f"Promoted edge {e.source}→{e.target} should be simulation-capable"
            )

    def test_verify_and_promote_end_to_end(self, test_graph):
        """The verify_and_promote() function should work end-to-end."""
        result = verify_and_promote(test_graph)
        assert "formula_results" in result
        assert "promotion_result" in result
        assert "tier_counts" in result
        assert result["promotion_result"]["promoted"] >= 1
        # After promotion, the graph should have VERIFIED edges
        assert result["tier_counts"]["verified"] >= 1, (
            f"Expected at least 1 VERIFIED edge after promotion, got {result['tier_counts']}"
        )
