"""
test_dr98_historical_recalibration.py — Tests for DR-98 Gate B.

Verifies the re-calibration runs all 7 historical claims, computes both
F1 formulas, and produces the expected report files.
"""
import sys
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from audit.measurement_integrity.dr98_historical_recalibration import (
    canon, m_exact, m_token, m_synonym, score_f1,
    HistoricalClaim, HISTORICAL_CLAIMS, recalibrate_claim,
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

def test_canon_normalizes_text():
    assert canon("Thermal Emission") == "thermal_emission"
    assert canon("BIOMINERALIZATION") == "biomineralization"
    assert canon(" heat-dissipation ") == "heat_dissipation"


def test_m_exact_strict_equality():
    assert m_exact("thermal emission", "thermal emission")
    assert not m_exact("thermal emission", "thermal radiation")


def test_m_token_finds_overlap():
    assert m_token("thermal emission", "thermal conductivity")
    assert not m_token("banana", "thermal conductivity")


def test_m_synonym_uses_synonym_map():
    synmap = {"thermal_emission": {"radiative_heat"}}
    assert m_synonym("thermal emission", "radiative heat", synmap)
    assert m_synonym("thermal emission", "thermal emission", synmap)
    assert not m_synonym("banana", "thermal emission", synmap)


# ============================================================================
# SCORE_F1
# ============================================================================

def test_score_f1_returns_both_formulas():
    gold = [{"bridge": "alpha"}, {"bridge": "beta"}]
    candidates = ["alpha", "gamma"]
    r = score_f1(gold, candidates, m_exact, "test")
    # tp=1 (alpha), fp=1 (gamma), fn=1 (beta)
    assert r["tp"] == 1
    assert r["fp"] == 1
    assert r["fn"] == 1
    assert r["precision"] == 0.5  # 1 / (1+1)
    assert r["recall"] == 0.5     # 1 / (1+1)
    # f1_honest = 2*0.5*0.5/(0.5+0.5) = 0.5
    assert r["f1_honest"] == 0.5
    # f1_dr91 = 2*0.5/(1+0.5) = 0.6667
    assert r["f1_dr91"] == round(2 * 0.5 / 1.5, 4)
    # Formula inflation should be positive when fp > 0
    assert r["f1_inflation_from_formula"] > 0


def test_score_f1_dr91_equals_honest_when_no_fp():
    """When fp=0 (every candidate matches), the two formulas agree."""
    gold = [{"bridge": "alpha"}, {"bridge": "beta"}]
    candidates = ["alpha", "beta"]  # both match, no fp
    r = score_f1(gold, candidates, m_exact, "test")
    assert r["fp"] == 0
    assert r["f1_honest"] == r["f1_dr91"] == 1.0
    assert r["f1_inflation_from_formula"] == 0.0


def test_score_f1_handles_empty_gold():
    r = score_f1([], ["alpha"], m_exact, "test")
    assert r["tp"] == 0
    assert r["f1_honest"] == 0.0


# ============================================================================
# HISTORICAL CLAIMS REGISTRY
# ============================================================================

def test_historical_claims_registry_has_7_entries():
    assert len(HISTORICAL_CLAIMS) == 7


def test_historical_claims_have_unique_ids():
    ids = [c.claim_id for c in HISTORICAL_CLAIMS]
    assert len(ids) == len(set(ids))


def test_historical_claims_cover_key_cycles():
    """The claims should cover cycles 145, 150, 170, 188, 201, 243."""
    cycles = {c.cycle for c in HISTORICAL_CLAIMS}
    assert {145, 150, 170, 188, 201, 243}.issubset(cycles)


def test_each_claim_has_required_fields():
    for c in HISTORICAL_CLAIMS:
        assert isinstance(c.claim_id, str) and c.claim_id.startswith("HC-")
        assert isinstance(c.cycle, int)
        assert 0.0 <= c.claimed_f1 <= 1.0
        assert c.description
        assert c.source_file
        assert c.gold_data_id
        assert c.matcher_used


# ============================================================================
# RECALIBRATION
# ============================================================================

def test_recalibrate_claim_returns_all_fields(gold_discoveries, synmap):
    claim = HISTORICAL_CLAIMS[0]  # HC-001
    r = recalibrate_claim(claim, gold_discoveries, synmap)
    expected_fields = {
        "claim_id", "cycle", "description", "source_file", "claimed_f1",
        "matcher_used_originally", "candidate_set", "n_candidates",
        "rescored_strict_f1_honest", "rescored_lenient_f1_dr91",
        "rescored_lenient_f1_honest", "f1_inflation_from_formula",
        "delta_vs_claimed_dr91_convention", "delta_vs_claimed_honest_convention",
        "delta_vs_claimed_strict", "verdict_dr91_convention",
        "verdict_honest_convention", "verdict_strict", "notes",
    }
    assert expected_fields.issubset(r.keys())


def test_recalibrate_hc006_uses_shared_entities(gold_discoveries, synmap):
    """HC-006 is the discovery F1 (shared entities). It must use shared_entities."""
    hc006 = next(c for c in HISTORICAL_CLAIMS if c.claim_id == "HC-006")
    r = recalibrate_claim(hc006, gold_discoveries, synmap)
    assert r["candidate_set"] == "shared_entities"
    # Should reproduce 0.8571 under DR-91 convention
    assert r["rescored_lenient_f1_dr91"] == 0.8571
    assert r["verdict_dr91_convention"] == "SURVIVES"


def test_recalibrate_hc007_uses_all_entities(gold_discoveries, synmap):
    """HC-007 is the recognition F1 (all entities). It must use all_entities."""
    hc007 = next(c for c in HISTORICAL_CLAIMS if c.claim_id == "HC-007")
    r = recalibrate_claim(hc007, gold_discoveries, synmap)
    assert r["candidate_set"] == "all_entities"
    # Should reproduce 1.0 under DR-91 convention
    assert r["rescored_lenient_f1_dr91"] == 1.0
    assert r["verdict_dr91_convention"] == "SURVIVES"


def test_recalibrate_hc005_does_not_survive(gold_discoveries, synmap):
    """HC-005 (cycle 201 F1=0.9189) was invalidated by DR-91; should NOT SURVIVE."""
    hc005 = next(c for c in HISTORICAL_CLAIMS if c.claim_id == "HC-005")
    r = recalibrate_claim(hc005, gold_discoveries, synmap)
    assert r["verdict_dr91_convention"] in ("ERODED", "INVALIDATED")


def test_formula_inflation_is_documented_for_hc007(gold_discoveries, synmap):
    """HC-007 should show significant formula inflation (DR-91 conv >> honest conv)."""
    hc007 = next(c for c in HISTORICAL_CLAIMS if c.claim_id == "HC-007")
    r = recalibrate_claim(hc007, gold_discoveries, synmap)
    # DR-91 convention says 1.0, honest convention says ~0.30
    # Inflation should be > 0.50
    assert r["f1_inflation_from_formula"] > 0.50


# ============================================================================
# END-TO-END
# ============================================================================

def test_main_runs_and_writes_reports():
    from audit.measurement_integrity.dr98_historical_recalibration import main
    rc = main()
    assert rc in [0, 2]  # PASS or FAIL
    reports_dir = REPO / "reports"
    assert (reports_dir / "historical_recalibration.json").exists()
    assert (reports_dir / "historical_recalibration.md").exists()
    data = json.loads((reports_dir / "historical_recalibration.json").read_text())
    assert data["gate"] == "B"
    assert data["gate_name"] == "historical_recalibration"
    assert data["n_claims"] == 7
    assert "gate_verdict" in data
    assert data["gate_verdict"] in ["PASS", "FAIL"]


def test_gate_b_has_verdict_tier_field():
    """Cycle 257 tightening: Gate B must report verdict_tier that is NOT
    SCIENCE_PASS (because this is sensitivity analysis, not full
    recalibration)."""
    from audit.measurement_integrity.dr98_historical_recalibration import main
    main()
    data = json.loads((REPO / "reports" / "historical_recalibration.json").read_text())
    assert "verdict_tier" in data
    assert data["verdict_tier"] in (
        "SENSITIVITY_ANALYSIS_PASS",
        "SCIENCE_PASS",
        "FAIL",
    )
    assert data["verdict_tier"] != "SCIENCE_PASS", (
        "Gate B should not claim SCIENCE_PASS — it is a sensitivity "
        "analysis, not a full historical recalibration."
    )


def test_gate_b_documents_formula_inflation_as_p0():
    """The formula_inflation finding must be marked as P0 severity."""
    from audit.measurement_integrity.dr98_historical_recalibration import main
    main()
    data = json.loads((REPO / "reports" / "historical_recalibration.json").read_text())
    assert data.get("formula_inflation_severity") == "P0"
    assert data.get("formula_inflation_observed") is True
