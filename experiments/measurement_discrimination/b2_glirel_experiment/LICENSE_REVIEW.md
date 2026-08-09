# LICENSE_REVIEW.md — GLiREL License Discrepancy

**Status:** UNRESOLVED — HARD GATE
**Date:** 2026-08-10

## The discrepancy

Two sources report conflicting licenses for GLiREL:

| Source | License |
|--------|---------|
| PyPI package metadata (`pip show glirel`) | Apache-2.0 |
| GitHub repository (jackboyla/GLiREL) README | CC BY-NC-SA 4.0 |

The PyPI metadata for `glirel==1.2.1` (installed in this experiment's venv) reports:
```
License: Apache-2.0
```

However, the CTO directive states: "The current GLiREL GitHub repository states CC BY-NC-SA 4.0 for GLiREL."

These two sources conflict. The discrepancy must be resolved before any production use.

## Hard gate (per CTO directive §15)

1. **Do NOT ship GLiREL into production.**
2. **Do NOT claim commercial-production suitability** until licensing is independently resolved.
3. The exact repository commit and model identifier must be recorded (see MODEL_FREEZE.md).
4. Package metadata must be recorded (see ENVIRONMENT.md).
5. The license discrepancy must be flagged (this document).

## Implications for this experiment

- This experiment is a **parallel engineering evaluation** only. It does NOT deploy GLiREL into any production path.
- The frozen B-2 detector (commit `f905b68`) is UNCHANGED and does NOT use GLiREL.
- No production substrate is modified.
- The experiment's findings are **research-only** and may inform a future architectural revision, but cannot authorize one.

## What needs to happen to resolve the license

An independent party must:
1. Contact the GLiREL maintainers (Jack Boylan, Urchade Zaratiana) to clarify which license applies.
2. Obtain written confirmation of the license.
3. If the license is CC BY-NC-SA 4.0: GLiREL cannot be used in commercial production without separate licensing agreements.
4. If the license is Apache-2.0: standard Apache-2.0 terms apply (with patent grant, etc.).
5. Until resolved: **LICENSE: UNRESOLVED**.

## Model license (separate from code license)

The GLiREL model (`jackboyla/glirel-large-v0`) on HuggingFace may have a separate license from the code. The HuggingFace model card must be checked for the model's license terms. This is a common pattern where code is Apache-2.0 but model weights are CC-BY-NC or similar.

This review does NOT constitute legal advice. Independent legal review is required before any production deployment.
