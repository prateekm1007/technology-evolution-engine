"""
test_sensitivity_m6.py — Tests for Stage M6 (Sensitivity Analysis).

Verifies:
  1. SensitivityResult has all required fields
  2. classify_sensitivity thresholds are correct
  3. Perturbation functions produce different inputs
  4. reports/sensitivity_m6.json exists with correct structure
  5. All 4 tested metrics have results
  6. FRAGILE perturbations are documented
  7. M-008 is the most robust metric (0 FRAGILE)
"""
import sys
import json
from pathlib import Path
from dataclasses import fields as dataclass_fields

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.sensitivity_m6 import (
    SensitivityResult, classify_sensitivity,
    perturb_input_drop_sentence, perturb_input_shuffle_sentences,
    perturb_input_truncate_75pct, perturb_gold_drop_1, perturb_gold_drop_2,
    perturb_gold_rename, perturb_synonym_remove_1,
    perturb_synonym_remove_25pct, perturb_synonym_remove_50pct,
    _split_sentences,
)


# ============================================================================
# SensitivityResult dataclass
# ============================================================================

def test_sensitivity_result_has_all_required_fields():
    """SensitivityResult must have all required fields."""
    field_names = {f.name for f in dataclass_fields(SensitivityResult)}
    required = {
        "metric_id", "metric_name", "perturbation_type", "perturbation_name",
        "baseline_value", "perturbed_value", "absolute_change",
        "relative_change", "sensitivity_class",
    }
    missing = required - field_names
    assert not missing, f"SensitivityResult missing fields: {missing}"


def test_sensitivity_result_to_dict():
    r = SensitivityResult(
        metric_id="M-005", metric_name="test", perturbation_type="INPUT",
        perturbation_name="test_perturb", baseline_value=0.85,
        perturbed_value=0.80, absolute_change=-0.05, relative_change=-0.0588,
        sensitivity_class="SENSITIVE",
    )
    d = r.to_dict()
    assert d["metric_id"] == "M-005"
    assert d["sensitivity_class"] == "SENSITIVE"
    assert d["absolute_change"] == -0.05


# ============================================================================
# classify_sensitivity
# ============================================================================

def test_classify_robust():
    """|relative_change| < 0.05 → ROBUST."""
    assert classify_sensitivity(0.0) == "ROBUST"
    assert classify_sensitivity(0.04) == "ROBUST"
    assert classify_sensitivity(-0.049) == "ROBUST"


def test_classify_sensitive():
    """0.05 <= |relative_change| < 0.15 → SENSITIVE."""
    assert classify_sensitivity(0.05) == "SENSITIVE"
    assert classify_sensitivity(0.10) == "SENSITIVE"
    assert classify_sensitivity(-0.14) == "SENSITIVE"


def test_classify_fragile():
    """|relative_change| >= 0.15 → FRAGILE."""
    assert classify_sensitivity(0.15) == "FRAGILE"
    assert classify_sensitivity(0.33) == "FRAGILE"
    assert classify_sensitivity(-0.75) == "FRAGILE"


def test_classify_zero():
    """Zero change → ROBUST."""
    assert classify_sensitivity(0.0) == "ROBUST"


# ============================================================================
# Perturbation functions
# ============================================================================

def test_split_sentences_basic():
    sents = _split_sentences("Hello world. This is a test. Done!")
    assert len(sents) == 3


def test_split_sentences_single():
    sents = _split_sentences("Only one sentence.")
    assert len(sents) == 1


def test_perturb_input_drop_sentence_reduces_length():
    """Dropping a sentence should reduce snippet length (if >1 sentence)."""
    gold = [{
        "bridge": "test",
        "source_snippet_a": "First sentence. Second sentence. Third sentence.",
        "source_snippet_b": "Fourth sentence. Fifth sentence.",
    }]
    perturbed = perturb_input_drop_sentence(gold)
    assert len(perturbed[0]["source_snippet_a"]) < len(gold[0]["source_snippet_a"])
    assert len(perturbed[0]["source_snippet_b"]) < len(gold[0]["source_snippet_b"])


def test_perturb_input_truncate_75pct():
    gold = [{
        "bridge": "test",
        "source_snippet_a": "A" * 100,
        "source_snippet_b": "B" * 100,
    }]
    perturbed = perturb_input_truncate_75pct(gold)
    assert len(perturbed[0]["source_snippet_a"]) == 75
    assert len(perturbed[0]["source_snippet_b"]) == 75


def test_perturb_gold_drop_1():
    gold = [{"bridge": f"b{i}"} for i in range(5)]
    perturbed = perturb_gold_drop_1(gold)
    assert len(perturbed) == 4
    assert perturbed[0]["bridge"] == "b1"


def test_perturb_gold_drop_2():
    gold = [{"bridge": f"b{i}"} for i in range(5)]
    perturbed = perturb_gold_drop_2(gold)
    assert len(perturbed) == 3
    assert perturbed[0]["bridge"] == "b2"


def test_perturb_gold_rename():
    gold = [{"bridge": "biomineralization"}]
    perturbed = perturb_gold_rename(gold)
    assert perturbed[0]["bridge"] == "biomineralization_variant"


def test_perturb_synonym_remove_1():
    synmap = {"a": {"x"}, "b": {"y"}, "c": {"z"}}
    perturbed = perturb_synonym_remove_1(synmap)
    assert len(perturbed) == 2


