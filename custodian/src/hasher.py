"""
custodian.src.hasher — Cryptographic hashing for all custodian artifacts.

Uses SHA-256 for all hashes. Hashes are computed on canonical JSON
(canonicalized: sorted keys, no extra whitespace, UTF-8 encoded).

This module is the single source of truth for hashing in the custodian.
No other module should compute hashes directly.
"""
import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> bytes:
    """Serialize to canonical JSON: sorted keys, no extra whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    """Compute SHA-256 hex digest of canonical JSON serialization."""
    return sha256_bytes(canonical_json(obj))


def sha256_string(s: str) -> str:
    """Compute SHA-256 hex digest of a string (UTF-8 encoded)."""
    return sha256_bytes(s.encode('utf-8'))


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
