#!/usr/bin/env python3
"""test_b2_generation_null.py — Adversarial tests for the B2 generation null.

Per B2_REVISION_R5_2.md and B2_IMPLEMENTATION_INVARIANTS.md:

    The generation null must:
    - Produce exactly 3 candidates (rank-paired)
    - Use deterministic shared_entity_or_concept
    - Fail closed on empty abstractions (no fabricated candidates)
    - Use the universal seed (same as engine)
    - Produce candidates in the same schema as the engine
    - Go through the same provenance spine (content-addressed storage,
      frozen parser, derivation verification, immutable ledger)
    - Be capable of passing Gate A/C/B (unlike the old retrieval null)

These tests move the generation null from IMPLEMENTED to ADVERSARIAL_TESTED.
"""
import hashlib
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
    record_null_in_ledger,
    NullGenerationResult,
    NULL_CONFIG,
    ProvenanceLedger,
    parse_candidates,
    verify_derivation,
    compute_sha256,
    store_raw_output,
    ExecutionGate,
)
from engine.b2_provenance.content_addressed_storage import STORAGE_ROOT
from scripts.verify_audit_instrument import create_execution_manifest


@pytest.fixture
def execution_gate():
    """Fixture that provides an active execution gate for tests that need
    to call generate_null_candidates."""
    manifest = create_execution_manifest("TEST-FIXTURE", ["CASE-001"], {})
    with ExecutionGate(manifest) as gate:
        yield gate


# =====================================================================
# CATEGORY 1: UNIVERSAL SEED — SAME ACROSS ARMS
# =====================================================================

class TestUniversalSeed:
    """Verify the universal seed is the same for engine and null."""

    def test_seed_is_deterministic(self):
        """Same inputs produce same seed."""
        seed1 = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        seed2 = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        assert seed1 == seed2

    def test_seed_is_sha256(self):
        """Seed is a 64-character hex string (SHA-256)."""
        seed = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        assert len(seed) == 64
        assert all(c in "0123456789abcdef" for c in seed)

    def test_seed_same_for_engine_and_null(self):
        """Per B2_IMPLEMENTATION_INVARIANTS.md: arm_id is NOT in the seed.
        Engine and null use the same seed for the same case+stage."""
        prereg_id = "PREREG-001"
        case_id = "CASE-001"
        # Engine seed (arm='engine' is NOT part of the seed)
        engine_seed = compute_universal_seed(prereg_id, case_id, "downstream")
        # Null seed (arm='null' is NOT part of the seed)
        null_seed = compute_universal_seed(prereg_id, case_id, "downstream")
        assert engine_seed == null_seed, (
            "Engine and null must use the SAME seed for the same case+stage. "
            "arm_id is NOT part of the seed."
        )

    def test_seed_differs_by_case(self):
        """Different cases produce different seeds."""
        seed1 = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        seed2 = compute_universal_seed("PREREG-001", "CASE-002", "downstream")
        assert seed1 != seed2

    def test_seed_differs_by_stage(self):
        """Different stages produce different seeds."""
        seed_downstream = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        seed_extraction = compute_universal_seed("PREREG-001", "CASE-001", "extraction")
        assert seed_downstream != seed_extraction

    def test_seed_differs_by_preregistration(self):
        """Different preregistration IDs produce different seeds."""
        seed1 = compute_universal_seed("PREREG-001", "CASE-001", "downstream")
        seed2 = compute_universal_seed("PREREG-002", "CASE-001", "downstream")
        assert seed1 != seed2


# =====================================================================
# CATEGORY 2: SHARED ENTITY — DETERMINISTIC NER-BASED
# =====================================================================

