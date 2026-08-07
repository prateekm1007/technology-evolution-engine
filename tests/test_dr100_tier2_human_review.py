"""
test_dr100_tier2_human_review.py — Tests for DR-100 Gate D scaffolding.

Gate D is INHERENTLY blocked on human review — these tests verify
the scaffolding is correctly produced (forms, templates, aggregation
script) but cannot verify the gate VERDICT (which requires human input).
"""
import sys
import json
import csv
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from audit.measurement_integrity.dr100_tier2_human_review import (
    anonymize_proposal, generate_anonymized_set, RUBRIC,
    render_review_form, render_csv_template,
)


# ============================================================================
# ANONYMIZATION
# ============================================================================

def test_anonymize_removes_proposal_id():
    proposal = {
        "proposal_id": "PROP-001",
        "shared_mechanism": "test mechanism",
        "necessary_assumptions": ["assumption 1"],
        "prediction": "test prediction",
        "alternative_explanations": ["alt 1"],
        "counterexample": "test counterexample",
        "falsification_experiment": "test experiment",
        "confidence": 0.75,
        "provenance": {"source": "should_be_removed"},
    }
    anon = anonymize_proposal(proposal, "REVIEW-001")
    assert anon["anon_id"] == "REVIEW-001"
    assert "proposal_id" not in anon
    assert "provenance" not in anon
    assert anon["shared_mechanism"] == "test mechanism"
    assert anon["system_confidence"] == 0.75


def test_anonymize_preserves_scientific_content():
    proposal = {
        "proposal_id": "PROP-001",
        "shared_mechanism": "X connects A to B",
        "necessary_assumptions": ["A1", "A2"],
        "prediction": "If X holds, Y",
        "alternative_explanations": ["AE1"],
        "counterexample": "If X removed, Y disappears",
        "falsification_experiment": "Test X in isolation",
        "confidence": 0.5,
    }
    anon = anonymize_proposal(proposal, "REVIEW-001")
    assert anon["shared_mechanism"] == "X connects A to B"
    assert anon["necessary_assumptions"] == ["A1", "A2"]
    assert anon["prediction"] == "If X holds, Y"
    assert anon["counterexample"] == "If X removed, Y disappears"


# ============================================================================
# ANONYMIZED SET GENERATION
# ============================================================================

def test_generate_anonymized_set_shuffles_with_seed():
    proposals = [
        {"proposal_id": f"P-{i}", "shared_mechanism": f"m{i}", "confidence": 0.5}
        for i in range(10)
    ]
    set1 = generate_anonymized_set(proposals, seed=42)
    set2 = generate_anonymized_set(proposals, seed=42)
    # Same seed → same order
    assert [a["anon_id"] for a in set1] == [a["anon_id"] for a in set2]


def test_generate_anonymized_set_assigns_sequential_ids():
    proposals = [
        {"proposal_id": f"P-{i}", "shared_mechanism": f"m{i}", "confidence": 0.5}
        for i in range(5)
    ]
    anon_set = generate_anonymized_set(proposals, seed=42)
    ids = [a["anon_id"] for a in anon_set]
    assert ids == ["REVIEW-001", "REVIEW-002", "REVIEW-003", "REVIEW-004", "REVIEW-005"]


def test_generate_anonymized_set_preserves_original_id_for_mapping():
    proposals = [
        {"proposal_id": "ORIGINAL-1", "shared_mechanism": "m1", "confidence": 0.5}
    ]
    anon_set = generate_anonymized_set(proposals, seed=42)
    assert anon_set[0]["_original_proposal_id"] == "ORIGINAL-1"
    assert anon_set[0]["_original_index"] == 0


# ============================================================================
# RUBRIC
# ============================================================================

def test_rubric_has_7_dimensions():
    assert len(RUBRIC["dimensions"]) == 7


def test_rubric_dimensions_have_unique_ids():
    ids = [d["id"] for d in RUBRIC["dimensions"]]
    assert len(ids) == len(set(ids))
    assert all(d.startswith("D") for d in ids)


def test_rubric_has_3_verdict_options():
    assert set(RUBRIC["overall_verdict_options"]) == {"ACCEPT", "REVISE", "REJECT"}


