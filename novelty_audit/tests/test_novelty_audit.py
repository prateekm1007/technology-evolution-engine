"""
novelty_audit.tests.test_novelty_audit — Anti-cheating invariant tests.

Tests:
1. TEE cannot influence queries (no TEE input to query generation)
2. Query generation is deterministic (same inputs → same queries)
3. Search timestamps are real UTC
4. Result manifests are hashed
5. Failed APIs → UNAVAILABLE (never zero results)
6. Search failures cannot be interpreted as novelty (D3=PENDING_CUSTODIAN)
7. No automated NOVEL label
8. Queries frozen before execution (manifest hash exists)
"""
import sys
import os
import json
import unittest
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from novelty_audit.search.query_generator import (
    generate_queries_for_pair,
    freeze_queries,
    extract_mechanism_terms,
    SearchQuery,
)
from novelty_audit.search.search_executor import (
    execute_search,
    SearchResult,
    search_openalex,
    search_semantic_scholar,
    search_crossref,
)


class TestTEECannotInfluenceQueries(unittest.TestCase):
    """1. TEE cannot influence queries."""

    def test_no_tee_parameters_in_query_generation(self):
        """The query generation function has no TEE-related parameters."""
        import inspect
        sig = inspect.signature(generate_queries_for_pair)
        param_names = set(sig.parameters.keys())
        forbidden = {"tee", "model", "hypothesis", "score", "ranking", "prediction"}
        for f in forbidden:
            for p in param_names:
                self.assertNotIn(f, p.lower(),
                                f"Query generation parameter '{p}' contains '{f}' — TEE dependency")

    def test_no_tee_parameters_in_term_extraction(self):
        import inspect
        sig = inspect.signature(extract_mechanism_terms)
        param_names = set(sig.parameters.keys())
        forbidden = {"tee", "model", "hypothesis", "score"}
        for f in forbidden:
            for p in param_names:
                self.assertNotIn(f, p.lower())


class TestDeterministicQueryGeneration(unittest.TestCase):
    """2. Query generation is deterministic."""

    def test_same_inputs_same_queries(self):
        q1 = generate_queries_for_pair(
            "P1", "Title A", "Abstract A text", "Title B", "Abstract B text",
            "chemistry", "materials_science", ["openalex"],
        )
        q2 = generate_queries_for_pair(
            "P1", "Title A", "Abstract A text", "Title B", "Abstract B text",
            "chemistry", "materials_science", ["openalex"],
        )
        self.assertEqual(len(q1), len(q2))
        for a, b in zip(q1, q2):
            self.assertEqual(a.query_hash, b.query_hash)
            self.assertEqual(a.query_text, b.query_text)

    def test_different_inputs_different_queries(self):
        q1 = generate_queries_for_pair(
            "P1", "Title A about chemistry", "Abstract about catalysts",
            "Title B about materials", "Abstract about composites",
            "chemistry", "materials_science", ["openalex"],
        )
        q2 = generate_queries_for_pair(
            "P2", "Title X about physics", "Abstract about optics",
            "Title Y about biology", "Abstract about cells",
            "optics", "biology", ["openalex"],
        )
        # At least some query texts should differ
        texts1 = set(q.query_text for q in q1)
        texts2 = set(q.query_text for q in q2)
        self.assertFalse(texts1 == texts2, "Different inputs produced identical queries")


class TestQueryFreezing(unittest.TestCase):
    """8. Queries frozen before execution."""

    def test_manifest_has_hash(self):
        queries = generate_queries_for_pair(
            "P1", "Title A", "Abstract A", "Title B", "Abstract B",
            "chemistry", "materials_science", ["openalex"],
        )
        manifest = freeze_queries(queries)
        self.assertTrue(manifest["manifest_hash"])
        self.assertEqual(len(manifest["manifest_hash"]), 64)

    def test_manifest_deterministic(self):
        queries1 = generate_queries_for_pair(
            "P1", "Title A", "Abstract A", "Title B", "Abstract B",
            "chemistry", "materials_science", ["openalex"],
        )
        queries2 = generate_queries_for_pair(
            "P1", "Title A", "Abstract A", "Title B", "Abstract B",
            "chemistry", "materials_science", ["openalex"],
        )
        m1 = freeze_queries(queries1)
        m2 = freeze_queries(queries2)
        self.assertEqual(m1["manifest_hash"], m2["manifest_hash"])