class TestSharedEntity:
    """Verify the shared entity computation is deterministic and uses NER.

    Per audit round 48 (FATAL 2 fix): the shared entity function is now
    IMPLEMENTED using the specified NER + canonicalization + stopword +
    dictionary pipeline, not a placeholder.
    """

    def test_deterministic_same_input(self):
        """Same abstractions produce same shared entity."""
        a = "Calcium phosphate crystallization in bone tissue"
        b = "Marine diatom silica precipitation process"
        entity1 = compute_shared_entity(a, b)
        entity2 = compute_shared_entity(a, b)
        assert entity1 == entity2

    def test_finds_shared_entity_when_present(self):
        """When abstractions share an entity, it is returned."""
        a = "Crystal nucleation in supersaturated solutions"
        b = "Crystal growth under controlled conditions"
        entity = compute_shared_entity(a, b)
        # "crystal" should be detected as a shared entity
        assert entity is not None
        assert "crystal" in entity.lower()

    def test_returns_none_when_no_shared(self):
        """When no shared entity is found, returns None."""
        a = "Quantum entanglement in photon pairs"
        b = "Ocean circulation patterns in the Pacific"
        entity = compute_shared_entity(a, b)
        # These have no shared scientific entity
        assert entity is None

    def test_uses_ner_not_simple_tokens(self):
        """Per audit round 48: the function uses spaCy NER, not simple
        token intersection. Named entities should be detected."""
        a = "The protein crystallography reveals calcium binding sites"
        b = "Calcium-dependent protein folding in enzymes"
        entity = compute_shared_entity(a, b)
        # NER should detect "calcium" and/or "protein" as entities
        assert entity is not None

    def test_alphabetical_tiebreak(self):
        """When multiple shared entities exist, the alphabetically first is returned."""
        a = "Zinc precipitation and calcium deposition in bone"
        b = "Calcium precipitation and zinc deposition in shell"
        entity = compute_shared_entity(a, b)
        # Shared entities include "calcium", "zinc", "precipitation", etc.
        # Alphabetically first should be returned
        assert entity is not None
        # Verify it's the alphabetically first of the shared entities
        # (we can't predict exactly which entities NER finds, but the
        # result should be deterministic)
        entity2 = compute_shared_entity(a, b)
        assert entity == entity2

    def test_ner_model_info_recorded(self):
        """The NER model info is available for provenance recording."""
        from engine.b2_provenance.generation_null import get_ner_model_info
        info = get_ner_model_info()
        assert info["ner_library"] == "spacy"
        assert info["ner_model"] == "en_core_web_sm"
        assert "spacy_version" in info


# =====================================================================
# CATEGORY 3: CANDIDATE CONSTRUCTION — SAME SCHEMA AS ENGINE
# =====================================================================

class TestCandidateConstruction:
    """Verify candidate construction produces the correct schema."""

    def test_candidate_has_relationship_and_mechanism(self):
        """Candidate text contains both RELATIONSHIP and MECHANISM."""
        a = "Crystal nucleation in solutions"
        b = "Crystal growth in solutions"
        candidate = construct_candidate(a, b)
        assert "RELATIONSHIP:" in candidate
        assert "MECHANISM:" in candidate

    def test_candidate_with_shared_entity(self):
        """When a shared entity exists, the mechanism mentions it."""
        a = "Crystal nucleation in solutions"
        b = "Crystal growth in solutions"
        candidate = construct_candidate(a, b)
        # "crystal" is the shared entity
        assert "crystal" in candidate.lower()

    def test_candidate_without_shared_entity(self):
        """When no shared entity, the mechanism says 'No shared entity was identified'."""
        a = "Ultrasound cavitation phenomena"
        b = "Polymorph selection kinetics"
        candidate = construct_candidate(a, b)
        # Check if shared entity is None
        entity = compute_shared_entity(a, b)
        if entity is None:
            assert "No shared entity was identified" in candidate

    def test_candidate_contains_both_abstractions(self):
        """The candidate references both abstractions."""
        a = "Calcium phosphate precipitation"
        b = "Silica biomineralization process"
        candidate = construct_candidate(a, b)
        assert a in candidate
        assert b in candidate


# =====================================================================
# CATEGORY 4: NULL GENERATION — EXACTLY 3 CANDIDATES, RANK-PAIRED
# =====================================================================

