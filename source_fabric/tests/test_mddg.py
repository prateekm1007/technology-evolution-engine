"""
Medical Device Discovery Graph V1 — Tests (CTO directive #2, #4, #5, #7, #8, #9).
"""
import json
import sys
import tempfile
from pathlib import Path
from dataclasses import asdict

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.evidence_classes import (get_evidence_class, is_classified,
                                             quarantine_unclassified, EVIDENCE_CLASSES)
from source_fabric.mddg.ontology import (Entity, ENTITY_TYPES, make_device,
                                           make_failure_mode, make_mechanism)
from source_fabric.mddg.edges import (MDDGEdge, make_mddg_edge, MissingLink,
                                       TIER_A_RELATIONS, TIER_B_RELATIONS,
                                       TIER_C_RELATIONS, is_evidence, get_tier,
                                       ALL_MDDG_RELATIONS, MISSING_LINK_STATES)
from source_fabric.mddg.failure_taxonomy import (FAILURE_MODES, is_valid_failure_mode,
                                                  classify_failure_from_text)
from source_fabric.mddg.lifecycle import LifecycleReconstructor, DeviceLifecycle


# =====================================================================
# #2. FAIL-CLOSED EVIDENCE CLASSIFICATION (P0)
# =====================================================================

class TestFailClosedEvidence:
    def test_unknown_source_not_scientific(self):
        """Unknown source_id must NOT default to SCIENTIFIC_OBSERVATION."""
        ec = get_evidence_class("src:nonexistent_source")
        assert ec == "UNCLASSIFIED"
        assert ec != "SCIENTIFIC_OBSERVATION"

    def test_unknown_source_quarantined(self):
        """Unknown source produces a quarantine record."""
        q = quarantine_unclassified("src:typo_source", "rec:123")
        assert q["evidence_class"] == "UNCLASSIFIED"
        assert q["quarantine_reason"] == "UNKNOWN_SOURCE"
        assert q["action"] == "QUARANTINED"

    def test_known_source_classified(self):
        """Known sources get their proper evidence class."""
        assert get_evidence_class("src:openalex") == "SCIENTIFIC_OBSERVATION"
        assert get_evidence_class("src:fda_maude") == "ADVERSE_EVENT"

    def test_is_classified_rejects_unclassified(self):
        assert is_classified("UNCLASSIFIED") is False
        assert is_classified("SCIENTIFIC_OBSERVATION") is True


# =====================================================================
# #3. ONTOLOGY — 18 ENTITY TYPES
# =====================================================================

class TestOntology:
    def test_18_entity_types(self):
        assert len(ENTITY_TYPES) == 18

    def test_entity_has_6_mandatory_fields(self):
        """Every entity has canonical_id, source_ids, provenance, jurisdiction,
        date_range, confidence_status."""
        d = make_device(device_id="K123", source_ids=("src:fda_510k",),
                        provenance=({"source": "src:fda_510k"},),
                        date_range=("2020-01-01", "2020-01-01"))
        assert d.canonical_id == "device:K123"
        assert d.source_ids == ("src:fda_510k",)
        assert len(d.provenance) > 0
        assert d.jurisdiction == "US"
        assert d.date_range == ("2020-01-01", "2020-01-01")
        assert d.confidence_status == "VERIFIED"

    def test_bad_entity_type_rejected(self):
        with pytest.raises(ValueError, match="Bad entity_type"):
            Entity(canonical_id="x", entity_type="NOT_A_TYPE",
                   source_ids=(), provenance=(), jurisdiction="",
                   date_range=(None, None))


# =====================================================================
# #4, #5. TYPED EDGES — 3 TIERS
# =====================================================================

