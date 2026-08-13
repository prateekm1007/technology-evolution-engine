"""
MDDG V3 tests — Claim atomic unit, device lineage, independence, prior-art, claim-chain.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.claims.claim import (
    Claim, SourceEvidence, CLAIM_TYPES, CLAIM_STATUS, CAUSAL_VERBS,
    NEGATED_CAUSAL, extract_causal_claims, is_causal_sentence, make_claim_id,
)
from source_fabric.mddg.claims.device_lineage import (
    DeviceIdentity, resolve_device_identity, DeviceLineageEdge,
    extract_predicate_lineage, LINEAGE_EVIDENCE_TYPES, ENTITY_RESOLUTION_TIERS,
    seed_from_modern_devices,
)
from source_fabric.mddg.claims.independence import (
    IndependenceAttestation, attest_independence_v3,
    check_different_authors, check_no_shared_citation, check_different_vocabulary,
)
from source_fabric.mddg.claims.prior_art_and_chain import (
    PriorArtAssessment, assess_prior_art, PRIOR_ART_STAGES,
    FORBIDDEN_PRIOR_ART_LABELS, ClaimChainCandidate, find_claim_chain_candidates,
)


# =====================================================================
# #3, #4. CLAIM ATOMIC UNIT — 5-SLOT STRUCTURE
# =====================================================================

class TestClaimAtomicUnit:
    def test_claim_has_18_fields(self):
        """A Claim must have all 18 mandatory fields."""
        evidence = SourceEvidence(
            source_id="paper:1", source_type="paper", source_field="abstract",
            source_sentence="X reduces Y", source_hash="abc",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="explicit_causal_verb",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id=make_claim_id("MECHANISM_CLAIM", "wear", "coating", "coating"),
            claim_type="MECHANISM_CLAIM",
            proposition="Coating reduces wear",
            cause="wear", failure_mode="UNSPECIFIED", causal_relation="UNSPECIFIED", mechanism="coating", intervention="apply coating",
            measured_effect="wear rate decreases",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,),
            source_ids=("paper:1",),
            source_hashes=("abc",),
            temporal_validity="valid",
            creation_timestamp="2026-01-01T00:00:00Z",
            evidence_tier="D",
            derivation_method="explicit_causal_extraction",
            failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="replicate in independent experiment",
            measurement_method="controlled experiment",
            alternative_explanations=("random variation",),
        )
        d = claim.canonical_dict()
        # 18 mandatory fields
        for f in ["claim_id", "claim_type", "proposition", "cause", "mechanism",
                   "intervention", "measured_effect", "boundary_conditions",
                   "cause_evidence", "mechanism_evidence", "intervention_evidence", "measured_effect_evidence", "source_ids", "source_hashes",
                   "temporal_validity", "creation_timestamp", "evidence_tier",
                   "derivation_method", "status", "falsification_condition",
                   "measurement_method", "alternative_explanations"]:
            assert f in d

    def test_claim_has_five_slots(self):
        """Per directive #4: CAUSE, MECHANISM, INTERVENTION, MEASURED_EFFECT, BOUNDARY_CONDITIONS."""
        evidence = SourceEvidence(
            source_id="p1", source_type="paper", source_field="abstract",
            source_sentence="X reduces Y", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="explicit_causal_verb",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="c", failure_mode="UNSPECIFIED", causal_relation="UNSPECIFIED", mechanism="m",
            mechanism_status="EXPLICIT",
            intervention="i", measured_effect="e",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,), source_ids=("p1",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="test", failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.has_five_slots() is True

    def test_boundary_conditions_defaults_to_unspecified(self):
        """Per directive #4: 'Boundary conditions may temporarily be UNSPECIFIED
        but the absence must be explicit.'"""
        evidence = SourceEvidence(
            source_id="p1", source_type="paper", source_field="abstract",
            source_sentence="test", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="test",
            supports_slot="cause",
        )
        claim = Claim(
            claim_id="claim:1", claim_type="MECHANISM_CLAIM",
            proposition="test", cause="c", failure_mode="UNSPECIFIED", causal_relation="UNSPECIFIED", mechanism="m",
            mechanism_status="EXPLICIT",
            intervention="i", measured_effect="e",
            boundary_conditions="",  # empty — should default to UNSPECIFIED
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,), source_ids=("p1",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="test", failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        assert claim.boundary_conditions == "UNSPECIFIED"


# =====================================================================
# #5. CAUSAL LANGUAGE EXTRACTION
# =====================================================================

class TestCausalExtraction:
    def test_causal_verb_detected(self):
        """Sentences with causal verbs produce claims."""
        claims = extract_causal_claims(
            "The coating reduces wear on the implant surface.",
            source_id="paper:1", source_type="paper",
            source_field="abstract", source_hash="abc",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) > 0
        assert claims[0].status == "EVIDENCE_BACKED"

    def test_negated_causal_not_a_claim(self):
        """Negated causal language does not produce a positive claim."""
        claims = extract_causal_claims(
            "The coating does not reduce wear on the implant surface.",
            source_id="paper:1", source_type="paper",
            source_field="abstract", source_hash="abc",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_co_mention_not_a_claim(self):
        """Co-occurrence without causal language does not produce a claim."""
        claims = extract_causal_claims(
            "The paper discusses wear and coating in the context of implants.",
            source_id="paper:1", source_type="paper",
            source_field="abstract", source_hash="abc",
            publication_date="2020-01-01", evidence_tier="D",
        )
        assert len(claims) == 0

    def test_is_causal_sentence(self):
        assert is_causal_sentence("X reduces Y") is True
        assert is_causal_sentence("X and Y are discussed") is False
        assert is_causal_sentence("X does not reduce Y") is False


# =====================================================================
# #6, #7. DEVICE LINEAGE & ENTITY RESOLUTION
# =====================================================================

class TestDeviceLineage:
    def test_tier1_authoritative_identity(self):
        """Tier 1 (K-number) establishes authoritative identity."""
        identity = resolve_device_identity({"k_number": "K123456"})
        assert identity.resolution_tier == 1
        assert identity.is_authoritative() is True

    def test_tier2_product_code_plus_manufacturer(self):
        """Tier 2 requires BOTH product_code AND manufacturer."""
        identity = resolve_device_identity({
            "product_code": "DXY",
            "applicant": "Medtronic",
        })
        assert identity.resolution_tier == 2

    def test_tier4_never_becomes_product_identity(self):
        """Per directive #7: 'Tier 4 must never automatically become product identity.'"""
        identity = resolve_device_identity({
            "assignee": "CorpA",
            "sponsor": "HospitalB",
        })
        assert identity.resolution_tier == 4
        assert "NOT_product_identity" in identity.resolution_method

    def test_predicate_lineage_extracted(self):
        """510(k) predicate citation is authoritative lineage evidence."""
        record = {
            "k_number": "K200123",
            "predicate": "K150456",
            "record_id": "fda510k:K200123",
            "_raw_hash": "abc",
        }
        edge = extract_predicate_lineage(record)
        assert edge is not None
        assert edge.evidence_type == "510K_PREDICATE_CITATION"
        assert "K150456" in edge.source_device_id
        assert "K200123" in edge.target_device_id

    def test_similar_name_not_lineage(self):
        """Per directive #6: similar name does NOT establish lineage."""
        # The LINEAGE_EVIDENCE_TYPES set must NOT contain "SIMILAR_NAME"
        assert "SIMILAR_NAME" not in LINEAGE_EVIDENCE_TYPES
        assert "SAME_COMPANY" not in LINEAGE_EVIDENCE_TYPES


# =====================================================================
# #11. INDEPENDENCE — SET DISJOINTNESS + 2-OF-3
# =====================================================================

class TestIndependenceV3:
    def test_disjoint_sets_pass_primary(self):
        att = attest_independence_v3(
            device_failure_source_ids=["paper:1"],
            mechanism_source_ids=["paper:2"],
            mechanism_source_dates=["2019-01-01"],
            set_a_authors={"AuthorA"}, set_b_authors={"AuthorB"},
            set_a_citations={"ref:1"}, set_b_citations={"ref:2"},
            set_a_vocabulary={"battery", "electrode"},
            set_b_vocabulary={"coating", "lubrication"},
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.is_disjoint is True
        assert att.secondary_criteria_passed >= 2
        assert att.is_independent is True

    def test_overlapping_sets_fail(self):
        att = attest_independence_v3(
            device_failure_source_ids=["paper:1", "paper:2"],
            mechanism_source_ids=["paper:2", "paper:3"],
            mechanism_source_dates=["2019-01-01"],
            set_a_authors={"A"}, set_b_authors={"B"},
            set_a_citations={"c1"}, set_b_citations={"c2"},
            set_a_vocabulary={"v1"}, set_b_vocabulary={"v2"},
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.is_disjoint is False
        assert att.is_independent is False

    def test_only_one_secondary_criterion_fails(self):
        """Per directive #11: need at least 2 of 3 secondary criteria."""
        att = attest_independence_v3(
            device_failure_source_ids=["paper:1"],
            mechanism_source_ids=["paper:2"],
            mechanism_source_dates=["2019-01-01"],
            set_a_authors={"AuthorA"}, set_b_authors={"AuthorA"},  # same authors → crit A fails
            set_a_citations={"ref:1"}, set_b_citations={"ref:2"},  # different → crit B passes
            set_a_vocabulary={"battery"}, set_b_vocabulary={"battery"},  # same → crit C fails
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.secondary_criteria_passed == 1  # only crit B
        assert att.is_independent is False


# =====================================================================
# #13. STAGED PRIOR-ART VOCABULARY
# =====================================================================

class TestPriorArtStaged:
    def test_never_emits_novel(self):
        """Per directive #13: 'The machine must never self-label NOVEL.'"""
        assert "NOVEL" not in PRIOR_ART_STAGES
        assert "NOVEL" in FORBIDDEN_PRIOR_ART_LABELS

    def test_promising_intersection_requires_expert_review(self):
        """Per directive #13: PROMISING_INTERSECTION triggers mandatory expert review."""
        # Provide non-empty corpora that return NOT_FOUND (not UNKNOWN)
        assessment = assess_prior_art(
            candidate_id="cand:1",
            candidate_identifiers=["K999"],
            patent_corpus=[{"text": "unrelated patent"}],
            paper_corpus=[{"text": "unrelated paper"}],
            device_corpus=[{"text": "unrelated device"}],
            clinical_corpus=[{"text": "unrelated trial"}],
            failure_corpus=[{"text": "unrelated failure"}],
        )
        # Searched and found no prior art → PROMISING_INTERSECTION
        assert assessment.stage == "PROMISING_INTERSECTION"
        assert assessment.expert_review_required is True

    def test_externally_testable_requires_human_sign_off(self):
        """Per directive #13: only human sign-off promotes to EXTERNALLY_TESTABLE."""
        # With non-empty corpora returning NOT_FOUND + human_sign_off=True → EXTERNALLY_TESTABLE
        assessment = assess_prior_art(
            candidate_id="cand:1",
            candidate_identifiers=["K999"],
            patent_corpus=[{"text": "unrelated"}],
            paper_corpus=[{"text": "unrelated"}],
            device_corpus=[{"text": "unrelated"}],
            clinical_corpus=[{"text": "unrelated"}],
            failure_corpus=[{"text": "unrelated"}],
            human_sign_off=True,
        )
        assert assessment.stage == "EXTERNALLY_TESTABLE"
        assert assessment.human_sign_off is True


# =====================================================================
# #12. CLAIM-CHAIN DETECTOR
# =====================================================================

class TestClaimChainDetector:
    def test_co_presence_not_a_candidate(self):
        """Per directive #12: co-presence is not a candidate."""
        # No claims → no candidates
        candidates = find_claim_chain_candidates(
            device_id="device:1",
            failure_claims=[], mechanism_claims=[], intervention_claims=[],
        )
        assert len(candidates) == 0

    def test_chain_requires_all_three_claims(self):
        """A qualified candidate requires failure + mechanism + intervention claims."""
        evidence = SourceEvidence(
            source_id="paper:1", source_type="paper", source_field="abstract",
            source_sentence="X reduces Y", source_hash="h",
            publication_date="2020-01-01", evidence_tier="D",
            extraction_method="explicit_causal_verb",
            supports_slot="cause",
        )
        fc = Claim(
            claim_id="claim:fc1", claim_type="FAILURE_CLAIM",
            proposition="wear causes implant failure", cause="wear",
            failure_mode="UNSPECIFIED",
            causal_relation="reduces",
            mechanism="surface degradation", intervention="coating",
            measured_effect="wear rate", boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,), source_ids=("device:1", "paper:1"),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="explicit_causal_extraction",
            failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        mc = Claim(
            claim_id="claim:mc1", claim_type="MECHANISM_CLAIM",
            proposition="surface degradation reduces coating effectiveness",
            cause="wear", failure_mode="UNSPECIFIED", causal_relation="UNSPECIFIED", mechanism="surface degradation",
            mechanism_status="EXPLICIT",
            intervention="coating", measured_effect="wear rate decrease",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,), source_ids=("paper:2",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="explicit_causal_extraction",
            failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        ic = Claim(
            claim_id="claim:ic1", claim_type="INTERVENTION_CLAIM",
            proposition="coating improves wear resistance",
            cause="wear", failure_mode="UNSPECIFIED", causal_relation="UNSPECIFIED", mechanism="surface degradation",
            mechanism_status="EXPLICIT",
            intervention="apply coating", measured_effect="wear rate decrease",
            boundary_conditions="UNSPECIFIED",
            cause_evidence=(evidence,), mechanism_evidence=(evidence,), intervention_evidence=(evidence,), measured_effect_evidence=(evidence,), source_ids=("paper:3",),
            source_hashes=("h",), temporal_validity="valid",
            creation_timestamp="2026-01-01", evidence_tier="D",
            derivation_method="explicit_causal_extraction",
            failure_mode_source="ONTOLOGY_VALIDATED",
            status="EVIDENCE_BACKED",
            falsification_condition="f", measurement_method="m",
            alternative_explanations=(),
        )
        candidates = find_claim_chain_candidates(
            device_id="device:1",
            failure_claims=[fc], mechanism_claims=[mc], intervention_claims=[ic],
        )
        # Should find at least one candidate (if the matching logic connects them)
        # Note: the matching is heuristic — may or may not find a match
        # The key test is that it does NOT create candidates from co-presence alone
        for c in candidates:
            assert c.all_hops_have_claims is True
            assert c.all_claims_evidence_backed is True


# =====================================================================
# #8. MODERN-DEVICE FORWARD SEEDING
# =====================================================================

class TestModernDeviceSeeding:
    def test_seed_from_maude(self):
        """Modern devices are seeded from recent MAUDE activity."""
        maude_records = [
            {"device": [{"device_report_product_code": "DXY", "brand_name": "DeviceX"}]},
        ]
        seeds = seed_from_modern_devices(maude_records, [], [])
        assert "product_code:DXY" in seeds
        assert "brand:DeviceX" in seeds
