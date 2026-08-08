"""f1_optimization_freeze.py — Machine-enforce F1 optimization freeze (Phase 7 R3).

Per audit round 17:
    "The structural hash is not actually frozen. The first execution
     defines the freeze. That is not tamper-evidence."

    "The freeze needs a committed, immutable-at-runtime reference artifact
     created at the actual freeze point."

    "Never: hash current artifacts → if no baseline exists: make current
     artifacts the baseline."

This module loads an IMMUTABLE committed manifest
(reports/phase7/frozen_f1_manifest.json) and compares current production
hashes against the manifest values. It NEVER self-baselines. If the
manifest is missing, the gate fails closed. If hash computation fails,
the gate fails closed (P6: never write bare except Exception).

Enforcement layers:
    1. STRUCTURAL: SHA-256 tamper-evidence against immutable manifest
    2. DESCRIPTIVE: action-string patterns (weaker tripwire)
    3. EPISTEMIC: zero eligible metrics (nothing to optimize against)
    4. POST_COMPUTATION: F1 result checked against frozen baseline
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Optional


REPO = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO / "reports" / "phase7" / "frozen_f1_manifest.json"

FROZEN_F1_BASELINE = 0.5714
FROZEN_F1_BASELINE_SHA256 = hashlib.sha256(
    json.dumps({"f1": FROZEN_F1_BASELINE, "source": "stage-1-measurement-integrity-baseline",
                "cycle": 134}).encode()
).hexdigest()

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
    engage in forbidden optimization. Hard failure — operation cannot proceed."""
    pass


class FreezeManifestMissing(F1OptimizationForbidden):
    """Raised when the immutable freeze manifest is missing.
    The gate fails closed — no manifest = no freeze = no execution."""
    pass


class FreezeManifestCorrupt(F1OptimizationForbidden):
    """Raised when the freeze manifest is malformed or missing required fields."""
    pass


class HashComputationFailed(F1OptimizationForbidden):
    """Raised when hash computation fails. Per P6: fail closed, not open.
    A failed hash computation must NOT produce a fallback string that
    could become a baseline."""
    pass