class TestTypedEdges:
    def test_3_tiers_present(self):
        assert len(TIER_A_RELATIONS) >= 9   # structural
        assert len(TIER_B_RELATIONS) >= 12  # substantive
        assert len(TIER_C_RELATIONS) >= 4   # inferred

    def test_tier_c_never_evidence(self):
        """Tier C edges must have evidence_status=SEARCH_ONLY."""
        e = make_mddg_edge(
            "SEMANTIC_SIMILARITY", "device:1", "paper:1",
            provenance="", source_field="title",
            retrieval_time="2026-01-01T00:00:00Z", temporal_validity="unknown",
            derivation_method="embedding",
            evidence_status="EVIDENCE",  # try to set EVIDENCE — should be overridden
        )
        assert e.tier == "C"
        assert e.evidence_status == "SEARCH_ONLY"
        assert is_evidence("SEMANTIC_SIMILARITY") is False

    def test_tier_a_is_evidence(self):
        e = make_mddg_edge(
            "DEVICE_HAS_510K", "device:1", "regulatory:1",
            provenance="src:fda_510k", source_field="k_number",
            retrieval_time="2026-01-01T00:00:00Z", temporal_validity="valid",
            derivation_method="exact_id_match",
        )
        assert e.tier == "A"
        assert e.evidence_status == "EVIDENCE"
        assert is_evidence("DEVICE_HAS_510K") is True

    def test_tier_b_is_evidence(self):
        e = make_mddg_edge(
            "PAPER_DESCRIBES_MECHANISM", "paper:1", "mechanism:1",
            provenance="src:openalex", source_field="abstract",
            retrieval_time="2026-01-01T00:00:00Z", temporal_validity="valid",
            derivation_method="text_extraction",
        )
        assert e.tier == "B"
        assert e.evidence_status == "EVIDENCE"

    def test_related_to_forbidden(self):
        """RELATED_TO must be rejected — it's not in the vocabulary."""
        with pytest.raises(ValueError, match="Bad relation_type: 'RELATED_TO'"):
            make_mddg_edge("RELATED_TO", "a", "b",
                          provenance="", source_field="",
                          retrieval_time="", temporal_validity="",
                          derivation_method="")

    def test_edge_has_9_mandatory_fields(self):
        e = make_mddg_edge(
            "DEVICE_HAS_RECALL", "device:1", "recall:1",
            provenance="src:fda_recalls", source_field="product_code",
            retrieval_time="2026-01-01T00:00:00Z", temporal_validity="valid",
            derivation_method="product_code_match",
        )
        d = e.canonical_dict()
        for f in ["relation_type", "source", "target", "provenance",
                   "source_field", "retrieval_time", "temporal_validity",
                   "derivation_method", "evidence_status"]:
            assert f in d


# =====================================================================
# #7. FAILURE TAXONOMY
# =====================================================================

class TestFailureTaxonomy:
    def test_18_failure_modes(self):
        assert len(FAILURE_MODES) == 18

    def test_classify_mechanical_failure(self):
        fms = classify_failure_from_text("The device suffered a mechanical failure due to fracture.")
        assert "MECHANICAL_FAILURE" in fms

    def test_classify_battery_failure(self):
        fms = classify_failure_from_text("The implantable pacemaker experienced premature battery depletion.")
        assert "BATTERY_FAILURE" in fms

    def test_classify_infection(self):
        fms = classify_failure_from_text("Patient developed infection and sepsis after implant.")
        assert "INFECTION" in fms

    def test_classify_empty_text(self):
        fms = classify_failure_from_text("")
        assert fms == []


# =====================================================================
# #6. MISSING LINKS
# =====================================================================

class TestMissingLinks:
    def test_missing_link_states(self):
        assert "UNKNOWN" in MISSING_LINK_STATES
        assert "NOT_FOUND" in MISSING_LINK_STATES
        assert "NOT_APPLICABLE" in MISSING_LINK_STATES
        assert "SOURCE_NOT_AVAILABLE" in MISSING_LINK_STATES

    def test_missing_link_rejects_bad_state(self):
        with pytest.raises(ValueError, match="Bad missing-link state"):
            MissingLink(source="device:1", expected_target_type="PATENT",
                        state="MAYBE_EXISTS")


# =====================================================================
# #6. LIFECYCLE RECONSTRUCTION
# =====================================================================

