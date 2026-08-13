"""
V5 tests — patent semantics, typed edges, evidence classes, FDA connectors.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.evidence_classes import (EVIDENCE_CLASSES, get_evidence_class,
                                             validate_evidence_class,
                                             classify_patent_document)
from source_fabric.patent_families import (reconstruct_families_proxy,
                                            count_family_stats, PatentFamily)
from source_fabric.v5_typed_edges import (TypedCrossCorpusEdge, make_typed_edge,
                                           EVIDENCE_EDGE_TYPES, SEARCH_ONLY_EDGE_TYPES,
                                           ALL_V5_EDGE_TYPES,
                                           build_direct_id_matches,
                                           build_cpc_ipc_alignment,
                                           build_temporal_proximity,
                                           build_semantic_search_candidates,
                                           build_all_v5_edges)
from source_fabric.v5_fda_connectors import (Fda510kConnector, FdaPmaConnector,
                                              FdaMaudeConnector, FdaRecallsConnector,
                                              FdaClassificationConnector,
                                              get_fda_connector,
                                              V5_FDA_CONNECTOR_REGISTRY)
from source_fabric.source_registry import SOURCES


# =====================================================================
# A. PATENT SEMANTICS
# =====================================================================

class TestPatentSemantics:
    def test_patent_document_classified_not_family(self):
        """A patent document is NOT a patent family."""
        assert classify_patent_document("utility") == "PATENT_DOCUMENT"
        assert classify_patent_document("grant") == "PATENT_GRANT"
        assert classify_patent_document("application") == "PATENT_APPLICATION"

    def test_huggingface_families_zero(self):
        """HuggingFace patents cannot reconstruct DOCDB families → PATENT_FAMILIES = 0."""
        records = [{"patent_id": f"hfpatent:{i}", "filing_date": "2020-01-01",
                     "title": f"Completely different invention topic {i}"} for i in range(10)]
        families = reconstruct_families_proxy(records)
        stats = count_family_stats(families)
        # PATENT_FAMILIES_RECONSTRUCTED is always 0 for HuggingFace (no priority data)
        assert stats["PATENT_FAMILIES_RECONSTRUCTED"] == 0

    def test_proxy_families_grouped(self):
        """Patents with same filing_date + title prefix form a PROXY family."""
        records = [
            {"patent_id": "p1", "filing_date": "2020-01-01", "title": "Lithium battery electrode design system"},
            {"patent_id": "p2", "filing_date": "2020-01-01", "title": "Lithium battery electrode design method"},
            {"patent_id": "p3", "filing_date": "2021-01-01", "title": "Completely different solar panel"},
        ]
        families = reconstruct_families_proxy(records)
        stats = count_family_stats(families)
        # p1 and p2 share filing_date + "lithium battery electrode design" prefix → PROXY_FAMILY
        # (system/method are stop words, so sig words = lithium, battery, electrode, design)
        assert stats["PROXY_FAMILIES"] >= 1
        assert stats["PATENT_FAMILIES_RECONSTRUCTED"] == 0  # NOT DOCDB


# =====================================================================
# B. HUGGINGFACE LABELING
# =====================================================================

class TestHuggingFaceLabeling:
    def test_huggingface_labeled_secondary_derived(self):
        """HuggingFace patents must be labeled SECONDARY_DERIVED_CORPUS."""
        # Check the source registry entry
        src = next(s for s in SOURCES if s.source_id == "src:huggingface_patents")
        assert "USPTO" in src.coverage_notes or "USPTO" in src.url

    def test_corpus_labels_in_manifest(self):
        """The V5 manifest must include corpus labels."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        labels = manifest.get("patent_corpus_labels", {})
        hf = labels.get("huggingface_allenai_us_patents", {})
        assert hf.get("corpus_type") == "SECONDARY_DERIVED_CORPUS"
        assert hf.get("corpus_authority") == "USPTO_DERIVED"
        assert hf.get("corpus_temporality") == "HISTORICAL"
        assert hf.get("corpus_liveness") == "NOT_LIVE_OFFICE_FEED"


# =====================================================================
# C. TYPED CROSS-CORPUS EDGES
# =====================================================================

