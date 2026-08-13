"""
Source Fabric tests (Issue #5).

Negative-test style: every test constructs a BAD condition, runs the system,
and asserts the system BLOCKS or REJECTS.

Run:
    python -m pytest source_fabric/tests/test_fabric.py -v
"""
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from source_fabric.source_registry import (SOURCES, Source, registry_manifest,
                                            get_primary_sources, get_by_evidence_type)
from source_fabric.domain_map import DOMAINS, UNIVERSES, domain_distance, universe_distance
from source_fabric.connector_base import (Connector, HarvestState, HarvestedRecord,
                                           HarvestError, hash_payload, now_iso)
from source_fabric.provenance import (ProvenanceEdge, PREDICATES, CROSS_CORPUS_PREDICATES,
                                       EMPIRICAL_PREDICATES, validate_edge)
from source_fabric.multilingual import (MultilingualText, make_translation,
                                         validate_multilingual_pair,
                                         is_supported_language)
from source_fabric.failure_recorder import FailureLog, FailureRecord, FAILURE_TYPES
from source_fabric.snapshot_manager import (create_snapshot, verify_snapshot,
                                             is_frozen, SnapshotManifest)
from source_fabric.source_validator import (validate_source_structural,
                                             validate_all_sources,
                                             OpenAlexConnector, EpoOpsConnector,
                                             GithubCodeConnector,
                                             get_connector)
from source_fabric.knowledge_distance import compute_distance, WEIGHTS
from source_fabric.cross_evidence_motifs import (ALL_CROSS_EVIDENCE_MOTIFS,
                                                  motif_c01_paper_patent_standard,
                                                  motif_c02_paper_patent_dataset,
                                                  motif_c05_paper_patent_failure)
from source_fabric.orchestrator import run_fabric, forensic_audit


# =====================================================================
# 1. SOURCE REGISTRY
# =====================================================================

class TestSourceRegistry:
    def test_at_least_100_sources(self):
        """Issue #5 requires 100+ source candidates."""
        assert len(SOURCES) >= 100, f"Only {len(SOURCES)} sources"

    def test_every_source_has_required_fields(self):
        """No source may have empty required fields."""
        for s in SOURCES:
            assert s.source_id, f"empty source_id: {s}"
            assert s.name, f"empty name: {s}"
            assert s.url, f"empty url: {s}"
            assert s.evidence_type, f"empty evidence_type: {s}"
            assert s.access_method, f"empty access_method: {s}"
            assert s.license, f"empty license: {s}"
            assert s.evidence_tier in "ABCDEFGHI"
            assert s.universes, f"empty universes: {s}"

    def test_primary_sources_present(self):
        """Primary sources must be present (not all aggregators)."""
        primaries = get_primary_sources()
        assert len(primaries) >= 50, f"Only {len(primaries)} primary sources"

    def test_all_evidence_types_represented(self):
        """All 10 evidence types from Issue #5 must be represented."""
        types_present = {s.evidence_type for s in SOURCES}
        required = {"paper", "patent", "technical_report", "standard", "dataset",
                    "code", "experiment", "clinical_trial", "product", "failure_record"}
        missing = required - types_present
        assert not missing, f"Missing evidence types: {missing}"

    def test_no_silent_primary_to_secondary_substitution(self):
        """A source labeled 'primary' must not be a known aggregator. This is
        a structural check; semantic verification requires live validation."""
        for s in SOURCES:
            if s.primary_or_secondary == "primary":
                # primary sources should not have 'aggregator' or 'secondary' in name
                name_lower = s.name.lower()
                assert "aggregator" not in name_lower, \
                    f"{s.source_id} labeled primary but name suggests aggregator"

    def test_registry_manifest_hash_stable(self):
        """The registry content hash must be stable across calls."""
        m1 = registry_manifest()
        m2 = registry_manifest()
        assert m1["registry_content_hash"] == m2["registry_content_hash"]


# =====================================================================
# 2. DOMAIN MAP
# =====================================================================

class TestDomainMap:
    def test_30_or_more_domains(self):
        """CEO directive: 30+ domains."""
        assert len(DOMAINS) >= 30, f"Only {len(DOMAINS)} domains"

    def test_six_universes(self):
        """CEO directive: 6 technological universes."""
        assert len(UNIVERSES) == 6
        assert set(UNIVERSES) == {"matter", "energy", "life", "machine",
                                   "information", "planet"}

    def test_every_domain_in_valid_universe(self):
        for d in DOMAINS:
            assert d.universe in UNIVERSES, f"bad universe: {d.universe}"

    def test_domain_distance_zero_for_same(self):
        assert domain_distance("materials", "materials") == 0

    def test_domain_distance_one_for_same_universe(self):
        assert domain_distance("materials", "chemistry") == 1  # both matter

    def test_domain_distance_five_for_different_universe(self):
        assert domain_distance("materials", "robotics") == 5  # matter vs machine


