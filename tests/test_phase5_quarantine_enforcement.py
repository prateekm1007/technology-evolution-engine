"""Tests: Phase 5 forbidden metrics quarantine enforcement.

Per the 18-phase plan:
    "Phase 5: Quarantine forbidden metrics"

These tests verify:
1. ALL metrics are forbidden for scientific use until independently regenerated
2. M-008 is fully quarantined
3. The 37 other metrics are provisionally quarantined
4. 0 metrics are scientifically eligible
5. The historical compliance report is marked STALE (not modified or deleted)
6. No metric value has been deleted, replaced, or averaged
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]
QUARANTINE_PATH = REPO / "reports" / "phase5" / "forbidden_metrics_quarantine.json"


def test_quarantine_manifest_exists():
    assert QUARANTINE_PATH.exists(), "Phase 5 quarantine manifest must exist"


def test_all_metrics_forbidden_for_scientific_use():
    """ALL metrics must be forbidden for scientific use until independently
    regenerated. No metric is scientifically eligible."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    for m in q.get("forbidden_metrics", []):
        mid = m.get("metric_id", "?")
        assert m["forbidden_for_scientific_use"] is True, (
            f"Metric {mid} must be forbidden for scientific use. No metric "
            f"is scientifically eligible until independently regenerated."
        )


def test_m008_fully_quarantined():
    """M-008 must be fully quarantined (regeneration failed)."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    m008 = None
    for m in q.get("forbidden_metrics", []):
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None, "M-008 must be in the quarantine manifest"
    assert m008["quarantine_severity"] == "FULL"
    assert "REGENERATION_FAILED" in m008["forbidden_reasons"]
    assert "QUARANTINED" in m008["forbidden_reasons"]


def test_37_metrics_provisionally_quarantined():
    """37 metrics must be provisionally quarantined (not independently verified)."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    provisional = [m for m in q.get("forbidden_metrics", [])
                   if m["quarantine_severity"] == "PROVISIONAL"]
    assert len(provisional) == 37, (
        f"Expected 37 provisionally quarantined metrics, got {len(provisional)}"
    )

    for m in provisional:
        assert "NOT_INDEPENDENTLY_REGENERATED" in m["forbidden_reasons"]
        assert "NOT_SCIENTIFICALLY_ELIGIBLE" in m["forbidden_reasons"]


def test_zero_scientifically_eligible():
    """No metric may be scientifically eligible."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    assert q["summary"]["scientifically_eligible"] == 0


def test_historical_compliance_report_marked_stale():
    """The historical compliance report must be marked STALE (not modified or deleted).

    Per MC-6: no metric may be silently altered. The historical report is
    preserved as-is but marked stale because it does not reflect the current
    epistemic state (M-008 is now quarantined).
    """
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    status = q.get("compliance_report_status", {})
    assert "STALE" in status.get("current_status", ""), (
        "Historical compliance report must be marked STALE"
    )
    assert status.get("historical_report") == "reports/measurement_constitution_m8.json"

    # Verify the historical report still exists (not deleted)
    historical = REPO / "reports" / "measurement_constitution_m8.json"
    assert historical.exists(), "Historical compliance report must not be deleted"


def test_no_value_modification():
    """No metric value has been deleted, replaced, or averaged."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    assert q["no_retroactive_repair"] is True
    assert q["no_value_deletion"] is True
    assert q["no_value_replacement"] is True
    assert q["no_value_averaging"] is True


def test_critical_path_metrics_all_forbidden():
    """All 10 critical-path metrics must be forbidden for scientific use."""
    assert QUARANTINE_PATH.exists()
    q = json.loads(QUARANTINE_PATH.read_text())

    critical = [m for m in q.get("forbidden_metrics", [])
                if m.get("critical_path_for_matcher_discrimination")]
    assert len(critical) == 10, (
        f"Expected 10 critical-path metrics, got {len(critical)}"
    )

    for m in critical:
        assert m["forbidden_for_scientific_use"] is True, (
            f"Critical-path metric {m['metric_id']} must be forbidden "
            f"for scientific use"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
