"""
Tests for F-046 experimentation scoping.

Per F-046 (FAILURES.md): the experimentation layer has never executed
a single predict→build→observe→learn cycle. This test file verifies
the SCOPING module (experimentation_layer/scoping.py) which defines
what a closed loop looks like per PR-23.

Per PR-23 (Closed-loop learning requirement): a learning claim requires
a closed loop with 5 specific steps:
  1. prediction (T1)
  2. observation (T2 > T1)
  3. root-cause identification
  4. module revision (with commit hash)
  5. second prediction (T3 > T2) measurably closer to observation

The scoping module provides ExperimentSpec, ClosedLoopTracker, and
EXPERIMENT_CANDIDATES. These tests verify the scoping is real code
(not just docstrings) and that the closed-loop validation correctly
enforces all 5 PR-23 criteria.

NOTE: F-046 is PARTIALLY RESOLVED by this scoping work. The actual
execution (build + observe) requires reality cooperation per PR-26
and cannot be closed by code work alone.
"""
import sys
import pathlib
from datetime import datetime, timezone, timedelta

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experimentation_layer.scoping import (
    ExperimentSpec,
    ClosedLoopTracker,
    EXPERIMENT_CANDIDATES,
    PH_PREDICTION_EXPERIMENT,
    ELECTROLYTE_EXPERIMENT,
    validate_closed_loop,
    list_experiment_candidates,
    get_experiment_spec,
)


# ----------------------------------------------------------------------
# 1. ExperimentSpec: structure and validation
# ----------------------------------------------------------------------

def test_experiment_spec_dataclass_exists():
    """F-046: ExperimentSpec is a real dataclass (not just a docstring)."""
    assert ExperimentSpec is not None
    # Can instantiate
    spec = ExperimentSpec(
        experiment_id="test",
        name="test",
        domain="test",
        problem_statement="test",
    )
    assert spec.experiment_id == "test"


def test_experiment_spec_validate_returns_empty_for_complete_spec():
    """A complete ExperimentSpec (all 5 steps defined) validates cleanly."""
    errors = PH_PREDICTION_EXPERIMENT.validate()
    assert errors == [], f"PH_PREDICTION_EXPERIMENT validation errors: {errors}"


def test_experiment_spec_validate_catches_missing_steps():
    """An incomplete ExperimentSpec (missing steps) returns validation errors."""
    incomplete = ExperimentSpec(
        experiment_id="incomplete",
        name="incomplete",
        domain="test",
        problem_statement="test",
        # prediction, build, observe, learn, revise all default to empty dicts
    )
    errors = incomplete.validate()
    assert len(errors) == 5, f"Expected 5 validation errors, got {len(errors)}: {errors}"
    assert any("prediction missing" in e for e in errors)
    assert any("build missing" in e for e in errors)
    assert any("observe missing" in e for e in errors)
    assert any("learn missing" in e for e in errors)
    assert any("revise missing" in e for e in errors)


def test_experiment_spec_to_dict_roundtrips():
    """ExperimentSpec.to_dict() produces a serializable dict."""
    d = PH_PREDICTION_EXPERIMENT.to_dict()
    assert d["experiment_id"] == "EXP-001-ph-prediction"
    assert "prediction" in d
    assert "build" in d
    assert "observe" in d
    assert "learn" in d
    assert "revise" in d


# ----------------------------------------------------------------------
# 2. Pre-scoped experiment candidates exist
# ----------------------------------------------------------------------

def test_experiment_candidates_registry_has_at_least_2_experiments():
    """F-046: at least 2 pre-scoped experiment candidates exist
    (from milestone_001 pH prediction + milestone_002 electrolyte)."""
    candidates = list_experiment_candidates()
    assert len(candidates) >= 2, f"Expected >=2 candidates, got {candidates}"


def test_ph_prediction_experiment_exists():
    """The pH prediction experiment (EXP-001) exists with all 5 steps."""
    assert "EXP-001-ph-prediction" in EXPERIMENT_CANDIDATES
    spec = get_experiment_spec("EXP-001-ph-prediction")
    assert spec.domain == "chemistry"
    assert spec.class_label == "A"  # infrastructure milestone
    errors = spec.validate()
    assert errors == [], f"PH_PREDICTION validation errors: {errors}"


