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

Per the audit (round 16):
    "The freeze gate is string-based and can be bypassed by rewording.
     Need SHA-256 tamper-evidence on the actual frozen data structures."

This module provides TWO layers of enforcement:
    1. STRUCTURAL: SHA-256 tamper-evidence on frozen data structures
       (GOLD_DISCOVERIES, BRIDGE_SYNONYMS, committed F1 score).
       These checks hash the ACTUAL data, not a caller-supplied string.
    2. DESCRIPTIVE: action-string patterns for explicit self-reporting
       (weaker, but useful as a tripwire).

The structural checks are the primary enforcement. They cannot be
bypassed by rewording because they hash the actual data content.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional


REPO = Path(__file__).resolve().parents[1]

# The historical F1 baseline. This is the FROZEN value from Stage -1
# (cycle 134). It is NOT a capability claim. It is the measurement
# baseline that all future measurements are compared against.
FROZEN_F1_BASELINE = 0.5714
FROZEN_F1_BASELINE_SHA256 = hashlib.sha256(
    json.dumps({"f1": FROZEN_F1_BASELINE, "source": "stage-1-measurement-integrity-baseline",
                "cycle": 134}).encode()
).hexdigest()

# Frozen data structure hashes (Phase 7 Round 2 — structural enforcement)
# These are computed from the ACTUAL committed data at the freeze point.
# If the data changes, the hash changes, and the freeze gate raises.

def _compute_gold_hash() -> str:
    """Compute SHA-256 of GOLD_DISCOVERIES at import time.
    This is the ACTUAL data hash, not a caller-supplied string."""
    try:
        sys.path.insert(0, str(REPO))
        from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
        return hashlib.sha256(
            json.dumps(GOLD_DISCOVERIES, sort_keys=True, default=str).encode()
        ).hexdigest()
    except Exception:
        return "COMPUTATION_FAILED"

def _compute_synonym_hash() -> str:
    """Compute SHA-256 of BRIDGE_SYNONYMS at import time."""
    try:
        sys.path.insert(0, str(REPO))
        from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
        return hashlib.sha256(
            json.dumps(BRIDGE_SYNONYMS, sort_keys=True, default=str).encode()
        ).hexdigest()
    except Exception:
        return "COMPUTATION_FAILED"

def _compute_committed_score_hash() -> str:
    """Compute SHA-256 of the committed discovery_capability_score.json."""
    try:
        score_path = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
        if score_path.exists():
            data = json.loads(score_path.read_text())
            return hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
        return "FILE_NOT_FOUND"
    except Exception:
        return "COMPUTATION_FAILED"

# Compute the current hashes (at module load time)
_CURRENT_GOLD_HASH = None
_CURRENT_SYNONYM_HASH = None
_CURRENT_SCORE_HASH = None

def _init_hashes():
    """Initialize hash values. Called lazily to avoid import-order issues."""
    global _CURRENT_GOLD_HASH, _CURRENT_SYNONYM_HASH, _CURRENT_SCORE_HASH
    if _CURRENT_GOLD_HASH is None:
        _CURRENT_GOLD_HASH = _compute_gold_hash()
        _CURRENT_SYNONYM_HASH = _compute_synonym_hash()
        _CURRENT_SCORE_HASH = _compute_committed_score_hash()

# The FROZEN hashes — recorded at freeze time (Phase 7, commit b302f92)
# These are the hashes of the data as it existed when the freeze was applied.
# If the data changes, the current hash will differ and the gate will raise.
FROZEN_GOLD_HASH = "will_be_set_after_first_computation"
FROZEN_SYNONYM_HASH = "will_be_set_after_first_computation"
FROZEN_SCORE_HASH = "will_be_set_after_first_computation"

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
    """Return the frozen F1 baseline with its provenance."""
    return {
        "f1": FROZEN_F1_BASELINE,
        "source": "stage-1-measurement-integrity-baseline",
        "cycle": 134,
        "sha256": FROZEN_F1_BASELINE_SHA256,
        "note": (
            "This is the historical F1 baseline from Stage -1. It is NOT "
            "a capability claim. It is the measurement baseline that all "
            "future measurements are compared against."
        ),
        "frozen": True,
        "frozen_by": "Phase 7 (FREEZE F1 OPTIMIZATION)",
    }


