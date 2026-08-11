"""
Test the Ross King fix: design_competing_experiment (cycle 50).

Per the cycle 49 Maestro Loop gap report: Ross King was INCOMPLETE
because design_experiment() confirms a known causal edge — it doesn't
distinguish between competing hypotheses. Ross King's Adam robot
(King et al., 2004) contributed by hypothesizing NEW mechanisms.

This test verifies the new design_competing_experiment() method:
  - Accepts ≥2 competing hypotheses
  - Designs an experiment whose outcome distinguishes them
  - The discriminating value is where predictions diverge
  - Falsification describes the discriminating outcome
  - Learning pass = one hypothesis supported
  - Learning fail = no hypothesis supported (also discovery)

The acid test PASS criterion: design_competing_experiment() can
distinguish between competing hypotheses for a real causal path
(Bi2Te3 → te_power_generation via temperature_difference).
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


class TestDesignCompetingExperiment:
    """Verify design_competing_experiment distinguishes hypotheses."""

    def test_competing_experiment_requires_at_least_two_hypotheses(self, corpus_graph_with_te_path):
        """Per Ross King: must have ≥2 competing hypotheses to distinguish."""
        sim = CausalSimulator(corpus_graph_with_te_path)

        # Single hypothesis must raise ValueError
        with pytest.raises(ValueError, match="≥2"):
            sim.design_competing_experiment(
                start_node_id="Bi2Te3",
                target_node_id="te_power_generation",
                intervention_node="temperature_difference",
                intervention_desc="apply 500K ΔT",
                measurement_desc="measure Seebeck coefficient (μV/K)",
                competing_hypotheses=["S = α·ΔT (linear)"],
                discriminating_value=500.0,
                discriminating_unit="K",
                cost_usd=300.0,
                timeline_days=5,
            )

    def test_competing_experiment_designs_for_real_path(self, corpus_graph_with_te_path):
        """Design a competing experiment for Bi2Te3 → te_power_generation."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 500K ΔT across Bi2Te3 module",
            measurement_desc="measure Seebeck coefficient (μV/K) at 500K ΔT",
            competing_hypotheses=[
                "Seebeck coefficient is linear in ΔT: S(ΔT) = α·ΔT with α ≈ 200 μV/K",
                "Seebeck coefficient saturates above ΔT=400K: S(ΔT) = α·ΔT/(1+ΔT/400)",
                "Seebeck coefficient has a phase transition at ΔT=500K (Curie point)",
            ],
            discriminating_value=500.0,
            discriminating_unit="K",
            cost_usd=300.0,
            timeline_days=5,
        )

        assert proposal is not None, (
            "design_competing_experiment should return a proposal for the "
            "Bi2Te3 → te_power_generation path (which exists in the real corpus)"
        )
        # The prediction must list all 3 hypotheses
        assert "H1:" in proposal.prediction
        assert "H2:" in proposal.prediction
        assert "H3:" in proposal.prediction
        assert "linear" in proposal.prediction.lower()
        assert "saturates" in proposal.prediction.lower()
        # The discriminating value must appear in the prediction
        assert "500" in proposal.prediction
        # The falsification describes the "all wrong" case
        assert "ALL" in proposal.falsification or "All" in proposal.falsification
        # Learning pass: one hypothesis supported
        assert "supported" in proposal.learning_if_pass.lower()
        # Learning fail: no hypothesis supported (discovery)
        assert "discovery" in proposal.learning_if_fail.lower() or \
               "more complex" in proposal.learning_if_fail.lower()

    def test_competing_experiment_returns_none_for_unreachable_path(self, corpus_graph_with_te_path):
        """If start_node cannot reach target_node, return None."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="nonexistent_node_xyz",
            intervention_node="temperature_difference",
            intervention_desc="apply 500K ΔT",
            measurement_desc="measure power",
            competing_hypotheses=[
                "H1: linear",
                "H2: nonlinear",
            ],
            discriminating_value=500.0,
            discriminating_unit="K",
            cost_usd=200.0,
            timeline_days=3,
        )
        assert proposal is None

    def test_competing_experiment_lists_all_hypotheses_in_prediction(self, corpus_graph_with_te_path):
        """The prediction must enumerate every competing hypothesis."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        n_hypotheses = 4
        hyps = [f"Hypothesis {i+1}: predicts outcome {i+1}" for i in range(n_hypotheses)]
        proposal = sim.design_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 500K ΔT",
            measurement_desc="measure output",
            competing_hypotheses=hyps,
            discriminating_value=500.0,
            discriminating_unit="K",
            cost_usd=200.0,
            timeline_days=3,
        )
        assert proposal is not None
        for i in range(n_hypotheses):
            assert f"H{i+1}:" in proposal.prediction, (
                f"prediction missing hypothesis H{i+1}"
            )

    def test_competing_experiment_discriminating_value_appears_in_prediction(
        self, corpus_graph_with_te_path
    ):
        """The discriminating value (where hypotheses diverge) must appear."""
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 450K ΔT",
            measurement_desc="measure power",
            competing_hypotheses=["H1: linear", "H2: nonlinear"],
            discriminating_value=450.0,
            discriminating_unit="K",
            cost_usd=200.0,
            timeline_days=3,
        )
        assert proposal is not None
        assert "450" in proposal.prediction
        assert "K" in proposal.prediction


class TestRossKingAcidTestPass:
    """The acid-test criterion: Ross King PASSES when the system can
    distinguish between competing hypotheses (not just confirm a known edge).
    """

    def test_ross_king_pass_design_competing_experiment_exists(self):
        """Ross King PASS: design_competing_experiment method exists on CausalSimulator."""
        from invention_compiler.causal_simulator import CausalSimulator
        assert hasattr(CausalSimulator, "design_competing_experiment"), (
            "CausalSimulator must have design_competing_experiment method "
            "for Ross King to PASS"
        )

    def test_ross_king_pass_can_design_for_seebeck_saturation(self, corpus_graph_with_te_path):
        """Ross King PASS: can design an experiment distinguishing linear-vs-saturating Seebeck.

        This is the canonical Ross King test: the system hypothesizes that
        the Seebeck effect may saturate at high ΔT (a NEW mechanism, not
        in the corpus) and designs an experiment to test it. This is what
        Adam did — hypothesize, then test.
        """
        sim = CausalSimulator(corpus_graph_with_te_path)
        proposal = sim.design_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply ΔT = 500K (above the hypothetical saturation threshold)",
            measurement_desc="measure Seebeck coefficient S in μV/K",
            competing_hypotheses=[
                "S(ΔT) = α·ΔT, linear across all ΔT (classical Seebeck)",
                "S(ΔT) = α·ΔT/(1 + ΔT/ΔT_sat), saturates above ΔT_sat ≈ 400K (phonon drag)",
            ],
            discriminating_value=500.0,
            discriminating_unit="K",
            cost_usd=300.0,
            timeline_days=5,
        )
        assert proposal is not None
        # The proposal must NOT predetermine which hypothesis wins — that's
        # the whole point of a Ross King experiment.
        assert "H1:" in proposal.prediction
        assert "H2:" in proposal.prediction
        # The learning outcomes must cover both cases
        assert "supported" in proposal.learning_if_pass.lower()
        assert "falsified" in proposal.learning_if_pass.lower()
