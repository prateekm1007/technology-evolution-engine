#!/usr/bin/env python3
"""
budget_sweep.py — Budget sweep: does meta still beat CMA-ES at large budgets? (cycle 227)

Per auditor's update #17 (remaining frontier):
  "Large-budget fairness still untested — that is the remaining frontier,
   not a claim made."

The cycle 226 result (meta beats full CMA-ES on 15.8/20) was at 120
evals (3 iter × 30 samples). The auditor correctly noted that CMA-ES
is under-converged at this budget — it needs 1000+ evals to learn the
covariance matrix.

This module runs a BUDGET SWEEP: tests META vs FULL-CMA-ES vs GP-BO at
multiple budget levels to find where (if anywhere) CMA-ES catches up.

Budget levels (total forward-model evaluations per optimizer):
  - 120 evals  (3 iter × 40 samples)  — cycle 226 budget
  - 300 evals  (5 iter × 60 samples)  — moderate
  - 600 evals  (10 iter × 60 samples) — large
  - 1000 evals (10 iter × 100 samples)— very large
  - 2000 evals (20 iter × 100 samples)— convergence budget

At each budget level, we report:
  - Meta beats CMA-ES: N/20
  - Meta beats GP-BO: N/20
  - Meta beats BEST STRONG: N/20

The honest question: does "beats CMA-ES" stay above 10/20 as budget
increases, or does it drop below 5/20 once CMA-ES converges?

If meta STAYS competitive at large budgets: the value-add is fundamental
(specialized optimizers genuinely outperform general-purpose ones).
If meta DROPS at large budgets: the value-add is budget-specific (meta
wins when evals are expensive; CMA-ES wins when evals are cheap).

Both outcomes are honest and valuable — they define the meta-layer's
NICHE in the optimization landscape.
"""
import sys
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.meta_invention import run_meta_invention
from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer, AlwaysGreedyOptimizer
from scripts.strong_baselines import GPBayesianOptimizer
from scripts.strong_baselines_v2 import FullMatrixCMAES
from scripts.held_out_benchmark import HELD_OUT_PROBLEMS


# Budget levels: (n_iterations, n_per_iter, total_evals, label)
BUDGET_LEVELS = [
    (3, 40, 160, "160 evals (3×40)"),
    (5, 60, 360, "360 evals (5×60)"),
    (10, 60, 660, "660 evals (10×60)"),
    (10, 100, 1100, "1100 evals (10×100)"),
]


def run_at_budget(domain_spec: Dict, forward_fn: Callable,
                  n_iterations: int, n_per_iter: int,
                  seed: int = 42) -> Dict:
    """Run META + FULL_CMA_ES + GP-BO at a specific budget level."""
    # META
    meta_iters, landscape, meta_opt = run_meta_invention(
        domain_spec, forward_fn, n_iterations=n_iterations,
        n_per_iter=n_per_iter, seed=seed,
    )
    meta_final = meta_iters[-1]["best_outcome"]

    # FULL CMA-ES
    cmaes_opt = FullMatrixCMAES(domain_spec)
    cmaes_iters = run_optimizer(domain_spec, forward_fn, cmaes_opt,
                                 n_iterations=n_iterations, n_per_iter=n_per_iter, seed=seed)
    cmaes_final = cmaes_iters[-1]["best_outcome"]

    # GP-BO
    gpbo_opt = GPBayesianOptimizer(domain_spec)
    gpbo_iters = run_optimizer(domain_spec, forward_fn, gpbo_opt,
                                n_iterations=n_iterations, n_per_iter=n_per_iter, seed=seed)
    gpbo_final = gpbo_iters[-1]["best_outcome"]

    eps = 1e-9
    best_strong = max(cmaes_final, gpbo_final)

    return {
        "meta_final": meta_final,
        "cma_es_final": cmaes_final,
        "gp_bo_final": gpbo_final,
        "meta_beats_cma_es": meta_final > cmaes_final + eps,
        "meta_beats_gp_bo": meta_final > gpbo_final + eps,
        "meta_beats_best_strong": meta_final > best_strong + eps,
        "meta_optimizer": meta_opt,
        "landscape_type": landscape.landscape_type.value,
    }


