"""
custodian.intake.tests.test_intake — Tests for the corpus intake pipeline.

Covers all 15 items from the CTO directive, plus:
- TEE cannot mutate or consume intake state
- Exposure detection (UNSEEN/POSSIBLY_SEEN/KNOWN_SEEN/UNDETERMINABLE)
- Contamination detection (CLEAN/FLAGGED/CONTAMINATED)
- ELIGIBLE/FLAGGED/REJECTED/UNDETERMINABLE states
"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

CUSTODIAN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CUSTODIAN_ROOT))

from src.hasher import sha256_string
from intake.src.intake_gateway import (
    CorpusIntakeGateway,
    IntakeRecord,
    IntakeStatus,
)
from intake.src.exposure_detector import ExposureStatus, check_tee_exposure
from intake.src.contamination_detector import ContaminationLevel, check_contamination
from intake.fixtures.synthetic.synthetic_corpus import (
    SYNTHETIC_SOURCES,
    CONTAMINATED_SOURCE,
    KNOWN_SEEN_SOURCE,
    KNOWN_SEEN_CONTENT,
    KNOWN_SEEN_HASH,
)


class TestIntakeBasics(unittest.TestCase):
    """Test basic intake pipeline functionality."""

    def test_intake_clean_source(self):
        """A clean, unseen source is ELIGIBLE."""
        gw = CorpusIntakeGateway()
        src = SYNTHETIC_SOURCES[0]
        record = gw.intake_source(**src)
        self.assertEqual(record.intake_status, IntakeStatus.ELIGIBLE)
        self.assertEqual(record.exposure_result.status, ExposureStatus.UNSEEN)
        self.assertEqual(record.contamination_result.level, ContaminationLevel.CLEAN)

    def test_intake_multiple_sources(self):
        """Multiple clean sources can be intaken."""
        gw = CorpusIntakeGateway()
        for src in SYNTHETIC_SOURCES:
            record = gw.intake_source(**src)
            self.assertEqual(record.intake_status, IntakeStatus.ELIGIBLE)
        self.assertEqual(len(gw.list_records()), 4)

    def test_duplicate_source_id_rejected(self):
        """Duplicate source_id is rejected."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        with self.assertRaises(ValueError) as ctx:
            gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertIn("DUPLICATE_INTAKE", str(ctx.exception))

    def test_duplicate_content_rejected(self):
        """Different source_id but same content is rejected."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        dup = {**SYNTHETIC_SOURCES[0], "source_id": "DIFFERENT-ID"}
        with self.assertRaises(ValueError) as ctx:
            gw.intake_source(**dup)
        self.assertIn("DUPLICATE_CONTENT", str(ctx.exception))


class TestExposureDetection(unittest.TestCase):
    """Test TEE prior-exposure detection."""

    def test_unseen_source(self):
        """Source not in TEE artifacts → UNSEEN."""
        gw = CorpusIntakeGateway(
            tee_corpus_hashes=set(),
            tee_artifact_paths=[],
        )
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertEqual(record.exposure_result.status, ExposureStatus.UNSEEN)

    def test_known_seen_source(self):
        """Source with hash in TEE corpus → KNOWN_SEEN → REJECTED."""
        gw = CorpusIntakeGateway(
            tee_corpus_hashes={KNOWN_SEEN_HASH},
        )
        record = gw.intake_source(**KNOWN_SEEN_SOURCE)
        self.assertEqual(record.exposure_result.status, ExposureStatus.KNOWN_SEEN)
        self.assertEqual(record.intake_status, IntakeStatus.REJECTED)

    def test_possibly_seen_source(self):
        """Source with known TEE phrase → POSSIBLY_SEEN → FLAGGED."""
        gw = CorpusIntakeGateway(
            tee_known_phrases=["remarkable specificity through geometric complementarity"],
        )
        record = gw.intake_source(**SYNTHETIC_SOURCES[1])
        self.assertEqual(record.exposure_result.status, ExposureStatus.POSSIBLY_SEEN)
        self.assertEqual(record.intake_status, IntakeStatus.FLAGGED)

    def test_hash_in_tee_artifact_file(self):
        """Source hash found in a TEE artifact file → KNOWN_SEEN."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(f"Processed hash: {sha256_string(SYNTHETIC_SOURCES[0]['content'])}\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            gw = CorpusIntakeGateway(tee_artifact_paths=[temp_path])
            record = gw.intake_source(**SYNTHETIC_SOURCES[0])
            self.assertEqual(record.exposure_result.status, ExposureStatus.KNOWN_SEEN)
            self.assertEqual(record.intake_status, IntakeStatus.REJECTED)
        finally:
            os.unlink(temp_path)


