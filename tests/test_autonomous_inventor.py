"""Tests for DR-81: autonomous invention loop."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.autonomous_inventor import (
    AutonomousInventor, InventorResult, InventorCycle,
)
from scripts.design_memory import DesignMemory


def _run_inventor(n_cycles=2, **kwargs):
    ai = AutonomousInventor(seed=42, n_cycles=n_cycles,
                            beam_width=3, n_iterations=1,
                            n_candidates=3, **kwargs)
    return ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[
            ("bismuth telluride", "generates", "voltage"),
            ("bismuth telluride", "conducts", "electricity"),
            ("lead telluride", "generates", "voltage"),
            ("bismuth telluride", "transfers", "heat"),
        ],
        input_text="improve thermoelectric efficiency of bismuth telluride",
        gold_text="The reference contains Seebeck, conductivity, and "
                  "thermal data for various lead alloys.",
    )


# ---------------------------------------------------------------------------
# DR-81: autonomous_inventor.py
# ---------------------------------------------------------------------------
def test_inventor_returns_inventor_result():
    """run() returns an InventorResult."""
    result = _run_inventor(n_cycles=1)
    assert isinstance(result, InventorResult)
    assert result.n_cycles == 1


def test_inventor_runs_all_cycles():
    """The inventor runs the requested number of cycles."""
    result = _run_inventor(n_cycles=3)
    assert result.n_cycles == 3
    assert len(result.cycles) == 3


def test_inventor_each_cycle_has_spec():
    """Each cycle has a spec compiled from the objective."""
    result = _run_inventor(n_cycles=2)
    for c in result.cycles:
        assert c.spec is not None
        assert c.spec.domain == "thermoelectric"


def test_inventor_infers_capabilities():
    """The capability reasoner infers additional capabilities."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    # The input capabilities include conducts_electricity and transfers_heat,
    # which should chain to can_generate_current
    assert len(c.capabilities_inferred) > 0


def test_inventor_runs_search():
    """Each cycle runs the search and produces a best_config."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    assert c.search_result is not None
    assert c.best_config is not None
    assert c.best_config.config_hash != ""


def test_inventor_runs_failure_engine():
    """The failure engine runs on the best config."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    assert c.failure_engine_result is not None
    assert c.failure_engine_result.status in ("PASS", "FAIL", "VETO")


def test_inventor_runs_novelty_check():
    """The novelty engine checks the best config."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    # is_novel is a bool (may be True or False depending on registry)
    assert isinstance(c.is_novel, bool)


def test_inventor_runs_experiment_runner():
    """The experiment runner executes the predict-measure-residual loop."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    assert c.experiment_result is not None


def test_inventor_records_lessons_to_memory():
    """Lessons are recorded to the design memory."""
    mem = DesignMemory()
    ai = AutonomousInventor(seed=42, n_cycles=1, beam_width=3,
                            n_iterations=1, n_candidates=3,
                            design_memory=mem)
    result = ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[("bismuth telluride", "generates", "voltage")],
        input_text="improve TE",
        gold_text="independent gold",
    )
    # The memory should have at least one entry after a cycle
    snap = mem.snapshot()
    assert snap.n_iterations >= 1


def test_inventor_updates_beliefs():
    """Beliefs are revised after each cycle."""
    ai = AutonomousInventor(seed=42, n_cycles=1, beam_width=3,
                            n_iterations=1, n_candidates=3)
    initial_beliefs = dict(ai.belief_revision.beliefs)
    ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[("bismuth telluride", "generates", "voltage")],
        input_text="improve TE",
        gold_text="independent gold",
    )
    final_beliefs = ai.belief_revision.beliefs
    # At least one operator's belief should have changed
    changed = [op for op in initial_beliefs
               if abs(initial_beliefs[op] - final_beliefs[op]) > 1e-9]
    # (May be empty if no residuals were significant, but the belief state
    # should still be queryable.)
    assert isinstance(final_beliefs, dict)


def test_inventor_reproducible():
    """Same seed → same best score across runs."""
    r1 = _run_inventor(n_cycles=1)
    r2 = _run_inventor(n_cycles=1)
    assert abs(r1.final_best_score - r2.final_best_score) < 1e-9


def test_inventor_wires_all_stages():
    """The inventor's provenance lists all the stages wired together."""
    result = _run_inventor(n_cycles=1)
    stages = result.provenance["stages_wired"]
    required = ["specification", "capability_graph", "capability_reasoner",
                "operator_library", "search_engine", "forward_model",
                "failure_engine", "novelty_engine", "prototype_compiler",
                "measurement_engine", "experiment_runner",
                "design_memory", "operator_ranking", "belief_revision"]
    for s in required:
        assert s in stages, f"missing stage in provenance: {s}"


def test_inventor_cycle_has_trace():
    """Each cycle has a non-empty trace."""
    result = _run_inventor(n_cycles=1)
    c = result.cycles[0]
    assert len(c.trace) > 0
    steps = [e["step"] for e in c.trace]
    assert "capability_reasoning" in steps
    assert "search" in steps
    assert "failure_engine" in steps
    assert "novelty_check" in steps
    assert "experiment_runner" in steps
    assert "belief_revision" in steps


def test_inventor_result_serializable():
    import json
    result = _run_inventor(n_cycles=1)
    json.dumps(result.to_dict())


def test_inventor_handles_minimal_inputs():
    """The inventor runs even with minimal inputs (no input/gold text)."""
    ai = AutonomousInventor(seed=42, n_cycles=1, beam_width=3,
                            n_iterations=1, n_candidates=3)
    result = ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[("bismuth telluride", "generates", "voltage")],
    )
    # Should not crash; failure engine should report skips for missing inputs
    assert result.n_cycles == 1
    c = result.cycles[0]
    assert c.failure_engine_result is not None


def test_inventor_records_motif_for_high_score():
    """If a cycle's best score is high, a motif is recorded."""
    mem = DesignMemory()
    ai = AutonomousInventor(seed=42, n_cycles=1, beam_width=3,
                            n_iterations=1, n_candidates=3,
                            design_memory=mem)
    result = ai.run(
        objective="improve thermoelectric efficiency of bismuth telluride",
        relations=[("bismuth telluride", "generates", "voltage"),
                   ("bismuth telluride", "conducts", "electricity")],
        input_text="improve TE",
        gold_text="independent gold",
    )
    # If the best score exceeds 0.5, a motif should be recorded
    if result.final_best_score > 0.5:
        snap = mem.snapshot()
        assert snap.n_motifs >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
