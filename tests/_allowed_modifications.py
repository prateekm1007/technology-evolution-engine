"""
Shared allowlist for the "modify ONE component" architecture-freeze guard.

Per the Master Protocol consolidation: the coder reads MASTER_PROTOCOL.md
and FAILURES.md. The allowlist tracks which source files have been
modified across cycles.
"""

ALLOWED_MODIFICATIONS = frozenset({
    # Phase 1-5 modules
    "invention_compiler/simulation_module.py",
    "invention_compiler/dependency_module.py",
    "invention_compiler/blueprint_module.py",
    "invention_compiler/orchestrator.py",
    "invention_compiler/prototype_module.py",
    "product/discovery/synthesizer.py",
    "web/backend/adapters/oracle_deep.py",
    "product/scoring/feasibility.py",
    "product/ingestion/patent_parser.py",
    "product/ingestion/paper_parser.py",
    "product/ingestion/text_normalizer.py",
    "scripts/ingest_real_sources.py",
    "scripts/generate_ingestion_data.py",
    # Phase 9-14 scripts
    "scripts/run_backtest.py",
    "scripts/run_scored_backtest.py",
    "scripts/run_calibrated_backtest.py",
    "scripts/run_rival_formulas_backtest.py",
    "scripts/run_inevitability_backtest.py",
    "scripts/run_expanded_and_generalization.py",
    "scripts/run_ablation.py",
    "scripts/run_semiconductor_backtest.py",
    "scripts/run_telecom_backtest.py",
    "scripts/run_phase13_open_items.py",
    # Phase 3-5 one-off scripts
    "scripts/measure_convergence.py",
    "scripts/capture_snapshot.py",
    "scripts/extract_patent_text.py",
    "scripts/ingest_real_patents_phase5.py",
    "scripts/extract_arxiv_text.py",
    "scripts/ingest_real_arxiv_phase5b.py",
    "scripts/ingest_real_arxiv_phase5c.py",
    "scripts/measure_normalization_gap.py",
    "scripts/classify_labels.py",
    "scripts/build_capability_graph.py",
    "scripts/build_trusted_graph.py",
    "scripts/build_trusted_graph_v21.py",
    # Honesty Loop code
    "scripts/enforce_law27.py",
    "scripts/check_aep_gate.py",
    "web/backend/adapters/retraction_registry.py",
    "web/backend/adapters/test_registry.py",
    "web/backend/main.py",
    "product/reporting/generator.py",
    "product/blueprint/composer.py",
    "product/scoring/epistemic_status.py",
    # PKG-EVBT-001
    "scripts/register_ev_battery_artifacts.py",
    # Master Protocol consolidation
    "scripts/remember_governance.py",
    # PKG-AWG-001 (factory production test)
    "scripts/register_awg_artifacts.py",
    # PKG-AWG-002 (factory revision test)
    "scripts/register_awg_rev1_artifacts.py",
    # Archived tests (moved during Master Protocol consolidation)
    "archive/governance-pre-consolidation/test_aep_enforcement.py",
    "archive/governance-pre-consolidation/test_honesty_loop.py",
    # PDF generation (CEO directive: world-class PDF non-negotiable)
    "scripts/generate_pdf.py",
    "scripts/pdf_template.css",
    # Phase 2: thermal model (simulation gap closure, 5/10 → target 10/10)
    "scripts/thermal_model_1d.py",
    # Phase 1: independent recomputation verifier (Law 13)
    "scripts/verify_arithmetic.py",
    # F-044 / PR-22: independent benchmark recomputation verifier
    # (Law 13 extended from package layer to benchmark layer)
    "scripts/verify_benchmarks.py",
    "scripts/run_compiler_benchmarks.py",
    # F-044 tests
    "tests/test_verify_benchmarks.py",
    # F-045 / PR-21: corpus-derived tolerances replacing prior-map
    "invention_compiler/constraint_module.py",
    "tests/test_f045_corpus_derived_tolerances.py",
    # F-047: paper corpus remediation (same pattern as F-043)
    "tests/test_f047_paper_corpus.py",
    # Self-audit fixes: product enforcement tests + CI updates
    "tests/test_product_enforcement.py",
    "product/PRODUCT.md",  # canonical source for the customer-facing PDF
})