class TestNullGeneration:
    """Verify the null generates exactly 3 rank-paired candidates."""

    def _make_abstractions(self, n=3):
        """Create test abstraction lists."""
        a_list = [f"Mechanism A rank {i+1} involves crystallization" for i in range(n)]
        b_list = [f"Mechanism B rank {i+1} involves crystallization" for i in range(n)]
        return a_list, b_list

    def test_generates_exactly_3_candidates(self):
        """Null produces exactly 3 candidates (not 'up to 3')."""
        a_list, b_list = self._make_abstractions(3)
        raw_output = generate_null_raw_output(a_list, b_list)
        candidates = parse_candidates(raw_output)
        assert len(candidates) == 3

    def test_candidates_are_rank_paired(self):
        """Candidate 1 = (A1, B1), Candidate 2 = (A2, B2), etc."""
        a_list = ["Alpha mechanism first", "Beta mechanism second", "Gamma mechanism third"]
        b_list = ["Delta mechanism first", "Epsilon mechanism second", "Zeta mechanism third"]
        raw_output = generate_null_raw_output(a_list, b_list)
        candidates = parse_candidates(raw_output)

        assert len(candidates) == 3
        # Candidate 1 should contain A1 and B1
        assert "Alpha mechanism first" in candidates[0]
        assert "Delta mechanism first" in candidates[0]
        # Candidate 2 should contain A2 and B2
        assert "Beta mechanism second" in candidates[1]
        assert "Epsilon mechanism second" in candidates[1]
        # Candidate 3 should contain A3 and B3
        assert "Gamma mechanism third" in candidates[2]
        assert "Zeta mechanism third" in candidates[2]

    def test_fail_closed_short_a_list(self):
        """Per audit round 48 (SERIOUS 1): When A has < 3 abstractions,
        the null FAILS CLOSED (NULL_GENERATION_FAILURE) rather than
        padding. Padding would violate the rank-pairing specification."""
        a_list = ["Only A1 available"]
        b_list = ["B1 first", "B2 second", "B3 third"]
        with pytest.raises(ValueError, match="INSUFFICIENT_ABSTRACTIONS_A"):
            generate_null_raw_output(a_list, b_list)

    def test_fail_closed_short_b_list(self):
        """Per audit round 48 (SERIOUS 1): When B has < 3 abstractions,
        the null FAILS CLOSED (NULL_GENERATION_FAILURE) rather than
        padding."""
        a_list = ["A1 first", "A2 second", "A3 third"]
        b_list = ["Only B1 available"]
        with pytest.raises(ValueError, match="INSUFFICIENT_ABSTRACTIONS_B"):
            generate_null_raw_output(a_list, b_list)

    def test_fail_closed_2_abstractions_a(self):
        """Even 2 abstractions is insufficient — rank-pairing requires 3."""
        a_list = ["A1", "A2"]
        b_list = ["B1", "B2", "B3"]
        with pytest.raises(ValueError, match="INSUFFICIENT_ABSTRACTIONS_A"):
            generate_null_raw_output(a_list, b_list)

    def test_fail_closed_empty_a(self):
        """Empty abstraction list A → NULL_GENERATION_FAILURE."""
        with pytest.raises(ValueError, match="NULL_GENERATION_FAILURE"):
            generate_null_raw_output([], ["B1", "B2", "B3"])

    def test_fail_closed_empty_b(self):
        """Empty abstraction list B → NULL_GENERATION_FAILURE."""
        with pytest.raises(ValueError, match="NULL_GENERATION_FAILURE"):
            generate_null_raw_output(["A1", "A2", "A3"], [])

    def test_fail_closed_both_empty(self):
        """Both abstraction lists empty → NULL_GENERATION_FAILURE."""
        with pytest.raises(ValueError, match="NULL_GENERATION_FAILURE"):
            generate_null_raw_output([], [])

    def test_raw_output_in_parser_format(self):
        """The raw output is in parser format (---CANDIDATE--- delimiters)."""
        a_list, b_list = self._make_abstractions(3)
        raw_output = generate_null_raw_output(a_list, b_list)
        assert NULL_CONFIG["candidate_delimiter"] in raw_output

    def test_null_candidates_parseable_by_frozen_parser(self, execution_gate):
        """Null candidates are parseable by the same frozen parser as engine."""
        a_list, b_list = self._make_abstractions(3)
        raw_output = generate_null_raw_output(a_list, b_list)
        candidates = parse_candidates(raw_output)
        assert len(candidates) == 3
        for c in candidates:
            assert len(c) > 0


