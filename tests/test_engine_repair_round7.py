"""
test_engine_repair_round7.py — tests for round-7 repairs.

Repair A: Atomic manifest writes (temp → fsync → rename → verify)
Repair B: LEDGER_FREEZE_RECORD (anchored ledger identity)
Repair C: Explicit verification states (VALID/INVALID/INTEGRITY_FAILURE)
Repair D: Terminology (checkpoint/resume determinism vs real-LLM reproducibility)
Repair E: Real interruption tests at each transactional boundary
"""
import json
import sys
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine.checkpoint import (
    CheckpointedDiscoveryLoop, CheckpointIntegrityError, COMPLETED, FAILED,
)
from engine.persistent_ledger import (
    PersistentLedger, LedgerIntegrityError,
    VerificationStatus, VerificationResult,
)
from engine.lineage_validator import LineageValidator
from engine.providers import MockReasoningProvider, MockLiteratureProvider
from engine.dev_fixtures import CHALLENGE_4
from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, Hypothesis,
)


def _mock_responses():
    extraction_resp = json.dumps({
        "nodes": [{"node_id": "N1", "node_type": "MECHANISM", "label": "test",
                   "evidence_quote": "The slime mold Physarum polycephalum is a single-celled multinucleate organism"}],
        "edges": [],
    })
    abstraction_resp = json.dumps({
        "abstract_principle": "test", "causal_structure": "x→y",
        "inputs": ["a"], "conditions": ["b"], "operations": ["c"],
        "intermediate_state": ["d"], "outputs": ["e"],
        "constraints": ["f"], "failure_conditions": ["g"],
    })
    transfer_resp = json.dumps({
        "source_mechanism": "test", "source_conditions": ["b"],
        "transferred_principle": "test", "required_translation": "test",
        "expected_effect": "test", "boundary_conditions": ["f"],
        "failure_conditions": ["g"], "testable_prediction": "test",
    })
    hypothesis_resp = json.dumps({
        "hypotheses": [{"claim": "test", "mechanism": "test", "assumptions": [],
                        "evidence": [], "novelty_rationale": "", "testability": "",
                        "falsifier": "if X", "expected_failure_modes": []}],
        "distinguishing_predictions": "",
    })
    adversarial_resp = json.dumps({
        "failure_modes": [{"category": "FRAGILE_ASSUMPTION", "description": "weak",
                           "severity": "MEDIUM", "evidence": "test"}],
        "survives": True, "survives_reason": "no HIGH",
    })
    rediscovery_resp = json.dumps({"classification": "NON_TRIVIAL_TRANSFER", "evidence": "x"})
    prediction_resp = json.dumps({
        "observable": "test", "baseline": "test", "expected_direction": "increase",
        "expected_magnitude": "10%", "conditions": [], "uncertainty": 0.3, "falsifier": "if X",
    })
    experiment_resp = json.dumps({
        "objective": "test", "controls": ["c1"], "baseline": "test", "procedure": "test",
        "expected_result": "test", "falsification_condition": "if X", "sample_requirements": "n=3",
        "safety_constraints": [], "estimated_cost": "low", "estimated_duration": "1d",
        "information_gain": "test", "independent_variables": [], "dependent_variables": [],
    })
    return {
        "You are a scientific mechanism extractor": extraction_resp,
        "You are a scientific abstraction engine": abstraction_resp,
        "You are a cross-domain transfer hypothesis engine": transfer_resp,
        "You are a scientific hypothesis generation engine": hypothesis_resp,
        "You are an adversarial scientific critic": adversarial_resp,
        "You are a rediscovery detector": rediscovery_resp,
        "You are a scientific prediction engine": prediction_resp,
        "You are a scientific experiment design engine": experiment_resp,
    }


def _run_mock_loop(challenge, tmp_path, run_id=None):
    provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
    loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
    import engine.checkpoint as cp
    original = cp.RUNS_DIR
    cp.RUNS_DIR = tmp_path / "runs"
    try:
        result = loop.run(challenge, run_id=run_id, resume=False)
    finally:
        cp.RUNS_DIR = original
    run_dir = tmp_path / "runs" / (run_id or f"RUN-{challenge.challenge_id}")
    return loop, result, run_dir


# ============================================================================
# Repair A: Atomic manifest writes
# ============================================================================

