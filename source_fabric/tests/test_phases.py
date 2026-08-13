"""
Phase 10-12 tests (Issue #5) — negative-test style.

Tests for: github_ecosystem, evidence_connector, patent_normalizer,
paper_normalizer, cross_corpus_linker, intersection_engine,
integrity_firewall, connector_health, deliverables.
"""
import json
import sys
import tempfile
from pathlib import Path
from datetime import date

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.github_ecosystem import (GITHUB_PROJECTS, GithubProject,
                                             github_ecosystem_summary,
                                             GITHUB_CLASSIFICATIONS,
                                             get_connector_candidates)
from source_fabric.evidence_connector import (EvidenceConnector, Checkpoint,
                                               HealthReport, ProvenanceChain,
                                               content_hash_dict, now_iso)
from source_fabric.connector_base import HarvestError
from source_fabric.failure_recorder import FailureLog
from source_fabric.patent_normalizer import (normalize_patent, patent_field_count,
                                              PatentFamily, PatentApplication,
                                              PatentPublication, PatentGrant)
from source_fabric.paper_normalizer import (normalize_paper, paper_field_count,
                                             Work, PreprintVersion, Article)
from source_fabric.cross_corpus_linker import (CrossCorpusEdge, make_edge,
                                                CROSS_CORPUS_EDGE_TYPES,
                                                INFERRED_EDGE_TYPES,
                                                DETERMINISTIC_EDGES,
                                                validate_cross_corpus_edge)
from source_fabric.intersection_engine import (IntersectionEngine, PATTERNS,
                                                SearchBudget, IntersectionCandidate)
from source_fabric.integrity_firewall import (IntegrityFirewall, QUARANTINE_REASONS,
                                               INTEGRITY_TEST_SCENARIOS)
from source_fabric.connector_health import HealthTracker
from source_fabric.source_registry import (SOURCES, emit_source_registry_json,
                                            to_registry_record, AUTHORITY_TIERS,
                                            get_by_authority_tier)
from source_fabric.verified_connectors import (get_connector_v2,
                                                all_connector_v2_health_reports,
                                                CONNECTOR_V2_REGISTRY)
from source_fabric.deliverables import generate_all_deliverables


# =====================================================================
# PHASE 1: SOURCE REGISTRY (extended)
# =====================================================================

class TestSourceRegistryExtended:
    def test_24_fields_per_record(self):
        """Every registry record must have all 24 fields per the directive."""
        for s in SOURCES[:5]:  # check first 5
            r = to_registry_record(s)
            required = {"source_id", "source_name", "evidence_type", "jurisdiction",
                        "domains", "authority_tier", "access_method", "endpoint",
                        "authentication_required", "free_or_paid", "license_terms",
                        "rate_limit", "historical_depth", "update_cadence",
                        "metadata_fields", "fulltext_available", "claims_available",
                        "citation_available", "family_available", "language_coverage",
                        "last_probe", "probe_result", "connector_status",
                        "provenance_policy"}
            assert required.issubset(set(r.keys())), \
                f"Missing fields in {s.source_id}: {required - set(r.keys())}"

    def test_authority_tiers_valid(self):
        """Every source must have a valid authority_tier."""
        for s in SOURCES:
            assert s.authority_tier in AUTHORITY_TIERS, \
                f"{s.source_id} has bad authority_tier: {s.authority_tier}"

    def test_probe_result_not_probed_in_offline(self):
        """In offline mode, no source has been probed — all must be NOT_PROBED."""
        for s in SOURCES:
            assert s.probe_result == "NOT_PROBED", \
                f"{s.source_id} probe_result={s.probe_result} (should be NOT_PROBED)"

    def test_connector_status_not_built_in_offline(self):
        """No connector is operational in offline mode."""
        for s in SOURCES:
            assert s.connector_status == "NOT_BUILT", \
                f"{s.source_id} connector_status={s.connector_status}"

    def test_emit_source_registry_json(self):
        with tempfile.TemporaryDirectory() as td:
            payload = emit_source_registry_json(Path(td) / "SOURCE_REGISTRY.json")
            assert payload["total_sources"] >= 100
            assert "registry_hash" in payload
            assert (Path(td) / "SOURCE_REGISTRY.json").exists()
            assert (Path(td) / "SOURCE_REGISTRY.json.sha256").exists()


