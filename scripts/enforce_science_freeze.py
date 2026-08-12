#!/usr/bin/env python3
"""
CI Enforcement: Science Freeze

Fails if a PR modifies frozen paths unless explicitly tagged as phase-3-experiment.

Usage in CI:
    python3 scripts/enforce_science_freeze.py

Exit code 0 = PASS (no violations)
Exit code 1 = FAIL (frozen path modified without authorization)
"""
import subprocess
import sys
import os
from pathlib import Path

FROZEN_PATHS = [
    "discovery_fabric/discovery_modes/",
    "invention_compiler/",
    "discovery_fabric/evaluation/discovery_value/",
    "discovery_fabric/evaluation/funding/",
    "patent_discovery/",
    "discovery_fabric/dsb_v1/scorer.py",
    "discovery_fabric/dsb_v1/cases/",
    "discovery_fabric/dsb_v1/receipts/",
    "discovery_fabric/dsb_v1/scores/",
]

AUTHORIZED_TAG = "phase-3-experiment"


def get_changed_files():
    """Get list of files changed in this PR (vs main)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fallback: diff vs origin/main
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main"],
            capture_output=True, text=True
        )
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def is_authorized():
    """Check if PR is explicitly tagged as phase-3-experiment."""
    # Check commit message
    result = subprocess.run(
        ["git", "log", "--format=%s", "-1"],
        capture_output=True, text=True
    )
    if AUTHORIZED_TAG in result.stdout:
        return True
    # Check environment variable
    if os.environ.get("PHASE_3_EXPERIMENT", "").lower() in ("true", "1", "yes"):
        return True
    # Check for label file
    if Path(".phase-3-authorized").exists():
        return True
    return False


def main():
    changed = get_changed_files()
    if not changed:
        print("No changed files detected. PASS.")
        sys.exit(0)

    violations = []
    for filepath in changed:
        for frozen in FROZEN_PATHS:
            if filepath.startswith(frozen):
                violations.append(filepath)
                break

    if not violations:
        print(f"✓ No frozen paths modified. PASS.")
        sys.exit(0)

    if is_authorized():
        print(f"⚠ Frozen paths modified but PR is authorized as {AUTHORIZED_TAG}.")
        for v in violations:
            print(f"  - {v}")
        print("PASS (authorized).")
        sys.exit(0)

    print(f"✗ SCIENCE FREEZE VIOLATION: {len(violations)} frozen path(s) modified.")
    print()
    print("The following paths are frozen per SCIENCE_FREEZE.md:")
    for v in violations:
        print(f"  - {v}")
    print()
    print("To authorize a Phase 3 experiment, either:")
    print(f"  1. Include '{AUTHORIZED_TAG}' in the commit message")
    print(f"  2. Set PHASE_3_EXPERIMENT=true environment variable")
    print(f"  3. Create a .phase-3-authorized file")
    print()
    print("Otherwise, no modifications to frozen paths are permitted.")
    sys.exit(1)


if __name__ == "__main__":
    main()