class TestContaminationDetection(unittest.TestCase):
    """Test benchmark/answer-key contamination detection."""

    def test_clean_source(self):
        """Clean source → CLEAN."""
        result = check_contamination("S1", "Normal scientific text about photosynthesis.")
        self.assertEqual(result.level, ContaminationLevel.CLEAN)

    def test_answer_key_contamination(self):
        """Source with ground_truth → CONTAMINATED."""
        result = check_contamination("S1", "The ground_truth: expected_mechanism is riblet lifting.")
        self.assertEqual(result.level, ContaminationLevel.CONTAMINATED)
        self.assertTrue(any("ANSWER_KEY_PATTERN" in f for f in result.flags))

    def test_benchmark_identifier_contamination(self):
        """Source with DXP- identifier → CONTAMINATED."""
        result = check_contamination("S1", "This relates to DXP-004 test case.")
        self.assertEqual(result.level, ContaminationLevel.CONTAMINATED)

    def test_hypothesis_language_flagged(self):
        """Source with hypothesis language → FLAGGED."""
        result = check_contamination("S1", "The correct hypothesis is that riblets lift vortices.")
        self.assertEqual(result.level, ContaminationLevel.FLAGGED)

    def test_bridge_discussion_flagged(self):
        """Source discussing the bridge → FLAGGED."""
        result = check_contamination("S1", "We apply this mechanism from biology to engineering.")
        self.assertEqual(result.level, ContaminationLevel.FLAGGED)

    def test_contaminated_source_rejected(self):
        """Contaminated source → REJECTED."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**CONTAMINATED_SOURCE)
        self.assertEqual(record.intake_status, IntakeStatus.REJECTED)
        self.assertEqual(record.contamination_result.level, ContaminationLevel.CONTAMINATED)


class TestDomainClassification(unittest.TestCase):
    """Test domain classification using safe taxonomy."""

    def test_canonical_domain_assigned(self):
        """Intake record has canonical_domain."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertEqual(record.canonical_domain, "fluid_mechanics")

    def test_unknown_domain_flagged(self):
        """Unknown domain → FLAGGED."""
        gw = CorpusIntakeGateway()
        src = {**SYNTHETIC_SOURCES[0], "domain": "nonexistent_domain_xyz"}
        record = gw.intake_source(**src)
        self.assertEqual(record.intake_status, IntakeStatus.FLAGGED)
        self.assertTrue(any("not in frozen taxonomy" in f for f in record.flags))

    def test_domain_distribution(self):
        """Domain distribution uses canonical domains."""
        gw = CorpusIntakeGateway()
        for src in SYNTHETIC_SOURCES:
            gw.intake_source(**src)
        dist = gw.get_domain_distribution()
        self.assertEqual(dist["fluid_mechanics"], 1)
        self.assertEqual(dist["enzymology"], 1)
        self.assertEqual(dist["optics"], 1)
        self.assertEqual(dist["materials_science"], 1)


