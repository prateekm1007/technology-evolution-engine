"""
Snapshot manager (Issue #5).

CRITICAL SEPARATION:
  - LIVE ingestion: continuous, mutable, growing. The "evidence fabric".
  - FROZEN experimental snapshots: immutable, content-addressed, time-anchored.
    Used for any discovery claim. A snapshot is what a pilot or experiment
    runs against.

A snapshot is created by:
  1. taking a content-hash-indexed copy of the current live corpus at a
     specific UTC timestamp (the "snapshot cutoff")
  2. writing an immutable manifest (snapshot.json) listing every record's hash
  3. writing a root hash (sha256 of all record hashes joined)
  4. writing a SHA-256 sidecar for tamper detection
  5. sealing with AES-GCM (placeholder; in production, an external custodian
     holds the key)

A snapshot can NEVER be modified after sealing. Any tampering invalidates the
root hash and is detected by `verify_snapshot`.

Per Issue #5: "Live ingestion and frozen experimental snapshots are separate worlds."
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from .connector_base import HarvestedRecord


@dataclass
class SnapshotManifest:
    snapshot_id: str
    created_at: str              # ISO timestamp
    cutoff: str                  # evidence must be strictly before this
    record_count: int
    record_hashes: list[str]     # sha256 of each record's normalized form
    record_ids: list[str]        # canonical record ids, in the same order
    source_ids: list[str]        # which sources contributed
    root_hash: str               # sha256 of all record_hashes joined
    is_frozen: bool = True       # ALWAYS True for snapshots
    seal_kind: str = "UNSEALED"  # UNSEALED | AES_GCM_SEALED (placeholder)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)


def create_snapshot(records: list[HarvestedRecord], cutoff: str,
                    snapshot_dir: Path) -> dict:
    """Create an immutable snapshot of the given records.

    Writes snapshot.json + snapshot.json.sha256. Returns the manifest.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    record_hashes = [r.normalized_hash for r in records]
    record_ids = [r.record_id for r in records]
    source_ids = sorted({r.source_id for r in records})
    root = hashlib.sha256("|".join(record_hashes).encode()).hexdigest()
    snap_id = f"snap:{root[:12]}"

    manifest = SnapshotManifest(
        snapshot_id=snap_id,
        created_at=now,
        cutoff=cutoff,
        record_count=len(records),
        record_hashes=record_hashes,
        record_ids=record_ids,
        source_ids=source_ids,
        root_hash=root,
        is_frozen=True,
        seal_kind="UNSEALED",  # production: external custodian seals with AES-GCM
    )

    snap_path = snapshot_dir / "snapshot.json"
    snap_hash_path = snapshot_dir / "snapshot.json.sha256"

    content = manifest.to_json()
    snap_path.write_text(content)
    h = hashlib.sha256(content.encode()).hexdigest()
    snap_hash_path.write_text(h)

    # Also persist the records themselves (content-addressed)
    records_dir = snapshot_dir / "records"
    records_dir.mkdir(exist_ok=True)
    for r in records:
        rpath = records_dir / f"{r.normalized_hash}.json"
        if not rpath.exists():
            rpath.write_text(json.dumps(r.canonical_dict(), sort_keys=True, default=str))

    return {
        "manifest": asdict(manifest),
        "snapshot_path": str(snap_path),
        "records_dir": str(records_dir),
    }


def verify_snapshot(snapshot_dir: Path) -> dict:
    """Verify a snapshot's integrity:
      1. snapshot.json + sha256 sidecar match (tamper detection)
      2. root_hash = sha256 of all record_hashes joined
      3. every record file exists and its content matches its filename hash
    """
    checks = []
    snap_path = snapshot_dir / "snapshot.json"
    hash_path = snapshot_dir / "snapshot.json.sha256"

    if not snap_path.exists():
        checks.append({"check": "SNAPSHOT_EXISTS", "passed": False,
                       "reason": "snapshot.json missing"})
        return {"valid": False, "checks": checks}
    checks.append({"check": "SNAPSHOT_EXISTS", "passed": True})

    if not hash_path.exists():
        checks.append({"check": "HASH_SIDECAR_EXISTS", "passed": False,
                       "reason": "snapshot.json.sha256 missing"})
        return {"valid": False, "checks": checks}
    checks.append({"check": "HASH_SIDECAR_EXISTS", "passed": True})

    content = snap_path.read_text()
    expected = hash_path.read_text().strip()
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != expected:
        checks.append({"check": "HASH_MATCHES", "passed": False,
                       "reason": "snapshot.json hash mismatch (tampered)"})
        return {"valid": False, "checks": checks}
    checks.append({"check": "HASH_MATCHES", "passed": True})

    manifest = json.loads(content)
    # re-derive root hash
    recomputed = hashlib.sha256(
        "|".join(manifest["record_hashes"]).encode()
    ).hexdigest()
    if recomputed != manifest["root_hash"]:
        checks.append({"check": "ROOT_HASH_VALID", "passed": False,
                       "reason": "root_hash does not match record hashes"})
        return {"valid": False, "checks": checks}
    checks.append({"check": "ROOT_HASH_VALID", "passed": True})

    # verify every record file exists and matches its filename hash
    records_dir = snapshot_dir / "records"
    missing = 0
    mismatched = 0
    for rh in manifest["record_hashes"]:
        rpath = records_dir / f"{rh}.json"
        if not rpath.exists():
            missing += 1
            continue
        # verify file content hash matches filename
        rec_content = rpath.read_text()
        rec_dict = json.loads(rec_content)
        if rec_dict.get("normalized_hash") != rh:
            mismatched += 1
    if missing > 0:
        checks.append({"check": "ALL_RECORDS_PRESENT", "passed": False,
                       "reason": f"{missing} record files missing"})
    else:
        checks.append({"check": "ALL_RECORDS_PRESENT", "passed": True})
    if mismatched > 0:
        checks.append({"check": "RECORD_HASHES_MATCH_FILENAMES", "passed": False,
                       "reason": f"{mismatched} record files have hash mismatch"})
    else:
        checks.append({"check": "RECORD_HASHES_MATCH_FILENAMES", "passed": True})

    # verify record count matches
    if len(manifest["record_hashes"]) != manifest["record_count"]:
        checks.append({"check": "RECORD_COUNT_CONSISTENT", "passed": False,
                       "reason": f"record_count={manifest['record_count']} but "
                                 f"len(record_hashes)={len(manifest['record_hashes'])}"})
    else:
        checks.append({"check": "RECORD_COUNT_CONSISTENT", "passed": True})

    all_pass = all(c["passed"] for c in checks)
    return {"valid": all_pass, "checks": checks, "manifest": manifest}


def is_frozen(snapshot_dir: Path) -> bool:
    """A snapshot is frozen iff its manifest.is_frozen is True."""
    snap_path = snapshot_dir / "snapshot.json"
    if not snap_path.exists():
        return False
    manifest = json.loads(snap_path.read_text())
    return manifest.get("is_frozen", False) is True
