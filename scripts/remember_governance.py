#!/usr/bin/env python3
"""
Print the mandatory pre-coding read list.

Per the Master Protocol consolidation: the coder reads MASTER_PROTOCOL.md
and FAILURES.md. That is enough. The other governance documents have been
archived (see archive/governance-pre-consolidation/).

Usage:
    python scripts/remember_governance.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

READ_LIST = [
    ("MASTER_PROTOCOL.md",
     "the factory. Defines the 11-section structure for any package, the typed status rules (no numerical confidence), the retraction rule, the validation levels. The protocol decides; the coder executes."),
    ("FAILURES.md",
     "institutional memory of failures. Do not re-introduce. Each failure is a specific past mistake with a lesson."),
    ("CONSTITUTION.md",
     "the 8 research-process laws. Law 7 (historical permanence — no silent edits) and Law 8 (verification standard — positive AND negative evidence before 'verified') are the most often violated."),
    ("ANTI_ENTROPY.md",
     "operational anti-entropy rules: tests first, single responsibility, refactor constantly, lock deps, document assumptions, decouple, clear dead code, maintain patterns."),
    ("CONTRIBUTING.md",
     "pre-commit checklist. Read BEFORE every commit."),
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