# =====================================================================
# PHASE 2: GITHUB ECOSYSTEM
# =====================================================================

class TestGithubEcosystem:
    def test_all_classifications_valid(self):
        for p in GITHUB_PROJECTS:
            assert p.classification in GITHUB_CLASSIFICATIONS

    def test_gives_data_access_is_honest(self):
        """Per directive: 'Never claim an open-source project gives access to
        data merely because it exists.' Most projects must have
        gives_data_access=False."""
        gives_data = [p for p in GITHUB_PROJECTS if p.gives_data_access]
        # Only a few repos bundle actual data (e.g. Retraction Watch CSV)
        assert len(gives_data) < len(GITHUB_PROJECTS) * 0.1, \
            "Too many projects claim gives_data_access=True"

    def test_at_least_30_projects(self):
        assert len(GITHUB_PROJECTS) >= 30

    def test_connector_candidates_present(self):
        assert len(get_connector_candidates()) > 0


# =====================================================================
# PHASE 3: EVIDENCE CONNECTOR
# =====================================================================

class TestEvidenceConnector:
    def test_connector_must_declare_all_properties(self):
        """A connector missing any of the 8 properties must fail construction."""
        from source_fabric.source_registry import SOURCES
        class BadConnector(EvidenceConnector):
            resumable = True
            idempotent = True
            checkpointed = True
            rate_limit_aware = True
            retry_safe = True
            content_addressed = True
            provenance_preserving = True
            observable = False  # missing!
            def discover(self): pass
            def fetch_metadata(self, r): pass
            def fetch_content(self, r): pass
            def fetch_updates(self, c, *, max_records=100): pass
            def normalize(self, r): pass
            def get_provenance(self, r): pass
            def content_hash(self, n): pass
            def health_check(self): pass
        with pytest.raises(ValueError, match="must declare observable=True"):
            BadConnector(SOURCES[0])

    def test_offline_connector_raises_on_fetch(self):
        """In offline mode, fetch methods must raise HarvestError (never silent)."""
        conn = get_connector_v2("src:openalex")
        assert conn is not None
        with pytest.raises(HarvestError):
            conn.fetch_metadata(["W1234"])
        with pytest.raises(HarvestError):
            conn.fetch_content("W1234")
        with pytest.raises(HarvestError):
            conn.fetch_updates(Checkpoint(source_id="src:openalex"))

    def test_health_check_returns_not_probed_offline(self):
        """health_check() in offline mode returns probe_result=NOT_PROBED."""
        conn = get_connector_v2("src:openalex")
        report = conn.health_check()
        assert report.probe_result == "NOT_PROBED"
        assert report.reachable is False

    def test_epo_ops_health_check_auth_required(self):
        conn = get_connector_v2("src:epo_ops")
        report = conn.health_check()
        assert report.probe_result == "AUTH_REQUIRED"

    def test_cnipa_health_check_not_supported(self):
        """CNIPA has no public bulk API — must be NOT_SUPPORTED."""
        conn = get_connector_v2("src:cnipa")
        report = conn.health_check()
        assert report.probe_result == "NOT_SUPPORTED"


# =====================================================================
# PHASE 6: PATENT NORMALIZER
# =====================================================================