# =====================================================================
# 3. CONNECTOR BASE
# =====================================================================

class TestConnectorBase:
    def test_harvest_error_raised_in_offline_mode(self):
        """In offline mode, every concrete connector must raise HarvestError."""
        src = SOURCES[0]
        conn = OpenAlexConnector(src)
        state = HarvestState(source_id=src.source_id)
        with pytest.raises(HarvestError, match="live harvest not enabled"):
            conn.harvest(state)

    def test_no_silent_substitution(self):
        """A connector must NEVER silently substitute a secondary source.
        This is enforced by raising HarvestError — never returning empty."""
        src = next(s for s in SOURCES if s.source_id == "src:openalex")
        conn = OpenAlexConnector(src)
        state = HarvestState(source_id=src.source_id)
        # The connector must raise, not return empty records
        with pytest.raises(HarvestError):
            conn.harvest(state)

    def test_epo_ops_requires_auth(self):
        """EPO OPS requires auth — must not proceed without credentials."""
        src = next(s for s in SOURCES if s.source_id == "src:epo_ops")
        conn = EpoOpsConnector(src)
        state = HarvestState(source_id=src.source_id)
        with pytest.raises(HarvestError, match="auth_required|credentials|live"):
            conn.harvest(state)

    def test_github_requires_token(self):
        src = next(s for s in SOURCES if s.source_id == "src:github")
        conn = GithubCodeConnector(src)
        state = HarvestState(source_id=src.source_id)
        with pytest.raises(HarvestError):
            conn.harvest(state)

    def test_hashed_record_content_addressable(self):
        """Same content -> same hash (content-addressed)."""
        r1 = HarvestedRecord(
            record_id="test:1", source_id="src:test", harvested_at="t",
            raw_payload_hash="abc", normalized={"k": "v"}, normalized_hash="def",
        )
        r2 = HarvestedRecord(
            record_id="test:1", source_id="src:test", harvested_at="t",
            raw_payload_hash="abc", normalized={"k": "v"}, normalized_hash="def",
        )
        assert r1.content_hash() == r2.content_hash()


# =====================================================================
# 4. PROVENANCE
# =====================================================================

class TestProvenance:
    def test_unknown_predicate_rejected(self):
        """A predicate outside the controlled vocabulary must be rejected."""
        with pytest.raises(ValueError, match="Unknown predicate"):
            ProvenanceEdge("a", "b", "RELATED_TO", "D", "src:test")  # generic forbidden

    def test_cites_requires_role(self):
        """A cites edge without a citation_role is invalid."""
        e = ProvenanceEdge("a", "b", "cites", "D", "src:test", citation_role=None)
        errors = validate_edge(e)
        assert any("citation_role" in err for err in errors)

    def test_bad_citation_role_rejected(self):
        with pytest.raises(ValueError, match="Bad citation_role"):
            ProvenanceEdge("a", "b", "cites", "D", "src:test", citation_role="Z")

    def test_bad_evidence_tier_rejected(self):
        with pytest.raises(ValueError, match="Bad evidence_tier"):
            ProvenanceEdge("a", "b", "validates", "X", "src:test")

    def test_no_generic_related_to(self):
        """The vocabulary must NOT contain 'RELATED_TO' — that's the antidote
        to 'everything is connected to everything'."""
        assert "RELATED_TO" not in PREDICATES
        assert "related_to" not in PREDICATES

    def test_cross_corpus_predicates_nonempty(self):
        assert len(CROSS_CORPUS_PREDICATES) >= 10

    def test_empirical_predicates_present(self):
        """Empirical predicates (validates, refutes, reproduced_from,
        failed_to_reproduce) must be in the vocabulary."""
        for p in ["validates", "refutes", "reproduced_from", "failed_to_reproduce"]:
            assert p in EMPIRICAL_PREDICATES

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="Bad confidence"):
            ProvenanceEdge("a", "b", "validates", "A", "src:test", confidence=1.5)


# =====================================================================
# 5. MULTILINGUAL
# =====================================================================