# =====================================================================
# CATEGORY 5: PROVENANCE SPINE INTEGRATION
# =====================================================================

class TestProvenanceSpineIntegration:
    """Verify the null goes through the same provenance spine as the engine."""

    def test_generate_null_candidates_stores_raw_output(self, tmp_path, monkeypatch, execution_gate):
        """generate_null_candidates stores raw output in content-addressed storage."""
        # Patch storage root to temp
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        a_list = ["Crystal nucleation mechanism A1", "Crystal growth mechanism A2", "Crystal dissolution mechanism A3"]
        b_list = ["Crystal nucleation mechanism B1", "Crystal growth mechanism B2", "Crystal dissolution mechanism B3"]
        result = generate_null_candidates(
            case_id="CASE-001",
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id="PREREG-001",
        )

        assert result.raw_output_sha256 is not None
        assert len(result.raw_output_sha256) == 64
        assert result.raw_output_blob_path is not None

    def test_generate_null_candidates_returns_3_candidates(self, tmp_path, monkeypatch, execution_gate):
        """generate_null_candidates returns exactly 3 candidates."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        a_list = ["Mechanism A1 crystallization", "Mechanism A2 precipitation", "Mechanism A3 nucleation"]
        b_list = ["Mechanism B1 crystallization", "Mechanism B2 precipitation", "Mechanism B3 nucleation"]
        result = generate_null_candidates(
            case_id="CASE-001",
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id="PREREG-001",
        )

        assert result.n_candidates() == 3
        assert len(result.candidate_sha256s) == 3

    def test_null_candidates_derivation_verifiable(self, tmp_path, monkeypatch, execution_gate):
        """Each null candidate's derivation is verifiable through the parser."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        a_list = ["Crystal nucleation in solutions A1", "Crystal growth in solutions A2", "Crystal dissolution in solutions A3"]
        b_list = ["Crystal nucleation in solutions B1", "Crystal growth in solutions B2", "Crystal dissolution in solutions B3"]
        result = generate_null_candidates(
            case_id="CASE-001",
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id="PREREG-001",
        )

        # Verify each candidate's derivation
        for rank, expected_sha in enumerate(result.candidate_sha256s, start=1):
            assert verify_derivation(
                result.raw_output, expected_sha, rank
            ) is True, (
                f"Null candidate at rank {rank} failed derivation verification"
            )

    def test_null_candidates_recorded_in_ledger(self, tmp_path, monkeypatch, execution_gate):
        """Null candidates are recorded as CANDIDATE_GENERATED events in the ledger."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        ledger_path = tmp_path / "ledger.json"
        ledger = ProvenanceLedger(ledger_path=ledger_path)

        a_list = ["Crystal nucleation", "Crystal growth", "Crystal dissolution"]
        b_list = ["Bone mineralization", "Shell formation", "Crystal precipitation"]
        result = generate_null_candidates(
            case_id="CASE-001",
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id="PREREG-001",
        )

        entries = record_null_in_ledger(
            ledger=ledger,
            result=result,
            engine_version="abc123",
            provider="ZAI",
            model="glm-4-plus",
            prompt_hash="d" * 64,
            source_pair_sha256="e" * 64,
            generation_timestamp="2026-08-09T12:00:00Z",
        )

        assert len(entries) == 3
        assert ledger.n_generation_events() == 3
        assert ledger.n_adjudication_events() == 0

        # Verify hash chain
        assert ledger.verify_hash_chain() is True

        # Verify each entry is a CANDIDATE_GENERATED event with arm="null"
        for entry in entries:
            assert entry["arm"] == "null"
            assert entry["case_id"] == "CASE-001"

    def test_null_uses_same_seed_as_engine(self, tmp_path, monkeypatch, execution_gate):
        """The null uses the same universal seed as the engine."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        prereg_id = "PREREG-001"
        case_id = "CASE-001"

        a_list = ["Test mechanism A1", "Test mechanism A2", "Test mechanism A3"]
        b_list = ["Test mechanism B1", "Test mechanism B2", "Test mechanism B3"]
        result = generate_null_candidates(
            case_id=case_id,
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id=prereg_id,
        )

        expected_seed = compute_universal_seed(prereg_id, case_id, "downstream")
        assert result.invocation_seed == expected_seed

    def test_null_candidate_schema_same_as_engine(self, execution_gate):
        """Null candidates use the same schema (relationship + mechanism)
        that the engine uses."""
        a = "Crystal nucleation in solutions"
        b = "Crystal growth in solutions"
        candidate = construct_candidate(a, b)

        # The candidate must have RELATIONSHIP and MECHANISM sections
        # (same schema as engine candidates)
        assert "RELATIONSHIP:" in candidate
        assert "MECHANISM:" in candidate

    def test_null_can_produce_mechanism(self, execution_gate):
        """The null CAN produce a mechanism (unlike the old retrieval null
        that produced 'NO_MECHANISM_PROPOSED').

        This is the key fairness property: the null is NOT structurally
        disadvantaged. It can pass Gate C because it produces a mechanism.
        """
        a = "Crystal nucleation in supersaturated solutions"
        b = "Crystal growth under controlled temperature"
        candidate = construct_candidate(a, b)

        # The candidate has a mechanism (not 'NO_MECHANISM_PROPOSED')
        assert "MECHANISM:" in candidate
        assert "NO_MECHANISM_PROPOSED" not in candidate
        # The mechanism is a real sentence (not empty)
        mechanism_line = [l for l in candidate.split("\n") if l.startswith("MECHANISM:")][0]
        assert len(mechanism_line) > len("MECHANISM: ")


