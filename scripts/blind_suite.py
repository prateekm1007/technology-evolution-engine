#!/usr/bin/env python3
"""
blind_suite.py — Blind benchmark suite for L5a (cycle 229).

Per auditor's update #19:
  "Take 20 completely unrelated optimization problems (Ackley,
   Rosenbrock, TSP, SAT, Job Shop, Portfolio Optimization, Bayesian
   hyperparameter tuning, Circuit placement, Protein toy folding,
   Symbolic regression, etc.). Hide their names. Only expose
   sample() and evaluate() to the engine."

The key property: the engine sees ONLY sample() and evaluate(). It
does not know whether it's optimizing a math function, a combinatorial
problem, or an engineering simulation. If L5a discovers programs that
work across this blind suite, the search machinery is learning
optimization STRATEGIES, not exploiting domain characteristics.

This module implements 20 blind problems:
  1-7:   Synthetic continuous (Ackley, Rosenbrock, etc.) — wrapped
         to hide their identity
  8-12:  Discrete/combinatorial (TSP, SAT, Knapsack, Bin Packing,
         Job Shop) — encoded as continuous → discrete
  13-16: Engineering surrogate (circuit placement, portfolio,
         hyperparameter, protein folding) — simplified models
  17-20: Hybrid (symbolic regression, neural architecture, control,
         scheduling) — mixed continuous/discrete

Each problem exposes:
  - sample(): returns a random design point (continuous encoding)
  - evaluate(dp): returns a scalar outcome (higher = better)
  - bounds: the search space bounds

The engine NEVER sees the problem name or type. It only sees
sample() → evaluate() → outcome.
"""
import sys
import math
import random
from typing import Dict, Tuple, Callable, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ============================================================================
# BLIND PROBLEM WRAPPER
# ============================================================================

class BlindProblem:
    """A blind optimization problem. Only exposes sample() and evaluate().

    The problem's NAME and TYPE are hidden. The engine sees only:
    - bounds: the search space
    - sample(): random design point
    - evaluate(dp): scalar outcome (higher = better)
    """

    def __init__(self, problem_id: str, bounds: Dict[str, Tuple[float, float]],
                 evaluate_fn: Callable, sample_fn: Callable = None):
        self.problem_id = problem_id  # "BLIND-001" etc — NO domain name
        self.bounds = bounds
        self._evaluate_fn = evaluate_fn
        self._sample_fn = sample_fn
        # Domain spec format (for compatibility with existing optimizers)
        self.design_vars = [
            {"name": name, "bounds": b, "human": name}
            for name, b in bounds.items()
        ]

    def sample(self, rng: random.Random) -> Dict[str, float]:
        """Sample a random design point."""
        if self._sample_fn:
            return self._sample_fn(rng)
        dp = {}
        for name, (lo, hi) in self.bounds.items():
            if lo > 0 and hi / lo > 100:
                dp[name] = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            else:
                dp[name] = rng.uniform(lo, hi)
        return dp

    def evaluate(self, dp: Dict[str, float]) -> float:
        """Evaluate a design point. Returns scalar (higher = better)."""
        return self._evaluate_fn(dp)

    def to_domain_spec(self) -> Dict:
        """Convert to domain_spec format for compatibility."""
        return {
            "name": self.problem_id,
            "outcome_name": "outcome",
            "outcome_target": 0.0,
            "design_vars": self.design_vars,
            "conditions": [],
        }

    def forward(self, dp: Dict[str, float]) -> Tuple[float, Dict]:
        """Forward function (for compatibility with run_meta_invention)."""
        outcome = self.evaluate(dp)
        return outcome, {}


# ============================================================================
# 20 BLIND PROBLEMS
# ============================================================================

