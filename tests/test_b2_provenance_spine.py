#!/usr/bin/env python3
"""test_b2_provenance_spine.py — Adversarial tests for the B2 provenance spine.

Tests the three components of the provenance spine:
1. Content-addressed storage (tamper detection)
2. Frozen parser (determinism, derivation verification)
3. Append-only hash-chained ledger (chain integrity, tamper detection)

Per B2_IMPLEMENTATION_INVARIANTS.md and the acceptance ladder:
    SPECIFIED → IMPLEMENTED → ADVERSARIAL_TESTED → FREEZE_VERIFIED

These tests move the provenance spine from IMPLEMENTED to ADVERSARIAL_TESTED.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.b2_provenance import (
    compute_sha256,
    store_raw_output,
    retrieve_raw_output,
    verify_blob_integrity,
    blob_exists,
    parse_candidates,
    get_candidate_by_rank,
    compute_candidate_sha256,
    verify_derivation,
    get_parser_sha256,
    get_parser_config_sha256,
    get_parser_version,
    ProvenanceLedger,
)
from engine.b2_provenance.content_addressed_storage import STORAGE_ROOT


# =====================================================================
# CATEGORY 1: CONTENT-ADDRESSED STORAGE — TAMPER DETECTION
# =====================================================================

class TestContentAddressedStorage:
    """Verify content-addressed storage detects tampering."""

    def test_store_and_retrieve(self):
        """Storing raw output and retrieving it returns identical bytes."""
        raw = "This is a test raw output for case CASE-001 engine."
        blob_path, sha = store_raw_output("CASE-001", "engine", raw)
        assert blob_exists(sha)
        retrieved = retrieve_raw_output(sha)
        assert retrieved == raw.encode("utf-8")

    def test_sha256_matches_content(self):
        """The returned SHA-256 matches the content."""
        raw = "Test content for hash verification."
        blob_path, sha = store_raw_output("CASE-TEST", "engine", raw)
        expected_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        assert sha == expected_sha

    def test_filename_is_sha256(self):
        """The blob filename IS the SHA-256 of the content."""
        raw = "Content-addressed storage test."
        blob_path, sha = store_raw_output("CASE-FN", "engine", raw)
        assert Path(blob_path).name == f"{sha}.txt"

    def test_deduplication_same_content(self):
        """Storing the same content twice returns the same path (dedup)."""
        raw = "Deduplication test content."
        path1, sha1 = store_raw_output("CASE-DEDUP-1", "engine", raw)
        path2, sha2 = store_raw_output("CASE-DEDUP-2", "null", raw)
        assert path1 == path2
        assert sha1 == sha2

    def test_different_content_different_path(self):
        """Different content produces different paths."""
        raw1 = "Content A."
        raw2 = "Content B."
        _, sha1 = store_raw_output("CASE-DIFF-1", "engine", raw1)
        _, sha2 = store_raw_output("CASE-DIFF-2", "engine", raw2)
        assert sha1 != sha2

    def test_tamper_detection(self, tmp_path, monkeypatch):
        """If a blob is modified after storage, verify_blob_integrity
        raises RuntimeError (tampering detected).

        Uses a temporary storage root to avoid state leakage between
        test runs."""
        # Patch STORAGE_ROOT to use a temp directory
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")
        # Also patch the imported reference in the test module's namespace
        monkeypatch.setattr(
            "engine.b2_provenance.content_addressed_storage.STORAGE_ROOT",
            tmp_path / "raw_outputs",
        )

        raw = "Original content that will be tampered."
        blob_path, sha = store_raw_output("CASE-TAMPER", "engine", raw)

        # Tamper: modify the blob.
        Path(blob_path).write_bytes(b"TAMPERED CONTENT")

        with pytest.raises(RuntimeError, match="TAMPERING DETECTED"):
            retrieve_raw_output(sha)

        with pytest.raises(RuntimeError, match="TAMPERING DETECTED"):
            verify_blob_integrity(sha)

    def test_empty_output_rejected(self):
        """Empty raw output is rejected."""
        with pytest.raises(ValueError, match="empty raw output"):
            store_raw_output("CASE-EMPTY", "engine", "")

    def test_retrieve_nonexistent_returns_none(self):
        """Retrieving a non-existent blob returns None."""
        result = retrieve_raw_output("0" * 64)
        assert result is None

    def test_verify_nonexistent_returns_false(self):
        """Verifying a non-existent blob returns False (no tampering,
        just missing)."""
        result = verify_blob_integrity("0" * 64)
        assert result is False


# =====================================================================
# CATEGORY 2: FROZEN PARSER — DETERMINISM AND DERIVATION
# =====================================================================

class TestFrozenParser:
    """Verify the parser is deterministic and derivation is verifiable."""

    TEST_RAW_OUTPUT = """---PREAMBLE---
