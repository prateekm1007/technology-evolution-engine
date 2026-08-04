"""
Tests for the Discovery Loop (DR-20) — the end-to-end execution pipeline.

Verifies that the 13-step loop runs end-to-end without crashing and
produces honest output for each step.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.discovery_loop import DiscoveryLoop


class TestDiscoveryLoop:
    """Test the end-to-end discovery loop."""

    def test_loop_runs_end_to_end(self):
        """The loop must run all 13 steps without crashing."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result is not None
        assert len(result["steps"]) == 13, f"Expected 13 steps, got {len(result['steps'])}"

    def test_loop_produces_graph(self):
        """The loop must produce a causal graph with nodes and edges."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["total_nodes"] > 0, "Loop must produce nodes"
        assert result["total_edges"] > 0, "Loop must produce edges"

    def test_loop_finds_bridges(self):
        """Step 6 (Swanson) must find bridges in the corpus."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["bridges_found"] > 0, "Swanson must find bridges"

    def test_loop_finds_analogies(self):
        """Step 7 (Gentner) must find analogous chains."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["analogies_found"] > 0, "Gentner must find analogies"

    def test_loop_designs_experiment(self):
        """Step 10 must design an experiment."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["experiment_designed"] is True, "Loop must design an experiment"

    def test_loop_has_closed_loop(self):
        """Step 11 must have at least 1 closed learning loop (EXP-001)."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["closed_loops"] >= 1, "Loop must have ≥1 closed learning loop"

    def test_loop_reports_honest_results(self):
        """Each step must report PASS, INCOMPLETE, or NOT IMPLEMENTED."""
        loop = DiscoveryLoop()
        result = loop.run()
        for step in result["steps"]:
            assert step["status"] in ("PASS", "INCOMPLETE", "NOT IMPLEMENTED", "FAIL"), (
                f"Step {step['step']} has invalid status: {step['status']}"
            )

    def test_loop_pass_count_meets_threshold(self):
        """At least 8 of 13 steps must PASS for the loop to be 'connected'."""
        loop = DiscoveryLoop()
        result = loop.run()
        assert result["pass_count"] >= 8, (
            f"Expected ≥8 PASS steps, got {result['pass_count']}. "
            f"The loop is not fully connected."
        )

    def test_loop_law_generation_is_honestly_not_implemented(self):
        """Step 5 (BACON law generation) must be NOT IMPLEMENTED (honest)."""
        loop = DiscoveryLoop()
        result = loop.run()
        law_step = [s for s in result["steps"] if s["step"] == 5][0]
        assert law_step["status"] == "NOT IMPLEMENTED", (
            f"BACON law generation should be NOT IMPLEMENTED, got {law_step['status']}"
        )
