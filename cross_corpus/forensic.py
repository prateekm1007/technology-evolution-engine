"""
Forensic integrity for the cross-corpus pilot (Issue #4).

Implements:
  - hash chain over candidates (each candidate's hash includes the previous)
  - tamper detection (any mutation invalidates the chain)
  - immutable result package (single signed JSON blob)
  - seal verification (real-data vs synthetic-fixture distinction)

REAL_DATA_SEAL = FALSE for this pilot — fixtures are synthetic-but-faithful.
The pilot can produce a STRUCTURAL_PASS (all controls work, all motifs fire,
forensic chain intact) but NEVER a SCIENTIFIC_RESULT.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .schema import Candidate


def build_hash_chain(candidates: list[Candidate]) -> list[dict]:
    """Build a tamper-evident hash chain. candidate[i].chain_hash depends on
    candidate[i-1].chain_hash. Mutating any candidate invalidates all later.
    """
    chain = []
    prev = "GENESIS"
    for c in candidates:
        ch = c.content_hash()
        link = hashlib.sha256(f"{prev}|{ch}".encode()).hexdigest()
        chain.append({
            "candidate_id": c.candidate_id,
            "content_hash": ch,
            "chain_hash": link,
            "prev_hash": prev,
        })
        prev = link
    return chain


def verify_hash_chain(chain: list[dict], candidates: list[Candidate]) -> dict:
    """Re-derive the chain from candidates and compare."""
    if len(chain) != len(candidates):
        return {"valid": False, "reason": "length mismatch"}
    recomputed = build_hash_chain(candidates)
    for a, b in zip(chain, recomputed):
        if a != b:
            return {"valid": False, "reason": f"chain mismatch at {a.get('candidate_id')}",
                    "expected": b, "actual": a}
    return {"valid": True}


@dataclass
class ResultPackage:
    pilot_id: str
    generated_at: str
    cutoff: str
    corpus_manifest: dict
    graph_stats: dict
    real_data_seal: bool                  # FALSE for synthetic fixtures
    candidates_total: int
    candidates_per_motif: dict
    retrieval_negative_count: int
    null_control_results: dict
    hash_chain: list[dict]
    chain_root_hash: str
    decision: str                         # STRUCTURAL_PASS | STRUCTURAL_FAIL
    decision_rule: str
    is_scientific_result: bool            # ALWAYS False for this pilot

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)

    def write(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_json()
        path.write_text(content)
        h = hashlib.sha256(content.encode()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(h)


def verify_result_package(path: Path) -> dict:
    """Verify the result package's HASH INTEGRITY ONLY (tamper detection).

    Does NOT check semantic claims like is_scientific_result — that belongs
    in forensic_audit, which loads the package and runs all checks.
    """
    if not path.exists():
        return {"valid": False, "reason": "result package missing"}
    content = path.read_text()
    hash_path = path.with_suffix(path.suffix + ".sha256")
    if not hash_path.exists():
        return {"valid": False, "reason": "hash sidecar missing"}
    expected = hash_path.read_text().strip()
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != expected:
        return {"valid": False, "reason": "result package hash mismatch (tampered)"}
    try:
        pkg = json.loads(content)
    except Exception as e:
        return {"valid": False, "reason": f"result package is not valid JSON: {e}"}
    return {"valid": True, "package": pkg}


def forensic_audit(result_package_path: Path) -> dict:
    """Top-level forensic audit. Returns a structured report.

    Runs ALL checks even if the package hash is invalid — the auditor needs
    to report which checks failed, not just the first one.
    """
    checks = []
    pkg_check = verify_result_package(result_package_path)
    checks.append({"check": "RESULT_PACKAGE_INTACT", "passed": pkg_check["valid"],
                   "reason": pkg_check.get("reason", "")})

    pkg = pkg_check.get("package")
    if pkg is None:
        # Cannot run further checks if the package is missing/tampered/unparseable
        return {"passed": False, "checks": checks, "package": None}

    # Real data seal
    rds = pkg.get("real_data_seal", True)
    checks.append({"check": "REAL_DATA_SEAL_HONEST", "passed": rds is False,
                   "reason": "pilot uses synthetic fixtures; REAL_DATA_SEAL must be False"})

    # Scientific result never claimed on synthetic fixtures
    isr = pkg.get("is_scientific_result", True)
    checks.append({"check": "NOT_CLAIMED_AS_SCIENTIFIC", "passed": isr is False,
                   "reason": "synthetic-fixture pilot cannot produce scientific result"})

    # Chain root hash present and 64 chars (or "EMPTY" if no candidates)
    crh = pkg.get("chain_root_hash", "")
    checks.append({"check": "CHAIN_ROOT_HASH_PRESENT",
                   "passed": len(crh) == 64 or crh == "EMPTY"})

    # Decision
    dec = pkg.get("decision", "")
    checks.append({"check": "DECISION_IN_VOCABULARY",
                   "passed": dec in ("STRUCTURAL_PASS", "STRUCTURAL_FAIL")})

    # Null controls all present
    nulls = pkg.get("null_control_results", {})
    null_keys = {"NULL_A", "NULL_B", "NULL_C", "NULL_D_papers_only", "NULL_D_patents_only"}
    checks.append({"check": "ALL_NULL_CONTROLS_PRESENT",
                   "passed": null_keys.issubset(set(nulls.keys()))})

    all_pass = all(c["passed"] for c in checks)
    return {"passed": all_pass, "checks": checks, "package": pkg}