This is the engine's raw output preamble.

---CANDIDATE---
Candidate 1: This is the first candidate mechanism.
It proposes a cross-domain relationship.

---CANDIDATE---
Candidate 2: This is the second candidate mechanism.
It proposes a different relationship.

---CANDIDATE---
Candidate 3: This is the third candidate mechanism.
Yet another proposal.

---CANDIDATE---
Candidate 4: This should be discarded (max 3).
"""

    def test_parser_is_deterministic(self):
        """Same input always produces same output."""
        results1 = parse_candidates(self.TEST_RAW_OUTPUT)
        results2 = parse_candidates(self.TEST_RAW_OUTPUT)
        assert results1 == results2

    def test_max_three_candidates(self):
        """Parser returns at most 3 candidates."""
        candidates = parse_candidates(self.TEST_RAW_OUTPUT)
        assert len(candidates) == 3

    def test_fourth_candidate_discarded(self):
        """The 4th candidate is discarded (max 3 rule)."""
        candidates = parse_candidates(self.TEST_RAW_OUTPUT)
        assert "discarded" not in candidates[2].lower()

    def test_get_candidate_by_rank(self):
        """get_candidate_by_rank returns the correct candidate."""
        c1 = get_candidate_by_rank(self.TEST_RAW_OUTPUT, 1)
        c2 = get_candidate_by_rank(self.TEST_RAW_OUTPUT, 2)
        c3 = get_candidate_by_rank(self.TEST_RAW_OUTPUT, 3)
        c4 = get_candidate_by_rank(self.TEST_RAW_OUTPUT, 4)

        assert c1 is not None and "first" in c1
        assert c2 is not None and "second" in c2
        assert c3 is not None and "third" in c3
        assert c4 is None  # no 4th candidate

    def test_compute_candidate_sha256(self):
        """compute_candidate_sha256 returns the correct hash."""
        c1 = get_candidate_by_rank(self.TEST_RAW_OUTPUT, 1)
        sha = compute_candidate_sha256(self.TEST_RAW_OUTPUT, 1)
        expected = hashlib.sha256(c1.encode("utf-8")).hexdigest()
        assert sha == expected

    def test_derivation_verification_success(self):
        """verify_derivation succeeds when the candidate hash matches."""
        sha = compute_candidate_sha256(self.TEST_RAW_OUTPUT, 1)
        assert verify_derivation(self.TEST_RAW_OUTPUT, sha, 1) is True

    def test_derivation_verification_wrong_hash(self):
        """verify_derivation fails when the candidate hash doesn't match."""
        wrong_sha = "0" * 64
        with pytest.raises(AssertionError, match="Derivation verification FAILED"):
            verify_derivation(self.TEST_RAW_OUTPUT, wrong_sha, 1)

    def test_derivation_verification_no_candidate_at_rank(self):
        """verify_derivation fails when no candidate at the given rank."""
        sha = compute_candidate_sha256(self.TEST_RAW_OUTPUT, 1)
        with pytest.raises(AssertionError, match="no candidate at rank 4"):
            verify_derivation(self.TEST_RAW_OUTPUT, sha, 4)

    def test_parser_sha256_stable(self):
        """Parser SHA-256 is stable across calls (same source = same hash)."""
        sha1 = get_parser_sha256()
        sha2 = get_parser_sha256()
        assert sha1 == sha2

    def test_parser_config_sha256_stable(self):
        """Parser config SHA-256 is stable across calls."""
        sha1 = get_parser_config_sha256()
        sha2 = get_parser_config_sha256()
        assert sha1 == sha2

    def test_parser_version_recorded(self):
        """get_parser_version returns all version info."""
        version = get_parser_version()
        assert "parser_sha256" in version
        assert "parser_config_sha256" in version
        assert "parser_source_path" in version
        assert "parser_config" in version

    def test_derivation_verification_with_parser_version(self):
        """verify_derivation checks parser version when expected hashes
        are provided."""
        sha = compute_candidate_sha256(self.TEST_RAW_OUTPUT, 1)
        parser_sha = get_parser_sha256()
        config_sha = get_parser_config_sha256()

        # Correct parser version → passes
        assert verify_derivation(
            self.TEST_RAW_OUTPUT, sha, 1,
            expected_parser_sha256=parser_sha,
            expected_parser_config_sha256=config_sha,
        ) is True

        # Wrong parser version → fails
        with pytest.raises(AssertionError, match="Parser version mismatch"):
            verify_derivation(
                self.TEST_RAW_OUTPUT, sha, 1,
                expected_parser_sha256="0" * 64,
            )

    def test_empty_raw_output_rejected(self):
        """Empty raw output is rejected by the parser."""
        with pytest.raises(ValueError, match="empty raw output"):
            parse_candidates("")

    def test_no_candidates_returns_empty(self):
        """Raw output with no candidate delimiters returns empty list."""
        candidates = parse_candidates("Just preamble, no candidates.")
        assert candidates == []

    def test_overlong_candidate_rejected_not_truncated(self):
        """Per audit round 46 (SERIOUS): overlong candidates are REJECTED,
        not truncated. The parser must NOT transform candidates — it
        only selects eligible ones. Truncation would silently modify
        the candidate before hashing, creating a provenance ambiguity."""
        # Create a candidate that exceeds max_candidate_length (10000)
        overlong_text = "X" * 10001
        raw_output = f"---PREAMBLE---\n---CANDIDATE---\n{overlong_text}\n---CANDIDATE---\nNormal length candidate here."
        candidates = parse_candidates(raw_output)

        # The overlong candidate was REJECTED (not truncated)
        assert len(candidates) == 1
        assert candidates[0] == "Normal length candidate here."
        # The overlong text is NOT present (would be if truncated)
        assert "X" * 10000 not in candidates[0]

    def test_parser_does_not_modify_candidate_text(self):
        """The parser must return candidates EXACTLY as they appear in
        the raw output (after stripping whitespace). No truncation,
        no repair, no silent modification."""
        original = "This is an exact candidate that must not be modified."
        raw_output = f"---PREAMBLE---\n---CANDIDATE---\n{original}\n"
        candidates = parse_candidates(raw_output)
        assert len(candidates) == 1
        assert candidates[0] == original  # exact match, no modification