def _make_blind_suite() -> List[BlindProblem]:
    """Build 20 blind problems. Names are hidden — only BLIND-001..020."""

    problems = []

    # --- 1-7: Synthetic continuous (identity hidden) ---
    # 1. Ackley (multimodal)
    p1_bounds = {f"x{i}": (-5.0, 5.0) for i in range(4)}
    def p1_eval(dp):
        x = [dp[f"x{i}"] for i in range(4)]
        n = len(x)
        sum_sq = sum(xi**2 for xi in x) / n
        sum_cos = sum(math.cos(2*math.pi*xi) for xi in x) / n
        val = -20*math.exp(-0.2*math.sqrt(sum_sq)) - math.exp(sum_cos) + 20 + math.e
        return -val
    problems.append(BlindProblem("BLIND-001", p1_bounds, p1_eval))

    # 2. Rosenbrock (smooth valley)
    p2_bounds = {f"x{i}": (-2.0, 2.0) for i in range(4)}
    def p2_eval(dp):
        x = [dp[f"x{i}"] for i in range(4)]
        val = sum(100*(x[i+1]-x[i]**2)**2 + (1-x[i])**2 for i in range(3))
        return -val
    problems.append(BlindProblem("BLIND-002", p2_bounds, p2_eval))

    # 3. Rastrigin (periodic multimodal)
    p3_bounds = {f"x{i}": (-5.12, 5.12) for i in range(4)}
    def p3_eval(dp):
        x = [dp[f"x{i}"] for i in range(4)]
        n = len(x)
        val = 10*n + sum(xi**2 - 10*math.cos(2*math.pi*xi) for xi in x)
        return -val
    problems.append(BlindProblem("BLIND-003", p3_bounds, p3_eval))

    # 4. Sphere (smooth convex)
    p4_bounds = {f"x{i}": (-5.0, 5.0) for i in range(4)}
    def p4_eval(dp):
        return -sum(dp[f"x{i}"]**2 for i in range(4))
    problems.append(BlindProblem("BLIND-004", p4_bounds, p4_eval))

    # 5. Beale (2D irregular)
    p5_bounds = {"a": (-4.5, 4.5), "b": (-4.5, 4.5)}
    def p5_eval(dp):
        a, b = dp["a"], dp["b"]
        val = (1.5-a+a*b)**2 + (2.25-a+a*b**2)**2 + (2.625-a+a*b**3)**2
        return -val
    problems.append(BlindProblem("BLIND-005", p5_bounds, p5_eval))

    # 6. Easom (needle)
    p6_bounds = {"x": (-10, 10), "y": (-10, 10)}
    def p6_eval(dp):
        x, y = dp["x"], dp["y"]
        val = -math.cos(x)*math.cos(y)*math.exp(-((x-math.pi)**2 + (y-math.pi)**2))
        return val
    problems.append(BlindProblem("BLIND-006", p6_bounds, p6_eval))

    # 7. Himmelblau (4 global minima)
    p7_bounds = {"x": (-5, 5), "y": (-5, 5)}
    def p7_eval(dp):
        x, y = dp["x"], dp["y"]
        val = (x**2+y-11)**2 + (x+y**2-7)**2
        return -val
    problems.append(BlindProblem("BLIND-007", p7_bounds, p7_eval))

    # --- 8-12: Discrete/combinatorial (continuous encoding) ---

    # 8. TSP (5-city, continuous encoding → nearest-city tour)
    p8_bounds = {f"city{i}": (0.0, 1.0) for i in range(5)}
    # Fixed city coordinates
    p8_cities = [(0, 0), (1, 0), (0.5, 1), (1, 1), (0.5, 0.5)]
    def p8_eval(dp):
        # Sort cities by their continuous value to get tour order
        order = sorted(range(5), key=lambda i: dp[f"city{i}"])
        # Total distance (including return to start)
        dist = 0.0
        for i in range(5):
            c1 = p8_cities[order[i]]
            c2 = p8_cities[order[(i+1) % 5]]
            dist += math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
        return -dist  # higher = better (shorter tour)
    problems.append(BlindProblem("BLIND-008", p8_bounds, p8_eval))

    # 9. SAT (3-SAT, 5 clauses, 4 variables — continuous relaxation)
    p9_bounds = {f"v{i}": (0.0, 1.0) for i in range(4)}
    # Clauses: (v0 OR ~v1 OR v2), (~v0 OR v3 OR ~v2), etc.
    p9_clauses = [(0, -1, 2), (-0, 3, -2), (1, -3, 0), (-1, 2, 3), (2, -0, -3)]
    def p9_eval(dp):
        # Continuous relaxation: v_i = sigmoid(dp[v_i]) → probability v_i is True
        satisfied = 0
        for clause in p9_clauses:
            clause_val = 0
            for lit in clause:
                var_idx = abs(lit)
                p_true = 1.0 / (1.0 + math.exp(-5 * (dp[f"v{var_idx}"] - 0.5)))
                if lit < 0:
                    p_true = 1 - p_true
                clause_val = max(clause_val, p_true)
            satisfied += clause_val
        return satisfied
    problems.append(BlindProblem("BLIND-009", p9_bounds, p9_eval))

    # 10. Knapsack (10 items, continuous relaxation)
    p10_bounds = {f"item{i}": (0.0, 1.0) for i in range(10)}
    p10_weights = [2, 3, 5, 7, 1, 4, 1, 3, 6, 2]
    p10_values = [10, 15, 25, 35, 5, 20, 8, 17, 30, 12]
    p10_capacity = 15
    def p10_eval(dp):
        total_weight = sum(p10_weights[i] * dp[f"item{i}"] for i in range(10))
        total_value = sum(p10_values[i] * dp[f"item{i}"] for i in range(10))
        # Penalty for exceeding capacity
        if total_weight > p10_capacity:
            total_value -= 10 * (total_weight - p10_capacity)
        return total_value
    problems.append(BlindProblem("BLIND-010", p10_bounds, p10_eval))

    # 11. Bin Packing (5 items, 3 bins — continuous assignment)
    p11_bounds = {f"item{i}_bin": (0.0, 1.0) for i in range(5)}
    p11_sizes = [3, 5, 2, 4, 6]
    p11_bin_capacity = 10
    def p11_eval(dp):
        # Assign each item to a bin based on continuous value
        bins = [0, 0, 0]
        for i in range(5):
            bin_idx = min(2, int(dp[f"item{i}_bin"] * 3))
            bins[bin_idx] += p11_sizes[i]
        # Score: negative overflow
        overflow = sum(max(0, b - p11_bin_capacity) for b in bins)
        # Bonus for using fewer bins
        used_bins = sum(1 for b in bins if b > 0)
        return -overflow * 10 - used_bins
    problems.append(BlindProblem("BLIND-011", p11_bounds, p11_eval))

    # 12. Job Shop (3 jobs × 3 machines, continuous scheduling)
    p12_bounds = {f"j{i}_m{j}": (0.0, 1.0) for i in range(3) for j in range(3)}
    p12_durations = [[2, 3, 1], [1, 2, 4], [3, 1, 2]]
    def p12_eval(dp):
        # Continuous relaxation: priority values determine schedule
        # Simplified: sum of completion times (minimize)
        priorities = [[dp[f"j{i}_m{j}"] for j in range(3)] for i in range(3)]
        # Greedy schedule by priority
        machine_free = [0, 0, 0]
        job_done = [0, 0, 0]
        for step in range(9):
            # Find highest priority unscheduled operation
            best = (-1, -1, -1)
            for i in range(3):
                for j in range(3):
                    # Check if this op can run (job's previous ops done)
                    if j > 0 and job_done[i] < j:
                        continue
                    if priorities[i][j] > best[2]:
                        best = (i, j, priorities[i][j])
            if best[0] < 0:
                break
            i, j = best[0], best[1]
            start = max(machine_free[j], job_done[i] if j == 0 else 0)
            end = start + p12_durations[i][j]
            machine_free[j] = end
            job_done[i] = end
        makespan = max(machine_free)
        return -makespan
    problems.append(BlindProblem("BLIND-012", p12_bounds, p12_eval))

    # --- 13-16: Engineering surrogates ---

    # 13. Circuit placement (4 cells, wirelength minimization)
    p13_bounds = {f"cell{i}_{c}": (0.0, 10.0) for i in range(4) for c in ["x", "y"]}
    p13_connections = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    def p13_eval(dp):
        total_wirelength = 0
        for c1, c2 in p13_connections:
            x1, y1 = dp[f"cell{c1}_x"], dp[f"cell{c1}_y"]
            x2, y2 = dp[f"cell{c2}_x"], dp[f"cell{c2}_y"]
            total_wirelength += abs(x1-x2) + abs(y1-y2)
        return -total_wirelength
    problems.append(BlindProblem("BLIND-013", p13_bounds, p13_eval))

    # 14. Portfolio optimization (5 assets, return - risk)
    p14_bounds = {f"w{i}": (0.0, 1.0) for i in range(5)}
    p14_returns = [0.05, 0.08, 0.12, 0.15, 0.10]
    p14_risks = [0.10, 0.15, 0.25, 0.35, 0.20]
    p14_correlations = [0.3, 0.5, 0.2, 0.4, 0.1]  # simplified
    def p14_eval(dp):
        total_w = sum(dp[f"w{i}"] for i in range(5))
        if total_w < 1e-6:
            return -100
        # Normalize weights
        weights = [dp[f"w{i}"] / total_w for i in range(5)]
        ret = sum(p14_returns[i] * weights[i] for i in range(5))
        risk = sum(p14_risks[i] * weights[i] * (1 + p14_correlations[i]) for i in range(5))
        return (ret - 0.5 * risk) * 100  # risk-adjusted return
    problems.append(BlindProblem("BLIND-014", p14_bounds, p14_eval))

    # 15. Hyperparameter tuning (3 hyperparams, loss landscape)
    p15_bounds = {"lr": (1e-5, 1.0), "batch_size": (8.0, 256.0), "reg": (1e-6, 0.1)}
    def p15_eval(dp):
        lr = dp["lr"]
        bs = dp["batch_size"]
        reg = dp["reg"]
        # Simulated validation loss (simplified)
        loss = 0.5 * (math.log(lr) + 5)**2 + 0.001 * (bs - 64)**2 + 1000 * reg
        if lr > 0.5:
            loss += 10  # diverges
        if reg < 1e-5:
            loss += 5  # overfits
        return -loss
    problems.append(BlindProblem("BLIND-015", p15_bounds, p15_eval))

    # 16. Protein folding (simplified HP model, 6 residues)
    p16_bounds = {f"res{i}_{c}": (-3.0, 3.0) for i in range(6) for c in ["x", "y"]}
    p16_hydrophobic = [1, 0, 1, 1, 0, 1]  # H=1, P=0
    def p16_eval(dp):
        # Score: minimize energy = maximize H-H contacts (non-adjacent)
        coords = [(dp[f"res{i}_x"], dp[f"res{i}_y"]) for i in range(6)]
        energy = 0
        for i in range(6):
            for j in range(i+2, 6):  # skip adjacent
                if p16_hydrophobic[i] and p16_hydrophobic[j]:
                    dist = math.sqrt((coords[i][0]-coords[j][0])**2 +
                                     (coords[i][1]-coords[j][1])**2)
                    if dist < 1.5:
                        energy -= 1  # favorable contact
        # Chain length penalty (want compact)
        chain_length = sum(math.sqrt((coords[i][0]-coords[i+1][0])**2 +
                                     (coords[i][1]-coords[i+1][1])**2)
                          for i in range(5))
        return -energy - 0.1 * chain_length
    problems.append(BlindProblem("BLIND-016", p16_bounds, p16_eval))

    # --- 17-20: Hybrid problems ---

    # 17. Symbolic regression (fit y = sin(x) + x^2, 3 parameters)
    p17_bounds = {"a": (-2.0, 2.0), "b": (-2.0, 2.0), "c": (-2.0, 2.0)}
    p17_x_data = [0.1 * i for i in range(20)]
    p17_y_data = [math.sin(x) + x**2 for x in p17_x_data]
    def p17_eval(dp):
        a, b, c = dp["a"], dp["b"], dp["c"]
        # Model: a*sin(b*x) + c*x^2
        error = 0
        for x, y in zip(p17_x_data, p17_y_data):
            pred = a * math.sin(b * x) + c * x**2
            error += (pred - y)**2
        return -error
    problems.append(BlindProblem("BLIND-017", p17_bounds, p17_eval))

    # 18. Neural architecture (3 layer sizes, simplified)
    p18_bounds = {"l1": (4.0, 64.0), "l2": (4.0, 64.0), "l3": (4.0, 32.0), "lr": (1e-4, 0.1)}
    def p18_eval(dp):
        l1, l2, l3 = int(dp["l1"]), int(dp["l2"]), int(dp["l3"])
        lr = dp["lr"]
        # Simulated accuracy (simplified)
        capacity = l1 * l2 + l2 * l3
        target = 1000  # sweet spot
        accuracy = 0.9 - 0.001 * abs(capacity - target)
        if lr > 0.05:
            accuracy -= 0.1  # too high
        if lr < 1e-3:
            accuracy -= 0.05  # too low
        return accuracy * 100
    problems.append(BlindProblem("BLIND-018", p18_bounds, p18_eval))

    # 19. Control (PID tuning, simplified)
    p19_bounds = {"kp": (0.0, 10.0), "ki": (0.0, 5.0), "kd": (0.0, 5.0)}
    def p19_eval(dp):
        kp, ki, kd = dp["kp"], dp["ki"], dp["kd"]
        # Simulated settling time (simplified)
        settling = 10.0 / (1 + kp) + 5.0 / (1 + ki) + 2.0 * kd
        overshoot = max(0, kp + ki - 5) * 0.1
        return -(settling + overshoot * 10)
    problems.append(BlindProblem("BLIND-019", p19_bounds, p19_eval))

    # 20. Scheduling (5 tasks, 2 resources, continuous priority)
    p20_bounds = {f"task{i}": (0.0, 1.0) for i in range(5)}
    p20_durations = [3, 5, 2, 4, 6]
    p20_deadlines = [5, 10, 4, 8, 12]
    def p20_eval(dp):
        # Schedule by priority (descending)
        order = sorted(range(5), key=lambda i: -dp[f"task{i}"])
        resource_time = [0, 0]
        tardiness = 0
        for task_idx in order:
            # Assign to least-loaded resource
            res = 0 if resource_time[0] <= resource_time[1] else 1
            start = resource_time[res]
            end = start + p20_durations[task_idx]
            resource_time[res] = end
            if end > p20_deadlines[task_idx]:
                tardiness += end - p20_deadlines[task_idx]
        return -tardiness
    problems.append(BlindProblem("BLIND-020", p20_bounds, p20_eval))

    return problems


