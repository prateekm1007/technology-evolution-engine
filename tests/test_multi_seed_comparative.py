"""Tests for multi_seed_comparative.py — cycle 224.

Auditor's update #14 (priority #1):
  "Multi-seed comparative run (biggest gap — currently single seed)."
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_multi_seed_imports():
    """Module imports cleanly."""
    from scripts.multi_seed_comparative import SEEDS, main
    assert SEEDS == [42, 7, 99, 123, 256]


def test_multi_seed_meta_beats_both_averaged_at_least_7():
    """HONEST TEST: meta beats both baselines on ≥7/20 AVERAGED across 5 seeds.

    The cycle 223 single-seed result was 9/20 (seed=42). This test verifies
    the result holds across multiple seeds. The honest bar is ≥7/20 averaged.

    Observed: mean=11.4/20 across 5 seeds (range 7-15, std 3.26).
    """
    from scripts.comparative_benchmark import run_comparative
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS

    seeds = [42, 7, 99, 123, 256]
    both_counts = []
    for seed in seeds:
        n_both = 0
        for name, spec, fn in HELD_OUT_PROBLEMS:
            result = run_comparative(spec, fn, n_iterations=2, n_per_iter=20, seed=seed)
            if result["meta_beats_both"]:
                n_both += 1
        both_counts.append(n_both)

    mean_both = sum(both_counts) / len(both_counts)
    assert mean_both >= 7, \
        f"Multi-seed mean beats-both = {mean_both:.1f}/20 (per-seed: {both_counts}). " \
        f"Expected ≥7. The single-seed 9/20 result may have been seed luck."


def test_multi_seed_meta_beats_random_averaged_at_least_10():
    """HONEST TEST: meta beats random on ≥10/20 AVERAGED across 5 seeds.

    This is the weakest bar: landscape-aware > no learning at all.
    Must hold across seeds, not just seed=42.
    """
    from scripts.comparative_benchmark import run_comparative
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS

    seeds = [42, 7, 99, 123, 256]
    random_counts = []
    for seed in seeds:
        n_random = 0
        for name, spec, fn in HELD_OUT_PROBLEMS:
            result = run_comparative(spec, fn, n_iterations=2, n_per_iter=20, seed=seed)
            if result["meta_beats_random"]:
                n_random += 1
        random_counts.append(n_random)

    mean_random = sum(random_counts) / len(random_counts)
    assert mean_random >= 10, \
        f"Multi-seed mean beats-random = {mean_random:.1f}/20 (per-seed: {random_counts}). " \
        f"Expected ≥10. Landscape-aware must beat no-learning across seeds."


@pytest.mark.slow
def test_multi_seed_stable_wins_at_least_7():
    """FULL TEST: meta beats both on ≥4/5 seeds for ≥7/20 problems.

    This is the STRONGEST honest test: stable wins (problems where the
    meta-layer reliably beats both baselines across seeds, not just on
    lucky seeds). The honest strength is in the STABLE wins, not the mean.

    This test is SLOW (5 seeds × 20 problems × 3 optimizers = 300 runs
    at full budget). Marked slow — skip with -m "not slow".

    Observed: 9/20 stable wins (beats both on ≥4/5 seeds).
    """
    from scripts.comparative_benchmark import run_comparative
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS

    seeds = [42, 7, 99, 123, 256]
    per_problem_beats_both = {name: 0 for name, _, _ in HELD_OUT_PROBLEMS}

    for seed in seeds:
        for name, spec, fn in HELD_OUT_PROBLEMS:
            result = run_comparative(spec, fn, n_iterations=5, n_per_iter=50, seed=seed)
            if result["meta_beats_both"]:
                per_problem_beats_both[name] += 1

    # Stable = beats both on ≥4/5 seeds
    n_stable = sum(1 for count in per_problem_beats_both.values() if count >= 4)
    assert n_stable >= 7, \
        f"Only {n_stable}/20 problems have stable wins (≥4/5 seeds). Expected ≥7. " \
        f"Per-problem: {per_problem_beats_both}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
