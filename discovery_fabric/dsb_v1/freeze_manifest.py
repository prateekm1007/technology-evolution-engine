"""
DSB V1 — FREEZE MANIFEST
=========================

This file declares DSB V1 artifacts FROZEN as of 2026-08-12.

FROZEN ARTIFACTS (must NOT be modified):
  - cases/real/DSB-R-*.json (10 real cases)
  - cases/fabricated/DSB-F-*.json (10 fabricated cases)
  - build_real_cases.py
  - build_fabricated_cases.py
  - payload_builder.py
  - leakage_audit.py
  - generator.py
  - receipts/RECEIPT-*.json (80 receipts — already hash-sealed)
  - scorer.py (FROZEN — must NOT be tuned on these 80 cases)
  - human_adjudication_packet.py
  - recomputation_check.py
  - adjudication/adjudication_packets_BLIND.json (80 blind packets)

POLICY:
  1. The 80 cases and prompts are FROZEN. No modifications.
  2. The scorer is FROZEN. No tuning on these 80 cases.
     If human adjudication reveals systematic false positives, a SEPARATE
     scorer-calibration set must be created (new cases, not these 80).
  3. E5 (human adjudication) is relabeled as PENDING_HUMAN_ADJUDICATION.
     It is NOT a PASS until human adjudication is complete.
  4. DSB V1 is NOT scientifically closed until:
     (a) Human adjudication is complete (2-3 independent expert adjudicators)
     (b) Scorer validity is established against humans
     (c) The fabricated-vs-real inversion is explained
  5. No temporal reasoning, negative knowledge, patent integration, or
     architecture redesign until DSB V1 is closed.

This file is itself hash-sealed. Any modification is detectable.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone


def build_freeze_manifest() -> dict:
    """Build the freeze manifest with hashes of all frozen artifacts."""
    REPO = Path(__file__).resolve().parents[2]
    dsb_dir = REPO / "discovery_fabric/dsb_v1"

    frozen_paths = [
        "case_schema.py",
        "build_real_cases.py",
        "build_fabricated_cases.py",
        "payload_builder.py",
        "leakage_audit.py",
        "generator.py",
        "scorer.py",
        "human_adjudication_packet.py",
        "recomputation_check.py",
        "run_dsb_v1.py",
    ]

    frozen_artifacts = {}
    for rel_path in frozen_paths:
        full_path = dsb_dir / rel_path
        if full_path.exists():
            h = hashlib.sha256(full_path.read_bytes()).hexdigest()
            frozen_artifacts[rel_path] = h

    # Hash all case files
    for case_dir in ["cases/real", "cases/fabricated"]:
        for case_path in sorted((dsb_dir / case_dir).glob("DSB-*.json")):
            rel = f"{case_dir}/{case_path.name}"
            h = hashlib.sha256(case_path.read_bytes()).hexdigest()
            frozen_artifacts[rel] = h

    # Hash all receipts
    receipts_dir = dsb_dir / "receipts"
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        rel = f"receipts/{rp.name}"
        h = hashlib.sha256(rp.read_bytes()).hexdigest()
        frozen_artifacts[rel] = h

    # Hash blind adjudication packets
    blind_path = dsb_dir / "adjudication/adjudication_packets_BLIND.json"
    if blind_path.exists():
        frozen_artifacts["adjudication/adjudication_packets_BLIND.json"] = \
            hashlib.sha256(blind_path.read_bytes()).hexdigest()

    manifest = {
        "schema_version": "1.0.0",
        "manifest_type": "DSB_V1_FREEZE",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "policy": [
            "The 80 cases and prompts are FROZEN. No modifications.",
            "The scorer is FROZEN. No tuning on these 80 cases.",
            "If human adjudication reveals systematic false positives, a SEPARATE scorer-calibration set must be created (new cases, not these 80).",
            "E5 (human adjudication) is PENDING_HUMAN_ADJUDICATION, not PASS.",
            "DSB V1 is NOT scientifically closed until human adjudication is complete, scorer validity is established, and fabricated-vs-real inversion is explained.",
            "No temporal reasoning, negative knowledge, patent integration, or architecture redesign until DSB V1 is closed.",
        ],
        "frozen_artifacts": frozen_artifacts,
        "n_frozen": len(frozen_artifacts),
    }

    # Seal
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return manifest


def verify_freeze(manifest: dict) -> tuple[bool, list[str]]:
    """Verify that all frozen artifacts are unchanged."""
    REPO = Path(__file__).resolve().parents[2]
    dsb_dir = REPO / "discovery_fabric/dsb_v1"
    failures = []
    for rel_path, expected_hash in manifest.get("frozen_artifacts", {}).items():
        full_path = dsb_dir / rel_path
        if not full_path.exists():
            failures.append(f"MISSING: {rel_path}")
            continue
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            failures.append(f"MODIFIED: {rel_path} (expected {expected_hash[:16]}, got {actual_hash[:16]})")
    return (len(failures) == 0, failures)


def main():
    manifest = build_freeze_manifest()
    out_path = Path(__file__).resolve().parent / "FREEZE_MANIFEST.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Freeze manifest saved: {out_path}")
    print(f"Frozen artifacts: {manifest['n_frozen']}")
    print(f"Manifest hash: {manifest['manifest_hash'][:32]}...")
    print()
    print("POLICY:")
    for p in manifest["policy"]:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