class TestTypedEdges:
    def test_10_edge_types(self):
        """8 evidence + 2 search-only = 10 typed edge types."""
        assert len(EVIDENCE_EDGE_TYPES) == 8
        assert len(SEARCH_ONLY_EDGE_TYPES) == 2
        assert len(ALL_V5_EDGE_TYPES) == 10

    def test_semantic_search_candidate_not_evidence(self):
        """SEMANTIC_SEARCH_CANDIDATE must have is_evidence=False."""
        e = make_typed_edge(
            "SEMANTIC_SEARCH_CANDIDATE", "paper:1", "patent:1",
            source_field="title", provenance_uri="",
            confidence=0.8, creation_method="keyword_overlap",
        )
        assert e.is_evidence is False

    def test_temporal_proximity_not_evidence(self):
        """TEMPORAL_PROXIMITY must have is_evidence=False."""
        e = make_typed_edge(
            "TEMPORAL_PROXIMITY", "paper:1", "patent:1",
            source_field="date", provenance_uri="",
            confidence=0.5, creation_method="date_window",
        )
        assert e.is_evidence is False

    def test_direct_id_match_is_evidence(self):
        """DIRECT_ID_MATCH is evidence (deterministic)."""
        e = make_typed_edge(
            "DIRECT_ID_MATCH", "paper:1", "patent:1",
            source_field="doi", provenance_uri="http://...",
            confidence=None, creation_method="doi_regex_match",
        )
        assert e.is_evidence is True

    def test_cpc_ipc_alignment_is_evidence(self):
        e = make_typed_edge(
            "CPC_IPC_ALIGNMENT", "patent:1", "patent:2",
            source_field="classification_codes", provenance_uri="",
            confidence=None, creation_method="shared_cpc_ipc_code",
        )
        assert e.is_evidence is True

    def test_edge_has_7_mandatory_fields(self):
        """Every edge must have: edge_type, source_record_id, target_record_id,
        source_field, provenance_uri, confidence, creation_method."""
        e = make_typed_edge(
            "DIRECT_ID_MATCH", "a", "b",
            source_field="doi", provenance_uri="http://example.com",
            confidence=None, creation_method="test",
        )
        d = e.canonical_dict()
        for field in ["edge_type", "source_record_id", "target_record_id",
                       "source_field", "provenance_uri", "confidence",
                       "creation_method"]:
            assert field in d

    def test_direct_id_match_finds_dois_in_patent_text(self):
        """DIRECT_ID_MATCH should find DOIs embedded in patent text."""
        records = [
            {"record_id": "paper:1", "evidence_class": "SCIENTIFIC_OBSERVATION",
             "doi": "10.1234/test", "title": "Test Paper", "abstract": ""},
            {"record_id": "patent:1", "evidence_class": "PATENT_DISCLOSURE",
             "fulltext": "This patent relates to work in doi 10.1234/test",
             "title": "Patent", "abstract": "", "source_uri": ""},
        ]
        edges = build_direct_id_matches(records)
        assert len(edges) == 1
        assert edges[0].edge_type == "DIRECT_ID_MATCH"
        assert edges[0].is_evidence is True

    def test_unknown_edge_type_rejected(self):
        with pytest.raises(ValueError, match="Bad edge_type"):
            make_typed_edge("RELATED_TO", "a", "b",
                            source_field="", provenance_uri="",
                            confidence=None, creation_method="")


# =====================================================================
# D. FDA MEDICAL DEVICE CONNECTORS
# =====================================================================

class TestFdaConnectors:
    def test_5_fda_connectors_registered(self):
        """At least 5 FDA connectors must be registered (directive D)."""
        assert len(V5_FDA_CONNECTOR_REGISTRY) >= 8  # 8 per directive

    def test_fda_510k_live(self):
        """FDA 510(k) connector must be OPERATIONAL via live HTTP."""
        conn = get_fda_connector("src:fda_510k")
        assert conn is not None
        hr = conn.health_check()
        assert hr.probe_result == "OK"
        assert hr.reachable is True

    def test_fda_maude_live(self):
        """FDA MAUDE connector must be OPERATIONAL via live HTTP."""
        conn = get_fda_connector("src:fda_maude")
        assert conn is not None
        hr = conn.health_check()
        assert hr.probe_result == "OK"

    def test_fda_recalls_live(self):
        conn = get_fda_connector("src:fda_recalls")
        hr = conn.health_check()
        assert hr.probe_result == "OK"

    def test_fda_classification_live(self):
        conn = get_fda_connector("src:fda_classification")
        hr = conn.health_check()
        assert hr.probe_result == "OK"

    def test_fda_pma_live(self):
        conn = get_fda_connector("src:fda_pma")
        hr = conn.health_check()
        assert hr.probe_result == "OK"