class TestMultilingual:
    def test_original_marked_correctly(self):
        """An original text must have original_record_id=None."""
        t = MultilingualText(text="hello", language="en")
        assert t.is_original() is True

    def test_translation_marked_correctly(self):
        t = MultilingualText(text="hola", language="es", original_record_id="rec:1",
                             translation_engine="deepl")
        assert t.is_original() is False

    def test_same_language_pair_rejected(self):
        """Original and translation must be in different languages."""
        orig = MultilingualText(text="hello", language="en")
        trans = MultilingualText(text="hi", language="en",
                                  original_record_id="rec:1",
                                  translation_engine="test")
        errors = validate_multilingual_pair(orig, trans)
        assert any("same language" in e for e in errors)

    def test_translation_without_engine_rejected(self):
        orig = MultilingualText(text="hello", language="en")
        trans = MultilingualText(text="hola", language="es",
                                  original_record_id="rec:1",
                                  translation_engine=None)
        errors = validate_multilingual_pair(orig, trans)
        assert any("translation_engine" in e for e in errors)

    def test_translation_confidence_out_of_range_rejected(self):
        orig = MultilingualText(text="hello", language="en")
        trans = MultilingualText(text="hola", language="es",
                                  original_record_id="rec:1",
                                  translation_engine="test",
                                  translation_confidence=1.5)
        errors = validate_multilingual_pair(orig, trans)
        assert any("out of range" in e for e in errors)

    def test_supported_languages_check(self):
        assert is_supported_language("en") is True
        assert is_supported_language("xx") is False


# =====================================================================
# 6. FAILURE RECORDER
# =====================================================================

class TestFailureRecorder:
    def test_append_only(self):
        """The failure log is append-only — existing entries are never modified."""
        with tempfile.TemporaryDirectory() as td:
            log = FailureLog(Path(td) / "fail.jsonl")
            log.record("src:test", "API_BLOCKED", "first failure")
            entries1 = log.read_all()
            assert len(entries1) == 1
            log.record("src:test", "RATE_LIMITED", "second failure")
            entries2 = log.read_all()
            assert len(entries2) == 2
            # first entry unchanged
            assert entries1[0] == entries2[0]

    def test_bad_failure_type_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            log = FailureLog(Path(td) / "fail.jsonl")
            with pytest.raises(ValueError, match="Unknown failure_type"):
                log.record("src:test", "NOT_A_REAL_TYPE", "x")

    def test_failures_filterable_by_source(self):
        with tempfile.TemporaryDirectory() as td:
            log = FailureLog(Path(td) / "fail.jsonl")
            log.record("src:a", "API_BLOCKED", "x")
            log.record("src:b", "RATE_LIMITED", "y")
            log.record("src:a", "SCHEMA_CHANGED", "z")
            a_fails = log.failures_for_source("src:a")
            assert len(a_fails) == 2
            b_fails = log.failures_for_source("src:b")
            assert len(b_fails) == 1


# =====================================================================
# 7. SNAPSHOT MANAGER
# =====================================================================

class TestSnapshotManager:
    def test_snapshot_is_frozen(self):
        """A snapshot must always have is_frozen=True."""
        with tempfile.TemporaryDirectory() as td:
            result = create_snapshot([], "2024-01-01", Path(td) / "snap")
            assert result["manifest"]["is_frozen"] is True
            assert is_frozen(Path(td) / "snap") is True

    def test_snapshot_tamper_detected(self):
        """Mutating snapshot.json after creation invalidates its hash."""
        with tempfile.TemporaryDirectory() as td:
            create_snapshot([], "2024-01-01", Path(td) / "snap")
            sp = Path(td) / "snap" / "snapshot.json"
            sp.write_text(sp.read_text() + " TAMPERED")
            result = verify_snapshot(Path(td) / "snap")
            assert result["valid"] is False
            checks = {c["check"]: c["passed"] for c in result["checks"]}
            assert checks["HASH_MATCHES"] is False

    def test_snapshot_with_records_verifies_each_record(self):
        """Every record file must exist and its hash must match its filename."""
        with tempfile.TemporaryDirectory() as td:
            recs = [
                HarvestedRecord(
                    record_id="r:1", source_id="src:test", harvested_at="t",
                    raw_payload_hash="rh1",
                    normalized={"id": "r:1"}, normalized_hash="nh1",
                ),
                HarvestedRecord(
                    record_id="r:2", source_id="src:test", harvested_at="t",
                    raw_payload_hash="rh2",
                    normalized={"id": "r:2"}, normalized_hash="nh2",
                ),
            ]
            # fix the hashes to match
            import hashlib
            for r in recs:
                r.normalized_hash = hashlib.sha256(
                    json.dumps(r.normalized, sort_keys=True).encode()
                ).hexdigest()
            create_snapshot(recs, "2024-01-01", Path(td) / "snap")
            result = verify_snapshot(Path(td) / "snap")
            assert result["valid"] is True

    def test_snapshot_root_hash_recomputed(self):
        """verify_snapshot recomputes the root hash from record_hashes — does
        not trust the manifest's claimed root_hash."""
        with tempfile.TemporaryDirectory() as td:
            create_snapshot([], "2024-01-01", Path(td) / "snap")
            sp = Path(td) / "snap" / "snapshot.json"
            manifest = json.loads(sp.read_text())
            # tamper: claim a different root_hash
            manifest["root_hash"] = "0" * 64
            sp.write_text(json.dumps(manifest, sort_keys=True))
            # fix the sha256 sidecar to match the tampered content
            import hashlib
            (Path(td) / "snap" / "snapshot.json.sha256").write_text(
                hashlib.sha256(sp.read_text().encode()).hexdigest()
            )
            result = verify_snapshot(Path(td) / "snap")
            assert result["valid"] is False
            checks = {c["check"]: c["passed"] for c in result["checks"]}
            assert checks["ROOT_HASH_VALID"] is False