def _load_manifest() -> dict:
    """Load the immutable freeze manifest and verify it against git HEAD.

    Per audit round 18:
        "The manifest is a mutable repository file. Nothing verifies that
         the manifest itself is the originally committed manifest."

    This function:
        1. Reads the manifest from disk
        2. Reads the manifest from git HEAD (git cat-file)
        3. Compares them — if they differ, the manifest has been substituted
        4. Validates required fields

    Raises:
        FreezeManifestMissing: manifest file does not exist
        FreezeManifestCorrupt: manifest is malformed or missing fields
        F1OptimizationForbidden: manifest on disk doesn't match git HEAD
    """
    import subprocess

    if not MANIFEST_PATH.exists():
        raise FreezeManifestMissing(
            f"F1 FREEZE MANIFEST MISSING: {MANIFEST_PATH}. "
            f"The immutable freeze manifest must exist. Without it, the "
            f"freeze gate cannot verify that data has not been modified. "
            f"Per Phase 7 Round 3: the gate fails closed when the manifest "
            f"is missing. It NEVER self-baselines."
        )

    # Read the on-disk manifest
    disk_content = MANIFEST_PATH.read_text()

    # Read the git-committed manifest at HEAD
    try:
        result = subprocess.run(
            ["git", "cat-file", "blob", f"HEAD:{MANIFEST_PATH.relative_to(REPO)}"],
            cwd=REPO, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise FreezeManifestCorrupt(
                f"F1 FREEZE MANIFEST NOT IN GIT: cannot read "
                f"HEAD:{MANIFEST_PATH.relative_to(REPO)}. "
                f"git error: {result.stderr.strip()[:200]}. "
                f"The manifest must be committed to git."
            )
        git_content = result.stdout
    except FreezeManifestCorrupt:
        raise
    except Exception as e:
        raise HashComputationFailed(
            f"MANIFEST GIT VERIFICATION FAILED: {type(e).__name__}: {e}. "
            f"Per P6: fail closed. Cannot verify manifest against git HEAD."
        )

    # Verify on-disk matches git HEAD (prevents manifest substitution)
    if disk_content != git_content:
        raise F1OptimizationForbidden(
            f"MANIFEST SUBSTITUTION DETECTED: the manifest on disk does not "
            f"match the manifest committed at git HEAD. This means the manifest "
            f"has been locally modified after being committed. An attacker who "
            f"modifies both the manifest and the production data would be caught "
            f"here because the modified manifest doesn't match the git-committed "
            f"version. Per Phase 7 Round 4: the thing that defines the freeze "
            f"cannot be allowed to redefine itself."
        )

    # Parse the (verified) manifest
    try:
        manifest = json.loads(disk_content)
    except json.JSONDecodeError as e:
        raise FreezeManifestCorrupt(
            f"F1 FREEZE MANIFEST CORRUPT: {MANIFEST_PATH} is not valid JSON: {e}"
        )

    required_fields = [
        "gold_discoveries_sha256", "bridge_synonyms_sha256",
        "score_artifact_sha256", "benchmark_source_sha256",
        "baseline_f1", "immutable_reference"
    ]
    for field in required_fields:
        if field not in manifest:
            raise FreezeManifestCorrupt(
                f"F1 FREEZE MANIFEST CORRUPT: missing required field '{field}'"
            )

    if manifest.get("immutable_reference") is not True:
        raise FreezeManifestCorrupt(
            f"F1 FREEZE MANIFEST CORRUPT: immutable_reference must be true"
        )

    # Cross-validate: manifest baseline_f1 must match the Python constant
    manifest_f1 = manifest.get("baseline_f1")
    if manifest_f1 is not None and abs(float(manifest_f1) - FROZEN_F1_BASELINE) > 1e-6:
        raise F1OptimizationForbidden(
            f"F1 BASELINE MISMATCH BETWEEN SOURCES: "
            f"manifest baseline_f1={manifest_f1} but Python constant "
            f"FROZEN_F1_BASELINE={FROZEN_F1_BASELINE}. These must agree. "
            f"Per audit round 18: single source of truth for the baseline."
        )

    return manifest


def _compute_gold_hash() -> str:
    """Compute SHA-256 of GOLD_DISCOVERIES. Fail closed on any error."""
    try:
        sys.path.insert(0, str(REPO))
        from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
        return hashlib.sha256(
            json.dumps(GOLD_DISCOVERIES, sort_keys=True, default=str).encode()
        ).hexdigest()
    except Exception as e:
        raise HashComputationFailed(
            f"HASH COMPUTATION FAILED (GOLD_DISCOVERIES): {type(e).__name__}: {e}. "
            f"Per P6: fail closed. A failed hash computation must NOT produce "
            f"a fallback string. The gate cannot proceed without a valid hash."
        )


def _compute_synonym_hash() -> str:
    """Compute SHA-256 of BRIDGE_SYNONYMS. Fail closed on any error."""
    try:
        sys.path.insert(0, str(REPO))
        from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
        return hashlib.sha256(
            json.dumps(BRIDGE_SYNONYMS, sort_keys=True, default=str).encode()
        ).hexdigest()
    except Exception as e:
        raise HashComputationFailed(
            f"HASH COMPUTATION FAILED (BRIDGE_SYNONYMS): {type(e).__name__}: {e}. "
            f"Per P6: fail closed."
        )


def _compute_score_hash() -> str:
    """Compute SHA-256 of committed discovery_capability_score.json. Fail closed."""
    try:
        score_path = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
        if not score_path.exists():
            raise HashComputationFailed(
                f"HASH COMPUTATION FAILED: committed score file missing: {score_path}"
            )
        data = json.loads(score_path.read_text())
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
    except HashComputationFailed:
        raise
    except Exception as e:
        raise HashComputationFailed(
            f"HASH COMPUTATION FAILED (score artifact): {type(e).__name__}: {e}. "
            f"Per P6: fail closed."
        )


def _compute_benchmark_source_hash() -> str:
    """Compute SHA-256 of the benchmark source file. Fail closed."""
    try:
        path = REPO / "benchmarks" / "discovery_capability_benchmark.py"
        if not path.exists():
            raise HashComputationFailed(
                f"HASH COMPUTATION FAILED: benchmark source file missing: {path}"
            )
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except HashComputationFailed:
        raise
    except Exception as e:
        raise HashComputationFailed(
            f"HASH COMPUTATION FAILED (benchmark source): {type(e).__name__}: {e}. "
            f"Per P6: fail closed."
        )


def get_frozen_f1_baseline() -> dict:
    """Return the frozen F1 baseline with provenance."""
    return {
        "f1": FROZEN_F1_BASELINE,
        "source": "stage-1-measurement-integrity-baseline",
        "cycle": 134,
        "sha256": FROZEN_F1_BASELINE_SHA256,
        "frozen": True,
        "frozen_by": "Phase 7 (FREEZE F1 OPTIMIZATION)",
    }


def assert_f1_not_optimized(action: str, context: Optional[dict] = None) -> None:
    """Descriptive layer (weaker tripwire). Checks caller-supplied action string."""
    action_lower = action.lower()
    for pattern in FORBIDDEN_OPTIMIZATION_PATTERNS:
        if pattern in action_lower:
            raise F1OptimizationForbidden(
                f"F1 OPTIMIZATION FORBIDDEN: action='{action}' matches "
                f"forbidden pattern '{pattern}'. "
                f"Per STOP_BUILDING.md items 8 and 9: forbidden permanently."
            )
    threshold_patterns = ["lower_threshold", "reduce_threshold", "relax_threshold",
                          "widen_matcher", "expand_synonym", "add_synonym_for_score"]
    for pattern in threshold_patterns:
        if pattern in action_lower:
            raise F1OptimizationForbidden(
                f"F1 OPTIMIZATION FORBIDDEN: threshold-lowering pattern '{pattern}'. "
                f"Per the No-Gaming Rule: do NOT lower a threshold to silence a red."
            )


def assert_f1_baseline_unchanged(current_f1: float) -> None:
    """Post-computation check: verify F1 matches frozen baseline."""
    if abs(current_f1 - FROZEN_F1_BASELINE) > 1e-6:
        raise F1OptimizationForbidden(
            f"F1 BASELINE MODIFIED: frozen={FROZEN_F1_BASELINE}, "
            f"current={current_f1}. Per MC-6: no metric may be silently altered."
        )


def assert_zero_eligible_metrics_for_optimization() -> None:
    """Verify zero eligible metrics — optimization is epistemically impossible."""
    from engine.epistemic_state_enforcer import list_eligible_metrics
    eligible = list_eligible_metrics()
    if len(eligible) > 0:
        raise F1OptimizationForbidden(
            f"F1 OPTIMIZATION PRECONDITION VIOLATION: {len(eligible)} "
            f"metrics are eligible: {eligible}. Currently must be 0."
        )


# ===== STRUCTURAL ENFORCEMENT (Phase 7 Round 3 — immutable manifest) =====

def assert_frozen_data_unchanged() -> dict:
    """Assert that frozen data structures match the immutable manifest.

    Per audit round 17:
        "The freeze needs a committed, immutable-at-runtime reference artifact
         created at the actual freeze point."

    This function:
        1. Loads the committed manifest (reports/phase7/frozen_f1_manifest.json)
        2. Hashes the CURRENT production data
        3. Compares current hashes against manifest hashes
        4. Raises on ANY mismatch

    It NEVER self-baselines. If the manifest is missing, it fails closed.
    If hash computation fails, it fails closed (P6).

    Returns:
        dict with current and manifest hashes for comparison

    Raises:
        FreezeManifestMissing: manifest file does not exist
        FreezeManifestCorrupt: manifest is malformed
        HashComputationFailed: hash computation error (fail closed)
        F1OptimizationForbidden: any hash mismatch
    """
    manifest = _load_manifest()

    current_gold = _compute_gold_hash()
    current_synonym = _compute_synonym_hash()
    current_score = _compute_score_hash()
    current_benchmark = _compute_benchmark_source_hash()

    manifest_gold = manifest["gold_discoveries_sha256"]
    manifest_synonym = manifest["bridge_synonyms_sha256"]
    manifest_score = manifest["score_artifact_sha256"]
    manifest_benchmark = manifest["benchmark_source_sha256"]

    result = {
        "gold_hash_current": current_gold,
        "gold_hash_manifest": manifest_gold,
        "synonym_hash_current": current_synonym,
        "synonym_hash_manifest": manifest_synonym,
        "score_hash_current": current_score,
        "score_hash_manifest": manifest_score,
        "benchmark_hash_current": current_benchmark,
        "benchmark_hash_manifest": manifest_benchmark,
    }

    if current_gold != manifest_gold:
        raise F1OptimizationForbidden(
            f"GOLD SET MODIFIED: manifest={manifest_gold[:16]}... "
            f"current={current_gold[:16]}... "
            f"GOLD_DISCOVERIES does not match the immutable freeze manifest. "
            f"Per STOP_BUILDING.md: gold_set_modification_for_score is forbidden."
        )

    if current_synonym != manifest_synonym:
        raise F1OptimizationForbidden(
            f"SYNONYM MAP MODIFIED: manifest={manifest_synonym[:16]}... "
            f"current={current_synonym[:16]}... "
            f"BRIDGE_SYNONYMS does not match the immutable freeze manifest."
        )

    if current_score != manifest_score:
        raise F1OptimizationForbidden(
            f"COMMITTED SCORE MODIFIED: manifest={manifest_score[:16]}... "
            f"current={current_score[:16]}... "
            f"discovery_capability_score.json does not match the freeze manifest."
        )

    if current_benchmark != manifest_benchmark:
        raise F1OptimizationForbidden(
            f"BENCHMARK SOURCE MODIFIED: manifest={manifest_benchmark[:16]}... "
            f"current={current_benchmark[:16]}... "
            f"discovery_capability_benchmark.py source code has been modified "
            f"since the freeze. Changes to the benchmark source (including "
            f"matcher logic, F1 formula, thresholds) are forbidden. "
            f"Per STOP_BUILDING.md items 8 and 9."
        )

    result["all_unchanged"] = True
    return result


def assert_committed_f1_matches_baseline() -> None:
    """Assert committed discovery_capability_score.json contains f1=0.5714."""
    try:
        score_path = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
        if not score_path.exists():
            raise F1OptimizationForbidden(
                f"COMMITTED SCORE FILE MISSING: {score_path}"
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
                f"committed={committed_f1}."
            )
    except F1OptimizationForbidden:
        raise
    except Exception as e:
        raise HashComputationFailed(
            f"COMMITTED SCORE CHECK FAILED: {type(e).__name__}: {e}. "
            f"Per P6: fail closed."
        )


__all__ = [
    "F1OptimizationForbidden",
    "FreezeManifestMissing",
    "FreezeManifestCorrupt",
    "HashComputationFailed",
    "FROZEN_F1_BASELINE",
    "FORBIDDEN_OPTIMIZATION_PATTERNS",
    "get_frozen_f1_baseline",
    "assert_f1_not_optimized",
    "assert_f1_baseline_unchanged",
    "assert_zero_eligible_metrics_for_optimization",
    "assert_frozen_data_unchanged",
    "assert_committed_f1_matches_baseline",
]


if __name__ == "__main__":
    print("Phase 7: F1 Optimization Freeze (Round 3 — immutable manifest)")
    print("=" * 60)
    baseline = get_frozen_f1_baseline()
    print(f"Frozen F1 baseline: {baseline['f1']}")
    print()

    try:
        result = assert_frozen_data_unchanged()
        print("Frozen data unchanged: CONFIRMED (verified against immutable manifest)")
        print(f"  Gold hash:      {result['gold_hash_current'][:16]}...")
        print(f"  Synonym hash:   {result['synonym_hash_current'][:16]}...")
        print(f"  Score hash:     {result['score_hash_current'][:16]}...")
        print(f"  Benchmark hash: {result['benchmark_hash_current'][:16]}...")
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
    print("  1. Baseline frozen (0.5714) — verified against immutable manifest")
    print("  2. Gold set frozen — SHA-256 verified against manifest")
    print("  3. Synonym map frozen — SHA-256 verified against manifest")
    print("  4. Committed score frozen — SHA-256 verified against manifest")
    print("  5. Benchmark source frozen — SHA-256 verified against manifest")
    print("  6. Zero eligible metrics — nothing to optimize against")
    print("  7. NO self-baselining — manifest is committed, immutable reference")
    print("  8. Fail-closed on missing manifest, corrupt manifest, or hash errors")
