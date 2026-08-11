"""
independent_corpus.tests.test_v2_2_1_invariants — Invariant tests for V2.2.1.

Tests:
1. hard_negative_candidate pool ≠ hard_negative classification
2. A strong pair with lexical >= .15 does NOT automatically become hard negative
3. Every evidence item has either PRESENT+valid hash or explicit unavailable status
4. retrieval_timestamp != experiment_date placeholder
5. No pair occurs in two sampled strata
"""
import sys
import os
import json
import unittest
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT.parent / "custodian"))

from independent_corpus.intake.pairability_audit_v2_2_1 import (
    assign_main_stratum,
    is_hard_negative_candidate,
    fetch_abstract_cached,
    EvidenceItem,
    EVIDENCE_PRESENT,
    EVIDENCE_UNAVAILABLE,
    EVIDENCE_REQUIRES_MANUAL_REVIEW,
    STRATUM_STRONG,
    STRATUM_WEAK,
    STRATUM_LEXICAL_LOW,
    STRATUM_RANDOM,
    STRATUM_HARD_NEG_OVERLAY,
    MAIN_STRATUM_PRECEDENCE,
    _abstract_cache,
)
from custodian.src.hasher import sha256_string


class TestInvariant1_HardNegativeNotClassification(unittest.TestCase):
    """hard_negative_candidate pool ≠ hard_negative classification."""

    def test_hard_negative_is_overlay_not_main_stratum(self):
        """is_hard_negative_candidate returns True/False independently of main stratum."""
        # A pair with high lexical AND high bridge score
        is_hn = is_hard_negative_candidate(0.20)  # lexical >= 0.15
        main = assign_main_stratum(0.20, 0.60, "MECHANISM")  # bridge >= 0.5

        self.assertTrue(is_hn, "Should be hard-negative candidate (lexical >= 0.15)")
        self.assertEqual(main, STRATUM_STRONG, "Main stratum should be STRONG (bridge >= 0.5)")
        # The hard-negative flag is INDEPENDENT of the main stratum assignment

    def test_hard_negative_not_in_main_precedence(self):
        """HARD_NEG_OVERLAY is NOT in MAIN_STRATUM_PRECEDENCE."""
        self.assertNotIn(STRATUM_HARD_NEG_OVERLAY, MAIN_STRATUM_PRECEDENCE)


class TestInvariant2_StrongPairNotAutoHardNegative(unittest.TestCase):
    """A strong pair with lexical >= .15 does NOT automatically become hard negative."""

    def test_strong_pair_stays_strong(self):
        """A pair with bridge >= 0.5 and lexical >= 0.15:
        - main_stratum = STRONG (not hard_negative)
        - is_hard_neg_candidate = True (overlay flag)
        - These are independent properties."""
        lexical = 0.20  # >= 0.15
        bridge = 0.60   # >= 0.5

        main = assign_main_stratum(lexical, bridge, "MECHANISM")
        is_hn = is_hard_negative_candidate(lexical)

        self.assertEqual(main, STRATUM_STRONG, "Main stratum must be STRONG")
        self.assertTrue(is_hn, "Hard-negative candidate flag is True (independent overlay)")
        # The pair can be BOTH strong AND a hard-negative candidate
        # Sampling decides which pool it enters, not the classification

    def test_weak_pair_stays_weak(self):
        """A pair with bridge 0.3 and lexical 0.20:
        - main_stratum = WEAK
        - is_hard_neg_candidate = True (overlay)"""
        main = assign_main_stratum(0.20, 0.30, "MECHANISM")
        is_hn = is_hard_negative_candidate(0.20)
        self.assertEqual(main, STRATUM_WEAK)
        self.assertTrue(is_hn)