# =====================================================================
# 8. SOURCE VALIDATOR
# =====================================================================

class TestSourceValidator:
    def test_all_sources_structurally_valid(self):
        """Every source in the registry must pass structural validation."""
        for s in SOURCES:
            result = validate_source_structural(s)
            assert result.structural_ok, \
                f"{s.source_id} failed: {result.errors}"

    def test_bad_evidence_type_detected(self):
        """A source with a bad evidence_type must fail validation."""
        bad = Source(
            source_id="src:bad", name="Bad", url="https://example.com",
            evidence_type="not_a_real_type", access_method="rest_api",
            license="CC0", evidence_tier="D", universes=("matter",),
        )
        result = validate_source_structural(bad)
        assert result.structural_ok is False
        assert any("evidence_type" in e for e in result.errors)

    def test_bad_url_detected(self):
        bad = Source(
            source_id="src:bad", name="Bad", url="not-a-url",
            evidence_type="paper", access_method="rest_api",
            license="CC0", evidence_tier="D", universes=("matter",),
        )
        result = validate_source_structural(bad)
        assert result.structural_ok is False

    def test_proprietary_license_warns(self):
        """A proprietary license is valid but should warn."""
        s = next(s for s in SOURCES if "proprietary" in s.license.lower())
        result = validate_source_structural(s)
        assert result.structural_ok is True
        assert any("proprietary" in w for w in result.warnings)


# =====================================================================
# 9. KNOWLEDGE DISTANCE
# =====================================================================

class TestKnowledgeDistance:
    def test_distance_zero_for_identical(self):
        """Distance between identical anchor sets is 0."""
        d = compute_distance(
            domains_a=["materials"], domains_b=["materials"],
            mechanisms_a=["intercalation"], mechanisms_b=["intercalation"],
            date_a="2020-01-01", date_b="2020-01-01",
            evidence_types_a=["paper"], evidence_types_b=["paper"],
            implementations_a=["x"], implementations_b=["x"],
            constraints_a=["c1"], constraints_b=["c1"],
        )
        assert d.aggregate == 0.0

    def test_distance_max_for_completely_different(self):
        """Distance between orthogonal anchor sets approaches 1.0."""
        d = compute_distance(
            domains_a=["materials"], domains_b=["robotics"],
            mechanisms_a=["intercalation"], mechanisms_b=["spike_timing"],
            date_a="2010-01-01", date_b="2024-01-01",
            evidence_types_a=["paper"], evidence_types_b=["patent"],
            implementations_a=["x"], implementations_b=["y"],
            constraints_a=["c1"], constraints_b=["c2"],
        )
        assert d.aggregate > 0.8

    def test_weights_sum_to_one(self):
        """The aggregate-distance weights must sum to 1.0."""
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_distance_is_not_evidence(self):
        """Knowledge distance is a search-prioritization variable, NOT evidence
        of truth. The function returns a number — it does NOT return a
        'discovery' verdict."""
        d = compute_distance(
            domains_a=["a"], domains_b=["b"],
            mechanisms_a=["x"], mechanisms_b=["y"],
            date_a="2020-01-01", date_b="2024-01-01",
            evidence_types_a=["paper"], evidence_types_b=["patent"],
        )
        # The return is a KnowledgeDistance object with numeric fields.
        # It contains NO boolean 'is_discovery' field.
        assert not hasattr(d, "is_discovery")
        assert not hasattr(d, "is_valid")
        assert not hasattr(d, "is_true")


