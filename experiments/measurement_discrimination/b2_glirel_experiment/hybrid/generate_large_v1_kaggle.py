#!/usr/bin/env python3
"""generate_large_v1_kaggle.py — GLiREL-large-v0 isolated model-variable experiment.

Changes ONLY the model checkpoint. Everything else identical to V3:
  - Same V3 span adapter (frozen, unmodified)
  - Same gold benchmark (GLiREL-SPAN-GOLD-v1)
  - Same extraction labels (16 relation types)
  - Same entity definitions (controlled NER)
  - Same public 13-case fixture
  - Same evaluation code (gold_benchmark_analysis.py)

No LLM calls. No A/B/C. No hybrid. Pure evidence-substrate measurement.
"""
import json, os

CODE = r'''import os, sys, json, time, hashlib, subprocess, re
import torch
from datetime import datetime, timezone
from collections import Counter

ARTIFACT_DIR = "/kaggle/working/glirel_large_v1"
os.makedirs(ARTIFACT_DIR, exist_ok=True)
STATUS_FILE = os.path.join(ARTIFACT_DIR, "stage_status.jsonl")

def log_stage(stage, status, message=""):
    r = {"stage": stage, "status": status, "message": message,
         "timestamp": datetime.now(timezone.utc).isoformat()}
    with open(STATUS_FILE, "a") as f: f.write(json.dumps(r) + "\n")
    print(f"[{status}] {stage}: {message}", flush=True)

def run_pip(packages):
    result = subprocess.run([sys.executable, "-m", "pip", "install"] + packages,
                           text=True, capture_output=True)
    with open(os.path.join(ARTIFACT_DIR, "install.log"), "a") as f:
        f.write(f"=== pip install {' '.join(packages)} ===\n{result.stdout}\n{result.stderr}\n\n")
    if result.returncode != 0: raise RuntimeError(f"pip failed: {result.stderr[-500:]}")

log_stage("stage0", "PASS", "Setup")

# Clone repo
repo_dir = "/kaggle/working/repo"
if not os.path.exists(repo_dir):
    subprocess.run(["git", "clone", "--branch", "external-review-preparation", "--depth", "1",
                    "https://github.com/prateekm1007/technology-evolution-engine.git", repo_dir],
                   check=True, capture_output=True)
log_stage("stage1", "PASS", "Repo cloned")

# Install deps (same as V3 — no version changes)
run_pip(["setuptools_scm"])
os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"] = "1.2.2"
run_pip(["seqeval==1.2.2", "--no-build-isolation"])
del os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"]
run_pip(["glirel", "--no-deps"])
run_pip(["loguru", "protobuf", "sentencepiece", "datasets", "huggingface_hub", "tqdm"])
log_stage("stage2", "PASS", "Deps installed")

print(f"CUDA: {torch.cuda.is_available()}", flush=True)
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB", flush=True)

# Load glirel-large-v0 via local_loader (same loader as V3, different model ID)
sys.path.insert(0, os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/glirel_extractor"))
from local_loader import load_glirel_compatible, get_model_info

MODEL_ID = "jackboyla/glirel-large-v0"  # ONLY VARIABLE CHANGED from V3
print(f"Loading {MODEL_ID}...", flush=True)
t0 = time.time()
model = load_glirel_compatible(MODEL_ID, device="cuda")
t1 = time.time()
model_info = get_model_info(model)
param_count = model_info.get("param_count", 0)
print(f"Loaded: {param_count:,} params in {t1-t0:.1f}s", flush=True)
print(f"Backbone: {model_info.get('backbone')}", flush=True)
if torch.cuda.is_available():
    print(f"VRAM allocated: {torch.cuda.memory_allocated()/1e9:.3f} GB", flush=True)
    print(f"Max VRAM: {torch.cuda.max_memory_allocated()/1e9:.3f} GB", flush=True)
log_stage("stage4_model", "PASS", f"Loaded: {param_count:,} params, VRAM={torch.cuda.max_memory_allocated()/1e9:.3f}GB")

# Load V3 span adapter (FROZEN, unmodified)
sys.path.insert(0, os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/hybrid"))
from span_adapter_v3 import fix_glirel_output_v3, fix_span_v3, tokenize_like_glirel, run_span_fidelity_test_v3

# Span adapter tests (same as V3)
span_tests = run_span_fidelity_test_v3()
all_pass = all(t["pass"] for t in span_tests.values())
with open(os.path.join(ARTIFACT_DIR, "span_fidelity_v3.json"), "w") as f:
    json.dump(span_tests, f, indent=2)
log_stage("stage5_span", "PASS" if all_pass else "FAIL", f"V3 adapter: {'all pass' if all_pass else 'FAIL'}")

# Load fixture (same as V3)
fixture_path = os.path.join(repo_dir, "experiments/measurement_discrimination/b2_adversarial_v2/test_fixture.json")
with open(fixture_path) as f:
    fixture = json.load(f)
source_a = fixture["source_a"]
source_b = fixture["source_b"]

# Same entity definitions (controlled NER — Pipeline A)
def char_to_token_ner(text, entities):
    _, ts, te = tokenize_like_glirel(text)
    ner = []
    for ent in entities:
        st = next((i for i, s in enumerate(ts) if s >= ent["start"]), None)
        et = max((i for i, e in enumerate(te) if e <= ent["end"]), default=None)
        if st is not None and et is not None: ner.append([st, et, ent["label"]])
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

# Same relation labels (16 extraction relations)
rel_labels = ["CAUSES","ENABLES","INHIBITS","USES","PRODUCES","TRANSFORMS","REQUIRES",
              "FUNCTIONS_AS","MECHANISTICALLY_RELATED_TO","STRUCTURALLY_RELATED_TO",
              "FUNCTIONALLY_RELATED_TO","LOCATED_IN","ACTS_ON","MODIFIES","GENERATES","DEPENDS_ON"]

# Extract relations from all 13 public cases
all_evidence = []
head_valid = 0; head_invalid = 0; tail_valid = 0; tail_invalid = 0
fix_methods = {}

for tc in fixture["cases"]:
    t0 = time.time()
    raw_a = model.predict_relations(source_a, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_a)
    raw_b = model.predict_relations(source_b, labels=rel_labels, threshold=0.0, top_k=5, ner=ner_b)
    t1 = time.time()
    fixed_a = fix_glirel_output_v3(source_a, raw_a)
    fixed_b = fix_glirel_output_v3(source_b, raw_b)

    for edges in [fixed_a, fixed_b]:
        for r in edges:
            hs = r.get("head_span", {}); ts = r.get("tail_span", {})
            hv = hs.get("valid", False); tv = ts.get("valid", False)
            if hv: head_valid += 1
            else: head_invalid += 1
            if tv: tail_valid += 1
            else: tail_invalid += 1
            for side in ["head", "tail"]:
                m = r.get("span_fix_methods", {}).get(side, "unknown")
                fix_methods[m] = fix_methods.get(m, 0) + 1

    all_evidence.append({
        "case_id": tc["id"], "candidate": tc["candidate"],
        "source_a": {"text": source_a, "entities": ents_a, "relations": fixed_a},
        "source_b": {"text": source_b, "entities": ents_b, "relations": fixed_b},
        "stats": {"total_a": len(fixed_a), "total_b": len(fixed_b),
                  "valid_a": sum(1 for r in fixed_a if r.get("spans_valid", False)),
                  "valid_b": sum(1 for r in fixed_b if r.get("spans_valid", False)),
                  "runtime_ms": round((t1-t0)*1000, 1)}
    })
    print(f"[{tc['id']}] A:{len(fixed_a)}({all_evidence[-1]['stats']['valid_a']} valid) B:{len(fixed_b)}({all_evidence[-1]['stats']['valid_b']} valid) ({(t1-t0)*1000:.0f}ms)", flush=True)

total_rels = sum(e["stats"]["total_a"] + e["stats"]["total_b"] for e in all_evidence)
total_spans = total_rels * 2
both_valid = sum(e["stats"]["valid_a"] + e["stats"]["valid_b"] for e in all_evidence)
fidelity = both_valid / total_spans * 100 if total_spans > 0 else 0

with open(os.path.join(ARTIFACT_DIR, "evidence_graphs_large.json"), "w") as f:
    json.dump(all_evidence, f, indent=2, default=str)

span_summary = {
    "total_relations": total_rels, "total_spans": total_spans,
    "head_valid": head_valid, "head_invalid": head_invalid,
    "tail_valid": tail_valid, "tail_invalid": tail_invalid,
    "both_valid": both_valid,
    "head_fidelity_pct": round(head_valid/(head_valid+head_invalid)*100, 1) if (head_valid+head_invalid) > 0 else 0,
    "tail_fidelity_pct": round(tail_valid/(tail_valid+tail_invalid)*100, 1) if (tail_valid+tail_invalid) > 0 else 0,
    "both_fidelity_pct": round(both_valid/total_spans*100, 1) if total_spans > 0 else 0,
    "fix_methods": fix_methods,
}
with open(os.path.join(ARTIFACT_DIR, "span_fidelity_summary.json"), "w") as f:
    json.dump(span_summary, f, indent=2)

print(f"\nTotal: {total_rels} rels, {total_spans} spans", flush=True)
print(f"Head: {head_valid}/{head_valid+head_invalid} = {span_summary['head_fidelity_pct']}%", flush=True)
print(f"Tail: {tail_valid}/{tail_valid+tail_invalid} = {span_summary['tail_fidelity_pct']}%", flush=True)
print(f"Both: {both_valid}/{total_spans} = {span_summary['both_fidelity_pct']}%", flush=True)
print(f"Fix methods: {fix_methods}", flush=True)
log_stage("stage6_extract", "PASS", f"{total_rels} rels, fidelity={span_summary['both_fidelity_pct']}%")

# ── GOLD BENCHMARK (same gold set, same evaluation code) ──
gold_path = os.path.join(repo_dir, "experiments/measurement_discrimination/b2_glirel_experiment/hybrid/gold_span_benchmark.json")
with open(gold_path) as f:
    gold = json.load(f)
gold_relations = gold["gold_relations"]
source_a_text = gold["source_a"]
source_b_text = gold["source_b"]

# Build gold entities
gold_entities = {}
for gr in gold_relations:
    src = gr["source"]
    h_key = (src, gr["head_start"], gr["head_end"])
    t_key = (src, gr["tail_start"], gr["tail_end"])
    gold_entities[h_key] = gr["head_text"]
    gold_entities[t_key] = gr["tail_text"]

def spans_overlap(s1, s2):
    return s1[0] < s2[1] and s2[0] < s1[1]

def span_matches(gold_span, extracted_span):
    gs = (gold_span["start"], gold_span["end"])
    es = (extracted_span["start"], extracted_span["end"])
    if gs == es: return "EXACT"
    if es[0] >= gs[0] and es[1] <= gs[1]: return "PARTIAL_SUBSET"
    if gs[0] >= es[0] and gs[1] <= es[1]: return "PARTIAL_SUPERSET"
    if spans_overlap(gs, es): return "OVERLAP"
    return "NO_MATCH"

def classify_relation(gold_rel, extracted_rel):
    head_match = span_matches(
        {"start": gold_rel["head_start"], "end": gold_rel["head_end"]},
        {"start": extracted_rel["head_span"]["start"], "end": extracted_rel["head_span"]["end"]}
    ) if extracted_rel.get("head_span") else "NO_MATCH"
    tail_match = span_matches(
        {"start": gold_rel["tail_start"], "end": gold_rel["tail_end"]},
        {"start": extracted_rel["tail_span"]["start"], "end": extracted_rel["tail_span"]["end"]}
    ) if extracted_rel.get("tail_span") else "NO_MATCH"
    rel_match = gold_rel["relation"] == extracted_rel.get("label", "")
    gold_dir = gold_rel.get("direction", "A_TO_B")
    extracted_dir = "A_TO_B"
    dir_match = gold_dir == extracted_dir

    if head_match == "EXACT" and tail_match == "EXACT":
        if rel_match and dir_match: return "CORRECT"
        elif not rel_match: return "WRONG_RELATION"
        elif not dir_match: return "WRONG_DIRECTION"
    elif head_match in ("EXACT","PARTIAL_SUBSET","PARTIAL_SUPERSET","OVERLAP") and \
         tail_match in ("EXACT","PARTIAL_SUBSET","PARTIAL_SUPERSET","OVERLAP"):
        return "PARTIAL"
    elif head_match == "EXACT" or tail_match == "EXACT":
        return "WRONG_ENTITY"
    elif head_match != "NO_MATCH" or tail_match != "NO_MATCH":
        return "PARTIAL"
    return "AMBIGUOUS"

# Use first case (same sources as gold)
case = all_evidence[0]
extracted_a = case["source_a"]["relations"]
extracted_b = case["source_b"]["relations"]

# Span precision
extracted_spans = []
correct_spans = 0
for source_id, source_text, relations in [("A", source_a_text, extracted_a), ("B", source_b_text, extracted_b)]:
    for rel in relations:
        for side in ["head", "tail"]:
            span = rel.get(f"{side}_span", {})
            if not span or not span.get("valid"): continue
            s = (span["start"], span["end"])
            extracted_spans.append((source_id, s, span["text"]))
            for gkey in gold_entities:
                gsrc, gstart, gend = gkey
                if gsrc != source_id: continue
                match = span_matches({"start": gstart, "end": gend}, {"start": s[0], "end": s[1]})
                if match in ("EXACT","PARTIAL_SUBSET","PARTIAL_SUPERSET"):
                    correct_spans += 1
                    break

total_extracted_spans = len(extracted_spans)
span_precision = correct_spans / total_extracted_spans * 100 if total_extracted_spans > 0 else 0

# Span recall
gold_recovered = 0
for gkey in gold_entities:
    gsrc, gstart, gend = gkey
    for es in extracted_spans:
        if es[0] != gsrc: continue
        match = span_matches({"start": gstart, "end": gend}, {"start": es[1][0], "end": es[1][1]})
        if match in ("EXACT","PARTIAL_SUBSET","PARTIAL_SUPERSET"):
            gold_recovered += 1
            break
span_recall = gold_recovered / len(gold_entities) * 100 if gold_entities else 0

# Relation precision
correct_relations = 0
relation_classifications = []
for source_id, source_text, relations in [("A", source_a_text, extracted_a), ("B", source_b_text, extracted_b)]:
    for idx, rel in enumerate(relations):
        best_class = "AMBIGUOUS"
        for gr in gold_relations:
            if gr["source"] != source_id: continue
            cls = classify_relation(gr, rel)
            if cls == "CORRECT":
                best_class = "CORRECT"
                break
            elif cls in ("PARTIAL","WRONG_RELATION","WRONG_DIRECTION","WRONG_ENTITY"):
                if best_class == "AMBIGUOUS": best_class = cls
        if best_class == "CORRECT": correct_relations += 1
        relation_classifications.append({
            "source": source_id, "idx": idx,
            "label": rel.get("label"), "head": rel.get("head_text"), "tail": rel.get("tail_text"),
            "score": rel.get("score"), "classification": best_class
        })

total_extracted_relations = len(extracted_a) + len(extracted_b)
relation_precision = correct_relations / total_extracted_relations * 100 if total_extracted_relations > 0 else 0

# Relation recall
gold_recovered_rel = 0
for gr in gold_relations:
    source_id = gr["source"]
    relations = extracted_a if source_id == "A" else extracted_b
    for rel in relations:
        if classify_relation(gr, rel) == "CORRECT":
            gold_recovered_rel += 1
            break
relation_recall = gold_recovered_rel / len(gold_relations) * 100 if gold_relations else 0

# Direction accuracy
dir_correct = 0; dir_total = 0
for rc in relation_classifications:
    if rc["classification"] in ("CORRECT","PARTIAL","WRONG_RELATION"):
        dir_total += 1
        if rc["classification"] == "CORRECT": dir_correct += 1
dir_accuracy = dir_correct / dir_total * 100 if dir_total > 0 else 0

# Mechanical validity (independent)
mech_valid = 0; mech_total = 0
for source_id, source_text, relations in [("A", source_a_text, extracted_a), ("B", source_b_text, extracted_b)]:
    for rel in relations:
        for side in ["head", "tail"]:
            span = rel.get(f"{side}_span", {})
            if span:
                mech_total += 1
                if span.get("valid") and source_text[span["start"]:span["end"]] == span["text"]:
                    mech_valid += 1
mech_pct = mech_valid / mech_total * 100 if mech_total > 0 else 0

# Classification breakdown
cls_counts = Counter(rc["classification"] for rc in relation_classifications)

gold_results = {
    "model": MODEL_ID,
    "gold_relations": len(gold_relations), "gold_entities": len(gold_entities),
    "extracted_relations": total_extracted_relations, "extracted_spans": total_extracted_spans,
    "mechanical_validity_pct": round(mech_pct, 1),
    "span_precision_pct": round(span_precision, 1),
    "span_recall_pct": round(span_recall, 1),
    "relation_precision_pct": round(relation_precision, 1),
    "relation_recall_pct": round(relation_recall, 1),
    "direction_accuracy_pct": round(dir_accuracy, 1),
    "relation_classification": dict(cls_counts.most_common()),
    "fix_methods": fix_methods,
}
with open(os.path.join(ARTIFACT_DIR, "gold_benchmark_results.json"), "w") as f:
    json.dump(gold_results, f, indent=2)
with open(os.path.join(ARTIFACT_DIR, "gold_relation_classifications.json"), "w") as f:
    json.dump(relation_classifications, f, indent=2)

print(f"\n{'='*60}", flush=True)
print(f"GOLD BENCHMARK — {MODEL_ID}", flush=True)
print(f"{'='*60}", flush=True)
print(f"Mechanical validity: {mech_pct:.1f}% ({mech_valid}/{mech_total})", flush=True)
print(f"Span precision: {span_precision:.1f}% ({correct_spans}/{total_extracted_spans})", flush=True)
print(f"Span recall: {span_recall:.1f}% ({gold_recovered}/{len(gold_entities)})", flush=True)
print(f"Relation precision: {relation_precision:.1f}% ({correct_relations}/{total_extracted_relations})", flush=True)
print(f"Relation recall: {relation_recall:.1f}% ({gold_recovered_rel}/{len(gold_relations)})", flush=True)
print(f"Direction accuracy: {dir_accuracy:.1f}% ({dir_correct}/{dir_total})", flush=True)
print(f"Classification: {dict(cls_counts.most_common())}", flush=True)
print(f"Fix methods: {fix_methods}", flush=True)
log_stage("stage7_gold", "PASS", f"rel_precision={relation_precision:.1f}%, dir_accuracy={dir_accuracy:.1f}%")

# ── COMPARISON TABLE ──
print(f"\n{'='*60}", flush=True)
print(f"COMPARISON: glirel_beta (V3) vs glirel-large-v0", flush=True)
print(f"{'='*60}", flush=True)
print(f"{'Metric':<30} {'Beta (V3)':<20} {'Large (v1)':<20}", flush=True)
print(f"{'-'*70}", flush=True)
print(f"{'Mechanical validity':<30} {'100.0%':<20} {mech_pct:.1f}%{'':<15}", flush=True)
print(f"{'Span precision':<30} {'100.0%':<20} {span_precision:.1f}%{'':<15}", flush=True)
print(f"{'Span recall':<30} {'73.7%':<20} {span_recall:.1f}%{'':<15}", flush=True)
print(f"{'Relation precision':<30} {'1.2%':<20} {relation_precision:.1f}%{'':<15}", flush=True)
print(f"{'Relation recall':<30} {'10.0%':<20} {relation_recall:.1f}%{'':<15}", flush=True)
print(f"{'Direction accuracy':<30} {'2.0%':<20} {dir_accuracy:.1f}%{'':<15}", flush=True)
print(f"{'Total relations':<30} {'250':<20} {total_extracted_relations:<20}", flush=True)

# ── DECISION GATE ──
print(f"\n{'='*60}", flush=True)
print(f"PRE-REGISTERED DECISION GATE", flush=True)
print(f"{'='*60}", flush=True)
beta_rel_precision = 1.2
improvement = relation_precision - beta_rel_precision
print(f"Beta relation precision: {beta_rel_precision}%", flush=True)
print(f"Large relation precision: {relation_precision:.1f}%", flush=True)
print(f"Improvement: {improvement:.1f} percentage points", flush=True)
print(f"Direction accuracy: {dir_accuracy:.1f}% (beta was 2.0%)", flush=True)

if relation_precision <= beta_rel_precision + 2.0:
    decision = "STOP — relation precision did not materially improve"
    print(f"\nDECISION: {decision}", flush=True)
    print("GLiREL-large-v0 does not materially improve relation quality.", flush=True)
    print("GLiREL investigation should be suspended.", flush=True)
elif dir_accuracy < 10.0:
    decision = "STOP — direction accuracy still too low"
    print(f"\nDECISION: {decision}", flush=True)
    print("Relation precision improved but direction accuracy remains unreliable.", flush=True)
else:
    decision = "PROCEED — relation precision materially improved; authorize A/B/C"
    print(f"\nDECISION: {decision}", flush=True)
    print("GLiREL-large-v0 materially improves evidence quality.", flush=True)
    print("Next step: run A/B/C representation experiment with large model.", flush=True)

# ── Environment + pack ──
import platform, shutil
env = {"python": sys.version, "torch": torch.__version__, "cuda": torch.cuda.is_available(),
       "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
       "vram_gb": torch.cuda.get_device_properties(0).total_memory/1e9 if torch.cuda.is_available() else 0,
       "vram_allocated_gb": torch.cuda.memory_allocated()/1e9 if torch.cuda.is_available() else 0,
       "max_vram_gb": torch.cuda.max_memory_allocated()/1e9 if torch.cuda.is_available() else 0,
       "glirel": __import__("glirel").__version__,
       "model_id": MODEL_ID, "param_count": param_count,
       "backbone": model_info.get("backbone"),
       "load_time_s": round(t1-t0, 1),
       "timestamp": datetime.now(timezone.utc).isoformat()}
with open(os.path.join(ARTIFACT_DIR, "environment.json"), "w") as f:
    json.dump(env, f, indent=2)

ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
archive = f"/kaggle/working/glirel_large_v1_{ts_str}"
shutil.make_archive(archive, "gztar", ARTIFACT_DIR)
with open(f"{archive}.tar.gz", "rb") as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()
print(f"\nSHA-256: {sha256}", flush=True)

final_report = {
    "experiment": "GLiREL-large-v0 isolated model-variable experiment",
    "model": MODEL_ID, "param_count": param_count,
    "mechanical_validity_pct": round(mech_pct, 1),
    "span_precision_pct": round(span_precision, 1),
    "span_recall_pct": round(span_recall, 1),
    "relation_precision_pct": round(relation_precision, 1),
    "relation_recall_pct": round(relation_recall, 1),
    "direction_accuracy_pct": round(dir_accuracy, 1),
    "relation_classification": dict(cls_counts.most_common()),
    "decision": decision,
    "artifact_sha256": sha256,
    "frozen_b2_unchanged": True, "heldout_accessed": False,
    "v3_adapter_unchanged": True,
    "label": "NON-AUTHORITATIVE PARALLEL ENGINEERING EXPERIMENT",
    "comparison": {
        "beta_relation_precision": 1.2, "large_relation_precision": round(relation_precision, 1),
        "beta_direction_accuracy": 2.0, "large_direction_accuracy": round(dir_accuracy, 1),
        "improvement_relation_precision": round(improvement, 1),
    }
}
with open(os.path.join(ARTIFACT_DIR, "final_report.json"), "w") as f:
    json.dump(final_report, f, indent=2)

log_stage("stage8_pack", "PASS", f"SHA-256: {sha256}")
print(f"\n{'='*60}", flush=True)
print("EXPERIMENT COMPLETE", flush=True)
print(f"{'='*60}", flush=True)
print(json.dumps(final_report, indent=2), flush=True)
'''

lines = CODE.split('\n')
source_list = [line + '\n' for line in lines[:-1]] + [lines[-1]]

cells = [
    {"cell_type": "markdown", "metadata": {},
     "source": ["# GLiREL-large-v0 Isolated Model-Variable Experiment\n",
                "\n", "ONLY VARIABLE CHANGED: model checkpoint (glirel_beta -> glirel-large-v0)\n",
                "V3 adapter: FROZEN (unmodified). Gold benchmark: same. Entities: same. Labels: same.\n",
                "No LLM calls. No A/B/C. No hybrid. Pure evidence-substrate measurement.\n",
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

outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b2_glirel_large_v1_kaggle.ipynb")
with open(outpath, "w") as f:
    json.dump(notebook, f, indent=2)
print(f"Notebook generated: {outpath}")
print(f"Code cell lines: {len(source_list)}")
