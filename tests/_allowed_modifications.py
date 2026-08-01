"""
Shared allowlist for the "modify ONE component" architecture-freeze guard.

Per the external auditor's finding: five separate hardcoded copies of
the same allowlist in test_gap1_fix.py through test_gap5_fix.py is a
maintenance trap by construction. Every cycle that touches a file
outside invention_compiler/ requires updating all five copies
independently — and if any one is missed, the test suite goes red
silently (as happened in commit 3643873, recorded as F-019).

This module is the single source of truth. All five gap-fix tests
import from here instead of maintaining their own copies.

Usage in tests:
    from tests._allowed_modifications import ALLOWED_MODIFICATIONS
    violations = set(code_changes) - ALLOWED_MODIFICATIONS
"""

# The accumulated set of source files modified across all Maestro Loop
# cycles + Phase 2 constraint propagation. Each entry corresponds to
# a specific gap fix or migration:
#
# Gap 1 (identical scoring):         simulation_module.py
# Gap 2+7 (arbitrary deps + causal): dependency_module.py
# Gap 3 (non-buildable blueprints):   blueprint_module.py
# Gap 4 (missing counterevidence):   orchestrator.py
# Gap 5 (templated plans):           prototype_module.py
# Phase 2 (constraint propagation):  synthesizer.py (compat fix)
#
# NOTE: scripts/propagate_constraints_to_graph.py is a one-off
# migration script, NOT a module — it's excluded from this allowlist
# because the "only X was modified" tests already filter out
# scripts/ via their path-prefix checks.

ALLOWED_MODIFICATIONS = frozenset({
    "invention_compiler/simulation_module.py",
    "invention_compiler/dependency_module.py",
    "invention_compiler/blueprint_module.py",
    "invention_compiler/orchestrator.py",
    "invention_compiler/prototype_module.py",
    "product/discovery/synthesizer.py",  # Phase 2 compat fix
})
