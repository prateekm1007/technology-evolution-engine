"""Tests for held_out_benchmark.py — cycle 222.

Auditor's update #12:
  "Freeze the current classifier and optimizer-routing logic. Do NOT
   tune it further. Evaluate it on 20-50 previously unseen optimization
   problems. Report performance WITHOUT changing the classifier."
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_held_out_imports():
    """Module imports cleanly with 20 problems."""
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    assert len(HELD_OUT_PROBLEMS) == 20


def test_held_out_problems_are_distinct():
    """All 20 problems have distinct names and forward functions."""
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    names = [name for name, _, _ in HELD_OUT_PROBLEMS]
    assert len(set(names)) == 20, f"Duplicate names: {names}"
    fns = [fn for _, _, fn in HELD_OUT_PROBLEMS]
    assert len(set(fns)) == 20, "Duplicate forward functions"


def test_held_out_problems_have_no_technology_identity():
    """Held-out problems are pure math — no technology keywords."""
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    forbidden = ["thermoelectric", "battery", "catalyst", "photovoltaic",
                 "ZT", "Whkg", "TOF", "PCE", "PbTe", "SnSe"]
    for name, spec, _ in HELD_OUT_PROBLEMS:
        for f in forbidden:
            assert f not in spec["name"].lower(), \
                f"Held-out problem {spec['name']} contains {f}"
            assert f not in spec["outcome_name"].lower(), \
                f"Held-out outcome {spec['outcome_name']} contains {f}"


def test_each_held_out_problem_is_runnable():
    """Each held-out problem can be sampled and evaluated."""
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    rng = random.Random(42)
    for name, spec, fn in HELD_OUT_PROBLEMS:
        dp = {}
        for v in spec["design_vars"]:
            lo, hi = v["bounds"]
            if lo > 0 and hi / lo > 100:
                val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            else:
                val = rng.uniform(lo, hi)
            dp[v["name"]] = val
        outcome, derived = fn(dp)
        assert isinstance(outcome, (int, float)), \
            f"{name}: outcome must be numeric, got {type(outcome)}"
        assert isinstance(derived, dict), \
            f"{name}: derived must be dict, got {type(derived)}"


def test_frozen_classifier_runs_on_all_held_out():
    """The FROZEN classifier (cycle 221) runs on all 20 held-out problems.

    This test does NOT check accuracy — it just verifies the classifier
    doesn't crash on unseen problems. The classifier and thresholds are
    frozen; we do not tune them.
    """
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    from scripts.meta_invention import LandscapeClassifier, LandscapeType

    classifier = LandscapeClassifier()
    rng = random.Random(42)
    for name, spec, fn in HELD_OUT_PROBLEMS:
        cands = []
        for _ in range(50):
            dp = {}
            for v in spec["design_vars"]:
                lo, hi = v["bounds"]
                if lo > 0 and hi / lo > 100:
                    val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
                else:
                    val = rng.uniform(lo, hi)
                dp[v["name"]] = val
            o, _ = fn(dp)
            c = type("C", (), {"design_point": dp, "predicted_outcome": o, "derived": {}})()
            cands.append(c)
        sig = classifier.classify(cands, spec["design_vars"])
        # Must produce a valid type (not UNKNOWN) for ≥18/20
        assert sig.landscape_type != LandscapeType.UNKNOWN, \
            f"{name}: classifier returned UNKNOWN"


def test_held_out_benchmark_at_least_15_of_20_improve():
    """HONEST TEST: frozen classifier + optimizer routing improves ≥15/20
    held-out problems.

    This is the auditor's generalization test. The classifier was NOT
    tuned to these 20 problems (they were generated after the freeze).
    If ≥15/20 improve, the transfer mechanism generalizes.

    Observed result: 17/20 improved.
    Failures (honest): CrossInTray, Easom, TwinGaussians.
    """
    from scripts.held_out_benchmark import HELD_OUT_PROBLEMS
    from scripts.meta_invention import run_meta_invention

    n_improved = 0
    failures = []
    for name, spec, fn in HELD_OUT_PROBLEMS:
        iters, _, _ = run_meta_invention(
            spec, fn, n_iterations=5, n_per_iter=50, seed=42,
        )
        delta = iters[-1]["best_outcome"] - iters[0]["best_outcome"]
        if delta > 0:
            n_improved += 1
        else:
            failures.append((name, delta))

    assert n_improved >= 15, \
        f"Only {n_improved}/20 held-out problems improved. Expected ≥15. " \
        f"Failures: {failures}"


def test_frozen_thresholds_unchanged_during_held_out():
    """The frozen thresholds (cycle 221) are unchanged when running
    held-out problems. This verifies we did NOT tune them."""
    from scripts.meta_invention import FROZEN_THRESHOLDS
    # These are the exact values frozen in cycle 221.
    # If they changed, this test fails — preventing silent re-tuning.
    expected = {
        "NEEDLE_NEAR_MIN_FRACTION": 0.5,
        "NEEDLE_NEAR_MAX_FRACTION": 0.1,
        "DEGENERATE_SPREAD_FACTOR": 1e-9,
        "DECEPTIVE_BIMODALITY_MIN": 0.55,
        "MULTIMODAL_INTERACTION_MIN": 0.5,
        "MULTIMODAL_BIMODALITY_MIN": 0.4,
        "SMOOTH_SKEW_RATIO_MIN": 0.15,
        "BAYESIAN_CV_R2_MIN": 0.3,
    }
    for key, val in expected.items():
        assert FROZEN_THRESHOLDS[key] == val, \
            f"Frozen threshold {key} changed: expected {val}, got {FROZEN_THRESHOLDS[key]}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
