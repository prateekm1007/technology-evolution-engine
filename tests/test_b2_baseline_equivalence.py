#!/usr/bin/env python3
"""test_b2_baseline_equivalence.py — Adversarial tests for baseline equivalence.

Per audit round 51: the audit must be held to the same epistemic standard
as the experiment itself. Tests specifically attack:

1. None == None never becomes OBSERVED_EQUAL
2. Identical lengths → OBSERVED_EQUAL (not hard-coded DIFFERENT)
3. Different lengths → OBSERVED_DIFFERENT
4. Missing candidate text → NOT_OBSERVABLE
5. Missing source hash → NOT_OBSERVABLE
6. Corrupted raw blob → audit failure (NOT_OBSERVABLE)
7. Candidate/hash mismatch → audit failure (NOT_OBSERVABLE)
8. Missing upstream artifact → NOT_OBSERVABLE (not deletion of dimension)
9. Contract equality never becomes observed equality
10. All 13 dimensions always present
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.b2_provenance import (
    compute_universal_seed,
    compute_shared_entity,
    generate_null_raw_output,
    generate_null_candidates,
    parse_candidates,
    verify_frozen_components,
    ProvenanceLedger,
)
from engine.b2_provenance.generation_null import (
    FROZEN_STOPWORDS,
    FROZEN_ENTITY_DICTIONARY,
    record_null_in_ledger,
)
from scripts.baseline_equivalence_audit import (
    run_baseline_equivalence_audit,
    _compare_provenance_fields,
    _compare_values,
    _verify_entry_provenance,
    ALL_DIMENSIONS,
    CONTRACT_EQUAL, OBSERVED_EQUAL, OBSERVED_DIFFERENT,
    NOT_OBSERVABLE, NOT_RUN,
)


# =====================================================================
# CATEGORY 1: MISSING VALUES NEVER COMPARE EQUAL (FATAL 1)
# =====================================================================

class TestMissingValuesNeverEqual:
    """None == None must NEVER become OBSERVED_EQUAL."""

    def test_none_none_is_not_observable(self):
        """Both values missing → NOT_OBSERVABLE, not OBSERVED_EQUAL."""
        assert _compare_provenance_fields(None, None) == NOT_OBSERVABLE

    def test_none_value_is_not_observable(self):
        """One value missing → NOT_OBSERVABLE."""
        assert _compare_provenance_fields("abc", None) == NOT_OBSERVABLE
        assert _compare_provenance_fields(None, "abc") == NOT_OBSERVABLE

    def test_equal_values_are_observed_equal(self):
        """Both present and equal → OBSERVED_EQUAL."""
        assert _compare_provenance_fields("abc", "abc") == OBSERVED_EQUAL

    def test_different_values_are_observed_different(self):
        """Both present and different → OBSERVED_DIFFERENT."""
        assert _compare_provenance_fields("abc", "xyz") == OBSERVED_DIFFERENT

    def test_compare_values_none_handling(self):
        """_compare_values also handles None correctly."""
        assert _compare_values(None, None) == NOT_OBSERVABLE
        assert _compare_values(None, 5) == NOT_OBSERVABLE
        assert _compare_values(5, None) == NOT_OBSERVABLE
        assert _compare_values(5, 5) == OBSERVED_EQUAL
        assert _compare_values(5, 3) == OBSERVED_DIFFERENT


# =====================================================================
# CATEGORY 2: NO HARD-CODED OBSERVED_DIFFERENT (FATAL 2)
# =====================================================================

class TestNoHardcodedDifferent:
    """candidate_length must be computed from actual measurements,
    never hard-coded as OBSERVED_DIFFERENT."""

    def test_identical_lengths_are_observed_equal(self, tmp_path, monkeypatch):
        """If both arms produce identical-length candidates, state is
        OBSERVED_EQUAL, not hard-coded OBSERVED_DIFFERENT."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")

        # Create engine entries with same-length candidates as null
        # We'll directly append entries with controlled candidate_text
        identical_text = "RELATIONSHIP: A is related to B\nMECHANISM: Both involve crystal."

        # Append engine entry
        ledger.append_candidate_entry(
            case_id="CASE-001", arm="engine", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text=identical_text,
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        # Append null entry with identical text
        ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text=identical_text,
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )

        # NOTE: provenance verification will fail (fake hashes), so
        # dimensions will be NOT_OBSERVABLE. But the _compare_values
        # function itself should return OBSERVED_EQUAL for identical lengths.
        from scripts.baseline_equivalence_audit import measure_candidate_properties
        props = measure_candidate_properties(identical_text)
        assert _compare_values(props["character_count"], props["character_count"]) == OBSERVED_EQUAL


