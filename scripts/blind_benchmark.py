#!/usr/bin/env python3
"""
blind_benchmark.py — Blind landscape classification benchmark (cycle 221).

Per auditor's update #11:
  "Don't benchmark technologies. Benchmark landscapes.
   Now ask: Can the meta-layer classify the landscape WITHOUT knowing
   which benchmark it is? If yes, you've built something much closer to
   a general search engine than a thermoelectric inventor."

This module:
  1. Collects all 11 landscapes (7 synthetic + 4 technology)
  2. STRIPS all domain identity (renames variables to x1..xn, outcome to y)
  3. Runs the classifier BLIND — it cannot know which landscape it is
  4. Reports: did the classifier produce a SENSIBLE classification
     (one of the 5 valid types) for each?

The classifier is NOT compared against "expected" labels here — because
the technology domains don't have a ground-truth landscape type (their
"true" type is itself a matter of interpretation). Instead, we verify:

  (a) The classifier produces a valid type (not UNKNOWN) for ≥9/11
  (b) The classification is STABLE across multiple seeds (same type
      for ≥80% of seeds per landscape)
  (c) The classification DIFFERS across landscapes (not all the same type)

If all three hold, the classifier is genuinely reading the landscape
shape, not defaulting to a single label.

Additionally, for the 7 SYNTHETIC landscapes, we DO have ground truth
(the expected classifications from synthetic_landscapes.py). We report
the blind classification accuracy on those 7.
"""
import sys
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.meta_invention import LandscapeClassifier, LandscapeType
from scripts.synthetic_landscapes import (
    SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN, RASTRIGIN_DOMAIN,
    NEEDLE_DOMAIN, DECEPTIVE_DOMAIN, CONSTRAINT_DOMAIN,
    sphere_forward, rosenbrock_forward, ackley_forward, rastrigin_forward,
    needle_forward, deceptive_forward, constraint_forward,
    EXPECTED_CLASSIFICATIONS,
)
from scripts.cross_domain_transfer import (
    THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
    thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
)


def strip_domain_identity(domain_spec: Dict, forward_fn: Callable) -> Tuple[Dict, Callable]:
    """Strip all domain identity from a landscape.

    Renames all design variables to x1, x2, ... and the outcome to 'y'.
    The classifier cannot tell whether this is a thermoelectric, battery,
    catalyst, PV, or synthetic landscape.
    """
    n_vars = len(domain_spec["design_vars"])
    stripped_vars = [
        {"name": f"x{i+1}", "bounds": v["bounds"], "human": f"x{i+1}"}
        for i, v in enumerate(domain_spec["design_vars"])
    ]
    stripped_spec = {
        "name": "anonymous",
        "outcome_name": "y",
        "outcome_target": 0.0,
        "design_vars": stripped_vars,
        "conditions": [],
    }

    # Wrapper: rename incoming design_point keys, call original forward_fn
    def stripped_forward(dp):
        # Map x1, x2, ... back to original variable names
        original_dp = {}
        for i, v in enumerate(domain_spec["design_vars"]):
            original_dp[v["name"]] = dp[f"x{i+1}"]
        outcome, derived = forward_fn(original_dp)
        # Strip derived of any identifying keys
        stripped_derived = {f"d{i+1}": v for i, v in enumerate(derived.values())}
        return outcome, stripped_derived

    return stripped_spec, stripped_forward


def sample_landscape(domain_spec: Dict, forward_fn: Callable,
                     n_samples: int, rng: random.Random) -> List:
    """Sample n candidates from a landscape."""
    cands = []
    for _ in range(n_samples):
        dp = {}
        for v in domain_spec["design_vars"]:
            lo, hi = v["bounds"]
            if lo > 0 and hi / lo > 100:
                val = math.exp(rng.uniform(math.log(lo), math.log(hi)))
            else:
                val = rng.uniform(lo, hi)
            dp[v["name"]] = val
        outcome, derived = forward_fn(dp)
        c = type("C", (), {"design_point": dp, "predicted_outcome": outcome,
                            "derived": derived})()
        cands.append(c)
    return cands


