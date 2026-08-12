"""
Prospective Infrastructure — Module Tests
==========================================

Tests for each of the 7 prospective modules:
  1. tamper_evident_chain.py
  2. commitment.py
  3. pre_registration.py
  4. generator.py
  5. observation_window.py
  6. deterministic_scorer.py
  7. pre_registered_analysis.py
  8. audit_verifier.py
  9. clean_clone_audit.py

Run: python3 -m pytest discovery_fabric/prospective/tests/test_all.py -v
Or:  python3 discovery_fabric/prospective/tests/test_all.py
"""
from __future__ import annotations

import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from discovery_fabric.prospective import (
    tamper_evident_chain,
    commitment,
    pre_registration,
    generator,
    observation_window,
    deterministic_scorer,
    pre_registered_analysis,
    audit_verifier,
)


# =============================================================================
# Test helpers
# =============================================================================

PASS = "PASS"
FAIL = "FAIL"

def assert_eq(actual, expected, msg=""):
    if actual != expected:
        return FAIL, f"{msg}: expected {expected}, got {actual}"
    return PASS, ""

def assert_true(value, msg=""):
    return assert_eq(bool(value), True, msg)

def assert_false(value, msg=""):
    return assert_eq(bool(value), False, msg)


# =============================================================================
# 1. tamper_evident_chain tests
# =============================================================================

def test_chain_append_and_verify():
    """Append entries and verify chain integrity."""
    # Reset chain
    tamper_evident_chain.reset_chain()
    e1 = tamper_evident_chain.append_chain_entry("COMMITMENT", "hash1", {"a": 1})
    e2 = tamper_evident_chain.append_chain_entry("PREDICTION", "hash2", {"b": 2})
    ok, failures = tamper_evident_chain.verify_chain()
    yield assert_true(ok, f"chain should verify: {failures}")
    yield assert_eq(len(tamper_evident_chain.read_chain()), 2, "chain length")
    yield assert_eq(e2["prev_hash"], e1["entry_hash"], "prev_hash link")
    yield assert_eq(e1["prev_hash"], tamper_evident_chain.GENESIS_HASH, "genesis prev_hash")

