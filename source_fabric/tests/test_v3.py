"""
V3 tests — real connectors, 3-hash model, regression tests (Issue #5 V3).

Negative-test style + regression tests for the content-hash invariant.
"""
import json
import sys
import tempfile
import hashlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.connector_base import (HarvestedRecord, HarvestError,
                                           CONNECTOR_STATUS_VOCAB, is_operational)
from source_fabric.evidence_connector import EvidenceConnector
from source_fabric.cross_corpus_linker import (CrossCorpusEdge, make_edge,
                                                CROSS_CORPUS_EDGE_TYPES)
from source_fabric.real_connectors import (OpenAlexRealConnector,
                                            EuropePmcRealConnector,
                                            GooglePatentsRealConnector,
                                            REAL_CONNECTOR_REGISTRY,
                                            get_real_connector)
from source_fabric.source_registry import SOURCES


# =====================================================================
# 1. THREE-HASH MODEL (V3 Phase 2)
# =====================================================================

class TestThreeHashModel:
    def test_identical_content_identical_normalized_hash(self):
        """REGRESSION: identical normalized content → identical normalized_content_hash,
        regardless of harvest timestamp, connector version, or provenance metadata."""
        norm = {"work_id": "W1234", "title": "Test", "doi": "10.1000/xyz"}
        r1 = HarvestedRecord(
            record_id="openalex:W1234", source_id="src:openalex",
            harvested_at="2026-01-01T00:00:00Z",
            raw_payload_hash="aaa", normalized=norm, normalized_hash="",
            connector_version="v1",
        )
        r2 = HarvestedRecord(
            record_id="openalex:W1234", source_id="src:openalex",
            harvested_at="2026-06-15T12:30:00Z",  # DIFFERENT timestamp
            raw_payload_hash="bbb",                # DIFFERENT raw hash
            normalized=norm,                        # SAME content
            normalized_hash="",
            connector_version="v2",                 # DIFFERENT version
        )
        assert r1.normalized_content_hash() == r2.normalized_content_hash()

    def test_different_content_different_normalized_hash(self):
        """Different normalized content → different normalized_content_hash."""
        r1 = HarvestedRecord(
            record_id="a", source_id="src", harvested_at="t",
            raw_payload_hash="x", normalized={"title": "A"}, normalized_hash="",
        )
        r2 = HarvestedRecord(
            record_id="b", source_id="src", harvested_at="t",
            raw_payload_hash="y", normalized={"title": "B"}, normalized_hash="",
        )
        assert r1.normalized_content_hash() != r2.normalized_content_hash()

    def test_manifest_hash_includes_provenance(self):
        """record_manifest_hash includes provenance metadata, so different
        harvest times → different manifest hashes even with same content."""
        norm = {"title": "Test"}
        r1 = HarvestedRecord(
            record_id="a", source_id="src",
            harvested_at="2026-01-01T00:00:00Z",
            raw_payload_hash="x", normalized=norm, normalized_hash="",
            connector_version="v1",
        )
        r2 = HarvestedRecord(
            record_id="a", source_id="src",
            harvested_at="2026-06-01T00:00:00Z",
            raw_payload_hash="x", normalized=norm, normalized_hash="",
            connector_version="v1",
        )
        # normalized_content_hash is the same
        assert r1.normalized_content_hash() == r2.normalized_content_hash()
        # but manifest_hash differs (different timestamp)
        assert r1.record_manifest_hash() != r2.record_manifest_hash()

    def test_raw_content_hash_uses_raw_bytes(self):
        """raw_content_hash is SHA-256 of the raw payload bytes."""
        raw = b'{"test": true}'
        r = HarvestedRecord(
            record_id="a", source_id="src", harvested_at="t",
            raw_payload_hash="stored", normalized={},
            normalized_hash="", raw_payload=raw,
        )
        import hashlib
        expected = hashlib.sha256(raw).hexdigest()
        assert r.raw_content_hash() == expected


# =====================================================================
# 2. CONNECTOR STATUS VOCABULARY (V3 Phase 3)
# =====================================================================