class TestNearDuplicateDetection(unittest.TestCase):
    """Test near-duplicate detection at intake layer."""

    def test_near_duplicate_titles_flagged(self):
        """Sources with very similar titles are flagged."""
        gw = CorpusIntakeGateway()
        gw.intake_source(
            source_id="S1", domain="fluid_mechanics", title="Microscopic surface textures in organisms",
            origin="test", source_uri="test://1", content="content A", version="v1",
        )
        gw.intake_source(
            source_id="S2", domain="enzymology", title="Microscopic surface textures in organisms",  # Same title
            origin="test", source_uri="test://2", content="content B", version="v1",
        )
        flags = gw.check_near_duplicates()
        self.assertTrue(len(flags) > 0, "Near-duplicate titles not detected")

    def test_different_titles_not_flagged(self):
        """Sources with different titles are not flagged."""
        gw = CorpusIntakeGateway()
        gw.intake_source(
            source_id="S1", domain="fluid_mechanics", title="Drag reduction in pipelines",
            origin="test", source_uri="test://1", content="content A", version="v1",
        )
        gw.intake_source(
            source_id="S2", domain="enzymology", title="Enzyme catalytic mechanisms",
            origin="test", source_uri="test://2", content="content B", version="v1",
        )
        flags = gw.check_near_duplicates()
        self.assertEqual(len(flags), 0, "Different titles incorrectly flagged")


class TestIntakeStatus(unittest.TestCase):
    """Test ELIGIBLE/FLAGGED/REJECTED/UNDETERMINABLE states."""

    def test_eligible_source(self):
        """Clean, unseen source → ELIGIBLE."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertEqual(record.intake_status, IntakeStatus.ELIGIBLE)

    def test_flagged_source(self):
        """Source with possible exposure → FLAGGED."""
        gw = CorpusIntakeGateway(
            tee_known_phrases=["microscopic surface textures"],
        )
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertEqual(record.intake_status, IntakeStatus.FLAGGED)

    def test_rejected_source_contamination(self):
        """Contaminated source → REJECTED."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**CONTAMINATED_SOURCE)
        self.assertEqual(record.intake_status, IntakeStatus.REJECTED)

    def test_rejected_source_known_seen(self):
        """Known-seen source → REJECTED."""
        gw = CorpusIntakeGateway(
            tee_corpus_hashes={KNOWN_SEEN_HASH},
        )
        record = gw.intake_source(**KNOWN_SEEN_SOURCE)
        self.assertEqual(record.intake_status, IntakeStatus.REJECTED)

    def test_list_by_status(self):
        """Can list records by status."""
        gw = CorpusIntakeGateway(
            tee_corpus_hashes={KNOWN_SEEN_HASH},
        )
        gw.intake_source(**SYNTHETIC_SOURCES[0])  # ELIGIBLE
        gw.intake_source(**KNOWN_SEEN_SOURCE)  # REJECTED
        gw.intake_source(**CONTAMINATED_SOURCE)  # REJECTED

        eligible = gw.list_by_status(IntakeStatus.ELIGIBLE)
        rejected = gw.list_by_status(IntakeStatus.REJECTED)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(len(rejected), 2)


class TestManifests(unittest.TestCase):
    """Test machine-readable manifest and human-readable audit."""

    def test_intake_manifest(self):
        """Machine-readable manifest is generated."""
        gw = CorpusIntakeGateway()
        for src in SYNTHETIC_SOURCES:
            gw.intake_source(**src)
        manifest = gw.get_intake_manifest()
        self.assertEqual(manifest["source_count"], 4)
        self.assertIn("domain_distribution", manifest)
        self.assertIn("status_distribution", manifest)
        self.assertIn("records", manifest)

    def test_intake_audit_report(self):
        """Human-readable audit report is generated."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        report = gw.get_intake_audit_report()
        self.assertIn("CORPUS INTAKE AUDIT REPORT", report)
        self.assertIn("Status Distribution", report)
        self.assertIn("Domain Distribution", report)
        self.assertIn("Per-Source Details", report)

    def test_audit_trail_recorded(self):
        """Intake events are recorded in audit trail."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        trail = gw.get_audit_trail()
        events = trail.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "SOURCE_INTAKEN")


