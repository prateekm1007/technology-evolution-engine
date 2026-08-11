"""
test_dr101_final_verdict_eligibility.py — Tests for DR-101 Gate E
(meta-gate that harvests results from gates A-D).
"""
import sys
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from audit.measurement_integrity.dr101_final_verdict_eligibility import (
    harvest_gate_a, harvest_gate_b, harvest_gate_c, harvest_gate_d,
    decide_eligibility, write_final_verdict, write_blocked_verdict,
)


@pytest.fixture
def reports_dir():
    return REPO / "reports"


@pytest.fixture
def sample_gates_all_pass():
    """All gates SCIENCE_PASS — only this earns FINAL verdict (cycle 257)."""
    return {
        "A": {"available": True, "verdict": "PASS", "verdict_tier": "SCIENCE_PASS",
              "production_f1_strict": 0.0, "production_f1_lenient": 0.8571,
              "fp_floor_lenient": 1.0, "comparisons_lenient": []},
        "B": {"available": True, "verdict": "PASS", "verdict_tier": "SCIENCE_PASS",
              "n_claims": 7, "formula_inflation_observed": True},
        "C": {"available": True, "verdict": "PASS", "verdict_tier": "SCIENCE_PASS",
              "n_total": 40, "n_met": True,
              "distribution": {"lenient_honest": {"mean": 0.5}}},
        "D": {"available": True, "verdict": "PASS", "verdict_tier": "SCIENCE_PASS",
              "n_responses": 3, "accept_rate": 0.6, "overall_mean_score": 3.8},
    }


@pytest.fixture
def sample_gates_d_blocked():
    """Gate D BLOCKED — FINAL blocked."""
    return {
        "A": {"available": True, "verdict": "PASS",
              "verdict_tier": "INSTRUMENTATION_SCAFFOLD_PASS"},
        "B": {"available": True, "verdict": "PASS",
              "verdict_tier": "SENSITIVITY_ANALYSIS_PASS"},
        "C": {"available": True, "verdict": "PASS",
              "verdict_tier": "WEAK_STATISTICAL_PASS"},
        "D": {"available": True, "verdict": "BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW",
              "verdict_tier": "BLOCKED_ON_HUMAN_OR_AI_SURROGATE_REVIEW",
              "blocked_reason": "Awaiting review responses"},
    }


@pytest.fixture
def sample_gates_current_cycle_257():
    """Cycle 257 actual state: A,B,C instrumentation-only, D AI surrogate FAIL."""
    return {
        "A": {"available": True, "verdict": "PASS",
              "verdict_tier": "INSTRUMENTATION_SCAFFOLD_PASS"},
        "B": {"available": True, "verdict": "PASS",
              "verdict_tier": "SENSITIVITY_ANALYSIS_PASS"},
        "C": {"available": True, "verdict": "PASS",
              "verdict_tier": "WEAK_STATISTICAL_PASS"},
        "D": {"available": True, "verdict": "FAIL",
              "verdict_tier": "AI_SURROGATE_REVIEW_FAIL",
              "accept_rate": 0.0, "overall_mean_score": 2.2381,
              "reviewer_type": "AI_PRE_REVIEW"},
    }


# ============================================================================
# HARVESTERS
# ============================================================================

def test_harvest_gate_a_reads_json(reports_dir):
    result = harvest_gate_a(reports_dir)
    assert result["available"] is True
    assert "verdict" in result
    assert "production_f1_strict" in result
    assert "production_f1_lenient" in result


def test_harvest_gate_a_handles_missing_file(tmp_path):
    result = harvest_gate_a(tmp_path)
    assert result["available"] is False
    assert result["verdict"] == "NOT_RUN"


def test_harvest_gate_b_reads_json(reports_dir):
    result = harvest_gate_b(reports_dir)
    assert result["available"] is True
    assert "verdict" in result
    assert "n_claims" in result


def test_harvest_gate_c_reads_json(reports_dir):
    result = harvest_gate_c(reports_dir)
    assert result["available"] is True
    assert "verdict" in result
    assert "n_total" in result


def test_harvest_gate_d_reads_status_when_no_aggregated(reports_dir):
    """Gate D should return BLOCKED_ON_HUMAN when scaffolding exists
    but no aggregated responses have been collected yet."""
    result = harvest_gate_d(reports_dir)
    assert result["available"] is True
    # Either BLOCKED_ON_HUMAN (scaffolding only) or PASS/PARTIAL/FAIL (aggregated)
    assert result["verdict"] in ("BLOCKED_ON_HUMAN", "PASS", "PARTIAL", "FAIL")


# ============================================================================
# ELIGIBILITY DECISION
# ============================================================================

def test_decide_eligibility_all_pass(sample_gates_all_pass):
    result = decide_eligibility(sample_gates_all_pass)
    assert result["eligible"] is True
    assert result["blocking_gates"] == []
    assert result["n_gates_science_pass"] == 4
    assert result["n_gates_total"] == 4


def test_decide_eligibility_d_blocked(sample_gates_d_blocked):
    """Cycle 257: ALL gates block (A,B,C are instrumentation-only, D is BLOCKED)."""
    result = decide_eligibility(sample_gates_d_blocked)
    assert result["eligible"] is False
    # All 4 gates block under cycle 257 tightening
    assert "A" in result["blocking_gates"]
    assert "B" in result["blocking_gates"]
    assert "C" in result["blocking_gates"]
    assert "D" in result["blocking_gates"]
    assert result["n_gates_science_pass"] == 0


