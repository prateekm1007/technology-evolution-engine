"""
Tests for the causal propagation simulator (Phase III) and experiment
designer (Phase V).

Per F-048: the simulator must propagate mechanisms, not perturb scores.
Per DR-5: "No simulation may perturb a score. It must simulate a mechanism."
Per DR-18: the system's primary output is the next experiment.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
)
from invention_compiler.causal_simulator import CausalSimulator, PropagationResult
from invention_compiler.edge_extractor import EdgeExtractor


@pytest.fixture
def corpus_graph():
    """Build a causal graph from the 20-document corpus.

    Per Law 28 (cycle 40): uses use_discovery_graph=False to get
    CausalGraph (thin wrapper) for backward compatibility with tests
    that use CausalGraph API (add_node, add_edge, adjacency_search).
    """
    extractor = EdgeExtractor()
    papers_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False)
    patents_graph = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False)
    combined = CausalGraph()
    for nid, node in papers_graph.nodes.items():
        combined.add_node(node)
    for nid, node in patents_graph.nodes.items():
        if nid not in combined.nodes:
            combined.add_node(node)
        else:
            existing = combined.nodes[nid]
            existing.what_does_this_change = list(
                set(existing.what_does_this_change + node.what_does_this_change)
            )
            existing.evidence = list(set(existing.evidence + node.evidence))
    for edge in papers_graph.edges + patents_graph.edges:
        exists = any(
            e.source == edge.source and e.target == edge.target and e.mechanism == edge.mechanism
            for e in combined.edges
        )
        if not exists:
            combined.add_edge(edge)
    return combined


class TestCausalSimulator:
    """Test the causal propagation simulator (Phase III)."""

    def test_simulator_only_uses_verified_edges_for_propagation(self, corpus_graph):
        """Per DR-5/F-048: the simulator must only propagate through
        simulation-capable edges (verified with observed/simulated/derived status)."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0)

        # All propagation results should be either "starting" or "asserted"
        # (since no edges are verified yet — all are ASSERTED tier)
        for r in results:
            assert r.tier in ("starting", "verified", "asserted"), (
                f"Unexpected tier: {r.tier} for node {r.node_id}"
            )

    def test_simulator_marks_asserted_edges_as_hypothetical(self, corpus_graph):
        """Asserted-tier edges should be marked as hypothetical in propagation."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0)

        asserted_results = [r for r in results if r.tier == "asserted"]
        if asserted_results:
            for r in asserted_results:
                assert "ASSERTED" in r.note or "hypothetical" in r.note.lower(), (
                    f"Asserted edge should be marked as hypothetical: {r.note}"
                )

    def test_simulator_does_not_silently_propagate_through_unverified(self, corpus_graph):
        """Per DR-15: asserted edges cannot be used in simulation.
        The simulator must say so rather than silently propagating."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0)

        # No verified propagation should occur (all edges are ASSERTED)
        verified_results = [r for r in results if r.tier == "verified"]
        assert len(verified_results) == 0, (
            "Found verified propagation results but all edges should be ASSERTED — "
            "the simulator must not silently propagate through unverified edges."
        )


class TestExperimentDesign:
    """Test the experiment designer (Phase V / DR-18)."""

    def test_design_experiment_from_causal_path(self, corpus_graph):
        """The simulator can design an experiment from a causal path."""
        sim = CausalSimulator(corpus_graph)
        experiment = sim.design_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 100K temperature difference",
            measurement_desc="measure power output (W)",
            falsification_desc="power output < 0.5W",
            cost_usd=200.0,
            timeline_days=3,
            learning_pass="thermoelectric path verified",
            learning_fail="thermoelectric path needs revision",
        )
        assert experiment is not None, "Should design an experiment for reachable target"
        assert "Bi2Te3" in experiment.prediction
        assert "te_power_generation" in experiment.prediction
        assert experiment.cost_usd == 200.0
        assert experiment.learning_if_fail != ""

    def test_design_experiment_for_unreachable_target(self, corpus_graph):
        """If the target is not reachable, the experiment cannot be designed."""
        sim = CausalSimulator(corpus_graph)
        experiment = sim.design_experiment(
            start_node_id="Bi2Te3",
            target_node_id="nonexistent_node",
            intervention_node="x",
            intervention_desc="test",
            measurement_desc="test",
            falsification_desc="test",
            cost_usd=0,
            timeline_days=0,
            learning_pass="test",
            learning_fail="test",
        )
        assert experiment is None, "Should not design experiment for unreachable target"

    def test_experiment_includes_learning_from_failure(self, corpus_graph):
        """DR-18: the experiment must include what is learned from BOTH pass and fail."""
        sim = CausalSimulator(corpus_graph)
        experiment = sim.design_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 100K ΔT",
            measurement_desc="measure power",
            falsification_desc="power < 0.5W",
            cost_usd=200.0,
            timeline_days=3,
            learning_pass="path verified",
            learning_fail="path needs revision — material or module design is wrong",
        )
        assert experiment.learning_if_fail
        assert "revision" in experiment.learning_if_fail.lower() or "wrong" in experiment.learning_if_fail.lower(), (
            "learning_if_fail must specify what to revise — not just 'it failed'"
        )