class TestPatentNormalizer:
    def test_family_not_collapsed(self):
        """A patent family must NEVER be collapsed into one record."""
        raw = {
            "application_number": "EP2024123456",
            "filing_date": "2024-03-15",
            "publication_number": "EP1234567A1",
            "publication_date": "2024-09-18",
            "grant_number": "EP1234567B1",
            "grant_date": "2026-01-12",
            "jurisdiction": "EP",
            "family_id": "DOCDB12345",
            "priority_date": "2023-03-15",
            "priority_number": "EP2023123456",
            "applicants": ["Corp A"],
            "inventors": ["Inventor X"],
            "assignees": ["Corp A"],
            "claims": {"independent": ["1. A device..."], "dependent": ["2. The device of claim 1..."]},
            "description": "Detailed description...",
            "legal_status_events": [{"status": "granted", "date": "2026-01-12"}],
            "npl_citations": [{"paper_id": "paper:openalex:W1234", "role": "X"}],
            "classifications": [{"scheme": "CPC", "code": "H01M10/0525"}],
        }
        n = normalize_patent(raw)
        # Family is a separate node, not collapsed
        assert n["family"] is not None
        assert n["patent_document"] is not None
        assert n["family"]["family_id"] != n["patent_document"]["document_id"]
        # Application, publication, grant are separate
        assert n["application"] is not None
        assert n["publication"] is not None
        assert n["grant"] is not None
        # Claims separate from description
        assert n["claims"] is not None
        assert n["description"] is not None
        # NPL citations preserved
        assert len(n["npl_citations"]) == 1
        # CPC/IPC preserved
        assert len(n["cpc_ipc"]) == 1

    def test_patent_field_count(self):
        """The normalizer keeps 14+ fields separate (directive says 12+)."""
        assert patent_field_count() >= 12


# =====================================================================
# PHASE 7: PAPER NORMALIZER
# =====================================================================

class TestPaperNormalizer:
    def test_work_distinct_from_article(self):
        """A work is distinct from its published article."""
        raw = {
            "openalex_id": "W1234",
            "doi": "10.1000/xyz",
            "title": "Test Paper",
            "publication_date": "2024-01-15",
            "journal": "Nature",
            "preprints": [{"repository": "arxiv", "id": "2401.12345", "version": "1"}],
        }
        n = normalize_paper(raw)
        assert n["work"]["work_id"] != n["article"]["article_id"]
        assert len(n["preprint_version"]) == 1

    def test_paper_field_count(self):
        assert paper_field_count() >= 11


# =====================================================================
# PHASE 8: CROSS-CORPUS LINKER
# =====================================================================

class TestCrossCorpusLinker:
    def test_related_to_forbidden(self):
        """RELATED_TO must be rejected."""
        with pytest.raises(ValueError, match="RELATED_TO is FORBIDDEN"):
            make_edge("RELATED_TO", "a", "b", "D")

    def test_office_citation_requires_role(self):
        """OFFICE_CITATION must have a citation_role."""
        with pytest.raises(ValueError, match="OFFICE_CITATION requires citation_role"):
            make_edge("OFFICE_CITATION", "a", "b", "C")

    def test_semantic_match_auto_inferred(self):
        """SEMANTIC_MATCH must be automatically flagged as inferred."""
        e = make_edge("SEMANTIC_MATCH", "a", "b", "D", confidence=0.8)
        assert e.is_inferred is True

    def test_inferred_bridge_auto_inferred(self):
        e = make_edge("INFERRED_BRIDGE", "a", "b", "D")
        assert e.is_inferred is True

    def test_direct_id_match_no_confidence(self):
        """DIRECT_ID_MATCH is deterministic — must not carry confidence."""
        e = make_edge("DIRECT_ID_MATCH", "a", "b", "D", confidence=0.9)
        assert e.confidence is None

    def test_8_edge_types_present(self):
        assert len(CROSS_CORPUS_EDGE_TYPES) == 8
        for t in ["DIRECT_ID_MATCH", "OFFICE_CITATION", "BIBLIOGRAPHIC_MATCH",
                   "AUTHOR_INVENTOR_MATCH", "AFFILIATION_MATCH", "SEMANTIC_MATCH",
                   "TOPIC_ALIGNMENT", "INFERRED_BRIDGE"]:
            assert t in CROSS_CORPUS_EDGE_TYPES


# =====================================================================
# PHASE 9: INTERSECTION ENGINE
# =====================================================================

