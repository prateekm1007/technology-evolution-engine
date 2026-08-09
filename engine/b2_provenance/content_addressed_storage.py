#!/usr/bin/env python3
"""b2_provenance/content_addressed_storage.py — Content-addressed raw-output storage.

Per B2_REVISION_R5_1.md (FATAL 2 fix) and B2_IMPLEMENTATION_INVARIANTS.md:

    Raw output is written to content-addressed storage:
        path = provenance/raw_outputs/{raw_output_sha256}.txt

    The filename IS the SHA-256. If the content changes, the path changes.
    The blob is committed to git BEFORE adjudication.

This module provides:
    - store_raw_output(case_id, arm, raw_output) -> blob_path, sha256
    - retrieve_raw_output(sha256) -> raw_output bytes
    - verify_blob_integrity(sha256) -> bool

This is the first component of the provenance spine:
    raw output → content-addressed blob → frozen parser → candidate(rank) →
    candidate SHA → derivation verification → append-only ledger → adjudication
"""
import hashlib
import os
from pathlib import Path
from typing import Optional


# The storage root is under the repo's provenance/ directory.
# This is committed to git, so blobs are version-controlled.
REPO_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = REPO_ROOT / "provenance" / "raw_outputs"


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def store_raw_output(case_id: str, arm: str, raw_output: str) -> tuple:
    """Store raw output in content-addressed storage.

    The raw output is written to:
        provenance/raw_outputs/{sha256}.txt

    The filename IS the SHA-256 of the content. If the content changes,
    the path changes. This makes tampering detectable.

    Args:
        case_id: e.g., "CASE-001"
        arm: e.g., "engine" or "null"
        raw_output: the raw output string from the engine/null

    Returns:
        (blob_path, sha256) where blob_path is the absolute path
        and sha256 is the content hash.

    Raises:
        ValueError: if raw_output is empty.
    """
    if not raw_output:
        raise ValueError(
            f"Cannot store empty raw output for case={case_id}, arm={arm}"
        )

    # Encode to UTF-8 bytes.
    raw_bytes = raw_output.encode("utf-8")
    sha256 = compute_sha256(raw_bytes)

    # Content-addressed path: the filename IS the hash.
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    blob_path = STORAGE_ROOT / f"{sha256}.txt"

    # Check if blob already exists (content-addressed deduplication).
    if blob_path.exists():
        # Verify the existing blob matches (defensive).
        existing_bytes = blob_path.read_bytes()
        if compute_sha256(existing_bytes) != sha256:
            raise RuntimeError(
                f"Blob path collision: {blob_path} exists but content "
                f"hash does not match. This should never happen with "
                f"content-addressed storage."
            )
        # Blob already stored — this is fine (deduplication).
    else:
        # Write the blob.
        blob_path.write_bytes(raw_bytes)
        # Verify write integrity.
        written_bytes = blob_path.read_bytes()
        if compute_sha256(written_bytes) != sha256:
            raise RuntimeError(
                f"Write integrity check failed for {blob_path}. "
                f"The blob was not written correctly."
            )

    return str(blob_path), sha256


def retrieve_raw_output(sha256: str) -> Optional[bytes]:
    """Retrieve raw output from content-addressed storage by SHA-256.

    Args:
        sha256: the content hash

    Returns:
        The raw output bytes, or None if not found.

    Raises:
        RuntimeError: if the blob exists but its hash does not match
            the requested sha256 (tampering detected).
    """
    blob_path = STORAGE_ROOT / f"{sha256}.txt"
    if not blob_path.exists():
        return None

    # Read and verify integrity.
    blob_bytes = blob_path.read_bytes()
    actual_sha256 = compute_sha256(blob_bytes)
    if actual_sha256 != sha256:
        raise RuntimeError(
            f"TAMPERING DETECTED: blob at {blob_path} has hash "
            f"{actual_sha256} but was expected to have {sha256}. "
            f"The raw output has been modified after storage."
        )

    return blob_bytes


def verify_blob_integrity(sha256: str) -> bool:
    """Verify that a blob exists and its content matches its hash.

    Args:
        sha256: the content hash

    Returns:
        True if the blob exists and is integrity-verified.
        False if the blob does not exist.

    Raises:
        RuntimeError: if the blob exists but its hash does not match
            (tampering detected).
    """
    blob_path = STORAGE_ROOT / f"{sha256}.txt"
    if not blob_path.exists():
        return False

    blob_bytes = blob_path.read_bytes()
    actual_sha256 = compute_sha256(blob_bytes)
    if actual_sha256 != sha256:
        raise RuntimeError(
            f"TAMPERING DETECTED: blob at {blob_path} has hash "
            f"{actual_sha256} but was expected to have {sha256}."
        )

    return True


def blob_exists(sha256: str) -> bool:
    """Check if a blob exists in storage (without verifying integrity)."""
    return (STORAGE_ROOT / f"{sha256}.txt").exists()


def list_all_blobs() -> list:
    """List all stored blobs (for audit purposes).

    Returns:
        List of (sha256, size_bytes) tuples.
    """
    if not STORAGE_ROOT.exists():
        return []
    blobs = []
    for path in sorted(STORAGE_ROOT.iterdir()):
        if path.is_file() and path.name.endswith(".txt"):
            sha256 = path.stem
            size = path.stat().st_size
            blobs.append((sha256, size))
    return blobs