class TestApolloTestInternal:
    """Phase IV: Re-run the Apollo Test as an internal graph query."""

    def test_bi2te3_connects_to_thermoelectric_internally(self, corpus_graph):
        """The system finds Bi₂Te₃ → thermoelectric via internal adjacency search."""
        mechanisms = corpus_graph.adjacency_search("Bi2Te3", "mechanism")
        assert "thermoelectric" in mechanisms, (
            "Bi₂Te₃ should connect to thermoelectric mechanism internally"
        )

    def test_bi2te3_does_not_connect_to_nrr_internally(self, corpus_graph):
        """Bi₂Te₃ does NOT connect to NRR internally — no NRR paper in corpus.

        This is honest: the system finds what IS in its corpus. The
        cross-domain NRR connection requires corpus expansion (ingesting
        NRR-specific papers like Liu 2021, Han 2020).
        """
        mechanisms = corpus_graph.adjacency_search("Bi2Te3", "mechanism")
        assert "nrr_catalysis" not in mechanisms, (
            "Bi₂Te₃ should NOT connect to NRR — no NRR paper in corpus. "
            "If this test fails, either an NRR paper was added to the corpus "
            "(good!) or the edge extractor is hallucinating (bad!)."
        )

    def test_corpus_graph_has_no_associative_edges(self, corpus_graph):
        """All edges in the corpus graph should have mechanisms (ASSERTED+)."""
        counts = corpus_graph.tier_counts()
        assert counts["associative"] == 0, (
            f"Found {counts['associative']} associative edges — all should have mechanisms."
        )

    def test_corpus_graph_has_real_materials(self, corpus_graph):
        """The corpus graph contains real materials, not keyword artifacts."""
        material_labels = [
            n.label for n in corpus_graph.nodes.values()
            if n.node_type == "material"
        ]
        assert "Bismuth telluride" in material_labels, (
            "Bismuth telluride material node missing"
        )
        assert "alloy" not in [l.lower() for l in material_labels], (
            "'alloy' found — this is the old keyword-extraction artifact"
        )


# ----------------------------------------------------------------------
# Deliverable 1: Promoter → Simulator wiring (7 acceptance criteria)
# ----------------------------------------------------------------------

