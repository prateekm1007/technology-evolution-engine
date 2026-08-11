#!/usr/bin/env python3
"""
synthetic_landscapes.py — Classic optimization test functions as landscapes (cycle 220).

Per auditor update #10 (priority #3):
  "Synthetic-landscape benchmark: prove the meta-layer classifies a real
   hidden function (Rosenbrock/Ackley/Rastrigin/convex/needle) it's never
   seen, with no technology identity."

This module implements 7 classic optimization test functions as
DomainAgnosticLearner-compatible landscapes. Each is a pure math function
with NO domain identity — no "thermoelectric", no "battery", no "catalyst".
Just (x_1, x_2, ..., x_n) → scalar.

The test: does the meta-invention layer correctly classify each landscape
and select an appropriate optimizer, WITHOUT any domain knowledge?

Expected classifications:
  Sphere         → SMOOTH          (convex, single global min)
  Rosenbrock     → SMOOTH          (narrow valley, but smooth)
  Ackley         → MULTIMODAL      (many local minima, one global)
  Rastrigin      → MULTIMODAL      (periodic local minima)
  Needle         → NEEDLE          (sharp spike in flat landscape)
  Deceptive      → DECEPTIVE       (false optimum far from true)
  Constraint_dom → CONSTRAINT_DOM  (most points infeasible → 0)

Each landscape is wrapped in the same domain_spec format as the technology
domains, so DomainAgnosticLearner can run on them without modification.

Note: all landscapes are MINIMIZED in the literature. We NEGATE them so
that "higher = better" matches the engine's convention (predicted_outcome
is what we maximize).
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ============================================================================
# Landscape 1: SPHERE (smooth convex)
# ============================================================================

SPHERE_DOMAIN = {
    "name": "synthetic_sphere",
    "outcome_name": "neg_sphere",
    "outcome_target": -0.01,
    "design_vars": [
        {"name": "x1", "bounds": (-5.0, 5.0), "human": "x1"},
        {"name": "x2", "bounds": (-5.0, 5.0), "human": "x2"},
        {"name": "x3", "bounds": (-5.0, 5.0), "human": "x3"},
        {"name": "x4", "bounds": (-5.0, 5.0), "human": "x4"},
    ],
    "conditions": [],
}


def sphere_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Sphere function: f(x) = sum(x_i^2). Global min = 0 at origin.
    We return -f(x) so higher = better (best = 0)."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    val = sum(xi ** 2 for xi in x)
    return -val, {"sum_squares": val, "norm": math.sqrt(val)}


# ============================================================================
# Landscape 2: ROSENBROCK (smooth but narrow valley)
# ============================================================================

ROSENBROCK_DOMAIN = {
    "name": "synthetic_rosenbrock",
    "outcome_name": "neg_rosenbrock",
    "outcome_target": -1.0,
    "design_vars": [
        {"name": "x1", "bounds": (-2.0, 2.0), "human": "x1"},
        {"name": "x2", "bounds": (-2.0, 2.0), "human": "x2"},
        {"name": "x3", "bounds": (-2.0, 2.0), "human": "x3"},
        {"name": "x4", "bounds": (-2.0, 2.0), "human": "x4"},
    ],
    "conditions": [],
}


def rosenbrock_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Rosenbrock: f(x) = sum(100*(x_{i+1}-x_i^2)^2 + (1-x_i)^2).
    Global min = 0 at (1,1,...,1). We return -f(x)."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    val = sum(100 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2 for i in range(3))
    return -val, {"rosenbrock_val": val}


# ============================================================================
# Landscape 3: ACKLEY (multimodal with many local minima)
# ============================================================================

ACKLEY_DOMAIN = {
    "name": "synthetic_ackley",
    "outcome_name": "neg_ackley",
    "outcome_target": -1.0,
    "design_vars": [
        {"name": "x1", "bounds": (-5.0, 5.0), "human": "x1"},
        {"name": "x2", "bounds": (-5.0, 5.0), "human": "x2"},
        {"name": "x3", "bounds": (-5.0, 5.0), "human": "x3"},
        {"name": "x4", "bounds": (-5.0, 5.0), "human": "x4"},
    ],
    "conditions": [],
}


def ackley_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Ackley function: many local minima, one global at origin.
    f(x) = -20*exp(-0.2*sqrt(sum(x^2)/n)) - exp(sum(cos(2*pi*x))/n) + 20 + e
    Global min = 0 at origin. We return -f(x)."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    n = len(x)
    sum_sq = sum(xi ** 2 for xi in x) / n
    sum_cos = sum(math.cos(2 * math.pi * xi) for xi in x) / n
    val = -20 * math.exp(-0.2 * math.sqrt(sum_sq)) - math.exp(sum_cos) + 20 + math.e
    return -val, {"ackley_val": val, "sum_sq_component": sum_sq, "cos_component": sum_cos}


# ============================================================================
# Landscape 4: RASTRIGIN (multimodal, periodic)
# ============================================================================

RASTRIGIN_DOMAIN = {
    "name": "synthetic_rastrigin",
    "outcome_name": "neg_rastrigin",
    "outcome_target": -1.0,
    "design_vars": [
        {"name": "x1", "bounds": (-5.12, 5.12), "human": "x1"},
        {"name": "x2", "bounds": (-5.12, 5.12), "human": "x2"},
        {"name": "x3", "bounds": (-5.12, 5.12), "human": "x3"},
        {"name": "x4", "bounds": (-5.12, 5.12), "human": "x4"},
    ],
    "conditions": [],
}


def rastrigin_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Rastrigin: f(x) = 10*n + sum(x_i^2 - 10*cos(2*pi*x_i)).
    Global min = 0 at origin. Highly multimodal. We return -f(x)."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    n = len(x)
    val = 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)
    return -val, {"rastrigin_val": val}


# ============================================================================
# Landscape 5: NEEDLE (sharp spike in flat landscape)
# ============================================================================

NEEDLE_DOMAIN = {
    "name": "synthetic_needle",
    "outcome_name": "needle_value",
    "outcome_target": 0.9,
    "design_vars": [
        {"name": "x1", "bounds": (-1.0, 1.0), "human": "x1"},
        {"name": "x2", "bounds": (-1.0, 1.0), "human": "x2"},
        {"name": "x3", "bounds": (-1.0, 1.0), "human": "x3"},
        {"name": "x4", "bounds": (-1.0, 1.0), "human": "x4"},
    ],
    "conditions": [],
}


def needle_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Needle: returns 1.0 only if all |x_i| < 0.05, else returns 0.001.
    Most candidates produce ~0, success is rare. Classic needle-in-haystack."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    if all(abs(xi) < 0.05 for xi in x):
        return 1.0, {"in_needle": 1.0}
    return 0.001, {"in_needle": 0.0}


# ============================================================================
# Landscape 6: DECEPTIVE (false optimum far from true)
# ============================================================================

DECEPTIVE_DOMAIN = {
    "name": "synthetic_deceptive",
    "outcome_name": "deceptive_value",
    "outcome_target": 1.0,
    "design_vars": [
        {"name": "x1", "bounds": (0.0, 1.0), "human": "x1"},
        {"name": "x2", "bounds": (0.0, 1.0), "human": "x2"},
        {"name": "x3", "bounds": (0.0, 1.0), "human": "x3"},
        {"name": "x4", "bounds": (0.0, 1.0), "human": "x4"},
    ],
    "conditions": [],
}


def deceptive_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Deceptive: a local optimum at (0.5, 0.5, 0.5, 0.5) gives 0.6,
    but the global optimum at (0.0, 0.0, 0.0, 0.0) gives 1.0.
    Most random samples land near 0.5 and see only the local optimum."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    dist_local = math.sqrt(sum((xi - 0.5) ** 2 for xi in x))
    dist_global = math.sqrt(sum(xi ** 2 for xi in x))

    # Local optimum: high value at distance 0 from (0.5, 0.5, 0.5, 0.5)
    local_value = 0.6 * math.exp(-10 * dist_local ** 2)
    # Global optimum: very high value at distance 0 from origin
    global_value = 1.0 * math.exp(-50 * dist_global ** 2)

    return max(local_value, global_value), {
        "local_component": local_value,
        "global_component": global_value,
        "dist_to_local": dist_local,
        "dist_to_global": dist_global,
    }


# ============================================================================
# Landscape 7: CONSTRAINT-DOMINATED (most candidates infeasible)
# ============================================================================

CONSTRAINT_DOMAIN = {
    "name": "synthetic_constraint",
    "outcome_name": "constraint_value",
    "outcome_target": 1.0,
    "design_vars": [
        {"name": "x1", "bounds": (-1.0, 1.0), "human": "x1"},
        {"name": "x2", "bounds": (-1.0, 1.0), "human": "x2"},
        {"name": "x3", "bounds": (-1.0, 1.0), "human": "x3"},
        {"name": "x4", "bounds": (-1.0, 1.0), "human": "x4"},
    ],
    "conditions": [],
}


def constraint_forward(design_point: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Constraint-dominated: feasible only if sum(x_i^2) < 0.1 (inside
    a small ball). Most candidates are infeasible (return 0). Feasible
    candidates get a value based on distance from origin."""
    x = [design_point[f"x{i+1}"] for i in range(4)]
    norm_sq = sum(xi ** 2 for xi in x)
    if norm_sq < 0.1:
        # Feasible: high value, peaks at origin
        return 1.0 - norm_sq, {"feasible": 1.0, "norm_sq": norm_sq}
    return 0.0, {"feasible": 0.0, "norm_sq": norm_sq}


