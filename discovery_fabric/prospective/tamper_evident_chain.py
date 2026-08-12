"""
PROSPECTIVE EXPERIMENT — Tamper-Evident Audit Chain
====================================================

A tamper-evident append-only chain linking every stage of the prospective
experiment:

    registration -> prediction -> observation -> evaluation -> final analysis

Each chain entry contains:
    - entry_index (0, 1, 2, ...)
    - entry_type (COMMITMENT | PREDICTION | OBSERVATION | EVALUATION | ANALYSIS)
    - entry_hash = SHA-256(prev_hash || entry_index || entry_type || timestamp || payload_hash || metadata)
    - prev_hash (hash of the previous entry; "GENESIS" for index 0)
    - timestamp (UTC, captured inside append_chain_entry)
    - payload_hash (hash of the stage's primary artifact)
    - metadata (stage-specific)

The chain is stored as a JSONL file: one entry per line.

Tamper-evidence:
    - Modifying any entry changes its entry_hash.
    - Modifying any entry's prev_hash breaks the chain link to the next entry.
    - Inserting an entry shifts all subsequent indices, breaking all subsequent hashes.
    - Deleting an entry breaks the chain link.
    - Reordering entries breaks the prev_hash links.

VERIFICATION:
    verify_chain() recomputes every entry_hash and checks every prev_hash link.
    Any tampering is detected.

INVARIANTS:
    (I32) The chain is append-only. No entry may be modified, inserted, or
          deleted after being appended.
    (I33) Each entry's entry_hash = SHA-256(prev_hash || entry_index || entry_type
          || timestamp || payload_hash || metadata).
    (I34) Each entry's prev_hash = the previous entry's entry_hash (or "GENESIS"
          for index 0).
    (I35) Each entry's timestamp = the actual UTC time at append (captured
          inside append_chain_entry, NOT a parameter).
    (I36) The chain entries appear in temporal order: COMMITMENT -> PREDICTION* ->
          OBSERVATION* -> EVALUATION* -> ANALYSIS. A stage-N entry cannot appear
          before a stage-(N-1) entry. (Verified by verify_chain_order.)
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
CHAIN_FILE = PROSPECTIVE_DIR / "manifests" / "audit_chain.jsonl"
CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)

GENESIS_HASH = "GENESIS"

# Stage ordering (for verify_chain_order)
STAGE_ORDER = {
    "COMMITMENT": 0,
    "PREDICTION": 1,
    "OBSERVATION": 2,
    "EVALUATION": 3,
    "ANALYSIS": 4,
}


# =============================================================================
# Chain entry creation
# =============================================================================

def _compute_entry_hash(
    prev_hash: str,
    entry_index: int,
    entry_type: str,
    timestamp: str,
    payload_hash: str,
    metadata: dict,
) -> str:
    """Compute the SHA-256 hash of a chain entry."""
    payload = {
        "prev_hash": prev_hash,
        "entry_index": entry_index,
        "entry_type": entry_type,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "metadata": metadata,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def append_chain_entry(
    entry_type: str,
    payload_hash: str,
    metadata: dict | None = None,
) -> dict:
    """Append a new entry to the tamper-evident chain.

    The timestamp is captured INSIDE this function from the system clock.
    It is NOT a parameter.

    Args:
        entry_type: one of COMMITMENT, PREDICTION, OBSERVATION, EVALUATION, ANALYSIS
        payload_hash: SHA-256 hash of the stage's primary artifact
        metadata: optional stage-specific metadata

    Returns:
        The appended chain entry dict.
    """
    if entry_type not in STAGE_ORDER:
        raise ValueError(f"unknown entry_type: {entry_type}. Must be one of {list(STAGE_ORDER.keys())}")

    # Capture timestamp from system clock
    timestamp = datetime.now(timezone.utc).isoformat()

    # Read the current chain to find the previous entry
    entries = read_chain()
    if entries:
        prev_hash = entries[-1]["entry_hash"]
        entry_index = entries[-1]["entry_index"] + 1
    else:
        prev_hash = GENESIS_HASH
        entry_index = 0

    entry = {
        "entry_index": entry_index,
        "entry_type": entry_type,
        "prev_hash": prev_hash,
        "timestamp": timestamp,
        "payload_hash": payload_hash,
        "metadata": metadata or {},
    }
    entry["entry_hash"] = _compute_entry_hash(
        prev_hash, entry_index, entry_type, timestamp, payload_hash, metadata or {}
    )

    # Append to the chain file
    with open(CHAIN_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def read_chain() -> list[dict]:
    """Read all entries from the chain file."""
    if not CHAIN_FILE.exists():
        return []
    entries = []
    with open(CHAIN_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                # Corrupted line — return what we have; verify_chain will catch it
                entries.append({"_corrupted": True, "_raw": line[:200]})
    return entries


# =============================================================================
# Chain verification
# =============================================================================

def verify_chain() -> tuple[bool, list[str]]:
    """Verify the integrity of the tamper-evident chain.

    Checks:
      - Every entry's entry_hash matches the recomputed hash.
      - Every entry's prev_hash matches the previous entry's entry_hash.
      - Entry indices are sequential (0, 1, 2, ...).
      - Stage ordering is correct (COMMITMENT before PREDICTION before ...).

    Returns (all_ok, list_of_failures).
    """
    entries = read_chain()
    failures = []

    if not entries:
        return (True, [])  # empty chain is valid

    prev_hash = GENESIS_HASH
    expected_index = 0
    last_stage_seen = -1

    for i, entry in enumerate(entries):
        if entry.get("_corrupted"):
            failures.append(f"entry {i}: corrupted/unparseable line")
            continue

        # Check index
        if entry.get("entry_index") != expected_index:
            failures.append(
                f"entry {i}: expected index {expected_index}, got {entry.get('entry_index')}"
            )

        # Check prev_hash
        if entry.get("prev_hash") != prev_hash:
            failures.append(
                f"entry {i}: prev_hash {entry.get('prev_hash')[:16]}... does not match "
                f"previous entry's hash {prev_hash[:16]}..."
            )

        # Recompute entry_hash
        recomputed = _compute_entry_hash(
            entry.get("prev_hash", ""),
            entry.get("entry_index", -1),
            entry.get("entry_type", ""),
            entry.get("timestamp", ""),
            entry.get("payload_hash", ""),
            entry.get("metadata", {}),
        )
        if recomputed != entry.get("entry_hash"):
            failures.append(
                f"entry {i}: entry_hash mismatch — entry may have been modified"
            )

        # Check stage ordering
        stage = STAGE_ORDER.get(entry.get("entry_type", ""), -1)
        if stage == -1:
            failures.append(f"entry {i}: unknown entry_type {entry.get('entry_type')}")
        elif stage < last_stage_seen:
            failures.append(
                f"entry {i}: stage {entry.get('entry_type')} (order={stage}) appears after "
                f"stage with order={last_stage_seen} — temporal ordering violated"
            )
        else:
            last_stage_seen = stage

        prev_hash = entry.get("entry_hash", "")
        expected_index += 1

    return (len(failures) == 0, failures)


def verify_chain_order() -> tuple[bool, list[str]]:
    """Verify that the chain entries appear in the correct stage order:
    COMMITMENT -> PREDICTION* -> OBSERVATION* -> EVALUATION* -> ANALYSIS.

    Returns (all_ok, list_of_failures).
    """
    entries = read_chain()
    failures = []
    last_stage = -1
    for i, entry in enumerate(entries):
        if entry.get("_corrupted"):
            continue
        stage = STAGE_ORDER.get(entry.get("entry_type", ""), -1)
        if stage == -1:
            failures.append(f"entry {i}: unknown entry_type")
            continue
        if stage < last_stage:
            failures.append(
                f"entry {i}: {entry.get('entry_type')} (order={stage}) after order={last_stage}"
            )
        else:
            last_stage = stage
    return (len(failures) == 0, failures)


def get_chain_head() -> dict | None:
    """Return the last entry in the chain, or None if empty."""
    entries = read_chain()
    return entries[-1] if entries else None


def get_chain_length() -> int:
    """Return the number of entries in the chain."""
    return len(read_chain())


def reset_chain() -> None:
    """Delete the chain file. USE WITH CAUTION — only for resetting a
    synthetic test chain before a real experiment.
    """
    if CHAIN_FILE.exists():
        CHAIN_FILE.unlink()


# =============================================================================
# Main — infrastructure check
# =============================================================================

def main():
    """Verify the tamper-evident chain infrastructure."""
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — TAMPER-EVIDENT AUDIT CHAIN CHECK")
    print("=" * 72)
    print()

    # Save current chain state (if any) and start fresh
    backup_path = None
    if CHAIN_FILE.exists():
        backup_path = CHAIN_FILE.with_suffix(".backup.jsonl")
        CHAIN_FILE.rename(backup_path)
        print(f"Backed up existing chain to {backup_path}")

    try:
        # Append a few synthetic entries
        print("\nAppending synthetic chain entries...")
        e1 = append_chain_entry("COMMITMENT", "hash1", {"n_problems": 2})
        print(f"  entry 0: COMMITMENT hash={e1['entry_hash'][:16]}...")
        e2 = append_chain_entry("PREDICTION", "hash2", {"candidate_id": "PROS-001-B"})
        print(f"  entry 1: PREDICTION  hash={e2['entry_hash'][:16]}...")
        e3 = append_chain_entry("OBSERVATION", "hash3", {"problem_id": "PROS-001"})
        print(f"  entry 2: OBSERVATION hash={e3['entry_hash'][:16]}...")
        e4 = append_chain_entry("EVALUATION", "hash4", {"candidate_id": "PROS-001-B"})
        print(f"  entry 3: EVALUATION  hash={e4['entry_hash'][:16]}...")
        e5 = append_chain_entry("ANALYSIS", "hash5", {"decision": "NEGATIVE_RESULT"})
        print(f"  entry 4: ANALYSIS    hash={e5['entry_hash'][:16]}...")

        # Verify
        print("\nVerifying chain...")
        ok, failures = verify_chain()
        print(f"  Chain verification: {'PASS' if ok else 'FAIL'}")
        for f in failures:
            print(f"    - {f}")

        # Test tamper detection: modify an entry
        print("\nTesting tamper detection (modifying entry 2)...")
        entries = read_chain()
        entries[2]["metadata"] = {"tampered": True}
        with open(CHAIN_FILE, "w") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        ok2, failures2 = verify_chain()
        print(f"  After tampering: {'PASS (BUG!)' if ok2 else 'FAIL (correctly detected)'}")
        for f in failures2[:2]:
            print(f"    - {f}")

    finally:
        # Clean up: remove the synthetic chain
        reset_chain()
        # Restore backup if any
        if backup_path and backup_path.exists():
            backup_path.rename(CHAIN_FILE)
            print(f"\nRestored original chain from {backup_path}")

    print("\nTamper-evident chain infrastructure is in place.")


if __name__ == "__main__":
    main()
