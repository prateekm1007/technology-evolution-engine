#!/usr/bin/env python3
"""
test_no_duplicate_sources_of_truth.py — PRECONDITION 0.5 enforcement
(cycle 185, auditor update #3 addendum).

Per the auditor's PRECONDITION 0.5: "after the single rubric is chosen,
delete nine_tenths_loop.py outright rather than leaving it importable.
A CI test that fails the build if a second file defining assess_all or
a second directory named engine reappears would turn 'don't create a
duplicate source of truth' from a discipline someone has to remember
into something the build enforces."

This test enforces:
1. No second scoring file defining `assess_all` (only nine_tenths_loop_v2.py).
2. No live `engine/` directory (the dead engine is in archive/dead_engine/).
3. No second causal module with hardcoded probabilities (causal_real_corpus.py
   was deleted; only causal_data_estimated.py remains).
4. No second discovery-graph scorer that disagrees with the primary.

If any of these reappear, this test fails the build.
"""
import sys
import ast
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_no_second_assess_all_file():
    """Only nine_tenths_loop_v2.py may define assess_all.

    The old nine_tenths_loop.py was deleted in cycle 185 (PRECONDITION 0.5).
    If a second file defining assess_all reappears, this test fails.
    """
    files_with_assess_all = []
    for py_file in SCRIPTS.glob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "assess_all":
                    files_with_assess_all.append(py_file.name)
                    break
        except SyntaxError:
            continue

    # Only nine_tenths_loop_v2.py should define assess_all
    expected = {"nine_tenths_loop_v2.py"}
    actual = set(files_with_assess_all)

    # Remove the expected one
    extras = actual - expected
    assert not extras, (
        f"PRECONDITION 0.5 violation: multiple files define assess_all. "
        f"Expected only {expected}, but found: {actual}. "
        f"Extras: {extras}. "
        f"Delete the duplicate — don't leave a second source of truth."
    )


def test_no_live_engine_directory():
    """No live engine/ directory at the repo root.

    The engine/ directory was archived to archive/dead_engine/engine/ in
    a prior cycle. If a live engine/ reappears at the repo root, this
    test fails.
    """
    live_engine = ROOT / "engine"
    assert not live_engine.exists(), (
        f"PRECONDITION 0.5 violation: live engine/ directory found at "
        f"{live_engine}. The dead engine is archived at "
        f"archive/dead_engine/engine/. Delete the live copy — don't leave "
        f"a second source of truth."
    )


def test_no_hardcoded_causal_module():
    """causal_real_corpus.py (hardcoded probabilities) must not exist.

    It was deleted in cycle 185 (F-088 fix). Only causal_data_estimated.py
    remains, which returns honest 'I don't know' when data is insufficient.
    """
    hardcoded_module = SCRIPTS / "causal_real_corpus.py"
    assert not hardcoded_module.exists(), (
        f"PRECONDITION 0.5 violation: {hardcoded_module} exists. "
        f"This module used hardcoded probabilities (F-088). "
        f"It was deleted in cycle 185. Use causal_data_estimated.py instead."
    )


def test_no_second_citation_disjoint_module():
    """Only swanson_citation_disjoint.py and swanson_real_citation_disjoint.py.

    The first is the algorithm; the second is the real-corpus runner.
    No third duplicate should exist.
    """
    swanson_modules = list(SCRIPTS.glob("swanson*citation*.py"))
    # Expected: swanson_citation_disjoint.py (algorithm) +
    # swanson_real_citation_disjoint.py (real-corpus runner)
    names = {m.name for m in swanson_modules}
    expected = {"swanson_citation_disjoint.py", "swanson_real_citation_disjoint.py"}
    extras = names - expected
    assert not extras, (
        f"PRECONDITION 0.5 violation: unexpected swanson citation modules: "
        f"{extras}. Expected only {expected}."
    )


def test_nine_tenths_loop_v2_is_importable():
    """The single source of truth for scoring must be importable."""
    from scripts.nine_tenths_loop_v2 import assess_all
    results = assess_all()
    assert isinstance(results, dict)
    assert "_summary" in results
    assert results["_summary"]["total_benchmarks"] == 7


def test_causal_data_estimated_is_importable():
    """The single source of truth for causal reasoning must be importable."""
    from scripts.causal_data_estimated import DataEstimatedCounterfactual
    dec = DataEstimatedCounterfactual()
    # Must NOT have hardcoded probability attributes
    assert not hasattr(dec, "_hardcoded_p_high"), (
        "DataEstimatedCounterfactual must not have hardcoded probabilities."
    )


def test_generate_auditor_scorecard_is_importable():
    """The single source of truth for the scorecard must be importable."""
    from scripts.generate_auditor_scorecard import generate_scorecard
    content = generate_scorecard()
    assert "MEASURED" in content
    assert "auto-generated" in content


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