# =====================================================================
# CATEGORY 3: PROVENANCE LEDGER — HASH CHAIN AND TAMPER DETECTION
# =====================================================================

class TestProvenanceLedger:
    """Verify the append-only hash-chained ledger."""

    def _create_test_ledger(self, tmp_path):
        """Create a test ledger in a temporary path."""
        ledger_path = tmp_path / "test_ledger.json"
        return ProvenanceLedger(ledger_path=ledger_path)

    def _make_test_entry_params(self, case_id="CASE-001", arm="engine", rank=1):
        """Create test parameters for a ledger entry."""
        return {
            "case_id": case_id,
            "arm": arm,
            "candidate_rank": rank,
            "raw_output_sha256": "a" * 64,
            "raw_output_blob_path": "/provenance/raw_outputs/aaa.txt",
            "candidate_sha256": "b" * 64,
            "candidate_text": "Test candidate text.",
            "generation_timestamp": "2026-08-09T12:00:00Z",
            "engine_version": "abc123",
            "provider": "ZAI",
            "model": "glm-4-plus",
            "prompt_hash": "c" * 64,
            "source_pair_sha256": "d" * 64,
            "invocation_seed": "e" * 64,
        }

    def test_append_and_retrieve(self, tmp_path):
        """Appending an entry and retrieving it works."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        entry = ledger.append_candidate_entry(**params)

        assert entry["candidate_id"] == "CASE-001-ENGINE-CAND-001"
        assert entry["case_id"] == "CASE-001"
        assert entry["arm"] == "engine"
        assert entry["prev_entry_hash"] == "GENESIS"
        assert "entry_hash" in entry

        # Retrieve
        retrieved = ledger.get_entry("CASE-001-ENGINE-CAND-001")
        assert retrieved is not None
        assert retrieved["candidate_id"] == "CASE-001-ENGINE-CAND-001"

    def test_hash_chain_genesis(self, tmp_path):
        """First entry's prev_entry_hash is 'GENESIS'."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        entry = ledger.append_candidate_entry(**params)
        assert entry["prev_entry_hash"] == "GENESIS"

    def test_hash_chain_linkage(self, tmp_path):
        """Second entry's prev_entry_hash matches first entry's entry_hash."""
        ledger = self._create_test_ledger(tmp_path)

        params1 = self._make_test_entry_params(rank=1)
        entry1 = ledger.append_candidate_entry(**params1)

        params2 = self._make_test_entry_params(rank=2)
        entry2 = ledger.append_candidate_entry(**params2)

        assert entry2["prev_entry_hash"] == entry1["entry_hash"]

    def test_verify_hash_chain_intact(self, tmp_path):
        """verify_hash_chain returns True for an unmodified ledger."""
        ledger = self._create_test_ledger(tmp_path)
        for rank in [1, 2, 3]:
            params = self._make_test_entry_params(rank=rank)
            ledger.append_candidate_entry(**params)

        assert ledger.verify_hash_chain() is True

    def test_tamper_detection_modified_entry(self, tmp_path):
        """If an entry is modified after hashing, verify_hash_chain fails."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        entry = ledger.append_candidate_entry(**params)

        # Tamper: modify the entry directly (bypassing the ledger API)
        entry["candidate_text"] = "TAMPERED TEXT"

        with pytest.raises(AssertionError, match="Entry hash mismatch"):
            ledger.verify_hash_chain()

    def test_tamper_detection_broken_chain(self, tmp_path):
        """If prev_entry_hash is modified, verify_hash_chain fails."""
        ledger = self._create_test_ledger(tmp_path)
        params1 = self._make_test_entry_params(rank=1)
        entry1 = ledger.append_candidate_entry(**params1)

        params2 = self._make_test_entry_params(rank=2)
        entry2 = ledger.append_candidate_entry(**params2)

        # Tamper: break the chain
        entry2["prev_entry_hash"] = "TAMPERED"

        with pytest.raises(AssertionError, match="Hash chain broken"):
            ledger.verify_hash_chain()

    def test_append_only_no_overwrite(self, tmp_path):
        """Appending a duplicate entry raises ValueError (append-only)."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params(rank=1)
        ledger.append_candidate_entry(**params)

        with pytest.raises(ValueError, match="already exists"):
            ledger.append_candidate_entry(**params)

    def test_append_adjudication_result(self, tmp_path):
        """Adjudication creates a SEPARATE event (not a mutation of the
        generation entry). Per audit round 46 (FATAL): the generation
        entry must remain immutable."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        gen_entry = ledger.append_candidate_entry(**params)

        # Record the generation entry's hash BEFORE adjudication.
        gen_hash_before = gen_entry["entry_hash"]

        adj_entry = ledger.append_adjudication_result(
            candidate_id="CASE-001-ENGINE-CAND-001",
            adjudication_input_sha256="f" * 64,
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

        # The adjudication event is a SEPARATE entry.
        assert adj_entry["event_type"] == "ADJUDICATION_RECORDED"
        assert adj_entry["candidate_id"] == "CASE-001-ENGINE-CAND-001"
        assert adj_entry["gate_a_classification"] == "A4"
        assert adj_entry["case_success"] is True

        # The generation entry's hash has NOT changed (immutable).
        gen_entry_after = ledger.get_generation_event("CASE-001-ENGINE-CAND-001")
        assert gen_entry_after["entry_hash"] == gen_hash_before, (
            "Generation entry hash changed after adjudication — "
            "the generation record is supposed to be immutable."
        )

        # The generation entry does NOT contain adjudication fields.
        assert "gate_a_classification" not in gen_entry_after
        assert "case_success" not in gen_entry_after

        # The adjudication event is linked in the chain.
        assert adj_entry["prev_entry_hash"] == gen_hash_before

    def test_no_overwrite_adjudication(self, tmp_path):
        """Adjudication events cannot be duplicated (no double-adjudication)."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        ledger.append_candidate_entry(**params)

        adj_params = dict(
            candidate_id="CASE-001-ENGINE-CAND-001",
            adjudication_input_sha256="f" * 64,
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
        ledger.append_adjudication_result(**adj_params)

        # Second attempt should fail
        with pytest.raises(ValueError, match="already exists"):
            ledger.append_adjudication_result(**adj_params)

    def test_generation_entry_immutable_after_adjudication(self, tmp_path):
        """Per audit round 46 (FATAL): the generation entry must remain
        immutable after adjudication. This test verifies:

        1. The generation entry's hash is unchanged after adjudication
        2. The generation entry contains NO adjudication fields
        3. verify_generation_immutability() passes
        4. The adjudication is a separate event in the chain
        """
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        gen_entry = ledger.append_candidate_entry(**params)
        gen_hash = gen_entry["entry_hash"]

        # Adjudicate
        ledger.append_adjudication_result(
            candidate_id="CASE-001-ENGINE-CAND-001",
            adjudication_input_sha256="f" * 64,
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

        # 1. Generation hash unchanged
        gen_after = ledger.get_generation_event("CASE-001-ENGINE-CAND-001")
        assert gen_after["entry_hash"] == gen_hash

        # 2. No adjudication fields in generation entry
        for field in ["gate_a_classification", "gate_c_classification",
                       "case_success", "adjudication_input_sha256"]:
            assert field not in gen_after, (
                f"Generation entry contains adjudication field '{field}'"
            )

        # 3. verify_generation_immutability passes
        assert ledger.verify_generation_immutability("CASE-001-ENGINE-CAND-001") is True

        # 4. Adjudication is a separate event
        adj_entry = ledger.get_adjudication_event("CASE-001-ENGINE-CAND-001")
        assert adj_entry is not None
        assert adj_entry["event_type"] == "ADJUDICATION_RECORDED"
        assert adj_entry is not gen_after  # different objects

    def test_generation_immutability_detects_mutation(self, tmp_path):
        """If the generation entry is mutated after adjudication,
        verify_generation_immutability raises AssertionError."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        gen_entry = ledger.append_candidate_entry(**params)

        ledger.append_adjudication_result(
            candidate_id="CASE-001-ENGINE-CAND-001",
            adjudication_input_sha256="f" * 64,
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

        # Tamper: mutate the generation entry directly
        gen_entry["candidate_text"] = "TAMPERED"

        with pytest.raises(AssertionError, match="MODIFIED"):
            ledger.verify_generation_immutability("CASE-001-ENGINE-CAND-001")

    def test_adjudication_requires_generation_event(self, tmp_path):
        """Cannot adjudicate a candidate that was never generated."""
        ledger = self._create_test_ledger(tmp_path)

        with pytest.raises(KeyError, match="No CANDIDATE_GENERATED event"):
            ledger.append_adjudication_result(
                candidate_id="CASE-001-ENGINE-CAND-001",
                adjudication_input_sha256="f" * 64,
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

    def test_combined_record_merges_events(self, tmp_path):
        """get_combined_record merges generation + adjudication into
        a single view (without modifying the underlying events)."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        ledger.append_candidate_entry(**params)

        ledger.append_adjudication_result(
            candidate_id="CASE-001-ENGINE-CAND-001",
            adjudication_input_sha256="f" * 64,
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

        combined = ledger.get_combined_record("CASE-001-ENGINE-CAND-001")
        assert combined["candidate_id"] == "CASE-001-ENGINE-CAND-001"
        assert combined["gate_a_classification"] == "A4"
        assert combined["case_success"] is True
        # The underlying events are still separate
        assert ledger.n_generation_events() == 1
        assert ledger.n_adjudication_events() == 1

    def test_ledger_persists_to_disk(self, tmp_path):
        """The ledger persists entries to disk and reloads them."""
        ledger_path = tmp_path / "test_ledger.json"
        ledger = ProvenanceLedger(ledger_path=ledger_path)
        params = self._make_test_entry_params()
        ledger.append_candidate_entry(**params)

        # Create a new ledger instance pointing to the same path
        ledger2 = ProvenanceLedger(ledger_path=ledger_path)
        assert ledger2.n_entries() == 1
        entry = ledger2.get_entry("CASE-001-ENGINE-CAND-001")
        assert entry is not None

    def test_ledger_sha256_stable(self, tmp_path):
        """The ledger SHA-256 is stable for the same content."""
        ledger = self._create_test_ledger(tmp_path)
        params = self._make_test_entry_params()
        ledger.append_candidate_entry(**params)

        sha1 = ledger.get_ledger_sha256()
        sha2 = ledger.get_ledger_sha256()
        assert sha1 == sha2

    def test_ledger_sha256_changes_on_append(self, tmp_path):
        """The ledger SHA-256 changes when a new entry is appended."""
        ledger = self._create_test_ledger(tmp_path)
        params1 = self._make_test_entry_params(rank=1)
        ledger.append_candidate_entry(**params1)
        sha1 = ledger.get_ledger_sha256()

        params2 = self._make_test_entry_params(rank=2)
        ledger.append_candidate_entry(**params2)
        sha2 = ledger.get_ledger_sha256()

        assert sha1 != sha2

    def test_get_entries_for_case(self, tmp_path):
        """get_entries_for_case returns all entries for a case."""
        ledger = self._create_test_ledger(tmp_path)

        for rank in [1, 2, 3]:
            ledger.append_candidate_entry(
                **self._make_test_entry_params(rank=rank)
            )

        # Add a different case
        params2 = self._make_test_entry_params(case_id="CASE-002", rank=1)
        ledger.append_candidate_entry(**params2)

        case1_entries = ledger.get_entries_for_case("CASE-001")
        case2_entries = ledger.get_entries_for_case("CASE-002")

        assert len(case1_entries) == 3
        assert len(case2_entries) == 1

    def test_get_entries_for_case_filtered_by_arm(self, tmp_path):
        """get_entries_for_case with arm filter works."""
        ledger = self._create_test_ledger(tmp_path)

        # Engine entries
        for rank in [1, 2, 3]:
            ledger.append_candidate_entry(
                **self._make_test_entry_params(rank=rank, arm="engine")
            )

        # Null entries
        for rank in [1, 2, 3]:
            ledger.append_candidate_entry(
                **self._make_test_entry_params(rank=rank, arm="null")
            )

        engine_entries = ledger.get_entries_for_case("CASE-001", arm="engine")
        null_entries = ledger.get_entries_for_case("CASE-001", arm="null")

        assert len(engine_entries) == 3
        assert len(null_entries) == 3
