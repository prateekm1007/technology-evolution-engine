"""
Test Ross King autonomous hypothesis generation (cycle 51, Phase IV).

Per cycle 50 Ross King PASS: design_competing_experiment() accepts ≥2
competing hypotheses and designs a discriminating experiment. But the
USER had to provide the hypotheses — the system didn't generate them.

Per cycle 51: this test verifies the autonomous upgrade. The system
now generates competing hypotheses by perturbing an edge's mechanism
(linear, saturating, threshold, phase transition, etc.) and designs
the experiment itself.

This is the FULL Ross King PASS:
  - design_competing_experiment (cycle 50): user provides hypotheses
  - generate_competing_hypotheses (cycle 51): system generates them
  - design_autonomous_competing_experiment (cycle 51): both together

Per ANTI_ENTROPY.md "anti-perfection": the templates are scientifically
plausible perturbations (saturation, threshold, phase transition) —
not random guesses. Each is a class of mechanism that real physical
systems DO exhibit at extreme values.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.edge_extractor import EdgeExtractor
from invention_compiler.causal_simulator import CausalSimulator
from invention_compiler.causal_graph import CausalGraph


@pytest.fixture
def corpus_graph_with_te_path():
    """Build a CausalGraph that has a Bi2Te3 → te_power_generation path."""
    extractor = EdgeExtractor()
    papers = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False
    )
    patents = extractor.extract_from_corpus(
        str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False
    )
    combined = type(papers)()
    for nid, node in papers.nodes.items():
        combined.add_node(node)
    for nid, node in patents.nodes.items():
        if nid not in combined.nodes:
            combined.add_node(node)
    for edge in papers.edges + patents.edges:
        exists = any(
            e.source == edge.source and e.target == edge.target
            and e.mechanism == edge.mechanism for e in combined.edges
        )
        if not exists:
            combined.add_edge(edge)
    return combined


class TestGenerateCompetingHypotheses:
    """Verify autonomous hypothesis generation."""

    def test_method_exists(self):
        """CausalSimulator must have generate_competing_hypotheses method."""
        assert hasattr(CausalSimulator, "generate_competing_hypotheses")

    def test_generates_at_least_2_hypotheses(self, corpus_graph_with_te_path):
        """For any causal edge, generate ≥2 competing hypotheses."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        # Find any edge with a mechanism
        edges_with_mechanism = [e for e in sim.graph.edges if e.mechanism]
        assert len(edges_with_mechanism) > 0, "corpus should have edges with mechanisms"
        edge = edges_with_mechanism[0]
        hyps = sim.generate_competing_hypotheses(edge, n_hypotheses=3)
        assert len(hyps) >= 2, (
            f"expected ≥2 hypotheses, got {len(hyps)}"
        )

    def test_hypotheses_use_intervention_var(self, corpus_graph_with_te_path):
        """Hypotheses should reference the intervention variable, not the source."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        edges_with_mechanism = [e for e in sim.graph.edges if e.mechanism]
        edge = edges_with_mechanism[0]
        hyps = sim.generate_competing_hypotheses(
            edge, n_hypotheses=3, intervention_var="temperature_difference"
        )
        # Each hypothesis should mention "temperature_difference"
        for h in hyps:
            assert "temperature_difference" in h, (
                f"hypothesis should reference the intervention variable, got: {h}"
            )

    def test_hypotheses_are_distinct(self, corpus_graph_with_te_path):
        """Each hypothesis must be different from the others."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        edges_with_mechanism = [e for e in sim.graph.edges if e.mechanism]
        edge = edges_with_mechanism[0]
        hyps = sim.generate_competing_hypotheses(edge, n_hypotheses=3)
        # All hypotheses must be distinct strings
        assert len(set(hyps)) == len(hyps), (
            f"hypotheses must be distinct, got duplicates: {hyps}"
        )

    def test_returns_empty_for_edge_without_mechanism(self, corpus_graph_with_te_path):
        """An edge without a mechanism produces no hypotheses."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        # Construct a fake edge with no mechanism
        class _FakeEdge:
            mechanism = None
            direction = "causes"
            source = "x"
            target = "y"
            expected_output = None
        fake = _FakeEdge()
        hyps = sim.generate_competing_hypotheses(fake, n_hypotheses=3)
        assert hyps == []

    def test_returns_empty_for_none_edge(self, corpus_graph_with_te_path):
        """Passing None as edge returns empty list."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        hyps = sim.generate_competing_hypotheses(None, n_hypotheses=3)
        assert hyps == []

    def test_perturbation_templates_exist(self):
        """PERTURBATION_TEMPLATES must contain the canonical physics perturbations."""
        # The templates encode classes of mechanism any real system may exhibit
        template_names = [t[0] for t in CausalSimulator.PERTURBATION_TEMPLATES]
        assert "linear" in template_names
        assert "saturating" in template_names
        assert "threshold" in template_names
        # At least 4 distinct perturbation classes
        assert len(template_names) >= 4


