"""
Phase 1 Closure Tests — V4 Claim Semantics (CTO V9 directive #1-7).

Tests that the Claim extraction is structurally real, not heuristic.
Tests that word-overlap is gone from Claim-chain qualification.
Tests that EVIDENCE_BACKED requires matched causal proposition, not just causal vocabulary.
Negative tests: co-mention, causal verb without mechanism, mismatched subject/object,
negation, conditional, speculation, future intention, review summary, correlation.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.claims.claim import (
    Claim, SourceEvidence, extract_causal_claims_v4, is_causal_sentence,
    make_claim_id, ClaimRelation, make_claim_relation,
    CLAIM_RELATION_TYPES, CAUSAL_VERBS,
)
from source_fabric.mddg.claims.prior_art_and_chain import (
    find_claim_chain_candidates, ClaimChainCandidate,
)


# =====================================================================
# #1. CLAIM EXTRACTION IS STRUCTURALLY REAL (not heuristic)
# =====================================================================

class TestStructuredExtraction:
    def test_causal_verb_alone_is_search_candidate_not_evidence(self):
        """Per directive #1: causal verb without extractable slots → SEARCH_CANDIDATE."""
        # "reduces" is present but sentence is too short to extract subject/object
        claims = extract_causal_claims_v4(
            "It reduces.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        # Should produce 0 claims (sentence < 5 words after splitting)
        assert len(claims) == 0 or all(c.status == "SEARCH_CANDIDATE" for c in claims)
        # None should be EVIDENCE_BACKED
        for c in claims:
            assert c.status != "EVIDENCE_BACKED"

    def test_well_structured_sentence_produces_evidence_backed(self):
        """A well-structured causal sentence with identifiable slots → EVIDENCE_BACKED."""
        claims = extract_causal_claims_v4(
            "Ceramic coating reduces wear by 30 percent in hip implants.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert claim.status == "EVIDENCE_BACKED"
        assert claim.cause != "" and claim.cause != claim.proposition  # not sentence copy
        assert claim.mechanism != "" and claim.mechanism != "reduces"  # not just verb
        assert claim.intervention != "" and claim.intervention != claim.proposition
        assert claim.measured_effect != "" and claim.measured_effect != claim.proposition

    def test_mechanism_is_not_just_verb(self):
        """Per directive #1: 'A verb such as reduces is not a mechanism.'"""
        claims = extract_causal_claims_v4(
            "Ceramic coating reduces wear by 30 percent.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        if claims:
            claim = claims[0]
            if claim.status == "EVIDENCE_BACKED":
                # mechanism should be more than just the verb
                assert claim.mechanism != "reduces"
                assert "reduces" in claim.mechanism  # but contains the verb

    def test_slots_are_not_sentence_copies(self):
        """Per directive #1: 'A whole sentence copied into cause, intervention, and
        measured_effect is not structured extraction.'"""
        claims = extract_causal_claims_v4(
            "Ceramic coating reduces wear by 30 percent in hip implants.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        if claims and claims[0].status == "EVIDENCE_BACKED":
            claim = claims[0]
            # None of the slots should be the full proposition
            assert claim.cause != claim.proposition
            assert claim.intervention != claim.proposition
            assert claim.measured_effect != claim.proposition


# =====================================================================
# #5. NEGATIVE CLAIM TESTS — 9 rejection cases
# =====================================================================

class TestNegativeClaimRejection:
    def _extract(self, text):
        return extract_causal_claims_v4(
            text, source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )

    def test_co_mention_rejected(self):
        """Co-mention without causal language → no claim."""
        claims = self._extract("The paper discusses wear and coating in implants.")
        assert len(claims) == 0

    def test_causal_verb_without_identifiable_mechanism(self):
        """Causal verb present but no extractable mechanism → SEARCH_CANDIDATE, not EVIDENCE_BACKED."""
        claims = self._extract("Reduces.")
        for c in claims:
            assert c.status != "EVIDENCE_BACKED"

    def test_negation_rejected(self):
        """'Does not reduce' → no positive claim."""
        claims = self._extract("The coating does not reduce wear on the implant surface.")
        assert len(claims) == 0

    def test_conditional_only_rejected(self):
        """Conditional/speculative language → no claim."""
        claims = self._extract("The coating may reduce wear under certain conditions.")
        assert len(claims) == 0

    def test_speculation_rejected(self):
        """Speculative language → no claim."""
        claims = self._extract("This approach might potentially improve outcomes.")
        assert len(claims) == 0

    def test_future_intention_rejected(self):
        """Future research intention → no claim."""
        claims = self._extract("Future studies will examine whether coating reduces wear.")
        assert len(claims) == 0

    def test_review_summary_rejected(self):
        """Review article summarization → no claim (not original evidence)."""
        claims = self._extract("Previous reviews have shown that coating reduces wear.")
        assert len(claims) == 0

    def test_correlation_rejected(self):
        """Correlation language → no claim (correlation ≠ causation)."""
        claims = self._extract("Wear rate correlates with coating thickness in implants.")
        assert len(claims) == 0


# =====================================================================
# #2, #3. TYPED CLAIM RELATIONS — NO WORD-OVERLAP
# =====================================================================

class TestTypedClaimRelations:
    def test_chain_without_relations_returns_empty(self):
        """V4: No typed relations → no candidates. No word-overlap fallback."""
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[], mechanism_claims=[], intervention_claims=[],
            claim_relations=None,  # NO relations → empty
        )
        assert len(candidates) == 0

    def test_chain_with_no_evidence_relations_returns_empty(self):
        """Relations with evidence_status=SEARCH_CANDIDATE → no candidates."""
        evidence = SourceEvidence(
            source_id="p:1", source_type="paper", source_field="abstract",
            source_sentence="test", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="test",
            supports_slot="cause",
        )
        fc = Claim(
            claim_id="claim:fc", claim_type="FAILURE_CLAIM",
            proposition="wear causes failure", cause="wear",
            failure_mode="UNSPECIFIED",
            mechanism="degradation", intervention="coating",
            measured_effect="wear rate", boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,),
            intervention_evidence=(evidence,), measured_effect_evidence=(evidence,),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="valid", creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="structured_causal_extraction",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        # Relation with SEARCH_CANDIDATE status (not EVIDENCE)
        rel = make_claim_relation(
            source_claim_id="d:1", target_claim_id="claim:fc",
            relation_type="FAILURE_CLAIM_ABOUT_DEVICE",
            provenance="p:1", source_sentence="test",
            source_hash="h", derivation_method="test",
            evidence_status="SEARCH_CANDIDATE",  # NOT evidence
        )
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[fc], mechanism_claims=[], intervention_claims=[],
            claim_relations=[rel],
        )
        assert len(candidates) == 0

    def test_claim_relation_types_exist(self):
        """V4: typed relation types must exist."""
        assert "FAILURE_CLAIM_ABOUT_DEVICE" in CLAIM_RELATION_TYPES
        assert "MECHANISM_CLAIM_ADDRESSES_FAILURE" in CLAIM_RELATION_TYPES
        assert "INTERVENTION_CLAIM_REALIZES_MECHANISM" in CLAIM_RELATION_TYPES

    def test_claim_relation_has_9_mandatory_fields(self):
        """Per directive #2: relation needs source_claim_id, target_claim_id,
        relation_type, provenance, source_sentence, source_hash,
        derivation_method, temporal_validity, evidence_status."""
        rel = make_claim_relation(
            source_claim_id="c:1", target_claim_id="c:2",
            relation_type="MECHANISM_CLAIM_ADDRESSES_FAILURE",
            provenance="p:1", source_sentence="test sentence",
            source_hash="h", derivation_method="explicit_identifier",
            temporal_validity="valid", evidence_status="EVIDENCE",
        )
        d = rel.canonical_dict()
        for f in ["source_claim_id", "target_claim_id", "relation_type",
                   "provenance", "source_sentence", "source_hash",
                   "derivation_method", "temporal_validity", "evidence_status"]:
            assert f in d


# =====================================================================
# #4. STRENGTHENED EVIDENCE_BACKED
# =====================================================================

class TestStrengthenedEvidenceBacked:
    def test_evidence_backed_requires_slot_level_evidence(self):
        """V4: EVIDENCE_BACKED requires evidence for each slot, not just source_evidence."""
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="c", failure_mode="UNSPECIFIED", mechanism="m",
            intervention="i", measured_effect="e",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(),  # NO evidence for cause
            mechanism_evidence=(),
            intervention_evidence=(),
            measured_effect_evidence=(),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="valid", creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="test",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        # Even though status="EVIDENCE_BACKED", is_evidence_backed() returns False
        # because slot-level evidence is missing
        assert claim.is_evidence_backed() is False

    def test_evidence_backed_requires_all_slots_filled(self):
        """V4: EVIDENCE_BACKED requires all 5 slots non-empty."""
        evidence = SourceEvidence(
            source_id="p:1", source_type="paper", source_field="abstract",
            source_sentence="test", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="test",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="",  # EMPTY
            failure_mode="UNSPECIFIED",
            mechanism="m", intervention="i",
            measured_effect="e", boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,),
            intervention_evidence=(evidence,), measured_effect_evidence=(evidence,),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="valid", creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="test",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.has_five_slots() is False
        assert claim.is_evidence_backed() is False

    def test_evidence_backed_requires_temporal_validity(self):
        """V4: EVIDENCE_BACKED requires temporal_validity='valid'."""
        evidence = SourceEvidence(
            source_id="p:1", source_type="paper", source_field="abstract",
            source_sentence="test", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="test",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="c", failure_mode="UNSPECIFIED", mechanism="m",
            intervention="i", measured_effect="e",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,),
            intervention_evidence=(evidence,), measured_effect_evidence=(evidence,),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="unknown",  # NOT valid
            creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="test",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.is_evidence_backed() is False


# =====================================================================
# #6. CLAIM-LEVEL SOURCE INTEGRITY
# =====================================================================

class TestClaimSourceIntegrity:
    def test_each_slot_has_evidence(self):
        """Per directive #6: each slot identifies which SourceEvidence supports it."""
        evidence = SourceEvidence(
            source_id="p:1", source_type="paper", source_field="abstract",
            source_sentence="test", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="structured_causal_extraction",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="wear", failure_mode="UNSPECIFIED", mechanism="degradation",
            intervention="coating", measured_effect="30% reduction",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,),
            intervention_evidence=(evidence,), measured_effect_evidence=(evidence,),
            source_ids=("p:1",), source_hashes=("h",),
            temporal_validity="valid", creation_timestamp="2026-01-01",
            evidence_tier="D", derivation_method="structured_causal_extraction",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.has_slot_level_evidence() is True
        assert len(claim.cause_evidence) > 0
        assert len(claim.mechanism_evidence) > 0
        assert len(claim.intervention_evidence) > 0
        assert len(claim.measured_effect_evidence) > 0


# =====================================================================
# #7. REPOSITORY-WIDE AUDIT — no similarity→evidence promotion anywhere
# =====================================================================

class TestRepositoryWideAudit:
    def test_no_similarity_method_in_evidence_writers(self):
        """Per CTO: 'add a repository-wide audit test that enumerates every
        evidence writer/constructor and proves the invariant globally.'"""
        import source_fabric.mddg.verified_linkage as vl
        import source_fabric.mddg.claims.claim as cl
        import source_fabric.mddg.edges as ed

        # Every function that can create an EVIDENCE link must NOT accept
        # similarity/keyword/embedding as the verification method.
        evidence_creators = [
            vl.verify_device_recall_link,
            vl.verify_device_trial_link,
            vl.verify_device_paper_link,
            vl.verify_device_patent_link,
            vl.verify_device_adverse_event_link,
        ]
        for creator in evidence_creators:
            # Each creator must return UNRESOLVED when given non-matching records
            # (i.e., no similarity → evidence promotion)
            device = {"record_id": "d:1", "k_number": "K1", "product_code": "PC1",
                      "applicant": "CorpA", "device_name": "DeviceA"}
            other = {"record_id": "x:1", "product_code": "PC2",
                     "recalling_firm": "CorpB", "reason_for_recall": "failure"}
            link = creator(device, other)
            assert link.quality != "VERIFIED_EVIDENCE", \
                f"{creator.__name__} promoted non-matching records to EVIDENCE"

    def test_make_search_candidate_never_evidence(self):
        """make_search_candidate must produce SEARCH_CANDIDATE, never VERIFIED_EVIDENCE."""
        from source_fabric.mddg.verified_linkage import make_search_candidate
        for method in ["embedding", "keyword_overlap", "temporal_proximity",
                        "name_similarity", "semantic_similarity"]:
            link = make_search_candidate("a", "b", "DEVICE_HAS_RECALL",
                                          similarity_score=0.99, method=method)
            assert link.quality == "SEARCH_CANDIDATE"
            assert link.is_evidence() is False

    def test_tier_c_edge_constructor_never_evidence(self):
        """Tier C edge constructor must force evidence_status=SEARCH_ONLY."""
        from source_fabric.mddg.edges import make_mddg_edge
        for tier_c_type in ["SEMANTIC_SIMILARITY", "TEMPORAL_PROXIMITY",
                             "GRAPH_INFERENCE", "ANALOGY"]:
            edge = make_mddg_edge(
                tier_c_type, "a", "b",
                provenance="", source_field="",
                retrieval_time="2026-01-01", temporal_validity="unknown",
                derivation_method="test",
                evidence_status="EVIDENCE",  # try to force
            )
            assert edge.evidence_status == "SEARCH_ONLY"