class TestConnectorStatusVocab:
    def test_six_statuses_present(self):
        """V3 requires exactly 6 statuses: DISCOVERED, CATALOGUED, IMPLEMENTED,
        PROBED, OPERATIONAL, FAILED."""
        assert CONNECTOR_STATUS_VOCAB == {
            "DISCOVERED", "CATALOGUED", "IMPLEMENTED",
            "PROBED", "OPERATIONAL", "FAILED",
        }

    def test_operational_only_after_real_probe(self):
        """is_operational returns True ONLY for 'OPERATIONAL' status."""
        for status in CONNECTOR_STATUS_VOCAB:
            if status == "OPERATIONAL":
                assert is_operational(status) is True
            else:
                assert is_operational(status) is False


# =====================================================================
# 3. OLD CONNECTOR IS DEPRECATED (V3 Phase 1)
# =====================================================================

class TestConnectorDeprecation:
    def test_old_connector_is_deprecated(self):
        """The old Connector class must be marked DEPRECATED."""
        from source_fabric.connector_base import Connector
        assert "DEPRECATED" in Connector.__doc__ or "deprecated" in Connector.__doc__.lower()

    def test_evidence_connector_is_sole_interface(self):
        """EvidenceConnector is the sole connector contract (8 methods + 8 properties)."""
        # EvidenceConnector has 8 abstract methods
        import inspect
        abstract_methods = [m for m in dir(EvidenceConnector)
                            if getattr(getattr(EvidenceConnector, m, None), '__isabstractmethod__', False)]
        assert len(abstract_methods) == 8


# =====================================================================
# 4. REAL CONNECTORS (V3 Phase 4) — LIVE TESTS
# =====================================================================

class TestRealConnectorsLive:
    """These tests make LIVE HTTP calls. They verify real data retrieval."""

    @pytest.mark.skip(reason="Live HTTP test - run manually with --run-live")
    def test_openalex_health_check_live(self):
        """OpenAlex health_check() performs a real live probe."""
        src = next(s for s in SOURCES if s.source_id == "src:openalex")
        conn = OpenAlexRealConnector(src)
        hr = conn.health_check()
        # Must be OK (we verified network access earlier)
        assert hr.probe_result == "OK"
        assert hr.reachable is True
        assert hr.http_status == 200
        assert hr.latency_ms > 0

    @pytest.mark.skip(reason="Live HTTP test - run manually with --run-live")
    def test_openalex_fetch_real_records(self):
        """OpenAlex fetch_updates retrieves REAL records (not synthetic)."""
        src = next(s for s in SOURCES if s.source_id == "src:openalex")
        conn = OpenAlexRealConnector(src)
        from source_fabric.evidence_connector import Checkpoint
        cp = Checkpoint(source_id="src:openalex")
        cp.last_error = "default.search:lithium battery"
        records, cp2 = conn.fetch_updates(cp, max_records=3)
        assert len(records) == 3
        assert conn.operational_status == "OPERATIONAL"
        # Each record has all 3 hashes
        r = records[0]
        assert r.raw_payload_hash  # raw hash
        assert r.normalized_content_hash()  # normalized hash
        assert r.record_manifest_hash()  # manifest hash
        # Record has real content (not empty)
        assert r.normalized.get("title", "") != ""
        assert r.normalized.get("work_id", "") != ""

    def test_openalex_normalized_hash_invariant(self):
        """REGRESSION: harvesting the same content twice yields the same
        normalized_content_hash (the V3 invariant)."""
        src = next(s for s in SOURCES if s.source_id == "src:openalex")
        conn = OpenAlexRealConnector(src)
        from source_fabric.evidence_connector import Checkpoint
        cp1 = Checkpoint(source_id="src:openalex")
        cp1.last_error = "default.search:lithium battery"
        records1, _ = conn.fetch_updates(cp1, max_records=2)
        if records1:
            # Re-fetch the same record by ID
            rid = records1[0].record_id.split("/")[-1]
            url = f"{conn.BASE_URL}/works/{rid}"
            from source_fabric.real_connectors import _http_get
            status, body, _ = _http_get(url, timeout=15)
            raw = json.loads(body)
            norm = conn.normalize(raw)
            # The normalized_content_hash should match (same content)
            assert records1[0].normalized_content_hash() == \
                   hashlib.sha256(json.dumps(norm, sort_keys=True, default=str).encode()).hexdigest()

    def test_europepmc_health_check_live(self):
        """Europe PMC health_check() performs a real live probe."""
        src = next(s for s in SOURCES if s.source_id == "src:pubmed")
        conn = EuropePmcRealConnector(src)
        hr = conn.health_check()
        assert hr.probe_result == "OK"
        assert hr.reachable is True

    def test_europepmc_fetch_real_records(self):
        """Europe PMC fetch_updates retrieves REAL records."""
        src = next(s for s in SOURCES if s.source_id == "src:pubmed")
        conn = EuropePmcRealConnector(src)
        from source_fabric.evidence_connector import Checkpoint
        cp = Checkpoint(source_id="src:pubmed")
        cp.last_error = "lithium battery"
        records, cp2 = conn.fetch_updates(cp, max_records=3)
        assert len(records) == 3
        assert conn.operational_status == "OPERATIONAL"
        assert records[0].normalized.get("title", "") != ""


