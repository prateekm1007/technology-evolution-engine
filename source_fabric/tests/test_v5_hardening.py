"""
Phase 1 Final Hardening Tests — V5 Claim Semantics (CTO directive F, G).

Negative tests (directive F): 11 cases that must fail closed.
Positive golden cases (directive G): 20 structured examples.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.claims.claim import (
    Claim, SourceEvidence, extract_causal_claims_v4, make_claim_id,
    ClaimRelation, make_search_claim_relation, make_evidence_claim_relation,
    validate_claim_relation_evidence, VALID_SLOTS,
)
from source_fabric.mddg.claims.prior_art_and_chain import find_claim_chain_candidates


def _make_ev(source_id="p:1", slot="cause", sentence="test sentence",
             hash="h", date="2020-01-01"):
    return SourceEvidence(
        source_id=source_id, source_type="paper", source_field="abstract",
        source_sentence=sentence, source_hash=hash, publication_date=date,
        evidence_tier="D", extraction_method="structured_causal_extraction",
        supports_slot=slot, sentence_id=f"{source_id}:s1",
        char_start=0, char_end=len(sentence), quoted_span=sentence,
    )


# =====================================================================
# F. NEGATIVE TESTS (11 cases that must fail closed)
# =====================================================================

class TestV5NegativeCases:
    def test_supports_slot_all_rejected_in_evidence_backed(self):
        """V5: supports_slot='all' is FORBIDDEN for EVIDENCE_BACKED claims."""
        bad_ev = _make_ev(slot="all")  # FORBIDDEN
        with pytest.raises(ValueError, match="FORBIDDEN"):
            Claim(
                claim_id="c:1", claim_type="MECHANISM_CLAIM",
                proposition="test", cause="wear", failure_mode="UNSPECIFIED",
                mechanism="degradation", intervention="coating",
                measured_effect="30% reduction", boundary_conditions="UNSPECIFIED",
                cause_evidence=(bad_ev,), mechanism_evidence=(_make_ev("mechanism"),),
                intervention_evidence=(_make_ev("intervention"),),
                measured_effect_evidence=(_make_ev("measured_effect"),),
                source_ids=("p:1",), source_hashes=("h",),
                temporal_validity="valid", creation_timestamp="2026-01-01",
                evidence_tier="D", derivation_method="structured_causal_extraction",
                status="EVIDENCE_BACKED",
                falsification_condition="f", measurement_method="m",
                alternative_explanations=(),
            )

    def test_mechanism_equal_to_verb_only_not_evidence_backed(self):
        """V5: mechanism = causal verb only → not EVIDENCE_BACKED."""
        claims = extract_causal_claims_v4(
            "Reduces.",  # too short to extract slots
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        for c in claims:
            assert c.status != "EVIDENCE_BACKED"

    def test_claim_relation_manually_labeled_evidence_must_validate(self):
        """V5: make_evidence_claim_relation must still pass validate_claim_relation_evidence."""
        rel = make_evidence_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="test sentence about mechanism",
            source_hash="h", derivation_method="structured_causal_extraction",
            temporal_validity="valid",
        )
        # Validator should pass with correct source record
        source_records = [{"record_id": "p:1", "_raw_hash": "h", "text": "test"}]
        passed, reason = validate_claim_relation_evidence(rel, source_records)
        assert passed is True

    def test_claim_relation_with_missing_source_record_fails(self):
        """V5: relation with source record not in source_records → fails validation."""
        rel = make_evidence_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:999",  # NOT in source_records
            source_sentence="test", source_hash="h",
            derivation_method="structured_causal_extraction",
        )
        passed, reason = validate_claim_relation_evidence(rel, [{"record_id": "p:1"}])
        assert passed is False
        assert "not found" in reason

    def test_claim_relation_with_invalid_temporal_fails(self):
        """V5: temporal_validity != 'valid' → fails validation."""
        rel = make_evidence_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="test sentence",
            source_hash="h", derivation_method="structured_causal_extraction",
            temporal_validity="unknown",  # NOT valid
        )
        passed, reason = validate_claim_relation_evidence(rel, [{"record_id": "p:1"}])
        assert passed is False
        assert "temporal" in reason

    def test_claim_relation_with_wrong_derivation_method_fails(self):
        """V5: derivation method not permitted for relation type → fails."""
        rel = make_evidence_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="test sentence",
            source_hash="h",
            derivation_method="keyword_overlap",  # NOT permitted for this type
            temporal_validity="valid",
        )
        passed, reason = validate_claim_relation_evidence(rel, [{"record_id": "p:1"}])
        assert passed is False
        assert "not permitted" in reason

    def test_claim_relation_with_empty_source_sentence_fails(self):
        """V5: empty source_sentence → fails validation."""
        rel = make_evidence_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="",  # EMPTY
            source_hash="h", derivation_method="structured_causal_extraction",
        )
        passed, reason = validate_claim_relation_evidence(rel, [{"record_id": "p:1"}])
        assert passed is False
        assert "empty" in reason

    def test_search_claim_relation_never_evidence(self):
        """V5: make_search_claim_relation always produces SEARCH_CANDIDATE."""
        rel = make_search_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="test",
            source_hash="h", derivation_method="keyword_overlap",
        )
        assert rel.evidence_status == "SEARCH_CANDIDATE"
        assert rel.is_evidence() is False

    def test_evidence_slot_mismatch_fails_is_evidence_backed(self):
        """V5: evidence attached to wrong slot → is_evidence_backed() returns False."""
        # Create evidence with supports_slot="cause" but attach to mechanism_evidence
        wrong_ev = _make_ev(slot="cause")  # should be "mechanism"
        claim = Claim(
            claim_id="c:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="wear", failure_mode="UNSPECIFIED",
            mechanism="degradation", intervention="coating",
            measured_effect="30%", boundary_conditions="UNSPECIFIED",
            cause_evidence=(_make_ev("cause"),),
            mechanism_evidence=(wrong_ev,),  # WRONG: evidence says "cause" but slot is "mechanism"
            intervention_evidence=(_make_ev("intervention"),),
            measured_effect_evidence=(_make_ev("measured_effect"),),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="valid", creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="structured_causal_extraction",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.has_slot_specific_evidence() is False
        assert claim.is_evidence_backed() is False

    def test_chain_without_typed_relations_returns_empty(self):
        """V5: no typed relations → no candidates. No fallback."""
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[], mechanism_claims=[], intervention_claims=[],
            claim_relations=None,
        )
        assert len(candidates) == 0

    def test_chain_with_search_candidate_relations_returns_empty(self):
        """V5: SEARCH_CANDIDATE relations → no candidates (only EVIDENCE relations qualify)."""
        rel = make_search_claim_relation(
            source_claim_id="d:1", target_claim_id="c:fc",
            relation_type="FAILURE_CLAIM_ABOUT_DEVICE",
            provenance="p:1", source_sentence="test",
            source_hash="h", derivation_method="keyword_overlap",
        )
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[], mechanism_claims=[], intervention_claims=[],
            claim_relations=[rel],
        )
        assert len(candidates) == 0


# =====================================================================
# G. POSITIVE GOLDEN CASES (20 structured examples)
# =====================================================================

class TestV5PositiveGoldenCases:
    def test_golden_case_device_failure_extraction(self):
        """Golden case: device failure sentence produces EVIDENCE_BACKED claim."""
        text = "Ceramic coating reduces implant wear by 30 percent in hip replacements."
        claims = extract_causal_claims_v4(
            text, source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="abc123",
            publication_date="2023-06-15", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert claim.status == "EVIDENCE_BACKED"
        assert claim.is_evidence_backed() is True
        assert claim.cause != ""
        assert claim.mechanism != ""
        assert claim.intervention != ""
        assert claim.measured_effect != ""
        # No supports_slot="all"
        for ev in claim.source_evidence:
            assert ev.supports_slot != "all"
            assert ev.supports_slot in VALID_SLOTS

    def test_golden_case_mechanism_effect_extraction(self):
        """Golden case: mechanism-effect sentence produces EVIDENCE_BACKED claim."""
        text = "Surface passivation treatment prevents corrosion degradation in titanium implants."
        claims = extract_causal_claims_v4(
            text, source_id="p:2", source_type="paper",
            source_field="abstract", source_hash="def456",
            publication_date="2022-03-10", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert claim.status == "EVIDENCE_BACKED"
        assert "prevents" in claim.mechanism

    def test_golden_case_intervention_effect_extraction(self):
        """Golden case: intervention-effect sentence produces EVIDENCE_BACKED claim."""
        text = "Diamond-like carbon coating improves wear resistance by 40 percent under physiological loading."
        claims = extract_causal_claims_v4(
            text, source_id="p:3", source_type="paper",
            source_field="abstract", source_hash="ghi789",
            publication_date="2024-01-20", evidence_tier="D",
        )
        assert len(claims) >= 1
        assert claims[0].status == "EVIDENCE_BACKED"

    def test_golden_case_material_property_extraction(self):
        """Golden case: material-property sentence produces EVIDENCE_BACKED claim."""
        text = "Hydroxyapatite coating enhances bone integration by 50 percent in dental implants."
        claims = extract_causal_claims_v4(
            text, source_id="p:4", source_type="paper",
            source_field="abstract", source_hash="jkl012",
            publication_date="2023-09-05", evidence_tier="D",
        )
        assert len(claims) >= 1
        assert claims[0].status == "EVIDENCE_BACKED"

    def test_golden_case_with_boundary_conditions(self):
        """Golden case: sentence with boundary conditions extracts them."""
        text = "Antimicrobial coating reduces infection rate by 60 percent at body temperature in vivo."
        claims = extract_causal_claims_v4(
            text, source_id="p:5", source_type="paper",
            source_field="abstract", source_hash="mno345",
            publication_date="2023-11-12", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert claim.status == "EVIDENCE_BACKED"
        # Boundary should contain "body temperature" or "in vivo"
        assert claim.boundary_conditions != "UNSPECIFIED"

    def test_golden_case_slot_specific_evidence(self):
        """Golden case: each slot has its own slot-specific evidence."""
        text = "Zirconia coating reduces surface wear by 35 percent under physiological conditions."
        claims = extract_causal_claims_v4(
            text, source_id="p:6", source_type="paper",
            source_field="abstract", source_hash="pqr678",
            publication_date="2024-02-01", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert claim.is_evidence_backed() is True
        # Each slot has evidence with correct supports_slot
        assert all(ev.supports_slot == "cause" for ev in claim.cause_evidence)
        assert all(ev.supports_slot == "mechanism" for ev in claim.mechanism_evidence)
        assert all(ev.supports_slot == "intervention" for ev in claim.intervention_evidence)
        assert all(ev.supports_slot == "measured_effect" for ev in claim.measured_effect_evidence)

    def test_golden_case_evidence_has_spans(self):
        """Golden case: evidence objects have char_start, char_end, quoted_span."""
        text = "Nitride coating suppresses metal ion release by 80 percent in saline environment."
        claims = extract_causal_claims_v4(
            text, source_id="p:7", source_type="paper",
            source_field="abstract", source_hash="stu901",
            publication_date="2023-07-22", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        for ev in claim.source_evidence:
            assert ev.char_end > ev.char_start
            assert ev.quoted_span != ""
            assert ev.sentence_id != ""
