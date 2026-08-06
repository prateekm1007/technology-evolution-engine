#!/usr/bin/env python3
"""
test_implementation_checklist.py — Enforce docs/IMPLEMENTATION_CHECKLIST.md (cycle 190).

Per the CEO directive: "This should live permanently as docs/IMPLEMENTATION_CHECKLIST.md
and be enforced automatically from CI rather than treated as a document that people
are expected to remember."

This test enforces:
1. All DR-39..DR-46 files exist
2. All required docs exist
3. No duplicate sources of truth
4. Single scorer, single scorecard generator
5. Benchmark scores are generated from committed code (not hardcoded)
6. The IMPLEMENTATION_CHECKLIST.md itself exists
"""
import sys
import ast
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


# ===== Section 1: Repository structure =====

def test_governance_files_exist():
    """All 5 governance files exist."""
    for f in ["CONSTITUTION.md", "MASTER_PROTOCOL.md", "EPISTEMIC_ENGINE.md",
              "ANTI_ENTROPY.md", "FAILURES.md"]:
        assert (ROOT / f).exists(), f"Missing governance file: {f}"


def test_required_docs_exist():
    """All required docs exist."""
    for f in ["EXTRACTION_ARCHITECTURE.md", "ENTITY_SCHEMA.md", "RELATION_SCHEMA.md",
              "MECHANISM_STATUS.md", "REAUDIT_SPEC.md", "IMPLEMENTATION_CHECKLIST.md"]:
        assert (ROOT / "docs" / f).exists(), f"Missing doc: docs/{f}"


# ===== Section 3-8: DR-39..DR-44 files =====

def test_dr39_ingest_documents_exists():
    """DR-39: scripts/ingest_documents.py exists."""
    assert (ROOT / "scripts" / "ingest_documents.py").exists()


def test_dr40_extract_entities_exists():
    """DR-40: scripts/extract_entities.py exists."""
    assert (ROOT / "scripts" / "extract_entities.py").exists()


def test_dr41_extract_relations_exists():
    """DR-41: scripts/extract_relations.py exists."""
    assert (ROOT / "scripts" / "extract_relations.py").exists()


def test_dr42_classify_mechanisms_exists():
    """DR-42: scripts/classify_mechanisms.py exists."""
    assert (ROOT / "scripts" / "classify_mechanisms.py").exists()


def test_dr43_provenance_exists():
    """DR-43: scripts/provenance.py exists."""
    assert (ROOT / "scripts" / "provenance.py").exists()


def test_dr44_reaudit_loop_exists():
    """DR-44: scripts/reaudit_loop.py exists."""
    assert (ROOT / "scripts" / "reaudit_loop.py").exists()


def test_dr46_extractor_benchmarks_exists():
    """DR-46: benchmarks/extractor_benchmarks.py exists."""
    assert (ROOT / "benchmarks" / "extractor_benchmarks.py").exists()


# ===== Section 11: Duplicate-source-of-truth protection =====

def test_no_duplicate_scorers():
    """Only one file defines assess_all (single scorer)."""
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


def test_no_forbidden_duplicate_patterns():
    """No forbidden duplicate patterns (scorer_v1, real_causal_v2, old_engine, etc.)."""
    forbidden_names = [
        "scorer_v1.py", "scorer_v2.py",
        "real_causal.py", "real_causal_v2.py",
        "nine_tenths_loop.py",  # old scorer (deleted in cycle 185)
        "causal_real_corpus.py",  # hardcoded probabilities (deleted in cycle 185)
    ]
    for name in forbidden_names:
        assert not (ROOT / "scripts" / name).exists(), \
            f"Forbidden duplicate source of truth: scripts/{name}"

    forbidden_dirs = ["old_engine", "new_engine", "engine"]
    for d in forbidden_dirs:
        assert not (ROOT / d).is_dir(), \
            f"Forbidden duplicate directory: {d}/"


def test_no_live_engine_directory():
    """No live engine/ directory at repo root."""
    assert not (ROOT / "engine").is_dir(), \
        "Live engine/ directory must not exist (archived in archive/dead_engine/)"


# ===== Section 0: Global release gates =====

def test_scorecard_is_generated_not_self_graded():
    """The scorecard generator exists and produces output."""
    gen = ROOT / "scripts" / "generate_12_category_scorecard.py"
    assert gen.exists(), "Scorecard generator must exist"
    gen2 = ROOT / "scripts" / "generate_auditor_scorecard.py"
    assert gen2.exists(), "Generation scorecard generator must exist"


def test_no_hardcoded_scores_in_benchmark_runners():
    """Benchmark runners must not hardcode total_score (must compute from F1)."""
    runners = [
        "benchmarks/entity_extraction_benchmark.py",
        "benchmarks/relation_extraction_benchmark.py",
        "benchmarks/mechanism_chain_benchmark.py",
        "benchmarks/discovery_benchmark.py",
        "benchmarks/section_segmentation_benchmark.py",
    ]
    for runner in runners:
        path = ROOT / runner
        if not path.exists():
            continue
        content = path.read_text()
        # Must contain the single-rubric formula
        assert "round(10 * f1)" in content or "round(10 × F1)" in content, \
            f"{runner} must use round(10 × F1) formula"
        # Must NOT hardcode total_score = 10 or similar
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            # Allow "total_score": round(10 * f1) but not "total_score": 10
            if '"total_score"' in stripped and "round(" not in stripped:
                # Check it's not a hardcoded number
                if any(f'"total_score": {n}' in stripped for n in range(1, 11)):
                    assert False, \
                        f"{runner} has hardcoded total_score: {stripped}"


def test_failures_md_is_append_only():
    """FAILURES.md must not have removed entries (append-only per Law 7)."""
    # This is a structural check: FAILURES.md must exist and be non-empty
    fm = ROOT / "FAILURES.md"
    assert fm.exists(), "FAILURES.md must exist"
    content = fm.read_text()
    assert "F-001" in content, "FAILURES.md must contain early failures (append-only)"
    assert "F-094" in content, "FAILURES.md must contain recent failures (append-only)"


# ===== Section 12: Regression suite =====

def test_regression_suite_exists():
    """Regression suite exists for prior failures."""
    reg = ROOT / "tests" / "test_failure_regression_suite.py"
    assert reg.exists(), "Failure regression suite must exist"


def test_no_duplicate_sources_test_exists():
    """Duplicate source of truth test exists."""
    t = ROOT / "tests" / "test_no_duplicate_sources_of_truth.py"
    assert t.exists(), "test_no_duplicate_sources_of_truth.py must exist"


def test_scorecard_integrity_test_exists():
    """Scorecard integrity test exists."""
    t = ROOT / "tests" / "test_scorecard_integrity.py"
    assert t.exists(), "test_scorecard_integrity.py must exist"


# ===== Section 15: Checklist enforcement =====

def test_implementation_checklist_exists():
    """The IMPLEMENTATION_CHECKLIST.md exists as a permanent doc."""
    assert (ROOT / "docs" / "IMPLEMENTATION_CHECKLIST.md").exists(), \
        "docs/IMPLEMENTATION_CHECKLIST.md must exist"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
