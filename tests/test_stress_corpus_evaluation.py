"""Tests for stress_corpus_evaluation.py — 100-paper stress test."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


def test_stress_evaluation_runs():
    """The stress evaluation runs on all 100 papers."""
    summary_path = ROOT / "benchmarks" / "reports" / "stress_corpus_summary.json"
    assert summary_path.exists(), "Stress corpus summary must exist"

    with summary_path.open() as f:
        summary = json.load(f)

    assert summary["total_papers"] == 100, f"Expected 100 papers, got {summary['total_papers']}"
    assert summary["total_execution_time_seconds"] > 0
    assert summary["total_entities"] > 0
    assert "domain_breakdown" in summary
    assert "weaknesses" in summary


def test_per_paper_results_exist():
    """Per-paper results (JSONL) exist and have 100 entries."""
    per_paper_path = ROOT / "benchmarks" / "reports" / "stress_corpus_per_paper.jsonl"
    assert per_paper_path.exists()

    lines = per_paper_path.read_text().strip().split("\n")
    assert len(lines) == 100, f"Expected 100 entries, got {len(lines)}"

    # Each line is valid JSON
    for line in lines:
        data = json.loads(line)
        assert "document_id" in data
        assert "entities" in data
        assert "relations" in data
        assert "reaudit_verdict" in data


def test_weaknesses_are_honest():
    """The summary reports weaknesses honestly (not hidden)."""
    summary_path = ROOT / "benchmarks" / "reports" / "stress_corpus_summary.json"
    with summary_path.open() as f:
        summary = json.load(f)

    # Weaknesses must be a list (even if empty)
    assert isinstance(summary["weaknesses"], list)
    # If confidence is low, it must be reported as a weakness
    if summary["avg_confidence"] < 0.5:
        assert any("confidence" in w.lower() for w in summary["weaknesses"]), \
            "Low confidence must be reported as a weakness"


def test_reaudit_verdicts_sum_to_100():
    """Re-audit verdicts (upheld + overturned + unresolved + errors) = 100."""
    summary_path = ROOT / "benchmarks" / "reports" / "stress_corpus_summary.json"
    with summary_path.open() as f:
        summary = json.load(f)

    total = (summary["reaudit_upheld"] + summary["reaudit_overturned"] +
             summary["reaudit_unresolved"] + summary["reaudit_errors"])
    assert total == 100, f"Verdicts sum to {total}, expected 100"


def test_domain_breakdown_exists():
    """Per-domain breakdown exists with at least one domain."""
    summary_path = ROOT / "benchmarks" / "reports" / "stress_corpus_summary.json"
    with summary_path.open() as f:
        summary = json.load(f)

    assert len(summary["domain_breakdown"]) >= 1
    for domain, stats in summary["domain_breakdown"].items():
        assert "papers" in stats
        assert "avg_entities" in stats
        assert "avg_relations" in stats
        assert stats["papers"] > 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
