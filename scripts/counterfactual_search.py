#!/usr/bin/env python3
"""
counterfactual_search.py — Counterfactual reasoning (Causal reasoning 6→8).

Per cycle 180: the auditor requires counterfactual search. I have:
- do() via graph surgery (cycle 142)
- Backdoor adjustment on data (cycle 175)
Missing: COUNTERFACTUAL reasoning — "what would have happened if X
were different, given that we observed X=x and Y=y?"

Pearl's counterfactual (Pearl 2000):
  P(Y_x | X=x', Y=y') = probability that Y would have been Y_x if X
  had been x, given that we actually observed X=x' and Y=y'.

This is the THREE-STEP procedure:
1. ABDUCTION: update the model (posterior over unobserved variables)
2. ACTION: do(X=x) — modify the model
3. PREDICTION: compute P(Y) in the modified model

Usage:
    from scripts.counterfactual_search import CounterfactualSearcher
    searcher = CounterfactualSearcher()
    result = searcher.counterfactual(data, 'smoking', 1, 'cancer', 0, 1)
    # "Given that a non-smoker got cancer, what if they had smoked?"
"""
import math
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


@dataclass
class CounterfactualResult:
    """The result of a counterfactual query."""
    observation: str    # what was actually observed
    intervention: str   # what we're asking "what if"
    question: str       # the counterfactual question
    observed_outcome: float  # Y observed
    counterfactual_outcome: float  # P(Y=1 | do(X=x), observed X=x', Y=y')
    effect: float       # counterfactual - observed
    reasoning: str


