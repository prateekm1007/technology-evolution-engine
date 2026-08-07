"""Tests for DR-94: Proposal Calibration Study."""
import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr94_imports():
    from audit.measurement_integrity.dr94_calibration_study import (
        CalibrationMetrics, compute_calibration, build_calibration_table,
    )
    assert compute_calibration is not None


def test_compute_calibration_perfect():
    """Perfect calibration: internal == external → bias=0, MCE=0."""
    from audit.measurement_integrity.dr94_calibration_study import compute_calibration
    m = compute_calibration([3, 3, 3], [3, 3, 3])
    assert m.bias == 0.0
    assert m.mean_calibration_error == 0.0
    assert m.agreement_rate == 1.0


def test_compute_calibration_overestimate():
    """Internal always higher → positive bias."""
    from audit.measurement_integrity.dr94_calibration_study import compute_calibration
    m = compute_calibration([5, 5, 5], [2, 2, 2])
    assert m.bias == 3.0
    assert m.overestimate_rate == 1.0
    assert m.underestimate_rate == 0.0


def test_compute_calibration_underestimate():
    """External always higher → negative bias."""
    from audit.measurement_integrity.dr94_calibration_study import compute_calibration
    m = compute_calibration([2, 2, 2], [5, 5, 5])
    assert m.bias == -3.0
    assert m.underestimate_rate == 1.0


def test_gen0_bias_positive():
    """HONEST TEST: Gen0 internal evaluator overestimates (bias > 0).

    The calibration study found bias = +2.50. The internal heuristic
    rates proposals 4.5/5; the external LLM rates them 2.0/5.
    100% overestimate rate. This is the self-validation bias.
    """
    # Find repo root
    p = Path(__file__).resolve()
    repo = None
    for parent in p.parents:
        if (parent / "FAILURES.md").exists():
            repo = parent
            break
    if not repo:
        assert False, "Could not find repo root"

    calib_path = repo / "reports" / "calibration_study.json"
    if calib_path.exists():
        with open(calib_path) as f:
            data = json.load(f)
        metrics = data.get("metrics")
        if metrics:
            assert metrics["bias"] > 0, \
                f"Bias should be positive (internal overestimates). Got: {metrics['bias']}"
            assert metrics["overestimate_rate"] > 0.5, \
                f"Overestimate rate should be >50%. Got: {metrics['overestimate_rate']}"


def test_gen0_report_exists():
    """PROPOSAL_CALIBRATION_REPORT.md exists as permanent artifact."""
    # Find repo root by looking for FAILURES.md
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "FAILURES.md").exists():
            report = parent / "PROPOSAL_CALIBRATION_REPORT.md"
            assert report.exists(), f"PROPOSAL_CALIBRATION_REPORT.md must exist at {report}"
            return
    assert False, "Could not find repo root"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
