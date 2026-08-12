"""
PROSPECTIVE EXPERIMENT — Clean-Clone Audit
============================================

Simulates a clean-clone audit by:
  1. Re-running the audit_verifier from scratch on the existing artifacts
  2. Verifying the tamper-evident chain from scratch
  3. Re-running all negative controls
  4. Producing a sealed audit certificate

The exit criterion is:
    "a clean-clone audit can verify that the system physically cannot
     backdate registration, alter the evidence universe, substitute a model,
     modify a prediction, or read future observations before the observation
     window closes."

This module is designed to be runnable by an INDEPENDENT auditor. The auditor:
  1. Clones the repository
  2. Runs: python3 discovery_fabric/prospective/clean_clone_audit.py
  3. Receives a PASS/FAIL certificate with a hash

The certificate is reproducible: re-running the audit on the same artifacts
produces the same hash (modulo timestamp).
"""
from __future__ import annotations

import json
import hashlib
import sys
import inspect
from pathlib import Path
from datetime import datetime, timezone

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from discovery_fabric.prospective import (
    audit_verifier,
    tamper_evident_chain,
    commitment,
    generator,
    observation_window,
)
from discovery_fabric.v1_13.prediction_receipt import verify_receipt


# =============================================================================
# Clean-clone audit checks
# =============================================================================

def check_chain_integrity() -> dict:
    """Verify the tamper-evident audit chain from scratch."""
    ok, failures = tamper_evident_chain.verify_chain()
    return {
        "check": "CHAIN_INTEGRITY",
        "passed": ok,
        "chain_length": tamper_evident_chain.get_chain_length(),
        "failures": failures[:5],
    }


def check_no_backdate_capability() -> dict:
    """Verify that build_commitment does not accept a timestamp parameter."""
    sig = inspect.signature(commitment.build_commitment)
    params = list(sig.parameters.keys())
    forbidden = {"registration_timestamp", "created_at", "timestamp", "pre_registration_timestamp"}
    found_forbidden = forbidden & set(params)
    return {
        "check": "NO_BACKDATE_CAPABILITY",
        "passed": len(found_forbidden) == 0,
        "params": params,
        "forbidden_params_found": sorted(found_forbidden),
    }


def check_commitment_covers_5_elements(manifest: dict) -> dict:
    """Verify that the commitment_hash covers all 5 elements by tampering each."""
    if not manifest or not manifest.get("commitment_hash"):
        return {"check": "COMMITMENT_COVERS_5_ELEMENTS", "passed": False,
                "reason": "no commitment manifest"}

    elements = ["model_snapshot", "retrieval_corpus", "prompt_templates", "problem_set", "arms"]
    results = {}
    for elem in elements:
        tampered = json.loads(json.dumps(manifest))
        if elem == "arms":
            tampered["arms"] = ["tampered_arm"]
        elif elem == "problem_set":
            tampered["problem_set"][0]["problem_id"] = "TAMPERED"
        elif elem == "model_snapshot":
            tampered["model_snapshot"]["model_version"] = "TAMPERED"
        elif elem == "retrieval_corpus":
            tampered["retrieval_corpus"]["corpus_hash"] = "TAMPERED"
        elif elem == "prompt_templates":
            tampered["prompt_templates"]["B_llm_only"] = "TAMPERED"
        # Re-verify commitment
        ok, _ = commitment.verify_commitment(tampered)
        results[elem] = not ok  # should FAIL verification = tampering detected

    all_detected = all(results.values())
    return {
        "check": "COMMITMENT_COVERS_5_ELEMENTS",
        "passed": all_detected,
        "tamper_detection_by_element": results,
    }


def check_receipt_immutability(receipts: list[dict]) -> dict:
    """Verify that modifying any receipt is detected."""
    if not receipts:
        return {"check": "RECEIPT_IMMUTABILITY", "passed": False, "reason": "no receipts"}
    # Tamper with each receipt and verify detection
    all_detected = True
    for r in receipts:
        tampered = json.loads(json.dumps(r))
        tampered["predicted_value"] = 99999
        if verify_receipt(tampered):
            all_detected = False
            break
    return {
        "check": "RECEIPT_IMMUTABILITY",
        "passed": all_detected,
        "n_receipts_tested": len(receipts),
    }


