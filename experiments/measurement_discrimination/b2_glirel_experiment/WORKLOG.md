# B-2 GLiREL Experiment Worklog

## 2026-08-10

### CTO directive received
- Parallel engineering experiment: can GLiREL improve B-2 evidence extraction?
- Immutable boundary: frozen B-2 instrument (f905b68), spec (1c9d869), held-out seal — all untouched.
- GLiREL tested as extraction substrate, NOT as adjudicator.
- Three configurations: A (GLM only), B (GLiREL → B-2), C (GLiREL + GLM hybrid).
- License discrepancy (CC BY-NC-SA 4.0 vs Apache-2.0) — HARD GATE.

### Environment setup
- Created isolated venv at `b2_glirel_experiment/venv/`
- Installed: glirel==1.2.1, torch==2.13.0+cpu, transformers==4.57.6, huggingface_hub==0.36.2
- Note: had to downgrade huggingface_hub (<1.0) and transformers (<5.0) for GLiREL compatibility — the newer versions broke GLiREL's `_from_pretrained` signature.
- Additional deps: protobuf, sentencepiece, loguru

### License review
- PyPI metadata: Apache-2.0
- GitHub README: CC BY-NC-SA 4.0 (per CTO directive)
- DISCREPANCY FLAGGED — see LICENSE_REVIEW.md
- Hard gate: no production use until resolved.

### Model load attempts
- Model: `jackboyla/glirel-large-v0` (backbone: `microsoft/deberta-v3-large`, ~435M params)
- Attempt 1: timeout (model downloading)
- Attempt 2: cleared pip cache (3GB freed), model files downloaded successfully
- Attempt 3: foreground load — process hung (suspected OOM)
- Attempt 4: background load with memory monitoring — process KILLED by OOM killer
- Root cause: 3.9GB total RAM insufficient for deberta-v3-large + GLiREL layers + PyTorch overhead
- Attempted fallback: `jackboyla/glirel-base-v0` — not available on HuggingFace Hub (404)

### Status: BLOCKED
- Model cannot be loaded in current environment.
- All extraction tests blocked.
- No scientific results produced.
- No frozen instrument modified.
- No held-out material accessed.

### What was NOT done
- No relation extraction.
- No span fidelity test.
- No A/B/C comparison.
- No adversarial tests.
- No performance measurement.
- No code changes to frozen B-2 instrument.

### Recommendation
- Provision environment with ≥8GB RAM or GPU.
- Re-run with cached model files.
- Execute full experiment plan.
- This is an infrastructure blocker, not a scientific result.
