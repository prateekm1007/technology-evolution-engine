"""Benchmark Drift Detection (Discipline 3, Law 7)."""
import json, hashlib
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent.parent
DRIFT_DIR = ROOT / "benchmarks" / "drift"
BASELINE_FILE = DRIFT_DIR / "baseline.json"
DRIFT_LOG = DRIFT_DIR / "drift_log.jsonl"
OUTPUTS_DIR = ROOT / "benchmarks" / "outputs"
GRAPH_FILE = ROOT / "data" / "civilization_graph.json"
THRESHOLDS = {"score_delta":0.05,"node_count_delta":5,"edge_count_delta":10,"assumption_change":True,"prerequisite_delta":0.1,"resurrection_delta":0.1}

def compute_graph_signature() -> dict:
    if not GRAPH_FILE.exists(): return {"nodes":0,"edges":0,"hash":"missing"}
    with open(GRAPH_FILE) as f: graph = json.load(f)
    nodes, edges = graph.get("nodes",[]), graph.get("edges",[])
    h = hashlib.sha256(json.dumps(graph,sort_keys=True).encode()).hexdigest()[:16]
    return {"nodes":len(nodes),"edges":len(edges),"hash":h}

def compute_output_signatures() -> Dict[str,dict]:
    sigs = {}
    if not OUTPUTS_DIR.exists(): return sigs
    for f in sorted(OUTPUTS_DIR.glob("*_output.json")):
        with open(f) as fh: out = json.load(fh)
        bid = out.get("id", f.stem.replace("_output",""))
        sigs[bid] = {"pcs":out.get("pcs",0),"rps":out.get("rps",0),"assumptions":out.get("assumptions",[]),
            "permutation_count":len(out.get("permutations",[])),
            "content_hash":hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()[:16]}
    return sigs

def create_baseline() -> dict:
    b = {"created_at":datetime.now(timezone.utc).isoformat(),"graph_signature":compute_graph_signature(),
        "output_signatures":compute_output_signatures(),"thresholds":THRESHOLDS,"note":"Immutable (Law 7)."}
    with open(BASELINE_FILE,"w") as f: json.dump(b,f,indent=2)
    return b

def load_baseline() -> dict:
    if not BASELINE_FILE.exists(): return {}
    with open(BASELINE_FILE) as f: return json.load(f)

def detect_drift() -> dict:
    baseline = load_baseline()
    if not baseline: return {"status":"no_baseline","message":"Run --baseline first.","drifts":[]}
    drifts = []
    cg, bg = compute_graph_signature(), baseline.get("graph_signature",{})
    if abs(cg["nodes"]-bg.get("nodes",0)) > THRESHOLDS["node_count_delta"]:
        drifts.append({"type":"graph_expansion","severity":"high","detail":f"Nodes: {bg.get('nodes',0)} -> {cg['nodes']}"})
    if abs(cg["edges"]-bg.get("edges",0)) > THRESHOLDS["edge_count_delta"]:
        drifts.append({"type":"graph_expansion","severity":"high","detail":f"Edges: {bg.get('edges',0)} -> {cg['edges']}"})
    if cg["hash"] != bg.get("hash",""):
        drifts.append({"type":"graph_content_change","severity":"medium","detail":"Graph hash changed"})
    co, bo = compute_output_signatures(), baseline.get("output_signatures",{})
    for bid,bs in bo.items():
        if bid not in co: drifts.append({"type":"output_missing","severity":"high","detail":f"{bid} missing"}); continue
        cs = co[bid]
        if set(bs.get("assumptions",[])) != set(cs.get("assumptions",[])):
            drifts.append({"type":"assumption_change","severity":"high","detail":f"Assumptions changed: {bid}"})
        if abs(cs.get("pcs",0)-bs.get("pcs",0)) > THRESHOLDS["prerequisite_delta"]:
            drifts.append({"type":"pcs_drift","severity":"medium","detail":f"PCS drift: {bid}"})
        if abs(cs.get("rps",0)-bs.get("rps",0)) > THRESHOLDS["resurrection_delta"]:
            drifts.append({"type":"rps_drift","severity":"medium","detail":f"RPS drift: {bid}"})
    report = {"timestamp":datetime.now(timezone.utc).isoformat(),"status":"drift_detected" if drifts else "stable",
        "total_drifts":len(drifts),"high":len([d for d in drifts if d["severity"]=="high"]),
        "medium":len([d for d in drifts if d["severity"]=="medium"]),
        "low":len([d for d in drifts if d["severity"]=="low"]),"drifts":drifts}
    with open(DRIFT_LOG,"a") as f: f.write(json.dumps({"ts":report["timestamp"],"status":report["status"],"n":report["total_drifts"]})+"\n")
    return report
