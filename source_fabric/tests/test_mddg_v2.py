"""
MDDG V2 tests — evidence semantics corrections (CTO V8 directive).
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.mddg.verified_linkage import (
    LINK_QUALITY, VerifiedLink, verify_device_recall_link,
    verify_device_trial_link, verify_device_paper_link,
    verify_device_patent_link, verify_device_adverse_event_link,
    make_search_candidate, evaluate_linkage_precision,
    LinkageBenchmarkPair,
)
from source_fabric.mddg.qualification import (
    attest_independence, run_prior_art_check, run_adversarial_review,
    PRIOR_ART_STATUSES, ADVERSARIAL_ATTACKS, QualifiedCandidate,
)
from source_fabric.mddg.benchmark_v2 import (
    find_four_hop_candidates, run_all_null_controls_v2,
    FourHopCandidate,
)
from source_fabric.mddg.lifecycle import LifecycleReconstructor


# =====================================================================
# #2. SEARCH_CANDIDATE vs EVIDENCE_LINK
# =====================================================================

class TestLinkQualitySplit:
    def test_search_candidate_is_not_evidence(self):
        """A SEARCH_CANDIDATE link must never be evidence."""
        link = make_search_candidate("device:1", "paper:1", "PAPER_DESCRIBES_DEVICE",
                                      similarity_score=0.9, method="keyword_overlap")
        assert link.quality == "SEARCH_CANDIDATE"
        assert link.is_evidence() is False

    def test_verified_evidence_is_evidence(self):
        """A VERIFIED_EVIDENCE link (identifier match) is evidence."""
        device = {"record_id": "device:1", "k_number": "K123456", "product_code": "DXY",
                  "applicant": "Medtronic", "device_name": "Cardiac Pacemaker"}
        recall = {"record_id": "recall:1", "product_code": "DXY",
                  "recalling_firm": "Medtronic", "reason_for_recall": "battery failure"}
        link = verify_device_recall_link(device, recall)
        assert link.quality == "VERIFIED_EVIDENCE"
        assert link.is_evidence() is True

    def test_single_word_overlap_not_evidence(self):
        """Per CTO: 'A single shared word must never create an evidence edge.'"""
        device = {"record_id": "device:1", "k_number": "K123", "product_code": "ABC",
                  "applicant": "CorpA", "device_name": "Cardiac Sensor"}
        paper = {"record_id": "paper:1", "title": "Sensor Networks in Healthcare",
                 "abstract": "This paper discusses sensor technologies"}
        link = verify_device_paper_link(device, paper)
        # Single word "sensor" overlap → UNRESOLVED, not EVIDENCE
        assert link.quality == "UNRESOLVED"
        assert link.is_evidence() is False

    def test_no_identifier_match_is_unresolved(self):
        """When no auditable identifier matches, the link is UNRESOLVED."""
        device = {"record_id": "device:1", "k_number": "K123", "product_code": "ABC",
                  "applicant": "CorpA", "device_name": "Device X"}
        recall = {"record_id": "recall:1", "product_code": "XYZ",
                  "recalling_firm": "CorpB", "reason_for_recall": "failure"}
        link = verify_device_recall_link(device, recall)
        assert link.quality == "UNRESOLVED"
        assert "MISSING" in link.notes or "IDENTIFIER" in link.notes


# =====================================================================
# #9. FOUR-HOP FOLLOWS ACTUAL EDGES
# =====================================================================

class TestFourHopEdgeFollowing:
    def test_no_edge_no_hop(self):
        """V8: Co-presence of entities is NOT a candidate. No edge = no hop."""
        recon = LifecycleReconstructor()
        # Add a device with failure modes and mechanisms but NO edges between them
        recon.add_fda_510k({
            "k_number": "K999", "applicant": "Corp", "product_code": "ZZZ",
            "device_name": "Test Device", "decision_date": "2020-01-01",
            "_harvested_at": "2026-01-01", "_raw_hash": "test",
        })
        # Manually add failure modes and mechanisms WITHOUT edges
        from source_fabric.mddg.ontology import make_failure_mode, make_mechanism, make_material
        lc = list(recon.devices.values())[0]
        lc.failure_modes.append(make_failure_mode(
            name="BATTERY_FAILURE", source_ids=("src:test",), provenance=({},)))
        lc.mechanisms.append(make_mechanism(
            name="electrochemical", source_ids=("src:test",), provenance=({},)))
        lc.materials.append(make_material(
            name="lithium", source_ids=("src:test",), provenance=({},)))
        # No edges connect these → no candidates
        candidates = find_four_hop_candidates(recon)
        assert len(candidates) == 0


# =====================================================================
# #11. INDEPENDENT MECHANISM — SET DISJOINTNESS
# =====================================================================

class TestIndependentMechanism:
    def test_overlapping_sets_not_independent(self):
        """V8: A={p1,p2}, B={p2,p3} → NOT independent (intersection ≠ ∅)."""
        att = attest_independence(
            device_failure_source_ids=["paper:1", "paper:2"],
            mechanism_source_ids=["paper:2", "paper:3"],
            mechanism_vocabulary=["electrochemistry"],
            mechanism_source_dates=["2019-01-01"],
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.is_disjoint is False
        assert att.is_independent is False

    def test_disjoint_sets_with_predating_mechanism_is_independent(self):
        """V8: A={p1}, B={p2,p3} with mechanism predating lock → independent."""
        att = attest_independence(
            device_failure_source_ids=["paper:1"],
            mechanism_source_ids=["paper:2", "paper:3"],
            mechanism_vocabulary=["electrochemistry"],
            mechanism_source_dates=["2019-01-01", "2020-06-15"],
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.is_disjoint is True
        assert att.all_mechanism_sources_predate is True
        assert att.is_independent is True

    def test_mechanism_postdating_lock_not_independent(self):
        """V8: mechanism source after lock time → NOT independent."""
        att = attest_independence(
            device_failure_source_ids=["paper:1"],
            mechanism_source_ids=["paper:2"],
            mechanism_vocabulary=["electrochemistry"],
            mechanism_source_dates=["2027-01-01"],  # after lock
            lock_time="2026-01-01T00:00:00Z",
        )
        assert att.all_mechanism_sources_predate is False
        assert att.is_independent is False

    def test_full_source_lists_preserved(self):
        """V8: full source IDs preserved, not just hashes."""
        att = attest_independence(
            device_failure_source_ids=["paper:1", "paper:2"],
            mechanism_source_ids=["paper:3"],
            mechanism_vocabulary=["mech"],
            mechanism_source_dates=["2019-01-01"],
            lock_time="2026-01-01T00:00:00Z",
        )
        assert "paper:1" in att.source_set_a_ids
        assert "paper:2" in att.source_set_a_ids
        assert "paper:3" in att.source_set_b_ids
        assert len(att.mechanism_source_dates) == 1


# =====================================================================
# #12. PRIOR-ART — NO TOKEN OVERLAP
# =====================================================================

class TestPriorArtV8:
    def test_no_directly_disclosed_status(self):
        """V8: DIRECTLY_DISCLOSED removed. Only EXACT_IDENTIFIER_MATCH."""
        assert "DIRECTLY_DISCLOSED" not in PRIOR_ART_STATUSES
        assert "EXACT_IDENTIFIER_MATCH" in PRIOR_ART_STATUSES

    def test_identifier_match_finds_prior_art(self):
        """Prior-art search uses identifier matching, not token overlap."""
        result = run_prior_art_check(
            candidate_id="cand:1",
            candidate_identifiers=["K123456", "DXY"],
            patent_corpus=[{"text": "This patent relates to device K123456"}],
        )
        assert result.patent_search_status == "EXACT_IDENTIFIER_MATCH"

    def test_no_identifier_no_disclosure(self):
        """Without identifier match, status is NOT_FOUND (not DIRECTLY_DISCLOSED)."""
        result = run_prior_art_check(
            candidate_id="cand:1",
            candidate_identifiers=["K123456"],
            patent_corpus=[{"text": "This patent discusses cardiac sensors and battery technology"}],
        )
        assert result.patent_search_status == "NOT_FOUND"

    def test_never_emits_novel(self):
        """The prior-art procedure never emits NOVEL."""
        result = run_prior_art_check(
            candidate_id="cand:1",
            candidate_identifiers=["K123"],
            patent_corpus=[],
        )
        assert "NOVEL" not in result.overall_status


# =====================================================================
# #13. ADVERSARIAL — OBVIOUS_COMBINATION BLOCKED
# =====================================================================

class TestAdversarialV8:
    def test_obvious_combination_blocked_by_default(self):
        """V8: OBVIOUS_COMBINATION is BLOCKED by default → candidate cannot qualify."""
        review = run_adversarial_review(
            candidate_id="cand:1",
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

    def test_all_attacks_execute(self):
        """V8: Every attack must actually execute — no hardcoded PASS."""
        review = run_adversarial_review(
            candidate_id="cand:1",
            has_device_evidence=False,
            has_failure_evidence=True,
            has_mechanism_evidence=True,
            has_intervention_evidence=True,
            mechanism_predates_failure=True,
            prior_art_status="NOT_FOUND",
            evidence_tiers=["A"],
        )
        # RETRIEVAL and INSUFFICIENT_EVIDENCE should fail (no device evidence)
        assert "RETRIEVAL" in review.attacks_failed
        assert "INSUFFICIENT_EVIDENCE" in review.attacks_failed
        # OBVIOUS_COMBINATION should fail (blocked)
        assert "OBVIOUS_COMBINATION" in review.attacks_failed
        assert review.survived is False


# =====================================================================
# #14. NULL CONTROLS REBUILD GRAPHS
# =====================================================================

class TestNullControlsV8:
    def test_temporal_shuffle_rebuilds_graph(self):
        """V8: temporal shuffle actually rebuilds the graph."""
        recon = LifecycleReconstructor()
        recon.add_fda_510k({
            "k_number": "K1", "applicant": "Corp", "product_code": "PC1",
            "device_name": "Device 1", "decision_date": "2020-01-01",
            "_harvested_at": "2026-01-01", "_raw_hash": "test",
        })
        result = recon  # pass the reconstructor
        from source_fabric.mddg.benchmark_v2 import null_temporal_shuffle_v2
        null_result = null_temporal_shuffle_v2(result, seed=42)
        assert "candidates_after_shuffle" in null_result
        assert "V8" in null_result["note"]

    def test_single_corpus_only_removes_cross_corpus(self):
        """V8: single-corpus null removes papers/patents/trials."""
        recon = LifecycleReconstructor()
        recon.add_fda_510k({
            "k_number": "K1", "applicant": "Corp", "product_code": "PC1",
            "device_name": "Device 1", "decision_date": "2020-01-01",
            "_harvested_at": "2026-01-01", "_raw_hash": "test",
        })
        from source_fabric.mddg.benchmark_v2 import null_single_corpus_only_v2
        null_result = null_single_corpus_only_v2(recon)
        assert "candidates_fda_only" in null_result
        assert null_result["candidates_fda_only"] == 0  # no four-hop without cross-corpus


# =====================================================================
# #17. HELD-OUT LINKAGE BENCHMARK
# =====================================================================

class TestLinkageBenchmark:
    def test_precision_calculation(self):
        """Precision = TP / (TP + FP)."""
        pairs = [
            LinkageBenchmarkPair(pair_id="1", link_type="DEVICE_HAS_RECALL",
                                  device_record={"product_code": "DXY"},
                                  other_record={"product_code": "DXY"},
                                  true_label="TRUE_LINK",
                                  predicted_quality="VERIFIED_EVIDENCE"),
            LinkageBenchmarkPair(pair_id="2", link_type="DEVICE_HAS_RECALL",
                                  device_record={"product_code": "ABC"},
                                  other_record={"product_code": "XYZ"},
                                  true_label="FALSE_LINK",
                                  predicted_quality="UNRESOLVED"),
            LinkageBenchmarkPair(pair_id="3", link_type="DEVICE_HAS_RECALL",
                                  device_record={"product_code": "DEF"},
                                  other_record={"product_code": "DEF"},
                                  true_label="TRUE_LINK",
                                  predicted_quality="VERIFIED_EVIDENCE"),
        ]
        result = evaluate_linkage_precision(pairs)
        assert result["true_positives"] == 2
        assert result["false_positives"] == 0
        assert result["precision"] == 1.0
        assert result["precision_gate_pass"] is True

    def test_false_link_detected(self):
        """A FALSE_LINK predicted as VERIFIED_EVIDENCE is a false positive."""
        pairs = [
            LinkageBenchmarkPair(pair_id="1", link_type="DEVICE_HAS_RECALL",
                                  device_record={"product_code": "DXY"},
                                  other_record={"product_code": "DXY"},
                                  true_label="FALSE_LINK",  # actually false but predicted true
                                  predicted_quality="VERIFIED_EVIDENCE"),
        ]
        result = evaluate_linkage_precision(pairs)
        assert result["false_positives"] == 1
        assert result["precision"] == 0.0
        assert result["false_link_rate"] == 1.0