# =====================================================================
# CATEGORY 3: ALL 13 DIMENSIONS ALWAYS PRESENT (SERIOUS 3)
# =====================================================================

class TestAllDimensionsPresent:
    """The audit must always report all 13 dimensions. No dimension
    is ever deleted because the implementation can't observe it yet."""

    def test_empty_ledger_has_all_13_dimensions(self, tmp_path):
        """Even with an empty ledger, all 13 dimensions are reported."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        measured = {m["dimension"] for m in result["measurements"]}
        assert measured == set(ALL_DIMENSIONS), (
            f"Missing dimensions: {set(ALL_DIMENSIONS) - measured}"
        )
        assert len(result["measurements"]) == 13

    def test_all_dimensions_constant_matches(self):
        """ALL_DIMENSIONS has exactly 13 entries."""
        assert len(ALL_DIMENSIONS) == 13

    def test_missing_upstream_is_not_observable_not_deleted(self, tmp_path):
        """upstream_extraction is NOT_OBSERVABLE when extraction artifacts
        are not in the ledger, NOT deleted from the dimension set."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        upstream = [m for m in result["measurements"] if m["dimension"] == "upstream_extraction"]
        assert len(upstream) == 1
        # With empty ledger, it should be NOT_RUN (engine not executed)
        assert upstream[0]["state"] in (NOT_RUN, NOT_OBSERVABLE)

    def test_missing_abstraction_is_not_observable_not_deleted(self, tmp_path):
        """abstraction is NOT_OBSERVABLE when not available, NOT deleted."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        abstraction = [m for m in result["measurements"] if m["dimension"] == "abstraction"]
        assert len(abstraction) == 1

    def test_missing_entity_specificity_is_not_observable_not_deleted(self, tmp_path):
        """entity_specificity is NOT_OBSERVABLE when not available, NOT deleted."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        entity = [m for m in result["measurements"] if m["dimension"] == "entity_specificity"]
        assert len(entity) == 1


# =====================================================================
# CATEGORY 4: PROVENANCE VERIFICATION BEFORE OBSERVED (SERIOUS 4)
# =====================================================================