class TestProvenanceAndHashing(unittest.TestCase):
    """Test provenance chain and SHA-256 identity."""

    def test_content_hash_computed(self):
        """Content hash is SHA-256 of content."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        expected = sha256_string(SYNTHETIC_SOURCES[0]["content"])
        self.assertEqual(record.content_hash, expected)

    def test_provenance_chain(self):
        """Provenance records origin, timestamp, method, version."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(**SYNTHETIC_SOURCES[0])
        self.assertEqual(record.provenance["constructor"], SYNTHETIC_SOURCES[0]["origin"])
        self.assertIn("construction_timestamp", record.provenance)
        self.assertEqual(record.provenance["construction_method"], "external_custodian_intake")
        self.assertEqual(record.provenance["source_version"], SYNTHETIC_SOURCES[0]["version"])

    def test_source_registry_updated(self):
        """Source registry contains the intaken source."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        reg = gw.get_source_registry()
        entry = reg.get(SYNTHETIC_SOURCES[0]["source_id"])
        self.assertEqual(entry.domain, "fluid_mechanics")
        self.assertEqual(entry.content_hash, sha256_string(SYNTHETIC_SOURCES[0]["content"]))

    def test_acquisition_timestamp(self):
        """Acquisition timestamp is recorded."""
        gw = CorpusIntakeGateway()
        record = gw.intake_source(
            **SYNTHETIC_SOURCES[0],
            acquisition_timestamp="2026-01-15T10:00:00Z",
        )
        self.assertEqual(record.acquisition_timestamp, "2026-01-15T10:00:00Z")


class TestTEESeparation(unittest.TestCase):
    """Test that TEE cannot mutate or consume intake state."""

    def test_tee_safe_summary_no_content(self):
        """TEE-safe summary contains no source content."""
        gw = CorpusIntakeGateway()
        for src in SYNTHETIC_SOURCES:
            gw.intake_source(**src)
        summary = gw.export_tee_safe_summary()
        # Verify no source content in summary
        summary_str = json.dumps(summary)
        for src in SYNTHETIC_SOURCES:
            self.assertNotIn(src["content"], summary_str)

    def test_tee_safe_summary_no_answer_keys(self):
        """TEE-safe summary contains no answer-key fields."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        summary = gw.export_tee_safe_summary()
        summary_str = json.dumps(summary).lower()
        forbidden = ["ground_truth", "answer_key", "expected_mechanism", "falsifier"]
        for f in forbidden:
            self.assertNotIn(f, summary_str)

    def test_tee_safe_summary_has_only_aggregates(self):
        """TEE-safe summary has only aggregate statistics."""
        gw = CorpusIntakeGateway()
        for src in SYNTHETIC_SOURCES:
            gw.intake_source(**src)
        summary = gw.export_tee_safe_summary()
        self.assertIn("source_count", summary)
        self.assertIn("eligible_count", summary)
        self.assertIn("domain_count", summary)
        self.assertNotIn("records", summary)  # No individual records

    def test_intake_state_not_accessible_to_tee(self):
        """The intake gateway has no TEE-facing API that exposes records."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        # The only TEE-safe method is export_tee_safe_summary
        # All other methods (get_record, list_records, etc.) are custodian-only
        summary = gw.export_tee_safe_summary()
        self.assertNotIn("records", summary)
        self.assertNotIn("content", summary)
        self.assertNotIn("source_id", summary)


class TestImmutableRegistration(unittest.TestCase):
    """Test that source registration is immutable."""

    def test_cannot_re_register_source(self):
        """A source cannot be registered twice."""
        gw = CorpusIntakeGateway()
        gw.intake_source(**SYNTHETIC_SOURCES[0])
        with self.assertRaises(ValueError):
            gw.intake_source(**SYNTHETIC_SOURCES[0])

    def test_registry_entry_immutable_after_intake(self):
        """Registry entry hash doesn't change if content is the same.
        Note: retrieval_timestamp varies, so we compare content_hash instead."""
        gw1 = CorpusIntakeGateway()
        gw2 = CorpusIntakeGateway()
        gw1.intake_source(**SYNTHETIC_SOURCES[0])
        gw2.intake_source(**SYNTHETIC_SOURCES[0])
        r1 = gw1.get_record(SYNTHETIC_SOURCES[0]["source_id"])
        r2 = gw2.get_record(SYNTHETIC_SOURCES[0]["source_id"])
        self.assertEqual(r1.content_hash, r2.content_hash,
                         "Same content should produce same content hash")


if __name__ == '__main__':
    unittest.main(verbosity=2)
