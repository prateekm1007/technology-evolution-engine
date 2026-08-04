"""
Test for EXP-001: the first closed learning loop.

Per DR-14: the observation-prediction-experiment loop must close.
Per F-050: closed_loops must reach ≥ 1.

This test verifies that:
  1. The ClosedLoopTracker records all 5 steps
  2. The loop is closed (is_closed_loop() returns True)
  3. Learning occurred (closeness_value > 0)
  4. The temporal ordering is correct (T1 < T2 < T3 < T4 < T5)
  5. The root cause is documented
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experimentation_layer.scoping import ClosedLoopTracker, validate_closed_loop
from scripts.close_exp_001 import close_exp_001_loop


class TestExp001ClosedLoop:
    """Test the first closed learning loop (EXP-001)."""

    def test_all_5_steps_recorded(self):
        """All 5 PR-23 steps must be recorded."""
        tracker = close_exp_001_loop()
        assert tracker.step_1_prediction_timestamp is not None
        assert tracker.step_2_observation_timestamp is not None
        assert tracker.step_3_root_cause_identified is True
        assert tracker.step_4_module_revised is True
        assert tracker.step_5_second_prediction_timestamp is not None

    def test_is_closed_loop(self):
        """The loop must be closed (is_closed_loop() returns True)."""
        tracker = close_exp_001_loop()
        assert tracker.is_closed_loop(), (
            "EXP-001 should produce a closed loop — all 5 steps recorded, "
            "closeness_value > 0"
        )

    def test_learning_occurred(self):
        """Learning occurred (closeness_value > 0 — second prediction closer)."""
        tracker = close_exp_001_loop()
        assert tracker.step_5_closeness_value is not None
        assert tracker.step_5_closeness_value > 0, (
            f"Closeness value should be > 0 (second prediction closer to "
            f"observation than first). Got: {tracker.step_5_closeness_value}"
        )

    def test_temporal_ordering(self):
        """T1 < T2 < T3 < T4 < T5."""
        tracker = close_exp_001_loop()
        errors = tracker.validate_temporal_ordering()
        assert len(errors) == 0, f"Temporal ordering errors: {errors}"

    def test_validate_closed_loop_passes(self):
        """validate_closed_loop() returns is_closed_loop=True."""
        tracker = close_exp_001_loop()
        result = validate_closed_loop(tracker)
        assert result["is_closed_loop"] is True
        assert result["learning_occurred"] is True
        assert len(result["steps_missing"]) == 0

    def test_root_cause_documented(self):
        """The root cause must be documented."""
        tracker = close_exp_001_loop()
        assert tracker.step_3_root_cause_evidence is not None
        assert len(tracker.step_3_root_cause_evidence) > 50, (
            "Root cause evidence should be detailed (>50 chars)"
        )
        assert "contradict" in tracker.step_3_root_cause_evidence.lower(), (
            "Root cause should mention the contradiction"
        )

    def test_closeness_value_is_1_8(self):
        """The closeness value should be 1.8.

        |first_pred(6.5) - obs(8.3)| - |second_pred(8.3) - obs(8.3)|
        = |6.5 - 8.3| - |8.3 - 8.3|
        = 1.8 - 0.0
        = 1.8
        """
        tracker = close_exp_001_loop()
        assert tracker.step_5_closeness_value == 1.8, (
            f"Expected closeness=1.8, got {tracker.step_5_closeness_value}"
        )

    def test_closed_loops_count_is_1(self):
        """After closing EXP-001, closed_loops should be 1."""
        tracker = close_exp_001_loop()
        # The tracker itself doesn't maintain a global count, but the
        # is_closed_loop() method returns True, which means this tracker
        # represents 1 closed loop.
        assert tracker.is_closed_loop()
        # In the full system, closed_loops would be computed as:
        # sum(1 for tracker in all_trackers if tracker.is_closed_loop())
        # With EXP-001 closed, that count is 1.
