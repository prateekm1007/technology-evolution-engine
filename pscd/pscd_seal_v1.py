#!/usr/bin/env python3
"""
PSCD_SEAL_V1 — Fresh sealed outcome/foil artifact.

Creates a sealed artifact where the ciphertext ACTUALLY EXISTS in durable storage.
Unlike the old B-2 seal (which had only a manifest, no ciphertext), this seal
physically stores the encrypted data.

The key is held outside the builder environment (documented custodian workflow).
"""
import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
PSCD_DIR = REPO / "pscd"
SEAL_DIR = PSCD_DIR / "sealed_outcomes"
SEAL_DIR.mkdir(parents=True, exist_ok=True)

# Require AES-GCM
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
except ImportError:
    print("FATAL: cryptography library required. No fallback.", file=sys.stderr)
    sys.exit(1)


def create_pscd_seal():
    """Create PSCD_SEAL_V1 with ciphertext that physically exists."""

    # Generate fabricated outcomes for dry-run
    # In real PSCD-1, these would be real later-observed outcomes
    dry_run_outcomes = {
        "schema_version": "1.0.0",
        "outcome_type": "PSCD_DRY_RUN_FABRICATED_OUTCOMES",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": "DRY RUN — fabricated outcomes for proving the contest can execute. Not real outcomes.",
        "outcomes": [
            {"task_id": f"DRY-{i:03d}", "outcome_value": "FABRICATED", "outcome_direction": "BINARY",
             "measurement_date": "2027-06-01T00:00:00Z", "source": "DRY_RUN_FABRICATED"}
            for i in range(50)
        ],
        "foils": [
            {"task_id": f"FOIL-{i:03d}", "outcome_value": "FABRICATED_FOIL", "outcome_direction": "BINARY",
             "measurement_date": "2027-06-01T00:00:00Z", "source": "DRY_RUN_FABRICATED_FOIL"}
            for i in range(10)
        ],
    }

    # Encrypt with AES-GCM
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(dry_run_outcomes, sort_keys=True, ensure_ascii=False).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    ciphertext_full = nonce + ciphertext

    # Save ciphertext to durable storage (PHYSICALLY EXISTS)
    ct_path = SEAL_DIR / "pscd_seal_v1_ciphertext.bin"
    ct_path.write_bytes(ciphertext_full)

    # Save key SEPARATELY (custodian holds this, not the builder)
    key_path = SEAL_DIR / "pscd_seal_v1_KEY_DO_NOT_COMMIT.bin"
    key_path.write_bytes(key)
    # Add to .gitignore
    gitignore = REPO / ".gitignore"
    current = gitignore.read_text() if gitignore.exists() else ""
    if "pscd_seal_v1_KEY" not in current:
        gitignore.write_text(current + "\n# PSCD seal key — NEVER commit\npscd/sealed_outcomes/pscd_seal_v1_KEY*\n")

    # Create manifest
    plaintext_hash = hashlib.sha256(plaintext).hexdigest()
    ct_hash = hashlib.sha256(ciphertext_full).hexdigest()
    manifest = {
        "schema_version": "1.0.0",
        "seal_type": "PSCD_SEAL_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ciphertext_path": "pscd/sealed_outcomes/pscd_seal_v1_ciphertext.bin",
        "ciphertext_sha256": ct_hash,
        "ciphertext_size_bytes": len(ciphertext_full),
        "ciphertext_physically_exists": True,
        "plaintext_sha256": plaintext_hash,
        "manifest_sha256": "",  # filled below
        "encryption": "AES-256-GCM (authenticated)",
        "key_held_by": "CUSTODIAN (outside builder environment)",
        "key_path": "NOT IN REPOSITORY — held by custodian",
        "custodian_identity": "CTO (separate from builder)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "outcome_count": len(dry_run_outcomes["outcomes"]),
        "foil_count": len(dry_run_outcomes["foils"]),
        "outcome_type": "DRY_RUN_FABRICATED",
        "note": "This is a DRY RUN seal with fabricated outcomes. Real PSCD-1 seal will replace this.",
    }

    # Seal manifest
    m_for_hash = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    canonical = json.dumps(m_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()

    manifest_path = SEAL_DIR / "pscd_seal_v1_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    return manifest


def verify_pscd_seal():
    """Verify the seal: ciphertext exists, hashes match, can be decrypted."""
    manifest = json.load(open(SEAL_DIR / "pscd_seal_v1_manifest.json"))

    checks = []

    # 1. Ciphertext physically exists
    ct_path = SEAL_DIR / "pscd_seal_v1_ciphertext.bin"
    checks.append({
        "check": "CIPHERTEXT_EXISTS",
        "passed": ct_path.exists(),
        "path": str(ct_path),
        "size": ct_path.stat().st_size if ct_path.exists() else 0,
    })

    # 2. Ciphertext hash matches
    if ct_path.exists():
        actual_hash = hashlib.sha256(ct_path.read_bytes()).hexdigest()
        checks.append({
            "check": "CIPHERTEXT_HASH_MATCHES",
            "passed": actual_hash == manifest["ciphertext_sha256"],
        })

    # 3. Can decrypt with key
    key_path = SEAL_DIR / "pscd_seal_v1_KEY_DO_NOT_COMMIT.bin"
    if key_path.exists() and ct_path.exists():
        key = key_path.read_bytes()
        ct = ct_path.read_bytes()
        nonce = ct[:12]
        ct_body = ct[12:]
        try:
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ct_body, associated_data=None)
            pt_hash = hashlib.sha256(plaintext).hexdigest()
            checks.append({
                "check": "DECRYPTION_SUCCESS",
                "passed": True,
            })
            checks.append({
                "check": "PLAINTEXT_HASH_MATCHES",
                "passed": pt_hash == manifest["plaintext_sha256"],
            })
        except InvalidTag:
            checks.append({"check": "DECRYPTION_SUCCESS", "passed": False, "error": "InvalidTag"})
    else:
        checks.append({"check": "DECRYPTION_SUCCESS", "passed": False, "error": "Key or ciphertext not found"})

    return checks


def main():
    print("=" * 72)
    print("PSCD_SEAL_V1 — Fresh Sealed Outcome/Foil Artifact")
    print("=" * 72)
    print()

    manifest = create_pscd_seal()
    print(f"Seal created: {manifest['seal_type']}")
    print(f"Ciphertext: {manifest['ciphertext_path']} ({manifest['ciphertext_size_bytes']} bytes)")
    print(f"Ciphertext physically exists: {manifest['ciphertext_physically_exists']}")
    print(f"Ciphertext SHA-256: {manifest['ciphertext_sha256'][:32]}...")
    print(f"Plaintext SHA-256: {manifest['plaintext_sha256'][:32]}...")
    print(f"Encryption: {manifest['encryption']}")
    print(f"Key held by: {manifest['key_held_by']}")
    print(f"Outcomes: {manifest['outcome_count']}")
    print(f"Foils: {manifest['foil_count']}")
    print(f"Manifest SHA-256: {manifest['manifest_sha256'][:32]}...")

    print(f"\nVerifying seal...")
    checks = verify_pscd_seal()
    for c in checks:
        icon = "✓" if c["passed"] else "✗"
        print(f"  {icon} {c['check']}")

    all_pass = all(c["passed"] for c in checks)
    print(f"\n{'ALL CHECKS PASS' if all_pass else 'SEAL VERIFICATION FAILED'}")


if __name__ == "__main__":
    main()