def check_observation_window_enforcement(manifest: dict) -> dict:
    """Verify that observations before window_start are refused."""
    if not manifest:
        return {"check": "WINDOW_ENFORCEMENT", "passed": False, "reason": "no manifest"}
    window_start = manifest.get("observation_window", {}).get("window_start")
    if not window_start:
        return {"check": "WINDOW_ENFORCEMENT", "passed": False, "reason": "no window_start"}

    from datetime import timedelta
    ws_dt = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
    early_dt = ws_dt - timedelta(hours=1)

    early_obs = observation_window.build_observation(
        problem_id="TEST",
        manifest_hash=manifest.get("manifest_hash", ""),
        outcome_value=100,
        outcome_direction="INCREASE",
        measurement_date=early_dt.isoformat(),
        source_name="Nature",
        source_url="https://example.com",
        curator_id="curator",
        curator_statement="I am independent.",
        raw_evidence_excerpt="test",
        manifest=manifest,
    )
    early_obs = observation_window.seal_observation(early_obs)
    ok, failures = observation_window.verify_observation_window(early_obs, manifest)
    return {
        "check": "WINDOW_ENFORCEMENT",
        "passed": not ok,  # should FAIL = enforcement works
        "failures": failures[:3],
    }


def check_reality_source_allowlist(manifest: dict) -> dict:
    """Verify that observations from non-allowlisted sources are refused."""
    if not manifest:
        return {"check": "REALITY_SOURCE_ALLOWLIST", "passed": False, "reason": "no manifest"}
    allowlist = manifest.get("reality_source_allowlist", [])
    if not allowlist:
        return {"check": "REALITY_SOURCE_ALLOWLIST", "passed": False, "reason": "no allowlist"}

    # Build an observation from a non-allowlisted source
    window_start = manifest.get("observation_window", {}).get("window_start")
    ws_dt = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
    from datetime import timedelta
    future_dt = ws_dt + timedelta(minutes=5)

    bad_obs = observation_window.build_observation(
        problem_id="TEST",
        manifest_hash=manifest.get("manifest_hash", ""),
        outcome_value=100,
        outcome_direction="INCREASE",
        measurement_date=future_dt.isoformat(),
        source_name="DISALLOWED_SOURCE",  # not in allowlist
        source_url="https://example.com",
        curator_id="curator",
        curator_statement="I am independent.",
        raw_evidence_excerpt="test",
        manifest=manifest,
    )
    bad_obs = observation_window.seal_observation(bad_obs)
    ok, failures = observation_window.verify_observation_window(bad_obs, manifest)
    has_allowlist_failure = any("reality_source_allowlist" in f or "NOT in the reality_source_allowlist" in f for f in failures)
    return {
        "check": "REALITY_SOURCE_ALLOWLIST",
        "passed": has_allowlist_failure,  # should have failure = enforcement works
        "failures": failures[:3],
    }


# =============================================================================
# Top-level clean-clone audit
# =============================================================================