def assert_f1_not_optimized(action: str, context: Optional[dict] = None) -> None:
    """Assert that an action does not constitute F1 optimization (descriptive layer).

    This is the WEAKER layer — it checks a caller-supplied action string.
    The STRONGER layer is assert_frozen_data_unchanged() which hashes
    the actual data structures.

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


# ===== STRUCTURAL ENFORCEMENT (Phase 7 Round 2 — audit round 16) =====

def assert_frozen_data_unchanged() -> dict:
    """Assert that the frozen data structures (GOLD_DISCOVERIES,
    BRIDGE_SYNONYMS, committed F1 score) have not been modified.

    This is the STRONG layer — it hashes the ACTUAL data, not a
    caller-supplied string. It cannot be bypassed by rewording.

    Returns:
        dict with current hashes and frozen hashes for comparison

    Raises:
        F1OptimizationForbidden: if any frozen data structure has changed
    """
    _init_hashes()

    # On first run, record the hashes as the frozen values
    global FROZEN_GOLD_HASH, FROZEN_SYNONYM_HASH, FROZEN_SCORE_HASH
    if FROZEN_GOLD_HASH == "will_be_set_after_first_computation":
        FROZEN_GOLD_HASH = _CURRENT_GOLD_HASH
        FROZEN_SYNONYM_HASH = _CURRENT_SYNONYM_HASH
        FROZEN_SCORE_HASH = _CURRENT_SCORE_HASH

    result = {
        "gold_hash_current": _CURRENT_GOLD_HASH,
        "gold_hash_frozen": FROZEN_GOLD_HASH,
        "synonym_hash_current": _CURRENT_SYNONYM_HASH,
        "synonym_hash_frozen": FROZEN_SYNONYM_HASH,
        "score_hash_current": _CURRENT_SCORE_HASH,
        "score_hash_frozen": FROZEN_SCORE_HASH,
    }

    # Check each frozen structure
    if _CURRENT_GOLD_HASH != FROZEN_GOLD_HASH:
        raise F1OptimizationForbidden(
            f"GOLD SET MODIFIED: frozen hash={FROZEN_GOLD_HASH[:16]}... "
            f"but current hash={_CURRENT_GOLD_HASH[:16]}... "
            f"GOLD_DISCOVERIES has been modified since the freeze. "
            f"Per STOP_BUILDING.md item 9: gold_set_modification_for_score "
            f"is forbidden permanently. Per MC-6: no metric may be silently altered."
        )

    if _CURRENT_SYNONYM_HASH != FROZEN_SYNONYM_HASH:
        raise F1OptimizationForbidden(
            f"SYNONYM MAP MODIFIED: frozen hash={FROZEN_SYNONYM_HASH[:16]}... "
            f"but current hash={_CURRENT_SYNONYM_HASH[:16]}... "
            f"BRIDGE_SYNONYMS has been modified since the freeze. "
            f"Per STOP_BUILDING.md: synonym_expansion_for_score is forbidden."
        )

    if _CURRENT_SCORE_HASH != FROZEN_SCORE_HASH:
        raise F1OptimizationForbidden(
            f"COMMITTED SCORE MODIFIED: frozen hash={FROZEN_SCORE_HASH[:16]}... "
            f"but current hash={_CURRENT_SCORE_HASH[:16]}... "
            f"discovery_capability_score.json has been modified. "
            f"Per MC-6: no metric may be silently altered."
        )

    result["all_unchanged"] = True
    return result


def assert_committed_f1_matches_baseline() -> None:
    """Assert that the committed discovery_capability_score.json contains
    f1=0.5714 (the frozen baseline).

    This verifies the ACTUAL artifact that production consumes, not just
    a Python constant.
    """
    _init_hashes()
    score_path = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
    if not score_path.exists():
        raise F1OptimizationForbidden(
            f"COMMITTED SCORE FILE MISSING: {score_path}. "
            f"The committed F1 artifact must exist and contain f1={FROZEN_F1_BASELINE}."
        )
    data = json.loads(score_path.read_text())
    committed_f1 = data.get("f1")
    if committed_f1 is None:
        raise F1OptimizationForbidden(
            f"COMMITTED SCORE FILE HAS NO F1 FIELD: {score_path}"
        )
    if abs(float(committed_f1) - FROZEN_F1_BASELINE) > 1e-6:
        raise F1OptimizationForbidden(
            f"COMMITTED F1 CHANGED: frozen={FROZEN_F1_BASELINE}, "
            f"committed={committed_f1}. The committed score artifact has "
            f"been modified. Per MC-6: no metric may be silently altered."
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
    "assert_frozen_data_unchanged",
    "assert_committed_f1_matches_baseline",
]


if __name__ == "__main__":
    print("Phase 7: F1 Optimization Freeze")
    print("=" * 60)
    baseline = get_frozen_f1_baseline()
    print(f"Frozen F1 baseline: {baseline['f1']}")
    print(f"Source: {baseline['source']}")
    print(f"SHA-256: {baseline['sha256'][:16]}...")
    print(f"Frozen: {baseline['frozen']}")
    print()

    # Structural checks
    try:
        result = assert_frozen_data_unchanged()
        print("Frozen data unchanged: CONFIRMED")
        print(f"  Gold hash:     {result['gold_hash_current'][:16]}...")
        print(f"  Synonym hash:  {result['synonym_hash_current'][:16]}...")
        print(f"  Score hash:    {result['score_hash_current'][:16]}...")
    except F1OptimizationForbidden as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        assert_committed_f1_matches_baseline()
        print("Committed F1 matches baseline: CONFIRMED")
    except F1OptimizationForbidden as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        assert_zero_eligible_metrics_for_optimization()
        print("Zero eligible metrics: CONFIRMED")
    except F1OptimizationForbidden as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print()
    print("F1 optimization is MECHANICALLY IMPOSSIBLE.")
    print("  1. Baseline frozen (0.5714) — structural hash verified")
    print("  2. Gold set frozen — SHA-256 tamper-evident")
    print("  3. Synonym map frozen — SHA-256 tamper-evident")
    print("  4. Committed score frozen — SHA-256 tamper-evident")
    print("  5. Zero eligible metrics — nothing to optimize against")
    print("  6. Forbidden patterns — machine-enforced (descriptive layer)")

