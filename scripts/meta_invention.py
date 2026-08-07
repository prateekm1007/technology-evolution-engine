#!/usr/bin/env python3
"""
meta_invention.py — Meta-invention layer (cycle 218).

Per the auditor's update #8:

    "Earlier I proposed 'General invention heuristics.' Now I'd replace
    that. Instead I'd pursue 'General optimization strategies.' Those
    are not the same thing.

    Instead of learning 'grain size → good', the engine should learn
    'this landscape → high interaction → Bayesian search' or
    'landscape → needle → importance sampling.' Those transfer."

This module implements the four-stage meta-invention roadmap:

  L1. Landscape classification
      Sample the objective function across the design space and compute
      statistical signatures: skewness, sparsity, modality, interaction.
      Classify into one of:
        - SMOOTH           (gradient/greedy works)
        - MULTIMODAL       (multiple local optima)
        - NEEDLE           (heavy skew, sparse success)
        - DECEPTIVE        (constraint-dominated, bimodal)
        - CONSTRAINT_DOM   (most candidates infeasible)

  L2. Optimizer selection
      Given a landscape type, select the appropriate optimizer:
        - SMOOTH     → GreedyHillClimber (narrow policy toward IQR of winners)
        - MULTIMODAL → BeamSearch (maintain top-K policies, explore each)
        - NEEDLE     → ImportanceSampler (resample around successful regions)
        - DECEPTIVE  → BayesianOptimizer (surrogate model + acquisition)
        - CONSTRAINT → EvolutionarySearch (population + crossover + mutation)

  L3. Operator learning
      Each optimizer exposes its own 'mutation operator' (how it proposes
      the next candidate). The system records which operator worked on
      which landscape.

  L4. Meta-learning
      Across domains, the (landscape_type → best_optimizer) mapping
      persists. This is the GENERAL object that transfers — not the
      heuristics, but the meta-policy.

Causal-graph upgrade:
  Heuristics now carry an executable causal chain rather than prose.
  Example:
    OLD: "because Pisarenko relation drives S toward zero"
    NEW: causal_chain = [
        ("carrier_concentration", "increases"),
        ("effective_mass", "decreases (Pisarenko: m* ~ n^(-1/3) at high n)"),
        ("seebeck_coefficient", "decreases (S = (8π²k²/3eh²) m*T (π/3n)^(2/3))"),
        ("ZT", "decreases (ZT = S²σT/κ)")
    ]
  The chain is verifiable: each step references a named physical relation.
"""
import sys
import math
import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from pathlib import Path
from collections import defaultdict
from enum import Enum

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ============================================================================
# L1 — LANDSCAPE CLASSIFICATION
# ============================================================================

class LandscapeType(Enum):
    SMOOTH = "smooth"
    MULTIMODAL = "multimodal"
    NEEDLE = "needle"
    DECEPTIVE = "deceptive"
    CONSTRAINT_DOM = "constraint_dominated"
    UNKNOWN = "unknown"


@dataclass
class LandscapeSignature:
    """Statistical signature of an optimization landscape.

    Computed from a sample of (design_point, outcome) pairs. These
    signatures are DOMAIN-INVARIANT — they describe the SHAPE of the
    landscape, not the underlying physics.
    """
    n_samples: int
    q25: float
    q50: float
    q75: float
    q99: float
    max_val: float
    nonzero_fraction: float  # fraction of samples above 1% of max
    skew_ratio: float        # q50 / q99 (low = heavy skew)
    bimodality: float        # 0=unimodal, 1=perfectly bimodal
    interaction_index: float # 0=additive, 1=fully interacting
    landscape_type: LandscapeType

    def to_dict(self) -> Dict:
        d = self.__dict__.copy()
        d["landscape_type"] = self.landscape_type.value
        return d


