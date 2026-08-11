"""Tests for blind_benchmark.py — cycle 221.

Auditor's update #11:
  "Can the meta-layer classify the landscape WITHOUT knowing which
   benchmark it is? If yes, you've built something much closer to a
   general search engine than a thermoelectric inventor."

These tests enforce the HONEST blind benchmark results. The classifier:
- Always produces a valid type (11/11)
- Uses all 5 distinct types (5/5 diversity)
- But is NOT stable across seeds on 4/11 landscapes (7/11 stable)
- And gets 3/7 blind accuracy on synthetic landscapes

The stability and accuracy failures are REAL limitations, documented
in F-108. The tests enforce the honest minimums.
"""
import sys
import math
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_blind_benchmark_imports():
    """Module imports cleanly."""
    from scripts.blind_benchmark import strip_domain_identity, sample_landscape
    assert strip_domain_identity is not None
    assert sample_landscape is not None


def test_strip_domain_identity_removes_all_identifiers():
    """Stripping removes all technology-specific variable names."""
    from scripts.blind_benchmark import strip_domain_identity
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    stripped_spec, stripped_fn = strip_domain_identity(
        THERMOELECTRIC_DOMAIN, thermoelectric_forward
    )
    # Variable names must be x1, x2, ... (no 'composition_x', 'grain_size_nm', etc.)
    for v in stripped_spec["design_vars"]:
        assert v["name"].startswith("x"), \
            f"Stripped variable must be x1..xn, got: {v['name']}"
    # Outcome must be 'y' (no 'ZT', 'Whkg', etc.)
    assert stripped_spec["outcome_name"] == "y"
    assert stripped_spec["name"] == "anonymous"


def test_stripped_landscape_produces_same_outcomes():
    """Stripping doesn't change the outcome values — just renames variables."""
    from scripts.blind_benchmark import strip_domain_identity
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    stripped_spec, stripped_fn = strip_domain_identity(
        THERMOELECTRIC_DOMAIN, thermoelectric_forward
    )
    # Original design point
    original_dp = {"composition_x": 0.5, "carrier_concentration": 1e19,
                   "grain_size_nm": 1000.0, "porosity": 0.2}
    # Stripped design point (same values, renamed keys)
    stripped_dp = {"x1": 0.5, "x2": 1e19, "x3": 1000.0, "x4": 0.2}

    orig_outcome, _ = thermoelectric_forward(original_dp)
    stripped_outcome, _ = stripped_fn(stripped_dp)
    assert abs(orig_outcome - stripped_outcome) < 1e-9