class TestLifecycleReconstruction:
    def test_device_lifecycle_chain_length(self):
        """A lifecycle with device + adverse_event + failure_mode + paper has length 4."""
        lc = DeviceLifecycle(device=make_device(
            device_id="K1", source_ids=("src:fda_510k",),
            provenance=({},), date_range=("2020-01-01", "2020-01-01")))
        assert lc.lifecycle_chain_length() == 1
        lc.adverse_events.append(make_adverse_event_helper())
        assert lc.lifecycle_chain_length() == 2
        lc.failure_modes.append(make_failure_mode_helper())
        assert lc.lifecycle_chain_length() == 3

    def test_reconstructor_records_missing_links(self):
        """Devices without linked records get explicit missing-link records."""
        recon = LifecycleReconstructor()
        recon.add_fda_510k({
            "k_number": "K123456",
            "applicant": "TestCorp",
            "product_code": "XYZ",
            "device_name": "Test Device",
            "decision_date": "2020-01-01",
            "_harvested_at": "2026-01-01",
            "_raw_hash": "abc",
        })
        recon.record_missing_links()
        # Should have missing links for patent, paper, trial, adverse_event, recall, failure_mode
        missing_types = [ml.expected_target_type for ml in recon.all_missing_links]
        assert "PATENT" in missing_types
        assert "PAPER" in missing_types
        assert "CLINICAL_TRIAL" in missing_types
        assert "ADVERSE_EVENT" in missing_types


def make_adverse_event_helper():
    from source_fabric.mddg.ontology import make_adverse_event
    return make_adverse_event(event_id="12345", source_ids=("src:fda_maude",),
                              provenance=({},), date_range=("2020-01-01", "2020-01-01"))

def make_failure_mode_helper():
    from source_fabric.mddg.ontology import make_failure_mode
    return make_failure_mode(name="BATTERY_FAILURE", source_ids=("src:fda_maude",),
                             provenance=({},))


# =====================================================================
# #11. EXIT CRITERION — manifest from real pilot
# =====================================================================

class TestMDDGManifest:
    def test_manifest_exists(self):
        manifest_path = REPO / "source_fabric" / "mddg_output" / "MDDG_V1_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("MDDG manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        s = manifest["summary"]
        # Must have all 15 fields per directive #11
        for field in ["devices_ingested", "papers_linked", "patents_linked",
                       "trials_linked", "adverse_events_linked", "recalls_linked",
                       "failure_modes_extracted", "structural_edges",
                       "substantive_edges", "inferred_edges", "unresolved_links",
                       "provenance_completeness", "temporal_integrity",
                       "duplicate_rate", "orphan_rate"]:
            assert field in s, f"Missing field: {field}"

    def test_real_lifecycle_chains_gt_0(self):
        """REAL_LIFECYCLE_CHAINS must be > 0 (directive #11)."""
        manifest_path = REPO / "source_fabric" / "mddg_output" / "MDDG_V1_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("MDDG manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        ec = manifest["exit_criterion"]
        assert ec["REAL_LIFECYCLE_CHAINS"] > 0

    def test_null_controls_present(self):
        """All 5 null controls must be in the manifest."""
        manifest_path = REPO / "source_fabric" / "mddg_output" / "MDDG_V1_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("MDDG manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        nulls = manifest["null_controls"]
        for null_name in ["NULL_A_TEMPORAL_SHUFFLE", "NULL_B_SINGLE_CORPUS_ONLY",
                           "NULL_C_DEGREE_MATCHED", "NULL_D_SEMANTIC_ONLY",
                           "NULL_E_FAILURE_UNRELATED"]:
            assert null_name in nulls

    def test_no_discovery_claims(self):
        manifest_path = REPO / "source_fabric" / "mddg_output" / "MDDG_V1_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("MDDG manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        assert manifest["honest_boundaries"]["no_discovery_claims"] is True
        assert manifest["honest_boundaries"]["tier_c_never_evidence"] is True
        assert manifest["honest_boundaries"]["missing_links_explicitly_recorded"] is True