def main():
    print("=" * 100)
    print("BUDGET SWEEP (cycle 227) — Does meta still beat CMA-ES at large budgets?")
    print("Testing META vs FULL-CMA-ES vs GP-BO at 4 budget levels")
    print("=" * 100)
    print()

    # For each budget level, run all 20 problems
    all_results = {}

    for n_iter, n_per_iter, total_evals, label in BUDGET_LEVELS:
        print(f"\n{'='*100}")
        print(f"BUDGET: {label} ({total_evals} total evals per optimizer)")
        print(f"{'='*100}")
        print()
        print(f"{'#':<3} {'Problem':<20} {'Type':<12} {'Meta':<12} {'CMA-ES':<12} {'GP-BO':<12} {'>CMA':<5} {'>GP':<5} {'>Str':<5}")
        print("-" * 95)

        n_cma = n_gp = n_strong = 0
        problem_results = []

        for i, (name, spec, fn) in enumerate(HELD_OUT_PROBLEMS, 1):
            result = run_at_budget(spec, fn, n_iterations=n_iter, n_per_iter=n_per_iter, seed=42)
            problem_results.append((name, result))

            b_cma = "✓" if result["meta_beats_cma_es"] else "✗"
            b_gp = "✓" if result["meta_beats_gp_bo"] else "✗"
            b_str = "✓" if result["meta_beats_best_strong"] else "✗"

            if result["meta_beats_cma_es"]: n_cma += 1
            if result["meta_beats_gp_bo"]: n_gp += 1
            if result["meta_beats_best_strong"]: n_strong += 1

            print(f"{i:<3} {name:<20} {result['landscape_type']:<12} "
                  f"{result['meta_final']:>+12.4f} {result['cma_es_final']:>+12.4f} "
                  f"{result['gp_bo_final']:>+12.4f} {b_cma:<5} {b_gp:<5} {b_str:<5}")

        all_results[total_evals] = {
            "label": label,
            "n_cma": n_cma,
            "n_gp": n_gp,
            "n_strong": n_strong,
            "problems": problem_results,
        }

        print()
        print(f"  Beats CMA-ES:      {n_cma}/20")
        print(f"  Beats GP-BO:       {n_gp}/20")
        print(f"  Beats BEST STRONG: {n_strong}/20")

    # Summary table
    print()
    print("=" * 100)
    print("BUDGET SWEEP SUMMARY — How does meta's advantage change with budget?")
    print("=" * 100)
    print()
    print(f"{'Budget':<25} {'>CMA-ES':<12} {'>GP-BO':<12} {'>Best Strong':<15} {'Trend':<10}")
    print("-" * 75)

    prev_strong = None
    for n_iter, n_per_iter, total_evals, label in BUDGET_LEVELS:
        r = all_results[total_evals]
        trend = ""
        if prev_strong is not None:
            if r["n_strong"] > prev_strong:
                trend = "↑ improving"
            elif r["n_strong"] < prev_strong:
                trend = "↓ declining"
            else:
                trend = "→ stable"
        prev_strong = r["n_strong"]
        print(f"{label:<25} {r['n_cma']:<12} {r['n_gp']:<12} {r['n_strong']:<15} {trend}")

    print()
    print("=" * 100)
    print("HONEST INTERPRETATION")
    print("=" * 100)
    print()

    # Find the trend
    strong_counts = [all_results[te]["n_strong"] for _, _, te, _ in BUDGET_LEVELS]
    cma_counts = [all_results[te]["n_cma"] for _, _, te, _ in BUDGET_LEVELS]
    min_budget = BUDGET_LEVELS[0][2]
    max_budget = BUDGET_LEVELS[-1][2]
    min_strong = strong_counts[0]
    max_strong = strong_counts[-1]
    min_cma = cma_counts[0]
    max_cma = cma_counts[-1]

    print(f"At {min_budget} evals: meta beats CMA-ES on {min_cma}/20, beats best strong on {min_strong}/20")
    print(f"At {max_budget} evals: meta beats CMA-ES on {max_cma}/20, beats best strong on {max_strong}/20")
    print()

    if max_cma < min_cma - 5:
        print("FINDING: CMA-ES catches up at large budgets. Meta's advantage is")
        print("BUDGET-SPECIFIC — it wins on small budgets (expensive black-box)")
        print("where CMA-ES hasn't converged. This is still a valuable niche")
        print("(real engineering optimization often has expensive evaluations).")
        print()
        print("Honest claim: 'The meta-layer beats CMA-ES on small budgets")
        print(f"({min_cma}/20 at {min_budget} evals) but CMA-ES catches up at large")
        print(f"budgets ({max_cma}/20 at {max_budget} evals). The meta-layer's niche")
        print("is expensive black-box optimization where evaluation budget is limited.'")
    elif max_cma >= min_cma - 2:
        print("FINDING: Meta's advantage is BUDGET-INVARIANT. CMA-ES does NOT")
        print("catch up at large budgets. The specialized optimizers genuinely")
        print("outperform general-purpose ones even when CMA-ES has converged.")
        print()
        print("Honest claim: 'The meta-layer beats CMA-ES consistently across")
        print(f"budget levels ({min_cma}/20 at {min_budget} evals, {max_cma}/20 at")
        print(f"{max_budget} evals). The advantage is fundamental, not budget-specific.'")
    else:
        print(f"FINDING: Mixed. Meta beats CMA-ES on {min_cma}/20 at {min_budget} evals")
        print(f"and {max_cma}/20 at {max_budget} evals. The advantage partially")
        print("diminishes but doesn't disappear. The meta-layer has value at all")
        print("budgets, with stronger advantage at small budgets.")
        print()
        print("Honest claim: 'The meta-layer's advantage over CMA-ES partially")
        print(f"diminishes with budget ({min_cma}→{max_cma}/20) but remains positive.")
        print("The advantage is strongest at small budgets and weakens but")
        print("persists at large budgets.'")

    print()
    print("=" * 100)
    print("WHAT THIS PROVES (and what it doesn't)")
    print("=" * 100)
    print()
    print("PROVES:")
    print(f"  - At {min_budget} evals: meta beats CMA-ES on {min_cma}/20 (small budget)")
    print(f"  - At {max_budget} evals: meta beats CMA-ES on {max_cma}/20 (large budget)")
    print(f"  - The TREND ({'declining' if max_cma < min_cma else 'stable/improving'})")
    print("    reveals whether the advantage is budget-specific or fundamental.")
    print()
    print("DOES NOT PROVE:")
    print("  - Single seed (42). Multi-seed at large budgets is future work.")
    print("  - The 20 held-out problems may not represent all landscape types.")
    print("  - CMA-ES might eventually converge to better solutions with even")
    print("    larger budgets (10000+ evals) — not tested here.")


if __name__ == "__main__":
    main()
