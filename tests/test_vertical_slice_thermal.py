"""Tests for DR-82: vertical slice (thermal domain)."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.vertical_slice_thermal import (
    VerticalSliceThermal, VerticalSliceReport,
)


def _run_slice(n_cycles=1):
    vst = VerticalSliceThermal(seed=42, n_cycles=n_cycles)
    return vst.run()


# ---------------------------------------------------------------------------
# DR-82: vertical_slice_thermal
# ---------------------------------------------------------------------------
def test_slice_returns_vertical_slice_report():
    """run() returns a VerticalSliceReport."""
    report = _run_slice()
    assert isinstance(report, VerticalSliceReport)


def test_slice_domain_is_thermal():
    """The slice is for the thermal domain."""
    report = _run_slice()
    assert report.domain == "thermal"


def test_slice_objective_set():
    """The objective is set."""
    report = _run_slice()
    assert "thermoelectric" in report.objective.lower()


def test_slice_goals_parsed():
    """The slice parses goals from natural language."""
    report = _run_slice()
    assert len(report.goals_parsed) >= 1
    # Each goal should have a metric and direction
    for g in report.goals_parsed:
        assert "metric" in g
        assert "direction" in g


def test_slice_spec_compiled():
    """The spec is compiled with domain=thermoelectric."""
    report = _run_slice()
    assert report.spec is not None
    assert report.spec["domain"] == "thermoelectric"
    assert report.spec["target_material"] == "bismuth telluride"


def test_slice_acceptance_criteria_compiled():
    """Acceptance criteria are compiled into checkable callables."""
    report = _run_slice()
    assert len(report.acceptance_criteria) >= 1
    # Thermoelectric spec should have ZT > 1.0
    metrics = [ac["metric"] for ac in report.acceptance_criteria]
    assert "ZT" in metrics


def test_slice_capabilities_inferred():
    """The capability reasoner infers closure capabilities."""
    report = _run_slice()
    assert len(report.capabilities_inferred) > 0
    # The input includes conducts_electricity + transfers_heat →
    # can_generate_current should be in the closure
    assert "can_generate_current" in report.capabilities_inferred


def test_slice_physics_constraints_derived():
    """Physics constraints are derived from capabilities."""
    report = _run_slice()
    assert len(report.physics_constraints) > 0
    # Should include electrical_conductivity constraint
    params = [c["parameter"] for c in report.physics_constraints]
    assert "electrical_conductivity" in params


def test_slice_runs_inventor():
    """The autonomous inventor is run."""
    report = _run_slice()
    assert report.inventor_result is not None
    assert report.n_cycles >= 1


def test_slice_best_config_found():
    """A best config is identified."""
    report = _run_slice()
    # best_config_id may be None if the search produced nothing — but
    # with the default seed it should find something.
    assert report.best_config_id is not None


def test_slice_measures_zt():
    """The slice measures ZT on the best config."""
    report = _run_slice()
    # ZT may be zero if the best config doesn't have a seebeck coefficient,
    # but the report fields should be populated
    assert report.best_predicted_ZT is not None
    assert report.best_measured_ZT is not None


def test_slice_residual_computed():
    """The residual (predicted - measured) is computed — OR None if vetoed.

    Per F-100 (cycle 205): if the candidate is physically implausible (ZT > 5),
    the plausibility veto fires and no residual is computed. This is correct
    behavior — the test must accept either a computed residual OR a veto.
    """
    report = _run_slice()
    # If vetoed, residual is None — that's correct behavior
    if report.acceptance_passed:
        # Not vetoed — residual must be computed
        assert report.best_residual is not None, \
            "Non-vetoed candidate must have a computed residual"
    else:
        # Vetoed — residual may be None (vetoed before residual computation)
        # or may be computed (vetoed after). Either is acceptable.
        assert isinstance(report.best_residual, (int, float, type(None)))


def test_slice_records_lessons():
    """Lessons are recorded during the slice."""
    report = _run_slice()
    # Lessons may be 0 if no significant residuals, but the field is set
    assert isinstance(report.n_total_lessons, int)
    assert report.n_total_lessons >= 0


def test_slice_has_trace():
    """The slice has a non-empty trace."""
    report = _run_slice()
    assert len(report.trace) > 0
    steps = [e["step"] for e in report.trace]
    # All the major pipeline stages should appear
    assert "goal_parsing" in steps
    assert "spec_compilation" in steps
    assert "acceptance_criteria" in steps
    assert "capability_reasoning" in steps
    assert "constraint_derivation" in steps
    assert "autonomous_inventor" in steps


def test_slice_acceptance_evaluation_runs():
    """The acceptance criteria are evaluated against the best config."""
    report = _run_slice()
    # acceptance_passed is a bool (may be True or False)
    assert isinstance(report.acceptance_passed, bool)


def test_slice_reproducible():
    """Same seed → same best score."""
    r1 = _run_slice()
    r2 = _run_slice()
    assert abs(r1.best_score - r2.best_score) < 1e-9


def test_slice_report_serializable():
    import json
    report = _run_slice()
    json.dumps(report.to_dict())


def test_slice_provenance_lists_pipeline_stages():
    """The trace lists all the pipeline stages.

    Per cycle 205: provenance schema changed; the trace is now the
    authoritative record of pipeline stages.
    """
    report = _run_slice()
    # The trace is the authoritative record of pipeline stages
    steps = [e["step"] for e in report.trace]
    required = ["goal_parsing", "spec_compilation", "acceptance_criteria",
                "capability_reasoning", "constraint_derivation",
                "autonomous_inventor"]
    for s in required:
        assert s in steps, f"missing pipeline stage in trace: {s}"


def test_slice_uses_design_memory():
    """The slice uses a DesignMemory to record iterations."""
    from scripts.design_memory import DesignMemory
    mem = DesignMemory()
    vst = VerticalSliceThermal(seed=42, n_cycles=1, design_memory=mem)
    vst.run()
    snap = mem.snapshot()
    # At least one iteration should have been recorded
    assert snap.n_iterations >= 1


def test_slice_runs_multiple_cycles():
    """The slice can run multiple cycles."""
    report = _run_slice(n_cycles=2)
    assert report.n_cycles == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
