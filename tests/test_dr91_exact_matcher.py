"""Tests for DR-91 Phase 1: Independent measurement audit.

Tests that the independent matcher:
- Does NOT import production matching code
- Produces separate scores per mode
- Detects proposal-locus inflation
- Estimates false-positive floor via shuffled gold
"""
import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_exact_matcher_imports():
    """Module imports cleanly."""
    from audit.stage_minus1.exact_matcher import (
        independent_canonicalize,
        match_exact_normalized, match_exact_token, match_fuzzy,
        match_with_synonyms,
        score_gold_set, score_all_modes, score_proposal_only,
        shuffled_gold_estimate,
    )
    assert independent_canonicalize is not None


def test_no_production_imports():
    """The matcher does NOT import production MATCHING LOGIC.

    Per DR-91: 'Must NOT import production matcher.'
    The matcher can import GOLD DATA (read-only) but not the
    _bridge_matches function or BRIDGE_SYNONYMS map.
    """
    import audit.stage_minus1.exact_matcher as am
    source = open(am.__file__).read()
    # Must NOT import the matching function
    assert "from benchmarks.discovery_capability_benchmark import _bridge_matches" not in source, \
        "Independent matcher must NOT import _bridge_matches from production"
    # Must NOT import canonicalize from production
    assert "from benchmarks.discovery_capability_benchmark import canonicalize" not in source, \
        "Independent matcher must NOT import canonicalize from production"
    # CAN import GOLD_DISCOVERIES (data, not logic) — this is allowed
    # because the audit needs the gold set to score against


def test_canonicalize_independent():
    """Canonicalization works correctly."""
    from audit.stage_minus1.exact_matcher import independent_canonicalize
    assert independent_canonicalize("Thermal Emission") == "thermal_emission"
    assert independent_canonicalize("thermal-emission") == "thermal_emission"
    assert independent_canonicalize("  THERMAL_EMISSION  ") == "thermal_emission"
    assert independent_canonicalize("thermal emission!") == "thermal_emission"


def test_exact_normalized_strict():
    """Exact normalized match is strict — only identical canonical forms match."""
    from audit.stage_minus1.exact_matcher import match_exact_normalized
    assert match_exact_normalized("thermal_emission", "thermal emission")
    assert not match_exact_normalized("thermal_emission", "radiative_heat")
    assert not match_exact_normalized("thermal_emission", "thermal_emissions")


def test_exact_token_substring():
    """Token match catches substrings and significant token overlap."""
    from audit.stage_minus1.exact_matcher import match_exact_token
    assert match_exact_token("thermal_emission", "thermal_emissions")  # substring
    assert match_exact_token("thermal_emission", "thermal radiation emission")  # token overlap
    assert not match_exact_token("thermal_emission", "battery")


def test_fuzzy_near_miss():
    """Fuzzy match catches near-misses via bigram similarity."""
    from audit.stage_minus1.exact_matcher import match_fuzzy
    assert match_fuzzy("thermal_emission", "thermal_emissions")  # plural
    assert not match_fuzzy("thermal_emission", "battery")


def test_synonym_match():
    """Synonym match uses the synonym map."""
    from audit.stage_minus1.exact_matcher import match_with_synonyms
    syns = {"thermal_emission": {"radiative_heat", "thermal_radiation"}}
    assert match_with_synonyms("thermal_emission", "radiative_heat", syns)
    assert match_with_synonyms("thermal_emission", "thermal_radiation", syns)
    assert not match_with_synonyms("thermal_emission", "battery", syns)


def test_score_gold_set():
    """Score function produces correct TP/FN/recall/F1."""
    from audit.stage_minus1.exact_matcher import score_gold_set, match_exact_normalized
    gold = [{"bridge": "alpha"}, {"bridge": "beta"}, {"bridge": "gamma"}]
    entities = ["alpha", "delta"]  # 1 TP, 2 FN
    result = score_gold_set(gold, entities, match_exact_normalized)
    assert result.true_positives == 1
    assert result.false_negatives == 2
    assert abs(result.recall - 1/3) < 0.01


def test_shuffled_gold_estimate():
    """Shuffled gold estimates false-positive floor."""
    from audit.stage_minus1.exact_matcher import shuffled_gold_estimate, match_exact_normalized
    gold = [{"bridge": "alpha"}, {"bridge": "beta"}]
    entities = ["alpha", "beta", "gamma", "delta"]
    result = shuffled_gold_estimate(gold, entities, match_exact_normalized, n_shuffles=100)
    assert "fp_floor" in result
    assert "mean" in result
    assert result["n_shuffles"] == 100


def test_modes_produce_different_scores():
    """HONEST TEST: different matching modes produce different scores.

    The key finding: exact match scores 0.0 while synonym match scores
    1.0. This means ALL discovery credit comes from fuzzy/synonym
    matching, not exact extraction. If all modes scored the same,
    the mode separation would be meaningless.
    """
    from audit.stage_minus1.exact_matcher import (
        score_gold_set, match_exact_normalized, match_with_synonyms,
    )
    gold = [{"bridge": "thermal_emission"}]
    entities = ["radiative_heat"]
    syns = {"thermal_emission": {"radiative_heat"}}

    exact_result = score_gold_set(gold, entities, match_exact_normalized)
    syn_result = score_gold_set(gold, entities,
                                 lambda e, c: match_with_synonyms(e, c, syns))

    # Exact should be 0 (no exact match), synonym should be 1
    assert exact_result.f1 == 0.0, "Exact match should fail for synonym-only match"
    assert syn_result.f1 > 0, "Synonym match should succeed"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