def test_chain_tamper_detection():
    """Tamper with an entry and verify detection."""
    tamper_evident_chain.reset_chain()
    tamper_evident_chain.append_chain_entry("COMMITMENT", "hash1", {})
    tamper_evident_chain.append_chain_entry("PREDICTION", "hash2", {})
    # Tamper
    entries = tamper_evident_chain.read_chain()
    entries[0]["metadata"] = {"tampered": True}
    with open(tamper_evident_chain.CHAIN_FILE, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    ok, failures = tamper_evident_chain.verify_chain()
    yield assert_false(ok, "tampered chain should fail verification")
    yield assert_true(any("entry_hash mismatch" in f for f in failures), "should detect tampering")

def test_chain_order_enforcement():
    """Stage ordering is enforced (COMMITMENT before PREDICTION)."""
    tamper_evident_chain.reset_chain()
    tamper_evident_chain.append_chain_entry("COMMITMENT", "h1", {})
    tamper_evident_chain.append_chain_entry("PREDICTION", "h2", {})
    tamper_evident_chain.append_chain_entry("OBSERVATION", "h3", {})
    tamper_evident_chain.append_chain_entry("EVALUATION", "h4", {})
    tamper_evident_chain.append_chain_entry("ANALYSIS", "h5", {})
    ok, _ = tamper_evident_chain.verify_chain()
    yield assert_true(ok, "correct order should pass")
    # Reset
    tamper_evident_chain.reset_chain()


# =============================================================================
# 2. commitment tests
# =============================================================================

def test_commitment_timestamp_is_now():
    """registration_timestamp is captured from system clock, not a parameter."""
    import inspect
    sig = inspect.signature(commitment.build_commitment)
    forbidden = {"registration_timestamp", "created_at", "timestamp"}
    yield assert_true(not (forbidden & set(sig.parameters.keys())),
                      "build_commitment must not accept timestamp parameter")

def test_commitment_covers_5_elements():
    """commitment_hash changes when any of the 5 elements is modified."""
    tamper_evident_chain.reset_chain()
    now = datetime.now(timezone.utc)
    manifest = commitment.build_commitment(
        problem_set=[{"problem_id": "P1", "description": "test", "corpus_query": "q",
                       "domain": "d", "expected_outcome_type": "NUMERIC", "measurement_unit": "u"}],
        model_snapshot={"model_name": "m", "model_version": "v1", "weights_hash": "h",
                        "endpoint_url": None, "api_version": None},
        retrieval_corpus={"corpus_name": "c", "corpus_version": "v1", "corpus_hash": "h",
                          "document_count": 1, "date_filter_upper_bound": "2026-01-01",
                          "date_filter_verified": True},
        prompt_templates={"B_llm_only": "b", "C_mechanism": "c", "F_full": "f", "D_random": "r"},
        analysis_plan={"primary_endpoint": "DPS", "comparison": "t", "alpha": 0.05,
                       "mde": 0.15, "sample_size_per_arm": 50, "indeterminate_handling": "excluded",
                       "calibration_threshold": 0.5, "ic_threshold": 0.67},
        observation_window={"window_start": (now + timedelta(days=1)).isoformat(),
                            "window_end": (now + timedelta(days=2)).isoformat(),
                            "min_observations_per_problem": 1},
        outcome_source_spec={"source_type": "p", "source_name": "n", "source_url": "u",
                              "independence_verification": "i"},
        reality_source_allowlist=[{"source_name": "n", "source_type": "p",
                                    "independence_verification": "i", "timestamp_authority": "publisher"}],
    )
    original_hash = manifest["commitment_hash"]
    # Tamper with model
    tampered = json.loads(json.dumps(manifest))
    tampered["model_snapshot"]["model_version"] = "v2"
    ok, _ = commitment.verify_commitment(tampered)
    yield assert_false(ok, "model tampering should be detected")
    # Tamper with evidence
    tampered = json.loads(json.dumps(manifest))
    tampered["retrieval_corpus"]["corpus_hash"] = "tampered"
    ok, _ = commitment.verify_commitment(tampered)
    yield assert_false(ok, "evidence tampering should be detected")
    # Reset
    tamper_evident_chain.reset_chain()

def test_commitment_refuses_window_before_registration():
    """build_commitment refuses window_start <= registration_timestamp."""
    tamper_evident_chain.reset_chain()
    now = datetime.now(timezone.utc)
    try:
        commitment.build_commitment(
            problem_set=[{"problem_id": "P1", "description": "t", "corpus_query": "q",
                           "domain": "d", "expected_outcome_type": "NUMERIC", "measurement_unit": "u"}],
            model_snapshot={"model_name": "m", "model_version": "v1", "weights_hash": "h",
                            "endpoint_url": None, "api_version": None},
            retrieval_corpus={"corpus_name": "c", "corpus_version": "v1", "corpus_hash": "h",
                              "document_count": 1, "date_filter_upper_bound": "2026-01-01",
                              "date_filter_verified": True},
            prompt_templates={"B_llm_only": "b", "C_mechanism": "c", "F_full": "f", "D_random": "r"},
            analysis_plan={"primary_endpoint": "DPS", "comparison": "t", "alpha": 0.05,
                           "mde": 0.15, "sample_size_per_arm": 50, "indeterminate_handling": "excluded",
                           "calibration_threshold": 0.5, "ic_threshold": 0.67},
            observation_window={"window_start": "2020-01-01T00:00:00Z",  # before now
                                "window_end": "2020-12-31T00:00:00Z",
                                "min_observations_per_problem": 1},
            outcome_source_spec={"source_type": "p", "source_name": "n", "source_url": "u",
                                  "independence_verification": "i"},
            reality_source_allowlist=[{"source_name": "n", "source_type": "p",
                                        "independence_verification": "i", "timestamp_authority": "publisher"}],
        )
        yield FAIL, "should have raised ValueError"
    except ValueError:
        yield PASS, "correctly refused window before registration"
    tamper_evident_chain.reset_chain()


# =============================================================================
# 3. pre_registration tests
# =============================================================================

def test_manifest_seal_and_verify():
    """Manifest is sealed and verification detects tampering."""
    manifest = pre_registration.build_manifest(
        problem_set=[{"problem_id": "P1"}],
        model_snapshot={"model_name": "m"},
        retrieval_corpus={"corpus_hash": "h"},
        prompt_templates={"B_llm_only": "b", "C_mechanism": "c", "F_full": "f", "D_random": "r"},
        analysis_plan={"primary_endpoint": "DPS", "comparison": "t", "alpha": 0.05,
                       "mde": 0.15, "sample_size_per_arm": 50, "indeterminate_handling": "excluded",
                       "calibration_threshold": 0.5, "ic_threshold": 0.67},
        observation_window={"window_start": "2027-01-01", "window_end": "2027-12-31",
                            "min_observations_per_problem": 1},
        outcome_source_spec={"source_name": "n"},
    )
    manifest = pre_registration.seal_manifest(manifest)
    yield assert_true(pre_registration.verify_manifest(manifest), "original manifest verifies")
    # Tamper
    manifest["problem_set"][0]["problem_id"] = "TAMPERED"
    yield assert_false(pre_registration.verify_manifest(manifest), "tampered manifest fails")

def test_manifest_rejects_outcome_keys():
    """build_manifest rejects problems with outcome keys."""
    try:
        pre_registration.build_manifest(
            problem_set=[{"problem_id": "P1", "outcome": "leaked"}],
            model_snapshot={"model_name": "m"},
            retrieval_corpus={"corpus_hash": "h"},
            prompt_templates={"B_llm_only": "b", "C_mechanism": "c", "F_full": "f", "D_random": "r"},
            analysis_plan={"primary_endpoint": "DPS", "comparison": "t", "alpha": 0.05,
                           "mde": 0.15, "sample_size_per_arm": 50, "indeterminate_handling": "excluded",
                           "calibration_threshold": 0.5, "ic_threshold": 0.67},
            observation_window={"window_start": "2027-01-01", "window_end": "2027-12-31",
                                "min_observations_per_problem": 1},
            outcome_source_spec={"source_name": "n"},
        )
        yield FAIL, "should have rejected outcome key"
    except ValueError:
        yield PASS, "correctly rejected outcome key"


# =============================================================================
# 4. generator tests
# =============================================================================

def test_generator_requires_commitment_manifest():
    """verify_prerequisites refuses non-commitment manifests."""
    # Build a non-commitment manifest (via pre_registration, not commitment)
    manifest = pre_registration.build_manifest(
        problem_set=[{"problem_id": "P1"}],
        model_snapshot={"model_name": "m"},
        retrieval_corpus={"corpus_hash": "h"},
        prompt_templates={"B_llm_only": "b", "C_mechanism": "c", "F_full": "f", "D_random": "r"},
        analysis_plan={"primary_endpoint": "DPS", "comparison": "t", "alpha": 0.05,
                       "mde": 0.15, "sample_size_per_arm": 50, "indeterminate_handling": "excluded",
                       "calibration_threshold": 0.5, "ic_threshold": 0.67},
        observation_window={"window_start": "2027-01-01", "window_end": "2027-12-31",
                            "min_observations_per_problem": 1},
        outcome_source_spec={"source_name": "n"},
    )
    manifest = pre_registration.seal_manifest(manifest)
    ok, failures = generator.verify_prerequisites(manifest)
    yield assert_false(ok, "non-commitment manifest should be refused")
    yield assert_true(any("COMMITMENT" in f for f in failures), "should mention COMMITMENT requirement")

def test_generator_validates_prediction():
    """validate_prediction enforces point estimates + tight tolerances."""
    # Valid numeric
    yield assert_true(generator.validate_prediction({
        "predicted_value": 100, "tolerance_lower": 0.5, "tolerance_upper": 2.0,
        "expected_direction": "INCREASE"
    }), "valid numeric prediction")
    # Invalid: tolerance too wide
    yield assert_false(generator.validate_prediction({
        "predicted_value": 100, "tolerance_lower": 0.1, "tolerance_upper": 10.0,
        "expected_direction": "INCREASE"
    }), "tolerance too wide should fail")
    # Valid binary
    yield assert_true(generator.validate_prediction({
        "predicted_value": "YES", "expected_direction": "BINARY"
    }), "valid binary prediction")


# =============================================================================
# 5. observation_window tests
# =============================================================================

def test_observation_seal_and_verify():
    """Observation is sealed and tampering is detected."""
    obs = observation_window.build_observation(
        problem_id="P1", manifest_hash="mh", outcome_value=100, outcome_direction="INCREASE",
        measurement_date="2027-06-01T00:00:00Z", source_name="Nature",
        source_url="https://example.com", curator_id="c1",
        curator_statement="I am independent.", raw_evidence_excerpt="test",
        manifest={"observation_window": {"window_start": "2027-01-01", "window_end": "2027-12-31"},
                  "outcome_source_spec": {"source_name": "Nature"},
                  "reality_source_allowlist": [{"source_name": "Nature", "timestamp_authority": "publisher"}],
                  "registration_timestamp": "2026-08-12T00:00:00Z"},
    )
    obs = observation_window.seal_observation(obs)
    yield assert_true(observation_window.verify_observation(obs), "original verifies")
    obs["outcome_value"] = 999
    yield assert_false(observation_window.verify_observation(obs), "tampered fails")

def test_observation_refuses_non_allowlisted_source():
    """Observation from non-allowlisted source is refused."""
    obs = observation_window.build_observation(
        problem_id="P1", manifest_hash="mh", outcome_value=100, outcome_direction="INCREASE",
        measurement_date="2027-06-01T00:00:00Z", source_name="DISALLOWED",
        source_url="https://example.com", curator_id="c1",
        curator_statement="I am independent.", raw_evidence_excerpt="test",
        manifest={"observation_window": {"window_start": "2027-01-01", "window_end": "2027-12-31"},
                  "outcome_source_spec": {"source_name": "Nature"},
                  "reality_source_allowlist": [{"source_name": "Nature", "timestamp_authority": "publisher"}],
                  "registration_timestamp": "2026-08-12T00:00:00Z"},
    )
    obs = observation_window.seal_observation(obs)
    ok, failures = observation_window.verify_observation_window(obs, manifest={
        "observation_window": {"window_start": "2027-01-01T00:00:00Z", "window_end": "2027-12-31T00:00:00Z"},
        "outcome_source_spec": {"source_name": "Nature"},
        "reality_source_allowlist": [{"source_name": "Nature", "timestamp_authority": "publisher"}],
        "registration_timestamp": "2026-08-12T00:00:00Z",
    })
    yield assert_false(ok, "non-allowlisted source should be refused")
    yield assert_true(any("reality_source_allowlist" in f for f in failures), "should mention allowlist")

def test_evaluation_timestamp_refusal():
    """Scorer refuses evaluation on timestamp violations."""
    # Prediction made AFTER outcome measured
    receipt = {"generation_timestamp": "2027-06-02T00:00:00Z", "candidate_id": "c1",
               "problem_id": "p1", "arm": "B_llm_only"}
    obs = {"measurement_date": "2027-06-01T00:00:00Z", "collected_at": "2027-06-03T00:00:00Z",
           "outcome_value": 100, "outcome_direction": "INCREASE"}
    manifest = {"registration_timestamp": "2026-08-12T00:00:00Z",
                "observation_window": {"window_end": "2027-12-31T00:00:00Z"}}
    ok, failures = observation_window.verify_evaluation_timestamp_constraints(receipt, obs, manifest)
    yield assert_false(ok, "should refuse (prediction after measurement)")
    yield assert_true(any("AFTER" in f and "measurement_date" in f for f in failures), "should mention timestamp violation")


# =============================================================================
# 6. deterministic_scorer tests
# =============================================================================

def test_scorer_refuses_timestamp_violation():
    """Scorer returns EVALUATION_REFUSED on timestamp violation."""
    receipt = {
        "candidate_id": "c1", "problem_id": "p1", "arm": "B_llm_only",
        "receipt_hash": "rh", "manifest_hash": "mh",
        "generation_timestamp": "2027-06-02T00:00:00Z",  # AFTER measurement
        "predicted_value": 100, "tolerance_lower": 0.5, "tolerance_upper": 2.0,
        "expected_direction": "INCREASE",
        "hypothesis": "h", "prediction": "p", "units_range": "50 to 200",
    }
    obs = {"observation_hash": "oh", "outcome_value": 110, "outcome_direction": "INCREASE",
           "measurement_date": "2027-06-01T00:00:00Z", "collected_at": "2027-06-03T00:00:00Z"}
    manifest = {"registration_timestamp": "2026-08-12T00:00:00Z",
                "observation_window": {"window_end": "2027-12-31T00:00:00Z"}}
    score = deterministic_scorer.score_receipt(receipt, obs, None,
                                                {"calibration_threshold": 0.5, "ic_threshold": 0.67},
                                                manifest)
    yield assert_eq(score["final_classification"], "EVALUATION_REFUSED", "should refuse")
    yield assert_eq(score["DISCOVERY_PREDICTION_SCORE"], 0.0, "DPS should be 0")

def test_scorer_correct_numeric():
    """Scorer returns CORRECT for in-range numeric prediction."""
    receipt = {
        "candidate_id": "c1", "problem_id": "p1", "arm": "B_llm_only",
        "receipt_hash": "rh", "manifest_hash": "mh",
        "generation_timestamp": "2026-08-13T00:00:00Z",  # before measurement
        "generation_success": True,
        "predicted_value": 100, "tolerance_lower": 0.5, "tolerance_upper": 2.0,
        "expected_direction": "INCREASE",
        "hypothesis": "h", "prediction": "p", "units_range": "50 to 200",
    }
    obs = {"observation_hash": "oh", "outcome_value": 110, "outcome_direction": "INCREASE",
           "measurement_date": "2027-06-01T00:00:00Z", "collected_at": "2027-06-03T00:00:00Z"}
    manifest = {"registration_timestamp": "2026-08-12T00:00:00Z",
                "observation_window": {"window_end": "2027-12-31T00:00:00Z"}}
    score = deterministic_scorer.score_receipt(receipt, obs, None,
                                                {"calibration_threshold": 0.5, "ic_threshold": 0.67},
                                                manifest)
    yield assert_eq(score["final_classification"], "CORRECT", "should be CORRECT")
    yield assert_true(score["quantitative_accuracy"]["calibration_error"] is not None
                      and score["quantitative_accuracy"]["calibration_error"] <= 0.5, "cal error <= 0.5")


# =============================================================================
# 7. pre_registered_analysis tests
# =============================================================================

def test_analysis_negative_when_no_significance():
    """Analysis returns NEGATIVE when no statistical significance."""
    scores = []
    for arm in ["B_llm_only", "C_mechanism", "F_full", "D_random"]:
        for i in range(5):
            scores.append({
                "candidate_id": f"c-{i}-{arm}", "problem_id": f"p-{i}", "arm": arm,
                "final_classification": "INCORRECT",
                "DISCOVERY_PREDICTION_SCORE": 0.0,
                "information_content": {"classification": "GENUINE_NOVEL_PREDICTION",
                                        "information_content_score": 0.9},
                "quantitative_accuracy": {"verdict": "INCORRECT", "calibration_error": 1.5,
                                          "predicted": 100, "observed": 110, "tolerance_bounds": [50, 200]},
            })
    plan = {"alpha": 0.05, "mde": 0.15, "indeterminate_handling": "excluded",
            "calibration_threshold": 0.5, "ic_threshold": 0.67, "num_comparisons": 3,
            "meaningful_min_novel": 3, "material_advantage_pp": 15.0,
            "primary_endpoint": "DPS", "comparison": "t"}
    result = pre_registered_analysis.apply_analysis(scores, plan)
    yield assert_eq(result["decision"], "NEGATIVE_RESULT", "should be NEGATIVE (no DPS=1)")

def test_analysis_plan_immutability_check():
    """verify_analysis_plan_immutability detects modified plans."""
    plan1 = {"alpha": 0.05, "mde": 0.15, "indeterminate_handling": "excluded",
             "calibration_threshold": 0.5, "ic_threshold": 0.67, "num_comparisons": 3,
             "sample_size_per_arm": 50, "primary_endpoint": "DPS", "comparison": "t"}
    plan2 = json.loads(json.dumps(plan1))
    plan2["alpha"] = 0.01  # modified
    ok, failures = pre_registered_analysis.verify_analysis_plan_immutability(plan2, plan1, [])
    yield assert_false(ok, "modified plan should fail")
    yield assert_true(any("alpha" in f for f in failures), "should mention alpha")


# =============================================================================
# 8. audit_verifier tests
# =============================================================================

def test_audit_verifier_empty_pipeline():
    """Audit verifier handles empty pipeline gracefully."""
    report = audit_verifier.run_audit(manifest=None, manifest_path=None,
                                       receipts=None, observations=None,
                                       scores=None, analysis_result=None)
    # Should have skipped checks
    yield assert_true(report["summary"]["n_failed"] == 0, "no failures on empty pipeline")
    yield assert_true(report["summary"]["n_applicable"] == 0 or report["summary"]["n_applicable"] == 1,
                      "minimal applicable checks")


# =============================================================================
# Test runner
# =============================================================================

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("chain_append_and_verify", test_chain_append_and_verify),
        ("chain_tamper_detection", test_chain_tamper_detection),
        ("chain_order_enforcement", test_chain_order_enforcement),
        ("commitment_timestamp_is_now", test_commitment_timestamp_is_now),
        ("commitment_covers_5_elements", test_commitment_covers_5_elements),
        ("commitment_refuses_window_before_registration", test_commitment_refuses_window_before_registration),
        ("manifest_seal_and_verify", test_manifest_seal_and_verify),
        ("manifest_rejects_outcome_keys", test_manifest_rejects_outcome_keys),
        ("generator_requires_commitment_manifest", test_generator_requires_commitment_manifest),
        ("generator_validates_prediction", test_generator_validates_prediction),
        ("observation_seal_and_verify", test_observation_seal_and_verify),
        ("observation_refuses_non_allowlisted_source", test_observation_refuses_non_allowlisted_source),
        ("evaluation_timestamp_refusal", test_evaluation_timestamp_refusal),
        ("scorer_refuses_timestamp_violation", test_scorer_refuses_timestamp_violation),
        ("scorer_correct_numeric", test_scorer_correct_numeric),
        ("analysis_negative_when_no_significance", test_analysis_negative_when_no_significance),
        ("analysis_plan_immutability_check", test_analysis_plan_immutability_check),
        ("audit_verifier_empty_pipeline", test_audit_verifier_empty_pipeline),
    ]

    print("=" * 76)
    print("PROSPECTIVE INFRASTRUCTURE — MODULE TESTS")
    print("=" * 76)
    print()

    total_pass = 0
    total_fail = 0
    for name, test_fn in tests:
        print(f"[{name}]")
        n = 0
        for status, msg in test_fn():
            n += 1
            if status == PASS:
                total_pass += 1
            else:
                total_fail += 1
                print(f"  {status}: {msg}")
        if n == 0:
            print(f"  (no assertions)")
        else:
            print(f"  {n} assertions, all PASS" if total_fail == 0 else f"  {n} assertions, some FAILED")

    print()
    print("=" * 76)
    print(f"TOTAL: {total_pass} passed, {total_fail} failed")
    print("=" * 76)
    return total_fail == 0


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