def test_electrolyte_experiment_exists():
    """The electrolyte improvement experiment (EXP-002) exists."""
    assert "EXP-002-electrolyte-improvement" in EXPERIMENT_CANDIDATES
    spec = get_experiment_spec("EXP-002-electrolyte-improvement")
    assert spec.domain == "electrochemistry"
    assert spec.class_label == "B"  # invention milestone
    errors = spec.validate()
    assert errors == [], f"ELECTROLYTE validation errors: {errors}"


def test_ph_prediction_has_falsifier():
    """Per PR-23: every prediction must have a falsifier (a condition
    that, if true, falsifies the prediction)."""
    spec = PH_PREDICTION_EXPERIMENT
    assert "falsifier" in spec.prediction
    assert len(spec.prediction["falsifier"]) > 10


def test_ph_prediction_has_collaborator_requirements():
    """Per PR-26: the build step must specify collaborator requirements
    (since execution requires reality cooperation)."""
    spec = PH_PREDICTION_EXPERIMENT
    assert "collaborator_requirements" in spec.build
    assert len(spec.build["collaborator_requirements"]) > 20


def test_ph_prediction_has_pass_and_fail_criteria():
    """The observe step must have both pass_criteria and fail_criteria."""
    spec = PH_PREDICTION_EXPERIMENT
    assert "pass_criteria" in spec.observe
    assert "fail_criteria" in spec.observe
    assert len(spec.observe["pass_criteria"]) > 10
    assert len(spec.observe["fail_criteria"]) > 10


# ----------------------------------------------------------------------
# 3. ClosedLoopTracker: 5-step tracking
# ----------------------------------------------------------------------

def test_closed_loop_tracker_initial_state():
    """A fresh ClosedLoopTracker has no steps recorded and is not closed."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    assert not tracker.is_closed_loop()
    assert tracker.step_1_prediction_timestamp is None
    assert tracker.step_2_observation_timestamp is None
    assert tracker.step_3_root_cause_identified is False
    assert tracker.step_4_module_revised is False
    assert tracker.step_5_second_prediction_timestamp is None


def test_closed_loop_tracker_enforces_step_order():
    """Per PR-23: steps must be recorded in order (T1 < T2 < root cause < revision < T3)."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")

    # Step 2 before Step 1 → error
    with pytest.raises(ValueError, match="Cannot record observation before prediction"):
        tracker.record_observation()

    tracker.record_prediction()
    tracker.record_observation()

    # Step 4 before Step 3 → error
    with pytest.raises(ValueError, match="Cannot revise before root cause"):
        tracker.record_revision("commit_hash")

    tracker.record_root_cause("evidence")
    tracker.record_revision("commit_hash")

    # Step 5 before Step 4 → error (already done, but test the path)
    tracker2 = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    tracker2.record_prediction()
    tracker2.record_observation()
    with pytest.raises(ValueError, match="Cannot make second prediction before revision"):
        tracker2.record_second_prediction(0.5, "metric")


def test_closed_loop_tracker_complete_loop():
    """A complete loop with all 5 steps and closeness > 0 is closed."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")

    # T1: prediction
    t1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    tracker.record_prediction(t1)

    # T2: observation (after T1)
    t2 = (datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(days=7)).isoformat()
    tracker.record_observation(t2)

    # Step 3: root cause identified
    tracker.record_root_cause("pKa value in chemistry_knowledge_module was wrong")

    # Step 4: module revised
    tracker.record_revision("abc123def")

    # Step 5: second prediction (after T2), closeness > 0
    t3 = (datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(days=14)).isoformat()
    tracker.record_second_prediction(
        closeness_value=0.3,  # positive → learning occurred
        closeness_metric="abs(pred1-obs) - abs(pred2-obs) = 0.3",
        timestamp=t3,
    )

    assert tracker.is_closed_loop()
    result = validate_closed_loop(tracker)
    assert result["is_closed_loop"] is True
    assert result["learning_occurred"] is True
    assert result["closeness_value"] == 0.3
    assert len(result["steps_missing"]) == 0


def test_closed_loop_tracker_negative_closeness_not_closed():
    """If closeness_value <= 0 (second prediction NOT closer), the loop
    is NOT closed (learning did not occur per PR-23 step 5)."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    tracker.record_prediction("2026-01-01T12:00:00+00:00")
    tracker.record_observation("2026-01-08T12:00:00+00:00")
    tracker.record_root_cause("evidence")
    tracker.record_revision("abc123")
    tracker.record_second_prediction(
        closeness_value=-0.2,  # negative → no learning
        closeness_metric="metric",
        timestamp="2026-01-15T12:00:00+00:00",
    )

    assert not tracker.is_closed_loop()
    result = validate_closed_loop(tracker)
    assert result["is_closed_loop"] is False
    assert result["learning_occurred"] is False


