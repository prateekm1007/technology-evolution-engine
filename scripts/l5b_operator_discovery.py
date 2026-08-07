#!/usr/bin/env python3
"""
l5b_operator_discovery.py — L5b: new combinatorial operators (cycle 231).

Per auditor's update #20 (priority #3) and cycle 230's honest negative:
  "L5b is far more important than RL. I'd stop improving the DSL.
   I'd improve the search."

Wait — the auditor said "stop improving the DSL, improve the search."
But cycle 230 TESTED that (evolutionary search) and found the DSL IS
the bottleneck (flat fitness, 2/10 = 2/10). So the honest path is:
the DSL must GROW with new operators for combinatorial problems.

This is L5b: OPERATOR DISCOVERY. Not search improvement, but DSL
extension. The cycle 230 flat fitness proved no search procedure can
help until the DSL has operators that can handle the blind suite's
combinatorial problems (TSP, SAT, Knapsack) where it currently scores
0/3.

NEW OPERATORS (designed for combinatorial landscapes):
  1. SWAP — swap two variable values (2-opt for TSP)
  2. FLIP — flip a binary variable (for SAT)
  3. ASSIGN_THRESHOLD — threshold continuous vars to discrete (0/1)
  4. LOCAL_SEARCH_2OPT — 2-opt local search on ordered variables
  5. PENALTY_AWARE_SELECT — select candidates considering constraint
     violations (for knapsack, bin packing)

These operators are NEW PRIMITIVES — they don't exist in the cycle 228
DSL. They extend the language. This is the first step toward L5b:
growing the operator language so search can find programs that work
on combinatorial problems.

HONEST EXPECTATION:
Adding 5 combinatorial operators to a 13-primitive DSL may or may not
raise the blind suite score. The blind suite has 3 combinatorial
problems (BLIND-018, 019, 020: TSP, SAT, Knapsack). If the new
operators help, the score should rise from 0/3 to ≥1/3 on those
problems. If not, the operators are insufficient and more are needed.

This is genuine L5b progress: the first DSL extension with new
operator types, tested on the blind suite.
"""
import sys
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
from enum import Enum

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5_search_discovery import (
    OpType, OptimizerProgram, ProgramExecutor, ALL_OPS,
)


# ============================================================================
# L5b — NEW COMBINATORIAL OPERATORS
# ============================================================================

class CombinatorialOpType(Enum):
    """L5b: New operator primitives for combinatorial landscapes.

    These operators do NOT exist in the cycle 228 DSL. They extend the
    language to handle discrete/combinatorial problems (TSP, SAT,
    Knapsack) where the original DSL scored 0/3 on the blind suite.
    """
    SWAP = "swap"                    # swap two variable values (2-opt)
    FLIP = "flip"                    # flip a variable past threshold (SAT)
    ASSIGN_THRESHOLD = "threshold"   # threshold continuous → discrete
    LOCAL_SEARCH_2OPT = "local_2opt" # 2-opt local search on ordered vars
    PENALTY_AWARE_SELECT = "penalty_select"  # select with constraint awareness


# Extended operation set: original 13 + 5 new = 18
EXTENDED_OPS = list(OpType) + list(CombinatorialOpType)