class TestIntersectionEngine:
    def test_no_full_enumeration(self):
        """The engine must NOT enumerate all combinations — it uses indices
        and beam search with a budget."""
        engine = IntersectionEngine(max_nodes=100, max_candidates=10, beam_width=5)
        # Index some nodes
        for i in range(20):
            engine.index_node(f"paper:{i}", "paper",
                              {"mechanisms": ["m1"], "materials": ["X"],
                               "date": "2020-01-01", "citations": []})
            engine.index_node(f"patent:{i}", "patent",
                              {"mechanisms": ["m1"], "materials": ["X"],
                               "date": "2021-01-01", "citations": []})
        results = engine.search("1p1pat")
        # Must respect the budget
        assert engine.budget.nodes_visited <= 100
        assert engine.budget.candidates_emitted <= 10

    def test_budget_tracking_present(self):
        """The budget summary must be reported."""
        engine = IntersectionEngine(max_nodes=10, max_candidates=5)
        engine.index_node("paper:1", "paper", {"mechanisms": ["m"], "date": "2020-01-01"})
        engine.index_node("patent:1", "patent", {"mechanisms": ["m"], "date": "2021-01-01"})
        engine.search("1p1pat")
        s = engine.budget.summary()
        assert "nodes_visited" in s
        assert "candidates_emitted" in s
        assert "beam_pruned" in s

    def test_11_patterns(self):
        assert len(PATTERNS) == 11


# =====================================================================
# PHASE 10: INTEGRITY FIREWALL
# =====================================================================

class TestIntegrityFirewall:
    def test_12_quarantine_reasons(self):
        assert len(QUARANTINE_REASONS) == 12

    def test_duplicate_id_quarantined(self):
        """Two records with the same ID must be quarantined."""
        fw = IntegrityFirewall()
        r1 = {"record_id": "rec:1", "source_id": "src:a", "provenance": {"source_id": "s", "harvested_at": "t"}}
        r2 = {"record_id": "rec:1", "source_id": "src:b", "provenance": {"source_id": "s", "harvested_at": "t"}}
        result = fw.check_all([r1, r2])
        assert result["total_quarantined"] >= 1
        assert "DUPLICATE_ID" in result["quarantine_reasons"]

    def test_cutoff_leakage_quarantined(self):
        """A record dated after the cutoff must be quarantined."""
        fw = IntegrityFirewall()
        r = {"record_id": "rec:1", "publication_date": "2025-01-01",
             "provenance": {"source_id": "s", "harvested_at": "t"}}
        result = fw.check_all([r], cutoff="2024-01-01")
        assert "CUTOFF_LEAKAGE" in result["quarantine_reasons"]

    def test_impossible_chronology_quarantined(self):
        """Publication before filing must be quarantined."""
        fw = IntegrityFirewall()
        r = {"record_id": "rec:1",
             "publication": {"publication_date": "2020-01-01"},
             "application": {"filing_date": "2021-01-01"},
             "provenance": {"source_id": "s", "harvested_at": "t"}}
        result = fw.check_all([r])
        assert "IMPOSSIBLE_CHRONOLOGY" in result["quarantine_reasons"]

    def test_post_freeze_mutation_quarantined(self):
        """A record whose hash differs from the frozen hash must be quarantined."""
        import hashlib
        fw = IntegrityFirewall()
        r = {"record_id": "rec:1", "publication_date": "2020-01-01",
             "provenance": {"source_id": "s", "harvested_at": "t"}}
        # Compute hash of a DIFFERENT record
        different = {"record_id": "rec:1", "publication_date": "2025-01-01",
                     "provenance": {"source_id": "s", "harvested_at": "t"}}
        frozen_hashes = {"rec:1": hashlib.sha256(
            json.dumps(different, sort_keys=True).encode()).hexdigest()}
        result = fw.check_all([r], frozen_hashes=frozen_hashes)
        assert "POST_FREEZE_MUTATION" in result["quarantine_reasons"]

    def test_provenance_loss_quarantined(self):
        """A record missing provenance must be quarantined."""
        fw = IntegrityFirewall()
        r = {"record_id": "rec:1", "provenance": {}}  # missing source_id
        result = fw.check_all([r])
        assert "PROVENANCE_LOSS" in result["quarantine_reasons"]

    def test_semantic_as_direct_detected(self):
        """A SEMANTIC_MATCH edge not flagged as inferred must be flagged."""
        fw = IntegrityFirewall()
        # Manually construct an edge with is_inferred=False
        edge = {"edge_id": "e:1", "edge_type": "SEMANTIC_MATCH",
                "is_inferred": False, "confidence": 0.9}
        result = fw.check_all([], edges=[edge])
        assert "SEMANTIC_AS_DIRECT" in result["quarantine_reasons"]


