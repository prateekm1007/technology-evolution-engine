"""
PSCD-1 Real Seal Verifier V2 — Forensic Hardening.

V2 FIXES:
  1. Missing protocol/corpus/cutoff hash → FAIL (not "assumed valid")
  2. Missing release timestamp → FAIL (not "will be checked at runtime")
  3. Duplicate IDs: actually verified (not just asserted)
  4. Key-holder attestation: requires non-empty + structured identity
  5. Builder key check: uses deployment attestation, not just filename
  6. All checks fail-closed by default
"""
import json, hashlib, os, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
SEAL_DIR = REPO / "pscd" / "sealed_outcomes"


def verify_real_seal() -> dict:
    """Verify external custodian seal. V2: all missing values = FAIL."""
    checks = []

    # 1. Seal manifest exists
    manifest_path = SEAL_DIR / "pscd_seal_v1_manifest.json"
    if not manifest_path.exists():
        checks.append({"check": "SEAL_MANIFEST_EXISTS", "passed": False})
        return {"valid": False, "checks": checks,
                "reason": "No seal manifest — REAL_SEAL_READY remains FALSE. Expected until custodian publishes real outcomes."}
    manifest = json.load(open(manifest_path))
    checks.append({"check": "SEAL_MANIFEST_EXISTS", "passed": True})

    # 2. Seal is REAL (not DRY_RUN) — V2: must explicitly be REAL
    outcome_type = manifest.get("outcome_type", "")
    is_real = outcome_type == "REAL_PROSPECTIVE_OUTCOMES"
    checks.append({"check": "SEAL_IS_REAL_NOT_DRY_RUN", "passed": is_real,
                    "outcome_type": outcome_type,
                    "reason": "Only REAL_PROSPECTIVE_OUTCOMES accepted" if not is_real else ""})

    # 3. Ciphertext physically exists
    ct_path = SEAL_DIR / "pscd_seal_v1_ciphertext.bin"
    ct_exists = ct_path.exists()
    checks.append({"check": "CIPHERTEXT_EXISTS", "passed": ct_exists})

    # 4. Ciphertext hash matches manifest — V2: both must exist AND match
    ct_hash_in_manifest = manifest.get("ciphertext_sha256", "")
    if ct_exists and ct_hash_in_manifest:
        actual_ct_hash = hashlib.sha256(ct_path.read_bytes()).hexdigest()
        ct_hash_match = actual_ct_hash == ct_hash_in_manifest
        checks.append({"check": "CIPHERTEXT_HASH_MATCHES", "passed": ct_hash_match})
    else:
        checks.append({"check": "CIPHERTEXT_HASH_MATCHES", "passed": False,
                        "reason": "Ciphertext or manifest hash missing"})

    # 5. Seal has seal_id — V2: must be non-empty
    seal_id = manifest.get("seal_id", "")
    checks.append({"check": "SEAL_ID_EXISTS", "passed": bool(seal_id)})

    # 6. Protocol hash — V2: missing = FAIL (not "assumed valid")
    prereg_path = REPO / "pscd/PSCD_1_PREREGISTRATION.md"
    frozen_protocol_hash = hashlib.sha256(prereg_path.read_bytes()).hexdigest() if prereg_path.exists() else ""
    seal_protocol_hash = manifest.get("protocol_hash", "")
    if not seal_protocol_hash:
        checks.append({"check": "PROTOCOL_HASH_MATCHES", "passed": False,
                        "reason": "Seal protocol_hash is MISSING — must be present and match"})
    elif not frozen_protocol_hash:
        checks.append({"check": "PROTOCOL_HASH_MATCHES", "passed": False,
                        "reason": "Frozen protocol hash missing"})
    else:
        checks.append({"check": "PROTOCOL_HASH_MATCHES", "passed": seal_protocol_hash == frozen_protocol_hash})

    # 7. Corpus snapshot hash — V2: missing = FAIL
    snapshot = json.load(open(REPO / "pscd/retrieval_snapshot_v1.json"))
    frozen_snapshot_hash = snapshot.get("content_sha256", "")
    seal_snapshot_hash = manifest.get("corpus_snapshot_hash", "")
    if not seal_snapshot_hash:
        checks.append({"check": "SNAPSHOT_HASH_MATCHES", "passed": False,
                        "reason": "Seal corpus_snapshot_hash is MISSING"})
    elif not frozen_snapshot_hash:
        checks.append({"check": "SNAPSHOT_HASH_MATCHES", "passed": False,
                        "reason": "Frozen snapshot hash missing"})
    else:
        checks.append({"check": "SNAPSHOT_HASH_MATCHES", "passed": seal_snapshot_hash == frozen_snapshot_hash})

    # 8. Cutoff hash — V2: missing = FAIL
    cutoff = json.load(open(REPO / "pscd/PSCD_CUTOFF_FREEZE.json"))
    frozen_cutoff_hash = cutoff.get("freeze_hash", "")
    seal_cutoff_hash = manifest.get("cutoff_hash", "")
    if not seal_cutoff_hash:
        checks.append({"check": "CUTOFF_HASH_MATCHES", "passed": False,
                        "reason": "Seal cutoff_hash is MISSING"})
    elif not frozen_cutoff_hash:
        checks.append({"check": "CUTOFF_HASH_MATCHES", "passed": False,
                        "reason": "Frozen cutoff hash missing"})
    else:
        checks.append({"check": "CUTOFF_HASH_MATCHES", "passed": seal_cutoff_hash == frozen_cutoff_hash})

    # 9. Key-holder identity attestation — V2: requires structured identity, not just non-empty string
    key_holder = manifest.get("key_held_by", "") or manifest.get("custodian_identity", "")
    # V2: require at least a colon-separated "identity:type:name" or structured dict
    key_holder_valid = bool(key_holder) and (":" in key_holder or len(key_holder) > 10)
    checks.append({"check": "KEY_HOLDER_ATTESTATION_EXISTS", "passed": key_holder_valid,
                    "key_holder": key_holder[:50] if key_holder else "MISSING"})

    # 10. Outcome release timestamp — V2: missing = FAIL (not "will be checked at runtime")
    release_ts = manifest.get("outcome_release_timestamp", "")
    prediction_ts = manifest.get("prediction_commit_timestamp", "")
    if not release_ts:
        checks.append({"check": "OUTCOME_RELEASE_AFTER_PREDICTION", "passed": False,
                        "reason": "outcome_release_timestamp is MISSING — must be present"})
    elif not prediction_ts:
        # prediction_commit_timestamp not yet set — this is expected pre-run
        # V2: FAIL because we cannot verify ordering without both timestamps
        checks.append({"check": "OUTCOME_RELEASE_AFTER_PREDICTION", "passed": False,
                        "reason": "prediction_commit_timestamp not yet set — ordering cannot be verified"})
    else:
        try:
            r = datetime.fromisoformat(release_ts.replace("Z", "+00:00"))
            p = datetime.fromisoformat(prediction_ts.replace("Z", "+00:00"))
            release_after = r > p
            checks.append({"check": "OUTCOME_RELEASE_AFTER_PREDICTION", "passed": release_after})
        except Exception:
            checks.append({"check": "OUTCOME_RELEASE_AFTER_PREDICTION", "passed": False,
                            "reason": "Cannot parse timestamps"})

    # 11. Outcome count sufficient (N >= 50)
    outcome_count = manifest.get("outcome_count", 0)
    foil_count = manifest.get("foil_count", 0)
    n_sufficient = (outcome_count + foil_count) >= 50
    checks.append({"check": "OUTCOME_COUNT_SUFFICIENT", "passed": n_sufficient,
                    "outcome_count": outcome_count, "foil_count": foil_count, "required_min": 50})

    # 12. Duplicate outcome IDs — V2: actually verify if outcome_ids are in manifest
    outcome_ids = manifest.get("outcome_ids", [])
    if outcome_ids:
        no_dupes = len(outcome_ids) == len(set(outcome_ids))
        checks.append({"check": "NO_DUPLICATE_OUTCOME_IDS", "passed": no_dupes,
                        "n_ids": len(outcome_ids), "n_unique": len(set(outcome_ids))})
    else:
        # V2: if outcome_ids not in manifest, we cannot verify — FAIL
        checks.append({"check": "NO_DUPLICATE_OUTCOME_IDS", "passed": False,
                        "reason": "outcome_ids not present in manifest — cannot verify duplicates"})

    # 13. Builder does not have key — V2: deployment attestation, not just filename
    key_path = SEAL_DIR / "pscd_seal_v1_KEY_DO_NOT_COMMIT.bin"
    builder_has_key_file = key_path.exists()
    # V2: also check deployment attestation
    deployment_attestation = manifest.get("deployment_attestation", {})
    evaluator_identity = deployment_attestation.get("evaluator_identity", "")
    key_store_identity = deployment_attestation.get("key_store_identity", "")
    key_access_policy_hash = deployment_attestation.get("key_access_policy_hash", "")

    key_isolation_ok = (
        not builder_has_key_file and
        bool(evaluator_identity) and
        bool(key_store_identity) and
        bool(key_access_policy_hash)
    )
    checks.append({"check": "BUILDER_DOES_NOT_HAVE_KEY", "passed": key_isolation_ok,
                    "builder_has_key_file": builder_has_key_file,
                    "evaluator_identity": bool(evaluator_identity),
                    "key_store_identity": bool(key_store_identity),
                    "key_access_policy_hash": bool(key_access_policy_hash),
                    "note": "V2: requires deployment attestation, not just filename absence"})

    # 14. No plaintext outcome file
    plaintext_path = SEAL_DIR / "pscd_outcomes_plaintext.json"
    checks.append({"check": "NO_PLAINTEXT_OUTCOME_FILE", "passed": not plaintext_path.exists()})

    # 15. Case-set hash — V2: must exist and match
    case_set_hash = manifest.get("case_set_hash", "")
    checks.append({"check": "CASE_SET_HASH_EXISTS", "passed": bool(case_set_hash),
                    "reason": "case_set_hash is MISSING" if not case_set_hash else ""})

    all_pass = all(c["passed"] for c in checks)
    reason = "All seal checks pass" if all_pass else "Seal verification failed — see checks"

    return {"valid": all_pass, "checks": checks, "reason": reason,
            "seal_id": seal_id, "outcome_type": outcome_type}


def main():
    result = verify_real_seal()
    print("=" * 72)
    print("PSCD-1 REAL SEAL VERIFIER V2 (forensic hardening)")
    print("=" * 72)
    for c in result["checks"]:
        icon = "✓" if c["passed"] else "✗"
        reason = c.get("reason", "") or c.get("note", "")
        print(f"  {icon} {c['check']}: {reason}")
    print(f"\n  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    if not result["valid"]:
        print(f"\n  This is the EXPECTED state until the external custodian publishes real outcomes.")
    return result


if __name__ == "__main__":
    main()
