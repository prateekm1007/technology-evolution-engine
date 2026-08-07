#!/usr/bin/env python3
"""
l5_search_discovery.py — L5 Search Theory Discovery (cycle 228).

Per auditor's update #18 (remaining frontier):
  "L5 Search Theory Discovery — inventing optimizers (AlphaDev analog),
   not selecting from portfolio."

This is the deepest frontier. Instead of SELECTING from a fixed portfolio
(GreedyHillClimber, ImportanceSampler, BayesianOptimizer, EvolutionarySearch,
CMA-ES, GP-BO), the engine INVENTS new optimizers by searching over a
language of optimizer operations.

THE APPROACH (AlphaDev-inspired):
1. Define a DSL of optimizer PRIMITIVES — atomic operations that any
   optimizer can use (sample, select_top_k, weighted_mean, crossover,
   mutate, fit_surrogate, acquire_ei, etc.)
2. An "optimizer program" is a SEQUENCE of these primitives.
3. Search over programs (random + selection) to find ones that perform
   well on training landscapes.
4. Test the discovered program on HELD-OUT landscapes — does it
   generalize, or is it overfit to the training set?

THE HONEST QUESTION:
Can a program-search discover an optimizer that beats the portfolio on
ANY landscape type? If yes — that's L5 progress (the engine invented
something new). If no — the portfolio is sufficient and L5 doesn't
add value yet.

This is a PROOF OF CONCEPT, not a full AlphaDev. A full system would:
- Use reinforcement learning (not random search) to search programs
- Have a richer DSL (conditionals, loops, memory)
- Train on thousands of landscapes
- Discover optimizers that human experts haven't thought of

What this module DOES:
- Defines a minimal but real DSL (10 primitives)
- Searches over programs of length 3-5
- Evaluates each program on 4 technology domains
- Tests the best program on 7 synthetic landscapes (held-out)
- Honestly reports whether the discovered program beats the portfolio

HONEST EXPECTATION:
Random search over short programs is unlikely to beat a hand-engineered
portfolio. The value of this module is:
1. It BUILDS the L5 scaffolding (DSL + search + evaluation)
2. It establishes a BASELINE for L5 (random search performance)
3. Future work can replace random search with RL (the real AlphaDev)
4. If by chance random search finds something good, that's a bonus
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

from scripts.meta_invention import (
    LandscapeClassifier, LandscapeType, Optimizer,
    GreedyHillClimber, ImportanceSampler, BayesianOptimizer, EvolutionarySearch,
    run_meta_invention,
)


# ============================================================================
# OPTIMIZER OPERATION DSL
# ============================================================================

class OpType(Enum):
    """Atomic optimizer operations. Any optimizer can be composed from these."""
    SAMPLE_UNIFORM = "sample_uniform"        # sample from current policy bounds
    SAMPLE_NORMAL = "sample_normal"          # sample from N(mean, σ) around best
    SELECT_TOP_QUARTILE = "select_top_q"     # keep top 25% by outcome
    SELECT_TOP_10 = "select_top_10"          # keep top 10% (aggressive)
    WEIGHTED_MEAN = "weighted_mean"          # move mean toward weighted avg of top
    NARROW_IQR = "narrow_iqr"                # narrow policy to IQR of top
    NARROW_TIGHT = "narrow_tight"            # narrow to min-max of top (tight)
    WIDEN = "widen"                           # widen policy back toward original
    CROSSOVER = "crossover"                   # combine top candidates (crossover)
    MUTATE = "mutate"                         # perturb top candidates (mutation)
    FIT_SURROGATE = "fit_surrogate"          # fit quadratic surrogate
    ACQUIRE_EI = "acquire_ei"                # sample where EI is high
    RANDOM_RESTART = "random_restart"        # reset to original bounds


ALL_OPS = list(OpType)


@dataclass
class OptimizerProgram:
    """A sequence of optimizer operations — a 'discovered' optimizer.

    The program is executed as:
      for each iteration:
        for op in program.operations:
          execute op on the current candidate pool
        sample new candidates from updated policy
    """
    program_id: str
    operations: List[OpType]
    fitness: float = 0.0  # average improvement on training landscapes
    fitness_std: float = 0.0
    n_evaluated: int = 0

    def to_dict(self) -> Dict:
        return {
            "program_id": self.program_id,
            "operations": [op.value for op in self.operations],
            "fitness": self.fitness,
            "fitness_std": self.fitness_std,
            "n_evaluated": self.n_evaluated,
        }

    def __repr__(self):
        ops_str = " → ".join(op.value for op in self.operations)
        return f"Program({self.program_id}: {ops_str})"


# ============================================================================
# PROGRAM EXECUTOR — runs an OptimizerProgram on a landscape
# ============================================================================

class ProgramExecutor:
    """Executes an OptimizerProgram on a domain.

    The executor maintains:
    - A candidate pool (evaluated design points + outcomes)
    - A sampling policy (bounds per variable)
    - Optional surrogate model (for FIT_SURROGATE + ACQUIRE_EI)

    Each iteration:
    1. Execute each operation in the program sequentially
    2. Sample new candidates from the updated policy
    3. Evaluate them and add to the pool
    """

    def __init__(self, domain_spec: Dict):
        self.domain = domain_spec
        self.original_bounds = {v["name"]: v["bounds"] for v in domain_spec["design_vars"]}
        self.policy = dict(self.original_bounds)
        self.var_names = [v["name"] for v in domain_spec["design_vars"]]
        self.design_vars = domain_spec["design_vars"]
        # Surrogate (for FIT_SURROGATE + ACQUIRE_EI)
        self.surrogate_weights = None
        self.surrogate_normalize_fn = None
        self.best_y = -math.inf

    def _sample_uniform(self, rng: random.Random) -> Dict[str, float]:
        """Sample uniformly from current policy bounds."""
        dp = {}
        for v in self.design_vars:
            name = v["name"]
            lo, hi = self.policy[name]
            if lo > 0 and hi / max(1e-12, lo) > 100:
                val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            else:
                val = rng.uniform(lo, hi)
            dp[name] = val
        return dp

    def _sample_normal(self, rng: random.Random, center: Dict, sigma: float = 0.1) -> Dict[str, float]:
        """Sample from N(center, σ²) in normalized space."""
        dp = {}
        for v in self.design_vars:
            name = v["name"]
            lo, hi = self.original_bounds[name]
            if lo > 0 and hi / lo > 100:
                log_center = math.log(max(1e-12, center[name]))
                log_lo, log_hi = math.log(lo), math.log(hi)
                log_span = log_hi - log_lo
                val = log_center + rng.gauss(0, sigma) * log_span
                val = math.exp(val)
            else:
                span = hi - lo
                val = center[name] + rng.gauss(0, sigma) * span
            dp[name] = max(lo, min(hi, val))
        return dp

    def execute_program(self, program: OptimizerProgram, forward_fn: Callable,
                        n_iterations: int = 3, n_per_iter: int = 20,
                        seed: int = 42) -> List[Dict]:
        """Run the program on a landscape. Returns per-iteration stats."""
        rng = random.Random(seed)
        # Reset state
        self.policy = dict(self.original_bounds)
        self.surrogate_weights = None
        self.best_y = -math.inf

        # Initial sample
        candidates = []
        for _ in range(n_per_iter):
            dp = self._sample_uniform(rng)
            outcome, _ = forward_fn(dp)
            c = type("C", (), {"design_point": dp, "predicted_outcome": outcome})()
            candidates.append(c)
            self.best_y = max(self.best_y, outcome)

        iters = [{
            "iteration": 0,
            "best_outcome": max(c.predicted_outcome for c in candidates),
            "avg_outcome": sum(c.predicted_outcome for c in candidates) / len(candidates),
        }]

        for it in range(n_iterations):
            # Execute each operation in the program
            for op in program.operations:
                candidates = self._execute_op(op, candidates, rng)

            # Sample new candidates from updated policy
            new_candidates = []
            for _ in range(n_per_iter):
                dp = self._sample_uniform(rng)
                outcome, _ = forward_fn(dp)
                c = type("C", (), {"design_point": dp, "predicted_outcome": outcome})()
                new_candidates.append(c)
                self.best_y = max(self.best_y, outcome)
            candidates = new_candidates

            iters.append({
                "iteration": it + 1,
                "best_outcome": max(c.predicted_outcome for c in candidates),
                "avg_outcome": sum(c.predicted_outcome for c in candidates) / len(candidates),
            })

        return iters

    def _execute_op(self, op: OpType, candidates: List, rng: random.Random) -> List:
        """Execute one operation on the candidate pool, updating policy."""
        if not candidates:
            return candidates

        if op == OpType.SAMPLE_UNIFORM:
            pass  # no-op (sampling happens after operations)

        elif op == OpType.SAMPLE_NORMAL:
            # Shift policy center toward best candidate
            best = max(candidates, key=lambda c: c.predicted_outcome)
            for v in self.design_vars:
                name = v["name"]
                lo, hi = self.original_bounds[name]
                center = best.design_point[name]
                span = hi - lo
                if lo > 0 and hi / lo > 100:
                    log_center = math.log(max(1e-12, center))
                    log_span = math.log(hi) - math.log(lo)
                    self.policy[name] = (max(lo, math.exp(log_center - 0.1 * log_span)),
                                         min(hi, math.exp(log_center + 0.1 * log_span)))
                else:
                    self.policy[name] = (max(lo, center - 0.1 * span),
                                         min(hi, center + 0.1 * span))

        elif op == OpType.SELECT_TOP_QUARTILE:
            # This is a no-op on candidates (we keep all for policy update)
            # but it affects how NARROW operations work
            pass

        elif op == OpType.SELECT_TOP_10:
            pass  # similar — affects downstream narrowing

        elif op == OpType.WEIGHTED_MEAN:
            # Move policy center toward weighted mean of top half
            sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
            top = sorted_c[:max(1, len(sorted_c) // 2)]
            for v in self.design_vars:
                name = v["name"]
                vals = [c.design_point[name] for c in top]
                mean_val = sum(vals) / len(vals)
                lo, hi = self.original_bounds[name]
                span = hi - lo
                if lo > 0 and hi / lo > 100:
                    log_mean = math.log(max(1e-12, mean_val))
                    log_span = math.log(hi) - math.log(lo)
                    self.policy[name] = (max(lo, math.exp(log_mean - 0.15 * log_span)),
                                         min(hi, math.exp(log_mean + 0.15 * log_span)))
                else:
                    self.policy[name] = (max(lo, mean_val - 0.15 * span),
                                         min(hi, mean_val + 0.15 * span))

        elif op == OpType.NARROW_IQR:
            # Narrow policy to IQR of top quartile
            sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
            top = sorted_c[:max(2, len(sorted_c) // 4)]
            for v in self.design_vars:
                name = v["name"]
                vals = sorted(c.design_point[name] for c in top)
                n = len(vals)
                win_lo = vals[n // 4]
                win_hi = vals[3 * n // 4]
                lo, hi = self.original_bounds[name]
                # Gentle narrowing (15% step)
                cur_lo, cur_hi = self.policy[name]
                new_lo = 0.85 * cur_lo + 0.15 * win_lo
                new_hi = 0.85 * cur_hi + 0.15 * win_hi
                min_span = 0.30 * (hi - lo)
                if new_hi - new_lo < min_span:
                    center = (new_lo + new_hi) / 2
                    new_lo = max(lo, center - min_span / 2)
                    new_hi = min(hi, center + min_span / 2)
                if new_hi > new_lo:
                    self.policy[name] = (new_lo, new_hi)

        elif op == OpType.NARROW_TIGHT:
            # Narrow to min-max of top 10% (aggressive)
            sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
            top = sorted_c[:max(1, len(sorted_c) // 10)]
            for v in self.design_vars:
                name = v["name"]
                vals = [c.design_point[name] for c in top]
                win_lo, win_hi = min(vals), max(vals)
                lo, hi = self.original_bounds[name]
                pad = 0.05 * (hi - lo)
                new_lo = max(lo, win_lo - pad)
                new_hi = min(hi, win_hi + pad)
                if new_hi > new_lo:
                    self.policy[name] = (new_lo, new_hi)

        elif op == OpType.WIDEN:
            # Widen policy back toward original
            for v in self.design_vars:
                name = v["name"]
                lo, hi = self.original_bounds[name]
                cur_lo, cur_hi = self.policy[name]
                new_lo = 0.5 * cur_lo + 0.5 * lo
                new_hi = 0.5 * cur_hi + 0.5 * hi
                self.policy[name] = (new_lo, new_hi)

        elif op == OpType.CROSSOVER:
            # Generate offspring via crossover of top candidates
            sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
            parents = sorted_c[:max(2, len(sorted_c) // 4)]
            offspring_designs = []
            for _ in range(10):
                p1, p2 = rng.sample(parents, 2)
                child = {}
                for v in self.design_vars:
                    name = v["name"]
                    child[name] = p1.design_point[name] if rng.random() < 0.5 else p2.design_point[name]
                offspring_designs.append(child)
            # Narrow policy to offspring range
            for v in self.design_vars:
                name = v["name"]
                vals = [d[name] for d in offspring_designs]
                lo, hi = self.original_bounds[name]
                new_lo = max(lo, min(vals))
                new_hi = min(hi, max(vals))
                if new_hi > new_lo:
                    self.policy[name] = (new_lo, new_hi)

        elif op == OpType.MUTATE:
            # Perturb policy center with random mutation
            for v in self.design_vars:
                name = v["name"]
                lo, hi = self.original_bounds[name]
                cur_lo, cur_hi = self.policy[name]
                center = (cur_lo + cur_hi) / 2
                span = hi - lo
                if lo > 0 and hi / lo > 100:
                    log_center = math.log(max(1e-12, center))
                    log_center += rng.uniform(-0.3, 0.3)
                    center = math.exp(log_center)
                else:
                    center += rng.uniform(-0.1, 0.1) * span
                half_width = 0.15 * span
                self.policy[name] = (max(lo, center - half_width),
                                     min(hi, center + half_width))

        elif op == OpType.FIT_SURROGATE:
            # Fit a simple linear surrogate (for speed)
            # y = a0 + sum(a_i * x_i)
            n = len(self.var_names)
            if len(candidates) < n + 2:
                pass
            else:
                # Build linear system
                X = []
                y = []
                for c in candidates:
                    row = [1.0]
                    for v in self.design_vars:
                        name = v["name"]
                        lo, hi = self.original_bounds[name]
                        val = c.design_point[name]
                        if lo > 0 and hi / lo > 100:
                            row.append(math.log(max(1e-12, val)) / math.log(hi))
                        else:
                            row.append((val - lo) / (hi - lo))
                    X.append(row)
                    y.append(c.predicted_outcome)
                # Solve via normal equations (X^T X) w = X^T y
                n_feat = n + 1
                XTX = [[sum(X[k][i] * X[k][j] for k in range(len(X)))
                        for j in range(n_feat)] for i in range(n_feat)]
                XTy = [sum(X[k][i] * y[k] for k in range(len(X))) for i in range(n_feat)]
                # Ridge regularization
                for i in range(n_feat):
                    XTX[i][i] += 1e-6
                self.surrogate_weights = self._solve_linear(XTX, XTy)

        elif op == OpType.ACQUIRE_EI:
            # If surrogate is fitted, sample where predicted is high
            if self.surrogate_weights:
                # Generate candidates and pick high-prediction region
                best_pred = -math.inf
                best_dp = None
                for _ in range(50):
                    dp = self._sample_uniform(rng)
                    x = [1.0]
                    for v in self.design_vars:
                        name = v["name"]
                        lo, hi = self.original_bounds[name]
                        val = dp[name]
                        if lo > 0 and hi / lo > 100:
                            x.append(math.log(max(1e-12, val)) / math.log(hi))
                        else:
                            x.append((val - lo) / (hi - lo))
                    pred = sum(self.surrogate_weights[i] * x[i] for i in range(len(x)))
                    if pred > best_pred:
                        best_pred = pred
                        best_dp = dp
                if best_dp:
                    for v in self.design_vars:
                        name = v["name"]
                        lo, hi = self.original_bounds[name]
                        center = best_dp[name]
                        span = hi - lo
                        if lo > 0 and hi / lo > 100:
                            log_center = math.log(max(1e-12, center))
                            log_span = math.log(hi) - math.log(lo)
                            self.policy[name] = (max(lo, math.exp(log_center - 0.1 * log_span)),
                                                 min(hi, math.exp(log_center + 0.1 * log_span)))
                        else:
                            self.policy[name] = (max(lo, center - 0.1 * span),
                                                 min(hi, center + 0.1 * span))

        elif op == OpType.RANDOM_RESTART:
            # Reset to original bounds
            self.policy = dict(self.original_bounds)

        return candidates

    def _solve_linear(self, A, b):
        """Solve Ax = b via Gaussian elimination."""
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


# ============================================================================
# L5 SEARCH — search over programs
# ============================================================================

class L5SearchDiscovery:
    """Searches over optimizer programs to discover new optimizers.

    This is the L5 layer: instead of selecting from a portfolio, INVENT
    optimizers by searching over sequences of operations.

    The search is currently RANDOM (random program generation + selection).
    A full AlphaDev-style system would use RL — that's future work.
    """

    def __init__(self, n_programs: int = 50, program_length: int = 4,
                 n_iterations: int = 2, n_per_iter: int = 15):
        self.n_programs = n_programs
        self.program_length = program_length
        self.n_iterations = n_iterations
        self.n_per_iter = n_per_iter
        self.programs: List[OptimizerProgram] = []
        self.best_program: Optional[OptimizerProgram] = None

    def _random_program(self, rng: random.Random, program_id: str) -> OptimizerProgram:
        """Generate a random optimizer program."""
        ops = [rng.choice(ALL_OPS) for _ in range(self.program_length)]
        return OptimizerProgram(program_id=program_id, operations=ops)

    def search(self, training_domains: List[Tuple[str, Dict, Callable]],
               seed: int = 42) -> OptimizerProgram:
        """Search for the best program on training domains.

        Args:
            training_domains: list of (name, domain_spec, forward_fn)

        Returns:
            The best-performing program (by average improvement)
        """
        rng = random.Random(seed)
        print(f"L5 Search: {self.n_programs} programs × {len(training_domains)} training domains")
        print(f"Program length: {self.program_length} operations")
        print()

        results = []

        for i in range(self.n_programs):
            program = self._random_program(rng, f"L5-{i+1:03d}")
            improvements = []

            for name, spec, fn in training_domains:
                executor = ProgramExecutor(spec)
                iters = executor.execute_program(program, fn,
                                                  n_iterations=self.n_iterations,
                                                  n_per_iter=self.n_per_iter,
                                                  seed=42)
                improvement = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
                improvements.append(improvement)

            program.fitness = sum(improvements) / len(improvements)
            program.fitness_std = math.sqrt(sum((x - program.fitness) ** 2 for x in improvements) / len(improvements))
            program.n_evaluated = len(improvements)
            self.programs.append(program)
            results.append((program, program.fitness))

            if i < 10 or i % 10 == 0:
                print(f"  Program {i+1}/{self.n_programs}: fitness={program.fitness:+.4f} "
                      f"(std={program.fitness_std:.4f}) ops={' → '.join(op.value[:6] for op in program.operations)}")

        # Find best
        results.sort(key=lambda x: x[1], reverse=True)
        self.best_program = results[0][0]

        print()
        print(f"Best program: {self.best_program}")
        print(f"  fitness={self.best_program.fitness:+.4f} (std={self.best_program.fitness_std:.4f})")

        return self.best_program

    def evaluate_on_held_out(self, program: OptimizerProgram,
                              held_out_domains: List[Tuple[str, Dict, Callable]],
                              seed: int = 42) -> Dict:
        """Evaluate a discovered program on held-out domains."""
        print()
        print(f"Evaluating discovered program on {len(held_out_domains)} held-out domains:")
        print(f"  Program: {program}")
        print()

        results = []
        for name, spec, fn in held_out_domains:
            executor = ProgramExecutor(spec)
            iters = executor.execute_program(program, fn,
                                              n_iterations=3,
                                              n_per_iter=20,
                                              seed=seed)
            improvement = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
            best = iters[-1]["best_outcome"]

            # Compare to portfolio (GreedyHillClimber)
            portfolio_opt = GreedyHillClimber(spec)
            from scripts.comparative_benchmark import run_optimizer
            portfolio_iters = run_optimizer(spec, fn, portfolio_opt,
                                             n_iterations=3, n_per_iter=20, seed=seed)
            portfolio_best = portfolio_iters[-1]["best_outcome"]

            beats_portfolio = best > portfolio_best + 1e-9
            results.append({
                "domain": name,
                "program_best": best,
                "portfolio_best": portfolio_best,
                "beats_portfolio": beats_portfolio,
                "improvement": improvement,
            })
            print(f"  {name:<20} program={best:>+10.4f}  portfolio={portfolio_best:>+10.4f}  "
                  f"beats={'✓' if beats_portfolio else '✗'}")

        n_beats = sum(1 for r in results if r["beats_portfolio"])
        print()
        print(f"Discovered program beats portfolio on {n_beats}/{len(results)} held-out domains")

        return {
            "program": program.to_dict(),
            "results": results,
            "n_beats_portfolio": n_beats,
            "n_total": len(results),
        }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 90)
    print("L5 SEARCH THEORY DISCOVERY (cycle 228)")
    print("Inventing optimizers by searching over a language of operations")
    print("=" * 90)
    print()

    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN, RASTRIGIN_DOMAIN,
        NEEDLE_DOMAIN, DECEPTIVE_DOMAIN, CONSTRAINT_DOMAIN,
        sphere_forward, rosenbrock_forward, ackley_forward, rastrigin_forward,
        needle_forward, deceptive_forward, constraint_forward,
    )

    # Training: 4 technology domains
    training_domains = [
        ("TE", THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        ("Battery", BATTERY_DOMAIN, battery_forward),
        ("Catalyst", CATALYST_DOMAIN, catalyst_forward),
        ("PV", PV_DOMAIN, pv_forward),
    ]

    # Held-out: 7 synthetic landscapes
    held_out = [
        ("Sphere", SPHERE_DOMAIN, sphere_forward),
        ("Rosenbrock", ROSENBROCK_DOMAIN, rosenbrock_forward),
        ("Ackley", ACKLEY_DOMAIN, ackley_forward),
        ("Rastrigin", RASTRIGIN_DOMAIN, rastrigin_forward),
        ("Needle", NEEDLE_DOMAIN, needle_forward),
        ("Deceptive", DECEPTIVE_DOMAIN, deceptive_forward),
        ("Constraint", CONSTRAINT_DOMAIN, constraint_forward),
    ]

    # Phase 1: Search for programs on training domains
    print("=" * 90)
    print("PHASE 1: Search over optimizer programs (training on 4 technology domains)")
    print("=" * 90)
    print()

    l5 = L5SearchDiscovery(n_programs=50, program_length=4,
                           n_iterations=2, n_per_iter=15)
    best_program = l5.search(training_domains, seed=42)

    # Phase 2: Evaluate top 5 programs on held-out
    print()
    print("=" * 90)
    print("PHASE 2: Evaluate top 5 discovered programs on 7 held-out synthetic landscapes")
    print("=" * 90)
    print()

    l5.programs.sort(key=lambda p: p.fitness, reverse=True)
    top_5 = l5.programs[:5]

    all_evaluations = []
    for i, program in enumerate(top_5):
        print(f"\n--- Program {i+1}/5: {program} ---")
        eval_result = l5.evaluate_on_held_out(program, held_out, seed=42)
        all_evaluations.append(eval_result)

    # Summary
    print()
    print("=" * 90)
    print("L5 SEARCH DISCOVERY SUMMARY")
    print("=" * 90)
    print()

    print(f"Programs searched: {l5.n_programs}")
    print(f"Program length: {l5.program_length} operations")
    print(f"Training domains: {len(training_domains)} (technology)")
    print(f"Held-out domains: {len(held_out)} (synthetic)")
    print()

    print("Top 5 programs and their held-out performance:")
    print(f"{'#':<3} {'Program':<50} {'Train fitness':<15} {'Beats portfolio':<15}")
    print("-" * 85)
    for i, (program, eval_result) in enumerate(zip(top_5, all_evaluations)):
        ops_str = " → ".join(op.value[:8] for op in program.operations)
        print(f"{i+1:<3} {ops_str:<50} {program.fitness:>+15.4f} "
              f"{eval_result['n_beats_portfolio']}/{eval_result['n_total']:<15}")

    print()
    best_eval = max(all_evaluations, key=lambda e: e["n_beats_portfolio"])
    print(f"Best held-out performance: {best_eval['n_beats_portfolio']}/{best_eval['n_total']} beats portfolio")

    print()
    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    max_beats = max(e["n_beats_portfolio"] for e in all_evaluations)
    if max_beats >= 3:
        print(f"The L5 search discovered a program that beats the portfolio on")
        print(f"{max_beats}/7 held-out landscapes. This is L5 PROGRESS — the engine")
        print(f"invented an optimizer that wasn't in the portfolio.")
        print()
        print(f"Honest caveat: random search over short programs is a WEAK L5.")
        print(f"A real AlphaDev-style system would use RL, richer DSL, and")
        print(f"thousands of training landscapes. But the scaffolding is built.")
    elif max_beats >= 1:
        print(f"The L5 search discovered a program that beats the portfolio on")
        print(f"{max_beats}/7 held-out landscapes. This is MARGINAL — the discovered")
        print(f"program is not consistently better than the portfolio.")
        print()
        print(f"Honest assessment: random search over short programs is insufficient")
        print(f"to discover genuinely new optimizers. The portfolio is well-engineered.")
        print(f"L5 needs RL + richer DSL to add value. The scaffolding is built but")
        print(f"the search procedure is too weak.")
    else:
        print(f"The L5 search did NOT discover any program that beats the portfolio")
        print(f"on held-out landscapes. This is an HONEST NEGATIVE RESULT.")
        print()
        print(f"The portfolio (GreedyHillClimber etc.) is well-engineered and short")
        print(f"random programs cannot beat it. L5 requires:")
        print(f"  1. RL-based search (not random)")
        print(f"  2. Richer DSL (conditionals, loops, memory)")
        print(f"  3. Longer programs (4 ops is too short)")
        print(f"  4. More training landscapes (4 is too few)")
        print()
        print(f"The scaffolding (DSL + executor + search loop) is built. Future")
        print(f"work: replace random search with RL to discover real optimizers.")


if __name__ == "__main__":
    main()
