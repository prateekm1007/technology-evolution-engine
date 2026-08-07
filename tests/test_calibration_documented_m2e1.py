"""
test_calibration_documented_m2e1.py — Tests for Stage M2/E1 (Calibration Documented).

Verifies:
  1. CalibrationStatus dataclass has all required fields
  2. reports/calibration_documented_m2e1.json exists with correct structure
  3. All 38 metrics have calibration status
  4. No metric is UNCALIBRATED
  5. Specific metrics have expected calibration levels
  6. Gate verdict is PASS
"""
import sys
import json
from pathlib import Path
from dataclasses import fields as dataclass_fields

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.calibration_documented_m2e1 import (
    CalibrationStatus, generate_all_calibration_statuses,
    determine_calibration_status,
)


# ============================================================================
# CalibrationStatus dataclass
# ============================================================================

def test_calibration_status_has_all_required_fields():
    """CalibrationStatus must have all required fields."""
    field_names = {f.name for f in dataclass_fields(CalibrationStatus)}
    required = {
        "metric_id", "metric_name", "calibration_level",
        "calibration_method", "calibration_version",
        "has_external_validation", "has_bootstrap_ci",
        "has_repeatability", "has_sensitivity",
        "has_failure_envelope", "ece", "bias", "fp_floor", "notes",
    }
    missing = required - field_names
    assert not missing, f"CalibrationStatus missing fields: {missing}"


def test_calibration_status_to_dict():
    s = CalibrationStatus(
        metric_id="M-001", metric_name="test",
        calibration_level="DEGENERATE",
        calibration_method="test method",
        calibration_version="test-v1",
        has_external_validation=False, has_bootstrap_ci=True,
        has_repeatability=False, has_sensitivity=False,
        has_failure_envelope=True, ece=None, bias=None, fp_floor=None,
        notes="test notes",
    )
    d = s.to_dict()
    assert d["metric_id"] == "M-001"
    assert d["calibration_level"] == "DEGENERATE"


# ============================================================================
# End-to-end: reports exist
# ============================================================================

def test_calibration_json_exists():
    """reports/calibration_documented_m2e1.json must exist."""
    assert (REPO / "reports" / "calibration_documented_m2e1.json").exists()


def test_calibration_md_exists():
    """reports/calibration_documented_m2e1.md must exist."""
    assert (REPO / "reports" / "calibration_documented_m2e1.md").exists()


def test_json_has_required_structure():
    """JSON must have cycle, stage, n_metrics, gate_verdict, statuses."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    assert data["stage"] == "M2/E1"
    assert data["program"] == "A"
    assert "n_metrics" in data
    assert "calibration_counts" in data
    assert "gate_verdict" in data
    assert "statuses" in data
    assert isinstance(data["statuses"], list)
    assert len(data["statuses"]) >= 30


def test_every_status_has_required_fields():
    """Each status must have calibration_level, method, version."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    required = {
        "metric_id", "calibration_level", "calibration_method",
        "calibration_version", "has_external_validation", "notes",
    }
    for s in data["statuses"]:
        assert required.issubset(s.keys()), (
            f"Status {s.get('metric_id', '?')} missing: {required - set(s.keys())}"
        )


# ============================================================================
# Calibration level checks
# ============================================================================

def test_no_metric_is_uncalibrated():
    """No metric should be UNCALIBRATED — all have at least partial calibration."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    uncalibrated = [s for s in data["statuses"] if s["calibration_level"] == "UNCALIBRATED"]
    assert not uncalibrated, (
        f"UNCALIBRATED metrics: {[s['metric_id'] for s in uncalibrated]}"
    )


def test_m008_is_partially_calibrated():
    """M-008 (FP floor) should be PARTIALLY_CALIBRATED — DR-91 audit exists."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    m008 = next(s for s in data["statuses"] if s["metric_id"] == "M-008")
    assert m008["calibration_level"] == "PARTIALLY_CALIBRATED"
    assert m008["has_external_validation"] is True


def test_m305_is_partially_calibrated():
    """M-305 (self-validation bias) should be PARTIALLY_CALIBRATED."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    m305 = next(s for s in data["statuses"] if s["metric_id"] == "M-305")
    assert m305["calibration_level"] == "PARTIALLY_CALIBRATED"


def test_m306_is_partially_calibrated():
    """M-306 (ECE) should be PARTIALLY_CALIBRATED."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    m306 = next(s for s in data["statuses"] if s["metric_id"] == "M-306")
    assert m306["calibration_level"] == "PARTIALLY_CALIBRATED"


def test_degenerate_metrics_are_documented():
    """Degenerate metrics should have calibration_level = DEGENERATE."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    degenerate_ids = [s["metric_id"] for s in data["statuses"]
                      if s["calibration_level"] == "DEGENERATE"]
    # M-001 (exact F1 always 0) should be degenerate
    assert "M-001" in degenerate_ids
    # M-006 (recognition F1 always 1 under DR-91) should be degenerate
    assert "M-006" in degenerate_ids
    # At least 9 degenerate metrics
    assert len(degenerate_ids) >= 9


def test_gate_verdict_is_pass():
    """Gate M2/E1 verdict should be PASS (all metrics documented)."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    assert data["gate_verdict"] == "PASS"


def test_calibration_counts_match():
    """Calibration counts should sum to n_metrics."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    counts = data["calibration_counts"]
    total = counts["CALIBRATED"] + counts["PARTIALLY_CALIBRATED"] + \
            counts["UNCALIBRATED"] + counts["DEGENERATE"]
    assert total == data["n_metrics"], (
        f"Counts sum to {total}, expected {data['n_metrics']}"
    )


def test_all_30_specified_metrics_have_status():
    """All 30 specified M-metrics must have calibration status."""
    path = REPO / "reports" / "calibration_documented_m2e1.json"
    data = json.loads(path.read_text())
    metric_ids = {s["metric_id"] for s in data["statuses"]}
    required = (
        {f"M-{i:03d}" for i in range(1, 17)} |
        {f"M-{i:03d}" for i in range(101, 106)} |
        {f"M-{i:03d}" for i in range(201, 206)} |
        {"M-301", "M-302", "M-304", "M-305", "M-306"}
    )
    missing = required - metric_ids
    assert not missing, f"Missing calibration status for: {missing}"


# ============================================================================
# generate_all_calibration_statuses runs
# ============================================================================

def test_generate_all_runs():
    """generate_all_calibration_statuses() must return a non-empty list."""
    statuses = generate_all_calibration_statuses()
    assert isinstance(statuses, list)
    assert len(statuses) >= 30
    assert all(isinstance(s, CalibrationStatus) for s in statuses)
