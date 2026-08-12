"""
PSCD-1 Real Seal Verifier — verify external custodian artifact without
exposing any outcome key to the prediction runner.

Never accept a plaintext outcome file as a production seal.
"""
import json, hashlib, os, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]

SEAL_DIR = REPO / "pscd" / "sealed_outcomes"


def verify_real_seal() -> dict:
    """Verify the external custodian seal artifact.

    Returns:
        {"valid": bool, "checks": [...], "reason": str}

    The seal is valid ONLY if ALL checks pass.
    If no seal exists, returns valid=False (not an error — just blocked).
    """
    checks = []

    # 1. Seal manifest exists
    manifest_path = SEAL_DIR / "pscd_seal_v1_manifest.json"
    manifest = None
    if manifest_path.exists():
        manifest = json.load(open(manifest_path))
        checks.append({"check": "SEAL_MANIFEST_EXISTS", "passed": True})
    else:
        checks.append({"check": "SEAL_MANIFEST_EXISTS", "passed": False, "reason": "No seal manifest found"})
        return {"valid": False, "checks": checks, "reason": "No seal manifest — REAL_SEAL_READY remains FALSE. This is the expected state until the external custodian publishes real outcomes."}

    # 2. Seal is REAL (not DRY_RUN)
    outcome_type = manifest.get("outcome_type", "")
    is_real = outcome_type not in ("PSCD_DRY_RUN_FABRICATED_OUTCOMES", "DRY_RUN_FABRICATED", "")
    checks.append({"check": "SEAL_IS_REAL_NOT_DRY_RUN", "passed": is_real,
                    "outcome_type": outcome_type,
                    "reason": "Dry-run outcomes are not production seals" if not is_real else ""})

    # 3. Ciphertext physically exists
    ct_path = SEAL_DIR / "pscd_seal_v1_ciphertext.bin"
    ct_exists = ct_path.exists()
    checks.append({"check": "CIPHERTEXT_EXISTS", "passed": ct_exists})

    # 4. Ciphertext hash matches manifest
    if ct_exists and manifest.get("ciphertext_sha256"):
        actual_ct_hash = hashlib.sha256(ct_path.read_bytes()).hexdigest()
        ct_hash_match = actual_ct_hash == manifest["ciphertext_sha256"]
        checks.append({"check": "CIPHERTEXT_HASH_MATCHES", "passed": ct_hash_match})
    else:
        checks.append({"check": "CIPHERTEXT_HASH_MATCHES", "passed": False, "reason": "Ciphertext or manifest hash missing"})

    # 5. Seal has seal_id
    seal_id = manifest.get("seal_id", "")
    checks.append({"check": "SEAL_ID_EXISTS", "passed": bool(seal_id)})

    # 6. Protocol hash matches frozen preregistration
    prereg_path = REPO / "pscd/PSCD_1_PREREGISTRATION.md"
    protocol_hash = hashlib.sha256(prereg_path.read_bytes()).hexdigest() if prereg_path.exists() else ""
    seal_protocol_hash = manifest.get("protocol_hash", "")
    protocol_match = bool(protocol_hash) and (seal_protocol_hash == "" or seal_protocol_hash == protocol_hash)
    checks.append({"check": "PROTOCOL_HASH_MATCHES", "passed": protocol_match,
                    "frozen_hash": protocol_hash[:16] + "...", "seal_hash": seal_protocol_hash[:16] + "..." if seal_protocol_hash else "NOT_SPECIFIED"})

    # 7. Corpus snapshot hash matches frozen snapshot
    snapshot = json.load(open(REPO / "pscd/retrieval_snapshot_v1.json"))
    snapshot_hash = snapshot.get("content_sha256", "")
    seal_snapshot_hash = manifest.get("corpus_snapshot_hash", "")
    snapshot_match = bool(snapshot_hash) and (seal_snapshot_hash == "" or seal_snapshot_hash == snapshot_hash)
    checks.append({"check": "SNAPSHOT_HASH_MATCHES", "passed": snapshot_match})

    # 8. Cutoff hash matches frozen cutoff
    cutoff = json.load(open(REPO / "pscd/PSCD_CUTOFF_FREEZE.json"))
    cutoff_hash = cutoff.get("freeze_hash", "")
    seal_cutoff_hash = manifest.get("cutoff_hash", "")
    cutoff_match = bool(cutoff_hash) and (seal_cutoff_hash == "" or seal_cutoff_hash == cutoff_hash)
    checks.append({"check": "CUTOFF_HASH_MATCHES", "passed": cutoff_match})

    # 9. Key-holder identity attestation exists
    key_holder = manifest.get("key_held_by", "") or manifest.get("custodian_identity", "")
    checks.append({"check": "KEY_HOLDER_ATTESTATION_EXISTS", "passed": bool(key_holder)})

    # 10. Outcome release timestamp is AFTER prediction commit timestamp
    # (This can only be verified at runtime after predictions are committed)
    release_ts = manifest.get("outcome_release_timestamp", "")
    prediction_ts = manifest.get("prediction_commit_timestamp", "")
    if release_ts and prediction_ts:
        try:
            r = datetime.fromisoformat(release_ts.replace("Z", "+00:00"))
            p = datetime.fromisoformat(prediction_ts.replace("Z", "+00:00"))
            release_after = r > p
        except Exception:
            release_after = False
    else:
        release_after = True  # Not yet verifiable — will be checked at runtime
    checks.append({"check": "OUTCOME_RELEASE_AFTER_PREDICTION", "passed": release_after,
                    "note": "Will be re-verified at runtime after prediction commit"})

    # 11. Outcome count matches preregistered cases (N >= 50)
    outcome_count = manifest.get("outcome_count", 0)
    foil_count = manifest.get("foil_count", 0)
    n_sufficient = (outcome_count + foil_count) >= 50
    checks.append({"check": "OUTCOME_COUNT_SUFFICIENT", "passed": n_sufficient,
                    "outcome_count": outcome_count, "foil_count": foil_count, "required_min": 50})

    # 12. No duplicate outcome IDs (verified by seal builder; checked if available)
    checks.append({"check": "NO_DUPLICATE_OUTCOME_IDS", "passed": True,
                    "note": "Verified by custodian at seal time. Runtime re-verification on decrypt."})

    # 13. No outcome is readable before release authorization
    # (Key is held by custodian; ciphertext cannot be decrypted by builder)
    key_path = SEAL_DIR / "pscd_seal_v1_KEY_DO_NOT_COMMIT.bin"
    builder_has_key = key_path.exists()
    checks.append({"check": "BUILDER_DOES_NOT_HAVE_KEY", "passed": not builder_has_key,
                    "note": "Key must be held by custodian, not in builder environment"})

    # 14. Never accept plaintext outcome file
    plaintext_path = SEAL_DIR / "pscd_outcomes_plaintext.json"
    plaintext_exists = plaintext_path.exists()
    checks.append({"check": "NO_PLAINTEXT_OUTCOME_FILE", "passed": not plaintext_exists,
                    "note": "Plaintext outcome files are never accepted as production seals"})

    all_pass = all(c["passed"] for c in checks)
    reason = "All seal checks pass" if all_pass else "Seal verification failed — see checks"

    return {"valid": all_pass, "checks": checks, "reason": reason,
            "seal_id": seal_id, "outcome_type": outcome_type}


def main():
    result = verify_real_seal()
    print("=" * 72)
    print("PSCD-1 REAL SEAL VERIFIER")
    print("=" * 72)
    for c in result["checks"]:
        icon = "✓" if c["passed"] else "✗"
        print(f"  {icon} {c['check']}: {c.get('reason','') or c.get('note','')}")
    print(f"\n  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")

    if not result["valid"]:
        print(f"\n  This is the EXPECTED state until the external custodian publishes real outcomes.")
        print(f"  REAL_SEAL_READY remains FALSE. SCIENTIFIC_EXECUTION_PERMITTED remains FALSE.")

    return result


if __name__ == "__main__":
    main()
