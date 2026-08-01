"""Benchmark Immutability Enforcement (Discipline 1, Law 7)."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS_DIR = ROOT / "benchmarks"
PATENT_INPUT_DIR = BENCHMARKS_DIR / "patents" / "input"
CONSUMER_INPUT_DIR = BENCHMARKS_DIR / "consumer" / "input"
CHECKSUM_FILE = BENCHMARKS_DIR / "checksums.json"

def compute_checksum(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def build_checksum_registry() -> Dict[str, str]:
    registry = {}
    for d in [PATENT_INPUT_DIR, CONSUMER_INPUT_DIR]:
        if not d.exists(): continue
        for f in sorted(d.glob("*.json")):
            registry[str(f.relative_to(ROOT))] = compute_checksum(f)
    return registry

def save_checksums(registry=None) -> Dict[str, str]:
    if registry is None: registry = build_checksum_registry()
    with open(CHECKSUM_FILE, "w") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "law": "Law 7", "checksums": registry}, f, indent=2)
    return registry

def load_checksums() -> Dict[str, str]:
    if not CHECKSUM_FILE.exists(): return {}
    with open(CHECKSUM_FILE) as f: return json.load(f).get("checksums", {})

def verify_integrity() -> Tuple[bool, List[str]]:
    stored = load_checksums()
    if not stored: return True, ["No registry. Run save_checksums() to init."]
    violations = []
    current = build_checksum_registry()
    for p, h in stored.items():
        if p not in current: violations.append(f"DELETED: {p}")
        elif current[p] != h: violations.append(f"MODIFIED: {p}")
    for p in current:
        if p not in stored: violations.append(f"NEW: {p}")
    return len([v for v in violations if not v.startswith("NEW:")]) == 0, violations

def validate_review_naming(filepath: Path) -> Tuple[bool, str]:
    name = filepath.stem
    for s in ["_v2","_new","_fixed","_final","_latest","_updated","_copy"]:
        if name.endswith(s): return False, f"Forbidden suffix {s}"
    return True, "OK"

def register_new_benchmark(filepath: Path) -> str:
    stored = load_checksums()
    rel = str(filepath.relative_to(ROOT))
    stored[rel] = compute_checksum(filepath)
    save_checksums(stored)
    return stored[rel]