# ============================================================================
# Expected classifications (ground truth from optimization literature)
# ============================================================================

EXPECTED_CLASSIFICATIONS = {
    "synthetic_sphere":     "smooth",       # convex, single global min
    "synthetic_rosenbrock": "smooth",       # narrow valley but smooth gradient
    "synthetic_ackley":     "multimodal",   # many local minima
    "synthetic_rastrigin":  "multimodal",   # periodic local minima
    "synthetic_needle":     "needle",       # sharp spike in flat landscape
    "synthetic_deceptive":  "deceptive",    # false optimum far from true
    "synthetic_constraint": "constraint_dominated",  # most infeasible
}


ALL_SYNTHETIC_DOMAINS = [
    ("Sphere",     SPHERE_DOMAIN,     sphere_forward),
    ("Rosenbrock", ROSENBROCK_DOMAIN, rosenbrock_forward),
    ("Ackley",     ACKLEY_DOMAIN,     ackley_forward),
    ("Rastrigin",  RASTRIGIN_DOMAIN,  rastrigin_forward),
    ("Needle",     NEEDLE_DOMAIN,     needle_forward),
    ("Deceptive",  DECEPTIVE_DOMAIN,  deceptive_forward),
    ("Constraint", CONSTRAINT_DOMAIN, constraint_forward),
]


