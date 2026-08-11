"""
test_dr99_proposal_evaluation_n30.py — Tests for DR-99 Gate C.
"""
import sys
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from audit.measurement_integrity.dr99_proposal_evaluation_n30 import (
    canon, m_exact, m_synonym, score_one, f1_honest, f1_dr91,
    perturb_snippet_pair, evaluate_n30, compute_distribution_stats,
    t_test_against_fp_floor, _percentile,
)


@pytest.fixture
def gold_discoveries():
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    return GOLD_DISCOVERIES


@pytest.fixture
def synmap():
    from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
    return {canon(k): {canon(s) for s in v} for k, v in BRIDGE_SYNONYMS.items()}


# ============================================================================
# MATCHERS
# ============================================================================

def test_canon_normalizes():
    assert canon("Thermal Emission") == "thermal_emission"
    assert canon("Heat-Dissipation!") == "heat_dissipation"


def test_m_exact_strict():
    assert m_exact("a", "a")
    assert not m_exact("a", "b")


def test_m_synonym_with_map():
    synmap = {"thermal_emission": {"radiative_heat"}}
    assert m_synonym("thermal emission", "radiative heat", synmap)
    assert not m_synonym("banana", "thermal emission", synmap)


# ============================================================================
# SCORE_ONE / F1
# ============================================================================

def test_score_one_match_returns_tp():
    tp, fp, fn = score_one("alpha", "alpha", m_exact)
    assert (tp, fp, fn) == (1, 0, 0)


def test_score_one_no_match_returns_fp_fn():
    tp, fp, fn = score_one("alpha", "beta", m_exact)
    assert (tp, fp, fn) == (0, 1, 1)


def test_f1_honest_match_is_1():
    assert f1_honest(1, 0, 0) == 1.0


def test_f1_honest_no_match_is_0():
    assert f1_honest(0, 1, 1) == 0.0


def test_f1_dr91_equals_honest_when_no_fp():
    """When fp=0, both formulas agree."""
    assert f1_honest(1, 0, 0) == f1_dr91(1, 0, 0) == 1.0


def test_f1_dr91_inflates_when_fp_present():
    """DR-91 convention inflates F1 when there are false positives."""
    # tp=1, fp=5, fn=0: precision=1/6, recall=1
    # honest F1 = 2*(1/6)*1 / (1/6 + 1) = (1/3) / (7/6) = 2/7 ≈ 0.286
    # dr91 F1 = 2*1 / (1+1) = 1.0 (ignores fp!)
    assert f1_honest(1, 5, 0) < f1_dr91(1, 5, 0)
    assert f1_dr91(1, 5, 0) == 1.0  # ignores fp entirely


# ============================================================================
# PERTURBATION
# ============================================================================

def test_perturb_strategy_0_swaps_a_b():
    a = "First sentence. Second sentence."
    b = "Third sentence. Fourth sentence."
    pa, pb = perturb_snippet_pair(a, b, seed=0)
    assert (pa, pb) == (b, a)


def test_perturb_preserves_information():
    """Any perturbation should still contain meaningful text."""
    a = "Alpha beta gamma. Delta epsilon zeta."
    b = "Eta theta iota. Kappa lambda mu."
    for seed in range(8):
        pa, pb = perturb_snippet_pair(a, b, seed=seed)
        # At least one of pa/pb should have content
        assert len(pa) + len(pb) > 0


def test_perturb_strategy_out_of_range_returns_original():
    """Seeds that map to no-op should fall back to original."""
    a = "Single sentence only."
    b = "Another single sentence."
    # Strategy 1 (drop last sentence of A) requires len(a_sents) > 1
    # So seed=1 should fall back to original
    pa, pb = perturb_snippet_pair(a, b, seed=1)
    assert (pa, pb) == (a, b)


# ============================================================================
# EVALUATE N30
# ============================================================================

def test_evaluate_n30_returns_at_least_30(gold_discoveries, synmap):
    evaluations = evaluate_n30(gold_discoveries, synmap)
    assert len(evaluations) >= 30
    # Should be 20 original + 20 synthetic = 40
    assert len(evaluations) == 40


def test_evaluate_n30_has_original_and_synthetic(gold_discoveries, synmap):
    evaluations = evaluate_n30(gold_discoveries, synmap)
    sources = {e.source for e in evaluations}
    assert "original" in sources
    assert any(s.startswith("synthetic-strategy-") for s in sources)


def test_evaluate_n30_evaluations_have_required_fields(gold_discoveries, synmap):
    evaluations = evaluate_n30(gold_discoveries, synmap)
    e = evaluations[0]
    assert hasattr(e, "proposal_id")
    assert hasattr(e, "gold_bridge")
    assert hasattr(e, "candidate_entity")
    assert hasattr(e, "match_strict")
    assert hasattr(e, "match_lenient")
    assert hasattr(e, "f1_strict_honest")
    assert hasattr(e, "f1_lenient_dr91")
    assert hasattr(e, "f1_lenient_honest")
    assert hasattr(e, "source")


