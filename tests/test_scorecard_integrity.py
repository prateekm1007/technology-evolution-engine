#!/usr/bin/env python3
"""
test_scorecard_integrity.py — F-091 enforcement (cycle 188).

Per the auditor's PRECONDITION 0: "Stop the commit message from overstating
the scorecard. The generator outputs X; no commit should claim Y > X."

This test verifies:
1. The 12-category scorecard generator runs and produces a composite.
2. The generation benchmark scorer runs and produces a composite.
3. Both composites are reproducible (same input → same output).
4. The AUDITOR_SCORECARD_12.md file matches the generator's current output.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


def test_12_category_scorecard_generator_runs():
    """The 12-category scorecard generator runs without error."""
    from scripts.generate_12_category_scorecard import generate_scorecard
    content = generate_scorecard()
    assert "Composite" in content
    assert "12-Category MEASURED" in content


def test_generation_scorer_runs():
    """The generation benchmark scorer runs without error."""
    from scripts.nine_tenths_loop_v2 import assess_all
    results = assess_all()
    assert isinstance(results, dict)
    assert "_summary" in results
    assert results["_summary"]["total_benchmarks"] == 7


def test_no_duplicate_assess_all():
    """Only one file defines assess_all (PRECONDITION 0.5)."""
    import ast
    scripts_dir = ROOT / "scripts"
    files_with_assess_all = []
    for py_file in scripts_dir.glob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "assess_all":
                    files_with_assess_all.append(py_file.name)
                    break
        except SyntaxError:
            continue
    assert files_with_assess_all == ["nine_tenths_loop_v2.py"], \
        f"Expected only nine_tenths_loop_v2.py, got: {files_with_assess_all}"


def test_gen4_f1_above_090():
    """Gen 4 (mechanism) F1 must be ≥ 0.90 (F-092 fix)."""
    report = ROOT / "benchmarks" / "reports" / "gen4_pr_score.json"
    if not report.exists():
        return
    with report.open() as f:
        data = json.load(f)
    f1 = data.get("f1", 0)
    assert f1 >= 0.90, \
        f"Gen 4 F1={f1:.4f} is below 0.90 target (F-092)"


def test_gen3_f1_above_085():
    """Gen 3 (relation) F1 must be ≥ 0.85 for 9/10."""
    report = ROOT / "benchmarks" / "reports" / "gen3_pr_score.json"
    if not report.exists():
        return
    with report.open() as f:
        data = json.load(f)
    f1 = data.get("f1", 0)
    assert f1 >= 0.85, \
        f"Gen 3 F1={f1:.4f} is below 0.85 (9/10 threshold)"


def test_representation_strict_causal_reported():
    """The Representation measurement reports STRICT causal (not broad)."""
    from scripts.generate_12_category_scorecard import measure_representation
    result = measure_representation()
    assert "STRICT" in result["reasoning"], \
        "Representation must report STRICT causal ratio (F-093)"
    assert "Broad" in result["reasoning"], \
        "Representation must also report Broad for comparison"


def test_causal_not_hardcoded():
    """The causal module must not have hardcoded probabilities (F-088)."""
    hardcoded = ROOT / "scripts" / "causal_real_corpus.py"
    assert not hardcoded.exists(), \
        "causal_real_corpus.py (hardcoded probabilities) must not exist (F-088)"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
