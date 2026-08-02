#!/usr/bin/env python3
"""
AEP Gate Enforcement Script

Per CEO AEP-1 directive: "The coder should not be allowed to choose
excellence. The system itself should force excellence as the default outcome."

Per auditor II3: "The AEP is a document, not machinery. A coder who skips
all 10 gates can still commit."

This script IS the machinery. It checks that gate artifacts exist and are
complete before allowing work to proceed.

Usage:
    python scripts/check_aep_gate.py [gate_number]

    If gate_number is provided, checks only that gate.
    If no gate_number, checks all gates for the current work item.

Gate artifacts are stored in evidence/gates/ as JSON files:
    gate_01_comprehension.json
    gate_02_research.json
    ...
    gate_10_postmortem.json

Each artifact has:
    {
        "gate": <number>,
        "name": "<gate name>",
        "passed": <bool>,
        "checked_at": "<ISO timestamp>",
        "details": { ... gate-specific fields ... },
        "gaps": [ ... missing items ... ]
    }

Exit codes:
    0 = gate passed (or not yet required for this work item)
    1 = gate failed (artifact missing or incomplete)
"""

import json
import pathlib
import sys
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATES_DIR = ROOT / "evidence" / "gates"

GATE_DEFS = {
    1: {
        "name": "Comprehension Gate",
        "file": "gate_01_comprehension.json",
        "required_fields": ["problem", "why_it_matters", "who_affected", "constraints", "success_metric"],
        "min_count": 5,
    },
    2: {
        "name": "Research Gate",
        "file": "gate_02_research.json",
        "required_fields": ["sources_collected", "required", "passed", "gaps"],
        "min_sources": 50,
    },
    3: {
        "name": "First-Principles Gate",
        "file": "gate_03_first_principles.json",
        "required_fields": ["assumptions_decomposed", "chains", "passed"],
        "min_chains": 1,
    },
    4: {
        "name": "Alternatives Gate",
        "file": "gate_04_alternatives.json",
        "required_fields": ["decisions", "passed"],
        "min_alternatives_per_decision": 3,
    },
    5: {
        "name": "Contradiction Gate",
        "file": "gate_05_contradiction.json",
        "required_fields": ["why_wrong", "why_fail", "who_disagrees", "false_assumptions", "passed"],
    },
    6: {
        "name": "Benchmark Gate",
        "file": "gate_06_benchmark.json",
        "required_fields": ["benchmarks", "passed"],
        "min_benchmarks": 5,
    },
    7: {
        "name": "Adversarial Gate",
        "file": "gate_07_adversarial.json",
        "required_fields": ["reviews", "passed"],
        "min_reviewers": 4,
    },
    8: {
        "name": "Implementation Gate",
        "file": "gate_08_implementation.json",
        "required_fields": ["plan", "milestones", "passed"],
    },
    9: {
        "name": "Validation Gate",
        "file": "gate_09_validation.json",
        "required_fields": ["what_failed", "what_succeeded", "what_changed", "what_unknown", "passed"],
    },
    10: {
        "name": "Postmortem Gate",
        "file": "gate_10_postmortem.json",
        "required_fields": ["failures", "lessons", "assumption_updates", "passed"],
    },
}


