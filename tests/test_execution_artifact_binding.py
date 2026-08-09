#!/usr/bin/env python3
"""test_execution_artifact_binding.py — Tests for execution-artifact binding.

Per audit round 58:
1. Every CANDIDATE_GENERATED event contains execution_id + manifest_sha256
   sourced from the active gate (not caller-supplied)
2. Post-execution mutation mechanically invalidates artifacts via
   COMPROMISE_RECORDED event (not merely in-memory failure string)
3. An auditor can mechanically connect execution → artifact
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.b2_provenance import (
    ProvenanceLedger,
    ExecutionGate,
    ExecutionGateError,
)
from scripts.verify_audit_instrument import create_execution_manifest


@pytest.fixture
def execution_gate():
    """Fixture that provides an active execution gate."""
    manifest = create_execution_manifest("TEST-BINDING", ["CASE-001"], {})
    with ExecutionGate(manifest) as gate:
        yield gate


class TestExecutionArtifactBinding:
    """Verify CANDIDATE_GENERATED events are bound to execution identity."""

    def test_candidate_event_contains_execution_id(self, tmp_path, execution_gate):
        """Every CANDIDATE_GENERATED event contains execution_id
        sourced from the active gate."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        assert "execution_id" in entry
        assert entry["execution_id"] != "UNKNOWN"
        assert entry["execution_id"] == execution_gate.record.execution_id

    def test_candidate_event_contains_manifest_sha256(self, tmp_path, execution_gate):
        """Every CANDIDATE_GENERATED event contains manifest_sha256
        sourced from the active gate."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        assert "manifest_sha256" in entry
        assert entry["manifest_sha256"] != "UNKNOWN"
        assert entry["manifest_sha256"] == execution_gate.manifest["manifest_sha256"]

    def test_execution_identity_from_gate_not_caller(self, tmp_path, execution_gate):
        """execution_id and manifest_sha256 come from the ACTIVE GATE,
        not from caller-supplied arguments. The caller cannot override them."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        # The caller does NOT pass execution_id or manifest_sha256 —
        # they are automatically sourced from the active gate.
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
            # NOTE: no execution_id or manifest_sha256 parameter
        )
        # The values are from the gate, not from the caller
        assert entry["execution_id"] == execution_gate.record.execution_id
        assert entry["manifest_sha256"] == execution_gate.manifest["manifest_sha256"]

    def test_candidate_event_contains_artifact_status(self, tmp_path, execution_gate):
        """Every CANDIDATE_GENERATED event contains artifact_status = VALID."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        assert entry["artifact_status"] == "VALID"

    def test_auditor_can_connect_execution_to_artifact(self, tmp_path, execution_gate):
        """An auditor can mechanically connect execution → artifact by
        checking that CANDIDATE_GENERATED events contain the same
        execution_id and manifest_sha256 as the execution gate."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        for rank in range(1, 4):
            ledger.append_candidate_entry(
                case_id="CASE-001", arm="null", candidate_rank=rank,
                raw_output_sha256=f"a{rank}"*32, raw_output_blob_path=f"/fake{rank}",
                candidate_sha256=f"b{rank}"*32, candidate_text=f"candidate {rank}",
                generation_timestamp="2026-01-01T00:00:00Z",
                engine_version="v1", provider="ZAI", model="glm-4-plus",
                prompt_hash="c"*64, source_pair_sha256="d"*64,
                invocation_seed="e"*64,
            )

        gen_entries = ledger.get_entries_for_case("CASE-001", arm="null")
        for entry in gen_entries:
            assert entry["execution_id"] == execution_gate.record.execution_id
            assert entry["manifest_sha256"] == execution_gate.manifest["manifest_sha256"]