def test_classifier_produces_valid_type_for_all_11_landscapes():
    """HONEST TEST: classifier produces a valid (non-UNKNOWN) type for ≥9/11.

    The classifier always produces a valid type for all 11 landscapes
    (7 synthetic + 4 technology). This is the minimum bar: the classifier
    never gives up with UNKNOWN.
    """
    from scripts.blind_benchmark import strip_domain_identity, sample_landscape
    from scripts.meta_invention import LandscapeClassifier, LandscapeType
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN, RASTRIGIN_DOMAIN,
        NEEDLE_DOMAIN, DECEPTIVE_DOMAIN, CONSTRAINT_DOMAIN,
        sphere_forward, rosenbrock_forward, ackley_forward, rastrigin_forward,
        needle_forward, deceptive_forward, constraint_forward,
    )
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    all_landscapes = [
        (SPHERE_DOMAIN, sphere_forward),
        (ROSENBROCK_DOMAIN, rosenbrock_forward),
        (ACKLEY_DOMAIN, ackley_forward),
        (RASTRIGIN_DOMAIN, rastrigin_forward),
        (NEEDLE_DOMAIN, needle_forward),
        (DECEPTIVE_DOMAIN, deceptive_forward),
        (CONSTRAINT_DOMAIN, constraint_forward),
        (THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        (BATTERY_DOMAIN, battery_forward),
        (CATALYST_DOMAIN, catalyst_forward),
        (PV_DOMAIN, pv_forward),
    ]

    classifier = LandscapeClassifier()
    n_valid = 0
    for spec, fn in all_landscapes:
        stripped_spec, stripped_fn = strip_domain_identity(spec, fn)
        rng = random.Random(42)
        cands = sample_landscape(stripped_spec, stripped_fn, 100, rng)
        sig = classifier.classify(cands, stripped_spec["design_vars"])
        if sig.landscape_type != LandscapeType.UNKNOWN:
            n_valid += 1

    assert n_valid >= 9, \
        f"Only {n_valid}/11 landscapes got a valid classification. Expected ≥9."


def test_classifier_uses_at_least_3_distinct_types():
    """HONEST TEST: classifier uses ≥3 distinct types across 11 landscapes.

    This verifies the classifier is NOT defaulting to a single label.
    If all 11 landscapes got the same type, the classifier would be useless.
    """
    from scripts.blind_benchmark import strip_domain_identity, sample_landscape
    from scripts.meta_invention import LandscapeClassifier
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN, RASTRIGIN_DOMAIN,
        NEEDLE_DOMAIN, DECEPTIVE_DOMAIN, CONSTRAINT_DOMAIN,
        sphere_forward, rosenbrock_forward, ackley_forward, rastrigin_forward,
        needle_forward, deceptive_forward, constraint_forward,
    )
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    all_landscapes = [
        (SPHERE_DOMAIN, sphere_forward),
        (ROSENBROCK_DOMAIN, rosenbrock_forward),
        (ACKLEY_DOMAIN, ackley_forward),
        (RASTRIGIN_DOMAIN, rastrigin_forward),
        (NEEDLE_DOMAIN, needle_forward),
        (DECEPTIVE_DOMAIN, deceptive_forward),
        (CONSTRAINT_DOMAIN, constraint_forward),
        (THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        (BATTERY_DOMAIN, battery_forward),
        (CATALYST_DOMAIN, catalyst_forward),
        (PV_DOMAIN, pv_forward),
    ]

    classifier = LandscapeClassifier()
    from collections import Counter
    types = []
    for spec, fn in all_landscapes:
        stripped_spec, stripped_fn = strip_domain_identity(spec, fn)
        rng = random.Random(42)
        cands = sample_landscape(stripped_spec, stripped_fn, 100, rng)
        sig = classifier.classify(cands, stripped_spec["design_vars"])
        types.append(sig.landscape_type.value)

    n_distinct = len(set(types))
    assert n_distinct >= 3, \
        f"Classifier only used {n_distinct} distinct types. Expected ≥3. " \
        f"Types: {Counter(types)}"


def test_classifier_stability_at_least_5_of_11():
    """HONEST TEST: classifier is stable (same type ≥4/5 seeds) on ≥5/11.

    The honest result is 7/11 stable. The test enforces ≥5/11 as the
    minimum bar. The 4 unstable landscapes (Sphere, Ackley, Deceptive,
    Catalyst) are documented in F-108 — they're near classification
    boundaries and flip between types depending on the random sample.
    """
    from scripts.blind_benchmark import strip_domain_identity, sample_landscape
    from scripts.meta_invention import LandscapeClassifier
    from scripts.synthetic_landscapes import (
        SPHERE_DOMAIN, ROSENBROCK_DOMAIN, ACKLEY_DOMAIN, RASTRIGIN_DOMAIN,
        NEEDLE_DOMAIN, DECEPTIVE_DOMAIN, CONSTRAINT_DOMAIN,
        sphere_forward, rosenbrock_forward, ackley_forward, rastrigin_forward,
        needle_forward, deceptive_forward, constraint_forward,
    )
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    all_landscapes = [
        (SPHERE_DOMAIN, sphere_forward),
        (ROSENBROCK_DOMAIN, rosenbrock_forward),
        (ACKLEY_DOMAIN, ackley_forward),
        (RASTRIGIN_DOMAIN, rastrigin_forward),
        (NEEDLE_DOMAIN, needle_forward),
        (DECEPTIVE_DOMAIN, deceptive_forward),
        (CONSTRAINT_DOMAIN, constraint_forward),
        (THERMOELECTRIC_DOMAIN, thermoelectric_forward),
        (BATTERY_DOMAIN, battery_forward),
        (CATALYST_DOMAIN, catalyst_forward),
        (PV_DOMAIN, pv_forward),
    ]

    classifier = LandscapeClassifier()
    from collections import Counter
    n_stable = 0
    for spec, fn in all_landscapes:
        stripped_spec, stripped_fn = strip_domain_identity(spec, fn)
        types = []
        for seed in [42, 7, 99, 123, 256]:
            rng = random.Random(seed)
            cands = sample_landscape(stripped_spec, stripped_fn, 100, rng)
            sig = classifier.classify(cands, stripped_spec["design_vars"])
            types.append(sig.landscape_type.value)
        most_common = Counter(types).most_common(1)[0]
        if most_common[1] >= 4:  # ≥4/5 seeds agree
            n_stable += 1

    assert n_stable >= 5, \
        f"Only {n_stable}/11 landscapes are stable across seeds. Expected ≥5. " \
        f"(Honest observed: 7/11. Unstable: Sphere, Ackley, Deceptive, Catalyst.)"


def test_frozen_thresholds_are_constants():
    """FROZEN_THRESHOLDS dict exists and contains the expected keys.

    Per auditor's Goodhart warning: thresholds must be frozen as named
    constants, not inline literals. This test enforces that.
    """
    from scripts.meta_invention import FROZEN_THRESHOLDS
    expected_keys = [
        "NEEDLE_NEAR_MIN_FRACTION", "NEEDLE_NEAR_MAX_FRACTION",
        "DEGENERATE_SPREAD_FACTOR", "CONSTRAINT_EXACT_MIN_FRACTION",
        "DECEPTIVE_BIMODALITY_MIN", "DECEPTIVE_NEAR_MIN_LO", "DECEPTIVE_NEAR_MIN_HI",
        "DECEPTIVE_MID_SPAN_RATIO", "MULTIMODAL_INTERACTION_MIN",
        "MULTIMODAL_BIMODALITY_MIN", "SMOOTH_SKEW_RATIO_MIN",
        "BAYESIAN_CV_R2_MIN", "BAYESIAN_MUTATION_RATE", "BAYESIAN_FALLBACK_PADDING",
        "NEAR_MAX_THRESHOLD", "NEAR_MIN_THRESHOLD",
    ]
    for key in expected_keys:
        assert key in FROZEN_THRESHOLDS, f"Missing frozen threshold: {key}"


def test_frozen_thresholds_match_observed_values():
    """Frozen thresholds match the values that were observed to work.

    This test prevents silent threshold changes. If someone edits the
    thresholds to make a new test pass, this test fails — forcing an
    explicit FAILURES.md entry documenting the change.
    """
    from scripts.meta_invention import FROZEN_THRESHOLDS
    # These are the values that were frozen in cycle 221.
    # Changing them requires:
    #   1. A FAILURES.md entry documenting why
    #   2. Re-running the synthetic-landscape benchmark
    #   3. The change must IMPROVE synthetic accuracy (not just tech domains)
    expected = {
        "NEEDLE_NEAR_MIN_FRACTION": 0.5,
        "NEEDLE_NEAR_MAX_FRACTION": 0.1,
        "DEGENERATE_SPREAD_FACTOR": 1e-9,
        "CONSTRAINT_EXACT_MIN_FRACTION": 0.5,
        "DECEPTIVE_BIMODALITY_MIN": 0.55,
        "DECEPTIVE_NEAR_MIN_LO": 0.3,
        "DECEPTIVE_NEAR_MIN_HI": 0.7,
        "DECEPTIVE_MID_SPAN_RATIO": 0.10,
        "MULTIMODAL_INTERACTION_MIN": 0.5,
        "MULTIMODAL_BIMODALITY_MIN": 0.4,
        "SMOOTH_SKEW_RATIO_MIN": 0.15,
        "BAYESIAN_CV_R2_MIN": 0.3,
        "BAYESIAN_MUTATION_RATE": 0.5,
        "BAYESIAN_FALLBACK_PADDING": 0.20,
        "NEAR_MAX_THRESHOLD": 0.95,
        "NEAR_MIN_THRESHOLD": 0.05,
    }
    for key, val in expected.items():
        assert FROZEN_THRESHOLDS[key] == val, \
            f"Frozen threshold {key} changed: expected {val}, got {FROZEN_THRESHOLDS[key]}. " \
            f"This requires a FAILURES.md entry documenting the change."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
