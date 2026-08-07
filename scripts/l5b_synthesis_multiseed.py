#!/usr/bin/env python3
"""
l5b_synthesis_multiseed.py — L5b synthesis: multi-seed held-out (cycle 235).

Per auditor's update #24 (gap #2):
  "Multi-seed held-out not yet run. Single seed 42; stability unknown.
   Could be 9/10 at 42, 7/10 at other seeds."

The cycle 234 result (5/10 → 9/10 on held-out) was at seed 42 only.
The auditor correctly asks: is this stable across seeds?

This module runs the synthesis + held-out evaluation across 5 seeds:
1. For each seed: synthesize composites on training, evaluate on held-out
2. Report per-seed held-out score
3. Compute mean and std
4. Honest test: does the mean beat L5b's 5/10?

If the mean is ≥7/10, the synthesis generalization is robust.
If it drops below 5/10, the 9/10 was seed luck and the composites
are unstable.

HONEST EXPECTATION:
The synthesis + held-out pipeline has TWO stochastic steps:
1. Program discovery (random search) — different seeds find different programs
2. Composite synthesis (pair frequency analysis) — different programs → different pairs
So the composites themselves may vary across seeds, and their held-out
performance may vary too. The honest question is whether the VARIANCE
is low enough that the improvement is reliable.
"""
import sys
import math
import random
from typing import List, Dict, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.l5b_synthesis import OperatorSynthesizer, CompositeOperator
from scripts.l5b_synthesis_heldout import evaluate_on_held_out_with_composites
from scripts.blind_suite import BLIND_SUITE

SEEDS = [42, 7, 99, 123, 256]


def run_multiseed_synthesis_heldout(training, held_out, seeds=SEEDS,
                                     n_programs=30, program_length=4,
                                     n_iterations=2, n_per_iter=15,
                                     synth_n_programs=50, synth_program_length=5,
                                     min_pair_frequency=2):
    """Run synthesis + held-out across multiple seeds.

    For each seed:
    1. Synthesize composites on training (using that seed)
    2. Evaluate composite DSL on held-out (using that seed)
    3. Record: n_composites, n_selected, held-out beats score
    """
    results = []

    for seed in seeds:
        print(f"\n--- Seed {seed} ---")

        # Phase 1: Synthesize composites on training
        synthesizer = OperatorSynthesizer(
            n_programs=synth_n_programs,
            program_length=synth_program_length,
            n_iterations=n_iterations,
            n_per_iter=n_per_iter,
            min_pair_frequency=min_pair_frequency,
        )
        # Suppress detailed output during multi-seed run
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            synth_result = synthesizer.synthesize(training, seed=seed)

        composites = synthesizer.composites
        n_composites = len(composites)

        if not composites:
            print(f"  Seed {seed}: 0 composites synthesized — skipping held-out")
            results.append({
                "seed": seed,
                "n_composites": 0,
                "n_selected": 0,
                "n_beats": 0,
                "n_total": len(held_out),
            })
            continue

        # Reset selection counts
        for c in composites:
            c.selection_count = 0

        # Phase 2: Evaluate on held-out
        held_out_result = evaluate_on_held_out_with_composites(
            composites, held_out,
            n_programs=n_programs,
            program_length=program_length,
            n_iterations=n_iterations,
            n_per_iter=n_per_iter,
            seed=seed,
        )

        n_beats = held_out_result["n_beats_random"]
        n_selected = sum(1 for c in composites if c.selection_count > 0)
        total_selections = sum(c.selection_count for c in composites)

        print(f"  Composites: {n_composites}, Selected: {n_selected}/{n_composites} "
              f"({total_selections} total), Held-out beats: {n_beats}/{held_out_result['n_total']}")

        results.append({
            "seed": seed,
            "n_composites": n_composites,
            "n_selected": n_selected,
            "total_selections": total_selections,
            "n_beats": n_beats,
            "n_total": held_out_result["n_total"],
        })

    return results


def main():
    print("=" * 90)
    print("L5b SYNTHESIS — MULTI-SEED HELD-OUT (cycle 235)")
    print("5 seeds × synthesis + held-out evaluation")
    print("Is the 9/10 result stable across seeds?")
    print("=" * 90)
    print()

    training = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[:10]]
    held_out = [(p.problem_id, p.to_domain_spec(), p.forward) for p in BLIND_SUITE[10:]]

    results = run_multiseed_synthesis_heldout(
        training, held_out, seeds=SEEDS,
        n_programs=20, program_length=4,
        n_iterations=2, n_per_iter=12,
        synth_n_programs=30, synth_program_length=4,
        min_pair_frequency=2,
    )

    # Summary
    print()
    print("=" * 90)
    print("MULTI-SEED SYNTHESIS HELD-OUT SUMMARY")
    print("=" * 90)
    print()
    print(f"{'Seed':<8} {'Composites':<12} {'Selected':<12} {'Beats':<10}")
    print("-" * 45)
    for r in results:
        print(f"{r['seed']:<8} {r['n_composites']:<12} "
              f"{r['n_selected']}/{r['n_composites']:<12} "
              f"{r['n_beats']}/{r['n_total']:<10}")

    beats = [r["n_beats"] for r in results]
    n_composites_list = [r["n_composites"] for r in results]

    mean_beats = sum(beats) / len(beats)
    mean_composites = sum(n_composites_list) / len(n_composites_list)

    if len(beats) > 1:
        var = sum((b - mean_beats) ** 2 for b in beats) / len(beats)
        std_beats = math.sqrt(var)
    else:
        std_beats = 0

    print()
    print(f"Mean beats: {mean_beats:.1f}/10 (std={std_beats:.2f})")
    print(f"Mean composites: {mean_composites:.1f}")
    print(f"Per-seed beats: {beats}")
    print(f"Per-seed composites: {n_composites_list}")
    print()

    # L5b baseline was 5/10
    print(f"L5b baseline (no synthesis): 5/10")
    print(f"L5b+synthesis (multi-seed mean): {mean_beats:.1f}/10")
    print()

    if mean_beats >= 7:
        print(f"PASS: Multi-seed mean ({mean_beats:.1f}/10) ≥ 7. The 9/10 result is ROBUST.")
        print("The composites generalize across seeds — not seed luck.")
    elif mean_beats >= 5:
        print(f"PARTIAL: Multi-seed mean ({mean_beats:.1f}/10) ≥ 5 but < 7.")
        print("The composites help on average but the improvement is unstable.")
        print("Some seeds get 9/10; others get fewer. The variance is real.")
    else:
        print(f"FAIL: Multi-seed mean ({mean_beats:.1f}/10) < 5. The 9/10 was seed luck.")
        print("The composites do NOT reliably generalize across seeds.")
        print("The synthesis is unstable — different seeds produce different composites")
        print("with different held-out performance.")


if __name__ == "__main__":
    main()