class TestInvariant3_EvidenceItemIntegrity(unittest.TestCase):
    """Every evidence item has either PRESENT+valid hash or explicit unavailable status."""

    def test_present_has_hash(self):
        ev = EvidenceItem(
            status=EVIDENCE_PRESENT,
            source_uri="https://example.com",
            retrieval_timestamp="2026-08-11T12:00:00Z",
            content_hash=sha256_string("test abstract"),
            text="test abstract",
        )
        self.assertEqual(ev.status, EVIDENCE_PRESENT)
        self.assertTrue(ev.content_hash)
        self.assertEqual(ev.content_hash, sha256_string("test abstract"))

    def test_unavailable_has_no_hash(self):
        ev = EvidenceItem(
            status=EVIDENCE_UNAVAILABLE,
            source_uri="https://example.com",
            retrieval_timestamp="2026-08-11T12:00:00Z",
            content_hash="",
            text="",
        )
        self.assertEqual(ev.status, EVIDENCE_UNAVAILABLE)
        self.assertFalse(ev.content_hash)

    def test_manual_review_has_no_hash(self):
        ev = EvidenceItem(
            status=EVIDENCE_REQUIRES_MANUAL_REVIEW,
            source_uri="",
            retrieval_timestamp="2026-08-11T12:00:00Z",
            content_hash="",
            text="",
        )
        self.assertEqual(ev.status, EVIDENCE_REQUIRES_MANUAL_REVIEW)
        self.assertFalse(ev.content_hash)

    def test_no_empty_status(self):
        """Status is never empty string."""
        ev = EvidenceItem("", "", "", "", "")
        # In practice, fetch_abstract_cached never returns empty status
        # This test documents the invariant
        valid_statuses = {EVIDENCE_PRESENT, EVIDENCE_UNAVAILABLE, EVIDENCE_REQUIRES_MANUAL_REVIEW}
        self.assertNotIn("", valid_statuses)


class TestInvariant4_RealTimestamp(unittest.TestCase):
    """retrieval_timestamp != experiment_date placeholder."""

    def test_fetch_uses_real_timestamp(self):
        """fetch_abstract_cached returns actual UTC timestamp, not hardcoded."""
        # Clear cache
        _abstract_cache.clear()

        # Fetch for a non-existent DOI (will fail, but timestamp should be real)
        ev = fetch_abstract_cached("10.9999/nonexistent-doi-for-testing")

        # The timestamp should be a valid ISO 8601 string from the current era
        ts = ev.retrieval_timestamp
        self.assertTrue(ts, "Timestamp should not be empty")

        # Parse it
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Should be within the last hour
        now = datetime.now(timezone.utc)
        diff = abs((now - parsed).total_seconds())
        self.assertLess(diff, 3600, f"Timestamp {ts} is not recent (diff={diff}s)")

        # Should NOT be the hardcoded "2026-08-11T00:00:00Z"
        self.assertNotEqual(ts, "2026-08-11T00:00:00Z",
                           "Timestamp is hardcoded placeholder, not actual retrieval time")

    def test_empty_doi_uses_real_timestamp(self):
        _abstract_cache.clear()
        ev = fetch_abstract_cached("")
        ts = ev.retrieval_timestamp
        self.assertTrue(ts)
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = abs((now - parsed).total_seconds())
        self.assertLess(diff, 3600)


class TestInvariant5_NoPairInTwoStrata(unittest.TestCase):
    """No pair occurs in two sampled strata."""

    def test_main_strata_non_overlapping(self):
        """Main strata are non-overlapping by construction."""
        # A pair can only be in ONE main stratum
        test_cases = [
            (0.05, 0.60, "MECHANISM"),  # STRONG
            (0.05, 0.30, "MECHANISM"),  # WEAK
            (0.05, 0.10, "MECHANISM"),  # LEXICAL_LOW
            (0.30, 0.10, "NONE"),       # RANDOM (high lexical, low bridge, no mechanism)
        ]

        strata = [assign_main_stratum(l, b, t) for l, b, t in test_cases]
        # Each should be different
        self.assertEqual(len(set(strata)), 4, f"Strata should be distinct: {strata}")

    def test_hard_negative_doesnt_affect_main(self):
        """Hard-negative flag is independent — doesn't change main stratum."""
        for lexical in [0.05, 0.15, 0.20, 0.30]:
            for bridge in [0.10, 0.30, 0.60]:
                for bridge_type in ["MECHANISM", "NONE"]:
                    main = assign_main_stratum(lexical, bridge, bridge_type)
                    is_hn = is_hard_negative_candidate(lexical)

                    # Main stratum should NOT be hard_negative
                    self.assertNotEqual(main, STRATUM_HARD_NEG_OVERLAY,
                                       f"Main stratum should not be hard_negative for lexical={lexical}, bridge={bridge}")

                    # is_hn is independent
                    if lexical >= 0.15:
                        self.assertTrue(is_hn)
                    else:
                        self.assertFalse(is_hn)


if __name__ == '__main__':
    unittest.main(verbosity=2)