# =====================================================================
# 10. CROSS-EVIDENCE MOTIFS
# =====================================================================

class TestCrossEvidenceMotifs:
    def test_all_10_motifs_present(self):
        assert len(ALL_CROSS_EVIDENCE_MOTIFS) == 10

    def test_motif_uses_typed_provenance(self):
        """Every motif must use typed ProvenanceEdges, not generic RELATED_TO."""
        d = {"domain_distance": 5, "mechanism_distance": 0.5,
             "temporal_distance_years": 3.0, "evidence_distance": 1.0,
             "implementation_distance": 1.0, "constraint_distance": 1.0,
             "aggregate": 0.7}
        c = motif_c01_paper_patent_standard(
            "paper:1", "patent:1", "standard:1",
            paper_date="2020-01-01", patent_date="2021-01-01",
            standard_date="2019-01-01", domain="materials", distance=d,
        )
        for edge in c.edges:
            assert edge.predicate in PREDICATES
            assert edge.predicate != "RELATED_TO"

    def test_motif_carries_knowledge_distance(self):
        """Every motif candidate must carry a knowledge_distance dict."""
        d = {"domain_distance": 5, "mechanism_distance": 0.5,
             "temporal_distance_years": 3.0, "evidence_distance": 1.0,
             "implementation_distance": 1.0, "constraint_distance": 1.0,
             "aggregate": 0.7}
        c = motif_c02_paper_patent_dataset(
            "paper:1", "patent:1", "dataset:1",
            paper_date="2020-01-01", patent_date="2021-01-01",
            domain="materials", distance=d,
        )
        assert "aggregate" in c.knowledge_distance
        assert "domain_distance" in c.knowledge_distance

    def test_motif_has_falsifiable_prediction(self):
        """Every motif must produce a falsifiable, machine-checkable prediction."""
        d = {"aggregate": 0.5}
        c = motif_c05_paper_patent_failure(
            "paper:1", "patent:1", "failure:1",
            paper_date="2020-01-01", patent_date="2021-01-01",
            failure_date="2022-01-01", domain="life", distance=d,
        )
        assert c.predicted_outcome  # non-empty
        assert c.prediction_window_days > 0


# =====================================================================
# 11. END-TO-END FABRIC RUN
# =====================================================================

class TestEndToEnd:
    def test_fabric_runs_and_passes_audit(self):
        """End-to-end: fabric runs, forensic audit passes."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            audit = forensic_audit(Path(result["report_path"]))
            assert audit["passed"] is True, \
                f"Forensic audit failed: {[c for c in audit['checks'] if not c['passed']]}"

    def test_fabric_never_claims_scientific_result(self):
        """The fabric must never claim is_scientific_result=True."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            assert result["state"]["is_scientific_result"] is False

    def test_fabric_never_claims_real_data_seal(self):
        """The fabric must never claim real_data_seal=True in offline mode."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            assert result["state"]["real_data_seal"] is False

    def test_fabric_offline_mode_no_live_check(self):
        """In offline mode, live_check_performed must be False."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            assert result["state"]["live_check_performed"] is False

    def test_fabric_produces_snapshot(self):
        """The fabric must produce a verifiable snapshot."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            assert result["state"]["snapshot_created"] is True
            assert result["state"]["snapshot_verified"] is True

    def test_audit_detects_tampered_report(self):
        """Tampering with the fabric_state.json must fail forensic audit."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            rp = Path(result["report_path"])
            rp.write_text(rp.read_text() + " TAMPERED")
            audit = forensic_audit(rp)
            assert audit["passed"] is False

    def test_audit_detects_false_scientific_claim(self):
        """A fabric state claiming is_scientific_result=True must fail audit."""
        with tempfile.TemporaryDirectory() as td:
            result = run_fabric(Path(td))
            rp = Path(result["report_path"])
            content = json.loads(rp.read_text())
            content["is_scientific_result"] = True
            import hashlib
            new_content = json.dumps(content, sort_keys=True, default=str)
            rp.write_text(new_content)
            rp.with_suffix(rp.suffix + ".sha256").write_text(
                hashlib.sha256(new_content.encode()).hexdigest()
            )
            audit = forensic_audit(rp)
            assert audit["passed"] is False
            checks = {c["check"]: c["passed"] for c in audit["checks"]}
            assert checks["NOT_CLAIMED_AS_SCIENTIFIC"] is False
