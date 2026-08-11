#!/usr/bin/env python3
"""test_execution_gate.py — Adversarial tests for the execution gate.

Per audit round 55: the 14 execution-boundary tests establish that
tampering is detected. But they do not establish that the actual
production execution path is FORCED to invoke verify_execution_manifest()
before generating the first candidate.

The invariant:
    UNSEALED / INVALID MANIFEST → HARD STOP → NO GENERATION
    SEALED + VERIFIED MANIFEST → EXECUTION → IMMUTABLE ARTIFACTS → STOP

Tests:
1. No gate active → generation refuses (HARD STOP)
2. Unsealed manifest → gate refuses to open (HARD STOP)
3. Invalid manifest → gate refuses to open (HARD STOP)
4. Valid manifest → gate opens, generation proceeds
5. After gate closes → generation refuses again
6. Execution record contains only machine facts (no interpretive language)
7. Exception during execution → recorded as failure, gate closes
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.b2_provenance import (
    ExecutionGate,
    ExecutionGateError,
    ExecutionRecord,
    assert_execution_gate_active,
    generate_null_candidates,
    generate_null_raw_output,
    ProvenanceLedger,
)
from scripts.verify_audit_instrument import (
    create_execution_manifest,
    verify_execution_manifest,
)


class TestExecutionGateEnforcement:
    """Verify the execution gate is a HARD STOP — no bypass."""

    def test_no_gate_active_refuses_generation(self):
        """Without an active execution gate, generation is refused.

        This is the CENTRAL invariant: no generation without a sealed manifest.
        """
        with pytest.raises(ExecutionGateError, match="HARD STOP"):
            assert_execution_gate_active()

    def test_unsealed_manifest_refuses_gate(self):
        """An unsealed manifest (no manifest_sha256) → HARD STOP."""
        manifest = {
            "preregistration_id": "TEST",
            "case_ids": ["CASE-001"],
            # Missing manifest_sha256 — not sealed
        }
        with pytest.raises(ExecutionGateError, match="not sealed"):
            with ExecutionGate(manifest):
                pass  # should never reach here

    def test_invalid_manifest_refuses_gate(self):
        """An invalid manifest (tampered) → HARD STOP."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        # Tamper: add a case after sealing
        manifest["case_ids"].append("EVIL")
        with pytest.raises(ExecutionGateError, match="HARD STOP"):
            with ExecutionGate(manifest):
                pass

    def test_valid_manifest_opens_gate(self):
        """A valid sealed manifest → gate opens, generation proceeds."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            # Generation can proceed — gate is active
            assert gate.is_active
            assert_execution_gate_active()  # should NOT raise

    def test_gate_closes_after_context(self):
        """After the gate context exits, generation is refused again."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            assert gate.is_active

        # Gate is now closed
        with pytest.raises(ExecutionGateError, match="HARD STOP"):
            assert_execution_gate_active()

    def test_exception_during_execution_recorded(self):
        """If an exception occurs during execution, it's recorded as a
        failure and the gate closes."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})

        with pytest.raises(RuntimeError, match="deliberate"):
            with ExecutionGate(manifest) as gate:
                raise RuntimeError("deliberate failure")

        # The record should have the failure recorded
        assert gate.record is not None
        assert len(gate.record.failures) > 0
        assert "deliberate" in gate.record.failures[0]


class TestExecutionRecordMachineFacts:
    """Verify the execution record contains ONLY machine facts.

    Per audit round 55: the first run reports only machine facts:
    - what ran, what artifacts, hashes, failures, exclusions, provenance
    - NO: successful, failed, fair, discovery, significant, North Star
    """

    FORBIDDEN_WORDS = [
        "successful", "failed", "fair", "discovery",
        "significant", "north star", "evidence"
    ]

    def test_record_has_machine_fact_fields_only(self):
        """The execution record has only machine-fact fields."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            pass

        record = gate.record.to_dict()
        expected_fields = {
            "execution_id", "manifest_sha256", "started_at", "finished_at",
            "cases_processed", "arms_run", "artifacts_produced",
            "failures", "exclusions", "provenance_verified",
            "manifest_verified",
        }
        assert set(record.keys()) == expected_fields

    def test_record_does_not_contain_forbidden_language(self):
        """The execution record does not contain interpretive language."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            gate.add_case_processed("CASE-001")
            gate.add_arm_run("null")
            gate.add_artifact("CASE-001", "null", 1, "a"*64, "b"*64)

        record_str = json.dumps(gate.record.to_dict()).lower()
        for word in self.FORBIDDEN_WORDS:
            assert word not in record_str, (
                f"Execution record contains forbidden word '{word}'. "
                f"The record should contain only machine facts."
            )

    def test_record_artifacts_contain_only_hashes(self):
        """Artifacts in the record contain only case_id, arm, rank, and hashes."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            gate.add_artifact("CASE-001", "null", 1, "a"*64, "b"*64)

        artifact = gate.record.artifacts_produced[0]
        expected_keys = {
            "case_id", "arm", "candidate_rank",
            "candidate_sha256", "raw_output_sha256",
        }
        assert set(artifact.keys()) == expected_keys


class TestExecutionGateIntegration:
    """Verify the gate integrates with the generation pipeline."""

    def test_generation_proceeds_inside_gate(self, tmp_path, monkeypatch):
        """Null generation can proceed inside an active execution gate."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        with ExecutionGate(manifest) as gate:
            # This should work — gate is active
            assert_execution_gate_active()

            a_list = ["Crystal nucleation A1", "Crystal growth A2", "Crystal dissolution A3"]
            b_list = ["Marine precipitation B1", "Shell formation B2", "Bone mineralization B3"]
            result = generate_null_candidates(
                case_id="CASE-001",
                abstracted_mechanisms_a=a_list,
                abstracted_mechanisms_b=b_list,
                preregistration_id="TEST",
            )

            # Record artifacts
            for rank, sha in enumerate(result.candidate_sha256s, 1):
                gate.add_artifact("CASE-001", "null", rank, sha, result.raw_output_sha256)

            gate.add_case_processed("CASE-001")
            gate.add_arm_run("null")

        # Verify the record
        assert "CASE-001" in gate.record.cases_processed
        assert "null" in gate.record.arms_run
        assert len(gate.record.artifacts_produced) == 3
        assert gate.record.manifest_verified is True
        assert gate.record.provenance_verified is True
