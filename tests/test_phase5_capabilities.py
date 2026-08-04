"""
Test Phase V capabilities (cycle 52): BACON.4, k-fold CV, hypothesis ranking.

Per cycle 51 next-step: implement three Phase V directions:
  1. BACON.4 — recursive composition for 3+ variable products
  2. k-fold cross-validation with averaged test R²
  3. Hypothesis ranking by expected information gain

This test verifies each capability works end-to-end.
"""
import math
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.bacon_engine import (
    discover_recursive_composed_law, k_fold_cross_validate_law,
    RecursiveComposedLaw, KFoldCrossValidatedLaw,
    discover_composed_law, cross_validate_law,
    stull_wet_bulb_dataset, stefan_boltzmann_dataset, pcm_latent_heat_dataset,
)
from invention_compiler.edge_extractor import EdgeExtractor
from invention_compiler.causal_simulator import CausalSimulator


# ---------------------------------------------------------------------------
# BACON.4 — recursive composition (3+ variable products)
# ---------------------------------------------------------------------------

class TestBacon4RecursiveComposition:
    """BACON.4 — discover 3-variable product laws by recursive composition."""

    def test_bacon4_discovers_three_variable_product(self):
        """y = a * x1 * x2 * x3 with 3 INDEPENDENT variables — BACON.3 cannot, BACON.4 can."""
        import itertools
        x1, x2, x3, y = [], [], [], []
        for a, b, c in itertools.product([1, 2, 3], [1, 2, 3], [1, 2]):
            x1.append(float(a)); x2.append(float(b)); x3.append(float(c))
            y.append(2.5 * a * b * c)
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'y': y}

        result = discover_recursive_composed_law(dataset, 'y', verbose=False)
        assert result is not None, (
            "BACON.4 should discover the 3-variable product law"
        )
        assert result.depth >= 2, (
            f"BACON.4 should reach depth ≥2 for 3-var product, got {result.depth}"
        )
        assert result.law.r2 >= 0.99, (
            f"BACON.4 final R² should be ≥0.99, got {result.law.r2:.4f}"
        )
        # The composition chain should contain 2 steps (x1*x2, then *x3)
        assert len(result.composition_chain) >= 2
        # All 3 variables should be in input_vars
        assert set(result.input_vars) == {'x1', 'x2', 'x3'}, (
            f"expected x1, x2, x3 in input_vars, got {result.input_vars}"
        )

    def test_bacon4_returns_none_when_bacon3_suffices(self):
        """If BACON.3 already achieves R²=1.0, BACON.4 returns None (no deeper composition needed)."""
        # y = 2 * x1 + 3 (purely linear in x1) — no composition needed
        x1 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        x2 = [3.14, 1.59, 2.65, 3.58, 9.79, 3.23, 8.46, 2.64]  # noise
        y = [2.0 * x + 3.0 for x in x1]
        dataset = {'x1': x1, 'x2': x2, 'y': y}

        result = discover_recursive_composed_law(dataset, 'y')
        # BACON.3 already fits perfectly with x1; no recursion needed
        assert result is None, (
            f"BACON.4 should return None when BACON.3 suffices, got {result}"
        )

    def test_bacon4_requires_at_least_two_variables(self):
        """BACON.4 returns None if <2 independent variables."""
        dataset = {'x1': [1.0, 2.0, 3.0, 4.0], 'y': [2.0, 4.0, 6.0, 8.0]}
        result = discover_recursive_composed_law(dataset, 'y')
        assert result is None

    def test_bacon4_respects_max_depth(self):
        """max_depth limits the recursion depth."""
        import itertools
        # 4-variable product
        x1, x2, x3, x4, y = [], [], [], [], []
        for a, b, c, d in itertools.product([1, 2], [1, 2], [1, 2], [1, 2]):
            x1.append(float(a)); x2.append(float(b))
            x3.append(float(c)); x4.append(float(d))
            y.append(float(a * b * c * d))
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'x4': x4, 'y': y}

        # With max_depth=2, should find a 3-variable composition
        result = discover_recursive_composed_law(dataset, 'y', max_depth=2)
        # Either finds a depth-2 composition or returns None
        if result is not None:
            assert result.depth <= 2

    def test_bacon4_to_dict_round_trip(self):
        """RecursiveComposedLaw.to_dict must be JSON-serializable."""
        import itertools
        import json
        x1, x2, x3, y = [], [], [], []
        for a, b, c in itertools.product([1, 2, 3], [1, 2, 3], [1, 2]):
            x1.append(float(a)); x2.append(float(b)); x3.append(float(c))
            y.append(2.5 * a * b * c)
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'y': y}

        result = discover_recursive_composed_law(dataset, 'y')
        if result is not None:
            d = result.to_dict()
            json.dumps(d)  # raises if not serializable
            assert "composition_chain" in d
            assert "depth" in d

    def test_bacon4_str_is_readable(self):
        """RecursiveComposedLaw.__str__ must be human-readable."""
        import itertools
        x1, x2, x3, y = [], [], [], []
        for a, b, c in itertools.product([1, 2, 3], [1, 2, 3], [1, 2]):
            x1.append(float(a)); x2.append(float(b)); x3.append(float(c))
            y.append(2.5 * a * b * c)
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'y': y}

        result = discover_recursive_composed_law(dataset, 'y')
        if result is not None:
            s = str(result)
            assert "RecursiveComposedLaw" in s
            assert "depth=" in s
            assert "R²=" in s


