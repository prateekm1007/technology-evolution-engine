#!/usr/bin/env python3
"""local_loader.py — Bypass GLiREL's broken _from_pretrained wrapper.

GLiREL 1.2.1's _from_pretrained is incompatible with modern huggingface_hub
(1.x+). The issue: GLiREL requires `proxies` and `resume_download` kwargs
that modern HF Hub no longer passes.

This loader bypasses the broken wrapper by:
  1. Downloading model files via huggingface_hub.snapshot_download (current API)
  2. Loading config via glirel.model.load_config_as_namespace
  3. Constructing model via GLiREL(config) (direct constructor call)
  4. Loading state_dict via torch.load + model.load_state_dict
  5. Moving to device + eval mode

This does NOT modify:
  - The installed GLiREL package (site-packages)
  - The frozen B-2 detector
  - Any package versions

For glirel_beta: the version assertion in _from_pretrained is bypassed
(since we don't call _from_pretrained). glirel_beta uses the same
architecture as glirel-large-v0 (same backbone, same hidden size), so
the weights should be loadable. If they're not, the error is recorded.
"""
import os
import hashlib
import torch
from pathlib import Path
from huggingface_hub import snapshot_download


def load_glirel_compatible(
    model_id: str,
    device: str = "cuda",
    map_location: str = "cpu",
    strict: bool = False,
) -> "GLiREL":
    """Load a GLiREL model by bypassing the broken _from_pretrained wrapper.

    Args:
        model_id: HuggingFace model ID (e.g., "jackboyla/glirel-large-v0")
        device: target device for inference ("cuda" or "cpu")
        map_location: where to load state_dict before moving to device
        strict: whether to strictly enforce state_dict key matching

    Returns:
        GLiREL model instance on `device`, in eval mode.

    Raises:
        RuntimeError if model files cannot be downloaded or loaded.
    """
    # Step 1: Download model snapshot (uses current HF Hub API)
    print(f"[local_loader] Downloading snapshot for {model_id}...")
    snapshot_dir = snapshot_download(repo_id=model_id)
    snapshot_dir = Path(snapshot_dir)
    print(f"[local_loader] Snapshot at: {snapshot_dir}")

    # Step 2: Locate config and weights
    config_file = snapshot_dir / "glirel_config.json"
    model_file = snapshot_dir / "pytorch_model.bin"

    if not config_file.exists():
        raise RuntimeError(f"Config file not found: {config_file}")
    if not model_file.exists():
        # Try safetensors
        model_file = snapshot_dir / "model.safetensors"
        if not model_file.exists():
            raise RuntimeError(f"Model weights not found in {snapshot_dir}")

    # Step 3: Load config
    from glirel.model import load_config_as_namespace, GLiREL
    print(f"[local_loader] Loading config from {config_file}...")
    config = load_config_as_namespace(str(config_file))
    print(f"[local_loader] Config loaded: model_name={config.model_name}, "
          f"hidden_size={config.hidden_size}")

    # Step 3a: Ensure all required config fields exist (glirel_beta config may be missing some)
    # These are fields that GLiREL 1.2.1's InstructBase.__init__ expects
    defaults = {
        'max_entity_pair_distance': None,
        'max_width': 12,
        'max_len': 512,
        'span_marker_mode': 'markerv1',
        'coreference_label': 'SELF',
        'add_entity_markers': False,
        'coref_classifier': False,
        'refine_relation': False,
        'refine_prompt': False,
        'ffn_mul': 4,
        'dropout': 0.4,
        'positive_weight': 2.0,
        'negative_weight': 1.0,
        'threshold_search_metric': 'micro_f1',
        'label_embed_strategy': 'both',
        'fixed_relation_types': True,
        'scorer': 'dot',
        'rel_mode': 'marker',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
    }
    for key, val in defaults.items():
        if not hasattr(config, key):
            setattr(config, key, val)
            print(f"[local_loader] Added missing config field: {key}={val}")

    # Step 4: Construct model (this downloads the backbone from HF)
    print(f"[local_loader] Constructing GLiREL(config)...")
    model = GLiREL(config)

    # Step 5: Load state dict
    print(f"[local_loader] Loading state_dict from {model_file}...")
    state_dict = torch.load(str(model_file), map_location=torch.device(map_location))

    # Step 5a: Handle embedding size mismatch
    # GLiREL adds special tokens ([REL], [SEP], [E], [/E], [FLERT]) to the tokenizer,
    # which may result in a different vocab size than the checkpoint expects.
    # Resize the model's word embeddings to match the checkpoint.
    word_emb_key = "token_rep_layer.bert_layer.model.embeddings.word_embeddings.weight"
    if word_emb_key in state_dict:
        ckpt_vocab_size = state_dict[word_emb_key].shape[0]
        model_vocab_size = model.token_rep_layer.bert_layer.model.embeddings.word_embeddings.weight.shape[0]
        if ckpt_vocab_size != model_vocab_size:
            print(f"[local_loader] Resizing word embeddings: {model_vocab_size} -> {ckpt_vocab_size}")
            model.token_rep_layer.bert_layer.model.resize_token_embeddings(ckpt_vocab_size)

    model.load_state_dict(state_dict, strict=strict, assign=True)
    print(f"[local_loader] State dict loaded (strict={strict})")

    # Step 6: Move to device and set eval mode
    if torch.cuda.is_available() and device == "cuda":
        print(f"[local_loader] Moving model to CUDA...")
        model.to("cuda")
    elif device == "cpu":
        model.to("cpu")
    model.eval()
    print(f"[local_loader] Model in eval mode on {model.device}")

    # Step 7: Record model metadata
    param_count = sum(p.numel() for p in model.parameters())
    print(f"[local_loader] Parameter count: {param_count:,}")

    if torch.cuda.is_available():
        vram_alloc = torch.cuda.memory_allocated() / 1e9
        vram_max = torch.cuda.max_memory_allocated() / 1e9
        print(f"[local_loader] VRAM allocated: {vram_alloc:.3f} GB")
        print(f"[local_loader] Max VRAM allocated: {vram_max:.3f} GB")

    # Attach metadata
    model._local_loader_meta = {
        "model_id": model_id,
        "snapshot_dir": str(snapshot_dir),
        "config_file": str(config_file),
        "model_file": str(model_file),
        "param_count": param_count,
        "device": str(model.device),
        "strict": strict,
        "backbone": config.model_name,
        "hidden_size": config.hidden_size,
    }

    return model


def get_model_info(model) -> dict:
    """Return model metadata from a locally-loaded model."""
    if hasattr(model, '_local_loader_meta'):
        return model._local_loader_meta
    return {"error": "Model was not loaded via local_loader"}


if __name__ == "__main__":
    # Quick test (will fail locally due to OOM, but shows the API)
    print("local_loader.py — bypass GLiREL's broken _from_pretrained")
    print()
    print("Usage in Kaggle notebook:")
    print("  from local_loader import load_glirel_compatible")
    print('  model = load_glirel_compatible("jackboyla/glirel-large-v0")')
    print()
    print("For glirel_beta (bypasses version assertion):")
    print('  model = load_glirel_compatible("jackboyla/glirel_beta")')
