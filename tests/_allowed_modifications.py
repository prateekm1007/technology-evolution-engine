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
# Phase 3 Step 4 (real ingestion):  scripts/ingest_real_sources.py,
#                                    scripts/generate_ingestion_data.py
#
# NOTE: scripts/propagate_constraints_to_graph.py is a one-off
# migration script, NOT a module — it's excluded from this allowlist
# because the "only X was modified" tests already filter out
# scripts/ via their path-prefix checks.
#
# AUDITOR FINDING (Cycle 6, post-53320bc): the Phase 3 Step 4 commit
# added scripts/ingest_real_sources.py and scripts/generate_ingestion_data.py
# without updating this allowlist. The gap1 allowlist test was red at
# commit 53320bc — the auditor's "275 collected" report was the
# collection count, not the passing count, and the full suite was
# not run. This is the F-019 pattern (allowlist not updated when new
# files are added) recurring. The fix is to add the two scripts here
# and to re-verify by running the full suite, not just the Step 4 tests.

ALLOWED_MODIFICATIONS = frozenset({
    "invention_compiler/simulation_module.py",
    "invention_compiler/dependency_module.py",
    "invention_compiler/blueprint_module.py",
    "invention_compiler/orchestrator.py",
    "invention_compiler/prototype_module.py",
    "product/discovery/synthesizer.py",  # Phase 2 compat fix
    "web/backend/adapters/oracle_deep.py",  # C2 fix + E3 fix
    "product/scoring/feasibility.py",  # C2 fix: dict constraint handling
    "product/ingestion/patent_parser.py",  # Phase 3: patent ingestion + F-001 fix
    "product/ingestion/paper_parser.py",  # Phase 3 Step 3: paper ingestion; Phase 5.C keyword expansion
    "product/ingestion/text_normalizer.py",  # Phase 3: ingestion support
    "scripts/ingest_real_sources.py",  # Phase 3 Step 4: real ingestion
    "scripts/generate_ingestion_data.py",  # Phase 3 Step 4: synthetic abstracts
    "scripts/measure_convergence.py",  # Phase 4: convergence measurement (one-off)
    "scripts/capture_snapshot.py",  # Phase 5: snapshot capture (one-off)
    "scripts/extract_patent_text.py",  # Phase 5.A: patent text extraction (one-off)
    "scripts/ingest_real_patents_phase5.py",  # Phase 5.A: USPTO ingestion (one-off)
    "scripts/extract_arxiv_text.py",  # Phase 5.B: arXiv extraction (one-off)
    "scripts/ingest_real_arxiv_phase5b.py",  # Phase 5.B: arXiv ingestion (one-off)
    "scripts/ingest_real_arxiv_phase5c.py",  # Phase 5.C: re-ingestion with expanded parser (one-off)
    "scripts/measure_normalization_gap.py",  # Phase 5.D: normalization gap measurement (one-off)
    "scripts/classify_labels.py",  # Phase 5.E: classification exercise (one-off)
    "scripts/build_capability_graph.py",  # Phase 7B/7C: capability graph builder (one-off)
    "scripts/build_trusted_graph.py",  # Phase 7C.1: trusted graph v2.0 (one-off)
    "scripts/build_trusted_graph_v21.py",  # Phase 7C.2: trusted graph v2.1 (one-off)
    "scripts/run_backtest.py",  # Phase 9: frozen-time backtest (one-off)
    "scripts/run_scored_backtest.py",  # Phase 9: scored backtest (one-off)
    "scripts/run_calibrated_backtest.py",  # Phase 9: calibrated backtest (one-off)
})
