#!/usr/bin/env python3
"""
Print the mandatory pre-coding read list.

Not a gate — a reminder. The read list is documented in
GOVERNANCE.md and HANDOFF.md; this script exists so it can be
wired into a pre-commit hook or a CI step that prints the reminder
before any code-modifying operation.

Usage:
    python scripts/remember_governance.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

READ_LIST = [
    ("CONSTITUTION.md", "the eight immutable laws. Law 8 is the one most often violated."),
    ("INVENTION_COMPILER.md", "the master spec. The system is an invention compiler, not an idea generator."),
    ("ANTI_ENTROPY.md", "operational rules: tests first, single responsibility, refactor constantly, lock deps, document assumptions, decouple, clear dead code, maintain patterns."),
    ("CONTRIBUTING.md", "session-hardened principles + pre-commit checklist. Read BEFORE every commit."),
    ("FAILURES.md", "the failure taxonomy. Do not re-introduce."),
    ("HANDOFF.md", "current state and what's next."),
    ("CONVERGENCE.md", "Phase 4 convergence definition. Read BEFORE any convergence-related work. Implementation is FORBIDDEN until the prerequisite chain (snapshot_1 -> ingestion -> snapshot_2 -> delta -> temporal signal -> validation -> implementation) executes."),
    ("NORMALIZATION_GAP.md", "Phase 5.D normalization gap measurement. Read BEFORE any future parser or ingestion work. Documents the 4 failed bridges and the saturation point (d(shared)/d(total) = 0.00 for 2 consecutive cycles). Per the CEO's most important instruction: this is a measurement, NOT authorization for semantic matching."),
]


def check_files_exist():
    missing = []
    for name, _desc in READ_LIST:
        if not (ROOT / name).exists():
            missing.append(name)
    return missing


def main():
    print("=" * 60)
    print("PRE-CODING READ LIST (MANDATORY)")
    print("=" * 60)
    print()
    print("Before writing or modifying any code in this repository,")
    print("read these files in order:")
    print()
    for i, (name, desc) in enumerate(READ_LIST, start=1):
        marker = "[OK]" if (ROOT / name).exists() else "[MISSING]"
        print(f"  {i}. {marker} {name}")
        print(f"       {desc}")
    print()
    missing = check_files_exist()
    if missing:
        print(f"WARNING: missing governor files: {missing}")
        print("The anti-entropy layer is incomplete. Restore them before proceeding.")
        return 1
    print("All governor files present. Proceed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