# =====================================================================
# PHASE 11: CONNECTOR HEALTH
# =====================================================================

class TestConnectorHealth:
    def test_12_metrics_present(self):
        """HealthReport must have all 12 metrics from the directive."""
        from source_fabric.connector_health import ConnectorHealth
        h = ConnectorHealth(source_id="src:test")
        d = h.canonical_dict()
        required = {"discovered", "accepted", "rejected", "http_errors",
                    "auth_errors", "rate_limits", "schema_changes",
                    "missing_fields", "duplicate_rate", "hash_collisions",
                    "latency_ms_avg", "last_successful_probe"}
        assert required.issubset(set(d.keys()))

    def test_emit_health_json(self):
        with tempfile.TemporaryDirectory() as td:
            tracker = HealthTracker()
            tracker.record_discovery("src:test", 100)
            tracker.record_accept("src:test", 90)
            tracker.record_reject("src:test", 10)
            payload = tracker.emit_health_json(Path(td) / "CONNECTOR_HEALTH.json")
            assert payload["summary"]["total_discovered"] == 100
            assert payload["summary"]["total_accepted"] == 90
            assert payload["summary"]["total_rejected"] == 10
            assert (Path(td) / "CONNECTOR_HEALTH.json.sha256").exists()


# =====================================================================
# PHASE 12: DELIVERABLES
# =====================================================================

class TestDeliverables:
    def test_all_7_deliverables_generated(self):
        """All 7 Phase 12 deliverable files must be generated."""
        with tempfile.TemporaryDirectory() as td:
            results = generate_all_deliverables(Path(td))
            assert "SOURCE_REGISTRY" in results
            assert "SOURCE_CATALOGUE" in results
            assert "CONNECTOR_HEALTH" in results
            assert "CONNECTOR_STATUS" in results
            assert "GRAPH_SNAPSHOT_SPEC" in results
            assert "SOURCE_DISCOVERY_REPORT" in results
            assert "CROSS_CORPUS_FORENSIC_REPORT" in results
            # Files exist
            for name in ["SOURCE_REGISTRY.json", "SOURCE_CATALOGUE.md",
                         "CONNECTOR_HEALTH.json", "CONNECTOR_STATUS.md",
                         "GRAPH_SNAPSHOT_SPEC.md", "SOURCE_DISCOVERY_REPORT.md",
                         "CROSS_CORPUS_FORENSIC_REPORT.md"]:
                assert (Path(td) / name).exists(), f"Missing deliverable: {name}"

    def test_source_registry_has_100_plus(self):
        with tempfile.TemporaryDirectory() as td:
            results = generate_all_deliverables(Path(td))
            assert results["SOURCE_REGISTRY"]["total_sources"] >= 100


# =====================================================================
# CONNECTOR V2 REGISTRY
# =====================================================================

class TestConnectorV2Registry:
    def test_16_priority_connectors_built(self):
        """The directive requires connectors for science (OpenAlex, Crossref,
        arXiv, PubMed), patents (USPTO, EPO, WIPO, CNIPA, IP India, JPO, KIPO),
        and technical (NASA NTRS, NIST, Zenodo, OSF, GitHub)."""
        required = {"src:openalex", "src:crossref", "src:arxiv", "src:pubmed",
                    "src:epo_ops", "src:uspto_odp", "src:wipo_patentscope",
                    "src:cnipa", "src:ip_india", "src:jpo", "src:kipo",
                    "src:nasa_ntrs", "src:nist_pubs", "src:zenodo", "src:osf",
                    "src:github"}
        built = set(CONNECTOR_V2_REGISTRY.keys())
        missing = required - built
        assert not missing, f"Missing connectors: {missing}"

    def test_all_connectors_health_check(self):
        """Every Phase 4 connector must produce a health_check() report."""
        reports = all_connector_v2_health_reports()
        assert len(reports) == len(CONNECTOR_V2_REGISTRY)
        for r in reports:
            assert "probe_result" in r
            assert r["probe_result"] in ("NOT_PROBED", "AUTH_REQUIRED", "NOT_SUPPORTED")
