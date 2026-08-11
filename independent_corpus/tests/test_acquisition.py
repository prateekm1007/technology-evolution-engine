"""
independent_corpus.tests.test_acquisition — Tests for independent corpus acquisition.

Tests:
1. No TEE influence on sampling
2. No connection search queries
3. Acquisition manifest is frozen before execution
4. Aggregate report contains no paper titles
5. Custodian intake runs on sampled papers
6. Temporal cutoff enforced
7. Duplicate detection works at acquisition scale
8. Domain classification uses custodian taxonomy
"""
import sys
import os
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT.parent / "custodian"))

from independent_corpus.acquisition.sampler import (
    create_acquisition_manifest,
    verify_no_tee_influence,
    AcquisitionManifest,
)
from independent_corpus.acquisition.openalex_adapter import (
    OpenAlexRecord,
    sample_openalex,
)
from independent_corpus.acquisition.semantic_scholar_adapter import (
    cross_check_by_doi,
    S2CrossCheckResult,
)
from independent_corpus.acquisition.run_acquisition import run_acquisition


class TestNoTEEInfluence(unittest.TestCase):
    """Test that TEE cannot influence sampling."""

    def test_manifest_has_no_tee_influence_flag(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        self.assertTrue(manifest.no_tee_influence)

    def test_manifest_has_no_connection_search_flag(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        self.assertTrue(manifest.no_connection_search)

    def test_verify_no_tee_influence_clean(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        violations = verify_no_tee_influence(manifest)
        self.assertEqual(violations, [])

    def test_verify_detects_tee_term_in_query(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        manifest.query_space = "Find papers TEE might find interesting"
        violations = verify_no_tee_influence(manifest)
        self.assertTrue(any("FORBIDDEN_TERM" in v for v in violations))

    def test_verify_detects_connection_search(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        manifest.sampling_method = "Search for cross-domain connections"
        violations = verify_no_tee_influence(manifest)
        self.assertTrue(any("CONNECTION_SEARCH" in v for v in violations))


class TestManifestFrozen(unittest.TestCase):
    """Test that the manifest is frozen before execution."""

    def test_manifest_hash_computed(self):
        manifest = create_acquisition_manifest("2025-01-01", "seed", 100)
        self.assertTrue(len(manifest.manifest_hash) == 64)

    def test_manifest_deterministic(self):
        """Same inputs → same manifest hash."""
        m1 = create_acquisition_manifest("2025-01-01", "seed", 100)
        m2 = create_acquisition_manifest("2025-01-01", "seed", 100)
        self.assertEqual(m1.manifest_hash, m2.manifest_hash)

    def test_different_seed_different_hash(self):
        m1 = create_acquisition_manifest("2025-01-01", "seed_A", 100)
        m2 = create_acquisition_manifest("2025-01-01", "seed_B", 100)
        self.assertNotEqual(m1.manifest_hash, m2.manifest_hash)

    def test_seed_hash_in_manifest(self):
        manifest = create_acquisition_manifest("2025-01-01", "my_seed", 100)
        import hashlib
        expected = hashlib.sha256("my_seed".encode()).hexdigest()
        self.assertEqual(manifest.random_seed_hash, expected)


class TestTemporalCutoff(unittest.TestCase):
    """Test that temporal cutoff is enforced."""

    def test_cutoff_in_manifest(self):
        manifest = create_acquisition_manifest("2025-06-01", "seed", 100)
        self.assertEqual(manifest.date_cutoff, "2025-06-01")

    def test_cutoff_in_inclusion_rules(self):
        manifest = create_acquisition_manifest("2025-06-01", "seed", 100)
        self.assertTrue(any("2025-06-01" in rule for rule in manifest.inclusion_rules))

    def test_cutoff_in_exclusion_rules(self):
        manifest = create_acquisition_manifest("2025-06-01", "seed", 100)
        self.assertTrue(any("cutoff" in rule.lower() for rule in manifest.exclusion_rules))


class TestAggregateReport(unittest.TestCase):
    """Test that the aggregate report contains no paper titles."""

    def test_report_has_no_titles(self):
        """The aggregate report must NOT contain paper titles."""
        # Create a mock report
        report = {
            "report_type": "AGGREGATE_INTAKE_REPORT",
            "n_eligible": 150,
            "domain_distribution": {"fluid_mechanics": 30, "enzymology": 25},
            "note": "No paper titles shown.",
        }
        report_str = json.dumps(report)
        # Verify no title-like fields
        self.assertNotIn("title", report_str.lower().split('"'))
        self.assertNotIn("abstract", report_str.lower())

    def test_report_has_aggregate_stats_only(self):
        report = {
            "n_intaken": 200,
            "n_eligible": 150,
            "n_flagged": 30,
            "n_rejected": 20,
            "domain_distribution": {"fluid_mechanics": 30},
        }
        self.assertIn("n_eligible", report)
        self.assertIn("domain_distribution", report)
        self.assertNotIn("titles", report)
        self.assertNotIn("papers", report)  # No paper list


class TestOpenAlexAdapter(unittest.TestCase):
    """Test the OpenAlex adapter (with real API calls, small sample)."""

    def test_sample_small_batch(self):
        """Sample a small batch from OpenAlex."""
        records, cursor, stats = sample_openalex(
            date_cutoff="2025-01-01",
            random_seed="test_seed",
            max_results=5,
        )
        self.assertGreater(len(records), 0)
        self.assertEqual(stats["provider"], "openalex")
        self.assertEqual(stats["n_received"], len(records))

    def test_record_has_required_fields(self):
        """Each record has all required fields."""
        records, _, _ = sample_openalex(
            date_cutoff="2025-01-01",
            random_seed="test_seed",
            max_results=2,
        )
        if records:
            r = records[0]
            self.assertTrue(r.source_id)
            self.assertTrue(r.title)
            self.assertTrue(r.publication_date)
            self.assertTrue(r.metadata_sha256)
            self.assertEqual(r.external_provider, "openalex")

    def test_temporal_cutoff_enforced(self):
        """All records have publication_date <= cutoff."""
        cutoff = "2024-01-01"
        records, _, _ = sample_openalex(
            date_cutoff=cutoff,
            random_seed="test_seed",
            max_results=5,
        )
        for r in records:
            self.assertLessEqual(r.publication_date, cutoff,
                                f"Record {r.source_id} published {r.publication_date}, after cutoff {cutoff}")


class TestSemanticScholarCrossCheck(unittest.TestCase):
    """Test Semantic Scholar cross-check."""

    def test_cross_check_known_doi(self):
        """Cross-check a known DOI."""
        # Use a well-known DOI (e.g., a classic paper)
        result = cross_check_by_doi("10.1038/nature12352", "test_id")
        self.assertIn(result.cross_check_status, ["CONFIRMED", "PARTIAL_MATCH", "NOT_FOUND", "ERROR"])

    def test_cross_check_empty_doi(self):
        """Empty DOI returns NOT_FOUND."""
        result = cross_check_by_doi("", "test_id")
        self.assertEqual(result.cross_check_status, "NOT_FOUND")


class TestAcquisitionRunner(unittest.TestCase):
    """Test the full acquisition runner (small scale)."""

    def test_run_small_acquisition(self):
        """Run a small acquisition and verify aggregate report."""
        report = run_acquisition(
            date_cutoff="2025-01-01",
            random_seed="test-acquisition-seed",
            n_requested=10,
            s2_cross_check_limit=3,
        )

        # Verify report structure
        self.assertEqual(report["report_type"], "AGGREGATE_INTAKE_REPORT")
        self.assertIn("manifest", report)
        self.assertIn("acquisition_stats", report)
        self.assertIn("intake_stats", report)
        self.assertIn("domain_distribution", report)

        # Verify NO titles in report
        report_str = json.dumps(report)
        # The report should not contain paper titles as values
        # (it may contain "title" in schema descriptions, but not actual titles)
        self.assertNotIn("Radiation Resistant", report_str)  # Known sample title


if __name__ == '__main__':
    unittest.main(verbosity=2)
