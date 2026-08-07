#!/usr/bin/env python3
"""
belief_revision.py — DR-80: Revise beliefs about operator effectiveness.

Beliefs are represented as a probability distribution over operators
(indicating which operators are likely to produce good candidates).
After each measurement cycle, the beliefs are revised based on the
observed outcomes using a Bayesian update.

The belief revision:
  1. Maintains a prior probability per operator (initially uniform).
  2. For each observed (operator, passed) outcome, updates the belief
     using a simple Beta-Binomial update:
       P(op | pass) ∝ P(pass | op) * P(op)
     where P(pass | op) is the empirical success rate.
  3. After all updates, normalizes the beliefs.
  4. Returns a BeliefState with the revised distribution.

The revised beliefs drive operator selection in the next search
iteration (operators with higher beliefs are sampled more often).

Usage:
    from scripts.belief_revision import BeliefRevision
    br = BeliefRevision()
    br.observe("combine", passed=True)
    br.observe("substitute", passed=False)
    state = br.revise()
    # state.beliefs['combine'] > state.beliefs['substitute']
"""
import sys
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.operator_library import OPERATOR_LIBRARY


@dataclass
class BeliefState:
    """The current belief distribution over operators."""
    beliefs: Dict[str, float] = field(default_factory=dict)
    n_observations: int = 0
    n_operators: int = 0
    top_operator: Optional[str] = None
    bottom_operator: Optional[str] = None
    entropy: float = 0.0           # Shannon entropy (high = uniform)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beliefs": self.beliefs,
            "n_observations": self.n_observations,
            "n_operators": self.n_operators,
            "top_operator": self.top_operator,
            "bottom_operator": self.bottom_operator,
            "entropy": self.entropy,
            "timestamp": self.timestamp,
        }


@dataclass
class Observation:
    operator: str
    passed: bool
    weight: float = 1.0


class BeliefRevision:
    """DR-80: Bayesian belief revision over operator effectiveness."""

    def __init__(self,
                 operators: Optional[List[str]] = None,
                 prior_alpha: float = 1.0,
                 prior_beta: float = 1.0):
        """Args:
            operators: list of operator names (defaults to all 14)
            prior_alpha: Beta prior alpha (successes pseudo-count)
            prior_beta: Beta prior beta (failures pseudo-count)
        """
        self.operators: List[str] = list(operators) if operators else list(OPERATOR_LIBRARY.names)
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        # Per-operator pseudo-counts: (alpha, beta)
        self.counts: Dict[str, Tuple[float, float]] = {
            op: (prior_alpha, prior_beta) for op in self.operators
        }
        # Per-operator beliefs (posterior mean of Beta(alpha, beta))
        self.beliefs: Dict[str, float] = {
            op: prior_alpha / (prior_alpha + prior_beta)
            for op in self.operators
        }
        self.observations: List[Observation] = []

    # ----- public API ---------------------------------------------------
    def observe(self, operator: str, passed: bool, weight: float = 1.0) -> None:
        """Record one observation and update the belief for that operator."""
        if operator not in self.counts:
            self.counts[operator] = (self.prior_alpha, self.prior_beta)
            self.beliefs[operator] = self.prior_alpha / (self.prior_alpha + self.prior_beta)
        a, b = self.counts[operator]
        if passed:
            a += weight
        else:
            b += weight
        self.counts[operator] = (a, b)
        self.beliefs[operator] = a / (a + b)
        self.observations.append(Observation(
            operator=operator, passed=passed, weight=weight))

    def observe_many(self, observations: List[Tuple[str, bool]]) -> None:
        for op, passed in observations:
            self.observe(op, passed)

    def revise(self) -> BeliefState:
        """Return the current belief state.

        Beliefs are already updated incrementally in observe(); this
        method returns a snapshot.
        """
        # Compute Shannon entropy
        total = sum(self.beliefs.values())
        if total > 0:
            probs = [b / total for b in self.beliefs.values()]
            entropy = -sum(p * math.log(p + 1e-12) for p in probs if p > 0)
        else:
            entropy = 0.0

        # Top and bottom operators
        if self.beliefs:
            sorted_b = sorted(self.beliefs.items(), key=lambda x: -x[1])
            top = sorted_b[0][0]
            bottom = sorted_b[-1][0]
        else:
            top = None
            bottom = None

        return BeliefState(
            beliefs=dict(self.beliefs),
            n_observations=len(self.observations),
            n_operators=len(self.beliefs),
            top_operator=top,
            bottom_operator=bottom,
            entropy=round(entropy, 6),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_belief(self, operator: str) -> float:
        """Get the current belief (posterior mean) for an operator."""
        return self.beliefs.get(operator, 0.0)

    def recommended_operators(self, top_k: int = 5) -> List[str]:
        """Return the top-k operators by current belief."""
        sorted_ops = sorted(self.beliefs.items(), key=lambda x: -x[1])
        return [op for op, _ in sorted_ops[:top_k]]

    def reset(self) -> None:
        """Reset beliefs to the prior."""
        self.counts = {op: (self.prior_alpha, self.prior_beta)
                       for op in self.operators}
        self.beliefs = {op: self.prior_alpha / (self.prior_alpha + self.prior_beta)
                        for op in self.operators}
        self.observations = []


def main():
    print("=" * 60)
    print("BELIEF REVISION (DR-80)")
    print("=" * 60)
    print()

    br = BeliefRevision()
    state0 = br.revise()
    print(f"Initial beliefs (uniform): n_ops={state0.n_operators} "
          f"entropy={state0.entropy:.4f}")
    print()

    # Simulate observations
    for _ in range(5):
        br.observe("combine", passed=True)
    for _ in range(3):
        br.observe("substitute", passed=False)
    for _ in range(2):
        br.observe("invert", passed=True)
    for _ in range(2):
        br.observe("invert", passed=False)

    state = br.revise()
    print(f"After 12 observations:")
    print(f"  n_observations = {state.n_observations}")
    print(f"  entropy = {state.entropy:.4f}")
    print(f"  top operator = {state.top_operator}")
    print(f"  bottom operator = {state.bottom_operator}")
    print(f"  P(combine) = {state.beliefs['combine']:.4f}")
    print(f"  P(substitute) = {state.beliefs['substitute']:.4f}")
    print(f"  P(invert) = {state.beliefs['invert']:.4f}")
    print()
    print(f"Recommended top-3: {br.recommended_operators(top_k=3)}")


if __name__ == "__main__":
    main()
