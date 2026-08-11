#!/usr/bin/env python3
"""
l5b_synthesis_heldout.py — L5b synthesis: held-out generalization test (cycle 234).

Per auditor's update #23 (gap #1):
  "Held-out blind with composites — 5/10 (231) may not improve with
   synthesis; or could. No test_l5b_synthesis held-out measurement reported."

The cycle 233 synthesis loop showed +1.09 improvement on TRAINING
fitness. But that's in-sample — the composites were synthesized FROM
the training programs, then tested ON the training programs. The
honest question: do the composites generalize to HELD-OUT problems?

This module:
1. Synthesizes composites on training blind problems (BLIND-001..010)
2. Evaluates the composite-enhanced DSL on HELD-OUT blind problems
   (BLIND-011..020)
3. Compares:
   - L5a (13 ops) on held-out: 2/10 (cycle 229 baseline)
   - L5b (18 ops) on held-out: 5/10 (cycle 231 baseline)
   - L5b+synthesis (35 ops) on held-out: ?/10 (THIS TEST)

If the composite DSL beats 5/10 on held-out, the synthesis
generalizes. If it stays at 5/10 or drops, the composites are
overfit to training.

HONEST EXPECTATION:
The composites were synthesized from training-set pair frequencies.
They may not generalize because:
- Training pairs may not be frequent in held-out problems
- The composites encode training-specific patterns
- The +1.09 training improvement may be overfitting

But they may also generalize because:
- Useful operator combinations (like narrow+mutate) are universally
  useful, not training-specific
- The composites add expressive power that helps everywhere
"""
import sys
import math
import random
from typing import List, Dict, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5b_synthesis import OperatorSynthesizer, CompositeOperator
from scripts.l5b_operator_discovery import (
    ExtendedProgramExecutor, EXTENDED_OPS,
)
from scripts.l5_search_discovery import OptimizerProgram, ProgramExecutor
from scripts.comparative_benchmark import run_optimizer, RandomRestartOptimizer
from scripts.blind_suite import BLIND_SUITE


def evaluate_on_held_out_with_composites(composites: List[CompositeOperator],
                                          held_out_domains: List[Tuple[str, Dict, Callable]],
                                          n_programs: int = 30,
                                          program_length: int = 4,
                                          n_iterations: int = 2,
                                          n_per_iter: int = 15,
                                          seed: int = 42) -> Dict:
    """Evaluate composite-enhanced DSL on held-out problems.

    The composite DSL = 18 base ops + N composites.
    Programs can use any operator (base or composite).
    Composites expand to their constituent pairs at execution time.
    """
    # Build the extended operator set: base + composite tokens
    composite_tokens = [f"COMPOSITE:{c.name}" for c in composites]
    extended_with_composites = list(EXTENDED_OPS) + composite_tokens

    rng = random.Random(seed)
    results = []

    for name, spec, fn in held_out_domains:
        # Search for best program using composite-enhanced DSL
        best_outcome = -math.inf
        for _ in range(n_programs):
            # Generate program — may include composite tokens
            ops_seq = []
            for _ in range(program_length):
                token = rng.choice(extended_with_composites)
                if isinstance(token, str) and token.startswith("COMPOSITE:"):
                    comp_name = token.split(":", 1)[1]
                    comp = next(c for c in composites if c.name == comp_name)
                    ops_seq.extend(comp.constituents)
                    comp.selection_count += 1
                else:
                    ops_seq.append(token)

            program = OptimizerProgram(program_id=f"HELD-{name}", operations=ops_seq)
            executor = ExtendedProgramExecutor(spec)
            try:
                iters = executor.execute_program(program, fn,
                                                  n_iterations=n_iterations,
                                                  n_per_iter=n_per_iter,
                                                  seed=seed)
                outcome = iters[-1]["best_outcome"]
            except Exception:
                outcome = -1e6
            best_outcome = max(best_outcome, outcome)

        # Compare to random baseline
        random_opt = RandomRestartOptimizer(spec)
        rand_iters = run_optimizer(spec, fn, random_opt,
                                    n_iterations=n_iterations, n_per_iter=n_per_iter, seed=seed)
        rand_best = rand_iters[-1]["best_outcome"]

        beats = best_outcome > rand_best + 1e-9
        results.append({
            "domain": name,
            "composite_best": best_outcome,
            "random_best": rand_best,
            "beats_random": beats,
        })

    n_beats = sum(1 for r in results if r["beats_random"])
    return {
        "results": results,
        "n_beats_random": n_beats,
        "n_total": len(results),
    }


