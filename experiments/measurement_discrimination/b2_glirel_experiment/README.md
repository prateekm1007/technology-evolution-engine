# B-2 GLiREL Parallel Evaluation Experiment

**Status:** BLOCKED — Infrastructure limitation (OOM)
**Date:** 2026-08-10
**CTO Directive:** Evaluate GLiREL as an evidence-extraction substrate for B-2, without modifying the frozen scientific instrument.

## Objective

Determine whether GLiREL (zero-shot relation extraction) can materially improve the evidence-extraction layer of the B-2 detector without modifying, contaminating, or replacing the frozen B-2 scientific instrument.

## Immutable boundary (NOT modified by this experiment)

- B-2 specification: `1c9d869`
- Frozen implementation: `f905b68`
- Production substrate: unchanged
- Held-out status: unresolved / infrastructure-blocked (blind fixture missing)
- `b2_detector.mjs`, `SYSTEM_PROMPT.md`, `b2_trace_validator.mjs`: FROZEN
- B-2 ontology, inference-rule taxonomy, thresholds: FROZEN

## Current status: BLOCKED

The experiment cannot proceed due to an infrastructure limitation:

- **GLiREL model (`jackboyla/glirel-large-v0`) cannot be loaded** in the current environment (3.9GB RAM). The model uses `microsoft/deberta-v3-large` (~435M parameters) as its backbone, which exceeds available memory.
- **Smaller model not available:** `jackboyla/glirel-base-v0` is not published on HuggingFace Hub.
- **See MODEL_FREEZE.md** for full details.

## What was completed

1. ✅ Isolated experiment directory created (`b2_glirel_experiment/`)
2. ✅ Isolated Python venv created (`venv/`)
3. ✅ GLiREL 1.2.1 installed with all dependencies
4. ✅ Environment metadata frozen (ENVIRONMENT.md)
5. ✅ License discrepancy documented (LICENSE_REVIEW.md) — CC BY-NC-SA 4.0 (GitHub) vs Apache-2.0 (PyPI); UNRESOLVED
6. ✅ Model files downloaded from HuggingFace Hub
7. ❌ Model load FAILED — OOM (see MODEL_FREEZE.md)

## What was NOT completed

- ❌ Relation extraction on public 13-case calibration set
- ❌ Exact span fidelity test
- ❌ A/B/C comparison (GLM vs GLiREL vs hybrid)
- ❌ Adversarial engineering tests
- ❌ Performance/latency measurement
- ❌ Zero-shot degradation test
- ❌ Final decision report

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

## License status

**UNRESOLVED** — see LICENSE_REVIEW.md

| Source | License |
|--------|---------|
| PyPI (`pip show glirel`) | Apache-2.0 |
| GitHub (jackboyla/GLiREL) | CC BY-NC-SA 4.0 |

**Hard gate:** GLiREL must NOT be shipped to production or claimed as commercially suitable until this discrepancy is independently resolved.

## Decision (preliminary — based on infrastructure blocker only)

```
GLiREL evidence extraction:    INCONCLUSIVE (could not execute)
Exact span fidelity:           INCONCLUSIVE (could not execute)
Relation extraction:           INCONCLUSIVE (could not execute)
Cross-source evidence recall:  INCONCLUSIVE (could not execute)
Mode A:                        INCONCLUSIVE (could not execute)
Mode B:                        INCONCLUSIVE (could not execute)
Mode C:                        INCONCLUSIVE (could not execute)
Latency:                       INCONCLUSIVE (could not execute)
Licensing:                     UNRESOLVED

Recommendation:                DO NOT ADOPT (insufficient evidence;
                               infrastructure blocker prevents evaluation)
```

## Next steps (if infrastructure is upgraded)

1. Provision an environment with ≥8GB RAM (or GPU).
2. Re-run model load (files are already cached).
3. Execute the full experiment plan (§5-§13 of CTO directive).
4. Produce final decision report.

## Files

- `README.md` — this file
- `ENVIRONMENT.md` — frozen environment metadata
- `MODEL_FREEZE.md` — model freeze status (OOM failure documented)
- `LICENSE_REVIEW.md` — license discrepancy review
- `venv/` — isolated Python environment (not committed to git)