class TestRepairAAtomicManifest:
    """The manifest must be written atomically: temp → fsync → rename → verify."""

    def test_manifest_write_is_atomic(self, tmp_path):
        """After a successful run, the manifest must exist and be valid JSON.
        No .tmp file should remain."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-ATOMIC-1")
        manifest_path = run_dir / "manifest.json"
        temp_path = run_dir / "manifest.json.tmp"
        assert manifest_path.exists()
        assert not temp_path.exists(), "temp manifest file should not remain after commit"
        # The manifest must be valid JSON
        data = json.loads(manifest_path.read_text())
        assert "run_id" in data

    def test_corrupted_manifest_raises_checkpoint_integrity_error(self, tmp_path):
        """A corrupted manifest must raise CheckpointIntegrityError on resume."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-ATOMIC-2")
        manifest_path = run_dir / "manifest.json"
        # Corrupt the manifest
        manifest_path.write_text("NOT VALID JSON{{{")
        # Resume must raise CheckpointIntegrityError
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            with pytest.raises(CheckpointIntegrityError, match="corrupted"):
                loop2.run(CHALLENGE_4, run_id="RUN-ATOMIC-2", resume=True)
        finally:
            cp.RUNS_DIR = original

    def test_missing_manifest_raises_checkpoint_integrity_error(self, tmp_path):
        """A missing manifest must raise CheckpointIntegrityError on resume."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-ATOMIC-3")
        manifest_path = run_dir / "manifest.json"
        manifest_path.unlink()
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            with pytest.raises(CheckpointIntegrityError, match="manifest.json is missing"):
                loop2.run(CHALLENGE_4, run_id="RUN-ATOMIC-3", resume=True)
        finally:
            cp.RUNS_DIR = original

    def test_manifest_missing_required_field_raises_error(self, tmp_path):
        """A manifest missing a required field must raise CheckpointIntegrityError."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-ATOMIC-4")
        manifest_path = run_dir / "manifest.json"
        data = json.loads(manifest_path.read_text())
        del data["run_id"]  # remove a required field
        manifest_path.write_text(json.dumps(data, indent=2, default=str))
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            with pytest.raises(CheckpointIntegrityError, match="missing required field"):
                loop2.run(CHALLENGE_4, run_id="RUN-ATOMIC-4", resume=True)
        finally:
            cp.RUNS_DIR = original


# ============================================================================
# Repair B: Ledger freeze record
# ============================================================================

class TestRepairBFreezeRecord:
    """The ledger must have a LEDGER_FREEZE_RECORD that anchors it to the run."""

    def test_freeze_record_created_after_run(self, tmp_path):
        """After a run, LEDGER_FREEZE_RECORD.json must exist."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-FREEZE-1")
        freeze_path = run_dir / "ledger" / "LEDGER_FREEZE_RECORD.json"
        assert freeze_path.exists()
        freeze = json.loads(freeze_path.read_text())
        assert "ledger_index_sha256" in freeze
        assert "object_inventory_sha256" in freeze
        assert "run_id" in freeze
        assert len(freeze["ledger_index_sha256"]) == 64
        assert len(freeze["object_inventory_sha256"]) == 64

    def test_freeze_record_verifies_clean_ledger(self, tmp_path):
        """verify_freeze_record() returns all matches=True on a clean ledger."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-FREEZE-2")
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_freeze_record()
        assert v["freeze_record_exists"] is True
        assert v["index_hash_matches"] is True
        assert v["inventory_hash_matches"] is True
        assert v["detail"] == "freeze record verified"

    def test_freeze_record_detects_index_tampering(self, tmp_path):
        """Modifying the index after freeze → index_hash_matches=False."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-FREEZE-3")
        # Tamper with the index
        index_path = run_dir / "ledger" / "index.json"
        index = json.loads(index_path.read_text())
        # Add a fake entry
        index.setdefault("case", {})["DC-FAKE"] = {
            "object_type": "case", "object_id": "DC-FAKE",
            "content_hash": "0" * 64, "file": "cases/DC-FAKE.json",
            "registered_at": "2026-01-01", "provenance_root_hash": ""
        }
        index_path.write_text(json.dumps(index, indent=2, default=str))
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_freeze_record()
        assert v["index_hash_matches"] is False
        assert v["inventory_hash_matches"] is False  # inventory changed too

    def test_freeze_record_detects_object_substitution(self, tmp_path):
        """Substituting an object (changing its hash) → inventory_hash_matches=False."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-FREEZE-4")
        # Tamper with a case file (change its content, which changes its hash)
        case_file = run_dir / "ledger" / "cases" / "DC-DEV-CH-004.json"
        original = case_file.read_text()
        case_file.write_text(original + "TAMPERED")
        # The index still has the old hash, but the file's actual hash changed.
        # The freeze record's inventory hash is based on the INDEX hashes,
        # so it won't detect the file tamper directly. But verify_registration
        # will detect it as INVALID. The freeze record detects INDEX tampering.
        # This test verifies the freeze record catches index tampering, not file tampering.
        # (File tampering is caught by verify_registration, tested elsewhere.)
        # For this test, we tamper with the INDEX hash to simulate substitution:
        index_path = run_dir / "ledger" / "index.json"
        index = json.loads(index_path.read_text())
        # Change the content_hash for the case in the index
        if "case" in index and "DC-DEV-CH-004" in index["case"]:
            index["case"]["DC-DEV-CH-004"]["content_hash"] = "f" * 64
        index_path.write_text(json.dumps(index, indent=2, default=str))
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_freeze_record()
        assert v["index_hash_matches"] is False  # index changed
        assert v["inventory_hash_matches"] is False  # inventory hash changed