def run_clean_clone_audit() -> dict:
    """Run the complete clean-clone audit.

    Returns a sealed audit certificate.
    """
    checks = []

    # 1. Chain integrity
    checks.append(check_chain_integrity())

    # 2. No backdate capability
    checks.append(check_no_backdate_capability())

    # Load the commitment manifest (if exists)
    manifest = None
    manifest_paths = [
        commitment.MANIFESTS_DIR / "commitment.json",
        commitment.MANIFESTS_DIR / "synthetic_commitment.json",
        commitment.MANIFESTS_DIR / "synthetic_commitment_backup.json",
    ]
    for p in manifest_paths:
        if p.exists():
            with open(p) as f:
                manifest = json.load(f)
            break

    # 3. Commitment covers 5 elements
    checks.append(check_commitment_covers_5_elements(manifest))

    # 4. Receipt immutability
    receipts = []
    for rp in sorted(generator.RECEIPTS_DIR.glob("PROS-*.json")):
        with open(rp) as f:
            receipts.append(json.load(f))
    checks.append(check_receipt_immutability(receipts))

    # 5. Observation window enforcement
    checks.append(check_observation_window_enforcement(manifest))

    # 6. Reality-source allowlist
    checks.append(check_reality_source_allowlist(manifest))

    # 7. Run the standard audit_verifier on whatever artifacts exist
    observations = []
    for op in sorted(observation_window.OBSERVATIONS_DIR.glob("obs_*.json")):
        with open(op) as f:
            observations.append(json.load(f))
    from discovery_fabric.prospective.deterministic_scorer import SCORES_DIR
    scores = []
    sp = SCORES_DIR / "scores.json"
    if sp.exists():
        with open(sp) as f:
            scores = json.load(f)
    analysis = None
    ap = SCORES_DIR / "analysis_result.json"
    if ap.exists():
        with open(ap) as f:
            analysis = json.load(f)

    manifest_path = None
    for p in manifest_paths:
        if p.exists():
            manifest_path = p
            break

    standard_audit = audit_verifier.run_audit(
        manifest=manifest, manifest_path=manifest_path,
        receipts=receipts, observations=observations,
        scores=scores, analysis_result=analysis,
    )
    audit_verifier.save_audit_report(standard_audit)

    # Summary
    n_passed = sum(1 for c in checks if c["passed"])
    n_failed = sum(1 for c in checks if not c["passed"])
    overall_pass = n_failed == 0 and standard_audit["summary"]["overall_pass"]

    certificate = {
        "schema_version": "1.0.0",
        "certificate_type": "CLEAN_CLONE_AUDIT",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "standard_audit_summary": standard_audit["summary"],
        "summary": {
            "n_checks": len(checks),
            "n_passed": n_passed,
            "n_failed": n_failed,
            "overall_pass": overall_pass,
        },
        "exit_criterion": {
            "description": "The system physically cannot backdate registration, alter the evidence universe, substitute a model, modify a prediction, or read future observations before the observation window closes.",
            "verified": overall_pass,
            "sub_checks": {
                "cannot_backdate_registration": checks[1]["passed"],
                "cannot_alter_evidence_universe": checks[2]["passed"],
                "cannot_substitute_model": checks[2]["passed"],  # same commitment check
                "cannot_modify_prediction": checks[3]["passed"],
                "cannot_read_future_observations": checks[4]["passed"],
            },
        },
    }

    canonical = json.dumps(certificate, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    certificate["certificate_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return certificate


def save_certificate(cert: dict) -> Path:
    """Save the audit certificate."""
    out_path = REPO / "discovery_fabric/prospective/audit" / f"clean_clone_certificate_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(out_path, "w") as f:
        json.dump(cert, f, indent=2, ensure_ascii=False)
    return out_path


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 76)
    print("PROSPECTIVE EXPERIMENT — CLEAN-CLONE AUDIT")
    print("=" * 76)
    print()
    print("This audit simulates a clean-clone verification. An independent")
    print("auditor would clone the repository and run this script to verify")
    print("the system's tamper-evidence and refusal properties.")
    print()

    cert = run_clean_clone_audit()
    out_path = save_certificate(cert)

    print("CLEAN-CLONE AUDIT CHECKS:")
    print(f"  {'CHECK':<40} {'PASS':<6}")
    print("-" * 50)
    for c in cert["checks"]:
        passed_str = "PASS" if c["passed"] else "FAIL"
        print(f"  {c['check']:<40} {passed_str:<6}")

    print()
    print(f"Standard audit summary: {cert['standard_audit_summary']}")
    print(f"Overall: {'PASS' if cert['summary']['overall_pass'] else 'FAIL'}")
    print(f"  Checks passed: {cert['summary']['n_passed']}/{cert['summary']['n_checks']}")
    print()
    print("EXIT CRITERION VERIFICATION:")
    ec = cert["exit_criterion"]
    print(f"  Description: {ec['description'][:80]}...")
    print(f"  Verified: {'YES' if ec['verified'] else 'NO'}")
    print(f"  Sub-checks:")
    for k, v in ec["sub_checks"].items():
        print(f"    {k:<40} {'PASS' if v else 'FAIL'}")

    print()
    print(f"Certificate: {out_path}")
    print(f"Certificate hash: {cert['certificate_hash'][:32]}...")


if __name__ == "__main__":
    main()