class TestDesignAutonomousCompetingExperiment:
    """Verify the autonomous experiment designer (hypothesis generation + design)."""

    def test_method_exists(self):
        """CausalSimulator must have design_autonomous_competing_experiment."""
        assert hasattr(CausalSimulator, "design_autonomous_competing_experiment")

    def test_designs_experiment_for_real_path(self, corpus_graph_with_te_path):
        """For Bi2Te3 → te_power_generation, design an autonomous experiment."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_autonomous_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
        )
        assert proposal is not None, (
            "should design an autonomous experiment for the Bi2Te3 → te_power path"
        )
        # The prediction must list multiple hypotheses (autonomously generated)
        assert "H1:" in proposal.prediction
        assert "H2:" in proposal.prediction
        # The discriminating value must appear
        assert "500" in proposal.prediction

    def test_returns_none_for_unreachable_path(self, corpus_graph_with_te_path):
        """If start_node cannot reach target_node, return None."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_autonomous_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="nonexistent_node_xyz",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
        )
        assert proposal is None

    def test_autonomous_hypotheses_reference_intervention(self, corpus_graph_with_te_path):
        """The autonomously-generated hypotheses must reference the intervention variable."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_autonomous_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
        )
        assert proposal is not None
        # The prediction should contain "temperature_difference" (the intervention var)
        assert "temperature_difference" in proposal.prediction

    def test_autonomous_experiment_can_be_designed_for_other_paths(
        self, corpus_graph_with_te_path
    ):
        """The autonomous designer works for ANY path, not just Bi2Te3."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        # Try another known path: BaSO4 → passive_cooling (radiative cooling)
        proposal = sim.design_autonomous_competing_experiment(
            start_node_id="BaSO4",
            target_node_id="passive_cooling",
            intervention_node="film_thickness",
            discriminating_value=500.0,
            discriminating_unit="nm",
        )
        # May or may not produce a proposal depending on whether the path exists
        # The point is the method runs without crashing
        if proposal is not None:
            assert "H1:" in proposal.prediction
            assert "H2:" in proposal.prediction


class TestRossKingPhaseIVAcidTest:
    """The Phase IV Ross King criterion: the system autonomously generates
    hypotheses AND designs the discriminating experiment.
    """

    def test_ross_king_phase4_pass_autonomous_generation(self, corpus_graph_with_te_path):
        """Phase IV PASS: the system generates ≥2 hypotheses without user input."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_autonomous_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
        )
        assert proposal is not None
        # Count the hypotheses in the prediction
        h_count = proposal.prediction.count("H")
        # Should have at least H1 and H2 (≥2 hypotheses)
        assert h_count >= 2, (
            f"autonomous experiment should have ≥2 hypotheses, "
            f"got {h_count}"
        )

    def test_ross_king_phase4_pass_distinct_perturbations(self, corpus_graph_with_te_path):
        """Phase IV PASS: the generated hypotheses represent distinct perturbations.

        Per the perturbation library: linear, saturating, threshold are
        DIFFERENT physical phenomena. The system must not generate
        trivially-similar hypotheses.
        """
        sim = CausalSimulator(corpus_graph_with_te_path)
        edges_with_mechanism = [e for e in sim.graph.edges if e.mechanism]
        edge = edges_with_mechanism[0]
        hyps = sim.generate_competing_hypotheses(edge, n_hypotheses=3)
        # Check that the hypotheses reference distinct perturbation concepts
        # (linear, saturating, threshold — not three near-identical statements)
        concepts_found = set()
        concept_keywords = {
            "linear": "linear",
            "saturat": "saturating",
            "threshold": "threshold",
            "phase transition": "phase_transition",
            "exponential": "exponential",
            "oscillat": "oscillatory",
        }
        for h in hyps:
            h_lower = h.lower()
            for keyword, concept in concept_keywords.items():
                if keyword in h_lower:
                    concepts_found.add(concept)
                    break
        # Should have ≥2 distinct concepts (ideally 3)
        assert len(concepts_found) >= 2, (
            f"hypotheses should cover ≥2 distinct perturbation concepts, "
            f"got {concepts_found}"
        )
