# B-2 GLiREL Parallel Evaluation — Final Report

**Date:** 2026-08-10
**Status:** NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT
**Frozen B-2 instrument (commit f905b68):** UNTOUCHED
**Held-out set:** NOT ACCESSED
**Artifact SHA-256:** `0b9bdb33ab84d7c8a33fb6285d1adea8286ff9e90450458afb2340ea287e97c8`

## Execution Environment

| Dimension | Value |
|-----------|-------|
| Platform | Linux-6.12.90+-x86_64 (Kaggle) |
| Python | 3.12.13 |
| PyTorch | 2.10.0+cu128 |
| CUDA | Available (Tesla P100-PCIE-16GB, 17.06 GB VRAM) |
| GLiREL | 1.2.1 |
| Transformers | 5.0.0 |
| huggingface_hub | 1.11.0 |
| Model | jackboyla/glirel_beta |
| Parameter count | 466,576,896 |
| Backbone | microsoft/deberta-v3-large |
| Load time | 74.9s |
| Execution device | CPU (CUDA kernel image not available for P100; fell back to CPU) |

## Stage Results

All 12 stages PASSED:
1. Setup ✓
2. Repository clone ✓
3. Dependencies installed ✓ (seqeval installed with SETUPTOOLS_SCM_PRETEND_VERSION workaround)
4. Model loaded ✓ (466M params, deberta-v3-large backbone)
5. Smoke test ✓ (30 relations extracted; span invariant = INVALID — see below)
6. Public 13-case benchmark ✓
7. Threshold sweep ✓ (8 thresholds)
8. Top-K sweep ✓ (4 values)
9. Known failure cases ✓ (5 cases)
10. Environment recorded ✓
11. Artifacts packed ✓ (SHA-256: 0b9bdb33...)
12. Final report ✓

## Key Findings

### 1. GLiREL Beta Loads Successfully ✓

Model loaded with 466,576,896 parameters via the local_loader bypass. The local_loader successfully:
- Downloaded model snapshot via huggingface_hub (current API)
- Loaded config with missing-field defaults
- Resized word embeddings to match checkpoint
- Loaded state_dict (strict=False)
- Fell back to CPU when CUDA kernels unavailable on P100

### 2. Exact Span Fidelity: FAIL ✗

**CRITICAL FINDING:** The span invariant `source[start:end] == span_text` FAILS.

GLiREL's `predict_relations` returns `head_pos` and `tail_pos` as token positions, and `head_text`/`tail_text` as the text at those positions. However, the returned text does not match what our deterministic token→character mapper produces:

- GLiREL returns `head_text = "O"` for `head_pos = [0, 1]` (expected: "Osteoblasts")
- GLiREL returns `tail_text = "te"` for `tail_pos = [2, 4]` (expected: "calcium phosphate")

This indicates GLiREL's internal tokenization differs from the regex `re.finditer(r'\w+(?:[-_]\w+)*|\S', text)` used by `batch_predict_relations`. The `+1` adjustment in GLiREL's output code (`head_pos[1]+1`) is a spaCy compatibility artifact that does not align with the regex tokenizer.

**Implication:** GLiREL's token positions cannot be deterministically mapped to character offsets without reverse-engineering GLiREL's internal tokenization. This is a significant finding for the hybrid architecture question.

### 3. Relation Extraction: High Volume, Unknown Quality

- 100 relations per source per case (threshold=0.0, top_k=5)
- 1300 total Source A relations, 1950 total Source B relations across 13 cases
- Relations include CAUSES, ENABLES, PRODUCES, LOCATED_IN, ACTS_ON, etc.

The high volume at threshold=0.0 is expected (all possible entity pairs × all relation labels). The threshold sweep shows:
- threshold=0.0: 750 relations (3 cases)
- threshold=0.1: 417 relations
- threshold=0.3: 33 relations
- threshold=0.4+: 0 relations

### 4. Known Failure Cases: Relations Extracted

All 5 known B-2 failure cases (ADV-05, 06, 07, 08, 13) produced relations from both sources (200 from A, 300 from B at top_k=10). Whether these relations would help the GLM adjudicator make better decisions requires the hybrid experiment.

### 5. Performance

- Model load: 74.9s (CPU; includes backbone download)
- Per-case inference: ~1.5s (13 cases in ~20s total)
- CPU inference (P100 CUDA unavailable)

## Decision Matrix

| Question | Result |
|----------|--------|
| GLiREL-beta loads? | PASS |
| GLiREL-large loads? | NOT TESTED (beta completed first) |
| Exact span mapping? | **FAIL** — GLiREL token positions don't map to char offsets |
| Relation extraction useful? | MIXED — high volume, quality unknown without span validation |
| Mode A improved? | INCONCLUSIVE — spans invalid |
| Mode B improved? | INCONCLUSIVE — spans invalid |
| Mode C improved? | INCONCLUSIVE — spans invalid |
| False cross-source relations reduced? | INCONCLUSIVE |
| GLM semantic burden reduced? | INCONCLUSIVE — requires hybrid experiment |
| Latency improved? | NO — CPU fallback (1.5s/case vs GLM ~3s/case) |
| Reproducibility acceptable? | YES — deterministic given same model/config |
| License cleared? | **NO** — UNRESOLVED (CC BY-NC-SA 4.0 vs Apache-2.0) |
| Hybrid justified? | **NOT YET** — span fidelity must be solved first |

## Recommendation

**DO NOT ADOPT** — span fidelity is a hard gate that currently fails. GLiREL's internal tokenization does not align with its `predict_relations` output positions, making it impossible to map extracted relations to verbatim source spans without additional reverse-engineering.

Before considering adoption:
1. Solve the span fidelity problem (reverse-engineer GLiREL's internal tokenizer)
2. Re-evaluate with correct span mapping
3. Run the hybrid experiment (GLiREL → GLM adjudicator)
4. Resolve the license discrepancy

## What Was NOT Touched

- b2_detector.mjs, SYSTEM_PROMPT.md, b2_trace_validator.mjs: UNCHANGED
- Frozen LLM instrument: UNCHANGED
- B-2 ontology, inference-rule taxonomy, thresholds: UNCHANGED
- Production substrate: UNCHANGED
- Held-out material: NOT ACCESSED
- Package versions: NOT CHANGED (no downgrades)
- GLiREL site-packages: NOT MODIFIED