# Build the suite
BLIND_SUITE = _make_blind_suite()


def main():
    """Run L5a program discovery on the blind suite."""
    print("=" * 90)
    print("BLIND BENCHMARK SUITE (cycle 229)")
    print("20 unrelated problems. Names hidden. Only sample()/evaluate() exposed.")
    print("=" * 90)
    print()

    print(f"Total blind problems: {len(BLIND_SUITE)}")
    print()

    # Verify each problem is runnable
    print("Verifying all 20 problems are runnable...")
    rng = random.Random(42)
    for p in BLIND_SUITE:
        dp = p.sample(rng)
        outcome = p.evaluate(dp)
        assert isinstance(outcome, (int, float)), \
            f"{p.problem_id}: outcome must be numeric"
    print("All 20 problems verified.")
    print()

    # Run L5a program discovery on the blind suite
    from scripts.l5_search_discovery import L5ProgramDiscovery
    from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer

    # Training: first 10 blind problems
    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    # Held-out: last 10 blind problems
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    print("=" * 90)
    print("L5a PROGRAM DISCOVERY ON BLIND SUITE")
    print("Training: 10 blind problems (BLIND-001 to BLIND-010)")
    print("Held-out: 10 blind problems (BLIND-011 to BLIND-020)")
    print("=" * 90)
    print()

    l5 = L5ProgramDiscovery(n_programs=30, program_length=4,
                           n_iterations=2, n_per_iter=15)
    best_program = l5.search(training, seed=42)

    # Evaluate on held-out
    print()
    print("=" * 90)
    print("EVALUATING DISCOVERED PROGRAM ON 10 HELD-OUT BLIND PROBLEMS")
    print("=" * 90)
    print()

    print(f"{'Problem':<12} {'Program':<12} {'Random':<12} {'Beats':<8}")
    print("-" * 50)

    n_beats_random = 0
    for name, spec, fn in held_out:
        # Run discovered program
        executor = type('E', (), {'domain': spec, 'original_bounds': {v['name']: v['bounds'] for v in spec['design_vars']},
                                   'policy': {v['name']: v['bounds'] for v in spec['design_vars']},
                                   'var_names': [v['name'] for v in spec['design_vars']],
                                   'design_vars': spec['design_vars'],
                                   'surrogate_weights': None, 'best_y': -math.inf})()
        # Use ProgramExecutor properly
        from scripts.l5_search_discovery import ProgramExecutor
        executor = ProgramExecutor(spec)
        prog_iters = executor.execute_program(best_program, fn,
                                               n_iterations=3, n_per_iter=20, seed=42)
        prog_best = prog_iters[-1]["best_outcome"]

        # Run random baseline
        random_opt = RandomRestartOptimizer(spec)
        rand_iters = run_optimizer(spec, fn, random_opt,
                                    n_iterations=3, n_per_iter=20, seed=42)
        rand_best = rand_iters[-1]["best_outcome"]

        beats = "✓" if prog_best > rand_best + 1e-9 else "✗"
        if prog_best > rand_best + 1e-9:
            n_beats_random += 1

        print(f"{name:<12} {prog_best:>+12.4f} {rand_best:>+12.4f} {beats:<8}")

    print()
    print("=" * 90)
    print("BLIND SUITE SUMMARY")
    print("=" * 90)
    print()
    print(f"Discovered program beats RANDOM on {n_beats_random}/10 held-out blind problems")
    print()
    print("HONEST INTERPRETATION:")
    if n_beats_random >= 5:
        print(f"The discovered program generalizes to UNSEEN blind problems.")
        print(f"This is evidence that L5a is learning optimization STRATEGIES,")
        print(f"not exploiting domain characteristics of the training set.")
    elif n_beats_random >= 3:
        print(f"The discovered program generalizes PARTIALLY ({n_beats_random}/10).")
        print(f"Some strategies transfer; others are training-specific.")
    else:
        print(f"The discovered program does NOT generalize ({n_beats_random}/10).")
        print(f"It may be overfit to the training blind problems.")


if __name__ == "__main__":
    main()
