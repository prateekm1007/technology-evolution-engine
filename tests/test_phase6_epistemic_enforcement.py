"""Tests: Phase 6 epistemic state enforcement (mechanical, not documentary).

Per audit round 11:
    "Phase 6 must enforce epistemic states mechanically, not merely
     create another report saying that the states exist."

These tests verify that the epistemic_state_enforcer actually BLOCKS
forbidden metrics from scientific use. This is not a report test —
it is an execution test that verifies the enforcement code raises.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.epistemic_state_enforcer import (
    MetricNotEligible,
    MetricNotFound,
    get_metric_epistemic_state,
    assert_metric_eligible_for_scientific_use,
    assert_metric_not_quarantined,
    list_eligible_metrics,
    list_quarantined_metrics,
    list_provisionally_quarantined_metrics,
)


# ===== M-008 is fully quarantined =====

def test_m008_blocked_for_scientific_use():
    """M-008 must be BLOCKED for scientific use. The enforcer must raise."""
    with pytest.raises(MetricNotEligible, match="FULLY QUARANTINED"):
        assert_metric_eligible_for_scientific_use("M-008")


def test_m008_blocked_even_for_non_scientific_use():
    """M-008 must be BLOCKED even for non-scientific use (weaker check)."""
    with pytest.raises(MetricNotEligible, match="FULLY QUARANTINED"):
        assert_metric_not_quarantined("M-008")


def test_m008_epistemic_state():
    """M-008's epistemic state must be QUARANTINED with FAILED regeneration."""
    state = get_metric_epistemic_state("M-008")
    assert state["scientifically_eligible"] is False
    assert state["measurement_usability"] == "QUARANTINED"
    assert state["regeneration_status"] == "FAILED"
    assert state["quarantine_severity"] == "FULL"
    assert "REGENERATION_FAILED" in state["forbidden_reasons"]


# ===== All 37 other metrics are provisionally quarantined =====

def test_m005_blocked_for_scientific_use():
    """M-005 (and all other provisional metrics) must be BLOCKED for scientific use."""
    with pytest.raises(MetricNotEligible, match="PROVISIONALLY QUARANTINED"):
        assert_metric_eligible_for_scientific_use("M-005")


def test_m005_allowed_for_non_scientific_use():
    """M-005 should pass the weaker check (not fully quarantined)."""
    # Should NOT raise — M-005 is provisional, not full quarantine
    assert_metric_not_quarantined("M-005")


def test_all_critical_path_metrics_blocked_for_scientific_use():
    """All 10 critical-path metrics must be blocked for scientific use."""
    critical_path = ["M-004", "M-005", "M-006", "M-007", "M-008",
                     "M-010", "M-011", "M-012", "M-013", "M-015"]
    for mid in critical_path:
        with pytest.raises(MetricNotEligible):
            assert_metric_eligible_for_scientific_use(mid)


# ===== No metric is eligible =====

def test_zero_eligible_metrics():
    """No metric may be SCIENTIFICALLY_ELIGIBLE."""
    eligible = list_eligible_metrics()
    assert len(eligible) == 0, (
        f"Expected 0 eligible metrics, got {len(eligible)}: {eligible}. "
        f"No metric is scientifically eligible until independently regenerated."
    )


def test_one_quarantined_metric():
    """Exactly 1 metric (M-008) must be fully quarantined."""
    quarantined = list_quarantined_metrics()
    assert len(quarantined) == 1
    assert quarantined[0] == "M-008"


def test_37_provisionally_quarantined():
    """Exactly 37 metrics must be provisionally quarantined."""
    provisional = list_provisionally_quarantined_metrics()
    assert len(provisional) == 37


# ===== Unknown metrics are blocked =====

def test_unknown_metric_blocked():
    """An unknown metric ID must raise MetricNotEligible."""
    with pytest.raises(MetricNotEligible, match="not in the inventory"):
        assert_metric_eligible_for_scientific_use("M-999")


def test_unknown_metric_raises_not_found():
    """get_metric_epistemic_state for unknown metric raises MetricNotFound."""
    with pytest.raises(MetricNotFound):
        get_metric_epistemic_state("M-999")


# ===== Enforcement is mechanical, not documentary =====

def test_enforcement_raises_exception_not_returns_false():
    """The enforcer must RAISE an exception, not return False.

    This is the key mechanical enforcement: the code path cannot
    continue past the assertion. It's not a check that returns a
    boolean — it's a hard gate that blocks execution.
    """
    # This must raise, not return
    with pytest.raises(MetricNotEligible):
        assert_metric_eligible_for_scientific_use("M-008")

    # Verify the function returns None (not False) when it passes
    # (which it never does currently since no metric is eligible)


def test_enforcement_cannot_be_bypassed_by_ignoring_return_value():
    """The enforcer raises, so ignoring the return value doesn't help.

    A caller cannot do:
        assert_metric_eligible_for_scientific_use("M-008")  # raises
        # use M-008 anyway  # never reached

    The raise prevents the code from continuing.
    """
    # Simulate a scientific code path that tries to use M-008
    def scientific_operation_using_m008():
        assert_metric_eligible_for_scientific_use("M-008")
        return "M-008 value used in scientific decision"

    # The operation must fail before returning
    with pytest.raises(MetricNotEligible):
        result = scientific_operation_using_m008()
        # This line should never be reached
        assert result != "M-008 value used in scientific decision"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
