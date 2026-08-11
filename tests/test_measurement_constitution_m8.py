"""
test_measurement_constitution_m8.py — Tests for Stage M8 (Measurement Constitution).

Verifies:
  1. MEASUREMENT_CONSTITUTION.md exists with all 8 rules
  2. The compliance checker runs and produces results
  3. All metrics are compliant on all 8 rules
  4. reports/measurement_constitution_m8.json exists with correct structure
  5. The constitution document references M1-M7 stages
"""
import sys
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from programs.A_metrology.measurement_constitution_m8 import (
    CONSTITUTION_RULES, check_compliance, generate_constitution_md,
    ComplianceResult,
)


# ============================================================================
# Constitution rules
# ============================================================================

def test_constitution_has_8_rules():
    """The constitution must have exactly 8 rules."""
    assert len(CONSTITUTION_RULES) == 8


def test_constitution_rules_have_required_fields():
    """Each rule must have rule_id, name, statement, source, enforcement."""
    for rule in CONSTITUTION_RULES:
        assert "rule_id" in rule
        assert "name" in rule
        assert "statement" in rule
        assert "source" in rule
        assert "enforcement" in rule


def test_constitution_rule_ids_are_unique():
    ids = [r["rule_id"] for r in CONSTITUTION_RULES]
    assert len(ids) == len(set(ids))


def test_constitution_includes_all_roadmap_examples():
    """ROADMAP_V2 lists 6 example rules. All 6 must be in the constitution."""
    roadmap_examples = [
        "self-valid",           # MC-1 (self-validation)
        "independent rescoring", # MC-2
        "confidence calibration", # MC-3
        "evidence tier",        # MC-4
        "adversarial",          # MC-5
        "historical permanence", # MC-6
    ]
    all_text = " ".join(r["name"].lower() + " " + r["statement"].lower()
                        for r in CONSTITUTION_RULES)
    for example in roadmap_examples:
        assert example in all_text, (
            f"ROADMAP_V2 example '{example}' not found in constitution"
        )


# ============================================================================
# Constitution document
# ============================================================================

def test_constitution_md_exists():
    """MEASUREMENT_CONSTITUTION.md must exist."""
    assert (REPO / "MEASUREMENT_CONSTITUTION.md").exists()


def test_constitution_md_has_all_8_rules():
    """The document must reference all 8 rule IDs."""
    content = (REPO / "MEASUREMENT_CONSTITUTION.md").read_text()
    for rule in CONSTITUTION_RULES:
        assert rule["rule_id"] in content, (
            f"{rule['rule_id']} not found in MEASUREMENT_CONSTITUTION.md"
        )


def test_constitution_md_references_m1_through_m7():
    """The document must reference Stages M1-M7 (the sources)."""
    content = (REPO / "MEASUREMENT_CONSTITUTION.md").read_text()
    for stage in ("M1", "M2", "M3", "M4", "M6", "M7"):
        assert stage in content, f"Stage {stage} not referenced in constitution"


# ============================================================================
# Compliance check
# ============================================================================

def test_compliance_check_runs():
    """check_compliance() must return a list of ComplianceResult."""
    results = check_compliance()
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, ComplianceResult) for r in results)


def test_compliance_check_covers_all_8_rules():
    """Every rule must be checked for every metric."""
    results = check_compliance()
    rule_ids = {r.rule_id for r in results}
    expected = {rule["rule_id"] for rule in CONSTITUTION_RULES}
    assert rule_ids == expected


def test_all_metrics_compliant():
    """All metrics must be compliant on all 8 rules."""
    results = check_compliance()
    non_compliant = [r for r in results if not r.compliant]
    if non_compliant:
        msgs = [f"{r.rule_id}/{r.metric_id}: {r.evidence}" for r in non_compliant]
        pytest.fail(f"Non-compliant checks:\n  " + "\n  ".join(msgs))


# ============================================================================
# End-to-end: reports exist
# ============================================================================

def test_m8_json_exists():
    """reports/measurement_constitution_m8.json must exist."""
    assert (REPO / "reports" / "measurement_constitution_m8.json").exists()


def test_m8_md_exists():
    """reports/measurement_constitution_m8.md must exist."""
    assert (REPO / "reports" / "measurement_constitution_m8.md").exists()


def test_m8_json_has_required_structure():
    """JSON must have cycle, stage, n_rules, gate_verdict, results."""
    path = REPO / "reports" / "measurement_constitution_m8.json"
    data = json.loads(path.read_text())
    assert data["stage"] == "M8"
    assert data["program"] == "A"
    assert data["n_rules"] == 8
    assert "gate_verdict" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_m8_gate_verdict_is_pass():
    """Gate M8 verdict should be PASS (all metrics compliant)."""
    path = REPO / "reports" / "measurement_constitution_m8.json"
    data = json.loads(path.read_text())
    assert data["gate_verdict"] == "PASS", (
        f"Gate M8 verdict = {data['gate_verdict']}, expected PASS"
    )


def test_m8_all_metrics_pass():
    """All metrics should pass all 8 rules."""
    path = REPO / "reports" / "measurement_constitution_m8.json"
    data = json.loads(path.read_text())
    assert data["all_metrics_pass"] is True


def test_m8_n_non_compliant_is_zero():
    """Non-compliant count should be 0."""
    path = REPO / "reports" / "measurement_constitution_m8.json"
    data = json.loads(path.read_text())
    assert data["n_non_compliant"] == 0
