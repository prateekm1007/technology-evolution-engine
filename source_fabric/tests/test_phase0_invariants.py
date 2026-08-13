"""
Phase 0 Exit Gate Tests — NO_SIMILARITY_ONLY_EDGE_CAN_EVER_BECOME_EVIDENCE.

Per Fortune 50 / CTO directive: "The coder should be able to demonstrate
mechanically that embedding similarity, keyword overlap, temporal proximity,
and name similarity → SEARCH_CANDIDATE ONLY → NEVER VERIFIED.

If the code cannot demonstrate that with negative tests, Phase 0 is not complete."

These tests prove the invariant holds across ALL code paths.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.verified_linkage import (
    VerifiedLink, make_search_candidate, verify_device_recall_link,
    verify_device_paper_link, verify_device_patent_link,
    verify_device_trial_link, verify_device_adverse_event_link,
    LINK_QUALITY,
)
from source_fabric.mddg.claims.claim import (
    Claim, SourceEvidence, extract_causal_claims, is_causal_sentence,
    CAUSAL_VERBS, NEGATED_CAUSAL,
)
from source_fabric.mddg.claims.independence import attest_independence_v3
from source_fabric.mddg.claims.prior_art_and_chain import (
    assess_prior_art, find_claim_chain_candidates, ClaimChainCandidate,
)
from source_fabric.mddg.edges import make_mddg_edge, is_evidence, get_tier


# =====================================================================
# INVARIANT 1: make_search_candidate NEVER produces EVIDENCE
# =====================================================================

class TestSearchCandidateNeverEvidence:
    def test_search_candidate_is_not_evidence(self):
        """make_search_candidate must produce SEARCH_CANDIDATE, never VERIFIED_EVIDENCE."""
        link = make_search_candidate("a", "b", "DEVICE_HAS_RECALL",
                                      similarity_score=0.99, method="embedding")
        assert link.quality == "SEARCH_CANDIDATE"
        assert link.is_evidence() is False

    def test_high_similarity_still_not_evidence(self):
        """Even 0.99 similarity score must not produce evidence."""
        link = make_search_candidate("a", "b", "DEVICE_HAS_PAPER",
                                      similarity_score=0.99, method="keyword_overlap")
        assert link.is_evidence() is False

    def test_temporal_proximity_not_evidence(self):
        """Temporal proximity method must not produce evidence."""
        link = make_search_candidate("a", "b", "DEVICE_HAS_TRIAL",
                                      similarity_score=0.8, method="temporal_proximity")
        assert link.is_evidence() is False

    def test_name_similarity_not_evidence(self):
        """Name similarity method must not produce evidence."""
        link = make_search_candidate("a", "b", "DEVICE_HAS_RECALL",
                                      similarity_score=0.7, method="name_similarity")
        assert link.is_evidence() is False


# =====================================================================
# INVARIANT 2: verify_*_link functions NEVER produce EVIDENCE from similarity
# =====================================================================

class TestVerifyLinkNeverSimilarityEvidence:
    def test_paper_link_single_word_not_evidence(self):
        """A paper sharing one word with a device must NOT produce evidence."""
        device = {"record_id": "d:1", "k_number": "K123", "product_code": "PC",
                  "applicant": "Corp", "device_name": "Cardiac Sensor"}
        paper = {"record_id": "p:1", "title": "Sensor Networks",
                 "abstract": "Discusses sensor technology"}
        link = verify_device_paper_link(device, paper)
        assert link.quality != "VERIFIED_EVIDENCE"
        assert link.is_evidence() is False

    def test_patent_link_keyword_overlap_not_evidence(self):
        """A patent sharing keywords with a device must NOT produce evidence."""
        device = {"record_id": "d:1", "k_number": "K456", "product_code": "AB",
                  "applicant": "Corp", "device_name": "Implantable Pacemaker"}
        patent = {"record_id": "pat:1", "title": "Pacemaker battery technology",
                  "abstract": "Improves battery life in implantable devices"}
        link = verify_device_patent_link(device, patent)
        assert link.quality != "VERIFIED_EVIDENCE"

    def test_trial_link_name_similarity_not_evidence(self):
        """A trial with a similar name must NOT produce evidence."""
        device = {"record_id": "d:1", "k_number": "K789", "product_code": "XY",
                  "applicant": "Corp", "device_name": "Neurostimulator"}
        trial = {"record_id": "t:1", "nct_id": "NCT12345",
                 "brief_title": "Neurostimulation therapy study"}
        link = verify_device_trial_link(device, trial)
        assert link.quality != "VERIFIED_EVIDENCE"

    def test_recall_link_temporal_proximity_not_evidence(self):
        """A recall close in time must NOT produce evidence without identifier."""
        device = {"record_id": "d:1", "k_number": "K999", "product_code": "ZZ",
                  "applicant": "Corp", "device_name": " infusion pump"}
        recall = {"record_id": "r:1", "product_code": "YY",
                  "recalling_firm": "OtherCorp", "reason_for_recall": "pump failure",
                  "recall_initiation_date": "2024-01-01"}
        link = verify_device_recall_link(device, recall)
        assert link.quality != "VERIFIED_EVIDENCE"

    def test_ae_link_embedding_similarity_not_evidence(self):
        """An AE with embedding similarity must NOT produce evidence without identifier."""
        device = {"record_id": "d:1", "k_number": "K111", "product_code": "AA",
                  "applicant": "Corp", "device_name": "CT Scanner"}
        ae = {"record_id": "ae:1", "mdr_report_key": "123",
              "device": [{"device_report_product_code": "BB",
                          "brand_name": "MRI Scanner"}]}
        link = verify_device_adverse_event_link(device, ae)
        assert link.quality != "VERIFIED_EVIDENCE"


# =====================================================================
# INVARIANT 3: Claim extraction NEVER creates claims from co-mention
# =====================================================================

class TestClaimExtractionNeverCoMention:
    def test_co_mention_produces_no_claim(self):
        """Co-mention of 'wear' and 'coating' without causal language → no claim."""
        claims = extract_causal_claims(
            "The paper discusses wear and coating in implants.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_embedding_similarity_produces_no_claim(self):
        """Semantic similarity without causal verbs → no claim."""
        claims = extract_causal_claims(
            "This study examines the relationship between surface chemistry and implant degradation.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_temporal_proximity_produces_no_claim(self):
        """Temporal co-occurrence → no claim."""
        claims = extract_causal_claims(
            "In 2020, the device was marketed. In 2021, failures were reported.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_negated_causal_produces_no_claim(self):
        """'Does not reduce' → no positive claim."""
        claims = extract_causal_claims(
            "The coating does not reduce wear on the implant surface.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_only_explicit_causal_produces_claim(self):
        """Only explicit causal verbs produce claims."""
        claims = extract_causal_claims(
            "The ceramic coating reduces wear rate by 40% in hip implants.",
            source_id="p:1", source_type="paper",
            source_field="abstract", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 1
        assert claims[0].status == "EVIDENCE_BACKED"
        assert claims[0].derivation_method == "explicit_causal_extraction"


# =====================================================================
# INVARIANT 4: Tier C edges are NEVER evidence
# =====================================================================

class TestTierCNeverEvidence:
    def test_semantic_similarity_tier_c_not_evidence(self):
        """SEMANTIC_SIMILARITY (Tier C) must have is_evidence=False."""
        e = make_mddg_edge(
            "SEMANTIC_SIMILARITY", "a", "b",
            provenance="", source_field="title",
            retrieval_time="2026-01-01", temporal_validity="unknown",
            derivation_method="embedding",
            evidence_status="EVIDENCE",  # try to force — must be overridden
        )
        assert e.tier == "C"
        assert e.evidence_status == "SEARCH_ONLY"
        assert is_evidence("SEMANTIC_SIMILARITY") is False

    def test_temporal_proximity_tier_c_not_evidence(self):
        """TEMPORAL_PROXIMITY (Tier C) must have is_evidence=False."""
        e = make_mddg_edge(
            "TEMPORAL_PROXIMITY", "a", "b",
            provenance="", source_field="date",
            retrieval_time="2026-01-01", temporal_validity="unknown",
            derivation_method="date_window",
        )
        assert e.tier == "C"
        assert e.evidence_status == "SEARCH_ONLY"
        assert is_evidence("TEMPORAL_PROXIMITY") is False


# =====================================================================
# INVARIANT 5: Claim-chain detector NEVER qualifies from co-presence
# =====================================================================

class TestClaimChainNeverCoPresence:
    def test_no_claims_no_candidate(self):
        """No claims → no candidates. Co-presence of entities is NOT a candidate."""
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[], mechanism_claims=[], intervention_claims=[],
        )
        assert len(candidates) == 0

    def test_unverified_claims_no_qualified_candidate(self):
        """SEARCH_CANDIDATE-status claims cannot produce a qualified candidate."""
        evidence = SourceEvidence(
            source_id="p:1", source_type="paper", source_field="abstract",
            source_sentence="X mentions Y", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="co_mention",
        )
        fc = Claim(
            claim_id="c:fc", claim_type="FAILURE_CLAIM",
            proposition="wear mentioned", cause="wear",
            mechanism="degradation", intervention="coating",
            measured_effect="wear rate", boundary_conditions="UNSPECIFIED",
            source_evidence=(evidence,), source_ids=("d:1",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="co_mention",
            status="SEARCH_CANDIDATE",  # NOT evidence-backed
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        mc = Claim(
            claim_id="c:mc", claim_type="MECHANISM_CLAIM",
            proposition="degradation mentioned", cause="wear",
            mechanism="degradation", intervention="coating",
            measured_effect="wear rate", boundary_conditions="UNSPECIFIED",
            source_evidence=(evidence,), source_ids=("p:2",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="co_mention",
            status="SEARCH_CANDIDATE",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        ic = Claim(
            claim_id="c:ic", claim_type="INTERVENTION_CLAIM",
            proposition="coating mentioned", cause="wear",
            mechanism="degradation", intervention="coating",
            measured_effect="wear rate", boundary_conditions="UNSPECIFIED",
            source_evidence=(evidence,), source_ids=("p:3",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="co_mention",
            status="SEARCH_CANDIDATE",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        candidates = find_claim_chain_candidates(
            device_id="d:1",
            failure_claims=[fc], mechanism_claims=[mc], intervention_claims=[ic],
        )
        for c in candidates:
            assert c.qualified is False
            assert c.all_claims_evidence_backed is False


# =====================================================================
# INVARIANT 6: Independence NEVER passes with hash inequality alone
# =====================================================================

class TestIndependenceNeverHashInequality:
    def test_overlapping_sets_not_independent_even_if_hashes_differ(self):
        """A={p1,p2}, B={p2,p3} have different hashes but are NOT independent."""
        att = attest_independence_v3(
            device_failure_source_ids=["paper:1", "paper:2"],
            mechanism_source_ids=["paper:2", "paper:3"],
            mechanism_source_dates=["2019-01-01"],
            set_a_authors={"A"}, set_b_authors={"B"},
            set_a_citations={"c1"}, set_b_citations={"c2"},
            set_a_vocabulary={"v1"}, set_b_vocabulary={"v2"},
            lock_time="2026-01-01T00:00:00Z",
        )
        # Hashes ARE different (different sets), but sets are NOT disjoint
        assert att.set_a_hash != att.set_b_hash
        assert att.is_disjoint is False
        assert att.is_independent is False


# =====================================================================
# INVARIANT 7: Prior-art NEVER emits NOVEL
# =====================================================================

class TestPriorArtNeverNovel:
    def test_novel_not_in_vocabulary(self):
        """NOVEL must never appear in the prior-art stages."""
        from source_fabric.mddg.claims.prior_art_and_chain import (
            PRIOR_ART_STAGES, FORBIDDEN_PRIOR_ART_LABELS
        )
        assert "NOVEL" not in PRIOR_ART_STAGES
        assert "NOVEL" in FORBIDDEN_PRIOR_ART_LABELS

    def test_machine_cannot_self_assign_externally_testable(self):
        """EXTERNALLY_TESTABLE requires human_sign_off=True. Machine cannot self-assign."""
        from source_fabric.mddg.claims.prior_art_and_chain import PriorArtAssessment
        with pytest.raises(ValueError, match="human_sign_off"):
            PriorArtAssessment(
                candidate_id="c:1",
                stage="EXTERNALLY_TESTABLE",
                patent_search_result="NOT_FOUND",
                paper_search_result="NOT_FOUND",
                device_search_result="NOT_FOUND",
                clinical_search_result="NOT_FOUND",
                failure_search_result="NOT_FOUND",
                assessment_timestamp="2026-01-01",
                human_sign_off=False,  # NO human sign-off → CANNOT be EXTERNALLY_TESTABLE
            )


# =====================================================================
# INVARIANT 8: OBVIOUS_COMBINATION is BLOCKED (not hardcoded PASS)
# =====================================================================

class TestObviousCombinationBlocked:
    def test_obvious_combination_fails_by_default(self):
        """OBVIOUS_COMBINATION must FAIL by default (BLOCKED)."""
        from source_fabric.mddg.qualification import run_adversarial_review
        review = run_adversarial_review(
            candidate_id="c:1",
            has_device_evidence=True,
            has_failure_evidence=True,
            has_mechanism_evidence=True,
            has_intervention_evidence=True,
            mechanism_predates_failure=True,
            prior_art_status="NOT_FOUND",
            evidence_tiers=["A", "B"],
            obvious_combination_check_implemented=False,  # BLOCKED
        )
        assert "OBVIOUS_COMBINATION" in review.attacks_failed
        assert review.survived is False

    def test_candidate_cannot_qualify_with_blocked_attack(self):
        """A candidate CANNOT qualify while OBVIOUS_COMBINATION is blocked."""
        from source_fabric.mddg.qualification import run_adversarial_review
        review = run_adversarial_review(
            candidate_id="c:1",
            has_device_evidence=True,
            has_failure_evidence=True,
            has_mechanism_evidence=True,
            has_intervention_evidence=True,
            mechanism_predates_failure=True,
            prior_art_status="NOT_FOUND",
            evidence_tiers=["A", "B"],
        )
        assert review.survived is False
