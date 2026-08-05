#!/usr/bin/env python3
"""
test_extractor_benchmarks.py — DR-46 tests.

Per DR-46 test requirements:
  - stable inputs
  - stable scoring
  - no silent changes to metric definitions
  - no mixture of discovery success and extractor quality
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.extractor_benchmarks import ExtractorBenchmarks, BenchmarkResult


class TestDocumentParsingBenchmark:
    """Test document parsing benchmark."""

    def test_returns_dict(self):
        """Returns a dict with expected keys."""
        bm = ExtractorBenchmarks()
        class FakeDoc:
            sections = {"abstract": "text", "methods": "text"}
            paragraphs = {"abstract": [1, 2], "methods": [3]}
            citations = [1, 2, 3]
            tables = [1]
            provenance_hash = "abc123"
            retrieval_timestamp = "2026-01-01"
            def get_body_text(self):
                return "body text"
        result = bm.benchmark_document_parsing(FakeDoc())
        assert isinstance(result, dict)
        assert "sections_found" in result
        assert result["sections_found"] == 2
        assert result["has_provenance"] is True


class TestEntityPrecisionRecall:
    """Test entity precision/recall benchmark."""

    def test_perfect_precision_recall(self):
        """All extracted entities are correct → precision=1.0, recall=1.0."""
        bm = ExtractorBenchmarks()
        extracted = [{"canonical_id": "nanofiber"}, {"canonical_id": "permeability"}]
        known = ["nanofiber", "permeability"]
        result = bm.benchmark_entity_precision_recall(extracted, known)
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_partial_recall(self):
        """Missing some entities → recall < 1.0."""
        bm = ExtractorBenchmarks()
        extracted = [{"canonical_id": "nanofiber"}]
        known = ["nanofiber", "permeability"]
        result = bm.benchmark_entity_precision_recall(extracted, known)
        assert result["recall"] == 0.5
        assert result["false_negatives"] == 1

    def test_false_positives_lower_precision(self):
        """Wrong entities → precision < 1.0."""
        bm = ExtractorBenchmarks()
        extracted = [{"canonical_id": "nanofiber"}, {"canonical_id": "wrong"}]
        known = ["nanofiber"]
        result = bm.benchmark_entity_precision_recall(extracted, known)
        assert result["precision"] == 0.5
        assert result["false_positives"] == 1

    def test_stable_scoring(self):
        """Same inputs → same results (deterministic)."""
        bm = ExtractorBenchmarks()
        extracted = [{"canonical_id": "a"}, {"canonical_id": "b"}]
        known = ["a", "b", "c"]
        r1 = bm.benchmark_entity_precision_recall(extracted, known)
        r2 = bm.benchmark_entity_precision_recall(extracted, known)
        assert r1 == r2


class TestRelationPrecisionRecall:
    """Test relation precision/recall benchmark."""

    def test_perfect_match(self):
        """All relations match → F1=1.0."""
        bm = ExtractorBenchmarks()
        extracted = [{"subject": "A", "relation": "produces", "object": "B"}]
        known = [{"subject": "A", "relation": "produces", "object": "B"}]
        result = bm.benchmark_relation_precision_recall(extracted, known)
        assert result["f1"] == 1.0

    def test_different_relation_verb_is_miss(self):
        """Different verb → not a match."""
        bm = ExtractorBenchmarks()
        extracted = [{"subject": "A", "relation": "produces", "object": "B"}]
        known = [{"subject": "A", "relation": "enables", "object": "B"}]
        result = bm.benchmark_relation_precision_recall(extracted, known)
        assert result["true_positives"] == 0


class TestMechanismStatusAccuracy:
    """Test mechanism-status accuracy benchmark."""

    def test_all_valid(self):
        """All edges have valid status → accuracy=1.0."""
        bm = ExtractorBenchmarks()
        edges = [
            {"status": "asserted"},
            {"status": "associative"},
            {"status": "verified"},
        ]
        result = bm.benchmark_mechanism_status_accuracy(edges)
        assert result["accuracy"] == 1.0
        assert result["missing_status"] == 0

    def test_missing_status_detected(self):
        """Missing status → accuracy < 1.0."""
        bm = ExtractorBenchmarks()
        edges = [
            {"status": "asserted"},
            {"status": ""},
            {"status": "verified"},
        ]
        result = bm.benchmark_mechanism_status_accuracy(edges)
        assert result["accuracy"] < 1.0
        assert result["missing_status"] == 1


class TestWorldAuditOverturnRate:
    """Test world-audit overturn rate benchmark."""

    def test_all_upheld(self):
        """No overturns → rate=0.0."""
        bm = ExtractorBenchmarks()
        entries = [{"overturned": False}, {"overturned": False}]
        result = bm.benchmark_world_audit_overturn_rate(entries)
        assert result["overturn_rate"] == 0.0
        assert result["upheld"] == 2

    def test_mixed_results(self):
        """Some overturns → rate between 0 and 1."""
        bm = ExtractorBenchmarks()
        entries = [{"overturned": False}, {"overturned": True}, {"overturned": True}]
        result = bm.benchmark_world_audit_overturn_rate(entries)
        assert result["overturn_rate"] > 0.0
        assert result["overturned"] == 2

    def test_separate_from_discovery(self):
        """DR-46: benchmark doesn't depend on novelty labels."""
        bm = ExtractorBenchmarks()
        # The benchmark only checks overturned/upheld, not NOVEL/RETRIEVAL
        entries = [{"overturned": True, "verdict": "RETRIEVAL"}]
        result = bm.benchmark_world_audit_overturn_rate(entries)
        assert "verdict" not in result  # discovery label not in benchmark output
        assert "overturn_rate" in result


class TestRunAllBenchmarks:
    """Test the run_all_benchmarks aggregator."""

    def test_only_runs_provided_benchmarks(self):
        """Only runs benchmarks for provided data."""
        bm = ExtractorBenchmarks()
        results = bm.run_all_benchmarks(
            edges=[{"status": "asserted"}]
        )
        assert "mechanism_status" in results
        assert "document_parsing" not in results  # not provided

    def test_empty_call_returns_empty(self):
        """No data → empty results."""
        bm = ExtractorBenchmarks()
        results = bm.run_all_benchmarks()
        assert results == {}


class TestModuleContract:
    """Test module importability."""

    def test_module_importable(self):
        from benchmarks.extractor_benchmarks import ExtractorBenchmarks
        assert hasattr(ExtractorBenchmarks, "benchmark_document_parsing")
        assert hasattr(ExtractorBenchmarks, "benchmark_entity_precision_recall")
        assert hasattr(ExtractorBenchmarks, "benchmark_relation_precision_recall")
        assert hasattr(ExtractorBenchmarks, "benchmark_mechanism_status_accuracy")
        assert hasattr(ExtractorBenchmarks, "benchmark_world_audit_overturn_rate")
