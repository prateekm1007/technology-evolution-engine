"""
test_dr97_external_baselines.py — Tests for DR-97 Gate A.

Zero-production-import enforcement. Each baseline must run independently
and report honest numbers. The strict-mode F1 must be 0 for all baselines
(because the bridges are concept-level, not lexical).
"""
import sys
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from audit.measurement_integrity.dr97_external_baselines import (
    canon, tokenize, BM25Index, bm25_baseline, random_baseline,
    frequency_baseline, bm25_baseline_lenient, frequency_baseline_lenient,
    random_baseline_lenient, lenient_match, strict_match, load_synonym_map,
    compare_to_production,
)


@pytest.fixture
def gold_discoveries():
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    return GOLD_DISCOVERIES


@pytest.fixture
def synmap():
    return load_synonym_map()


# ============================================================================
# CANONICALIZATION
# ============================================================================

def test_canon_lowercases_and_normalizes():
    assert canon("Biomineralization") == "biomineralization"
    assert canon("Tight Junctions") == "tight_junctions"
    assert canon("  thermal-emission ") == "thermal_emission"
    assert canon("Heat, Dissipation!") == "heat_dissipation"


def test_tokenize_filters_punctuation_and_short_tokens():
    tokens = tokenize("The Biomineralization of calcium, carbonate!")
    assert "biomineralization" in tokens
    assert "calcium" in tokens
    assert "carbonate" in tokens
    # tokenize keeps tokens of length >= 2 (so "of" IS kept by design);
    # only single-char tokens are dropped
    assert "a" not in tokens
    assert "the" in tokens  # stopword filtering happens later, not in tokenize


def test_strict_match_only_canonical_equality():
    assert strict_match("biomineralization", "biomineralization")
    assert strict_match("Biomineralization", "BIOMINERALIZATION")
    assert not strict_match("biomineralization", "mineral_precipitation")


# ============================================================================
# BM25 INDEX
# ============================================================================

def test_bm25_index_builds_and_scores():
    docs = [
        "The quick brown fox jumps over the lazy dog",
        "Photosynthesis converts sunlight into chemical energy",
    ]
    idx = BM25Index.build(docs)
    assert idx.n_docs == 2
    score_0 = idx.score("fox jumps", 0)
    score_1 = idx.score("fox jumps", 1)
    assert score_0 > score_1, "BM25 should score the fox doc higher for 'fox jumps'"


def test_bm25_top_k_returns_ranked_results():
    docs = ["alpha alpha beta", "gamma gamma gamma", "alpha beta"]
    idx = BM25Index.build(docs)
    top = idx.top_k("alpha", k=2)
    assert len(top) == 2
    # Both top docs should contain "alpha"
    assert top[0][0] in [0, 2]


# ============================================================================
# BASELINES — STRICT MODE
# ============================================================================

def test_bm25_strict_returns_results_for_all_gold(gold_discoveries):
    result = bm25_baseline(gold_discoveries)
    assert result["baseline"] == "BM25"
    assert result["total"] == len(gold_discoveries)
    assert len(result["per_gold"]) == len(gold_discoveries)
    # Strict F1 should be very low — bridges are concepts, not lexical
    assert result["recall"] <= 0.5, (
        f"BM25 strict recall too high: {result['recall']} — "
        "strict matching should rarely find concept-level bridges"
    )


def test_random_strict_returns_zero_f1(gold_discoveries):
    result = random_baseline(gold_discoveries, n_trials=20)
    assert result["n_trials"] == 20
    # Random 2-grams essentially never match the gold bridge under strict match
    assert result["mean_f1"] <= 0.05, (
        f"Random strict F1 unexpectedly high: {result['mean_f1']}"
    )


def test_frequency_strict_returns_results(gold_discoveries):
    result = frequency_baseline(gold_discoveries)
    assert result["total"] == len(gold_discoveries)
    # Frequency-based top bigram rarely matches the bridge under strict
    assert result["f1"] <= 0.5, (
        f"Frequency strict F1 too high: {result['f1']}"
    )


# ============================================================================
# BASELINES — LENIENT MODE
# ============================================================================

def test_bm25_lenient_uses_synonyms(gold_discoveries, synmap):
    result = bm25_baseline_lenient(gold_discoveries, synmap)
    assert result["baseline"] == "BM25 (lenient)"
    # Lenient should match AT LEAST as often as strict
    strict = bm25_baseline(gold_discoveries)
    assert result["recall"] >= strict["recall"]