# =====================================================================
# 5. CROSS-CORPUS EDGES (V3 Phase 8)
# =====================================================================

class TestCrossCorpusEdgesV3:
    def test_google_patents_labeled_secondary(self):
        """Google Patents connector must be labeled SECONDARY."""
        src = next(s for s in SOURCES if s.source_id == "src:google_patents")
        conn = GooglePatentsRealConnector(src)
        assert "SECONDARY" in conn.CONNECTOR_VERSION
        # normalize() includes is_secondary=True
        norm = conn.normalize({"publication_number": "US12345678",
                                "title": "test", "assignee": "Corp"})
        assert norm.get("is_secondary") is True
        assert "secondary" in norm.get("primary_authority", "").lower() or \
               norm.get("primary_authority") == "EPO/USPTO/CNIPA"

    def test_no_related_to_in_cross_corpus_edges(self):
        """RELATED_TO is forbidden in cross-corpus edges."""
        with pytest.raises(ValueError, match="RELATED_TO is FORBIDDEN"):
            make_edge("RELATED_TO", "a", "b", "D")


# =====================================================================
# 6. REAL DATA CONNECTOR REPORT (V3 Phase 6)
# =====================================================================

class TestRealDataConnectorReport:
    @pytest.mark.skip(reason="Live HTTP test - run manually with --run-live")
    def test_connector_report_generated(self):
        """REAL_DATA_CONNECTOR_REPORT.json is generated with proof fields."""
        from source_fabric.real_data_report import generate_real_data_connector_report
        with tempfile.TemporaryDirectory() as td:
            report = generate_real_data_connector_report(Path(td))
            assert "connector_proofs" in report
            assert report["total_connectors_probed"] >= 2
            # At least OpenAlex should be operational
            oa_proof = next(p for p in report["connector_proofs"]
                            if p["source_id"] == "src:openalex")
            assert oa_proof["status"] == "OPERATIONAL"
            assert oa_proof["records_sampled"] > 0
            assert oa_proof["discovery_proven"] is True
            assert oa_proof["metadata_retrieval_proven"] is True
            assert oa_proof["hashing_proven"] is True
            assert oa_proof["first_normalized_hash"] != ""


# =====================================================================
# 7. REAL PILOT SNAPSHOT (V3 Phase 7)
# =====================================================================

class TestRealPilotSnapshot:
    def test_pilot_snapshot_has_real_data(self):
        """The pilot snapshot contains REAL records (not synthetic)."""
        # This test uses the snapshot already built in v3_output
        report_path = REPO / "source_fabric" / "v3_output" / "REAL_PILOT_SNAPSHOT_REPORT.json"
        if not report_path.exists():
            pytest.skip("pilot snapshot not built yet")
        report = json.loads(report_path.read_text())
        assert report["is_real_data"] is True
        assert report["no_synthetic_data"] is True
        sr = report["snapshot_result"]
        assert sr["science_records"] > 0
        assert sr["total_records"] > 0
        assert len(sr["domains"]) >= 5
        assert sr["real_snapshot_hash"] != ""
        assert report["snapshot_verification"]["valid"] is True
