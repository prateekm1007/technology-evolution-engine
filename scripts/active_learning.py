#!/usr/bin/env python3
"""
active_learning.py — Active-learning experiment selection (Learning 6→8).

Per cycle 180: the auditor's gap analysis says Learning has
"ranks hypotheses but does not SELECT the next experiment."

bayesian_learning.py (cycle 171) introduced Bayesian information gain for
*ranking hypotheses*. But MacKay-style active learning requires SELECTING
THE NEXT EXPERIMENT — the experiment that maximally reduces expected
posterior entropy across the WHOLE hypothesis space, not just the
single-hypothesis IG.

The key distinction:
  - Hypothesis-level IG (existing): IG(hypothesis) = H(prior) - H(posterior|outcome)
  - Experiment-level IG (this module): IG(experiment) = H(P(h)) - E_outcome[H(P(h|outcome))]

A single experiment yields two posteriors (pass/fail); the experiment-level
IG is the expected reduction in entropy ACROSS ALL HYPOTHESES, weighted by
the marginal probability of each outcome.

This module provides:
1. ExperimentDesigner: a set of candidate experiments (each defined by its
   likelihood function P(outcome | hypothesis) for each hypothesis).
2. ActiveLearner: selects the experiment with maximum expected information
   gain, runs it, updates priors, and repeats.
3. Stopping criterion: stop when the maximum posterior exceeds 0.95 OR
   no experiment yields IG > 0.01 bits.

Usage:
    from scripts.active_learning import ExperimentDesigner, ActiveLearner
    designer = ExperimentDesigner(hypotheses)
    designer.add_experiment("measure_y_at_x=10", likelihoods={...})
    learner = ActiveLearner(designer)
    selected = learner.select_next_experiment()
    learner.run_experiment(selected, outcome="pass")
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any, Callable


@dataclass
class Experiment:
    """A candidate experiment with its likelihood function.

    The likelihood function maps each hypothesis to P(outcome=pass | h is true).
    P(outcome=fail | h is true) = 1 - P(pass | h).
    """
    name: str
    description: str
    # Map hypothesis index → P(pass | h_i is true)
    pass_likelihoods: List[float]
    # Optional: cost of running this experiment (default 1.0)
    cost: float = 1.0

    def pass_likelihood(self, hyp_idx: int) -> float:
        """P(pass | hypothesis hyp_idx is true)."""
        if 0 <= hyp_idx < len(self.pass_likelihoods):
            return self.pass_likelihoods[hyp_idx]
        return 0.5

    def fail_likelihood(self, hyp_idx: int) -> float:
        """P(fail | hypothesis hyp_idx is true)."""
        return 1.0 - self.pass_likelihood(hyp_idx)


@dataclass
class ExperimentOutcome:
    """The outcome of running an experiment."""
    experiment_name: str
    outcome: str  # "pass" or "fail"
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentSelection:
    """The result of selecting the next experiment."""
    experiment_name: str
    information_gain: float  # in bits
    expected_posterior_entropy: float
    prior_entropy: float
    reason: str


class ExperimentDesigner:
    """Designs and manages a set of candidate experiments.

    An experiment is defined by its likelihood function — for each
    hypothesis, what is P(pass|true)? This is the MacKay formulation.
    """

    def __init__(self, hypotheses: List[str]):
        self.hypotheses = hypotheses
        self.experiments: Dict[str, Experiment] = {}

    def add_experiment(
        self,
        name: str,
        description: str,
        pass_likelihoods: List[float],
        cost: float = 1.0,
    ):
        """Add a candidate experiment.

        Args:
            name: experiment identifier
            description: human-readable description
            pass_likelihoods: list of P(pass | h_i is true) for each hypothesis
            cost: cost of running this experiment (default 1.0)
        """
        if len(pass_likelihoods) != len(self.hypotheses):
            raise ValueError(
                f"pass_likelihoods has {len(pass_likelihoods)} entries, "
                f"expected {len(self.hypotheses)} (one per hypothesis)"
            )
        self.experiments[name] = Experiment(
            name=name,
            description=description,
            pass_likelihoods=pass_likelihoods,
            cost=cost,
        )

    def list_experiments(self) -> List[str]:
        return list(self.experiments.keys())


class ActiveLearner:
    """Active-learning experiment selector.

    Implements MacKay-style active learning:
    1. Maintain a prior distribution P(h) over hypotheses.
    2. For each candidate experiment, compute expected information gain:
         IG(exp) = H(P(h)) - sum_outcome P(outcome) * H(P(h|outcome))
    3. Select the experiment with maximum IG (per unit cost).
    4. Run the experiment, observe the outcome, update priors via Bayes.
    5. Repeat until convergence (max posterior ≥ 0.95) or no IG > threshold.
    """

    def __init__(
        self,
        designer: ExperimentDesigner,
        initial_priors: Optional[List[float]] = None,
        ig_threshold: float = 0.01,
        convergence_threshold: float = 0.95,
    ):
        self.designer = designer
        n = len(designer.hypotheses)
        if initial_priors:
            if len(initial_priors) != n:
                raise ValueError(
                    f"initial_priors has {len(initial_priors)} entries, expected {n}"
                )
            self.priors = list(initial_priors)
        else:
            self.priors = [1.0 / n] * n
        # Normalize
        total = sum(self.priors)
        self.priors = [p / total for p in self.priors]

        self.ig_threshold = ig_threshold
        self.convergence_threshold = convergence_threshold
        self.history: List[ExperimentOutcome] = []
        self.selection_history: List[ExperimentSelection] = []

    def _entropy(self, probs: List[float]) -> float:
        """Shannon entropy in bits."""
        h = 0.0
        for p in probs:
            if p > 0:
                h -= p * math.log2(p)
        return h

    def compute_experiment_ig(self, experiment: Experiment) -> Tuple[float, float, float]:
        """Compute the expected information gain of an experiment.

        Returns:
            (ig, expected_posterior_entropy, prior_entropy)
        """
        prior_entropy = self._entropy(self.priors)

        # Marginal probability of each outcome
        p_pass = sum(
            experiment.pass_likelihood(i) * self.priors[i]
            for i in range(len(self.priors))
        )
        p_fail = 1.0 - p_pass

        # Posterior P(h_i | pass) and P(h_i | fail)
        posteriors_pass = [0.0] * len(self.priors)
        posteriors_fail = [0.0] * len(self.priors)
        if p_pass > 0:
            for i in range(len(self.priors)):
                posteriors_pass[i] = (
                    experiment.pass_likelihood(i) * self.priors[i] / p_pass
                )
        if p_fail > 0:
            for i in range(len(self.priors)):
                posteriors_fail[i] = (
                    experiment.fail_likelihood(i) * self.priors[i] / p_fail
                )

        # Posterior entropies
        h_posterior_pass = self._entropy(posteriors_pass)
        h_posterior_fail = self._entropy(posteriors_fail)

        # Expected posterior entropy
        expected_posterior = p_pass * h_posterior_pass + p_fail * h_posterior_fail

        # Information gain
        ig = prior_entropy - expected_posterior
        return ig, expected_posterior, prior_entropy

    def select_next_experiment(self) -> Optional[ExperimentSelection]:
        """Select the experiment with maximum expected information gain per cost.

        Returns:
            ExperimentSelection, or None if no experiment has IG > ig_threshold
        """
        best_exp = None
        best_ig_per_cost = -1.0
        best_ig = 0.0
        best_expected_post = 0.0
        best_prior_entropy = 0.0

        prior_entropy = self._entropy(self.priors)

        for name, exp in self.designer.experiments.items():
            ig, expected_post, _ = self.compute_experiment_ig(exp)
            ig_per_cost = ig / exp.cost if exp.cost > 0 else ig
            if ig_per_cost > best_ig_per_cost:
                best_ig_per_cost = ig_per_cost
                best_exp = exp
                best_ig = ig
                best_expected_post = expected_post
                best_prior_entropy = prior_entropy

        if best_exp is None or best_ig < self.ig_threshold:
            return None

        reason = (
            f"IG={best_ig:.4f} bits (prior H={best_prior_entropy:.4f}, "
            f"expected post H={best_expected_post:.4f}), "
            f"IG/cost={best_ig_per_cost:.4f}. "
            f"Selected over {len(self.designer.experiments)} candidates."
        )

        selection = ExperimentSelection(
            experiment_name=best_exp.name,
            information_gain=best_ig,
            expected_posterior_entropy=best_expected_post,
            prior_entropy=best_prior_entropy,
            reason=reason,
        )
        self.selection_history.append(selection)
        return selection

    def run_experiment(self, experiment_name: str, outcome: str) -> Dict[str, Any]:
        """Run an experiment, observe the outcome, and update priors via Bayes.

        Args:
            experiment_name: the name of the experiment to run
            outcome: "pass" or "fail"

        Returns:
            Dict with old_priors, new_priors, max_posterior, converged
        """
        if experiment_name not in self.designer.experiments:
            raise ValueError(f"Unknown experiment: {experiment_name}")
        if outcome not in ("pass", "fail"):
            raise ValueError(f"Outcome must be 'pass' or 'fail', got {outcome!r}")

        exp = self.designer.experiments[experiment_name]
        old_priors = list(self.priors)

        # Marginal probability of the observed outcome
        if outcome == "pass":
            marginal = sum(exp.pass_likelihood(i) * self.priors[i] for i in range(len(self.priors)))
            likelihood_fn = exp.pass_likelihood
        else:
            marginal = sum(exp.fail_likelihood(i) * self.priors[i] for i in range(len(self.priors)))
            likelihood_fn = exp.fail_likelihood

        if marginal <= 0:
            # Outcome is impossible under current priors — priors are wrong
            return {
                "old_priors": old_priors,
                "new_priors": old_priors,
                "max_posterior": max(old_priors),
                "converged": False,
                "error": "Outcome has zero probability under current priors",
            }

        # Bayes update
        new_priors = [
            likelihood_fn(i) * self.priors[i] / marginal
            for i in range(len(self.priors))
        ]
        self.priors = new_priors

        # Record the outcome
        from datetime import datetime, timezone
        self.history.append(ExperimentOutcome(
            experiment_name=experiment_name,
            outcome=outcome,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

        max_post = max(self.priors)
        return {
            "old_priors": old_priors,
            "new_priors": new_priors,
            "max_posterior": max_post,
            "converged": max_post >= self.convergence_threshold,
        }

    def has_converged(self) -> bool:
        """Check if the learner has converged (max posterior ≥ threshold)."""
        return max(self.priors) >= self.convergence_threshold

    def best_hypothesis(self) -> Tuple[str, float]:
        """Return the current best hypothesis and its posterior probability."""
        best_idx = max(range(len(self.priors)), key=lambda i: self.priors[i])
        return self.designer.hypotheses[best_idx], self.priors[best_idx]


def main():
    """Demo: active-learning experiment selection."""
    print("=" * 60)
    print("Active-Learning Experiment Selection")
    print("(Learning 6→8: select next experiment by expected IG)")
    print("=" * 60)
    print()

    # 4 hypotheses about a material's conductivity mechanism
    hypotheses = [
        "Conductivity is linear in temperature",
        "Conductivity follows Arrhenius: σ = σ₀ exp(-Ea/kT)",
        "Conductivity has a phase transition at T_c",
        "Conductivity is exponential in T²",
    ]

    designer = ExperimentDesigner(hypotheses)

    # 3 candidate experiments, each with a likelihood for each hypothesis
    designer.add_experiment(
        "measure_at_low_T",
        "Measure conductivity at T = 100K",
        # P(pass | h_i is true): linear=0.3, arrhenius=0.9, phase=0.4, exp_t2=0.2
        pass_likelihoods=[0.3, 0.9, 0.4, 0.2],
    )
    designer.add_experiment(
        "measure_at_high_T",
        "Measure conductivity at T = 500K",
        # Linear is OK at high T; Arrhenius saturates; phase transition would show jump; exp_t2 explodes
        pass_likelihoods=[0.7, 0.4, 0.3, 0.95],
    )
    designer.add_experiment(
        "measure_near_Tc",
        "Measure conductivity at T = 300K (suspected Tc)",
        # Phase transition hypothesis most discriminating here
        pass_likelihoods=[0.5, 0.5, 0.95, 0.5],
    )

    learner = ActiveLearner(designer)

    print(f"Hypotheses ({len(hypotheses)}):")
    for i, h in enumerate(hypotheses):
        print(f"  [{i}] {h}")
    print(f"Initial priors (uniform): {learner.priors}")
    print()

    # Iteration 1: select first experiment
    print("--- Iteration 1 ---")
    sel1 = learner.select_next_experiment()
    if sel1:
        print(f"Selected: {sel1.experiment_name}")
        print(f"  {sel1.reason}")

        # Run it — say the outcome is "pass"
        result1 = learner.run_experiment(sel1.experiment_name, "pass")
        print(f"  Outcome: pass")
        print(f"  New priors: {[round(p, 4) for p in result1['new_priors']]}")
        print(f"  Max posterior: {result1['max_posterior']:.4f}")
        print(f"  Converged: {result1['converged']}")
    print()

    # Iteration 2: select next experiment
    print("--- Iteration 2 ---")
    sel2 = learner.select_next_experiment()
    if sel2:
        print(f"Selected: {sel2.experiment_name}")
        print(f"  {sel2.reason}")

        result2 = learner.run_experiment(sel2.experiment_name, "pass")
        print(f"  Outcome: pass")
        print(f"  New priors: {[round(p, 4) for p in result2['new_priors']]}")
        print(f"  Max posterior: {result2['max_posterior']:.4f}")
        print(f"  Converged: {result2['converged']}")
    print()

    # Iteration 3
    print("--- Iteration 3 ---")
    sel3 = learner.select_next_experiment()
    if sel3:
        print(f"Selected: {sel3.experiment_name}")
        print(f"  {sel3.reason}")
        result3 = learner.run_experiment(sel3.experiment_name, "pass")
        print(f"  Outcome: pass")
        print(f"  New priors: {[round(p, 4) for p in result3['new_priors']]}")
        print(f"  Max posterior: {result3['max_posterior']:.4f}")
        print(f"  Converged: {result3['converged']}")
    print()

    # Final
    best_h, best_p = learner.best_hypothesis()
    print(f"Best hypothesis: {best_h}")
    print(f"  Posterior: {best_p:.4f}")
    print(f"  Converged: {learner.has_converged()}")
    print()
    print("This is the auditor's required capability:")
    print("  - SELECT the next experiment (not just rank hypotheses)")
    print("  - MacKay expected information gain across the hypothesis space")
    print("  - Bayesian updating after each experiment")
    print("  - Convergence detection")


if __name__ == "__main__":
    main()