def main():
    """Run the meta-invention layer on all 7 synthetic landscapes.

    The test: does the meta-layer correctly classify each landscape
    and select an appropriate optimizer, WITHOUT any domain knowledge?

    These are PURE MATH functions — no thermoelectric, no battery, no
    catalyst. If the meta-layer works here, it's genuinely domain-invariant.
    """
    from scripts.meta_invention import (
        run_meta_invention, OptimizerSelector, OperatorLogger,
        LandscapeClassifier,
    )

    print("=" * 78)
    print("SYNTHETIC-LANDSCAPE BENCHMARK (cycle 220)")
    print("Tests domain-invariance: 7 classic optimization functions")
    print("with NO technology identity. Pure math.")
    print("=" * 78)
    print()

    selector = OptimizerSelector()
    op_logger = OperatorLogger()
    classifier = LandscapeClassifier()

    print(f"{'Landscape':<14} {'Expected':<22} {'Classified':<22} {'Match':<8} {'Optimizer':<25} {'Iter0 best':<12} {'Iter5 best':<12} {'Δ':<10}")
    print("-" * 130)

    n_classified_correct = 0
    n_improved = 0
    all_results = {}

    for name, spec, fn in ALL_SYNTHETIC_DOMAINS:
        expected = EXPECTED_CLASSIFICATIONS[spec["name"]]

        # Initial sample to classify
        rng = random.Random(42)
        initial_cands = []
        for _ in range(50):
            dp = {}
            for v in spec["design_vars"]:
                lo, hi = v["bounds"]
                if lo > 0 and hi / lo > 100:
                    val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
                else:
                    val = rng.uniform(lo, hi)
                dp[v["name"]] = val
            outcome, derived = fn(dp)
            c = type("C", (), {"design_point": dp, "predicted_outcome": outcome, "derived": derived})()
            initial_cands.append(c)

        landscape = classifier.classify(initial_cands, spec["design_vars"])
        classified = landscape.landscape_type.value
        match = "✓" if classified == expected else "✗"
        if classified == expected:
            n_classified_correct += 1

        # Run meta-invention
        iters, _, opt_name = run_meta_invention(
            spec, fn, n_iterations=5, n_per_iter=50, seed=42,
            selector=selector, op_logger=op_logger,
        )
        all_results[name] = (iters, classified, opt_name)
        delta = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
        if delta > 0:
            n_improved += 1

        print(f"{name:<14} {expected:<22} {classified:<22} {match:<8} {opt_name:<25} "
              f"{iters[0]['best_outcome']:>+12.4f} {iters[-1]['best_outcome']:>+12.4f} {delta:>+10.4f}")

    print()
    print(f"Classification accuracy: {n_classified_correct}/7")
    print(f"Domains improved (iter5 > iter0): {n_improved}/7")
    print()

    # === Auditor's table ===
    print("=" * 78)
    print("THE AUDITOR'S TABLE — Iter1..Iter5 across 7 synthetic landscapes")
    print("=" * 78)
    print()
    print(f"{'Landscape':<14} {'Iter 0':>10} {'Iter 1':>10} {'Iter 2':>10} {'Iter 3':>10} {'Iter 4':>10} {'Iter 5':>10} {'Δ best':>10}")
    print("-" * 85)
    for name, _, _ in ALL_SYNTHETIC_DOMAINS:
        iters, _, _ = all_results[name]
        best_vals = [it["best_outcome"] for it in iters]
        delta = best_vals[-1] - best_vals[0]
        print(f"{name:<14} " + " ".join(f"{v:>10.4f}" for v in best_vals) + f" {delta:>+10.4f}")

    print()
    print("=" * 78)
    print("HONEST INTERPRETATION")
    print("=" * 78)
    print()
    print("1. Domain-invariance test:")
    print(f"   - {n_classified_correct}/7 landscapes classified correctly")
    print(f"   - {n_improved}/7 landscapes improved by the meta-layer")
    print("   - These are PURE MATH functions with no technology identity.")
    print("   - If classification ≥5/7 and improvement ≥5/7, the meta-layer")
    print("     is genuinely domain-invariant (not just TE-tuned).")
    print()
    print("2. What this rules out:")
    print("   - The meta-layer is NOT relying on technology-specific features")
    print("     (no 'thermoelectric' keyword, no material database).")
    print("   - The landscape classifier works on STATISTICAL SIGNATURES")
    print("     (skew, bimodality, interaction) that are domain-invariant.")
    print()
    print("3. What this does NOT prove:")
    print("   - It does not prove the meta-layer is universally general.")
    print("   - The 7 synthetic landscapes cover common archetypes but not all")
    print("     possible landscape types.")
    print("   - Real-world landscapes may have structure not captured here.")


if __name__ == "__main__":
    main()