def test_decide_eligibility_cycle_257_current_state(sample_gates_current_cycle_257):
    """Cycle 257 actual state: all 4 gates block."""
    result = decide_eligibility(sample_gates_current_cycle_257)
    assert result["eligible"] is False
    assert result["n_gates_science_pass"] == 0
    assert set(result["blocking_gates"]) == {"A", "B", "C", "D"}


def test_decide_eligibility_instrumentation_scaffold_pass_blocks():
    """A gate with verdict_tier=INSTRUMENTATION_SCAFFOLD_PASS must BLOCK
    eligibility (cycle 257 tightening). It's not SCIENCE_PASS."""
    gates = {
        "A": {"verdict": "PASS", "verdict_tier": "INSTRUMENTATION_SCAFFOLD_PASS"},
        "B": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "C": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "D": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
    }
    result = decide_eligibility(gates)
    assert result["eligible"] is False
    assert "A" in result["blocking_gates"]


def test_decide_eligibility_partial_blocks():
    gates = {
        "A": {"verdict": "PARTIAL", "verdict_tier": "PARTIAL"},
        "B": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "C": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "D": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
    }
    result = decide_eligibility(gates)
    assert result["eligible"] is False
    assert "A" in result["blocking_gates"]


def test_decide_eligibility_fail_blocks():
    gates = {
        "A": {"verdict": "FAIL", "verdict_tier": "FAIL"},
        "B": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "C": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "D": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
    }
    result = decide_eligibility(gates)
    assert result["eligible"] is False
    assert "A" in result["blocking_gates"]


def test_decide_eligibility_not_run_blocks():
    gates = {
        "A": {"verdict": "NOT_RUN", "verdict_tier": "NOT_RUN", "error": "file missing"},
        "B": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "C": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "D": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
    }
    result = decide_eligibility(gates)
    assert result["eligible"] is False
    assert "A" in result["blocking_gates"]


def test_decide_eligibility_ai_surrogate_fail_blocks():
    """Gate D with AI_SURROGATE_REVIEW_FAIL verdict_tier blocks eligibility."""
    gates = {
        "A": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "B": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "C": {"verdict": "PASS", "verdict_tier": "SCIENCE_PASS"},
        "D": {"verdict": "FAIL", "verdict_tier": "AI_SURROGATE_REVIEW_FAIL",
              "accept_rate": 0.0, "overall_mean_score": 2.0},
    }
    result = decide_eligibility(gates)
    assert result["eligible"] is False
    assert "D" in result["blocking_gates"]


# ============================================================================
# VERDICT WRITERS
# ============================================================================

def test_write_blocked_verdict_creates_file(tmp_path, sample_gates_d_blocked):
    eligibility = decide_eligibility(sample_gates_d_blocked)
    blocked_path = write_blocked_verdict(tmp_path, sample_gates_d_blocked, eligibility)
    assert blocked_path.exists()
    content = blocked_path.read_text()
    assert "FINAL VERDICT BLOCKED" in content
    assert "NOT TRUSTWORTHY" in content
    assert "D" in content  # blocking gate mentioned


def test_write_final_verdict_creates_file(tmp_path, sample_gates_all_pass):
    eligibility = decide_eligibility(sample_gates_all_pass)
    verdict_path = write_final_verdict(tmp_path, sample_gates_all_pass, eligibility)
    assert verdict_path.exists()
    content = verdict_path.read_text()
    assert "FINAL MEASUREMENT VERDICT" in content
    assert "TRUSTWORTHY" in content
    assert "PASS" in content
    # Should mention all 4 gates
    for gate_letter in ("A", "B", "C", "D"):
        assert f"Gate {gate_letter}" in content or f"| {gate_letter} |" in content


def test_write_final_verdict_documents_formula_inflation(tmp_path, sample_gates_all_pass):
    eligibility = decide_eligibility(sample_gates_all_pass)
    verdict_path = write_final_verdict(tmp_path, sample_gates_all_pass, eligibility)
    content = verdict_path.read_text()
    # sample_gates_all_pass has formula_inflation_observed=True for gate B
    assert "formula inflation" in content.lower() or "DR-91 F1 formula" in content


# ============================================================================
# END-TO-END
# ============================================================================

def test_main_runs_and_writes_reports():
    from audit.measurement_integrity.dr101_final_verdict_eligibility import main
    rc = main()
    # Currently Gate D is BLOCKED_ON_HUMAN → not eligible → rc=2
    assert rc in [0, 2]
    reports_dir = REPO / "reports"
    assert (reports_dir / "final_verdict_eligibility.json").exists()
    assert (reports_dir / "final_verdict_eligibility.md").exists()


def test_main_writes_correct_verdict_file():
    """Either FINAL_MEASUREMENT_VERDICT.md (if eligible) or
    FINAL_VERDICT_BLOCKED.md (if not). Exactly one should exist after main()."""
    from audit.measurement_integrity.dr101_final_verdict_eligibility import main
    main()
    final_path = REPO / "FINAL_MEASUREMENT_VERDICT.md"
    blocked_path = REPO / "FINAL_VERDICT_BLOCKED.md"
    # Exactly one should exist
    assert final_path.exists() ^ blocked_path.exists()


def test_main_currently_blocks_all_gates_cycle_257():
    """Cycle 257: 0/4 gates have SCIENCE_PASS. The verdict should be BLOCKED.
    All four gates (A, B, C, D) block eligibility under the tightened vocabulary."""
    from audit.measurement_integrity.dr101_final_verdict_eligibility import main
    rc = main()
    # Should be 2 (blocked) because no gate has SCIENCE_PASS
    assert rc == 2
    blocked_path = REPO / "FINAL_VERDICT_BLOCKED.md"
    assert blocked_path.exists()
    final_path = REPO / "FINAL_MEASUREMENT_VERDICT.md"
    assert not final_path.exists()