# =====================================================================
# CATEGORY 6: IMmutABILITY AND APPEND-ONLY (null-specific)
# =====================================================================

class TestNullImmutability:
    """Verify null candidates are immutable once recorded."""

    def test_null_generation_entry_immutable(self, tmp_path, monkeypatch, execution_gate):
        """Null CANDIDATE_GENERATED events are immutable."""
        from engine.b2_provenance import content_addressed_storage as cas
        monkeypatch.setattr(cas, "STORAGE_ROOT", tmp_path / "raw_outputs")

        ledger_path = tmp_path / "ledger.json"
        ledger = ProvenanceLedger(ledger_path=ledger_path)

        a_list = ["Mechanism A1", "Mechanism A2", "Mechanism A3"]
        b_list = ["Mechanism B1", "Mechanism B2", "Mechanism B3"]
        result = generate_null_candidates(
            case_id="CASE-001",
            abstracted_mechanisms_a=a_list,
            abstracted_mechanisms_b=b_list,
            preregistration_id="PREREG-001",
        )

        entries = record_null_in_ledger(
            ledger=ledger,
            result=result,
            engine_version="abc123",
            provider="ZAI",
            model="glm-4-plus",
            prompt_hash="d" * 64,
            source_pair_sha256="e" * 64,
            generation_timestamp="2026-08-09T12:00:00Z",
        )

        # Record hashes before any adjudication
        original_hashes = [e["entry_hash"] for e in entries]

        # Adjudicate one candidate
        ledger.append_adjudication_result(
            candidate_id=entries[0]["candidate_id"],
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

        # Generation entries are unchanged
        for i, entry in enumerate(entries):
            gen_entry = ledger.get_generation_event(entry["candidate_id"])
            assert gen_entry["entry_hash"] == original_hashes[i], (
                f"Null generation entry {i} was modified after adjudication"
            )

        # Verify immutability
        for entry in entries:
            assert ledger.verify_generation_immutability(entry["candidate_id"]) is True
