# Quarantined Modules (V1.12 Experimental)

The following modules have NOT demonstrated validated discovery value:
- Combination discovery engine (V1.7) — no incremental value over mechanism-only
- Constraint release detection (V1.9) — not validated
- Discovery value scoring (V1.8) — LLM-based, not validated
- Specialist attackers (V1.7) — LLM-based, not validated
- DSM scoring (V1.9-V1.12) — retired as inherently subjective
- V3 blinded scorer — not validated against human consensus

These modules are preserved for historical reference but are NOT active
in the V1.13 evaluation pipeline.

Retained and active:
- Mechanism extraction (validated in ablation as at-least-as-good as full system)
- Evidence graph/provenance (hash chain preserved)
- Deterministic novelty checking (100% reproducible)
- Prediction generation (hypothesis → prediction → falsifier)