class CounterfactualSearcher:
    """Pearl's counterfactual reasoning (3-step: abduction → action → prediction).

    This implements the counterfactual query:
      "Given that we observed X=x' and Y=y', what would Y have been if X
      had been x instead?"

    The three steps:
    1. ABDUCTION: Given the observation (X=x', Y=y'), update our belief
       about the unobserved variables (confounders, noise).
    2. ACTION: Modify the model by setting X=x (do(X=x)).
    3. PREDICTION: Compute P(Y=1) in the modified model, using the
       abducted values from step 1.
    """

    def counterfactual(self, data: List[Dict],
                       treatment: str, observed_x: float,
                       outcome: str, observed_y: float,
                       counterfactual_x: float,
                       backdoor_vars: Optional[List[str]] = None) -> CounterfactualResult:
        """Compute a counterfactual query.

        Args:
            data: observational data
            treatment: the treatment variable X
            observed_x: the actually observed value of X (x')
            outcome: the outcome variable Y
            observed_y: the actually observed value of Y (y')
            counterfactual_x: the counterfactual value of X (x)
            backdoor_vars: confounders Z to adjust for

        Returns:
            CounterfactualResult with the counterfactual prediction
        """
        if not data:
            return CounterfactualResult("", "", "", 0, 0, 0, "no data")

        # Identify backdoor variables if not provided
        if backdoor_vars is None:
            backdoor_vars = self._identify_confounders(data, treatment, outcome)

        # Step 1: ABDUCTION
        # Given X=x' and Y=y', what do we know about Z?
        # Find individuals with similar X and Y values
        similar = [
            d for d in data
            if abs(d.get(treatment, 0) - observed_x) < 0.5
            and abs(d.get(outcome, 0) - observed_y) < 0.5
        ]

        if not similar:
            # No similar individuals — use population average
            z_posterior = {}
            for z in backdoor_vars:
                z_vals = [d.get(z, 0) for d in data]
                z_posterior[z] = sum(z_vals) / len(z_vals) if z_vals else 0.5
        else:
            # Use the conditional distribution of Z given X=x', Y=y'
            z_posterior = {}
            for z in backdoor_vars:
                z_vals = [d.get(z, 0) for d in similar]
                z_posterior[z] = sum(z_vals) / len(z_vals) if z_vals else 0.5

        # Step 2: ACTION
        # do(X=x) — set treatment to counterfactual value
        # The model now has X=counterfactual_x, Z=z_posterior (abducted)

        # Step 3: PREDICTION
        # Compute P(Y=1 | do(X=counterfactual_x), Z=z_posterior)
        # Using the backdoor-adjusted estimate

        # Find individuals with X=counterfactual_x and Z near z_posterior
        counterfactual_individuals = []
        for d in data:
            if abs(d.get(treatment, 0) - counterfactual_x) < 0.5:
                # Check if Z values match the abducted posterior
                z_match = True
                for z in backdoor_vars:
                    if abs(d.get(z, 0) - z_posterior.get(z, 0.5)) > 0.5:
                        z_match = False
                        break
                if z_match or not backdoor_vars:
                    counterfactual_individuals.append(d)

        if counterfactual_individuals:
            cf_outcome = sum(d.get(outcome, 0) for d in counterfactual_individuals) / len(counterfactual_individuals)
        else:
            # Fall back to marginal P(Y | X=counterfactual_x)
            x_match = [d for d in data if abs(d.get(treatment, 0) - counterfactual_x) < 0.5]
            cf_outcome = sum(d.get(outcome, 0) for d in x_match) / len(x_match) if x_match else 0.5

        effect = cf_outcome - observed_y

        question = (f"Given {treatment}={observed_x} and {outcome}={observed_y}, "
                   f"what would {outcome} have been if {treatment}={counterfactual_x}?")

        reasoning = (
            f"Step 1 (Abduction): Given {treatment}={observed_x}, {outcome}={observed_y}, "
            f"updated belief about confounders: {z_posterior}. "
            f"Step 2 (Action): do({treatment}={counterfactual_x}). "
            f"Step 3 (Prediction): P({outcome}=1 | do({treatment}={counterfactual_x}), abducted Z) = {cf_outcome:.4f}. "
            f"Counterfactual effect: {effect:.4f}"
        )

        return CounterfactualResult(
            observation=f"{treatment}={observed_x}, {outcome}={observed_y}",
            intervention=f"do({treatment}={counterfactual_x})",
            question=question,
            observed_outcome=observed_y,
            counterfactual_outcome=round(cf_outcome, 4),
            effect=round(effect, 4),
            reasoning=reasoning,
        )

    def _identify_confounders(self, data: List[Dict], x: str, y: str) -> List[str]:
        """Identify confounders via correlation."""
        all_vars = set(data[0].keys()) - {x, y}
        confounders = []
        for z in all_vars:
            x_vals = [d.get(x, 0) for d in data]
            z_vals = [d.get(z, 0) for d in data]
            y_vals = [d.get(y, 0) for d in data]
            corr_xz = self._corr(x_vals, z_vals)
            corr_yz = self._corr(y_vals, z_vals)
            if abs(corr_xz) > 0.1 and abs(corr_yz) > 0.1:
                confounders.append(z)
        return confounders

    def _corr(self, x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2: return 0.0
        mx, my = sum(x)/n, sum(y)/n
        cov = sum((a-mx)*(b-my) for a,b in zip(x,y))
        vx = sum((a-mx)**2 for a in x)
        vy = sum((b-my)**2 for b in y)
        if vx == 0 or vy == 0: return 0.0
        return cov / (math.sqrt(vx) * math.sqrt(vy))


def main():
    """Demo: counterfactual reasoning."""
    import random
    random.seed(42)

    print("=" * 60)
    print("Counterfactual Reasoning (Pearl 3-step: abduction → action → prediction)")
    print("=" * 60)
    print()

    # Generate confounded data
    data = []
    for _ in range(1000):
        age = random.choice([0, 1])
        smoking = 1 if random.random() < (0.3 + 0.4 * age) else 0
        cancer_prob = 0.1 + 0.3 * age + 0.2 * smoking
        cancer = 1 if random.random() < cancer_prob else 0
        data.append({"smoking": smoking, "cancer": cancer, "age": age})

    searcher = CounterfactualSearcher()

    # Query 1: "Given a non-smoker got cancer, what if they had smoked?"
    result1 = searcher.counterfactual(data, "smoking", 0, "cancer", 1, 1)
    print(f"Query 1: {result1.question}")
    print(f"  Observed: cancer={result1.observed_outcome}")
    print(f"  Counterfactual: cancer={result1.counterfactual_outcome}")
    print(f"  Effect: {result1.effect}")
    print(f"  Reasoning: {result1.reasoning}")
    print()

    # Query 2: "Given a smoker did NOT get cancer, what if they hadn't smoked?"
    result2 = searcher.counterfactual(data, "smoking", 1, "cancer", 0, 0)
    print(f"Query 2: {result2.question}")
    print(f"  Observed: cancer={result2.observed_outcome}")
    print(f"  Counterfactual: cancer={result2.counterfactual_outcome}")
    print(f"  Effect: {result2.effect}")
    print()

    print("This is Pearl's counterfactual reasoning — the third level of")
    print("causal inference (after association and intervention).")
    print("Level 1: P(Y|X) — association")
    print("Level 2: P(Y|do(X)) — intervention (cycle 175)")
    print("Level 3: P(Y_x | X=x', Y=y') — counterfactual (this cycle)")


if __name__ == "__main__":
    main()