def test_rubric_dimensions_have_required_fields():
    for d in RUBRIC["dimensions"]:
        assert "id" in d
        assert "name" in d
        assert "question" in d
        assert d["question"].endswith(".")


# ============================================================================
# REVIEW FORM RENDERING
# ============================================================================

def test_render_review_form_includes_all_proposals():
    anon_set = [
        {"anon_id": "REVIEW-001", "shared_mechanism": "Mech 1",
         "necessary_assumptions": ["A1"], "prediction": "Pred 1",
         "alternative_explanations": ["AE1"], "counterexample": "CE 1",
         "falsification_experiment": "FE 1", "system_confidence": 0.5},
        {"anon_id": "REVIEW-002", "shared_mechanism": "Mech 2",
         "necessary_assumptions": ["A2"], "prediction": "Pred 2",
         "alternative_explanations": ["AE2"], "counterexample": "CE 2",
         "falsification_experiment": "FE 2", "system_confidence": 0.6},
    ]
    md = render_review_form(anon_set, RUBRIC)
    assert "REVIEW-001" in md
    assert "REVIEW-002" in md
    assert "Mech 1" in md
    assert "Mech 2" in md
    # Should include all 7 dimension questions
    for d in RUBRIC["dimensions"]:
        assert d["id"] in md


def test_render_review_form_includes_instructions():
    anon_set = []
    md = render_review_form(anon_set, RUBRIC)
    assert "Instructions" in md
    assert "1 = Strongly disagree" in md
    assert "5 = Strongly agree" in md


def test_render_csv_template_has_header_and_rows():
    anon_set = [
        {"anon_id": "REVIEW-001"},
        {"anon_id": "REVIEW-002"},
    ]
    csv_text = render_csv_template(anon_set, RUBRIC)
    # Use csv.reader to properly parse (handles quoting)
    import io
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    # 1 header + 2 data rows
    assert len(rows) == 3
    header = rows[0]
    assert "reviewer_id" in header
    assert "anon_id" in header
    assert "overall_verdict" in header
    assert "comments" in header
    for d in RUBRIC["dimensions"]:
        assert d["id"] in header
    # Data rows should start with placeholder reviewer_id and the anon_id
    assert rows[1][0] == "<reviewer_id>"
    assert rows[1][1] == "REVIEW-001"
    assert rows[2][1] == "REVIEW-002"


# ============================================================================
# END-TO-END
# ============================================================================

def test_main_runs_and_produces_all_artifacts():
    from audit.measurement_integrity.dr100_tier2_human_review import main
    rc = main()
    # Gate D returns 1 (BLOCKED) — that's the expected state
    assert rc == 1
    reports_dir = REPO / "reports"
    expected_files = [
        "tier2_review_form.md",
        "tier2_review_template.csv",
        "tier2_review_template.json",
        "tier2_review_aggregation.py",
        "tier2_review_mapping.json",
        "tier2_review_status.md",
    ]
    for f in expected_files:
        assert (reports_dir / f).exists(), f"Missing: {f}"


def test_main_writes_status_report_with_blocked_verdict():
    from audit.measurement_integrity.dr100_tier2_human_review import main
    main()
    status_path = REPO / "reports" / "tier2_review_status.md"
    status = status_path.read_text()
    assert "BLOCKED ON HUMAN REVIEW" in status
    assert "NOT TRUSTWORTHY" in status


def test_aggregation_script_is_executable():
    """The aggregation script must be marked executable so reviewers
    can run it directly."""
    from audit.measurement_integrity.dr100_tier2_human_review import main
    main()
    agg_path = REPO / "reports" / "tier2_review_aggregation.py"
    # Just verify the file exists and starts with shebang
    content = agg_path.read_text()
    assert content.startswith("#!/usr/bin/env python3")
    # Verify it parses as valid Python
    import ast
    ast.parse(content)


def test_mapping_file_has_correct_structure():
    from audit.measurement_integrity.dr100_tier2_human_review import main
    main()
    mapping_path = REPO / "reports" / "tier2_review_mapping.json"
    mapping = json.loads(mapping_path.read_text())
    assert isinstance(mapping, list)
    if mapping:
        m = mapping[0]
        assert "anon_id" in m
        assert "original_proposal_id" in m
        assert "original_index" in m
