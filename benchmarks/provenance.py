"""Benchmark Provenance Enforcement (Discipline 2, Law 7)."""
import json
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = ROOT / "benchmarks"
REQUIRED = ["id","type","source","domain","created_at","reviewer","version","assumptions","limitations"]
VALID_DOMAINS = {"energy","water","sensors","computation","transportation","medicine","agriculture"}

def validate_provenance(b: dict) -> Tuple[bool, List[str]]:
    issues = []
    for f in REQUIRED:
        if f not in b: issues.append(f"MISSING: {f}")
        elif b[f] is None: issues.append(f"NULL: {f}")
        elif f in ("assumptions","limitations") and not isinstance(b[f], list): issues.append(f"BAD TYPE: {f}")
        elif f not in ("assumptions","limitations") and (not isinstance(b[f], str) or not b[f].strip()): issues.append(f"EMPTY: {f}")
    if b.get("type") not in ("patent","consumer",None): issues.append("BAD TYPE VALUE")
    if b.get("domain") and b["domain"] not in VALID_DOMAINS: issues.append(f"BAD DOMAIN: {b.get('domain')}")
    return len(issues)==0, issues

def add_provenance(b: dict) -> dict:
    defaults = {"created_at":"2026-08-01T00:00:00Z","reviewer":"unreviewed","version":"1.0",
        "assumptions":["Benchmark constructed from public domain knowledge","Expected values are expert estimates","Scoring is rule-based"],
        "limitations":["Single-domain benchmark","No expert validation yet","Expected values may be incomplete"]}
    for k,v in defaults.items():
        if k not in b: b[k] = v
    return b

def validate_all_benchmarks() -> Dict[str, List[str]]:
    results = {}
    for d in [BENCHMARKS_DIR/"patents"/"input", BENCHMARKS_DIR/"consumer"/"input"]:
        if not d.exists(): continue
        for f in sorted(d.glob("*.json")):
            with open(f) as fh: b = json.load(fh)
            ok, issues = validate_provenance(b)
            if issues: results[b.get("id", f.stem)] = issues
    return results
