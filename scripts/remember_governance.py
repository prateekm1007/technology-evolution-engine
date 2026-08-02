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
    ("CONVERGENCE.md", "Phase 4 convergence definition (CO_OCCURRENCE_MODEL architecture). Read BEFORE any convergence-related work. The CAPABILITY_MODEL (Phase 6) is under investigation; CONVERGENCE.md is the CO_OCCURRENCE_MODEL, preserved for comparison/backtest."),
    ("CAPABILITY_ONTOLOGY.md", "Phase 6 capability-centric architecture (CAPABILITY_MODEL, under investigation). Defines the new node types, edge types, evidence schema, temporal state, scope restriction (one vertical), embedding policy, and three independent scores. Implementation (Phase 7) NOT yet authorized."),
    ("ONTOLOGY_FREEZE.md", "Phase 6 ontology freeze guardrail (REDUCED per CEO 7C.1). Caps: 5 patents, 10 capabilities, 5 constraints, 4 edge types (ENABLES + SUBSTITUTES_FOR SUSPENDED). Any addition requires explicit CEO authorization."),
    ("CAUSALITY_POLICY.md", "Phase 7C.1 causality policy. Defines causality, enablement, substitutability, admissible/inadmissible evidence, confidence scale (1.0/0.8/0.5/0.2), reviewer responsibilities. Constitutional rules: no edge without evidence, no capability without evidence, no prediction without explanation."),
    ("AEP_PROTOCOL.md", "Autonomous Excellence Protocol. 10 mandatory gates that every work item must pass before implementation. Gate enforcement: scripts/check_aep_gate.py. Gate artifacts: evidence/gates/. Per CEO AEP-1: 'The system itself should force excellence as the default outcome.'"),
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