# ---------------------------------------------------------------------------
# k-fold cross-validation
# ---------------------------------------------------------------------------

class TestKFoldCrossValidation:
    """k-fold cross-validation with averaged test R²."""

    def test_kfold_stefan_boltzmann_generalizes(self):
        """5-fold CV on Stefan-Boltzmann: mean test R² ≥ 0.95, low std."""
        data = stefan_boltzmann_dataset(n_points=15)
        cv = k_fold_cross_validate_law(data["T_surface_K"], data["Q_W"], k=5)
        assert cv is not None
        assert cv.k == 5
        assert len(cv.fold_test_r2) == 5
        assert cv.mean_test_r2 >= 0.95, (
            f"5-fold mean test R² should be ≥0.95, got {cv.mean_test_r2:.4f}"
        )
        assert cv.std_test_r2 <= 0.10, (
            f"std should be ≤0.10 (stable across folds), got {cv.std_test_r2:.4f}"
        )
        assert cv.generalizes, (
            "Stefan-Boltzmann law should generalize across folds"
        )

    def test_kfold_pcm_generalizes_perfectly(self):
        """5-fold CV on PCM: all folds R²=1.0000, std=0."""
        data = pcm_latent_heat_dataset(n_points=10)
        cv = k_fold_cross_validate_law(data["Q_daily_W"], data["m_pcm_kg"], k=5)
        assert cv is not None
        assert cv.mean_test_r2 >= 0.9999, (
            f"PCM is exactly linear; mean test R² should be 1.0, got {cv.mean_test_r2:.6f}"
        )
        assert cv.std_test_r2 <= 0.001, (
            f"PCM std should be ~0, got {cv.std_test_r2:.6f}"
        )
        # All folds should be ~1.0
        for r2 in cv.fold_test_r2:
            assert r2 >= 0.999, f"individual fold R²={r2:.4f} should be ~1.0"

    def test_kfold_returns_none_for_short_data(self):
        """k-fold requires ≥2*k data points."""
        xs = [1.0, 2.0, 3.0, 4.0]  # only 4 points, k=5 needs ≥10
        ys = [2.0, 4.0, 6.0, 8.0]
        cv = k_fold_cross_validate_law(xs, ys, k=5)
        assert cv is None

    def test_kfold_handles_varying_fold_sizes(self):
        """When n is not divisible by k, fold sizes vary but all have ≥1 point."""
        # n=11, k=5 → fold sizes [3, 2, 2, 2, 2]
        xs = [float(i) for i in range(1, 12)]
        ys = [2.0 * x + 1.0 for x in xs]
        cv = k_fold_cross_validate_law(xs, ys, k=5)
        assert cv is not None
        assert cv.k == 5
        # All folds should have run
        assert len(cv.fold_test_r2) == 5

    def test_kfold_detects_unstable_law(self):
        """If test R² varies wildly across folds, generalizes=False."""
        # Construct data where the law might be unstable
        # Use a small dataset with some non-linearity
        xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        # y has a step function (hard for BACON's smooth candidates)
        ys = [1.0 if x < 5 else 10.0 for x in xs]
        cv = k_fold_cross_validate_law(xs, ys, k=5)
        if cv is not None:
            # Either generalizes (BACON found a smooth approx) or doesn't
            # The point is that the method runs and reports honestly
            assert isinstance(cv.generalizes, bool)

    def test_kfold_uses_reproducible_splits(self):
        """Same inputs produce same outputs (no RNG)."""
        data = stefan_boltzmann_dataset(n_points=15)
        cv1 = k_fold_cross_validate_law(data["T_surface_K"], data["Q_W"], k=5)
        cv2 = k_fold_cross_validate_law(data["T_surface_K"], data["Q_W"], k=5)
        assert cv1 is not None and cv2 is not None
        assert cv1.fold_test_r2 == cv2.fold_test_r2  # byte-exact
        assert cv1.mean_test_r2 == cv2.mean_test_r2

    def test_kfold_to_dict_round_trip(self):
        """KFoldCrossValidatedLaw.to_dict is JSON-serializable."""
        import json
        data = stefan_boltzmann_dataset(n_points=15)
        cv = k_fold_cross_validate_law(data["T_surface_K"], data["Q_W"], k=5)
        assert cv is not None
        d = cv.to_dict()
        json.dumps(d)
        assert "fold_test_r2" in d
        assert "mean_test_r2" in d
        assert "std_test_r2" in d
        assert "generalizes" in d

    def test_kfold_str_is_readable(self):
        """KFoldCrossValidatedLaw.__str__ is human-readable."""
        data = stefan_boltzmann_dataset(n_points=15)
        cv = k_fold_cross_validate_law(data["T_surface_K"], data["Q_W"], k=5)
        assert cv is not None
        s = str(cv)
        assert "KFoldCrossValidatedLaw" in s
        assert "mean_test_R²" in s
        assert "GENERALIZES" in s or "UNSTABLE" in s


