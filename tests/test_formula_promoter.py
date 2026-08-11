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

    def test_failing_formula_edge_marked_contradicted(self, test_graph):
        """GAP-002: An edge with a failing formula should be marked CONTRADICTED, not left ASSERTED.

        A CONTRADICTED edge is actively wrong — its stated expected_output
        does not match the formula's computed output. This is different
        from ASSERTED (untested) and from ASSOCIATIVE (no mechanism).
        """
        result = promote_edges_from_formula_results(test_graph)
        contradicted_edges = [
            d for d in result["promotion_details"]
            if d.get("promotion") == "ASSERTED → CONTRADICTED"
        ]
        assert len(contradicted_edges) >= 1, (
            "Expected at least 1 CONTRADICTED edge (the one with wrong expected output). "
            f"Details: {result['promotion_details']}"
        )
        # The CONTRADICTED edge should not be discovery-capable
        for edge in test_graph.edges:
            if edge.tier == EdgeTier.CONTRADICTED:
                assert not edge.is_discovery_capable(), (
                    "CONTRADICTED edges should not be discovery-capable"
                )
                assert not edge.is_simulation_capable(), (
                    "CONTRADICTED edges should not be simulation-capable"
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


# ----------------------------------------------------------------------
# GAP-003: On-demand formula execution (inputs not in FORMULA_REGISTRY)
# ----------------------------------------------------------------------

class TestOnDemandExecution:
    """GAP-003: The promoter should execute formulas on-demand for edges
    whose specific input/output combination isn't in the FORMULA_REGISTRY's
    test cases."""

    def test_on_demand_execution_promotes_matching_edge(self):
        """An edge with inputs NOT in the registry but that match the formula
        should be promoted via on-demand execution."""
        graph = CausalGraph()
        graph.add_node(CausalNode(
            node_id="T", node_type="property", label="Temperature",
            properties={}, what_does_this_change=["Twb"],
            what_changes_this=[], inputs=[], constraints=[], outputs=[],
            evidence=["test"], provenance={},
        ))
        graph.add_node(CausalNode(
            node_id="Twb", node_type="property", label="Wet-bulb",
            properties={}, what_does_this_change=["cooling"],
            what_changes_this=[], inputs=[], constraints=[], outputs=[],
            evidence=["test"], provenance={},
        ))

        # Edge with inputs (T=25, RH=60) — NOT in the FORMULA_REGISTRY
        # The actual Stull value for T=25, RH=60 is ~17.6°C
        from scripts.formulas.stull_wet_bulb import stull_wet_bulb
        actual_twb = stull_wet_bulb(25, 60)

        graph.add_edge(CausalEdge(
            source="T", target="Twb", direction="causes",
            mechanism="Stull wet-bulb formula",
            mechanism_status=MechanismStatus.ASSERTED,
            evidence=["test"], tier=EdgeTier.ASSERTED,
            formula="stull_wet_bulb",
            formula_inputs={"T": 25, "RH": 60},
            formula_output=actual_twb,  # correct value
            expected_output=actual_twb,
            tolerance=0.5,
            falsifiable_by="Execute Stull formula",
            what_does_this_change="Twb",
            intervention=None, counterfactual=None,
            created_at="", provenance={},
        ))

        result = promote_edges_from_formula_results(graph)
        assert result["promoted"] >= 1, (
            f"Expected on-demand promotion for edge with inputs not in registry. "
            f"Details: {result['promotion_details']}"
        )

    def test_on_demand_execution_contradicts_failing_edge(self):
        """An edge with inputs NOT in the registry and WRONG expected output
        should be marked CONTRADICTED via on-demand execution."""
        graph = CausalGraph()
        graph.add_node(CausalNode(
            node_id="T", node_type="property", label="Temperature",
            properties={}, what_does_this_change=["Twb"],
            what_changes_this=[], inputs=[], constraints=[], outputs=[],
            evidence=["test"], provenance={},
        ))
        graph.add_node(CausalNode(
            node_id="Twb", node_type="property", label="Wet-bulb",
            properties={}, what_does_this_change=["cooling"],
            what_changes_this=[], inputs=[], constraints=[], outputs=[],
            evidence=["test"], provenance={},
        ))

        # Edge with inputs (T=25, RH=60) — NOT in the FORMULA_REGISTRY
        # But expected_output is WRONG (10.0 instead of ~17.6)
        graph.add_edge(CausalEdge(
            source="T", target="Twb", direction="causes",
            mechanism="Stull wet-bulb formula (wrong value)",
            mechanism_status=MechanismStatus.ASSERTED,
            evidence=["test"], tier=EdgeTier.ASSERTED,
            formula="stull_wet_bulb",
            formula_inputs={"T": 25, "RH": 60},
            formula_output=10.0,  # WRONG — actual is ~17.6
            expected_output=10.0,
            tolerance=0.5,
            falsifiable_by="Execute Stull formula",
            what_does_this_change="Twb",
            intervention=None, counterfactual=None,
            created_at="", provenance={},
        ))

        result = promote_edges_from_formula_results(graph)
        contradicted = [
            d for d in result["promotion_details"]
            if d.get("promotion") == "ASSERTED → CONTRADICTED"
        ]
        assert len(contradicted) >= 1, (
            f"Expected on-demand CONTRADICTED for wrong edge. "
            f"Details: {result['promotion_details']}"
        )


# ----------------------------------------------------------------------
# GAP-004: Idempotency (running promoter twice should be safe)
# ----------------------------------------------------------------------

class TestIdempotency:
    """GAP-004: If the promoter runs twice on the same graph, it should
    skip already-VERIFIED edges and not re-process them."""

    def test_idempotent_on_second_run(self, test_graph):
        """Running promote_edges_from_formula_results twice should produce
        the same graph state — no double-promotion, no errors."""
        # First run
        result1 = promote_edges_from_formula_results(test_graph)
        promoted1 = result1["promoted"]
        verified1 = test_graph.tier_counts()["verified"]

        # Second run on the same graph
        result2 = promote_edges_from_formula_results(test_graph)
        promoted2 = result2["promoted"]
        verified2 = test_graph.tier_counts()["verified"]

        # Second run should NOT promote any new edges
        assert promoted2 == 0, (
            f"Second run promoted {promoted2} edges — should be 0 (idempotent). "
            f"First run promoted {promoted1}."
        )
        # Verified count should not change
        assert verified1 == verified2, (
            f"Verified count changed: {verified1} → {verified2}. Should be the same."
        )

    def test_idempotent_contradicted_edges(self, test_graph):
        """CONTRADICTED edges should not be re-processed on second run."""
        # First run — marks some edges CONTRADICTED
        promote_edges_from_formula_results(test_graph)
        contradicted1 = test_graph.tier_counts().get("contradicted", 0)

        # Second run
        promote_edges_from_formula_results(test_graph)
        contradicted2 = test_graph.tier_counts().get("contradicted", 0)

        assert contradicted1 == contradicted2, (
            f"Contradicted count changed: {contradicted1} → {contradicted2}. "
            f"Should be the same (idempotent)."
        )
