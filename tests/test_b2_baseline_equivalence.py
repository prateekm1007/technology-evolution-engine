#!/usr/bin/env python3
"""test_b2_baseline_equivalence.py — Tests for baseline equivalence audit.

Per audit round 50: the audit must consume REAL provenance records,
not simulated data. Uses 5-state classification:
    CONTRACT_EQUAL, OBSERVED_EQUAL, OBSERVED_DIFFERENT, NOT_OBSERVABLE, NOT_RUN

Tests:
1. Frozen component verification (NER identity frozen with SHA-256)
2. Process-order independence (no hidden global state)
3. Baseline equivalence audit with real provenance records
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
    construct_candidate,
    generate_null_raw_output,
    generate_null_candidates,
    parse_candidates,
    verify_frozen_components,
    NULL_CONFIG,
    ProvenanceLedger,
)
from engine.b2_provenance.generation_null import (
    FROZEN_STOPWORDS,
    FROZEN_ENTITY_DICTIONARY,
    get_ner_model_info,
    record_null_in_ledger,
)


# =====================================================================
# CATEGORY 1: FROZEN COMPONENT VERIFICATION
# =====================================================================

class TestFrozenComponentVerification:
    """Verify NER components are frozen with SHA-256 verification."""

    def test_verify_frozen_components_passes(self):
        result = verify_frozen_components()
        assert result["entity_dictionary_verified"] is True
        assert result["stopword_set_verified"] is True
        assert result["ner_model_info_verified"] is True

    def test_entity_dictionary_sha256_recorded(self):
        result = verify_frozen_components()
        assert len(result["entity_dictionary_sha256"]) == 64

    def test_stopword_set_sha256_recorded(self):
        result = verify_frozen_components()
        assert len(result["stopword_set_sha256"]) == 64

    def test_frozen_artifacts_exist_on_disk(self):
        base = REPO_ROOT / "provenance" / "frozen_components"
        for name in ["entity_dictionary", "stopword_set", "ner_model_info"]:
            assert (base / f"{name}.json").exists()
            assert (base / f"{name}.sha256").exists()

    def test_runtime_stopwords_match_frozen(self):
        base = REPO_ROOT / "provenance" / "frozen_components"
        frozen = set(json.loads((base / "stopword_set.json").read_text())["entries"])
        assert frozen == set(FROZEN_STOPWORDS)

    def test_runtime_dictionary_matches_frozen(self):
        base = REPO_ROOT / "provenance" / "frozen_components"
        frozen = set(json.loads((base / "entity_dictionary.json").read_text())["entries"])
        assert frozen == set(FROZEN_ENTITY_DICTIONARY)


# =====================================================================
# CATEGORY 2: PROCESS-ORDER INDEPENDENCE
# =====================================================================

class TestProcessOrderIndependence:
    """Verify null generation is independent of execution order."""

    TEST_A = [
        "Crystal nucleation in supersaturated solutions",
        "Protein-mediated biomineralization in bone tissue",
        "Acoustic cavitation controlling polymorph selection",
    ]
    TEST_B = [
        "Marine diatom silica precipitation via silicatein enzymes",
        "Thermal gradient effects on crystal growth kinetics",
        "Ultrasonic frequency influence on nucleation rate",
    ]

    def test_null_output_deterministic(self):
        raw1 = generate_null_raw_output(self.TEST_A, self.TEST_B)
        raw2 = generate_null_raw_output(self.TEST_A, self.TEST_B)
        assert raw1 == raw2

    def test_shared_entity_deterministic(self):
        e1 = compute_shared_entity(self.TEST_A[0], self.TEST_B[0])
        e2 = compute_shared_entity(self.TEST_A[0], self.TEST_B[0])
        assert e1 == e2

    def test_null_independent_of_prior_computation(self):
        different_a = ["Different A1", "Different A2", "Different A3"]
        different_b = ["Different B1", "Different B2", "Different B3"]
        _ = generate_null_raw_output(different_a, different_b)
        raw_after = generate_null_raw_output(self.TEST_A, self.TEST_B)
        raw_fresh = generate_null_raw_output(self.TEST_A, self.TEST_B)
        assert raw_after == raw_fresh


# =====================================================================
# CATEGORY 3: BASELINE EQUIVALENCE AUDIT (real provenance)
# =====================================================================

class TestBaselineEquivalenceAudit:
    """Verify the baseline equivalence audit consumes real provenance."""

    def test_audit_with_empty_ledger_reports_not_run(self, tmp_path):
        """With an empty ledger, all engine dimensions are NOT_RUN."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit, NOT_RUN
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        assert result["engine_entries_found"] == 0
        assert result["null_entries_found"] == 0
        assert result["summary"]["engine_executed"] is False
        assert result["summary"]["null_executed"] is False
        assert result["summary"]["fairness_established"] is False

        # All engine-dependent dimensions should be NOT_RUN
        for m in result["measurements"]:
            if m["dimension"] != "human_intervention":
                assert m["state"] == NOT_RUN

    def test_audit_with_null_only_reports_not_run_for_engine(self, tmp_path, monkeypatch):
        """With only null entries (no engine), engine dimensions are NOT_RUN."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit, NOT_RUN, OBSERVED_EQUAL
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        a_list = ["Crystal nucleation A1", "Crystal growth A2", "Crystal dissolution A3"]
        b_list = ["Marine precipitation B1", "Shell formation B2", "Bone mineralization B3"]
        result = generate_null_candidates("CASE-001", a_list, b_list, "PREREG-001")
        record_null_in_ledger(ledger, result, "v1", "ZAI", "glm-4-plus", "p"*64, "s"*64, "2026-01-01T00:00:00Z")

        audit = run_baseline_equivalence_audit(ledger, "CASE-001")
        assert audit["null_entries_found"] == 3
        assert audit["engine_entries_found"] == 0

        # Human intervention is CONTRACT_EQUAL (verified by ledger architecture)
        hi = [m for m in audit["measurements"] if m["dimension"] == "human_intervention"][0]
        assert hi["state"] == "CONTRACT_EQUAL"

    def test_audit_uses_5_state_classification(self, tmp_path):
        """The audit uses the 5-state classification, not boolean equivalent."""
        from scripts.baseline_equivalence_audit import (
            run_baseline_equivalence_audit,
            CONTRACT_EQUAL, OBSERVED_EQUAL, OBSERVED_DIFFERENT,
            NOT_OBSERVABLE, NOT_RUN,
        )
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        valid_states = {CONTRACT_EQUAL, OBSERVED_EQUAL, OBSERVED_DIFFERENT,
                        NOT_OBSERVABLE, NOT_RUN}
        for m in result["measurements"]:
            assert m["state"] in valid_states, (
                f"Invalid state '{m['state']}' for dimension '{m['dimension']}'. "
                f"Must be one of {valid_states}."
            )

    def test_audit_does_not_declare_fairness(self, tmp_path):
        """The audit NEVER declares fairness_established = True."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")
        assert result["summary"]["fairness_established"] is False

    def test_audit_measurements_have_provenance(self, tmp_path, monkeypatch):
        """When entries exist, measurements include provenance fields."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        a_list = ["Crystal nucleation A1", "Crystal growth A2", "Crystal dissolution A3"]
        b_list = ["Marine precipitation B1", "Shell formation B2", "Bone mineralization B3"]
        result = generate_null_candidates("CASE-001", a_list, b_list, "PREREG-001")
        record_null_in_ledger(ledger, result, "v1", "ZAI", "glm-4-plus", "p"*64, "s"*64, "2026-01-01T00:00:00Z")

        audit = run_baseline_equivalence_audit(ledger, "CASE-001")

        # Check that null provenance is recorded in measurements
        for m in audit["measurements"]:
            if m["null_provenance"]:
                assert "candidate_id" in m["null_provenance"]
                assert "raw_output_sha256" in m["null_provenance"]
                assert "candidate_sha256" in m["null_provenance"]

    def test_audit_no_arbitrary_threshold(self, tmp_path):
        """The audit does NOT use arbitrary thresholds like 3x length ratio.
        It reports raw measurements only."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        # Check that no measurement mentions a threshold
        for m in result["measurements"]:
            assert "threshold" not in m.get("notes", "").lower(), (
                f"Measurement '{m['dimension']}' mentions a threshold — "
                f"the audit should not use arbitrary thresholds."
            )
            assert "3x" not in m.get("notes", "").lower()
            assert "3.0" not in m.get("notes", "")

    def test_audit_distinguishes_contract_from_observed(self, tmp_path):
        """The audit distinguishes CONTRACT_EQUAL from OBSERVED_EQUAL.
        CONTRACT_EQUAL = the protocol says equal (not measured).
        OBSERVED_EQUAL = measured from actual artifacts and found equal."""
        from scripts.baseline_equivalence_audit import run_baseline_equivalence_audit, CONTRACT_EQUAL
        ledger = ProvenanceLedger(ledger_path=tmp_path / "empty.json")
        result = run_baseline_equivalence_audit(ledger, "CASE-001")

        # human_intervention should be CONTRACT_EQUAL (not observed from artifacts)
        hi = [m for m in result["measurements"] if m["dimension"] == "human_intervention"][0]
        assert hi["state"] == CONTRACT_EQUAL
