# B-2 GLiREL Parallel Evaluation Experiment

**Status:** MOVED TO KAGGLE (local OOM blocker)
**Date:** 2026-08-10
**CTO Directive:** Evaluate GLiREL as an evidence-extraction substrate for B-2, without modifying the frozen scientific instrument.

## Objective

Determine whether GLiREL (zero-shot relation extraction) can materially improve the evidence-extraction layer of the B-2 detector without modifying, contaminating, or replacing the frozen B-2 scientific instrument.

## Current status: Moved to Kaggle

The local environment (3.9GB RAM) could not load `glirel-large-v0` (OOM). Per CTO directive, the experiment has been moved to Kaggle GPU. The Kaggle notebook tests `glirel_beta` first (per the author's documentation), then `glirel-large-v0` if GPU permits.

### Kaggle notebook

`kaggle/b2_glirel_kaggle.ipynb` — reproducible notebook that:
1. Clones the repository
2. Installs pinned GLiREL dependencies
3. Verifies GPU
4. Loads `glirel_beta` (first), then `glirel-large-v0`
5. Runs span mapping tests (critical invariant: `source[start:end] == span_text`)
6. Runs public 13-case benchmark
7. Runs threshold/top-k sweeps
8. Tests 5 known failure cases (ADV-05, 06, 07, 08, 13)
9. Exports artifacts with SHA-256

## Immutable boundary (NOT modified by this experiment)

- B-2 specification: `1c9d869`
- Frozen implementation: `f905b68`
- Production substrate: unchanged
- Held-out status: unresolved / infrastructure-blocked (blind fixture missing)
- `b2_detector.mjs`, `SYSTEM_PROMPT.md`, `b2_trace_validator.mjs`: FROZEN

## Files

### Local (infrastructure + scripts)
- `README.md` — this file
- `ENVIRONMENT.md` — local environment metadata (where OOM occurred)
- `MODEL_FREEZE.md` — model freeze status (OOM documented)
- `LICENSE_REVIEW.md` — license discrepancy (CC BY-NC-SA 4.0 vs Apache-2.0)
- `WORKLOG.md` — experiment worklog
- `relation_taxonomy.json` — frozen relation vocabulary (16 extraction + 9 B-2 inference rules)
- `extraction_schema.json` — evidence graph schema with span invariant
- `glirel_extractor/extractor.py` — GLiREL wrapper with span verification
- `glirel_extractor/span_mapper.py` — deterministic token→char mapping (NO LLM)
- `glirel_extractor/graph.py` — evidence graph construction
- `hybrid_experimental.py` — EXPERIMENTAL hybrid GLiREL→GLM pipeline
- `adversarial/fixtures.json` — 8 independent adversarial test cases
- `venv/` — isolated Python environment (not committed; OOM-blocked locally)

### Kaggle (execution environment)
- `kaggle/b2_glirel_kaggle.ipynb` — reproducible Kaggle GPU notebook
- `kaggle/generate_kaggle_notebook.py` — script that generates the notebook

## License status

**UNRESOLVED** — see LICENSE_REVIEW.md

| Source | License |
|--------|---------|
| PyPI (`pip show glirel`) | Apache-2.0 |
| GitHub (jackboyla/GLiREL) | CC BY-NC-SA 4.0 |

**Hard gate:** GLiREL must NOT be shipped to production or claimed as commercially suitable until this discrepancy is independently resolved.

## What was NOT touched

- ❌ `b2_detector.mjs` — unchanged
- ❌ `SYSTEM_PROMPT.md` — unchanged
- ❌ `b2_trace_validator.mjs` — unchanged
- ❌ Frozen LLM instrument — unchanged
- ❌ B-2 ontology — unchanged
- ❌ Inference-rule taxonomy — unchanged
- ❌ Thresholds — unchanged
- ❌ Production substrate — unchanged
- ❌ Held-out material — not accessed, not searched, not reconstructed

## Next steps

1. Upload `b2_glirel_kaggle.ipynb` to Kaggle
2. Enable GPU
3. Run the notebook
4. Download artifacts (zip with SHA-256)
5. Analyze results
6. Produce final decision report
