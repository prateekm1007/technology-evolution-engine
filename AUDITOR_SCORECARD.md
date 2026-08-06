# AUDITOR_SCORECARD.md — MEASURED (auto-generated)

> Per F-086 (cycle 184): this file is GENERATED from committed benchmark
> reports by `scripts/generate_auditor_scorecard.py`. No manual entries.
> Every score points to a benchmark report file + a passing test.
> If a category has no measured benchmark, it gets score = 0.

**Generated:** 2026-08-06 18:58 UTC
**Composite (7 generation benchmarks):** 9.43 / 10
**Formula:** Single rubric — `total_score = round(10 × F1)` (or equivalent)
**CEO target:** 9.0 / 10

## Measured Scorecard

| Category | Score | Metric | Value | Report | Test | Notes |
|---|---|---|---|---|---|---|
| Gen 1: Document Parsing | **10/10** | F1 | 1.0000 | `benchmarks/reports/gen1_pr_score.json` | `tests/test_regression_suite.py` | Section segmentation |
| Gen 2: Entity Extraction | **9/10** | F1 | 0.9431 | `benchmarks/reports/gen2_pr_score.json` | `tests/test_regression_suite.py` | NER + alias resolution |
| Gen 3: Relation Extraction | **9/10** | F1 | 0.8632 | `benchmarks/reports/gen3_pr_score.json` | `tests/test_regression_suite.py` | BOTTLENECK — auditor's #1 target for F1≥0.90 |
| Gen 4: Mechanism Extraction | **9/10** | F1 | 0.9091 | `benchmarks/reports/gen4_pr_score.json` | `tests/test_regression_suite.py` | Mechanism chain benchmark |
| Gen 5: Discovery Layer (connection-finding) | **9/10** | F1 | 0.9375 | `benchmarks/reports/gen5_pr_score.json` | `tests/test_regression_suite.py` | F-087: F1 counts RETRIEVAL+NOVEL as TP. novelty_rate tracked separately. |
| Gen 6: Re-audit | **10/10** | overturn_rate | 0.2571 | `data/ledger/predictions.jsonl` | `tests/test_failure_regression_suite.py` | Re-audit adversarial verification |
| Calibration | **10/10** | ECE | 0.0038 | `benchmarks/reports/calibration_score.json` | `tests/test_failure_regression_suite.py` | Platt scaling LOOCV |
| Discovery Capability (operator-blind) | **3/10** | F1 | 0.3333 | `benchmarks/reports/discovery_capability_score.json` | `tests/test_failure_regression_suite.py` | Operator-blind gold-standard discovery |

## How to regenerate

```bash
python3 -m benchmarks.section_segmentation_benchmark  # Gen 1
python3 -m benchmarks.entity_extraction_benchmark    # Gen 2
python3 -m benchmarks.relation_extraction_benchmark  # Gen 3
python3 -m benchmarks.mechanism_chain_benchmark      # Gen 4
python3 -m benchmarks.discovery_benchmark            # Gen 5
python3 -m scripts.generate_auditor_scorecard        # this file
```

## Per Law 7 (historical permanence)

This file is reproducible: same benchmark reports → same scorecard.
Manual edits to scores are FORBIDDEN. To change a score, change
the underlying benchmark or extraction code, then re-run.

## Auditor's 12-category scorecard (separate from generation benchmarks)

The external auditor's 12 categories (Representation, Mechanism,
Constraint, Law, Swanson, Causal, Structural, Contradiction,
Experiment, Learning, Scalability, Scientific rigor) are NOT
self-graded. They are evaluated by the external auditor and
recorded in FAILURES.md. The last external audit (update #3,
cycle 183) gave an honest composite of ~4.5/10.

The generation-benchmark composite above is the INTERNALLY
measured score. The two scores measure different things and
should not be conflated.
