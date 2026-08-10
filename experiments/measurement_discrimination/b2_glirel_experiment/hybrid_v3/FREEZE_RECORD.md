# V3 Experiment Freeze Record

**Frozen at:** 2026-08-10
**Status:** IMMUTABLE — no further adapter changes

## Adapter

| Dimension | Value |
|-----------|-------|
| Adapter version | span_adapter_v3.py |
| Fix cases | 4 (standard, single_token, swapped_inversion, out_of_range) |
| Mechanical span validity | 100.0% (6500/6500 spans) |
| Gold span accuracy | 100.0% (all spans match known entities) |
| 520 inverted verification | 520/520 = MODEL_OUTPUT_INVERSION (Category A: correct inversion recovery) |

## GLiREL Model

| Dimension | Value |
|-----------|-------|
| Model ID | jackboyla/glirel_beta |
| Parameter count | 466,576,896 |
| Backbone | microsoft/deberta-v3-large |
| GLiREL version | 1.2.1 |
| PyTorch | 2.10.0+cu128 |
| Transformers | 5.0.0 |
| huggingface_hub | 1.11.0 |
| Device | CPU (P100 CUDA kernels unavailable; fell back to CPU) |

## Kaggle Execution

| Dimension | Value |
|-----------|-------|
| Kernel | prateekm1007/b2-hybrid-extraction |
| Kernel version | 5 |
| Execution timestamp | 2026-08-10T02:25:51Z to 2026-08-10T02:27:37Z |
| Artifact SHA-256 | babb317ec4ff7d031c7ff788503278feafb3d2563ac94700873d3dc528a1ce5b |

## Artifacts

| File | Location |
|------|----------|
| Evidence graphs (v3) | hybrid/results/glirel/evidence_graphs_v3.json |
| Span fidelity summary | hybrid/diagnostics/span_fidelity_summary_v3.json |
| 520 inverted verification | hybrid_v3/inverted_verification.json |
| 520 semantic verification | hybrid_v3/swapped_semantic_verification.json |
| Gold benchmark | hybrid/gold_span_benchmark.json (GLiREL-SPAN-GOLD-v1, 30 relations) |
| Environment | hybrid/results/glirel/environment_v3.json |

## Code Commit

| Dimension | Value |
|-----------|-------|
| Repository | prateekm1007/technology-evolution-engine |
| Branch | external-review-preparation |
| Commit | 98ed9c0 (span_adapter_v3 + v3 Kaggle notebook) |
| Later commits | 5657b79 (520 semantic verification), 997c24e (A/B/C failure cases) |

## Extraction Statistics

| Metric | Value |
|--------|-------|
| Total relations | 3250 (100 per source per case × 13 cases × 2.5 avg) |
| Total spans | 6500 |
| Head valid | 3250 (100.0%) |
| Tail valid | 3250 (100.0%) |
| Both valid | 3250 (100.0%) |
| Fix method: standard | 5330 (82.0%) |
| Fix method: single_token | 650 (10.0%) |
| Fix method: swapped_inversion | 520 (8.0%) |
| Fix method: still_invalid | 0 (0.0%) |

## What This Freeze Means

- span_adapter_v3.py is the canonical adapter. No v4.
- The 520 swapped_inversion spans are verified as semantically correct (Category A).
- All 6500 spans are mechanically valid AND semantically match known entities.
- The GLiREL model (glirel_beta) is frozen for this experiment.
- No further adapter changes are authorized.