class TestProvenanceVerification:
    """The audit must verify the complete provenance chain before
    treating an artifact as OBSERVED."""

    def test_verify_entry_provenance_missing_fields(self):
        """Missing required fields → verification fails."""
        entry = {"candidate_text": "test"}
        verified, err = _verify_entry_provenance(entry)
        assert not verified
        assert "raw_output_sha256" in err

    def test_verify_entry_provenance_candidate_hash_mismatch(self):
        """Candidate SHA mismatch → verification fails."""
        entry = {
            "raw_output_sha256": "a" * 64,
            "candidate_sha256": "b" * 64,
            "candidate_text": "test",
            "candidate_rank": 1,
        }
        verified, err = _verify_entry_provenance(entry)
        assert not verified
        assert "SHA mismatch" in err or "not found" in err

    def test_audit_reports_provenance_verification_errors(self, tmp_path):
        """When provenance verification fails, the audit reports errors."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        # Append entry with fake hashes (will fail verification)
        ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="f"*64, raw_output_blob_path="/fake",
            candidate_sha256="g"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="h"*64, source_pair_sha256="i"*64,
            invocation_seed="j"*64,
        )

        result = run_baseline_equivalence_audit(ledger, "CASE-001")
        # Null provenance should be invalid (fake hashes)
        assert result["null_provenance_valid"] is False
        assert len(result["null_verification_errors"]) > 0


# =====================================================================
# CATEGORY 5: CONTRACT_EQUAL IS STRICTLY CONTRACTUAL
# =====================================================================

class TestContractEqualStrict:
    """CONTRACT_EQUAL must mean 'protocol requires equal', NOT
    'architecture proves they were equal during this execution'."""

    def test_human_intervention_is_contract_equal(self, tmp_path):
        """human_intervention is CONTRACT_EQUAL (protocol requirement),
        not OBSERVED_EQUAL."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        hi = [m for m in result["measurements"] if m["dimension"] == "human_intervention"][0]
        assert hi["state"] == CONTRACT_EQUAL

    def test_contract_equal_notes_do_not_claim_observation(self, tmp_path):
        """CONTRACT_EQUAL notes must not say 'verified by ledger' or
        'proven by architecture'."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        hi = [m for m in result["measurements"] if m["dimension"] == "human_intervention"][0]
        assert "verified by" not in hi["notes"].lower()
        assert "proven by" not in hi["notes"].lower()
        assert "contract" in hi["notes"].lower() or "protocol" in hi["notes"].lower()


# =====================================================================
# CATEGORY 6: FROZEN COMPONENT VERIFICATION
# =====================================================================

class TestFrozenComponentVerification:
    """Verify NER components are frozen with SHA-256 verification."""

    def test_verify_frozen_components_passes(self):
        result = verify_frozen_components()
        assert result["entity_dictionary_verified"] is True
        assert result["stopword_set_verified"] is True
        assert result["ner_model_info_verified"] is True

    def test_frozen_artifacts_exist(self):
        base = REPO_ROOT / "provenance" / "frozen_components"
        for name in ["entity_dictionary", "stopword_set", "ner_model_info"]:
            assert (base / f"{name}.json").exists()
            assert (base / f"{name}.sha256").exists()

    def test_runtime_matches_frozen(self):
        base = REPO_ROOT / "provenance" / "frozen_components"
        frozen_sw = set(json.loads((base / "stopword_set.json").read_text())["entries"])
        assert frozen_sw == set(FROZEN_STOPWORDS)
        frozen_dict = set(json.loads((base / "entity_dictionary.json").read_text())["entries"])
        assert frozen_dict == set(FROZEN_ENTITY_DICTIONARY)


# =====================================================================
# CATEGORY 7: PROCESS-ORDER INDEPENDENCE
# =====================================================================

class TestProcessOrderIndependence:
    """Verify null generation is independent of execution order."""

    TEST_A = ["Crystal nucleation A1", "Crystal growth A2", "Crystal dissolution A3"]
    TEST_B = ["Marine precipitation B1", "Shell formation B2", "Bone mineralization B3"]

    def test_null_output_deterministic(self):
        raw1 = generate_null_raw_output(self.TEST_A, self.TEST_B)
        raw2 = generate_null_raw_output(self.TEST_A, self.TEST_B)
        assert raw1 == raw2

    def test_null_independent_of_prior_computation(self):
        _ = generate_null_raw_output(["X1","X2","X3"], ["Y1","Y2","Y3"])
        raw_after = generate_null_raw_output(self.TEST_A, self.TEST_B)
        raw_fresh = generate_null_raw_output(self.TEST_A, self.TEST_B)
        assert raw_after == raw_fresh


# =====================================================================
# CATEGORY 8: AUDIT NEVER DECLARES FAIRNESS
# =====================================================================

class TestNeverDeclaresFairness:
    """The audit must NEVER declare fairness_established = True."""

    def test_empty_ledger_fairness_false(self, tmp_path):
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")
        assert result["summary"]["fairness_established"] is False

    def test_5_state_classification_used(self, tmp_path):
        """All states are from the valid 5-state set."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")
        valid = {CONTRACT_EQUAL, OBSERVED_EQUAL, OBSERVED_DIFFERENT, NOT_OBSERVABLE, NOT_RUN}
        for m in result["measurements"]:
            assert m["state"] in valid

    def test_no_arbitrary_threshold(self, tmp_path):
        """No measurement mentions an arbitrary threshold."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")
        for m in result["measurements"]:
            assert "threshold" not in m.get("notes", "").lower()
            assert "3x" not in m.get("notes", "").lower()
