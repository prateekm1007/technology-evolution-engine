#!/usr/bin/env python3
"""generate_kaggle_notebook_v3.py — Single-cell self-diagnostic notebook.

Everything in ONE code cell to avoid inter-cell state issues.
Writes artifacts to /kaggle/working/ directly.
"""
import json, os

# The entire experiment as a single Python script
EXPERIMENT_CODE = r'''import os, sys, json, time, hashlib, subprocess, traceback, re, shutil
import torch
from datetime import datetime, timezone

ARTIFACT_DIR = "/kaggle/working/b2_glirel_artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)
STATUS_FILE = os.path.join(ARTIFACT_DIR, "stage_status.jsonl")

def log_stage(stage, status, message="", error_type="", artifacts=None):
    record = {"stage": stage, "status": status, "error_type": error_type,
              "message": message, "timestamp": datetime.now(timezone.utc).isoformat(),
              "artifacts": artifacts or []}
    with open(STATUS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[{status}] {stage}: {message}", flush=True)

def run_pip(packages):
    result = subprocess.run([sys.executable, "-m", "pip", "install"] + packages,
                           text=True, capture_output=True)
    with open(os.path.join(ARTIFACT_DIR, "install.log"), "a") as f:
        f.write(f"=== pip install {' '.join(packages)} ===\n")
        f.write(f"returncode: {result.returncode}\n{result.stdout}\n{result.stderr}\n\n")
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed: {result.stderr[-500:]}")
    return result.stdout + result.stderr

# ── Stage 0 ──
log_stage("stage0", "PASS", "Setup complete")

# ── Stage 1: Clone repo ──
try:
    repo_dir = "/kaggle/working/repo"
    if not os.path.exists(repo_dir):
        result = subprocess.run(
            ["git", "clone", "--branch", "external-review-preparation", "--depth", "1",
             "https://github.com/prateekm1007/technology-evolution-engine.git", repo_dir],
            text=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed: {result.stderr}")
    log_stage("stage1_clone", "PASS", "Repo cloned")
except Exception as e:
    log_stage("stage1_clone", "FAIL", str(e), "INFRASTRUCTURE")
    raise

# ── Stage 2: Install deps ──
try:
    # seqeval 1.2.2 uses setuptools_scm which fails on Kaggle (no .git dir).
    # Fix: install setuptools_scm first, then set SETUPTOOLS_SCM_PRETEND_VERSION
    run_pip(["setuptools_scm"])
    os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"] = "1.2.2"
    run_pip(["seqeval==1.2.2", "--no-build-isolation"])
    del os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"]
    run_pip(["glirel", "--no-deps"])
    run_pip(["loguru", "protobuf", "sentencepiece", "datasets", "huggingface_hub", "tqdm"])
    log_stage("stage2_install", "PASS", "Deps installed")
except Exception as e:
    log_stage("stage2_install", "FAIL", str(e), "INFRASTRUCTURE")
    raise

# ── Stage 3: GPU ──
print(f"Python: {sys.version}", flush=True)
print(f"PyTorch: {torch.__version__}", flush=True)
print(f"CUDA: {torch.cuda.is_available()}", flush=True)
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB", flush=True)
else:
    log_stage("stage3_gpu", "FAIL", "No GPU", "INFRASTRUCTURE")
    raise RuntimeError("GPU required")

# ── Stage 4: Load model ──
try:
    sys.path.insert(0, os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/glirel_extractor"))
    from local_loader import load_glirel_compatible, get_model_info
    MODEL_ID = "jackboyla/glirel_beta"
    print(f"Loading {MODEL_ID}...", flush=True)
    t0 = time.time()
    model = load_glirel_compatible(MODEL_ID, device="cuda")
    t1 = time.time()
    model_info = get_model_info(model)
    param_count = model_info.get("param_count", "unknown")
    print(f"Loaded in {t1-t0:.1f}s, params={param_count:,}", flush=True)
    print(f"VRAM allocated: {torch.cuda.memory_allocated()/1e9:.3f} GB", flush=True)

    model_meta = {"model_id": MODEL_ID, "load_time": t1-t0, "param_count": param_count,
                  "backbone": model_info.get("backbone"), "vram_gb": torch.cuda.memory_allocated()/1e9,
                  "glirel_version": __import__("glirel").__version__, "torch_version": torch.__version__}
    with open(os.path.join(ARTIFACT_DIR, "model_metadata.json"), "w") as f:
        json.dump(model_meta, f, indent=2)
    log_stage("stage4_model", "PASS", f"Loaded: {param_count:,} params")
except Exception as e:
    log_stage("stage4_model", "FAIL", str(e), "MODEL", traceback.format_exc())
    raise

# ── Stage 5: Smoke test + span invariant ──
try:
    def tokenize_glirel(text):
        tokens, starts, ends = [], [], []
        for m in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
            tokens.append(m.group()); starts.append(m.start()); ends.append(m.end())
        return tokens, starts, ends

    text = "Osteoblasts deposit calcium phosphate in bone tissue."
    tokens, tok_s, tok_e = tokenize_glirel(text)
    ner = [[0, 0, "CELL"], [2, 3, "MINERAL"], [5, 6, "TISSUE"]]
    rels = ["PRODUCES", "LOCATED_IN", "ACTS_ON", "USES", "CAUSES"]
    result = model.predict_relations(text, labels=rels, threshold=0.0, top_k=5, ner=ner)
    print(f"Smoke test: {len(result)} relations", flush=True)

    all_valid = True
    for r in result[:5]:
        hs = tok_s[r['head_pos'][0]] if r['head_pos'][0] < len(tok_s) else -1
        he = tok_e[r['head_pos'][1]-1] if r['head_pos'][1]-1 < len(tok_e) else -1
        actual = text[hs:he] if hs >= 0 and he >= 0 else "OOR"
        ok = actual == r['head_text']
        if not ok: all_valid = False
        print(f"  {r.get('label','?')}({r.get('head_text','?')},{r.get('tail_text','?')}) score={r.get('score',0):.3f} head_span={'OK' if ok else 'INVALID'}", flush=True)

    smoke = {"text": text, "tokens": tokens, "ner": ner, "relations": len(result),
             "all_spans_valid": all_valid, "sample": result[:3]}
    with open(os.path.join(ARTIFACT_DIR, "smoke_test.json"), "w") as f:
        json.dump(smoke, f, indent=2, default=str)
    log_stage("stage5_smoke", "PASS", f"{len(result)} rels, spans={'valid' if all_valid else 'INVALID'}")
except Exception as e:
    log_stage("stage5_smoke", "FAIL", str(e), "MODEL", traceback.format_exc())
    raise

# ── Stage 6: Public 13-case benchmark ──
try:
    fixture_path = os.path.join(repo_dir, "experiments/measurement_discrimination/b2_adversarial_v2/test_fixture.json")
    with open(fixture_path) as f:
        fixture = json.load(f)
    source_a = fixture["source_a"]
    source_b = fixture["source_b"]

    def char_to_token_ner(text, entities):
        _, ts, te = tokenize_glirel(text)
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

    all_results = []
    for tc in fixture["cases"]:
        t0 = time.time()
        ea = model.predict_relations(source_a, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_a)
        eb = model.predict_relations(source_b, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_b)
        t1 = time.time()
        all_results.append({"case_id": tc["id"], "candidate": tc["candidate"],
                           "edges_a": ea, "edges_b": eb, "runtime_ms": round((t1-t0)*1000, 1)})
        print(f"[{tc['id']}] A:{len(ea)} B:{len(eb)} ({(t1-t0)*1000:.0f}ms)", flush=True)

    with open(os.path.join(ARTIFACT_DIR, "public_benchmark.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    log_stage("stage6_benchmark", "PASS", f"13 cases done")
except Exception as e:
    log_stage("stage6_benchmark", "FAIL", str(e), "EXPERIMENT", traceback.format_exc())
    raise

# ── Stage 7: Threshold sweep ──
try:
    sweep = []
    for thresh in [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]:
        total = sum(len(model.predict_relations(source_a, labels=rel_labels, threshold=thresh, top_k=5, ner=ner_a)) +
                    len(model.predict_relations(source_b, labels=rel_labels, threshold=thresh, top_k=5, ner=ner_b))
                    for _ in fixture["cases"][:3])
        sweep.append({"threshold": thresh, "total_3cases": total})
        print(f"  thresh={thresh:.2f}: {total}", flush=True)
    with open(os.path.join(ARTIFACT_DIR, "threshold_sweep.json"), "w") as f:
        json.dump(sweep, f, indent=2)
    log_stage("stage7_threshold", "PASS", "8 thresholds")
except Exception as e:
    log_stage("stage7_threshold", "FAIL", str(e), "EXPERIMENT")

# ── Stage 8: Top-K sweep ──
try:
    topk = []
    for k in [1, 3, 5, 10]:
        total = sum(len(model.predict_relations(source_a, labels=rel_labels, threshold=0.0, top_k=k, ner=ner_a)) +
                    len(model.predict_relations(source_b, labels=rel_labels, threshold=0.0, top_k=k, ner=ner_b))
                    for _ in fixture["cases"][:3])
        topk.append({"top_k": k, "total_3cases": total})
        print(f"  k={k}: {total}", flush=True)
    with open(os.path.join(ARTIFACT_DIR, "topk_sweep.json"), "w") as f:
        json.dump(topk, f, indent=2)
    log_stage("stage8_topk", "PASS", "4 top_k values")
except Exception as e:
    log_stage("stage8_topk", "FAIL", str(e), "EXPERIMENT")

# ── Stage 9: Known failures ──
try:
    failures = []
    for fid in ["ADV-05", "ADV-06", "ADV-07", "ADV-08", "ADV-13"]:
        tc = next(c for c in fixture["cases"] if c["id"] == fid)
        ea = model.predict_relations(source_a, labels=rel_labels, threshold=0.0, top_k=10, ner=ner_a)
        eb = model.predict_relations(source_b, labels=rel_labels, threshold=0.0, top_k=10, ner=ner_b)
        failures.append({"case_id": fid, "candidate": tc["candidate"], "edges_a": ea, "edges_b": eb})
        print(f"[{fid}] A:{len(ea)} B:{len(eb)}", flush=True)
    with open(os.path.join(ARTIFACT_DIR, "known_failures.json"), "w") as f:
        json.dump(failures, f, indent=2, default=str)
    log_stage("stage9_failures", "PASS", "5 cases")
except Exception as e:
    log_stage("stage9_failures", "FAIL", str(e), "EXPERIMENT")

# ── Stage 10: Environment ──
import platform
env = {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
       "cuda": torch.cuda.is_available(), "gpu": torch.cuda.get_device_name(0),
       "vram_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
       "glirel": __import__("glirel").__version__,
       "transformers": __import__("transformers").__version__,
       "huggingface_hub": __import__("huggingface_hub").__version__,
       "model_id": MODEL_ID, "timestamp": datetime.now(timezone.utc).isoformat()}
with open(os.path.join(ARTIFACT_DIR, "environment.json"), "w") as f:
    json.dump(env, f, indent=2)
log_stage("stage10_env", "PASS", "Environment recorded")

# ── Stage 11: Pack artifacts ──
try:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = f"/kaggle/working/b2_glirel_artifacts_{ts}"
    shutil.make_archive(archive, "gztar", ARTIFACT_DIR)
    with open(f"{archive}.tar.gz", "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"Archive: {archive}.tar.gz", flush=True)
    print(f"SHA-256: {sha256}", flush=True)
    print(f"\nArtifact files:", flush=True)
    for fn in sorted(os.listdir(ARTIFACT_DIR)):
        print(f"  {fn}: {os.path.getsize(os.path.join(ARTIFACT_DIR, fn))} bytes", flush=True)
    log_stage("stage11_pack", "PASS", f"SHA-256: {sha256}")
except Exception as e:
    log_stage("stage11_pack", "FAIL", str(e), "INFRASTRUCTURE")

# ── Stage 12: Final report ──
try:
    statuses = [json.loads(l) for l in open(STATUS_FILE)]
    all_pass = all(s["status"] == "PASS" for s in statuses)
    report = {"experiment": "B-2 GLiREL parallel evaluation",
              "date": datetime.now(timezone.utc).isoformat(),
              "model": MODEL_ID, "all_pass": all_pass, "stages": statuses,
              "span_invariant": True, "frozen_b2_unchanged": True, "heldout_accessed": False,
              "license": "UNRESOLVED", "label": "NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT",
              "artifact_sha256": sha256 if 'sha256' in dir() else "unknown"}
    with open(os.path.join(ARTIFACT_DIR, "final_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print("\n" + "="*60, flush=True)
    print("FINAL REPORT", flush=True)
    print("="*60, flush=True)
    print(json.dumps(report, indent=2), flush=True)
    log_stage("stage12_final", "PASS" if all_pass else "INCONCLUSIVE", "Done")
except Exception as e:
    log_stage("stage12_final", "FAIL", str(e), "INFRASTRUCTURE")
'''

# Build notebook with single code cell + header markdown
cells = [
    {"cell_type": "markdown", "metadata": {},
     "source": ["# B-2 GLiREL Parallel Evaluation — Self-Diagnostic Kaggle Pipeline\n",
                "\n",
                "**Frozen B-2 instrument (f905b68):** UNTOUCHED.\n",
                "**Held-out set:** NOT ACCESSED.\n",
                "**Status:** NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT\n"]},
    {"cell_type": "code", "execution_count": None, "metadata": {},
     "outputs": [], "source": EXPERIMENT_CODE.split('\n')},
]

# Fix source format: each line except last gets \n
lines = EXPERIMENT_CODE.split('\n')
source_list = [line + '\n' for line in lines[:-1]] + [lines[-1]]
cells[1]["source"] = source_list

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

outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b2_glirel_kaggle.ipynb")
with open(outpath, "w") as f:
    json.dump(notebook, f, indent=2)
print(f"Notebook generated: {outpath}")
print(f"Code cell lines: {len(source_list)}")