def main():
    print("=" * 78)
    print("BLIND LANDSCAPE CLASSIFICATION BENCHMARK (cycle 221)")
    print("Per auditor: 'Can the meta-layer classify the landscape")
    print("WITHOUT knowing which benchmark it is?'")
    print("=" * 78)
    print()

    # All 11 landscapes (7 synthetic + 4 technology)
    all_landscapes = [
        ("Sphere",        SPHERE_DOMAIN,        sphere_forward,        "synthetic"),
        ("Rosenbrock",    ROSENBROCK_DOMAIN,    rosenbrock_forward,    "synthetic"),
        ("Ackley",        ACKLEY_DOMAIN,        ackley_forward,        "synthetic"),
        ("Rastrigin",     RASTRIGIN_DOMAIN,     rastrigin_forward,     "synthetic"),
        ("Needle",        NEEDLE_DOMAIN,        needle_forward,        "synthetic"),
        ("Deceptive",     DECEPTIVE_DOMAIN,     deceptive_forward,     "synthetic"),
        ("Constraint",    CONSTRAINT_DOMAIN,    constraint_forward,    "synthetic"),
        ("Thermoelectric",THERMOELECTRIC_DOMAIN, thermoelectric_forward,"technology"),
        ("Battery",       BATTERY_DOMAIN,       battery_forward,       "technology"),
        ("Catalyst",      CATALYST_DOMAIN,      catalyst_forward,      "technology"),
        ("Photovoltaic",  PV_DOMAIN,            pv_forward,            "technology"),
    ]

    classifier = LandscapeClassifier()

    # === Test 1: Valid classification (not UNKNOWN) ===
    print("=" * 78)
    print("TEST 1: Does the classifier produce a valid type for each landscape?")
    print("=" * 78)
    print()
    print(f"{'Landscape':<16} {'Category':<12} {'Type':<22} {'Valid':<8}")
    print("-" * 60)

    n_valid = 0
    classifications = {}
    for name, spec, fn, category in all_landscapes:
        stripped_spec, stripped_fn = strip_domain_identity(spec, fn)
        rng = random.Random(42)
        cands = sample_landscape(stripped_spec, stripped_fn, 100, rng)
        sig = classifier.classify(cands, stripped_spec["design_vars"])
        is_valid = sig.landscape_type != LandscapeType.UNKNOWN
        if is_valid:
            n_valid += 1
        classifications[name] = sig.landscape_type.value
        print(f"{name:<16} {category:<12} {sig.landscape_type.value:<22} {'✓' if is_valid else '✗'}")

    print()
    print(f"Valid classifications: {n_valid}/11")
    print()

    # === Test 2: Stability across seeds ===
    print("=" * 78)
    print("TEST 2: Is the classification stable across 5 seeds?")
    print("=" * 78)
    print()
    print(f"{'Landscape':<16} {'Seed 42':<12} {'Seed 7':<12} {'Seed 99':<12} {'Seed 123':<12} {'Seed 256':<12} {'Stable':<8}")
    print("-" * 85)

    n_stable = 0
    for name, spec, fn, category in all_landscapes:
        stripped_spec, stripped_fn = strip_domain_identity(spec, fn)
        types = []
        for seed in [42, 7, 99, 123, 256]:
            rng = random.Random(seed)
            cands = sample_landscape(stripped_spec, stripped_fn, 100, rng)
            sig = classifier.classify(cands, stripped_spec["design_vars"])
            types.append(sig.landscape_type.value)
        # Stable if same type in >=80% of seeds (4/5)
        from collections import Counter
        most_common = Counter(types).most_common(1)[0]
        is_stable = most_common[1] >= 4
        if is_stable:
            n_stable += 1
        print(f"{name:<16} " + " ".join(f"{t:<12}" for t in types) + f" {'✓' if is_stable else '✗'}")

    print()
    print(f"Stable classifications: {n_stable}/11")
    print()

    # === Test 3: Diversity (not all the same type) ===
    print("=" * 78)
    print("TEST 3: Does the classification differ across landscapes?")
    print("=" * 78)
    print()
    from collections import Counter
    type_counts = Counter(classifications.values())
    print(f"Type distribution across 11 landscapes:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:<22} {count}")
    print()
    n_distinct = len(type_counts)
    print(f"Distinct types used: {n_distinct}/5")
    print(f"Diversity: {'✓' if n_distinct >= 3 else '✗'} (need ≥3 distinct types)")
    print()

    # === Test 4: Synthetic ground truth (the 7 with known expected types) ===
    print("=" * 78)
    print("TEST 4: Synthetic landscapes — blind accuracy vs ground truth")
    print("=" * 78)
    print()
    print(f"{'Landscape':<16} {'Expected':<22} {'Blind':<22} {'Match':<8}")
    print("-" * 65)

    n_correct = 0
    for name, spec, fn, category in all_landscapes:
        if category != "synthetic":
            continue
        expected = EXPECTED_CLASSIFICATIONS[spec["name"]]
        blind = classifications[name]
        match = "✓" if blind == expected else "✗"
        if blind == expected:
            n_correct += 1
        print(f"{name:<16} {expected:<22} {blind:<22} {match}")

    print()
    print(f"Blind accuracy on synthetic: {n_correct}/7")
    print()

    # === Summary ===
    print("=" * 78)
    print("BLIND BENCHMARK SUMMARY")
    print("=" * 78)
    print()
    print(f"Test 1 (valid type):     {n_valid}/11  (need ≥9)")
    print(f"Test 2 (stable):         {n_stable}/11  (need ≥9)")
    print(f"Test 3 (diverse):        {n_distinct}/5 distinct types  (need ≥3)")
    print(f"Test 4 (synthetic acc):  {n_correct}/7  (need ≥4)")
    print()
    all_pass = (n_valid >= 9 and n_stable >= 9 and n_distinct >= 3 and n_correct >= 4)
    print(f"OVERALL: {'PASS' if all_pass else 'FAIL'}")
    print()
    if all_pass:
        print("The classifier produces valid, stable, diverse classifications")
        print("WITHOUT knowing which landscape it is. This is genuine domain-")
        print("invariant classification — the auditor's primary verification.")
    else:
        print("One or more tests failed. The classifier may be defaulting to")
        print("a single label or producing unstable classifications.")


if __name__ == "__main__":
    main()
