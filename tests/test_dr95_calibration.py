"""Tests for DR-95: Epistemic Calibration Research."""
import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr95_imports():
    from audit.measurement_integrity.dr95_epistemic_calibration import (
        llm_evaluate, multi_evaluator_calibration,
        compute_confidence_calibration, disagreement_analysis,
        ConfidenceCalibration,
    )
    assert compute_confidence_calibration is not None


def test_confidence_calibration_perfect():
    """Perfect calibration: confidence == acceptance rate."""
    from audit.measurement_integrity.dr95_epistemic_calibration import compute_confidence_calibration
    # confidence = 1.0 for accepted, 0.0 for rejected → perfect
    c = compute_confidence_calibration([1.0, 1.0, 0.0, 0.0], [True, True, False, False])
    assert c.ece == 0.0
    assert c.brier_score == 0.0


def test_confidence_calibration_poor():
    """Poor calibration: high confidence but low acceptance."""
    from audit.measurement_integrity.dr95_epistemic_calibration import compute_confidence_calibration
    # confidence = 0.9 but never accepted → poorly calibrated
    c = compute_confidence_calibration([0.9, 0.9, 0.9], [False, False, False])
    assert c.ece > 0.5
    assert c.brier_score > 0.5


def test_disagreement_analysis_categorizes():
    """Disagreement analysis categorizes rejection reasons."""
    from audit.measurement_integrity.dr95_epistemic_calibration import disagreement_analysis
    multi_results = [
        {
            "evaluations": {
                "judge_1": {"rejection_reason": "mechanism is too vague"},
                "judge_2": {"rejection_reason": "low confidence score"},
            }
        }
    ]
    result = disagreement_analysis(multi_results)
    assert "failure_modes" in result
    assert result["failure_modes"]["mechanism_vague"] >= 1
    assert result["failure_modes"]["low_confidence"] >= 1


def test_gen0_confidence_poorly_calibrated():
    """HONEST TEST: Gen0 confidence is poorly calibrated (ECE > 0.2).

    The calibration study found ECE = 0.433. The composer's confidence
    (0.2) does NOT predict acceptance (50% acceptance rate).
    This is a measurable calibration problem.
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

    calib_path = repo / "reports" / "dr95_calibration_research.json"
    if calib_path.exists():
        with open(calib_path) as f:
            data = json.load(f)
        conf_calib = data.get("confidence_calibration", {})
        if conf_calib:
            assert conf_calib["ece"] > 0.2, \
                f"ECE should be > 0.2 (poorly calibrated). Got: {conf_calib['ece']}"


def test_n6_is_exploratory():
    """STATISTICAL HONESTY: N=6 is exploratory, not conclusive.

    Per CTO: 'Correlation = 0.00 with only 6 proposals is almost
    meaningless. Instead report: N=6, Exploratory, Insufficient for
    statistical conclusions.'
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

    calib_path = repo / "reports" / "dr95_calibration_research.json"
    if calib_path.exists():
        with open(calib_path) as f:
            data = json.load(f)
        note = data.get("statistical_note", "")
        assert "exploratory" in note.lower() or "insufficient" in note.lower(), \
            f"Statistical note must mention exploratory/insufficient. Got: {note}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