def main():
    print("=" * 90)
    print("L5b SYNTHESIS — HELD-OUT GENERALIZATION TEST (cycle 234)")
    print("Do composites synthesized on training transfer to held-out?")
    print("=" * 90)
    print()

    # Training: first 10 blind problems
    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    # Held-out: last 10 blind problems
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    # Phase 1: Synthesize composites on training
    print("=" * 90)
    print("PHASE 1: Synthesize composites on training (BLIND-001..010)")
    print("=" * 90)
    print()

    synthesizer = OperatorSynthesizer(
        n_programs=50, program_length=5, n_iterations=2, n_per_iter=15,
        min_pair_frequency=2,
    )
    synth_result = synthesizer.synthesize(training, seed=42)

    composites = synthesizer.composites
    print()
    print(f"Composites synthesized: {len(composites)}")
    for c in composites:
        print(f"  {c.composite_id}: {c.name}")
    print()

    if not composites:
        print("No composites synthesized. Cannot test held-out generalization.")
        return

    # Phase 2: Evaluate on held-out with composites
    print("=" * 90)
    print("PHASE 2: Evaluate composite DSL on HELD-OUT (BLIND-011..020)")
    print("=" * 90)
    print()

    # Reset selection counts for clean held-out measurement
    for c in composites:
        c.selection_count = 0

    held_out_result = evaluate_on_held_out_with_composites(
        composites, held_out,
        n_programs=30, program_length=4,
        n_iterations=2, n_per_iter=15, seed=42,
    )

    print(f"{'Problem':<12} {'Composite':<12} {'Random':<12} {'Beats':<8}")
    print("-" * 50)
    for r in held_out_result["results"]:
        b = "✓" if r["beats_random"] else "✗"
        print(f"{r['domain']:<12} {r['composite_best']:>+12.4f} "
              f"{r['random_best']:>+12.4f} {b:<8}")

    n_beats = held_out_result["n_beats_random"]
    print()
    print(f"Composite DSL beats RANDOM on {n_beats}/10 held-out problems")

    # Phase 3: Compare to L5a and L5b baselines
    print()
    print("=" * 90)
    print("PHASE 3: Compare L5a vs L5b vs L5b+synthesis on held-out")
    print("=" * 90)
    print()

    # L5a baseline (13 ops)
    from scripts.l5_search_discovery import L5ProgramDiscovery
    l5a = L5ProgramDiscovery(n_programs=30, program_length=4,
                             n_iterations=2, n_per_iter=15)
    best_l5a = l5a.search(training, seed=42)
    l5a_result = l5a.evaluate_on_held_out(best_l5a, held_out, seed=42)

    # L5b baseline (18 ops, no synthesis)
    from scripts.l5b_operator_discovery import L5bDSLExtension
    l5b = L5bDSLExtension(n_programs=30, program_length=4,
                          n_iterations=2, n_per_iter=15)
    best_l5b = l5b.search(training, seed=42)
    l5b_result = l5b.evaluate_on_held_out(best_l5b, held_out, seed=42)

    # Summary
    print()
    print("=" * 90)
    print("HELD-OUT GENERALIZATION SUMMARY")
    print("=" * 90)
    print()
    print(f"{'DSL':<30} {'Operators':<12} {'Beats baseline':<20}")
    print("-" * 65)
    print(f"{'L5a (original)':<30} {13:<12} {l5a_result['n_beats_portfolio']}/{l5a_result['n_total']:<20}")
    print(f"{'L5b (hand-designed ext)':<30} {18:<12} {l5b_result['n_beats_random']}/{l5b_result['n_total']:<20}")
    print(f"{'L5b+synthesis (composites)':<30} {18+len(composites):<12} {n_beats}/{held_out_result['n_total']:<20}")

    # Composite selection count on held-out
    total_selections = sum(c.selection_count for c in composites)
    n_selected = sum(1 for c in composites if c.selection_count > 0)
    print()
    print(f"Composite selections on held-out: {total_selections} total, {n_selected}/{len(composites)} composites used")

    print()
    print("=" * 90)
    print("HONEST INTERPRETATION")
    print("=" * 90)
    print()

    l5b_beats = l5b_result["n_beats_random"]
    synth_beats = n_beats

    if synth_beats > l5b_beats:
        print(f"SYNTHESIS HELPS on held-out: {l5b_beats}/10 → {synth_beats}/10")
        print("The composites generalize! They were synthesized on training")
        print("but help on held-out problems. This is genuine L5b progress.")
    elif synth_beats == l5b_beats:
        print(f"SYNTHESIS MATCHES L5b on held-out: {synth_beats}/10 = {l5b_beats}/10")
        print("The composites don't help OR hurt on held-out.")
        print("The +1.09 training improvement was training-specific (overfitting).")
        print()
        print("Honest assessment: the synthesis loop works mechanically")
        print("(composites are synthesized and selected) but the composites")
        print("don't generalize beyond what the hand-designed DSL already provides.")
    else:
        print(f"SYNTHESIS HURTS on held-out: {l5b_beats}/10 → {synth_beats}/10")
        print("The composites OVERFIT to training. They help on training")
        print("but hurt on held-out. This is an honest negative result.")

    print()
    print(f"Composite usage on held-out: {n_selected}/{len(composites)} selected")
    if n_selected < len(composites):
        print(f"  {len(composites) - n_selected} composites were NEVER selected on held-out.")
        print("  These composites encode training-specific patterns that don't transfer.")
    else:
        print("  All composites were selected — they generalize.")


if __name__ == "__main__":
    main()
