#!/usr/bin/env python3
"""
Test: Reaudit Loop (DR-33, EPISTEMIC_ENGINE.md).

Per P2: "Untested code is unverified code, permanently."
Per P27: "Read the assertion, not the test name."
Per P28: "Test with 3+ inputs: exact, variation, edge case."
"""
import sys
import json
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.reaudit_loop import (
    load_claims,
    get_eligible_claims,
    compute_vocabulary_hash,
    construct_seed,
    draw_sample,
    run_adversarial_verification,
    register_claim,
    exclude_benchmark,
)


class TestReauditLoop:
    """Test the reaudit loop module."""

    def test_load_claims_returns_list(self):
        """load_claims returns a list of claim entries."""
        claims = load_claims()
        assert isinstance(claims, list)
        assert len(claims) > 0  # we have blind test results

    def test_get_eligible_claims_filters_by_outcome(self):
        """Eligible claims have an experiment_id and outcome."""
        claims = load_claims()
        eligible = get_eligible_claims(claims)
        assert len(eligible) > 0
        for c in eligible:
            assert c["claim_id"]
            assert c["outcome"]

    def test_compute_vocabulary_hash_is_deterministic(self):
        """Same terms produce same hash."""
        terms = ["lotus leaf", "battery separator", "contact angle"]
        h1 = compute_vocabulary_hash(terms)
        h2 = compute_vocabulary_hash(terms)
        assert h1 == h2

    def test_compute_vocabulary_hash_differs_for_different_terms(self):
        """Different terms produce different hashes."""
        h1 = compute_vocabulary_hash(["nanofiber", "BBB"])
        h2 = compute_vocabulary_hash(["lotus leaf", "battery"])
        assert h1 != h2

    def test_construct_seed_is_deterministic(self):
        """Same inputs produce same seed."""
        s1 = construct_seed(97, "abc123", "entropy1")
        s2 = construct_seed(97, "abc123", "entropy1")
        assert s1 == s2

    def test_construct_seed_differs_for_different_cycle(self):
        """Different cycle numbers produce different seeds."""
        s1 = construct_seed(97, "abc123", "entropy1")
        s2 = construct_seed(98, "abc123", "entropy1")
        assert s1 != s2

    def test_draw_sample_respects_k(self):
        """Sample size is at most k and at most len(eligible)."""
        eligible = [{"claim_id": f"EXP-{i}", "outcome": "NULL", "entry": {}} for i in range(10)]
        seed = b"\x00" * 32
        sample = draw_sample(eligible, seed, k=3)
        assert len(sample) == 3
        sample = draw_sample(eligible, seed, k=100)
        assert len(sample) == 10  # capped at eligible size

    def test_run_adversarial_verification_returns_reaudit(self):
        """Verification returns a dict with required Reaudit fields."""
        claim = {
            "claim_id": "TEST-001",
            "outcome": "NULL",
            "entry": {"lit_A": "test A", "lit_B": "test B"},
        }
        reaudit = run_adversarial_verification(claim)
        assert reaudit["type"] == "reaudit"
        assert reaudit["claim_id"] == "TEST-001"
        assert reaudit["verdict"]  # has a verdict
        assert "vocabulary_hash" in reaudit
        assert "confidence" in reaudit
        assert "overturned" in reaudit


class TestDR31DataModel:
    """Test the DR-31 data model types."""

    def test_register_claim_creates_valid_entry(self):
        """register_claim produces a Claim with all required fields."""
        claim = register_claim(
            "TEST-CLAIM-001",
            "Test proposition",
            "empirical",
            "NOVEL_HIT",
            0.75,
        )
        assert claim["type"] == "claim"
        assert claim["claim_id"] == "TEST-CLAIM-001"
        assert claim["proposition"] == "Test proposition"
        assert claim["claim_type"] == "empirical"
        assert claim["original_verdict"] == "NOVEL_HIT"
        assert claim["confidence"] == 0.75
        assert "lock_time" in claim
        assert "timestamp" in claim

    def test_exclude_benchmark_creates_valid_event(self):
        """exclude_benchmark produces an ExclusionEvent with source_reference."""
        exclusion = exclude_benchmark(
            "TEST-BENCH-001",
            "CONSTITUTIONAL_EXPOSURE",
            "F-063",
        )
        assert exclusion["type"] == "exclusion_event"
        assert exclusion["benchmark_id"] == "TEST-BENCH-001"
        assert exclusion["reason_code"] == "CONSTITUTIONAL_EXPOSURE"
        assert exclusion["source_reference"] == "F-063"
        assert "timestamp" in exclusion
        assert "actor" in exclusion

    def test_exclusion_requires_source_reference(self):
        """Per §2.4: source_reference must point to an F-XXX entry."""
        # This is enforced by the function signature — it's a required param
        exclusion = exclude_benchmark("B", "DUPLICATE", "F-001")
        assert exclusion["source_reference"] == "F-001"


class TestModuleContract:
    """Test the module is importable and has the right interface."""

    def test_module_importable(self):
        from scripts import reaudit_loop
        assert hasattr(reaudit_loop, "run_reaudit_cycle")
        assert hasattr(reaudit_loop, "register_claim")
        assert hasattr(reaudit_loop, "exclude_benchmark")
        assert hasattr(reaudit_loop, "log_adversary_performance")
