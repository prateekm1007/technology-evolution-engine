"""Tests for active_learning.py — Learning 6→8."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.active_learning import (
    ExperimentDesigner,
    ActiveLearner,
    Experiment,
    ExperimentSelection,
    ExperimentOutcome,
)


def _build_test_learner():
    """Build a test learner with 3 hypotheses and 2 experiments."""
    hypotheses = [
        "h1_linear",
        "h2_arrhenius",
        "h3_phase_transition",
    ]
    designer = ExperimentDesigner(hypotheses)
    designer.add_experiment(
        "exp_low_T",
        "Measure at low T",
        pass_likelihoods=[0.3, 0.9, 0.4],
    )
    designer.add_experiment(
        "exp_high_T",
        "Measure at high T",
        pass_likelihoods=[0.7, 0.4, 0.3],
    )
    learner = ActiveLearner(designer)
    return learner, designer


def test_initial_priors_uniform():
    """Initial priors are uniform when none are provided."""
    learner, _ = _build_test_learner()
    assert len(learner.priors) == 3
    assert all(abs(p - 1.0 / 3) < 1e-9 for p in learner.priors)


def test_initial_priors_normalized():
    """Custom initial priors are normalized to sum to 1."""
    hypotheses = ["h1", "h2"]
    designer = ExperimentDesigner(hypotheses)
    designer.add_experiment("e1", "test", [0.5, 0.7])
    learner = ActiveLearner(designer, initial_priors=[2.0, 6.0])
    assert abs(sum(learner.priors) - 1.0) < 1e-9
    assert abs(learner.priors[0] - 0.25) < 1e-9
    assert abs(learner.priors[1] - 0.75) < 1e-9


def test_select_next_experiment_returns_selection():
    """select_next_experiment returns an ExperimentSelection."""
    learner, _ = _build_test_learner()
    sel = learner.select_next_experiment()
    assert sel is not None
    assert isinstance(sel, ExperimentSelection)
    assert sel.experiment_name in ("exp_low_T", "exp_high_T")
    assert sel.information_gain > 0


def test_experiment_ig_nonnegative():
    """Information gain is always non-negative (entropy can only decrease)."""
    learner, _ = _build_test_learner()
    for name, exp in learner.designer.experiments.items():
        ig, _, _ = learner.compute_experiment_ig(exp)
        assert ig >= -1e-9, f"IG for {name} is negative: {ig}"


def test_bayesian_update_increases_correct_hypothesis():
    """After running an experiment that 'passes', the hypothesis with the
    highest P(pass|h) should have its posterior increased."""
    learner, _ = _build_test_learner()
    # exp_low_T has P(pass|arrhenius)=0.9 (highest)
    old_priors = list(learner.priors)
    result = learner.run_experiment("exp_low_T", "pass")
    new_priors = result["new_priors"]

    # h2_arrhenius (index 1) had P(pass|h)=0.9, the highest
    assert new_priors[1] > old_priors[1], \
        f"Arrhenius posterior should increase: {old_priors[1]} → {new_priors[1]}"


def test_bayesian_update_decreases_wrong_hypothesis():
    """After running an experiment that 'passes', the hypothesis with the
    lowest P(pass|h) should have its posterior decreased."""
    learner, _ = _build_test_learner()
    old_priors = list(learner.priors)
    result = learner.run_experiment("exp_low_T", "pass")
    new_priors = result["new_priors"]

    # h1_linear (index 0) had P(pass|h)=0.3, the lowest
    assert new_priors[0] < old_priors[0], \
        f"Linear posterior should decrease: {old_priors[0]} → {new_priors[0]}"


def test_priors_sum_to_one_after_update():
    """Priors always sum to 1 after a Bayesian update."""
    learner, _ = _build_test_learner()
    learner.run_experiment("exp_low_T", "pass")
    assert abs(sum(learner.priors) - 1.0) < 1e-9
    learner.run_experiment("exp_high_T", "fail")
    assert abs(sum(learner.priors) - 1.0) < 1e-9


def test_convergence_detection():
    """Convergence is detected when max posterior ≥ threshold."""
    hypotheses = ["h1", "h2"]
    designer = ExperimentDesigner(hypotheses)
    # Very discriminating experiment
    designer.add_experiment("e1", "test", [0.99, 0.01])
    learner = ActiveLearner(designer, convergence_threshold=0.95)
    assert not learner.has_converged()
    learner.run_experiment("e1", "pass")
    assert learner.has_converged()


def test_select_returns_none_when_converged():
    """When priors are extreme, IG is below threshold and select returns None."""
    hypotheses = ["h1", "h2"]
    designer = ExperimentDesigner(hypotheses)
    designer.add_experiment("e1", "test", [0.5, 0.5])  # uninformative
    learner = ActiveLearner(designer, ig_threshold=0.5)
    sel = learner.select_next_experiment()
    # IG of an uninformative experiment is ~0, below 0.5 threshold
    assert sel is None


def test_best_hypothesis_after_updates():
    """best_hypothesis returns the hypothesis with the highest posterior."""
    learner, _ = _build_test_learner()
    # Run exp_low_T which favors h2_arrhenius
    learner.run_experiment("exp_low_T", "pass")
    learner.run_experiment("exp_low_T", "pass")  # twice to make it dominate
    best_h, best_p = learner.best_hypothesis()
    assert best_h == "h2_arrhenius"
    assert best_p > 0.5


def test_experiment_likelihood_functions():
    """Experiment.pass_likelihood and fail_likelihood sum to 1."""
    exp = Experiment(name="e1", description="test", pass_likelihoods=[0.3, 0.7, 0.5])
    for i in range(3):
        assert abs(exp.pass_likelihood(i) + exp.fail_likelihood(i) - 1.0) < 1e-9


def test_invalid_outcome_raises():
    """Running an experiment with an invalid outcome raises ValueError."""
    learner, _ = _build_test_learner()
    try:
        learner.run_experiment("exp_low_T", "maybe")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_invalid_experiment_name_raises():
    """Running an unknown experiment raises ValueError."""
    learner, _ = _build_test_learner()
    try:
        learner.run_experiment("nonexistent_exp", "pass")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_history_recorded():
    """Each run_experiment call records an entry in history."""
    learner, _ = _build_test_learner()
    initial_history_len = len(learner.history)
    learner.run_experiment("exp_low_T", "pass")
    assert len(learner.history) == initial_history_len + 1
    last = learner.history[-1]
    assert isinstance(last, ExperimentOutcome)
    assert last.experiment_name == "exp_low_T"
    assert last.outcome == "pass"


def test_ig_is_higher_for_discriminating_experiment():
    """A discriminating experiment has higher IG than an uninformative one."""
    hypotheses = ["h1", "h2"]
    designer = ExperimentDesigner(hypotheses)
    designer.add_experiment("discriminating", "test", [0.95, 0.05])
    designer.add_experiment("uninformative", "test", [0.5, 0.5])
    learner = ActiveLearner(designer)

    ig_d, _, _ = learner.compute_experiment_ig(designer.experiments["discriminating"])
    ig_u, _, _ = learner.compute_experiment_ig(designer.experiments["uninformative"])
    assert ig_d > ig_u, \
        f"Discriminating IG ({ig_d}) should exceed uninformative IG ({ig_u})"


def test_selection_history_recorded():
    """select_next_experiment records the selection in history."""
    learner, _ = _build_test_learner()
    initial_len = len(learner.selection_history)
    learner.select_next_experiment()
    assert len(learner.selection_history) == initial_len + 1


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
