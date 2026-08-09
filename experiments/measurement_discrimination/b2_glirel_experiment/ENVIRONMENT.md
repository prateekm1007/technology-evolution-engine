# ENVIRONMENT.md — GLiREL Experiment Environment

**Frozen at:** 2026-08-10
**Isolated venv:** `experiments/measurement_discrimination/b2_glirel_experiment/venv/`

## System

| Dimension | Value |
|-----------|-------|
| OS | Linux 5.10.134-013.8.3.kangaroo.al8.x86_64 |
| Platform | Linux-5.10.134-013.8.3.kangaroo.al8.x86_64-x86_64-with-glibc2.41 |
| Hardware | x86_64 |
| Python | 3.12.13 (main, Jul 18 2026, Clang 22.1.3) |

## Installed packages (key)

| Package | Version |
|---------|---------|
| glirel | 1.2.1 |
| torch | 2.13.0+cpu (CPU-only; no CUDA available) |
| transformers | 5.14.1 |
| huggingface_hub | 1.27.0 |
| tokenizers | 0.22.2 |
| datasets | 5.0.1 |
| seqeval | 1.2.2 |
| loguru | 0.7.3 |
| numpy | 2.5.2 |

## Reproducibility notes

- CPU-only execution (no GPU available in this environment).
- The GLiREL model (`jackboyla/glirel-large-v0`) will be downloaded from HuggingFace Hub on first run. The model checksum will be recorded in MODEL_FREEZE.md after first successful load.
- `transformers==5.14.1` is newer than what GLiREL was originally tested against. If instability is observed, this will be flagged.

## Installation commands (for reproduction)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install --no-deps glirel
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers datasets huggingface_hub seqeval tqdm loguru
```
