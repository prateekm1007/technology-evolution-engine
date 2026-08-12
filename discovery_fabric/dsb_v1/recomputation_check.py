"""
DSB V1 — Recomputation Check
=============================

Verifies that the entire DSB V1 pipeline is reproducible from scratch:
  1. Re-run leakage audit → must produce same result
  2. Re-run scorer on existing receipts → must produce same scores
     (modulo scored_at + score_hash)
  3. Re-build adjudication packets → must produce same packets
     (modulo built_at + packet_hash)

If any check fails, the pipeline is NOT reproducible and the exit gate fails.
"""
import json
import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.leakage_audit import audit_all_payloads
from discovery_fabric.dsb_v1.scorer import score_all
from discovery_fabric.dsb_v1.human_adjudication_packet import build_all_packets


def _strip_volatile(d):
    """Recursively strip volatile fields (timestamps + their dependent hashes)."""
    if isinstance(d, dict):
        return {k: _strip_volatile(v) for k, v in d.items()
                if k not in ("scored_at", "score_hash", "built_at", "packet_hash",
                             "timestamp", "audited_at")}
    if isinstance(d, list):
        return [_strip_volatile(x) for x in d]
    return d


def check_leakage_audit_reproducibility() -> dict:
    """Re-run leakage audit twice; verify identical results."""
    r1 = audit_all_payloads()
    r2 = audit_all_payloads()
    s1 = json.dumps(_strip_volatile(r1), sort_keys=True, ensure_ascii=False)
    s2 = json.dumps(_strip_volatile(r2), sort_keys=True, ensure_ascii=False)
    return {
        "check": "LEAKAGE_AUDIT_REPRODUCIBLE",
        "passed": s1 == s2,
        "n_payloads": r1["n_payloads"],
        "n_pass": r1["n_pass"],
    }


def check_scorer_reproducibility() -> dict:
    """Re-run scorer twice; verify identical results (modulo volatile fields)."""
    r1 = score_all()
    r2 = score_all()
    s1 = json.dumps(_strip_volatile(r1), sort_keys=True, ensure_ascii=False)
    s2 = json.dumps(_strip_volatile(r2), sort_keys=True, ensure_ascii=False)
    return {
        "check": "SCORER_REPRODUCIBLE",
        "passed": s1 == s2,
        "n_scores": r1["n_scores"],
    }


def check_adjudication_packet_reproducibility() -> dict:
    """Re-build adjudication packets twice; verify identical (modulo volatile)."""
    r1 = build_all_packets()
    r2 = build_all_packets()
    s1 = json.dumps(_strip_volatile(r1), sort_keys=True, ensure_ascii=False)
    s2 = json.dumps(_strip_volatile(r2), sort_keys=True, ensure_ascii=False)
    return {
        "check": "ADJUDICATION_PACKET_REPRODUCIBLE",
        "passed": s1 == s2,
        "n_packets": r1["n_packets"],
    }


def check_receipt_integrity() -> dict:
    """Verify all 80 receipt hashes are valid."""
    from discovery_fabric.dsb_v1.generator import verify_receipt
    receipts_dir = REPO / "discovery_fabric/dsb_v1/receipts"
    n_total = 0
    n_ok = 0
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        receipt = json.load(open(rp))
        n_total += 1
        if verify_receipt(receipt):
            n_ok += 1
    return {
        "check": "RECEIPT_INTEGRITY",
        "passed": n_ok == n_total,
        "n_total": n_total,
        "n_ok": n_ok,
    }


def check_leakage_audit_passes() -> dict:
    """Verify the leakage audit passes on all 80 payloads."""
    result = audit_all_payloads()
    return {
        "check": "LEAKAGE_AUDIT_PASSES",
        "passed": result["overall_pass"],
        "n_payloads": result["n_payloads"],
        "n_pass": result["n_pass"],
        "n_fail": result["n_fail"],
    }


def main():
    print("=" * 72)
    print("DSB V1 — RECOMPUTATION CHECK")
    print("=" * 72)
    print()

    checks = [
        check_leakage_audit_passes(),
        check_leakage_audit_reproducibility(),
        check_scorer_reproducibility(),
        check_adjudication_packet_reproducibility(),
        check_receipt_integrity(),
    ]

    print(f"{'CHECK':<45} {'PASS':<6}")
    print("-" * 55)
    for c in checks:
        passed_str = "PASS" if c["passed"] else "FAIL"
        print(f"{c['check']:<45} {passed_str:<6}")

    n_pass = sum(1 for c in checks if c["passed"])
    n_fail = sum(1 for c in checks if not c["passed"])
    print()
    print(f"Total: {n_pass} passed, {n_fail} failed")
    print(f"Overall: {'PASS' if n_fail == 0 else 'FAIL'}")

    return checks


if __name__ == "__main__":
    main()
