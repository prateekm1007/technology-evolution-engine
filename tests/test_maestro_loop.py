"""
Test the Maestro Loop (cycle 49).

Per ANTI_ENTROPY.md "Epistemic anti-entropy rules": "Prefer loops over
modules." This test verifies the 7 stages of the Maestro Loop run
correctly and produce the expected artifacts.

The test does NOT commit to git (that's a destructive action). It runs
stages 1-6 in a temp directory to verify the loop produces a cycle report.
"""
import sys
import pathlib
import json
import shutil
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestMaestroLoopStages:
    """Verify each stage of the Maestro Loop works in isolation."""

    def test_stage_1_run_discovery_loop_returns_summary(self):
        """Stage 1: run_discovery_loop returns a dict with expected keys."""
        from scripts.maestro_loop import run_discovery_loop
        summary = run_discovery_loop()
        assert isinstance(summary, dict)
        assert "pass_count" in summary
        assert "total_nodes" in summary
        assert "total_edges" in summary
        assert "bridges_found" in summary
        assert "analogies_found" in summary
        assert "contradictions_found" in summary

    def test_stage_2_run_acid_test_returns_per_test_results(self):
        """Stage 2: run_acid_test returns PASS/INCOMPLETE/NOT IMPLEMENTED per test."""
        from scripts.maestro_loop import run_acid_test
        results = run_acid_test()
        # 8 tests + _meta
        assert len(results) == 9
        # Required test names
        for name in ("Swanson", "Pearl", "Popper", "Gentner", "Altshuller",
                     "Ross King", "BACON", "Arthur"):
            assert name in results, f"missing test: {name}"
            assert "status" in results[name]
            assert results[name]["status"] in (
                "PASS", "INCOMPLETE", "NOT IMPLEMENTED", "MERGED with Swanson"
            )
        # _meta has graph stats
        assert "_meta" in results
        assert "total_nodes" in results["_meta"]
        assert "total_edges" in results["_meta"]

    def test_stage_3_record_cycle_appends_to_log(self, tmp_path, monkeypatch):
        """Stage 3: record_cycle appends a JSON line to cycle_log.jsonl."""
        from scripts import maestro_loop

        # Patch CYCLE_LOG to point at tmp_path
        log_path = tmp_path / "cycle_log.jsonl"
        monkeypatch.setattr(maestro_loop, "CYCLE_LOG", log_path)
        monkeypatch.setattr(maestro_loop, "CYCLES_DIR", tmp_path)

        discovery_summary = {
            "pass_count": 11, "incomplete_count": 1, "not_implemented_count": 1,
            "total_nodes": 70, "total_edges": 224,
            "bridges_found": 702, "analogies_found": 215021,
            "contradictions_found": 126, "closed_loops": 1,
        }
        acid_test = {
            "Swanson":    {"status": "PASS", "count": 548, "threshold": 5, "unit": "u"},
            "Pearl":      {"status": "PASS", "count": 155, "threshold": 10, "unit": "u"},
            "Popper":     {"status": "PASS", "count": 224, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 191211, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 126, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "INCOMPLETE", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "NOT IMPLEMENTED", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 702, "threshold": None, "unit": "u"},
            "_meta": {"total_nodes": 70, "total_edges": 224, "total_bridges": 702,
                      "total_analogies": 215021, "total_contradictions": 126},
        }

        entry = maestro_loop.record_cycle(1, discovery_summary, acid_test)
        assert entry["cycle"] == 1
        assert entry["acid_test"]["pass_count"] == 5
        assert entry["acid_test"]["hardens"] is True
        assert log_path.exists()
        line = log_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed["cycle"] == 1

    def test_stage_3_next_cycle_number_increments(self, tmp_path, monkeypatch):
        """Stage 3: _next_cycle_number returns max+1."""
        from scripts import maestro_loop

        log_path = tmp_path / "cycle_log.jsonl"
        log_path.write_text(json.dumps({"cycle": 5}) + "\n" +
                            json.dumps({"cycle": 12}) + "\n")
        monkeypatch.setattr(maestro_loop, "CYCLE_LOG", log_path)
        assert maestro_loop._next_cycle_number() == 13

        # Empty log → cycle 1
        empty_log = tmp_path / "empty.jsonl"
        empty_log.write_text("")
        monkeypatch.setattr(maestro_loop, "CYCLE_LOG", empty_log)
        assert maestro_loop._next_cycle_number() == 1

    def test_stage_4_identify_gap_picks_closest_to_pass(self):
        """Stage 4: identify_gap picks the closest-to-PASS INCOMPLETE test."""
        from scripts.maestro_loop import identify_gap
        acid_test = {
            "Swanson":    {"status": "PASS", "count": 548, "threshold": 5, "unit": "u"},
            "Pearl":      {"status": "PASS", "count": 155, "threshold": 10, "unit": "u"},
            "Popper":     {"status": "PASS", "count": 224, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 191211, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 126, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "INCOMPLETE", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "NOT IMPLEMENTED", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 702, "threshold": None, "unit": "u"},
            "_meta": {},
        }
        gap = identify_gap(acid_test)
        # Ross King is the only INCOMPLETE (qualitative) → it's the gap
        # (BACON is NOT IMPLEMENTED Phase III, lowest priority)
        assert gap["test"] == "Ross King"
        assert gap["gap_type"] == "qualitative"

    def test_stage_4_identify_gap_returns_lowest_priority_when_all_pass(self):
        """Stage 4: when all tests PASS except BACON (NOT IMPLEMENTED), gap is BACON.

        BACON is Phase III work — it remains the only gap. The function
        should NOT return 'none' because BACON is genuinely missing.
        'none' is reserved for the case where everything is implemented
        AND passing (impossible today because BACON doesn't exist).
        """
        from scripts.maestro_loop import identify_gap
        acid_test = {
            "Swanson":    {"status": "PASS", "count": 100, "threshold": 5, "unit": "u"},
            "Pearl":      {"status": "PASS", "count": 100, "threshold": 10, "unit": "u"},
            "Popper":     {"status": "PASS", "count": 100, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 100, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 100, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "PASS", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "NOT IMPLEMENTED", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 100, "threshold": None, "unit": "u"},
            "_meta": {},
        }
        gap = identify_gap(acid_test)
        # BACON is the only remaining gap (Phase III NOT IMPLEMENTED)
        assert gap["test"] == "BACON"
        assert gap["gap_type"] == "not_implemented"
        assert gap["priority"] == 0  # lowest priority — Phase III

    def test_stage_4_identify_gap_returns_none_only_when_truly_nothing_left(self):
        """Stage 4: 'none' requires every test to PASS (including no NOT IMPLEMENTED)."""
        from scripts.maestro_loop import identify_gap
        acid_test = {
            "Swanson":    {"status": "PASS", "count": 100, "threshold": 5, "unit": "u"},
            "Pearl":      {"status": "PASS", "count": 100, "threshold": 10, "unit": "u"},
            "Popper":     {"status": "PASS", "count": 100, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 100, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 100, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "PASS", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "PASS", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 100, "threshold": None, "unit": "u"},
            "_meta": {},
        }
        gap = identify_gap(acid_test)
        # All 7 effective tests PASS, BACON is hypothetically PASS — nothing left
        assert gap["gap_type"] == "none"
        assert gap["test"] is None

    def test_stage_4_identify_gap_picks_numeric_closest_first(self):
        """Stage 4: when multiple numeric INCOMPLETE, pick the smallest deficit."""
        from scripts.maestro_loop import identify_gap
        acid_test = {
            "Swanson":    {"status": "INCOMPLETE", "count": 3, "threshold": 5, "unit": "u"},  # deficit 2
            "Pearl":      {"status": "INCOMPLETE", "count": 8, "threshold": 10, "unit": "u"},  # deficit 2
            "Popper":     {"status": "PASS", "count": 100, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 100, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 100, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "INCOMPLETE", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "NOT IMPLEMENTED", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 100, "threshold": None, "unit": "u"},
            "_meta": {},
        }
        gap = identify_gap(acid_test)
        # Both Swanson and Pearl have deficit 2; tie-break sorts by deficit only.
        # The chosen test should be one of them (smallest deficit).
        assert gap["test"] in ("Swanson", "Pearl")
        assert gap["deficit"] == 2

    def test_stage_5_propose_intervention_returns_concrete_action(self):
        """Stage 5: propose_intervention converts a gap into a concrete proposal."""
        from scripts.maestro_loop import propose_intervention
        gap = {
            "test": "Swanson", "gap_type": "numeric",
            "current_count": 3, "threshold": 5, "deficit": 2,
            "priority": 8,
            "intervention": "Add another cross-domain corpus (e.g., N₂ fixation).",
        }
        proposal = propose_intervention(gap, cycle_n=49)
        assert proposal["cycle"] == 50
        assert "Swanson" in proposal["task"]
        assert "Add another cross-domain corpus" in proposal["action"]
        assert "rationale" in proposal
        assert isinstance(proposal["estimated_files_changed"], list)
        assert len(proposal["estimated_files_changed"]) > 0

    def test_stage_5_propose_intervention_for_none_gap(self):
        """Stage 5: when gap is none, propose BACON (Phase III)."""
        from scripts.maestro_loop import propose_intervention
        gap = {"test": None, "gap_type": "none",
               "message": "All tests PASS."}
        proposal = propose_intervention(gap, cycle_n=49)
        assert proposal["cycle"] == 50
        assert "BACON" in proposal["action"] or "Phase III" in proposal["action"]

    def test_stage_6_write_cycle_report(self, tmp_path, monkeypatch):
        """Stage 6: write_cycle_report produces a Markdown file with required sections."""
        from scripts import maestro_loop

        monkeypatch.setattr(maestro_loop, "CYCLES_DIR", tmp_path)
        monkeypatch.setattr(maestro_loop, "CYCLE_LOG", tmp_path / "cycle_log.jsonl")

        discovery_summary = {
            "total_nodes": 70, "total_edges": 224,
            "bridges_found": 702, "analogies_found": 215021,
            "contradictions_found": 126, "closed_loops": 1,
            "pass_count": 11, "incomplete_count": 1, "not_implemented_count": 1,
        }
        acid_test = {
            "Swanson":    {"status": "PASS", "count": 548, "threshold": 5, "unit": "u"},
            "Pearl":      {"status": "PASS", "count": 155, "threshold": 10, "unit": "u"},
            "Popper":     {"status": "PASS", "count": 224, "threshold": 10, "unit": "u"},
            "Gentner":    {"status": "PASS", "count": 191211, "threshold": 5, "unit": "u"},
            "Altshuller": {"status": "PASS", "count": 126, "threshold": 3, "unit": "u"},
            "Ross King":  {"status": "INCOMPLETE", "count": None, "threshold": None, "unit": "u"},
            "BACON":      {"status": "NOT IMPLEMENTED", "count": None, "threshold": None, "unit": "u"},
            "Arthur":     {"status": "MERGED with Swanson", "count": 702, "threshold": None, "unit": "u"},
            "_meta": {"total_nodes": 70, "total_edges": 224, "total_bridges": 702,
                      "total_analogies": 215021, "total_contradictions": 126},
        }
        cycle_entry = {
            "cycle": 49,
            "timestamp": "2026-08-05T00:00:00+00:00",
            "acid_test": {"pass_count": 5, "incomplete_count": 1,
                          "not_implemented_count": 1, "merged_count": 1,
                          "hardens": True, "results": {}},
        }
        gap = {"test": "Ross King", "gap_type": "qualitative", "priority": 3,
               "intervention": "Design experiments that distinguish competing hypotheses."}
        proposal = {"cycle": 50, "task": "Close the Ross King gap",
                    "action": "Design experiments...",
                    "rationale": "Ross King is qualitative...",
                    "estimated_files_changed": ["invention_compiler/causal_simulator.py"]}

        report_path = maestro_loop.write_cycle_report(
            49, discovery_summary, acid_test, cycle_entry, gap, proposal,
        )
        assert report_path.exists()
        text = report_path.read_text()
        assert "Cycle 049" in text
        assert "Stage 1: Discovery Loop" in text
        assert "Stage 2: Acid Test" in text
        assert "Stage 3: Cycle Recorded" in text
        assert "Stage 4: Gap Identification" in text
        assert "Stage 5: Proposed Next Intervention" in text
        assert "Ross King" in text
        assert "Honest Scope" in text


class TestMaestroLoopIntegration:
    """Verify the loop runs end-to-end in dry-run mode."""

    def test_dry_run_produces_cycle_dict(self):
        """Run the loop in dry-run mode and verify it returns a cycle dict."""
        from scripts.maestro_loop import run_one_cycle
        result = run_one_cycle(commit=False, push=False, dry_run=True)
        assert result["dry_run"] is True
        assert "cycle" in result
        assert isinstance(result["cycle"], int)
        assert result["cycle"] >= 1
        assert "discovery" in result
        assert "acid_test" in result
        # In dry-run we don't identify gap or write report
        assert "gap" not in result
