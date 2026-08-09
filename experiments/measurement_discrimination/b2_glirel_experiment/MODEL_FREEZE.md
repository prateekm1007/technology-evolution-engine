# MODEL_FREEZE.md — GLiREL Model Freeze

**Date:** 2026-08-10
**Status:** MODEL LOAD FAILED — OOM (Out of Memory)

## Intended model

| Dimension | Value |
|-----------|-------|
| Model identifier | `jackboyla/glirel-large-v0` |
| Backnone encoder | `microsoft/deberta-v3-large` (~435M parameters) |
| Source | HuggingFace Hub |
| Model files | Downloaded and cached at `/home/z/.cache/huggingface/hub/models--jackboyla--glirel-large-v0/` |
| Backbone files | Downloaded and cached at `/home/z/.cache/huggingface/hub/models--microsoft--deberta-v3-large/` |

## Load failure — OOM

The model load was attempted 4 times. In all cases, the process was **Killed** by the OOM killer:

```
nohup python -c "from glirel import GLiREL; model = GLiREL.from_pretrained('jackboyla/glirel-large-v0')"
→ Killed (signal 9)
```

**Root cause:** The environment has 3.9GB total RAM (3.4GB free). The `deberta-v3-large` backbone (~435M parameters) requires ~1.7GB just for weights (FP32), and the GLiREL model adds relation-classification layers on top. With PyTorch overhead and the tokenizer, peak memory exceeds available RAM.

**Cache status:** The model files ARE fully downloaded in the HuggingFace cache. The failure is at load/inference time, not download time.

## Smaller model not available

An attempt was made to load `jackboyla/glirel-base-v0` (smaller backbone), but this model is not available on HuggingFace Hub (404 / not found). Only `glirel-large-v0` appears to be published.

## Model checksum

The model checksum could not be computed because the model could not be loaded into memory. The HuggingFace cache contains the downloaded files, but computing a checksum of the loaded model state dict requires successful instantiation.

**Partial checksums (of downloaded files in cache):**

```
/home/z/.cache/huggingface/hub/models--jackboyla--glirel-large-v0/
  model.safetensors — present (size TBD)
  config.json — present
  README.md — present

/home/z/.cache/huggingface/hub/models--microsoft--deberta-v3-large/
  model.safetensors — present (~1.7GB)
  tokenizer files — present
```

## Implications for the experiment

The GLiREL experiment **cannot proceed** in the current environment without one of:

1. **More RAM:** The environment needs ≥8GB RAM to load `glirel-large-v0` comfortably. Current: 3.9GB.
2. **A smaller GLiREL model:** If `jackboyla/glirel-base-v0` or another smaller variant is published, it may fit in 3.9GB. Currently not available.
3. **A different environment:** A machine with sufficient RAM or GPU memory.
4. **Quantized inference:** If GLiREL supports INT8/FP16 inference on CPU, memory usage could be halved. Not yet tested.

## What was verified

- GLiREL package (`glirel==1.2.1`) installs and imports correctly.
- Model files download successfully from HuggingFace Hub.
- The `GLiREL.from_pretrained()` method begins execution (tokenizer loads, config loads) but is killed during model weight loading due to OOM.
- The `predict_relations` method exists on the model class (confirmed via `hasattr` check before OOM kill — though this check could not complete because the model never finished loading).

## Recommendation

This is an **infrastructure blocker**, not a scientific result. The GLiREL experiment cannot be executed in the current 3.9GB RAM environment. A larger environment is required.

The frozen B-2 detector (commit `f905b68`) is UNAFFECTED — it uses GLM (via API), not GLiREL, and operates within available resources.
