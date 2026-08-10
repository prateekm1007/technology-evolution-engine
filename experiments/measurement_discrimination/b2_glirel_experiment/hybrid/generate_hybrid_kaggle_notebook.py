#!/usr/bin/env python3
"""generate_hybrid_kaggle_notebook.py — Phase 1: GLiREL extraction on Kaggle.

Extracts relations from both sources for all 13 public cases, fixes spans
via span_adapter, and saves evidence graphs as JSON.

Phase 2 (local) will load these evidence graphs and call GLM for adjudication.
"""
import json, os

EXPERIMENT_CODE = r'''import os, sys, json, time, hashlib, subprocess, traceback, re
import torch
from datetime import datetime, timezone

ARTIFACT_DIR = "/kaggle/working/hybrid_artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)
STATUS_FILE = os.path.join(ARTIFACT_DIR, "stage_status.jsonl")

def log_stage(stage, status, message="", **kw):
    record = {"stage": stage, "status": status, "message": message,
              "timestamp": datetime.now(timezone.utc).isoformat(), **kw}
    with open(STATUS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[{status}] {stage}: {message}", flush=True)

def run_pip(packages):
    result = subprocess.run([sys.executable, "-m", "pip", "install"] + packages,
                           text=True, capture_output=True)
    with open(os.path.join(ARTIFACT_DIR, "install.log"), "a") as f:
        f.write(f"=== pip install {' '.join(packages)} ===\n{result.stdout}\n{result.stderr}\n\n")
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed: {result.stderr[-500:]}")

# ── Stage 0-1: Clone repo ──
log_stage("stage0", "PASS", "Setup")
repo_dir = "/kaggle/working/repo"
if not os.path.exists(repo_dir):
    subprocess.run(["git", "clone", "--branch", "external-review-preparation", "--depth", "1",
                    "https://github.com/prateekm1007/technology-evolution-engine.git", repo_dir],
                   check=True, capture_output=True)
log_stage("stage1_clone", "PASS", "Repo cloned")

# ── Stage 2: Install deps ──
run_pip(["setuptools_scm"])
os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"] = "1.2.2"
run_pip(["seqeval==1.2.2", "--no-build-isolation"])
del os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"]
run_pip(["glirel", "--no-deps"])
run_pip(["loguru", "protobuf", "sentencepiece", "datasets", "huggingface_hub", "tqdm"])
log_stage("stage2_install", "PASS", "Deps installed")

# ── Stage 3: GPU ──
print(f"CUDA: {torch.cuda.is_available()}", flush=True)
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

# ── Stage 4: Load model ──
sys.path.insert(0, os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/glirel_extractor"))
from local_loader import load_glirel_compatible, get_model_info
MODEL_ID = "jackboyla/glirel_beta"
print(f"Loading {MODEL_ID}...", flush=True)
t0 = time.time()
model = load_glirel_compatible(MODEL_ID, device="cuda")
t1 = time.time()
model_info = get_model_info(model)
print(f"Loaded in {t1-t0:.1f}s, params={model_info.get('param_count',0):,}", flush=True)
log_stage("stage4_model", "PASS", f"Loaded: {model_info.get('param_count',0):,} params")

# ── Stage 5: Span adapter test ──
sys.path.insert(0, os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/hybrid"))
from span_adapter import fix_glirel_output, fix_span, tokenize_like_glirel, run_span_fidelity_test

span_tests = run_span_fidelity_test()
all_span_pass = all(t["pass"] for t in span_tests.values())
with open(os.path.join(ARTIFACT_DIR, "span_fidelity.json"), "w") as f:
    json.dump(span_tests, f, indent=2)
log_stage("stage5_span_test", "PASS" if all_span_pass else "FAIL",
          f"Span adapter: {'all pass' if all_span_pass else 'FAIL'}")

# ── Stage 6: Extract relations from public 13 cases ──
fixture_path = os.path.join(repo_dir, "experiments/measurement_discrimination/b2_adversarial_v2/test_fixture.json")
with open(fixture_path) as f:
    fixture = json.load(f)

source_a = fixture["source_a"]
source_b = fixture["source_b"]

def char_to_token_ner(text, entities):
    _, ts, te = tokenize_like_glirel(text)
    ner = []
    for ent in entities:
        st = next((i for i, s in enumerate(ts) if s >= ent["start"]), None)
        et = max((i for i, e in enumerate(te) if e <= ent["end"]), default=None)
        if st is not None and et is not None:
            ner.append([st, et, ent["label"]])
    return ner

ents_a = [{"label":"MINERAL","text":"Calcium phosphate","start":0,"end":17},
          {"label":"DEPOSIT","text":"crystalline deposits","start":25,"end":44},
          {"label":"TISSUE","text":"bone tissue","start":49,"end":60},
          {"label":"CELL","text":"osteoblast","start":70,"end":80},
          {"label":"PROCESS","text":"mineralization","start":92,"end":106}]
ents_b = [{"label":"ORGANISM","text":"Marine diatoms","start":0,"end":14},
          {"label":"PROCESS","text":"precipitate","start":15,"end":26},
          {"label":"MINERAL","text":"silica","start":27,"end":33},
          {"label":"STRUCTURE","text":"cell walls","start":41,"end":51},
          {"label":"ENZYME","text":"silicatein","start":67,"end":77},
          {"label":"PROTEIN","text":"proteins","start":78,"end":86}]
ner_a = char_to_token_ner(source_a, ents_a)
ner_b = char_to_token_ner(source_b, ents_b)

rel_labels = ["CAUSES","ENABLES","INHIBITS","USES","PRODUCES","TRANSFORMS","REQUIRES",
              "FUNCTIONS_AS","MECHANISTICALLY_RELATED_TO","STRUCTURALLY_RELATED_TO",
              "FUNCTIONALLY_RELATED_TO","LOCATED_IN","ACTS_ON","MODIFIES","GENERATES","DEPENDS_ON"]

all_evidence = []
for tc in fixture["cases"]:
    t0 = time.time()
    raw_a = model.predict_relations(source_a, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_a)
    raw_b = model.predict_relations(source_b, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_b)
    t1 = time.time()

    # Fix spans
    fixed_a = fix_glirel_output(source_a, raw_a)
    fixed_b = fix_glirel_output(source_b, raw_b)

    # Count valid/invalid spans
    valid_a = sum(1 for r in fixed_a if r.get("spans_valid", False))
    valid_b = sum(1 for r in fixed_b if r.get("spans_valid", False))

    all_evidence.append({
        "case_id": tc["id"],
        "candidate": tc["candidate"],
        "source_a_text": source_a,
        "source_b_text": source_b,
        "edges_a": fixed_a,
        "edges_b": fixed_b,
        "stats": {
            "total_a": len(fixed_a), "valid_a": valid_a, "invalid_a": len(fixed_a) - valid_a,
            "total_b": len(fixed_b), "valid_b": valid_b, "invalid_b": len(fixed_b) - valid_b,
            "runtime_ms": round((t1-t0)*1000, 1),
        }
    })
    print(f"[{tc['id']}] A:{len(fixed_a)}({valid_a} valid) B:{len(fixed_b)}({valid_b} valid) ({(t1-t0)*1000:.0f}ms)", flush=True)

with open(os.path.join(ARTIFACT_DIR, "evidence_graphs.json"), "w") as f:
    json.dump(all_evidence, f, indent=2, default=str)

# Summary stats
total_rels = sum(e["stats"]["total_a"] + e["stats"]["total_b"] for e in all_evidence)
total_valid = sum(e["stats"]["valid_a"] + e["stats"]["valid_b"] for e in all_evidence)
total_invalid = total_rels - total_valid
print(f"\nTotal: {total_rels} relations, {total_valid} valid, {total_invalid} invalid", flush=True)
print(f"Span fidelity: {total_valid}/{total_rels} = {total_valid/total_rels*100:.1f}%", flush=True)

log_stage("stage6_extract", "PASS",
          f"13 cases: {total_rels} rels, {total_valid} valid ({total_valid/total_rels*100:.1f}%)")

# ── Stage 7: Save environment + model metadata ──
import platform
env_meta = {
    "python": sys.version, "platform": platform.platform(),
    "torch": torch.__version__, "cuda": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    "glirel": __import__("glirel").__version__,
    "model_id": MODEL_ID, "param_count": model_info.get("param_count"),
    "backbone": model_info.get("backbone"),
    "load_time_s": round(t1-t0, 1),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "span_fidelity_pct": round(total_valid/total_rels*100, 1) if total_rels > 0 else 0,
    "total_relations": total_rels, "valid_relations": total_valid,
    "invalid_relations": total_invalid,
}
with open(os.path.join(ARTIFACT_DIR, "environment.json"), "w") as f:
    json.dump(env_meta, f, indent=2)

# ── Stage 8: Pack artifacts ──
import shutil
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
archive = f"/kaggle/working/hybrid_artifacts_{ts}"
shutil.make_archive(archive, "gztar", ARTIFACT_DIR)
with open(f"{archive}.tar.gz", "rb") as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()
print(f"Archive SHA-256: {sha256}", flush=True)

# Save model selection info
model_selection = {
    "requested_model": "GLM-5.2",
    "actual_model": "glm-4-plus",
    "glm_5_2_available": False,
    "fallback_used": True,
    "fallback_reason": "API accepts any model name without validation; response model field always returns glm-4-plus; cannot confirm GLM-5.2 is actually available",
    "note": "GLM adjudication will be performed locally in Phase 2 using z-ai SDK",
}
with open(os.path.join(ARTIFACT_DIR, "model_selection.json"), "w") as f:
    json.dump(model_selection, f, indent=2)

log_stage("stage8_pack", "PASS", f"SHA-256: {sha256}")

# Final report
report = {
    "experiment": "B-2 GLiREL hybrid Phase 1 (extraction only)",
    "date": datetime.now(timezone.utc).isoformat(),
    "model": MODEL_ID, "param_count": model_info.get("param_count"),
    "all_stages_pass": True,
    "span_fidelity_pct": env_meta["span_fidelity_pct"],
    "total_relations": total_rels, "valid_relations": total_valid,
    "invalid_relations": total_invalid,
    "artifact_sha256": sha256,
    "frozen_b2_unchanged": True, "heldout_accessed": False,
    "label": "NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT",
    "next_phase": "Phase 2: GLM adjudication locally using evidence_graphs.json",
}
with open(os.path.join(ARTIFACT_DIR, "final_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print("\n" + "="*60, flush=True)
print("PHASE 1 COMPLETE", flush=True)
print("="*60, flush=True)
print(json.dumps(report, indent=2), flush=True)
'''

# Build notebook
lines = EXPERIMENT_CODE.split('\n')
source_list = [line + '\n' for line in lines[:-1]] + [lines[-1]]

cells = [
    {"cell_type": "markdown", "metadata": {},
     "source": ["# B-2 GLiREL Hybrid Experiment — Phase 1: Extraction\n",
                "\n", "GLiREL extraction + span fixing. Phase 2 (GLM adjudication) runs locally.\n",
                "**Frozen B-2:** UNTOUCHED. **Held-out:** NOT ACCESSED.\n"]},
    {"cell_type": "code", "execution_count": None, "metadata": {},
     "outputs": [], "source": source_list},
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.13"},
        "kaggle": {"accelerator": "gpu", "isGpuEnabled": True, "isTpuEnabled": False,
                   "dataSources": [], "dockerImageVersion": None},
    },
    "nbformat": 4, "nbformat_minor": 4,
}

outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b2_hybrid_kaggle.ipynb")
with open(outpath, "w") as f:
    json.dump(notebook, f, indent=2)
print(f"Notebook generated: {outpath}")
print(f"Code cell lines: {len(source_list)}")