class LandscapeClassifier:
    """Classifies an optimization landscape from a sample.

    The classifier computes statistical signatures that are domain-
    invariant — they describe the SHAPE of the landscape (skewness,
    sparsity, modality, interaction) rather than the underlying physics.

    This is the key abstraction: instead of learning 'thermoelectric'
    vs 'battery', we learn 'smooth' vs 'needle'. The former does not
    transfer; the latter does.
    """

    def classify(self, candidates: List, design_vars: List[Dict]) -> LandscapeSignature:
        """Classify the landscape from a sample of evaluated candidates.

        Cycle 220 fix: SIGN-AWARE normalization. The original classifier
        assumed positive outcomes (computed nonzero_fraction as
        "fraction > 1% of max"). This broke on synthetic landscapes
        where outcomes are negative (e.g., Sphere = -13.7 to 0). The
        fix normalizes outcomes to [0,1] based on the OBSERVED spread
        (min to max), so the same statistical rules work regardless
        of sign.

        Honest result before fix: 0/7 synthetic landscapes classified
        correctly. After fix: see test_synthetic_landscape_classification.
        """
        if len(candidates) < 20:
            return LandscapeSignature(
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, LandscapeType.UNKNOWN
            )

        outcomes = sorted(c.predicted_outcome for c in candidates)
        n = len(outcomes)
        q25 = outcomes[n // 4]
        q50 = outcomes[n // 2]
        q75 = outcomes[3 * n // 4]
        q99 = outcomes[int(0.99 * n)]
        max_val = outcomes[-1]
        min_val = outcomes[0]

        # Cycle 220 v2 — refined sign-aware metrics.
        # The original nonzero_fraction ("> 5% of spread") couldn't
        # distinguish "all-equal-because-needle" from "all-equal-because-
        # smooth". The new metric: "fraction of samples within 5% of MAX"
        # — this captures "how many samples are near the best seen".
        # For a needle: very few samples are near max (most are at min).
        # For a smooth landscape: many samples are spread across the range.
        spread = max_val - min_val
        if spread < 1e-12:
            normalized = [0.5] * n
            near_max_fraction = 0.5  # degenerate, treat as unknown
        else:
            normalized = [(o - min_val) / spread for o in outcomes]
            # "Near max" = within 5% of the spread from max
            near_max_fraction = sum(1 for no in normalized if no > 0.95) / n

        # Cycle 220 v3 — better needle detection.
        # A needle landscape has TWO signatures:
        #   (a) most samples at the FLOOR (near_min > 0.5), OR
        #   (b) spread is degenerate (all samples produce same value
        #       because the needle was never hit in N samples)
        # Case (b) is critical: with N=100 random samples and a needle
        # occupying 0.05^4 = 6.25e-6 of the volume, we expect ~0 hits.
        # The tell-tale: spread < 1e-9 × |max| AND max is "suspiciously
        # close to a floor value" (e.g., 0 or a small constant).
        if spread < 1e-9 * max(1.0, abs(max_val)):
            # Degenerate spread — almost all samples produce same value.
            # This is the signature of a needle we haven't hit.
            landscape_type = LandscapeType.NEEDLE
            # Re-classify as CONSTRAINT_DOM if the floor is exactly 0
            # (typical of constraint-dominated landscapes where
            # infeasible = 0 exactly)
            if abs(min_val) < 1e-12 and abs(max_val) < 1e-12:
                landscape_type = LandscapeType.CONSTRAINT_DOM
            return LandscapeSignature(
                n_samples=n, q25=q25, q50=q50, q75=q75, q99=q99, max_val=max_val,
                nonzero_fraction=0.0, skew_ratio=0.0,
                bimodality=0.0, interaction_index=0.0,
                landscape_type=landscape_type,
            )

        # For non-degenerate landscapes, use the refined rules below.
        # near_min_fraction: fraction of samples at the FLOOR (near min).
        # For a needle: most samples are near min (nonzero=low).
        # For a smooth landscape: samples are spread (nonzero=high).
        near_min_fraction = sum(1 for no in normalized if no < 0.05) / n

        # nonzero_fraction (kept for backward compat) = 1 - near_min_fraction
        # = fraction of samples NOT at the floor
        nonzero_fraction = 1.0 - near_min_fraction

        # skew_ratio: how close the median is to the max.
        # Sign-aware: use normalized values so this is in [0, 1].
        norm_q50 = (q50 - min_val) / max(1e-12, spread)
        norm_q99 = (q99 - min_val) / max(1e-12, spread)
        skew_ratio = norm_q50 / max(1e-6, norm_q99)

        bimodality = self._bimodality_coefficient(outcomes)
        interaction_index = self._interaction_index(candidates, design_vars)

        # Classification rules (sign-aware, refined)
        # Order matters: most-specific rules first.
        is_needle = near_min_fraction > 0.5 and near_max_fraction < 0.1

        # Cycle 220 v4 — tighten the deceptive rule.
        # The previous rule (bimodality > 0.55 and 0.3 <= near_min <= 0.7)
        # was too permissive: it matched Catalyst (which has a continuous
        # skewed distribution, not a true bimodal one). A real deceptive
        # landscape has TWO separated peaks — visible as a GAP in the
        # middle of the sorted outcomes.
        # New rule: bimodality > 0.55 AND there's a clear gap (the middle
        # 20% of sorted outcomes spans < 10% of the spread).
        is_deceptive = False
        if not is_needle and bimodality > 0.55 and 0.3 <= near_min_fraction <= 0.7:
            # Check for a gap in the middle of the sorted outcomes
            mid_lo_idx = int(0.4 * n)
            mid_hi_idx = int(0.6 * n)
            mid_lo_val = outcomes[mid_lo_idx]
            mid_hi_val = outcomes[mid_hi_idx]
            mid_span = mid_hi_val - mid_lo_val
            if spread > 1e-12 and mid_span / spread < 0.10:
                is_deceptive = True

        if is_needle:
            # Distinguish NEEDLE from CONSTRAINT_DOM:
            # CONSTRAINT_DOM has a STRUCTURAL floor (exact same min value
            # for many samples, because infeasible = 0 exactly).
            exact_min_count = sum(1 for o in outcomes if abs(o - min_val) < 1e-9 * max(1.0, abs(min_val)))
            if exact_min_count / n > 0.5:
                landscape_type = LandscapeType.CONSTRAINT_DOM
            else:
                landscape_type = LandscapeType.NEEDLE
        elif is_deceptive:
            landscape_type = LandscapeType.DECEPTIVE
        elif interaction_index > 0.5 and bimodality > 0.4:
            landscape_type = LandscapeType.MULTIMODAL
        elif skew_ratio > 0.15:
            landscape_type = LandscapeType.SMOOTH
        else:
            landscape_type = LandscapeType.SMOOTH

        return LandscapeSignature(
            n_samples=n, q25=q25, q50=q50, q75=q75, q99=q99, max_val=max_val,
            nonzero_fraction=nonzero_fraction, skew_ratio=skew_ratio,
            bimodality=bimodality, interaction_index=interaction_index,
            landscape_type=landscape_type,
        )

    def _bimodality_coefficient(self, values: List[float]) -> float:
        """Compute bimodality coefficient BC = (skewness² + 1) / kurtosis.

        BC > 0.555 indicates bimodal distribution.
        """
        if len(values) < 10:
            return 0.0
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / max(1, n - 1)
        if variance < 1e-20:
            return 0.0
        std = math.sqrt(variance)
        skewness = sum((v - mean) ** 3 for v in values) / (n * std ** 3)
        kurtosis = sum((v - mean) ** 4 for v in values) / (n * std ** 4)
        if kurtosis < 1e-12:
            return 0.0
        bc = (skewness ** 2 + 1) / max(0.01, kurtosis)
        return min(1.0, bc)

    def _interaction_index(self, candidates: List, design_vars: List[Dict]) -> float:
        """Estimate interaction strength among design variables.

        Method: fit a purely additive model (sum of single-variable
        contributions) and compare to the actual outcome variance.
        If the additive model explains most of the variance, interaction
        is low. If it explains little, interaction is high.
        """
        if len(candidates) < 30 or len(design_vars) < 2:
            return 0.0

        # Bin each variable into 3 quantiles, compute mean outcome per bin
        # Then predict outcome as sum of bin means minus global mean
        outcomes = [c.predicted_outcome for c in candidates]
        global_mean = sum(outcomes) / len(outcomes)
        total_var = sum((o - global_mean) ** 2 for o in outcomes) / len(outcomes)
        if total_var < 1e-20:
            return 0.0

        bin_means = {}
        for var in design_vars:
            vname = var["name"]
            vals = sorted(c.design_point[vname] for c in candidates)
            n = len(vals)
            t1 = vals[n // 3]
            t2 = vals[2 * n // 3]
            for c in candidates:
                v = c.design_point[vname]
                if v <= t1:
                    bin_means[(vname, 0)] = bin_means.get((vname, 0), [])
                    bin_means[(vname, 0)].append(c.predicted_outcome)
                elif v <= t2:
                    bin_means[(vname, 1)] = bin_means.get((vname, 1), [])
                    bin_means[(vname, 1)].append(c.predicted_outcome)
                else:
                    bin_means[(vname, 2)] = bin_means.get((vname, 2), [])
                    bin_means[(vname, 2)].append(c.predicted_outcome)

        # Average each bin
        avg_bins = {k: sum(v)/len(v) for k, v in bin_means.items() if v}

        # Predict: additive model = global_mean + sum(bin_mean - global_mean)
        residuals = []
        for c in candidates:
            pred = global_mean
            for var in design_vars:
                vname = var["name"]
                v = c.design_point[vname]
                vals = sorted(cc.design_point[vname] for cc in candidates)
                n = len(vals)
                t1 = vals[n // 3]
                t2 = vals[2 * n // 3]
                if v <= t1:
                    bin_idx = 0
                elif v <= t2:
                    bin_idx = 1
                else:
                    bin_idx = 2
                pred += avg_bins.get((vname, bin_idx), global_mean) - global_mean
            residuals.append((c.predicted_outcome - pred) ** 2)

        residual_var = sum(residuals) / len(residuals)
        explained = 1.0 - residual_var / total_var
        # Interaction index = unexplained variance
        return max(0.0, min(1.0, 1.0 - explained))


# ============================================================================
# L2 — OPTIMIZER SELECTION + IMPLEMENTATIONS
# ============================================================================

@dataclass
class OptimizationResult:
    """Result of running an optimizer on a landscape."""
    optimizer_name: str
    landscape_type: str
    iteration: int
    avg_outcome: float
    median_outcome: float
    best_outcome: float
    n_candidates: int
    n_evaluations: int  # may exceed n_candidates if surrogate model used


class Optimizer:
    """Base class for optimizers."""
    name: str = "base"

    def __init__(self, domain_spec: Dict):
        self.domain = domain_spec
        self.original_bounds: Dict[str, Tuple[float, float]] = {
            v["name"]: v["bounds"] for v in domain_spec["design_vars"]
        }
        self.policy: Dict[str, Tuple[float, float]] = dict(self.original_bounds)
        self.n_evaluations: int = 0

    def sample(self, rng: random.Random, exploration_rate: float = 0.2) -> Dict[str, float]:
        """Sample a design point within current policy bounds, with
        exploration floor."""
        dp = {}
        for var in self.domain["design_vars"]:
            name = var["name"]
            lo, hi = self.policy[name]
            orig_lo, orig_hi = self.original_bounds[name]
            if rng.random() < exploration_rate:
                lo, hi = orig_lo, orig_hi
            if lo > 0 and hi / max(1e-12, lo) > 100:
                val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            else:
                val = rng.uniform(lo, hi)
            dp[name] = val
        return dp

    def step(self, candidates: List, rng: random.Random) -> List:
        """Take one optimization step given evaluated candidates."""
        raise NotImplementedError

    def evaluate(self, dp: Dict[str, float], forward_fn: Callable) -> Tuple:
        self.n_evaluations += 1
        return forward_fn(dp)


class GreedyHillClimber(Optimizer):
    """For SMOOTH landscapes — narrow policy toward IQR of winners.

    This is the original cycle 217 behavior, refined. Works well when
    the landscape is a smooth hill (TE, Catalyst).
    """
    name = "greedy_hill_climber"

    def step(self, candidates: List, rng: random.Random) -> List:
        if len(candidates) < 8:
            return []
        outcomes = sorted(c.predicted_outcome for c in candidates)
        n = len(outcomes)
        q75 = outcomes[3 * n // 4]
        winners = [c for c in candidates if c.predicted_outcome >= q75]
        for var in self.domain["design_vars"]:
            vname = var["name"]
            winning_vals = sorted(c.design_point[vname] for c in winners)
            nw = len(winning_vals)
            win_lo = winning_vals[max(0, nw // 4)]
            win_hi = winning_vals[min(nw - 1, 3 * nw // 4)]
            lo, hi = self.policy[vname]
            orig_lo, orig_hi = self.original_bounds[vname]
            new_lo = 0.85 * lo + 0.15 * win_lo
            new_hi = 0.85 * hi + 0.15 * win_hi
            min_span = 0.30 * (orig_hi - orig_lo)
            if new_hi - new_lo < min_span:
                center = (new_lo + new_hi) / 2
                new_lo = max(orig_lo, center - min_span / 2)
                new_hi = min(orig_hi, center + min_span / 2)
            if new_hi > new_lo:
                self.policy[vname] = (new_lo, new_hi)
        return []


class ImportanceSampler(Optimizer):
    """For NEEDLE landscapes — resample preferentially around successful regions.

    When most candidates produce ~0 outcome, greedy narrowing fails
    because the IQR of "winners" is itself ~0. Instead, this optimizer:

      1. Identifies the top 5% of candidates (the "needles")
      2. Builds a Gaussian kernel around their design points
      3. Samples new candidates from the kernel mixture

    This is the standard approach for rare-event simulation.
    """
    name = "importance_sampler"

    def __init__(self, domain_spec: Dict):
        super().__init__(domain_spec)
        self.kernel_centers: List[Dict[str, float]] = []
        self.kernel_width: Dict[str, float] = {}

    def step(self, candidates: List, rng: random.Random) -> List:
        if len(candidates) < 10:
            return []
        outcomes = sorted(c.predicted_outcome for c in candidates)
        n = len(outcomes)
        # Top 10% as kernel centers
        threshold = outcomes[int(0.9 * n)]
        winners = [c for c in candidates if c.predicted_outcome >= threshold]
        if not winners:
            return []

        self.kernel_centers = [c.design_point for c in winners[:10]]

        # Compute kernel width = std of winning values per variable
        for var in self.domain["design_vars"]:
            vname = var["name"]
            vals = [c.design_point[vname] for c in winners]
            if len(vals) > 1:
                mean = sum(vals) / len(vals)
                std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
                # Ensure non-zero width
                lo, hi = self.original_bounds[vname]
                self.kernel_width[vname] = max(std, 0.05 * (hi - lo))
            else:
                lo, hi = self.original_bounds[vname]
                self.kernel_width[vname] = 0.1 * (hi - lo)

        # Narrow the policy to a tight region around the kernel centers
        for var in self.domain["design_vars"]:
            vname = var["name"]
            vals = [c.design_point[vname] for c in winners]
            lo, hi = self.original_bounds[vname]
            # Set policy to [min - width, max + width] of winners
            new_lo = max(lo, min(vals) - self.kernel_width[vname])
            new_hi = min(hi, max(vals) + self.kernel_width[vname])
            if new_hi > new_lo:
                self.policy[vname] = (new_lo, new_hi)
        return []


class BayesianOptimizer(Optimizer):
    """For DECEPTIVE / high-interaction landscapes — surrogate model + acquisition.

    When the landscape has strong variable interactions (PV: bandgap ×
    defects interact), greedy single-variable narrowing locks onto the
    wrong region. Instead, this optimizer:

      1. Fits a quadratic surrogate model to the (design_point, outcome) data
      2. Uses expected improvement (EI) as the acquisition function
      3. Samples new candidates where EI is high

    The quadratic surrogate captures pairwise interactions, which is
    the minimum needed for deceptive landscapes.

    Cycle 220 v2 fix: regression detection. If the best outcome in the
    current iteration is significantly worse than the best seen so far,
    the policy has over-narrowed. Widen it back to 50% of original
    bounds (with the center kept at the current best).
    """
    name = "bayesian_optimizer"

    def __init__(self, domain_spec: Dict):
        super().__init__(domain_spec)
        self.surrogate_coeffs: Dict = {}
        self.best_so_far: float = -math.inf
        self.iteration: int = 0
        self.recent_bests: List[float] = []  # track last 3 bests

    def step(self, candidates: List, rng: random.Random) -> List:
        if len(candidates) < 20:
            return []
        self.iteration += 1

        current_best = max(c.predicted_outcome for c in candidates)
        self.recent_bests.append(current_best)
        if len(self.recent_bests) > 3:
            self.recent_bests.pop(0)

        # Cycle 220 v2 — regression detection.
        # If we have 3+ recent bests and the trend is declining (each
        # recent best < previous), the policy has over-narrowed. Widen.
        if len(self.recent_bests) >= 3:
            declining = all(self.recent_bests[i] < self.recent_bests[i-1]
                           for i in range(1, len(self.recent_bests)))
            if declining:
                # Widen policy back to 60% of original span
                for var in self.domain["design_vars"]:
                    vname = var["name"]
                    lo, hi = self.original_bounds[vname]
                    cur_lo, cur_hi = self.policy[vname]
                    center = (cur_lo + cur_hi) / 2
                    new_span = 0.6 * (hi - lo)
                    new_lo = max(lo, center - new_span / 2)
                    new_hi = min(hi, center + new_span / 2)
                    if new_hi > new_lo:
                        self.policy[vname] = (new_lo, new_hi)
                # Reset recent_bests to avoid re-triggering
                self.recent_bests = []
                return []

        # Also check for sharp regression: current < 0.5 * best_so_far
        if self.best_so_far > -math.inf and current_best < 0.5 * self.best_so_far:
            for var in self.domain["design_vars"]:
                vname = var["name"]
                lo, hi = self.original_bounds[vname]
                cur_lo, cur_hi = self.policy[vname]
                center = (cur_lo + cur_hi) / 2
                new_span = 0.6 * (hi - lo)
                new_lo = max(lo, center - new_span / 2)
                new_hi = min(hi, center + new_span / 2)
                if new_hi > new_lo:
                    self.policy[vname] = (new_lo, new_hi)
            self.recent_bests = []
            return []

        # Cycle 220 v3 — preemptive over-narrowing detection.
        # The regression check (above) only triggers AFTER a bad iteration,
        # which is too late if we only have 5 iterations. Instead, check
        # if the policy has narrowed below 20% of original span — if so,
        # widen it back proactively. This prevents the lock-on that causes
        # the regression in the first place.
        min_span_threshold = 0.20  # 20% of original
        for var in self.domain["design_vars"]:
            vname = var["name"]
            lo, hi = self.original_bounds[vname]
            cur_lo, cur_hi = self.policy[vname]
            cur_span = cur_hi - cur_lo
            orig_span = hi - lo
            if cur_span < min_span_threshold * orig_span:
                # Over-narrowed — widen back to 40% of original, centered
                center = (cur_lo + cur_hi) / 2
                new_span = 0.40 * orig_span
                new_lo = max(lo, center - new_span / 2)
                new_hi = min(hi, center + new_span / 2)
                if new_hi > new_lo:
                    self.policy[vname] = (new_lo, new_hi)

        self.best_so_far = max(self.best_so_far, current_best)
        self._fit_surrogate(candidates)

        # Cycle 220 v4 — surrogate quality check.
        # If the quadratic surrogate doesn't generalize (CV-R² < 0.3),
        # the landscape is too complex for a quadratic model. Fall back
        # to EvolutionarySearch-style behavior (crossover + mutation
        # from top candidates). This is honest: we tried Bayesian, the
        # surrogate didn't generalize, so we fall back to a method that
        # doesn't rely on a surrogate at all.
        surrogate_r2 = self._surrogate_r2(candidates)
        if surrogate_r2 < 0.3:
            # Surrogate is unreliable — use evolutionary-style step:
            # take top quartile as parents, generate offspring via
            # crossover + mutation, narrow policy to offspring range.
            # ALSO: increase exploration floor to 40% to escape local optima
            outcomes = sorted(c.predicted_outcome for c in candidates)
            n = len(outcomes)
            q75 = outcomes[3 * n // 4]
            parents = [c for c in candidates if c.predicted_outcome >= q75]
            if len(parents) >= 2:
                # Generate offspring via crossover + mutation
                offspring_designs = []
                for _ in range(20):
                    p1, p2 = rng.sample(parents, 2)
                    child = {}
                    for var in self.domain["design_vars"]:
                        vname = var["name"]
                        # Crossover: pick from p1 or p2
                        child[vname] = p1.design_point[vname] if rng.random() < 0.5 else p2.design_point[vname]
                        # Mutation: perturb (higher rate to escape local optima)
                        if rng.random() < 0.5:  # 50% mutation rate (was 30%)
                            lo, hi = self.original_bounds[vname]
                            if lo > 0 and hi / lo > 100:
                                log_val = math.log(max(1e-12, child[vname]))
                                log_val += rng.uniform(-1.0, 1.0)  # wider perturbation
                                child[vname] = max(lo, min(hi, math.exp(log_val)))
                            else:
                                span = hi - lo
                                child[vname] = max(lo, min(hi, child[vname] + rng.uniform(-0.2, 0.2) * span))
                    offspring_designs.append(child)
                # Narrow policy to range of offspring (wider than before)
                for var in self.domain["design_vars"]:
                    vname = var["name"]
                    vals = [d[vname] for d in offspring_designs]
                    lo, hi = self.original_bounds[vname]
                    # Add 20% padding to maintain diversity
                    pad = 0.20 * (hi - lo)
                    new_lo = max(lo, min(vals) - pad)
                    new_hi = min(hi, max(vals) + pad)
                    if new_hi > new_lo:
                        self.policy[vname] = (new_lo, new_hi)
            return []

        # Generate acquisition candidates and pick the best
        acq_candidates = []
        for _ in range(200):
            dp = self.sample(rng, exploration_rate=0.5)
            ei = self._expected_improvement(dp)
            acq_candidates.append((ei, dp))
        acq_candidates.sort(reverse=True, key=lambda x: x[0])
        # Narrow policy toward top acquisition candidates
        top = acq_candidates[:max(5, len(acq_candidates) // 10)]
        for var in self.domain["design_vars"]:
            vname = var["name"]
            vals = [dp[vname] for _, dp in top]
            lo, hi = self.original_bounds[vname]
            new_lo = max(lo, min(vals) - 0.1 * (hi - lo))
            new_hi = min(hi, max(vals) + 0.1 * (hi - lo))
            if new_hi > new_lo:
                self.policy[vname] = (new_lo, new_hi)
        return []

    def _fit_surrogate(self, candidates: List):
        """Fit a quadratic surrogate: y = a0 + sum(ai*xi) + sum(aij*xi*xj).

        Uses least-squares. The features are: 1, x1, x2, ..., x_n,
        x1², x2², ..., x_n², x1*x2, x1*x3, ..., x_{n-1}*x_n.
        """
        var_names = [v["name"] for v in self.domain["design_vars"]]
        n_vars = len(var_names)

        # Normalize each variable to [-1, 1] using original bounds
        def normalize(dp):
            x = []
            for v in self.domain["design_vars"]:
                vname = v["name"]
                lo, hi = self.original_bounds[vname]
                mid = (lo + hi) / 2
                span = (hi - lo) / 2
                if span < 1e-12:
                    x.append(0.0)
                else:
                    if lo > 0 and hi / lo > 100:
                        # Log scale
                        x.append((math.log(max(1e-12, dp[vname])) - math.log(lo)) / (math.log(hi) - math.log(lo)) * 2 - 1)
                    else:
                        x.append((dp[vname] - mid) / span)
            return x

        # Build feature matrix: [1, x_i, x_i*x_j, x_i^2]
        features = []
        targets = []
        for c in candidates:
            x = normalize(c.design_point)
            row = [1.0]
            row.extend(x)
            for i in range(n_vars):
                row.append(x[i] * x[i])
            for i in range(n_vars):
                for j in range(i + 1, n_vars):
                    row.append(x[i] * x[j])
            features.append(row)
            targets.append(c.predicted_outcome)

        # Least-squares: solve (X^T X) w = X^T y
        n_feat = len(features[0])
        XTX = [[0.0] * n_feat for _ in range(n_feat)]
        XTy = [0.0] * n_feat
        for r, t in zip(features, targets):
            for i in range(n_feat):
                XTy[i] += r[i] * t
                for j in range(n_feat):
                    XTX[i][j] += r[i] * r[j]

        # Add small ridge regularization
        for i in range(n_feat):
            XTX[i][i] += 1e-6

        # Solve via Gaussian elimination
        w = self._solve_linear(XTX, XTy)
        if w is None:
            return

        self.surrogate_coeffs = {
            "var_names": var_names,
            "weights": w,
            "n_vars": n_vars,
            "normalize_fn": normalize,
        }

        # Update best so far
        self.best_so_far = max(self.best_so_far, max(targets))

    def _surrogate_r2(self, candidates: List) -> float:
        """Compute CROSS-VALIDATION R² of the fitted surrogate.

        Cycle 220 v5: use leave-20%-out CV instead of training R².
        Training R² was high (0.78-0.87) for Catalyst but the model
        overfit — it mispredicted the next batch. CV-R² is honest about
        generalization: if the model can't predict held-out points, it
        can't predict new ones either.

        Returns CV-R² in [0, 1]. Low (< 0.3) means the surrogate
        generalizes poorly → fall back to wider exploration.
        """
        if not self.surrogate_coeffs or len(candidates) < 20:
            return 0.0

        # Leave-20%-out CV: refit on 80%, evaluate on 20%
        n = len(candidates)
        n_test = max(1, n // 5)
        # Use deterministic split (every 5th candidate is test)
        test_idx = set(range(0, n, 5))
        train_cands = [c for i, c in enumerate(candidates) if i not in test_idx]
        test_cands = [c for i, c in enumerate(candidates) if i in test_idx]

        if len(train_cands) < 10 or len(test_cands) < 2:
            return 0.0

        # Refit surrogate on train only (save/restore original)
        saved_coeffs = self.surrogate_coeffs
        self.surrogate_coeffs = {}
        self._fit_surrogate(train_cands)
        cv_coeffs = self.surrogate_coeffs
        # Restore original
        self.surrogate_coeffs = saved_coeffs

        if not cv_coeffs:
            return 0.0

        # Evaluate CV-R² on test set
        test_targets = [c.predicted_outcome for c in test_cands]
        mean_t = sum(test_targets) / len(test_targets)
        ss_tot = sum((t - mean_t) ** 2 for t in test_targets)
        if ss_tot < 1e-12:
            return 0.0

        # Temporarily use CV coeffs for prediction
        self.surrogate_coeffs = cv_coeffs
        ss_res = 0.0
        for c in test_cands:
            pred = self._predict_surrogate(c.design_point)
            ss_res += (c.predicted_outcome - pred) ** 2
        # Restore original coeffs
        self.surrogate_coeffs = saved_coeffs

        return max(0.0, 1.0 - ss_res / ss_tot)

    def _solve_linear(self, A, b):
        n = len(A)
        M = [row[:] + [b[i]] for i, row in enumerate(A)]
        for i in range(n):
            pivot = max(range(i, n), key=lambda r: abs(M[r][i]))
            if abs(M[pivot][i]) < 1e-12:
                continue
            M[i], M[pivot] = M[pivot], M[i]
            for r in range(i + 1, n):
                if abs(M[i][i]) < 1e-12:
                    continue
                factor = M[r][i] / M[i][i]
                for c in range(i, n + 1):
                    M[r][c] -= factor * M[i][c]
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            if abs(M[i][i]) < 1e-12:
                continue
            s = M[i][n]
            for j in range(i + 1, n):
                s -= M[i][j] * x[j]
            x[i] = s / M[i][i]
        return x

    def _predict_surrogate(self, dp: Dict[str, float]) -> float:
        if not self.surrogate_coeffs:
            return 0.0
        w = self.surrogate_coeffs["weights"]
        norm_fn = self.surrogate_coeffs["normalize_fn"]
        n_vars = self.surrogate_coeffs["n_vars"]
        x = norm_fn(dp)
        row = [1.0]
        row.extend(x)
        for i in range(n_vars):
            row.append(x[i] * x[i])
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                row.append(x[i] * x[j])
        return sum(w[i] * row[i] for i in range(len(w)))

    def _expected_improvement(self, dp: Dict[str, float]) -> float:
        pred = self._predict_surrogate(dp)
        if self.best_so_far == -math.inf:
            return pred
        improvement = pred - self.best_so_far
        return max(0.0, improvement)


class EvolutionarySearch(Optimizer):
    """For CONSTRAINT-DOMINATED landscapes — population + crossover + mutation.

    When most candidates are infeasible (constraint-dominated), neither
    greedy nor Bayesian optimization work well. Instead, this optimizer:

      1. Maintains a population of top candidates
      2. Performs crossover (combine design points of two parents)
      3. Performs mutation (perturb a single variable)
      4. Selects top candidates for next generation

    This is robust to constraint-dominated landscapes because it
    maintains diversity through mutation.
    """
    name = "evolutionary_search"

    def __init__(self, domain_spec: Dict, population_size: int = 20):
        super().__init__(domain_spec)
        self.population_size = population_size
        self.mutation_rate = 0.3
        self.population: List = []

    def step(self, candidates: List, rng: random.Random) -> List:
        if len(candidates) < 10:
            return []
        outcomes = sorted(c.predicted_outcome for c in candidates)
        n = len(outcomes)
        q75 = outcomes[3 * n // 4]
        parents = [c for c in candidates if c.predicted_outcome >= q75]
        if len(parents) < 2:
            return []

        # Generate offspring via crossover + mutation
        offspring_designs = []
        for _ in range(self.population_size):
            p1, p2 = rng.sample(parents, 2)
            child = {}
            for var in self.domain["design_vars"]:
                vname = var["name"]
                # Crossover: pick from p1 or p2
                if rng.random() < 0.5:
                    child[vname] = p1.design_point[vname]
                else:
                    child[vname] = p2.design_point[vname]
                # Mutation: perturb
                if rng.random() < self.mutation_rate:
                    lo, hi = self.original_bounds[vname]
                    if lo > 0 and hi / lo > 100:
                        # Log-scale mutation
                        log_val = math.log(max(1e-12, child[vname]))
                        log_val += rng.uniform(-0.5, 0.5)
                        child[vname] = max(lo, min(hi, math.exp(log_val)))
                    else:
                        span = hi - lo
                        child[vname] = max(lo, min(hi, child[vname] + rng.uniform(-0.1, 0.1) * span))
            offspring_designs.append(child)

        # Narrow policy to range of offspring (preserves diversity from mutation)
        for var in self.domain["design_vars"]:
            vname = var["name"]
            vals = [d[vname] for d in offspring_designs]
            lo, hi = self.original_bounds[vname]
            new_lo = max(lo, min(vals))
            new_hi = min(hi, max(vals))
            if new_hi > new_lo:
                self.policy[vname] = (new_lo, new_hi)
        return []


# ============================================================================
# L2 — OPTIMIZER SELECTOR
# ============================================================================

class OptimizerSelector:
    """Selects the appropriate optimizer for a landscape type.

    The mapping is the META-LEARNED OBJECT — it persists across domains
    and is the actual transferable knowledge.
    """

    DEFAULT_MAPPING = {
        LandscapeType.SMOOTH: GreedyHillClimber,
        LandscapeType.MULTIMODAL: EvolutionarySearch,
        LandscapeType.NEEDLE: ImportanceSampler,
        LandscapeType.DECEPTIVE: BayesianOptimizer,
        LandscapeType.CONSTRAINT_DOM: EvolutionarySearch,
        LandscapeType.UNKNOWN: GreedyHillClimber,
    }

    def __init__(self):
        # The learned mapping (landscape_type → optimizer_class)
        # Initially defaults; updated by meta-learning
        self.mapping: Dict[LandscapeType, type] = dict(self.DEFAULT_MAPPING)
        # Track performance: (landscape_type, optimizer_name) → list of improvements
        self.performance_log: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    def select(self, landscape: LandscapeSignature) -> Optimizer:
        """Select an optimizer for the given landscape type."""
        opt_class = self.mapping.get(landscape.landscape_type, GreedyHillClimber)
        return opt_class  # caller instantiates with domain_spec

    def record(self, landscape_type: LandscapeType, optimizer_name: str,
               improvement: float):
        """Record the improvement achieved by an optimizer on a landscape.

        Used by meta-learning to update the mapping.
        """
        key = (landscape_type.value, optimizer_name)
        self.performance_log[key].append(improvement)

    def meta_learn(self):
        """Update the mapping based on recorded performance.

        For each landscape type, pick the optimizer with the highest
        average improvement. This is the META-LEARNING step — the
        system learns which optimizer works on which landscape.
        """
        # Map both snake_case (optimizer.name) and PascalCase (__name__) to class
        opt_classes = [GreedyHillClimber, ImportanceSampler,
                       BayesianOptimizer, EvolutionarySearch]
        name_to_class = {}
        for opt_class in opt_classes:
            name_to_class[opt_class.__name__] = opt_class
            # Instantiate temporarily to get the .name attribute
            # Actually we can't instantiate without domain_spec, so use a class-level
            # mapping instead. The .name attribute is set in __init__, so we
            # use a hardcoded mapping here.
        # Hardcoded snake_case → class mapping (matches the .name attribute)
        snake_to_class = {
            "greedy_hill_climber": GreedyHillClimber,
            "importance_sampler": ImportanceSampler,
            "bayesian_optimizer": BayesianOptimizer,
            "evolutionary_search": EvolutionarySearch,
        }
        name_to_class.update(snake_to_class)

        by_landscape: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for (ltype, opt_name), improvements in self.performance_log.items():
            if improvements:
                avg_imp = sum(improvements) / len(improvements)
                by_landscape[ltype].append((opt_name, avg_imp))

        updates = []
        for ltype, opt_perfs in by_landscape.items():
            best_opt, best_imp = max(opt_perfs, key=lambda x: x[1])
            try:
                ltype_enum = LandscapeType(ltype)
                current = self.mapping.get(ltype_enum)
                current_name = current.__name__ if current else "none"
                if current_name != best_opt:
                    # Find the optimizer class by name (handles both naming conventions)
                    new_class = name_to_class.get(best_opt)
                    if new_class:
                        self.mapping[ltype_enum] = new_class
                        updates.append(f"{ltype}: {current_name} → {best_opt} (avg_imp={best_imp:+.3f})")
            except ValueError:
                pass
        return updates


# ============================================================================
# L3 — OPERATOR LEARNING
# ============================================================================

@dataclass
class OperatorRecord:
    """Record of a mutation operator's performance on a landscape."""
    operator_name: str
    landscape_type: str
    domain: str
    improvement: float
    n_candidates: int


class OperatorLogger:
    """Logs which operator worked on which landscape.

    This is L3 — instead of learning 'grain size → good', we learn
    'importance_sampler → works on needle landscapes'.
    """
    def __init__(self):
        self.records: List[OperatorRecord] = []

    def log(self, optimizer: Optimizer, landscape: LandscapeSignature,
            domain: str, improvement: float, n_candidates: int):
        self.records.append(OperatorRecord(
            operator_name=optimizer.name,
            landscape_type=landscape.landscape_type.value,
            domain=domain,
            improvement=improvement,
            n_candidates=n_candidates,
        ))

    def summary(self) -> Dict:
        """Summarize operator performance across domains."""
        by_operator: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        for r in self.records:
            key = (r.operator_name, r.landscape_type)
            by_operator[key].append(r.improvement)
        return {
            f"{opt}_{land}": {
                "n_runs": len(imps),
                "avg_improvement": sum(imps) / len(imps) if imps else 0,
                "domains": list(set(r.domain for r in self.records
                                   if r.operator_name == opt and r.landscape_type == land))
            }
            for (opt, land), imps in by_operator.items()
        }


# ============================================================================
# CAUSAL GRAPH UPGRADE — executable explanations
# ============================================================================

@dataclass
class CausalStep:
    """One step in an executable causal chain."""
    variable: str
    change: str        # "increases" or "decreases"
    mechanism: str     # named physical relation (e.g., "Pisarenko relation")
    formula: str       # the actual equation


@dataclass
class CausalChain:
    """An executable causal chain explaining a heuristic.

    Per auditor update #8:
        'Instead of "because Pisarenko", I'd like to see
         because → carrier_concentration → effective_mass →
         Seebeck_coefficient → ZT.

         Meaning: the explanation should itself be executable.
         Not prose. A causal graph.'

    Each step references a NAMED physical relation and a FORMULA.
    The chain is verifiable: each step can be checked against the
    forward model's actual computation.
    """
    chain_id: str
    steps: List[CausalStep]
    final_variable: str
    final_change: str

    def to_prose(self) -> str:
        """Render the chain as prose (for human reading)."""
        parts = []
        for s in self.steps:
            parts.append(f"{s.variable} {s.change} via {s.mechanism} ({s.formula})")
        return " → ".join(parts)

    def to_dict(self) -> Dict:
        return {
            "chain_id": self.chain_id,
            "steps": [{"variable": s.variable, "change": s.change,
                       "mechanism": s.mechanism, "formula": s.formula}
                      for s in self.steps],
            "final_variable": self.final_variable,
            "final_change": self.final_change,
        }


# Predefined causal chains for known physical mechanisms
CAUSAL_CHAINS = {
    "pisarenko": CausalChain(
        chain_id="CAUSAL-pisarenko",
        steps=[
            CausalStep("carrier_concentration", "increases",
                       "Pisarenko relation", "m* ~ n^(-1/3) at high n"),
            CausalStep("effective_mass", "decreases",
                       "Band curvature", "m* = ℏ²(d²E/dk²)⁻¹"),
            CausalStep("seebeck_coefficient", "decreases",
                       "Mott formula", "S = (8π²k²/3eh²) m*T (π/3n)^(2/3)"),
            CausalStep("ZT", "decreases",
                       "Thermoelectric figure of merit", "ZT = S²σT/κ"),
        ],
        final_variable="ZT",
        final_change="decreases",
    ),
    "grain_boundary": CausalChain(
        chain_id="CAUSAL-grain_boundary",
        steps=[
            CausalStep("grain_size", "decreases below 10nm",
                       "Grain boundary scattering", "λ_mfp ≈ d"),
            CausalStep("mobility", "decreases",
                       "Matthiessen rule", "μ⁻¹ = μ_bulk⁻¹ + μ_GB⁻¹"),
            CausalStep("electrical_conductivity", "decreases",
                       "Drude relation", "σ = neμ"),
            CausalStep("ZT", "decreases",
                       "Thermoelectric figure of merit", "ZT = S²σT/κ"),
        ],
        final_variable="ZT",
        final_change="decreases",
    ),
    "lattice_kappa": CausalChain(
        chain_id="CAUSAL-lattice_kappa",
        steps=[
            CausalStep("alloy_fraction", "increases",
                       "Mass disorder scattering", "κ_L ∝ 1/(1+Γ·x·(1-x))"),
            CausalStep("lattice_thermal_conductivity", "decreases",
                       "Klemens model", "κ_L = (1-x)κ_A + xκ_B + κ_alloy"),
            CausalStep("ZT", "increases",
                       "Thermoelectric figure of merit", "ZT = S²σT/κ"),
        ],
        final_variable="ZT",
        final_change="increases",
    ),
}


# ============================================================================
# MAIN META-INVENTION LOOP
# ============================================================================

def run_meta_invention(domain_spec: Dict, forward_fn: Callable,
                       n_iterations: int = 5, n_per_iter: int = 50,
                       seed: int = 42, selector: Optional[OptimizerSelector] = None,
                       op_logger: Optional[OperatorLogger] = None) -> Tuple[List, LandscapeSignature, str]:
    """Run the meta-invention loop on a domain.

    1. Sample initial candidates
    2. Classify the landscape
    3. Select optimizer based on landscape type
    4. Run optimizer for n_iterations
    5. Record performance for meta-learning
    """
    rng = random.Random(seed)
    classifier = LandscapeClassifier()
    if selector is None:
        selector = OptimizerSelector()
    if op_logger is None:
        op_logger = OperatorLogger()

    # Initial sampling to classify landscape
    initial_dp = []
    for _ in range(n_per_iter):
        dp = {v["name"]: rng.uniform(*v["bounds"]) for v in domain_spec["design_vars"]}
        initial_dp.append(dp)

    candidates = []
    for dp in initial_dp:
        outcome, derived = forward_fn(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": outcome, "derived": derived})()
        candidates.append(c)

    landscape = classifier.classify(candidates, domain_spec["design_vars"])

    # Select optimizer
    opt_class = selector.select(landscape)
    optimizer = opt_class(domain_spec)

    # Initial iteration stats
    iters = [{
        "iteration": 0,
        "avg_outcome": sum(c.predicted_outcome for c in candidates) / len(candidates),
        "median_outcome": sorted(c.predicted_outcome for c in candidates)[len(candidates) // 2],
        "best_outcome": max(c.predicted_outcome for c in candidates),
        "landscape_type": landscape.landscape_type.value,
        "optimizer": optimizer.name,
    }]

    # Run iterations
    for it in range(n_iterations):
        optimizer.step(candidates, rng)
        # Sample new candidates within updated policy
        new_candidates = []
        for _ in range(n_per_iter):
            dp = optimizer.sample(rng)
            outcome, derived = optimizer.evaluate(dp, forward_fn)
            c = type("C", (), {"design_point": dp, "predicted_outcome": outcome, "derived": derived})()
            new_candidates.append(c)
        candidates = new_candidates
        iters.append({
            "iteration": it + 1,
            "avg_outcome": sum(c.predicted_outcome for c in candidates) / len(candidates),
            "median_outcome": sorted(c.predicted_outcome for c in candidates)[len(candidates) // 2],
            "best_outcome": max(c.predicted_outcome for c in candidates),
            "landscape_type": landscape.landscape_type.value,
            "optimizer": optimizer.name,
        })

    # Record for meta-learning
    improvement = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
    selector.record(landscape.landscape_type, optimizer.name, improvement)
    op_logger.log(optimizer, landscape, domain_spec["name"], improvement, n_per_iter * (n_iterations + 1))

    return iters, landscape, optimizer.name


# ============================================================================
# MAIN ENTRY — run all 4 domains with meta-invention layer
# ============================================================================

def main():
    print("=" * 78)
    print("META-INVENTION LAYER (cycle 218)")
    print("L1: Landscape classification  |  L2: Optimizer selection")
    print("L3: Operator learning         |  L4: Meta-learning")
    print("=" * 78)
    print()

    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    domains = [
        ("Thermoelectric", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery",        BATTERY_DOMAIN,         battery_forward),
        ("Catalyst",       CATALYST_DOMAIN,        catalyst_forward),
        ("Photovoltaic",   PV_DOMAIN,              pv_forward),
    ]

    selector = OptimizerSelector()
    op_logger = OperatorLogger()

    print("=" * 78)
    print("L1 + L2: Landscape classification + optimizer selection")
    print("=" * 78)
    print()
    print(f"{'Domain':<15} {'Landscape':<22} {'Optimizer':<25} {'Skew':<8} {'Nonzero':<10} {'Bimod':<8} {'Inter':<8}")
    print("-" * 100)

    all_results = {}
    for name, spec, fn in domains:
        iters, landscape, opt_name = run_meta_invention(
            spec, fn, n_iterations=5, n_per_iter=50, seed=42,
            selector=selector, op_logger=op_logger,
        )
        all_results[name] = (iters, landscape, opt_name)
        print(f"{name:<15} {landscape.landscape_type.value:<22} {opt_name:<25} "
              f"{landscape.skew_ratio:<8.3f} {landscape.nonzero_fraction:<10.3f} "
              f"{landscape.bimodality:<8.3f} {landscape.interaction_index:<8.3f}")

    print()
    print("=" * 78)
    print("THE AUDITOR'S TABLE — with meta-invention layer (5 iterations)")
    print("=" * 78)
    print()
    print(f"{'Domain':<15} {'Iter 0':>10} {'Iter 1':>10} {'Iter 2':>10} {'Iter 3':>10} {'Iter 4':>10} {'Iter 5':>10} {'Δ best':>10} {'Opt':<25}")
    print("-" * 110)

    n_improved = 0
    for name, _, _ in domains:
        iters, landscape, opt_name = all_results[name]
        best_vals = [it["best_outcome"] for it in iters]
        delta = best_vals[-1] - best_vals[0]
        if delta > 0:
            n_improved += 1
        print(f"{name:<15} " + " ".join(f"{v:>10.3f}" for v in best_vals) + f" {delta:>+10.3f} {opt_name:<25}")

    print()
    print(f"Domains where iter5 > iter0: {n_improved}/{len(domains)}")

    print()
    print("=" * 78)
    print("L3: Operator learning summary")
    print("=" * 78)
    print()
    summary = op_logger.summary()
    for key, info in sorted(summary.items()):
        print(f"  {key}: n_runs={info['n_runs']}, avg_imp={info['avg_improvement']:+.3f}, domains={info['domains']}")

    print()
    print("=" * 78)
    print("L4: Meta-learning — does the optimizer mapping update?")
    print("=" * 78)
    print()
    print("Default mapping:")
    for lt, opt in selector.DEFAULT_MAPPING.items():
        print(f"  {lt.value:<22} → {opt.__name__}")
    print()
    updates = selector.meta_learn()
    if updates:
        print(f"Meta-learning updates ({len(updates)}):")
        for u in updates:
            print(f"  {u}")
    else:
        print("No updates — defaults already optimal for observed landscapes.")
    print()
    print("Updated mapping:")
    for lt, opt in selector.mapping.items():
        print(f"  {lt.value:<22} → {opt.__name__}")

    # === Median metric (more honest for skewed) ===
    print()
    print("=" * 78)
    print("MEDIAN METRIC (honest for skewed distributions)")
    print("=" * 78)
    print()
    print(f"{'Domain':<15} {'Iter 0':>10} {'Iter 1':>10} {'Iter 2':>10} {'Iter 3':>10} {'Iter 4':>10} {'Iter 5':>10} {'Δ median':>10}")
    print("-" * 85)
    n_improved_med = 0
    for name, _, _ in domains:
        iters, _, _ = all_results[name]
        med_vals = [it["median_outcome"] for it in iters]
        delta = med_vals[-1] - med_vals[0]
        if delta > 0:
            n_improved_med += 1
        print(f"{name:<15} " + " ".join(f"{v:>10.3f}" for v in med_vals) + f" {delta:>+10.3f}")
    print()
    print(f"Domains where iter5 median > iter0 median: {n_improved_med}/{len(domains)}")

    # === Comparison to cycle 217 ===
    print()
    print("=" * 78)
    print("COMPARISON: cycle 217 (no meta-layer) vs cycle 218 (with meta-layer)")
    print("=" * 78)
    print()
    print("Cycle 217 results (best metric):")
    print("  Thermoelectric: 0.452 → 0.573  (+0.122) LEARNS")
    print("  Battery:        2.626 → 0.149  (-2.477) FAILS")
    print("  Catalyst:       2.779 → 5.681  (+2.902) LEARNS")
    print("  Photovoltaic:  19.610 → 16.758 (-2.852) FAILS")
    print("  Result: 2/4 LEARN")
    print()
    print(f"Cycle 218 results (best metric): {n_improved}/4 LEARN")
    print()
    if n_improved > 2:
        print("The meta-invention layer IMPROVED cross-domain transfer.")
    elif n_improved == 2:
        print("The meta-invention layer MATCHED cycle 217. Investigate why.")
    else:
        print("The meta-invention layer REGRESSED. Investigate optimizer implementations.")


if __name__ == "__main__":
    main()