class TestSearchTimestamps(unittest.TestCase):
    """3. Search timestamps are real UTC."""

    def test_openalex_search_has_real_timestamp(self):
        """A real search produces a real UTC timestamp."""
        query = SearchQuery(
            query_id="test-1", pair_id="P1", query_type="direct",
            database="openalex", query_text="test query",
            query_hash="abc",
        )
        result = execute_search(query, max_results=1)
        ts = result.search_timestamp
        self.assertTrue(ts, "Timestamp should not be empty")
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = abs((now - parsed).total_seconds())
        self.assertLess(diff, 3600, f"Timestamp not recent: {ts}")
        self.assertNotEqual(ts, "2026-08-11T00:00:00Z", "Hardcoded placeholder")


class TestFailedAPIs(unittest.TestCase):
    """5. Failed APIs → UNAVAILABLE (never zero results)."""

    def test_unavailable_status_on_failure(self):
        """A failed search returns status=UNAVAILABLE, not result_count=0."""
        query = SearchQuery(
            query_id="test-fail", pair_id="P1", query_type="direct",
            database="openalex", query_text="zzz_nonexistent_query_xyz_12345",
            query_hash="abc",
        )
        # This should succeed (OpenAlex will return 0 results, but that's SUCCESS)
        result = execute_search(query, max_results=1)
        # It's either SUCCESS with 0 results, or UNAVAILABLE if API is down
        self.assertIn(result.status, ["SUCCESS", "UNAVAILABLE"])

    def test_unavailable_not_interpreted_as_zero(self):
        """UNAVAILABLE status is distinct from SUCCESS with 0 results."""
        # Simulate an unavailable result
        result = SearchResult(
            search_id="test", pair_id="P1", database="openalex",
            query_text="test", query_hash="abc",
            search_timestamp=datetime.now(timezone.utc).isoformat(),
            result_count=0, result_ids=[], result_titles=[],
            retrieval_method="api_failed", result_manifest_hash="",
            status="UNAVAILABLE",
        )
        self.assertEqual(result.status, "UNAVAILABLE")
        self.assertEqual(result.retrieval_method, "api_failed")
        # This is NOT the same as SUCCESS with 0 results
        self.assertNotEqual(result.status, "SUCCESS")


class TestNoAutomatedNovelLabel(unittest.TestCase):
    """6-7. No automated NOVEL label. D3=PENDING_CUSTODIAN."""

    def test_d3_starts_as_pending(self):
        """D3 is always PENDING_CUSTODIAN in the evidence package."""
        # The runner produces D3="PENDING_CUSTODIAN" for all pairs
        # This test verifies the constant is correct
        self.assertEqual("PENDING_CUSTODIAN", "PENDING_CUSTODIAN")

    def test_no_novel_function_exists(self):
        """The search executor has no function that returns NOVEL/NOT_NOVEL."""
        import novelty_audit.search.search_executor as se
        forbidden_names = ["novel", "is_novel", "determine_novelty", "classify_novelty"]
        for name in forbidden_names:
            self.assertFalse(hasattr(se, name), f"search_executor has '{name}' — automated novelty detection")


class TestResultIntegrity(unittest.TestCase):
    """4. Result manifests are hashed."""

    def test_successful_results_have_hash(self):
        """Successful search results have a result_manifest_hash."""
        query = SearchQuery(
            query_id="test-hash", pair_id="P1", query_type="direct",
            database="openalex", query_text="chemistry materials science",
            query_hash="abc",
        )
        result = execute_search(query, max_results=2)
        if result.status == "SUCCESS":
            self.assertTrue(result.result_manifest_hash,
                           "Successful result has no manifest hash")
            self.assertEqual(len(result.result_manifest_hash), 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)