def test_closed_loop_tracker_temporal_ordering_enforced():
    """Per PR-23: T1 < T2 < T3. Violations are caught."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    # T2 before T1 → temporal error
    tracker.record_prediction("2026-01-08T12:00:00+00:00")
    tracker.record_observation("2026-01-01T12:00:00+00:00")  # before T1
    tracker.record_root_cause("evidence")
    tracker.record_revision("abc123")
    tracker.record_second_prediction(
        closeness_value=0.3,
        closeness_metric="metric",
        timestamp="2026-01-15T12:00:00+00:00",
    )
    errors = tracker.validate_temporal_ordering()
    assert len(errors) >= 1
    assert any("T2" in e for e in errors)


# ----------------------------------------------------------------------
# 4. validate_closed_loop: the PR-23 enforcement function
# ----------------------------------------------------------------------

def test_validate_closed_loop_returns_complete_report():
    """validate_closed_loop returns a dict with all required fields."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    tracker.record_prediction()
    result = validate_closed_loop(tracker)
    assert "is_closed_loop" in result
    assert "steps_completed" in result
    assert "steps_missing" in result
    assert "temporal_errors" in result
    assert "closeness_value" in result
    assert "learning_occurred" in result
    assert "experiment_id" in result


def test_validate_closed_loop_incomplete_loop():
    """An incomplete loop reports missing steps."""
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    tracker.record_prediction()
    tracker.record_observation()
    # Steps 3, 4, 5 not done
    result = validate_closed_loop(tracker)
    assert result["is_closed_loop"] is False
    assert "step_3_root_cause" in result["steps_missing"]
    assert "step_4_revision" in result["steps_missing"]
    assert "step_5_second_prediction" in result["steps_missing"]


# ----------------------------------------------------------------------
# 5. The scoping module is real code, not just docstrings
# ----------------------------------------------------------------------

def test_scoping_module_imports_without_error():
    """The experimentation_layer.scoping module imports cleanly."""
    from experimentation_layer import scoping
    assert hasattr(scoping, "ExperimentSpec")
    assert hasattr(scoping, "ClosedLoopTracker")
    assert hasattr(scoping, "EXPERIMENT_CANDIDATES")
    assert hasattr(scoping, "validate_closed_loop")


def test_scoping_module_not_just_docstrings():
    """F-046: the scoping module has real functions, not just docstrings.
    The experimentation_layer/__init__.py is a docstring; scoping.py is code."""
    from experimentation_layer import scoping
    # ExperimentSpec is a real class (not None)
    assert scoping.ExperimentSpec is not None
    # ClosedLoopTracker is a real class
    assert scoping.ClosedLoopTracker is not None
    # EXPERIMENT_CANDIDATES is a non-empty dict
    assert isinstance(scoping.EXPERIMENT_CANDIDATES, dict)
    assert len(scoping.EXPERIMENT_CANDIDATES) >= 2
    # validate_closed_loop is callable
    assert callable(scoping.validate_closed_loop)


# ----------------------------------------------------------------------
# 6. Honest acknowledgment: F-046 is PARTIALLY RESOLVED
# ----------------------------------------------------------------------

def test_f046_status_is_partially_resolved():
    """F-046 scoping is complete (this module + tests). The EXECUTION
    (build + observe) requires reality cooperation per PR-26 and cannot
    be closed by code work alone. This test documents that honestly."""
    # The scoping module exists and works
    from experimentation_layer.scoping import PH_PREDICTION_EXPERIMENT
    errors = PH_PREDICTION_EXPERIMENT.validate()
    assert errors == [], "PH_PREDICTION_EXPERIMENT must be a valid spec"

    # But no closed loop has been recorded (no tracker with all 5 steps)
    # This is the honest state: scoping complete, execution pending.
    tracker = ClosedLoopTracker(experiment_id="EXP-001-ph-prediction")
    assert not tracker.is_closed_loop(), (
        "F-046 cannot be fully RESOLVED by code work alone. The execution "
        "(build + observe) requires an external collaborator per PR-26. "
        "Scoping is complete; execution is pending reality cooperation."
    )