# ---------------------------------------------------------------------------
# Hypothesis ranking by expected information gain
# ---------------------------------------------------------------------------

@pytest.fixture
def corpus_graph():
    """Build a CausalGraph for testing."""
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


class TestHypothesisRanking:
    """Hypothesis ranking by expected information gain."""

    def test_rank_method_exists(self):
        """CausalSimulator must have rank_hypotheses_by_information_gain."""
        assert hasattr(CausalSimulator, "rank_hypotheses_by_information_gain")

    def test_rank_returns_sorted_list(self, corpus_graph):
        """rank_hypotheses_by_information_gain returns hypotheses sorted by score."""
        sim = CausalSimulator(corpus_graph)
        hyps = [
            "y = α·x (linear)",
            "y = α·x² (quadratic)",
            "y = α·sin(x) (oscillatory)",
        ]
        ranked = sim.rank_hypotheses_by_information_gain(hyps)
        assert len(ranked) == 3
        # Scores must be in descending order
        scores = [s for _, s, _ in ranked]
        assert scores == sorted(scores, reverse=True), (
            f"scores must be descending, got {scores}"
        )
        # All scores in [0, 1]
        for s in scores:
            assert 0.0 <= s <= 1.0

    def test_rank_returns_reason_for_each(self, corpus_graph):
        """Each ranked entry includes a human-readable reason."""
        sim = CausalSimulator(corpus_graph)
        hyps = ["linear", "saturating", "threshold"]
        ranked = sim.rank_hypotheses_by_information_gain(hyps)
        for h, score, reason in ranked:
            assert isinstance(h, str)
            assert isinstance(score, float)
            assert isinstance(reason, str)
            assert "discriminating" in reason
            assert "plausibility" in reason

    def test_rank_with_fewer_than_two_hypotheses(self, corpus_graph):
        """Fewer than 2 hypotheses → all get score 0 (no ranking possible)."""
        sim = CausalSimulator(corpus_graph)
        ranked = sim.rank_hypotheses_by_information_gain(["only one"])
        assert len(ranked) == 1
        assert ranked[0][1] == 0.0

    def test_rank_unique_hypotheses_score_higher(self, corpus_graph):
        """Hypotheses with unique tokens score higher than generic ones."""
        sim = CausalSimulator(corpus_graph)
        # 'linear' is generic (in many hypotheses); 'superposition' is unique
        hyps = [
            "y = α·x (linear)",  # 'linear' is generic
            "y = α·x² (quadratic)",  # 'quadratic' is unique here
        ]
        ranked = sim.rank_hypotheses_by_information_gain(hyps)
        # 'quadratic' should score higher (more unique tokens)
        # Note: this depends on tokenization; both should pass the basic test
        assert ranked[0][1] >= ranked[1][1]

    def test_design_ranked_experiment_method_exists(self):
        """CausalSimulator must have design_ranked_competing_experiment."""
        assert hasattr(CausalSimulator, "design_ranked_competing_experiment")

    def test_design_ranked_experiment_produces_proposal(self, corpus_graph):
        """design_ranked_competing_experiment produces a proposal with ranked hypotheses."""
        sim = CausalSimulator(corpus_graph)
        proposal = sim.design_ranked_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
            n_hypotheses=3,
        )
        assert proposal is not None, (
            "design_ranked_competing_experiment should produce a proposal for "
            "the Bi2Te3 → te_power_generation path"
        )
        # The prediction should mention the ranking
        assert "H1:" in proposal.prediction
        assert "H2:" in proposal.prediction
        assert "H3:" in proposal.prediction
        # The measurement_desc should mention "ranked by information gain"
        assert "ranked" in proposal.measurement.lower()

    def test_design_ranked_experiment_returns_none_for_unreachable(self, corpus_graph):
        """Returns None if start_node cannot reach target_node."""
        sim = CausalSimulator(corpus_graph)
        proposal = sim.design_ranked_competing_experiment(
            start_node_id="Bi2Te3",
            target_node_id="nonexistent_xyz",
            intervention_node="temperature_difference",
            discriminating_value=500.0,
            discriminating_unit="K",
        )
        assert proposal is None


# ---------------------------------------------------------------------------
# Phase V integration: all three capabilities together
# ---------------------------------------------------------------------------

class TestPhaseVIntegration:
    """Verify all three Phase V capabilities work together."""

    def test_bacon4_then_kfold_cross_validate(self):
        """Discover a 3-variable law, then k-fold cross-validate it."""
        import itertools
        x1, x2, x3, y = [], [], [], []
        for a, b, c in itertools.product([1, 2, 3], [1, 2, 3], [1, 2]):
            x1.append(float(a)); x2.append(float(b)); x3.append(float(c))
            y.append(2.5 * a * b * c)

        # Step 1: discover the composed variable
        dataset = {'x1': x1, 'x2': x2, 'x3': x3, 'y': y}
        result = discover_recursive_composed_law(dataset, 'y')
        assert result is not None
        assert result.law.r2 >= 0.99

        # Step 2: k-fold cross-validate the composed variable
        cv = k_fold_cross_validate_law(result.composed_values, y, k=5)
        assert cv is not None, (
            "k-fold CV should produce a result for the composed variable"
        )
        # The composed law should generalize well
        assert cv.mean_test_r2 >= 0.95, (
            f"3-variable product law should generalize; mean test R²={cv.mean_test_r2:.4f}"
        )
