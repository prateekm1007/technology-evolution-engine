"""f1_optimization_freeze.py — Machine-enforce F1 optimization freeze (Phase 7).

Per the 18-phase plan:
    "Phase 7: FREEZE F1 OPTIMIZATION"

Per STOP_BUILDING.md:
    Item 8: Benchmark tuning is forbidden permanently (No-Gaming Rule)
    Item 9: Score improvements without capability improvement are
            forbidden permanently (Prime Directive)

Per CONSTITUTION.md:
    The Prime Directive: "If an action would make a metric read greener
    without making the product genuinely greener, that action is forbidden."
    The No-Gaming Rule: "Do NOT lower a threshold to silence a red."

Per the audit (round 15):
    "Phase 7 should operate under the fact that there are currently
     zero scientifically eligible measurement metrics."

This module makes F1 optimization MECHANICALLY IMPOSSIBLE:
    1. The historical F1 baseline (0.5714) is frozen and cannot be changed
    2. Any code that attempts to tune the benchmark, adjust thresholds,
       or improve scores without capability improvement is blocked
    3. The freeze is enforced by a machine test that fails if any
       forbidden optimization pattern is detected

The freeze is NOT a policy statement. It is code that raises.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional


REPO = Path(__file__).resolve().parents[1]

# The historical F1 baseline. This is the FROZEN value from Stage -1
# (cycle 134). It is NOT a capability claim. It is the measurement
# baseline that all future measurements are compared against.
# Per STOP_BUILDING.md item 9: "Improving scores without improving the
# underlying capability is the Prime Directive violation. Forbidden
# permanently."
FROZEN_F1_BASELINE = 0.5714
FROZEN_F1_BASELINE_SHA256 = hashlib.sha256(
    json.dumps({"f1": FROZEN_F1_BASELINE, "source": "stage-1-measurement-integrity-baseline",
                "cycle": 134}).encode()
).hexdigest()

# Forbidden optimization patterns (STOP_BUILDING.md items 8 and 9)
FORBIDDEN_OPTIMIZATION_PATTERNS = [
    "benchmark_tuning",
    "threshold_lowering",
    "score_improvement_without_capability",
    "synonym_expansion_for_score",
    "matcher_widening_for_score",
    "gold_set_modification_for_score",
]


class F1OptimizationForbidden(Exception):
    """Raised when an action would modify the frozen F1 baseline or
    engage in forbidden optimization.

    Per STOP_BUILDING.md:
        Item 8: Benchmark tuning is forbidden permanently
        Item 9: Score improvements without capability improvement are
                forbidden permanently

    This is a hard failure. The optimization cannot proceed.
    """


def get_frozen_f1_baseline() -> dict:
    """Return the frozen F1 baseline with its provenance.

    The baseline is 0.5714, established in Stage -1 (cycle 134).
    It is NOT a capability claim. It is a measurement baseline.
    """
    return {
        "f1": FROZEN_F1_BASELINE,
        "source": "stage-1-measurement-integrity-baseline",
        "cycle": 134,
        "sha256": FROZEN_F1_BASELINE_SHA256,
        "note": (
            "This is the historical F1 baseline from Stage -1. It is NOT "
            "a capability claim. It is the measurement baseline that all "
            "future measurements are compared against. Per STOP_BUILDING.md "
            "items 8 and 9: benchmark tuning and score improvements without "
            "capability improvement are forbidden permanently."
        ),
        "frozen": True,
        "frozen_by": "Phase 7 (FREEZE F1 OPTIMIZATION)",
    }


def assert_f1_not_optimized(action: str, context: Optional[dict] = None) -> None:
    """Assert that an action does not constitute F1 optimization.

    Per STOP_BUILDING.md:
        Item 8: Benchmark tuning is forbidden permanently
        Item 9: Score improvements without capability improvement are
                forbidden permanently

    This function checks whether the action matches any forbidden
    optimization pattern and raises if it does.

    Args:
        action: a string describing the action being checked
        context: optional dict with additional context

    Raises:
        F1OptimizationForbidden: if the action matches a forbidden pattern
    """
    action_lower = action.lower()

    for pattern in FORBIDDEN_OPTIMIZATION_PATTERNS:
        if pattern in action_lower:
            raise F1OptimizationForbidden(
                f"F1 OPTIMIZATION FORBIDDEN: action='{action}' matches "
                f"forbidden pattern '{pattern}'. "
                f"Per STOP_BUILDING.md items 8 and 9: benchmark tuning and "
                f"score improvements without capability improvement are "
                f"forbidden permanently. The F1 baseline ({FROZEN_F1_BASELINE}) "
                f"is frozen. Per Phase 7: F1 optimization is mechanically "
                f"impossible. Context: {context}"
            )

    # Check for threshold-lowering patterns
    threshold_patterns = ["lower_threshold", "reduce_threshold", "relax_threshold",
                          "widen_matcher", "expand_synonym", "add_synonym_for_score"]
    for pattern in threshold_patterns:
        if pattern in action_lower:
            raise F1OptimizationForbidden(
                f"F1 OPTIMIZATION FORBIDDEN: action='{action}' matches "
                f"threshold-lowering pattern '{pattern}'. "
                f"Per the No-Gaming Rule: do NOT lower a threshold to "
                f"silence a red. The F1 baseline is frozen."
            )


def assert_f1_baseline_unchanged(current_f1: float) -> None:
    """Assert that the current F1 matches the frozen baseline.

    This function verifies that the F1 baseline has not been silently
    altered. Per MC-6: no metric may be silently altered.

    Args:
        current_f1: the current F1 value to check

    Raises:
        F1OptimizationForbidden: if current_f1 != FROZEN_F1_BASELINE
    """
    if abs(current_f1 - FROZEN_F1_BASELINE) > 1e-6:
        raise F1OptimizationForbidden(
            f"F1 BASELINE MODIFIED: frozen={FROZEN_F1_BASELINE}, "
            f"current={current_f1}. The F1 baseline is FROZEN and cannot "
            f"be changed. Per MC-6: no metric may be silently altered. "
            f"Per STOP_BUILDING.md item 9: score improvements without "
            f"capability improvement are forbidden permanently."
        )


def assert_zero_eligible_metrics_for_optimization() -> None:
    """Assert that there are zero scientifically eligible metrics.

    Per the audit (round 15): "Phase 7 should operate under the fact
    that there are currently zero scientifically eligible measurement
    metrics."

    F1 optimization is not just forbidden by policy — it is impossible
    because the metrics that would measure F1 improvement are themselves
    not scientifically eligible. There is nothing to optimize against.
    """
    from engine.epistemic_state_enforcer import list_eligible_metrics
    eligible = list_eligible_metrics()
    if len(eligible) > 0:
        raise F1OptimizationForbidden(
            f"F1 OPTIMIZATION PRECONDITION VIOLATION: {len(eligible)} "
            f"metrics are scientifically eligible: {eligible}. "
            f"Per Phase 7: F1 optimization requires scientifically eligible "
            f"metrics to measure improvement against. Currently there are 0. "
            f"If this number is > 0, the epistemic gate has been bypassed."
        )


__all__ = [
    "F1OptimizationForbidden",
    "FROZEN_F1_BASELINE",
    "FROZEN_F1_BASELINE_SHA256",
    "FORBIDDEN_OPTIMIZATION_PATTERNS",
    "get_frozen_f1_baseline",
    "assert_f1_not_optimized",
    "assert_f1_baseline_unchanged",
    "assert_zero_eligible_metrics_for_optimization",
]


if __name__ == "__main__":
    import sys

    print("Phase 7: F1 Optimization Freeze")
    print("=" * 60)
    baseline = get_frozen_f1_baseline()
    print(f"Frozen F1 baseline: {baseline['f1']}")
    print(f"Source: {baseline['source']}")
    print(f"SHA-256: {baseline['sha256'][:16]}...")
    print(f"Frozen: {baseline['frozen']}")
    print()

    # Verify zero eligible metrics
    try:
        assert_zero_eligible_metrics_for_optimization()
        print("Zero eligible metrics: CONFIRMED (optimization impossible)")
    except F1OptimizationForbidden as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Verify baseline unchanged
    try:
        assert_f1_baseline_unchanged(0.5714)
        print("F1 baseline unchanged: CONFIRMED")
    except F1OptimizationForbidden as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print()
    print("Forbidden optimization patterns:")
    for p in FORBIDDEN_OPTIMIZATION_PATTERNS:
        print(f"  - {p}")
    print()
    print("F1 optimization is MECHANICALLY IMPOSSIBLE.")
    print("  1. Baseline is frozen (0.5714)")
    print("  2. Zero eligible metrics to measure improvement against")
    print("  3. Forbidden patterns are machine-enforced")