def test_evaluate_n30_f1_values_are_0_or_1(gold_discoveries, synmap):
    """Per-proposal F1 is binary (match/no-match)."""
    evaluations = evaluate_n30(gold_discoveries, synmap)
    for e in evaluations:
        assert e.f1_strict_honest in (0.0, 1.0)
        assert e.f1_lenient_honest in (0.0, 1.0)
        assert e.f1_lenient_dr91 in (0.0, 1.0)


# ============================================================================
# DISTRIBUTION STATS
# ============================================================================

def test_compute_distribution_stats_returns_all_fields(gold_discoveries, synmap):
    evaluations = evaluate_n30(gold_discoveries, synmap)
    stats = compute_distribution_stats(evaluations)
    assert "n_total" in stats
    assert "n_original" in stats
    assert "n_synthetic" in stats
    assert "strict_honest" in stats
    assert "lenient_dr91" in stats
    assert "lenient_honest" in stats
    for k in ("strict_honest", "lenient_dr91", "lenient_honest"):
        s = stats[k]
        for field in ("n", "mean", "median", "stdev", "min", "max", "q25", "q75"):
            assert field in s


def test_percentile_simple_cases():
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == 3.0
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0) == 1.0
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 100) == 5.0
    assert _percentile([], 50) == 0.0


# ============================================================================
# T-TEST
# ============================================================================

def test_t_test_against_fp_floor_rejects_when_mean_below_floor(gold_discoveries, synmap):
    evaluations = evaluate_n30(gold_discoveries, synmap)
    result = t_test_against_fp_floor(evaluations, fp_floor=1.0)
    assert result["test"] == "t_test"
    assert result["n"] >= 30
    assert "mean" in result
    assert "stdev" in result
    assert "t_statistic" in result
    assert "p_value" in result
    assert "verdict" in result
    # Mean honest F1 is well below 1.0
    assert result["mean"] < 1.0
    # Should reject H0 (mean = 1.0) at p<0.05
    assert result["verdict"] == "REJECT_H0"


def test_t_test_against_fp_floor_handles_zero_variance():
    """If all values are the same, variance is 0; test should handle gracefully."""
    from audit.measurement_integrity.dr99_proposal_evaluation_n30 import ProposalEvaluation
    evals = [
        ProposalEvaluation(
            proposal_id=f"P-{i}",
            gold_bridge="x",
            candidate_entity="y",
            match_strict=False,
            match_lenient=False,
            f1_strict_honest=0.5,
            f1_lenient_dr91=0.5,
            f1_lenient_honest=0.5,
            source="test",
        )
        for i in range(30)
    ]
    result = t_test_against_fp_floor(evals, fp_floor=1.0)
    # All same → se=0 → t=-inf or +inf
    assert result["test"] == "t_test"
    assert result["verdict"] in ("REJECT_H0", "FAIL_TO_REJECT")


# ============================================================================
# END-TO-END
# ============================================================================

def test_main_runs_and_writes_reports():
    from audit.measurement_integrity.dr99_proposal_evaluation_n30 import main
    rc = main()
    assert rc in [0, 1, 2]
    reports_dir = REPO / "reports"
    assert (reports_dir / "proposal_evaluation_n30.json").exists()
    assert (reports_dir / "proposal_evaluation_n30.md").exists()
    data = json.loads((reports_dir / "proposal_evaluation_n30.json").read_text())
    assert data["gate"] == "C"
    assert data["gate_name"] == "proposal_evaluation_n30"
    assert data["n_total"] >= 30
    assert data["n_met"] is True
    assert "gate_verdict" in data
    assert data["gate_verdict"] in ["PASS", "PARTIAL", "FAIL"]


def test_gate_c_has_verdict_tier_field():
    """Cycle 257 tightening: Gate C must report verdict_tier that is NOT
    SCIENCE_PASS (because per-proposal F1=0.15 is below 0.30 threshold)."""
    from audit.measurement_integrity.dr99_proposal_evaluation_n30 import main
    main()
    data = json.loads((REPO / "reports" / "proposal_evaluation_n30.json").read_text())
    assert "verdict_tier" in data
    assert data["verdict_tier"] in (
        "WEAK_STATISTICAL_PASS",
        "SCIENCE_PASS",
        "FAIL",
    )
    assert data["verdict_tier"] != "SCIENCE_PASS", (
        "Gate C should not claim SCIENCE_PASS — per-proposal honest F1 "
        "(0.1500) is below the useful-performance threshold (0.30)."
    )


def test_gate_c_reports_useful_performance_threshold_and_result():
    """Gate C must report the useful-performance threshold and whether it
    was met (cycle 257 tightening)."""
    from audit.measurement_integrity.dr99_proposal_evaluation_n30 import main
    main()
    data = json.loads((REPO / "reports" / "proposal_evaluation_n30.json").read_text())
    assert "useful_performance_threshold" in data
    assert data["useful_performance_threshold"] == 0.30
    assert "useful_performance_met" in data
    assert "honest_f1_mean" in data
    # Current observed mean is 0.15, below threshold
    assert data["useful_performance_met"] is False
    assert data["honest_f1_mean"] < data["useful_performance_threshold"]