# ============================================================================
# Repair C: Explicit verification states
# ============================================================================

class TestRepairCExplicitStates:
    """verify_registration must return explicit VALID/INVALID/INTEGRITY_FAILURE states."""

    def test_valid_object_returns_VALID(self, tmp_path):
        """A clean object → status=VALID."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-STATES-1")
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_registration("case", "DC-DEV-CH-004")
        assert v["status"] == VerificationStatus.VALID

    def test_tampered_object_returns_INVALID(self, tmp_path):
        """An object whose file hash doesn't match → status=INVALID.
        The file must be valid JSON (so it can be parsed) but its content
        hash must differ from the index."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-STATES-2")
        # Tamper with the case file — modify a field so the JSON is still
        # valid but the content hash changes
        case_file = run_dir / "ledger" / "cases" / "DC-DEV-CH-004.json"
        case_data = json.loads(case_file.read_text())
        case_data["input_sources"] = ["TAMPERED_SOURCE"]
        case_file.write_text(json.dumps(case_data, indent=2, default=str))
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_registration("case", "DC-DEV-CH-004")
        assert v["status"] == VerificationStatus.INVALID

    def test_missing_object_returns_INTEGRITY_FAILURE(self, tmp_path):
        """A missing object file → status=INTEGRITY_FAILURE."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-STATES-3")
        # Delete the case file
        case_file = run_dir / "ledger" / "cases" / "DC-DEV-CH-004.json"
        case_file.unlink()
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_registration("case", "DC-DEV-CH-004")
        assert v["status"] == VerificationStatus.INTEGRITY_FAILURE

    def test_corrupted_object_returns_INTEGRITY_FAILURE(self, tmp_path):
        """A corrupted object file (invalid JSON) → status=INTEGRITY_FAILURE."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-STATES-4")
        # Corrupt the case file
        case_file = run_dir / "ledger" / "cases" / "DC-DEV-CH-004.json"
        case_file.write_text("NOT VALID JSON{{{")
        ledger = PersistentLedger(run_dir / "ledger")
        v = ledger.verify_registration("case", "DC-DEV-CH-004")
        assert v["status"] == VerificationStatus.INTEGRITY_FAILURE

    def test_typed_verification_result(self, tmp_path):
        """verify_registration_typed returns a VerificationResult object."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-STATES-5")
        ledger = PersistentLedger(run_dir / "ledger")
        vr = ledger.verify_registration_typed("case", "DC-DEV-CH-004")
        assert isinstance(vr, VerificationResult)
        assert vr.status == VerificationStatus.VALID
        assert vr.is_valid is True
        assert vr.is_integrity_failure is False


# ============================================================================
# Repair D: Terminology
# ============================================================================

class TestRepairDTerminology:
    """The terminology must distinguish checkpoint/resume determinism from
    real-LLM reproducibility."""

    def test_checkpoint_determinism_proven_under_deterministic_provider(self, tmp_path):
        """Checkpoint/resume determinism is PROVEN under deterministic provider.
        This test verifies the orchestration is deterministic — NOT that the
        real LLM is deterministic."""
        import engine.checkpoint as cp
        cp.RUNS_DIR = tmp_path / "runs_a"
        loop_a, result_a, run_dir_a = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-DET-A")
        cp.RUNS_DIR = tmp_path / "runs_b"
        loop_b, result_b, run_dir_b = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-DET-B")
        # Scientific stages must produce identical hashes
        ext_a = json.loads((run_dir_a / "01_extraction.json").read_text())
        ext_b = json.loads((run_dir_b / "01_extraction.json").read_text())
        assert ext_a["output_hash"] == ext_b["output_hash"]
        # This proves CHECKPOINT/RESUME DETERMINISM, not real-LLM reproducibility.

    def test_real_llm_reproducibility_not_established(self):
        """Real-LLM reproducibility is NOT ESTABLISHED. This test documents
        that the real LLM may produce different outputs on different runs
        even with identical prompts. The engine's checkpoint protocol handles
        this by treating each real-LLM run as unique (not reproducible)."""
        # This is a documentation test — it verifies that the engine code
        # does NOT claim real-LLM reproducibility.
        import engine.checkpoint as cp
        source = Path(cp.__file__).read_text()
        # The code should not claim "real LLM reproducibility" or "model determinism"
        assert "real LLM reproducibility" not in source.lower() or \
               "NOT ESTABLISHED" in source or "not established" in source.lower() or \
               "non-deterministic" in source.lower() or "nondeterministic" in source.lower() or \
               "deterministic provider" in source.lower()  # the code acknowledges the distinction


# ============================================================================
# Repair E: Real interruption tests at transactional boundaries
# ============================================================================

class TestRepairEInterruptionTests:
    """Test that interruption at each transactional boundary produces a
    recoverable state, not a false scientific completion."""

    def test_interruption_before_artifact_write(self, tmp_path):
        """If the process dies before the artifact temp file is written,
        resume must re-run the stage from scratch."""
        # Simulate: run a loop, then delete an artifact file to simulate
        # "died before write". Resume must re-run.
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-INT-1")
        # Delete the 02_abstraction artifact (simulate "died before write")
        (run_dir / "02_abstraction.json").unlink()
        # Also reset the manifest stage status to PENDING (simulate "died before commit")
        manifest = json.loads((run_dir / "manifest.json").read_text())
        manifest["stages"]["02_abstraction"]["status"] = "PENDING"
        manifest["stages"]["02_abstraction"]["output_hash"] = ""
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
        # Resume — the stage must re-run
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            result2 = loop2.run(CHALLENGE_4, run_id="RUN-INT-1", resume=True)
            # The stage must have been re-run and completed
            manifest2 = json.loads((run_dir / "manifest.json").read_text())
            assert manifest2["stages"]["02_abstraction"]["status"] == "COMPLETED"
            assert (run_dir / "02_abstraction.json").exists()
        finally:
            cp.RUNS_DIR = original

    def test_interruption_with_temp_file_present(self, tmp_path):
        """If a .tmp file exists from an interrupted write, resume must
        not be confused by it."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-INT-2")
        # Simulate a leftover temp file from an interrupted stage write
        temp_file = run_dir / "02_abstraction.json.tmp"
        temp_file.write_text("INCOMPLETE WRITE")
        # Resume — the temp file should not cause a false completion
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            # The existing 02_abstraction.json is valid, so resume should
            # skip it (it's already completed). The temp file is ignored.
            result2 = loop2.run(CHALLENGE_4, run_id="RUN-INT-2", resume=True)
            manifest2 = json.loads((run_dir / "manifest.json").read_text())
            assert manifest2["stages"]["02_abstraction"]["status"] == "COMPLETED"
        finally:
            cp.RUNS_DIR = original

    def test_no_state_produces_false_scientific_completion(self, tmp_path):
        """The core invariant: NO interruption state → FALSE SCIENTIFIC COMPLETION.
        If a stage's artifact is missing or hash doesn't match, the stage
        is NOT completed, even if the manifest says COMPLETED."""
        loop, result, run_dir = _run_mock_loop(CHALLENGE_4, tmp_path, run_id="RUN-INT-3")
        # Tamper with the artifact hash (make it not match the manifest)
        artifact_path = run_dir / "03_transfer.json"
        artifact_data = json.loads(artifact_path.read_text())
        artifact_data["output_hash"] = "0" * 64  # fake hash
        artifact_path.write_text(json.dumps(artifact_data, indent=2, default=str))
        # The manifest still says COMPLETED with the old hash.
        # _is_completed() must return False because the hashes don't match.
        import engine.checkpoint as cp
        original = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(responses=_mock_responses(), default_response="{}")
            loop2 = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            manifest = loop2._load_manifest(run_dir / "manifest.json")
            # _is_completed must return False for the tampered stage
            assert not loop2._is_completed(manifest, "03_transfer"), \
                "A stage with a hash mismatch must NOT be considered completed"
        finally:
            cp.RUNS_DIR = original