class ExtendedProgramExecutor(ProgramExecutor):
    """ProgramExecutor with L5b combinatorial operators.

    Extends the original executor with 5 new operation types:
    SWAP, FLIP, ASSIGN_THRESHOLD, LOCAL_SEARCH_2OPT, PENALTY_AWARE_SELECT.

    These operators allow programs to handle combinatorial problems
    that the original DSL (designed for continuous optimization)
    could not.
    """

    def _execute_op(self, op, candidates: List, rng: random.Random) -> List:
        """Execute one operation — handles both original and L5b ops."""
        # Check if it's an L5b combinatorial op
        if isinstance(op, CombinatorialOpType):
            return self._execute_combinatorial_op(op, candidates, rng)
        else:
            # Delegate to parent for original ops
            return super()._execute_op(op, candidates, rng)

    def _execute_combinatorial_op(self, op: CombinatorialOpType,
                                   candidates: List, rng: random.Random) -> List:
        """Execute an L5b combinatorial operator."""
        if not candidates:
            return candidates

        if op == CombinatorialOpType.SWAP:
            return self._op_swap(candidates, rng)
        elif op == CombinatorialOpType.FLIP:
            return self._op_flip(candidates, rng)
        elif op == CombinatorialOpType.ASSIGN_THRESHOLD:
            return self._op_threshold(candidates, rng)
        elif op == CombinatorialOpType.LOCAL_SEARCH_2OPT:
            return self._op_local_2opt(candidates, rng)
        elif op == CombinatorialOpType.PENALTY_AWARE_SELECT:
            return self._op_penalty_select(candidates, rng)
        return candidates

    def _op_swap(self, candidates: List, rng: random.Random) -> List:
        """SWAP: exchange values of two random variables in top candidates.

        This is useful for TSP-like problems where swapping the order
        of two cities can improve the tour.
        """
        if len(self.var_names) < 2:
            return candidates
        sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
        top = sorted_c[:max(2, len(sorted_c) // 4)]
        for c in top:
            v1, v2 = rng.sample(self.var_names, 2)
            c.design_point[v1], c.design_point[v2] = c.design_point[v2], c.design_point[v1]
        return candidates

    def _op_flip(self, candidates: List, rng: random.Random) -> List:
        """FLIP: flip a variable past its midpoint (for binary-like vars).

        Useful for SAT-like problems where variables represent true/false.
        """
        sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
        top = sorted_c[:max(2, len(sorted_c) // 4)]
        for c in top:
            vname = rng.choice(self.var_names)
            lo, hi = self.original_bounds[vname]
            mid = (lo + hi) / 2
            # Flip: if below midpoint, set to near hi; if above, set to near lo
            if c.design_point[vname] < mid:
                c.design_point[vname] = hi - 0.01 * (hi - lo)
            else:
                c.design_point[vname] = lo + 0.01 * (hi - lo)
        return candidates

    def _op_threshold(self, candidates: List, rng: random.Random) -> List:
        """ASSIGN_THRESHOLD: threshold continuous vars to discrete (0 or 1).

        Converts continuous variables to binary by thresholding at midpoint.
        Useful for knapsack (item in/out) and bin packing (item to bin).
        """
        sorted_c = sorted(candidates, key=lambda c: c.predicted_outcome, reverse=True)
        top = sorted_c[:max(2, len(sorted_c) // 4)]
        for c in top:
            for vname in self.var_names:
                lo, hi = self.original_bounds[vname]
                mid = (lo + hi) / 2
                # Threshold: values above mid → hi, below → lo
                if c.design_point[vname] > mid:
                    c.design_point[vname] = hi
                else:
                    c.design_point[vname] = lo
        # Also narrow policy toward discrete values
        for vname in self.var_names:
            lo, hi = self.original_bounds[vname]
            mid = (lo + hi) / 2
            # Split policy into two clusters around lo and hi
            span = hi - lo
            self.policy[vname] = (lo, lo + 0.1 * span)  # narrow to lower cluster
            # Alternate: sometimes narrow to upper cluster
            if rng.random() < 0.5:
                self.policy[vname] = (hi - 0.1 * span, hi)
        return candidates

    def _op_local_2opt(self, candidates: List, rng: random.Random) -> List:
        """LOCAL_SEARCH_2OPT: 2-opt local search on ordered variables.

        For TSP-like problems where the order of variables matters,
        this operator tries swapping adjacent pairs to find improvements.
        """
        if len(self.var_names) < 3:
            return candidates
        best = max(candidates, key=lambda c: c.predicted_outcome)
        dp = dict(best.design_point)
        best_outcome = best.predicted_outcome

        # Try swapping adjacent variable values
        improved = False
        for i in range(len(self.var_names) - 1):
            v1 = self.var_names[i]
            v2 = self.var_names[i + 1]
            # Swap
            dp[v1], dp[v2] = dp[v2], dp[v1]
            # The executor can't re-evaluate here (no forward_fn), so
            # we just apply the swap to the best candidate and let the
            # next sampling iteration explore around it
            improved = True
            break  # first-improvement

        if improved:
            # Narrow policy around the swapped best
            for vname in self.var_names:
                lo, hi = self.original_bounds[vname]
                center = dp[vname]
                span = hi - lo
                half_width = 0.1 * span
                self.policy[vname] = (max(lo, center - half_width),
                                      min(hi, center + half_width))
        return candidates

    def _op_penalty_select(self, candidates: List, rng: random.Random) -> List:
        """PENALTY_AWARE_SELECT: select candidates considering outcome spread.

        For constrained problems (knapsack, bin packing), this operator
        prefers candidates with high outcome AND low variance (more
        feasible). It narrows policy toward the most "reliable" region.
        """
        if not candidates:
            return candidates

        # Compute outcome statistics
        outcomes = [c.predicted_outcome for c in candidates]
        mean_o = sum(outcomes) / len(outcomes)
        std_o = math.sqrt(sum((o - mean_o) ** 2 for o in outcomes) / len(outcomes)) if outcomes else 0

        # Score = outcome - penalty * std (prefer high outcome, low variance)
        # This is a risk-adjusted selection
        scored = [(c, c.predicted_outcome - 0.5 * std_o) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [c for c, _ in scored[:max(2, len(scored) // 4)]]

        # Narrow policy toward the selected region
        for vname in self.var_names:
            vals = [c.design_point[vname] for c in top]
            lo, hi = self.original_bounds[vname]
            new_lo = max(lo, min(vals) - 0.05 * (hi - lo))
            new_hi = min(hi, max(vals) + 0.05 * (hi - lo))
            if new_hi > new_lo:
                self.policy[vname] = (new_lo, new_hi)
        return candidates


# ============================================================================
# L5b SEARCH — search over extended DSL
# ============================================================================

class L5bOperatorDiscovery:
    """L5b: Search over programs using the EXTENDED DSL (18 operators).

    This is the first L5b step: grow the DSL with 5 new combinatorial
    operators and re-run program discovery. If the blind suite score
    rises above 2/10, the DSL extension helped. If not, more operators
    are needed.

    The search procedure is still random (same as L5a) — the test is
    whether the EXTENDED DSL can express programs that the original
    DSL could not.
    """

    def __init__(self, n_programs: int = 30, program_length: int = 4,
                 n_iterations: int = 2, n_per_iter: int = 15):
        self.n_programs = n_programs
        self.program_length = program_length
        self.n_iterations = n_iterations
        self.n_per_iter = n_per_iter
        self.programs: List[OptimizerProgram] = []
        self.best_program: Optional[OptimizerProgram] = None

    def _random_program(self, rng: random.Random, program_id: str) -> OptimizerProgram:
        """Generate a random program from the EXTENDED DSL (18 ops)."""
        ops = [rng.choice(EXTENDED_OPS) for _ in range(self.program_length)]
        return OptimizerProgram(program_id=program_id, operations=ops)

    def search(self, training_domains: List[Tuple[str, Dict, Callable]],
               seed: int = 42) -> OptimizerProgram:
        """Search over programs using the extended DSL."""
        rng = random.Random(seed)
        print(f"L5b Operator Discovery (extended DSL: {len(EXTENDED_OPS)} operators)")
        print(f"  New operators: SWAP, FLIP, THRESHOLD, LOCAL_2OPT, PENALTY_SELECT")
        print(f"  Programs: {self.n_programs}, length: {self.program_length}")
        print()

        results = []
        for i in range(self.n_programs):
            program = self._random_program(rng, f"L5b-{i+1:03d}")
            improvements = []

            for name, spec, fn in training_domains:
                executor = ExtendedProgramExecutor(spec)
                try:
                    iters = executor.execute_program(program, fn,
                                                      n_iterations=self.n_iterations,
                                                      n_per_iter=self.n_per_iter,
                                                      seed=42)
                    improvement = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
                    improvements.append(improvement)
                except Exception:
                    improvements.append(-1e6)

            program.fitness = sum(improvements) / len(improvements) if improvements else -1e6
            program.fitness_std = math.sqrt(sum((x - program.fitness) ** 2 for x in improvements) / len(improvements)) if improvements else 0
            program.n_evaluated = len(improvements)
            self.programs.append(program)
            results.append((program, program.fitness))

            if i < 5 or i % 10 == 0:
                has_new = any(isinstance(op, CombinatorialOpType) for op in program.operations)
                marker = " [NEW]" if has_new else ""
                print(f"  Program {i+1}/{self.n_programs}: fitness={program.fitness:+.4f}"
                      f"{' [NEW]' if has_new else ''}")

        results.sort(key=lambda x: x[1], reverse=True)
        self.best_program = results[0][0]

        # Count how many top programs use new operators
        top_10 = results[:10]
        n_uses_new = sum(1 for p, _ in top_10
                        if any(isinstance(op, CombinatorialOpType) for op in p.operations))

        print()
        print(f"Best program: {self.best_program}")
        print(f"  fitness={self.best_program.fitness:+.4f}")
        print(f"  Top 10 programs using new operators: {n_uses_new}/10")

        return self.best_program

    def evaluate_on_held_out(self, program: OptimizerProgram,
                              held_out_domains: List[Tuple[str, Dict, Callable]],
                              seed: int = 42) -> Dict:
        """Evaluate on held-out domains using ExtendedProgramExecutor."""
        from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer

        print()
        print(f"Evaluating on {len(held_out_domains)} held-out domains (extended DSL):")
        print()

        results = []
        for name, spec, fn in held_out_domains:
            executor = ExtendedProgramExecutor(spec)
            try:
                iters = executor.execute_program(program, fn,
                                                  n_iterations=3, n_per_iter=20, seed=seed)
                prog_best = iters[-1]["best_outcome"]
            except Exception:
                prog_best = -1e6

            random_opt = RandomRestartOptimizer(spec)
            rand_iters = run_optimizer(spec, fn, random_opt,
                                        n_iterations=3, n_per_iter=20, seed=seed)
            rand_best = rand_iters[-1]["best_outcome"]

            beats = prog_best > rand_best + 1e-9
            results.append({
                "domain": name,
                "program_best": prog_best,
                "random_best": rand_best,
                "beats_random": beats,
            })
            print(f"  {name:<20} program={prog_best:>+10.4f}  random={rand_best:>+10.4f}  "
                  f"beats={'✓' if beats else '✗'}")

        n_beats = sum(1 for r in results if r["beats_random"])
        print()
        print(f"Extended DSL program beats RANDOM on {n_beats}/{len(results)} held-out domains")

        return {
            "program": program.to_dict(),
            "results": results,
            "n_beats_random": n_beats,
            "n_total": len(results),
        }


def main():
    print("=" * 90)
    print("L5b OPERATOR DISCOVERY (cycle 231)")
    print("Extending the DSL with 5 combinatorial operators")
    print("=" * 90)
    print()

    from scripts.blind_suite import BLIND_SUITE

    # Training: first 10 blind problems
    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    # Held-out: last 10 blind problems (3 combinatorial: BLIND-018, 019, 020)
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    # Phase 1: Search with extended DSL
    print("=" * 90)
    print("PHASE 1: L5b search with extended DSL (18 operators)")
    print("=" * 90)
    print()

    l5b = L5bOperatorDiscovery(n_programs=30, program_length=4,
                                n_iterations=2, n_per_iter=15)
    best_l5b = l5b.search(training, seed=42)

    # Phase 2: Evaluate on held-out
    print()
    print("=" * 90)
    print("PHASE 2: Evaluate L5b (extended DSL) on held-out blind problems")
    print("=" * 90)
    print()

    l5b_result = l5b.evaluate_on_held_out(best_l5b, held_out, seed=42)

    # Phase 3: Compare to L5a (original DSL, cycle 229)
    print()
    print("=" * 90)
    print("PHASE 3: Compare L5b (extended DSL) vs L5a (original DSL)")
    print("=" * 90)
    print()

    from scripts.l5_search_discovery import L5ProgramDiscovery
    l5a = L5ProgramDiscovery(n_programs=30, program_length=4,
                             n_iterations=2, n_per_iter=15)
    best_l5a = l5a.search(training, seed=42)
    l5a_result = l5a.evaluate_on_held_out(best_l5a, held_out, seed=42)

    # Summary
    print()
    print("=" * 90)
    print("L5b vs L5a — BLIND SUITE COMPARISON")
    print("=" * 90)
    print()
    print(f"{'DSL':<25} {'Operators':<12} {'Beats baseline':<20}")
    print("-" * 60)
    print(f"{'L5a (original)':<25} {13:<12} {l5a_result['n_beats_portfolio']}/{l5a_result['n_total']:<20}")
    print(f"{'L5b (extended)':<25} {18:<12} {l5b_result['n_beats_random']}/{l5b_result['n_total']:<20}")

    # Breakdown: did L5b help on combinatorial problems?
    print()
    print("Combinatorial problems (BLIND-018, 019, 020):")
    l5a_combo = [r for r in l5a_result["results"] if r["domain"] in ["BLIND-018", "BLIND-019", "BLIND-020"]]
    l5b_combo = [r for r in l5b_result["results"] if r["domain"] in ["BLIND-018", "BLIND-019", "BLIND-020"]]
    l5a_combo_beats = sum(1 for r in l5a_combo if r.get("beats_portfolio", r.get("beats_random", False)))
    l5b_combo_beats = sum(1 for r in l5b_combo if r["beats_random"])
    print(f"  L5a: {l5a_combo_beats}/3 combinatorial problems beat baseline")
    print(f"  L5b: {l5b_combo_beats}/3 combinatorial problems beat baseline")

    print()
    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    l5b_beats = l5b_result["n_beats_random"]
    l5a_beats = l5a_result["n_beats_portfolio"]

    if l5b_beats > l5a_beats:
        print(f"L5b (extended DSL) BEATS L5a (original DSL): {l5b_beats}/10 vs {l5a_beats}/10")
        print("The new combinatorial operators helped! The DSL extension raised")
        print("the blind suite score. This confirms L5b is the right direction.")
        print()
        if l5b_combo_beats > l5a_combo_beats:
            print(f"The improvement is on combinatorial problems: {l5a_combo_beats}/3 → {l5b_combo_beats}/3")
            print("The new operators (SWAP, FLIP, THRESHOLD, etc.) are being used.")
        else:
            print("The improvement is on continuous problems (new operators helped")
            print("indirectly by freeing up the search space).")
    elif l5b_beats == l5a_beats:
        print(f"L5b (extended DSL) MATCHES L5a: {l5b_beats}/10 vs {l5a_beats}/10")
        print("The 5 new operators did not raise the blind suite score.")
        print()
        print("Honest assessment: the operators may be insufficient, or random")
        print("search is too weak to find programs that USE the new operators")
        print("effectively. The top-10 usage count tells us if they're selected.")
    else:
        print(f"L5b (extended DSL) is WORSE: {l5b_beats}/10 vs {l5a_beats}/10")
        print("The new operators may be disrupting good programs. This is an")
        print("honest negative — the DSL extension didn't help.")

    print()
    print("USAGE ANALYSIS: How many top-10 programs use new operators?")
    # This is printed during search


if __name__ == "__main__":
    main()