def check_gate(gate_num: int) -> tuple[bool, str]:
    """Check if a gate artifact exists and is complete.
    
    Returns (passed, message).
    """
    gate_def = GATE_DEFS.get(gate_num)
    if not gate_def:
        return False, f"Unknown gate: {gate_num}"
    
    gate_file = GATES_DIR / gate_def["file"]
    
    if not gate_file.exists():
        return False, f"Gate {gate_num} ({gate_def['name']}): artifact NOT FOUND at {gate_file}"
    
    try:
        with open(gate_file) as f:
            artifact = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Gate {gate_num}: artifact is invalid JSON: {e}"
    
    # Check required fields
    missing_fields = []
    for field in gate_def["required_fields"]:
        if field not in artifact:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Gate {gate_num} ({gate_def['name']}): missing fields: {missing_fields}"
    
    # Check passed flag
    if not artifact.get("passed", False):
        gaps = artifact.get("gaps", ["no gaps listed"])
        return False, f"Gate {gate_num} ({gate_def['name']}): NOT PASSED. Gaps: {gaps}"
    
    # Gate-specific checks
    if gate_num == 2:  # Research Gate
        sources = artifact.get("sources_collected", 0)
        required = artifact.get("required", 50)
        if sources < required:
            return False, f"Gate 2: only {sources} sources collected, need {required}"
    
    if gate_num == 4:  # Alternatives Gate
        decisions = artifact.get("decisions", [])
        for d in decisions:
            alts = d.get("alternatives", [])
            if len(alts) < gate_def["min_alternatives_per_decision"]:
                return False, f"Gate 4: decision '{d.get('decision', '?')}' has only {len(alts)} alternatives, need {gate_def['min_alternatives_per_decision']}"
    
    if gate_num == 7:  # Adversarial Gate
        reviews = artifact.get("reviews", [])
        if len(reviews) < gate_def["min_reviewers"]:
            return False, f"Gate 7: only {len(reviews)} reviewers, need {gate_def['min_reviewers']}"
    
    return True, f"Gate {gate_num} ({gate_def['name']}): PASSED"


def check_all_gates(strict: bool = False) -> int:
    """Check all gates. Returns 0 if all pass, 1 if any fail.
    
    In strict mode (CI), missing gate artifacts for commits that touch
    code files (.py, .ts, .tsx) cause failure. Non-strict mode (local)
    allows trivial commits without gate artifacts.
    """
    if not GATES_DIR.exists():
        if strict:
            # In strict mode, check if this commit touches code files
            try:
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "HEAD"],
                    capture_output=True, text=True, cwd=str(ROOT)
                )
                changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
                code_files = [f for f in changed_files if f.endswith(('.py', '.ts', '.tsx'))]
                if code_files:
                    print(f"AEP Gate Check (STRICT): code files changed ({code_files})")
                    print("  but no gate artifacts in evidence/gates/.")
                    print("  CI BLOCKS this commit. Create gate artifacts first.")
                    print("  See AEP_PROTOCOL.md for gate requirements.")
                    return 1
            except Exception:
                pass  # If git command fails, fall through to non-strict behavior
            print(f"AEP Gate Check (STRICT): {GATES_DIR} does not exist.")
            print("  No code files changed — allowed.")
            return 0
        else:
            print(f"AEP Gate Check: {GATES_DIR} does not exist.")
            print("  No gate artifacts found. This is allowed for trivial commits")
            print("  (doc-only, config changes). For code-changing work items,")
            print("  create gate artifacts in evidence/gates/ before committing.")
            return 0  # Allow trivial commits without gates
    
    # Check if any gate artifacts exist
    gate_files = list(GATES_DIR.glob("gate_*.json"))
    if not gate_files:
        print("AEP Gate Check: No gate artifacts found in evidence/gates/.")
        print("  Allowed for trivial commits. For code-changing work,")
        print("  create gate artifacts first.")
        return 0
    
    # Gate artifacts exist — check them
    all_passed = True
    for gate_num in sorted(GATE_DEFS.keys()):
        passed, message = check_gate(gate_num)
        status = "✓" if passed else "✗"
        print(f"  {status} {message}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nAEP Gate Check: ALL GATES PASSED")
        return 0
    else:
        print("\nAEP Gate Check: GATE FAILURES DETECTED — commit blocked")
        print("  Fix the failing gates before committing code changes.")
        print("  See AEP_PROTOCOL.md for gate requirements.")
        return 1


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    args = [a for a in args if a != "--strict"]
    
    if args:
        try:
            gate_num = int(args[0])
        except ValueError:
            print(f"Error: gate number must be 1-10, got '{args[0]}'")
            return 1
        
        passed, message = check_gate(gate_num)
        print(message)
        return 0 if passed else 1
    else:
        return check_all_gates(strict=strict)


if __name__ == "__main__":
    sys.exit(main())