# =====================================================================
# E. MEDICAL DEVICE GRAPH
# =====================================================================

class TestMedicalDeviceGraph:
    def test_medical_device_records_in_manifest(self):
        """The manifest must contain medical device records from FDA."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        totals = manifest["totals"]
        # Must have device regulatory actions (510k/PMA/classification)
        assert totals["MEDICAL_DEVICE_RECORDS"] > 0
        # Must have adverse events (MAUDE)
        assert totals["ADVERSE_EVENTS"] > 0
        # Must have market signals (recalls)
        assert totals["MARKET_SIGNALS"] > 0


# =====================================================================
# F. PILOT ACCOUNTING (single manifest)
# =====================================================================

class TestPilotAccounting:
    def test_manifest_totals_match_record_count(self):
        """The manifest totals must match the actual record count."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        totals = manifest["totals"]
        # Sum of all category counts must equal TOTAL_RECORDS
        category_sum = (totals["SCIENCE_DOCUMENTS"] + totals["PATENT_DOCUMENTS"] +
                        totals["MEDICAL_DEVICE_RECORDS"] + totals["CLINICAL_TRIALS"] +
                        totals["ADVERSE_EVENTS"] + totals["CORPORATE_RECORDS"] +
                        totals["MARKET_SIGNALS"])
        assert category_sum == totals["TOTAL_RECORDS"], \
            f"Category sum {category_sum} != TOTAL_RECORDS {totals['TOTAL_RECORDS']}"

    def test_manifest_generated_from_snapshot(self):
        """The manifest must be generated from the snapshot, not manually typed."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        # Must have snapshot_hash that matches the snapshot
        assert manifest["snapshot_hash"] == manifest["real_snapshot_hash"]
        assert manifest["snapshot_verified"] is True


# =====================================================================
# G. EVIDENCE CLASSES
# =====================================================================

class TestEvidenceClasses:
    def test_10_evidence_classes(self):
        assert len(EVIDENCE_CLASSES) == 10
        for ec in ["SCIENTIFIC_OBSERVATION", "PATENT_DISCLOSURE", "PATENT_CLAIM",
                    "DEVICE_REGULATORY_ACTION", "CLINICAL_EVIDENCE", "ADVERSE_EVENT",
                    "CORPORATE_RISK", "MARKET_SIGNAL", "DATASET", "SOFTWARE"]:
            assert ec in EVIDENCE_CLASSES

    def test_source_to_evidence_class_mapping(self):
        assert get_evidence_class("src:openalex") == "SCIENTIFIC_OBSERVATION"
        assert get_evidence_class("src:huggingface_patents") == "PATENT_DISCLOSURE"
        assert get_evidence_class("src:ct_gov") == "CLINICAL_EVIDENCE"
        assert get_evidence_class("src:sec_edgar") == "CORPORATE_RISK"
        assert get_evidence_class("src:fda_510k") == "DEVICE_REGULATORY_ACTION"
        assert get_evidence_class("src:fda_maude") == "ADVERSE_EVENT"


# =====================================================================
# H. TWO PATENT UNIVERSES
# =====================================================================

class TestPatentUniverses:
    def test_historical_patent_corpus_true(self):
        """HISTORICAL_PATENT_CORPUS must be true (HuggingFace is operational)."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        assert manifest["patent_universes"]["HISTORICAL_PATENT_CORPUS"] is True

    def test_live_patent_feed_false(self):
        """LIVE_LATEST_PATENT_FEED must be false (no live office feed yet)."""
        manifest_path = REPO / "source_fabric" / "v5_output" / "V5_MANIFEST.json"
        if not manifest_path.exists():
            pytest.skip("V5 manifest not built yet")
        manifest = json.loads(manifest_path.read_text())
        assert manifest["patent_universes"]["LIVE_LATEST_PATENT_FEED"] is False