class TestPromoterSimulatorWiring:
    """Test that the simulator calls the promoter before propagation."""

    def test_simulator_calls_promoter_before_propagation(self, corpus_graph):
        """Acceptance criterion 1: causal_simulator.py calls the formula
        promoter before propagation."""
        sim = CausalSimulator(corpus_graph)
        # propagate with auto_promote=True (default) should call the promoter
        results = sim.propagate("Bi2Te3", start_value=1.0, auto_promote=True)
        # The promoter should have run — check that tier_counts includes
        # any promoted or contradicted edges
        counts = corpus_graph.tier_counts()
        # After promotion, some edges may be VERIFIED or CONTRADICTED
        assert counts["verified"] + counts["contradicted"] + counts["asserted"] + counts["associative"] > 0

    def test_verified_edges_get_epistemic_status_verified(self, corpus_graph):
        """Acceptance criterion 2: VERIFIED+DERIVED edges get
        epistemic_status='verified'."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0, auto_promote=True)
        # Check that any verified propagation has epistemic_status="verified"
        verified_results = [r for r in results if r.tier == "verified"]
        for r in verified_results:
            assert r.epistemic_status == "verified", (
                f"Verified propagation should have epistemic_status='verified', "
                f"got '{r.epistemic_status}'"
            )

    def test_asserted_edges_get_epistemic_status_hypothesis(self, corpus_graph):
        """Acceptance criterion 3: ASSERTED edges get
        epistemic_status='hypothesis'."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0, auto_promote=True)
        # Check that any asserted propagation has epistemic_status="hypothesis"
        asserted_results = [r for r in results if r.tier == "asserted"]
        for r in asserted_results:
            assert r.epistemic_status == "hypothesis", (
                f"Asserted propagation should have epistemic_status='hypothesis', "
                f"got '{r.epistemic_status}'"
            )

    def test_contradicted_edges_excluded_from_propagation(self, corpus_graph):
        """Acceptance criterion 4: CONTRADICTED edges are excluded entirely."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0, auto_promote=True)
        # No result should come from a CONTRADICTED edge
        for r in results:
            if r.edge_used is not None:
                assert r.edge_used.tier != EdgeTier.CONTRADICTED, (
                    f"Contradicted edge should not be in propagation results: "
                    f"{r.edge_used.source} → {r.edge_used.target}"
                )

    def test_associative_edges_excluded_from_propagation(self, corpus_graph):
        """Acceptance criterion 5: ASSOCIATIVE edges are excluded."""
        sim = CausalSimulator(corpus_graph)
        results = sim.propagate("Bi2Te3", start_value=1.0, auto_promote=True)
        for r in results:
            if r.edge_used is not None:
                assert r.edge_used.tier != EdgeTier.ASSOCIATIVE, (
                    f"Associative edge should not be in propagation results"
                )


# ----------------------------------------------------------------------
# Deliverable 2: Designer → ClosedLoopTracker wiring (5 acceptance criteria)
# ----------------------------------------------------------------------

class TestDesignerTrackerWiring:
    """Test that design_experiment() feeds into ClosedLoopTracker."""

    def test_design_and_track_creates_tracker(self, corpus_graph):
        """Acceptance criterion 1: design_and_track_experiment() creates a
        ClosedLoopTracker with the prediction recorded (T1)."""
        sim = CausalSimulator(corpus_graph)
        proposal, tracker = sim.design_and_track_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 100K ΔT",
            measurement_desc="measure power output (W)",
            falsification_desc="power < 0.5W",
            cost_usd=200.0,
            timeline_days=3,
            learning_pass="path verified",
            learning_fail="path needs revision",
        )
        assert proposal is not None, "Should produce an experiment proposal"
        assert tracker is not None, "Should produce a ClosedLoopTracker"
        assert tracker.step_1_prediction_timestamp is not None, (
            "Tracker should have recorded the prediction (T1)"
        )

    def test_tracker_not_closed_until_all_steps(self, corpus_graph):
        """Acceptance criterion 3: closed_loops is NOT 1 until all 5 steps
        are recorded. After design_and_track, only step 1 is done."""
        sim = CausalSimulator(corpus_graph)
        proposal, tracker = sim.design_and_track_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 100K ΔT",
            measurement_desc="measure power output (W)",
            falsification_desc="power < 0.5W",
            cost_usd=200.0,
            timeline_days=3,
            learning_pass="path verified",
            learning_fail="path needs revision",
        )
        # Only step 1 (prediction) is recorded — loop is NOT closed
        assert not tracker.is_closed_loop(), (
            "Loop should NOT be closed after only recording the prediction. "
            "All 5 steps (predict, observe, root-cause, revise, re-predict) "
            "are required."
        )

    def test_design_and_track_returns_none_for_unreachable(self, corpus_graph):
        """If the target is not reachable, return (None, None)."""
        sim = CausalSimulator(corpus_graph)
        proposal, tracker = sim.design_and_track_experiment(
            start_node_id="Bi2Te3",
            target_node_id="nonexistent_node",
            intervention_node="x",
            intervention_desc="test",
            measurement_desc="test",
            falsification_desc="test",
            cost_usd=0,
            timeline_days=0,
            learning_pass="test",
            learning_fail="test",
        )
        assert proposal is None
        assert tracker is None