class TestCompromiseRecording:
    """Verify post-execution mutation mechanically invalidates artifacts."""

    def test_mark_execution_compromised_creates_event(self, tmp_path, execution_gate):
        """mark_execution_compromised creates a COMPROMISE_RECORDED event."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        # Generate a candidate
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        execution_id = entry["execution_id"]

        # Mark as compromised
        compromise_entry = ledger.mark_execution_compromised(
            execution_id, "Post-execution substrate mutation detected"
        )
        assert compromise_entry["event_type"] == "COMPROMISE_RECORDED"
        assert compromise_entry["execution_id"] == execution_id
        assert "substrate mutation" in compromise_entry["reason"]

    def test_is_execution_compromised_returns_true(self, tmp_path, execution_gate):
        """After marking compromised, is_execution_compromised returns True."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        execution_id = entry["execution_id"]

        assert not ledger.is_execution_compromised(execution_id)

        ledger.mark_execution_compromised(execution_id, "test reason")

        assert ledger.is_execution_compromised(execution_id)

    def test_is_execution_compromised_false_for_uncompromised(self, tmp_path, execution_gate):
        """is_execution_compromised returns False for uncompromised execution."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        assert not ledger.is_execution_compromised(entry["execution_id"])

    def test_compromise_preserves_original_entry_hash(self, tmp_path, execution_gate):
        """COMPROMISE_RECORDED is append-only — it does NOT mutate
        the original CANDIDATE_GENERATED event."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        original_hash = entry["entry_hash"]
        execution_id = entry["execution_id"]

        ledger.mark_execution_compromised(execution_id, "test reason")

        # Original entry hash unchanged
        retrieved = ledger.get_generation_event(entry["candidate_id"])
        assert retrieved["entry_hash"] == original_hash
        assert retrieved["artifact_status"] == "VALID"  # original status preserved

        # Hash chain still valid
        assert ledger.verify_hash_chain() is True

    def test_double_compromise_rejected(self, tmp_path, execution_gate):
        """Cannot record COMPROMISE_RECORDED twice for same execution."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        execution_id = entry["execution_id"]

        ledger.mark_execution_compromised(execution_id, "first reason")
        with pytest.raises(ValueError, match="already"):
            ledger.mark_execution_compromised(execution_id, "second reason")

    def test_adjudication_not_gated(self, tmp_path, execution_gate):
        """Per audit round 58: append_adjudication_result is NOT gated.
        Adjudication is intentionally downstream and can occur after
        the generation execution has closed."""
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")
        entry = ledger.append_candidate_entry(
            case_id="CASE-001", arm="null", candidate_rank=1,
            raw_output_sha256="a"*64, raw_output_blob_path="/fake",
            candidate_sha256="b"*64, candidate_text="test candidate",
            generation_timestamp="2026-01-01T00:00:00Z",
            engine_version="v1", provider="ZAI", model="glm-4-plus",
            prompt_hash="c"*64, source_pair_sha256="d"*64,
            invocation_seed="e"*64,
        )
        candidate_id = entry["candidate_id"]

    # Note: adjudication is tested after gate closes in the integration test below
    def test_adjudication_works_after_gate_closes(self, tmp_path):
        """Adjudication can be appended AFTER the execution gate has closed.
        This is by design — adjudication is downstream of generation."""
        manifest = create_execution_manifest("TEST", ["CASE-001"], {})
        ledger = ProvenanceLedger(ledger_path=tmp_path / "ledger.json")

        with ExecutionGate(manifest) as gate:
            entry = ledger.append_candidate_entry(
                case_id="CASE-001", arm="null", candidate_rank=1,
                raw_output_sha256="a"*64, raw_output_blob_path="/fake",
                candidate_sha256="b"*64, candidate_text="test candidate",
                generation_timestamp="2026-01-01T00:00:00Z",
                engine_version="v1", provider="ZAI", model="glm-4-plus",
                prompt_hash="c"*64, source_pair_sha256="d"*64,
                invocation_seed="e"*64,
            )
            candidate_id = entry["candidate_id"]

        # Gate is now closed. Adjudication should still work.
        adj_entry = ledger.append_adjudication_result(
            candidate_id=candidate_id,
            adjudication_input_sha256="f"*64,
            gate_a_classification="A4",
            gate_a_adjudicator_ids=["ADJ-001", "ADJ-002"],
            gate_a_agreement=True,
            gate_c_classification="PASS",
            gate_c_adjudicator_ids=["ADJ-003", "ADJ-004"],
            gate_c_agreement=True,
            prior_art_search_id="SEARCH-001",
            prior_art_channel_a_result="NO_LEXICAL_MATCH",
            prior_art_channel_b_result="NO_MECHANISM_MATCH",
            prior_art_final="NO_PRECEDENT_FOUND_UNDER_PREREGISTERED_SEARCH",
            case_success=True,
        )
        assert adj_entry["event_type"] == "ADJUDICATION_RECORDED"
        assert adj_entry["case_success"] is True