def test_perturb_synonym_remove_25pct():
    synmap = {f"k{i}": {f"s{i}"} for i in range(8)}
    perturbed = perturb_synonym_remove_25pct(synmap, seed=42)
    assert len(perturbed) == 6  # 8 - 2 (25% of 8)


def test_perturb_synonym_remove_50pct():
    synmap = {f"k{i}": {f"s{i}"} for i in range(8)}
    perturbed = perturb_synonym_remove_50pct(synmap, seed=42)
    assert len(perturbed) == 4  # 8 - 4 (50% of 8)


def test_perturb_synonym_empty_map():
    """Empty synonym map should return empty (not crash)."""
    perturbed = perturb_synonym_remove_1({})
    assert len(perturbed) == 0


# ============================================================================
# End-to-end: reports exist with correct structure
# ============================================================================

def test_sensitivity_m6_json_exists():
    """reports/sensitivity_m6.json must exist after running Stage M6."""
    path = REPO / "reports" / "sensitivity_m6.json"
    assert path.exists(), (
        "reports/sensitivity_m6.json missing. "
        "Run: python3 -m programs.A_metrology.sensitivity_m6"
    )


def test_sensitivity_m6_md_exists():
    path = REPO / "reports" / "sensitivity_m6.md"
    assert path.exists()


def test_sensitivity_json_has_required_structure():
    """JSON must have cycle, stage, results, gate_verdict."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    assert data["stage"] == "M6"
    assert data["program"] == "A"
    assert "n_perturbations" in data
    assert "results" in data
    assert "gate_verdict" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 20  # at least 20 perturbations


def test_every_result_has_required_fields():
    """Each result must have metric_id, baseline, perturbed, change, class."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    required = {
        "metric_id", "perturbation_type", "perturbation_name",
        "baseline_value", "perturbed_value", "absolute_change",
        "relative_change", "sensitivity_class",
    }
    for r in data["results"]:
        assert required.issubset(r.keys()), (
            f"Result missing: {required - set(r.keys())}"
        )


def test_all_4_metrics_tested():
    """M6 must test M-005, M-008, M-010, M-013."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    metric_ids = {r["metric_id"] for r in data["results"]}
    required = {"M-005", "M-008", "M-010", "M-013"}
    missing = required - metric_ids
    assert not missing, f"Missing metrics: {missing}"


def test_all_3_perturbation_types_tested():
    """M6 must test INPUT, GOLD, and SYNONYM perturbation types."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    ptypes = {r["perturbation_type"] for r in data["results"]}
    required = {"INPUT", "GOLD", "SYNONYM"}
    missing = required - ptypes
    assert not missing, f"Missing perturbation types: {missing}"


def test_m008_is_most_robust():
    """M-008 (FP floor) should have 0 FRAGILE perturbations — it's
    the most robust metric because it measures a property of the
    matcher (FP rate) that is insensitive to input perturbation."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    m008_results = [r for r in data["results"] if r["metric_id"] == "M-008"]
    fragile_count = sum(1 for r in m008_results if r["sensitivity_class"] == "FRAGILE")
    assert fragile_count == 0, (
        f"M-008 should have 0 FRAGILE, got {fragile_count}"
    )


def test_fragile_perturbations_exist():
    """M6 should find at least 1 FRAGILE perturbation (truncate_75pct
    on M-005/M-013 is expected to be fragile)."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    fragile = [r for r in data["results"] if r["sensitivity_class"] == "FRAGILE"]
    assert len(fragile) >= 1, (
        "Expected at least 1 FRAGILE perturbation (truncate is devastating)"
    )


def test_truncate_75pct_is_fragile():
    """INPUT/truncate_75pct should be FRAGILE for M-005 and M-013
    (truncating snippets to 75% removes entities and drops F1)."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    truncate_results = [r for r in data["results"]
                        if r["perturbation_name"] == "truncate_75pct"]
    for r in truncate_results:
        assert r["sensitivity_class"] == "FRAGILE", (
            f"{r['metric_id']}/truncate_75pct should be FRAGILE, "
            f"got {r['sensitivity_class']} (rel Δ={r['relative_change']})"
        )


def test_gold_drop_is_robust_for_high_baseline_metrics():
    """GOLD/drop_1_gold and drop_2_gold should be ROBUST for M-005 and
    M-013 (which have high baselines ~0.85, so dropping 1-2 of 20 gold
    bridges causes < 5% relative change).

    M-010 (baseline 0.20) is SENSITIVE to gold drop, not ROBUST — this
    is expected because the low baseline means a small absolute change
    is a large relative change."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    drop_results = [r for r in data["results"]
                    if r["perturbation_name"] in ("drop_1_gold", "drop_2_gold")
                    and r["metric_id"] in ("M-005", "M-013")]
    for r in drop_results:
        assert r["sensitivity_class"] == "ROBUST", (
            f"{r['metric_id']}/{r['perturbation_name']} should be ROBUST, "
            f"got {r['sensitivity_class']} (rel Δ={r['relative_change']})"
        )


def test_gate_verdict_documented():
    """Gate M6 verdict must be documented (PASS, PARTIAL, or FAIL)."""
    path = REPO / "reports" / "sensitivity_m6.json"
    data = json.loads(path.read_text())
    assert data["gate_verdict"] in ("PASS", "PARTIAL", "FAIL")