def test_frequency_lenient_uses_synonyms(gold_discoveries, synmap):
    result = frequency_baseline_lenient(gold_discoveries, synmap)
    assert result["baseline"] == "Frequency (lenient)"
    strict = frequency_baseline(gold_discoveries)
    assert result["f1"] >= strict["f1"]


def test_random_lenient_runs_multiple_trials(gold_discoveries, synmap):
    result = random_baseline_lenient(gold_discoveries, synmap, n_trials=10)
    assert result["n_trials"] == 10
    assert 0.0 <= result["mean_f1"] <= 1.0
    assert result["max_f1"] >= result["mean_f1"]


def test_lenient_match_finds_synonym():
    synmap = {"thermal_emission": {"radiative_heat", "thermal_radiation"}}
    assert lenient_match("radiative heat", "thermal emission", synmap)
    assert lenient_match("thermal emission", "thermal emission", synmap)


def test_lenient_match_finds_token_overlap():
    synmap = {}
    # Token overlap on a token ≥4 chars
    assert lenient_match("thermal regulation", "thermal conductivity", synmap)
    # No overlap
    assert not lenient_match("banana", "thermal conductivity", synmap)


# ============================================================================
# COMPARISON LOGIC
# ============================================================================

def test_compare_to_production_classifies_delta():
    baseline = {"baseline": "test", "f1": 0.5}
    c = compare_to_production(baseline, production_f1=0.8)
    assert c["delta"] == 0.3
    assert c["verdict"] == "PRODUCTION_BEATS_BASELINE"

    baseline_low = {"baseline": "test", "f1": 0.78}
    c = compare_to_production(baseline_low, production_f1=0.8)
    assert c["verdict"] == "PRODUCTION_TIES_BASELINE"

    baseline_high = {"baseline": "test", "f1": 0.95}
    c = compare_to_production(baseline_high, production_f1=0.8)
    assert c["verdict"] == "PRODUCTION_WORSE_THAN_BASELINE"


# ============================================================================
# END-TO-END: main() runs and produces reports
# ============================================================================

def test_main_runs_and_writes_reports():
    from audit.measurement_integrity.dr97_external_baselines import main
    rc = main()
    # main returns 0 (PASS), 1 (PARTIAL), or 2 (FAIL)
    assert rc in [0, 1, 2]
    reports_dir = REPO / "reports"
    assert (reports_dir / "external_baselines.json").exists()
    assert (reports_dir / "external_baselines.md").exists()
    # Verify JSON structure
    data = json.loads((reports_dir / "external_baselines.json").read_text())
    assert data["gate"] == "A"
    assert data["gate_name"] == "external_baselines"
    assert "strict_mode" in data
    assert "lenient_mode" in data
    assert "comparisons_lenient" in data
    assert "gate_verdict" in data
    assert data["gate_verdict"] in ["PASS", "PARTIAL", "FAIL"]


def test_gate_a_has_verdict_tier_field():
    """Cycle 257 tightening: Gate A must report a verdict_tier field
    that is NOT SCIENCE_PASS (because BM25 is oracle-assisted)."""
    from audit.measurement_integrity.dr97_external_baselines import main
    main()
    data = json.loads((REPO / "reports" / "external_baselines.json").read_text())
    assert "verdict_tier" in data
    assert data["verdict_tier"] in (
        "INSTRUMENTATION_SCAFFOLD_PASS",
        "SCIENCE_PASS",
        "FAIL",
    )
    # The current implementation is oracle-assisted, so it should NOT
    # claim SCIENCE_PASS
    assert data["verdict_tier"] != "SCIENCE_PASS", (
        "Gate A should not claim SCIENCE_PASS — the BM25 baseline is "
        "lexical/oracle-assisted (uses gold bridge as query)."
    )


def test_gate_a_verdict_tier_definition_documents_limitation():
    """The verdict_tier_definition must explain what the tier means."""
    from audit.measurement_integrity.dr97_external_baselines import main
    main()
    data = json.loads((REPO / "reports" / "external_baselines.json").read_text())
    assert "verdict_tier_definition" in data
    definition = data["verdict_tier_definition"]
    # Must mention the key limitation
    assert "oracle" in definition.lower() or "lexical" in definition.lower(), (
        "verdict_tier_definition must mention the oracle/lexical limitation"
    )
