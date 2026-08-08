"""Test: M-008 causal-attribution-open consistency across all Phase 4 artifacts.

Per audit round 10:

    "The repository should now be explicit that M-008 is not explained yet,
     only narrowed. That distinction needs to remain machine-readable, not
     just prose-readable."

    "Phase 5 can proceed only after that final wording/state consistency
     check is confirmed."

This test verifies that every Phase 4 artifact that references M-008
maintains the causal-attribution-open state:
    CAUSE_OF_DISCREPANCY_ESTABLISHED = false
    RECONCILIATION_STATUS = RECONCILIATION_OPEN
    DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS = true

And that no Phase 4 artifact contains language implying the cause has
been identified.

Artifacts checked:
    - reports/phase4/metric_inventory.json
    - experiments/measurement_discrimination/PHASE_STATUS_phase3.json
    - experiments/measurement_discrimination/PHASE_STATUS_phase4.json
    - reports/phase3/regeneration_result.json
    - reports/program_state/PROGRAM_STATE.json
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]

# Phase 4 artifacts that reference M-008 and must be consistent
PHASE4_ARTIFACTS = [
    REPO / "reports" / "phase4" / "metric_inventory.json",
    REPO / "experiments" / "measurement_discrimination" / "PHASE_STATUS_phase3.json",
    REPO / "experiments" / "measurement_discrimination" / "PHASE_STATUS_phase4.json",
    REPO / "reports" / "phase3" / "regeneration_result.json",
    REPO / "reports" / "program_state" / "PROGRAM_STATE.json",
]

# Phrases that imply causal attribution has been established (forbidden)
FORBIDDEN_CAUSAL_PHRASES = [
    "discrepancy must come from",
    "must come from a change in",
    "discrepancy from input change",
    "cause has been identified",
    "cause is established",
    "explained the discrepancy",
    "root cause is",
    "root cause has been",
]

# Required machine-readable fields for M-008 (must be present in metric_inventory.json)
REQUIRED_M008_FIELDS = {
    "CAUSE_OF_DISCREPANCY_ESTABLISHED": False,
    "RECONCILIATION_STATUS": "RECONCILIATION_OPEN",
    "DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS": True,
}


def test_all_phase4_artifacts_exist():
    """Every Phase 4 artifact that references M-008 must exist."""
    for artifact in PHASE4_ARTIFACTS:
        assert artifact.exists(), (
            f"Phase 4 artifact must exist: {artifact}"
        )


def test_no_phase4_artifact_claims_causal_attribution():
    """No Phase 4 artifact may contain language implying the M-008
    discrepancy cause has been identified.

    Per audit round 10: "the repository should now be explicit that M-008
    is not explained yet, only narrowed."
    """
    for artifact in PHASE4_ARTIFACTS:
        content = artifact.read_text().lower()

        for phrase in FORBIDDEN_CAUSAL_PHRASES:
            # The phrase is forbidden UNLESS it appears in a meta-context
            # (e.g., describing what was replaced, or in a test that checks
            # for the forbidden phrase). We allow it if the surrounding
            # context includes "replaced", "forbidden", "implies", etc.
            # But for simplicity, we check that the phrase does not appear
            # as a positive claim about M-008.

            if phrase in content:
                # Check if this is a meta-reference (allowed) or a claim (forbidden)
                # Meta-references include: "replaced", "forbidden", "implies",
                # "does NOT", "not claim", etc.
                lines_with_phrase = [
                    line for line in content.split("\n") if phrase in line
                ]
                for line in lines_with_phrase:
                    # If the line is describing the correction (meta), it's OK
                    meta_markers = [
                        "replaced", "forbidden", "implies", "does not",
                        "not claim", "must not", "verifies", "checks",
                        "per audit", "which implies",
                    ]
                    is_meta = any(marker in line for marker in meta_markers)
                    if not is_meta:
                        pytest.fail(
                            f"{artifact.name} contains forbidden phrase "
                            f"'{phrase}' in a non-meta context:\n  {line.strip()}\n"
                            f"This implies M-008 causal attribution has been "
                            f"established, which it has NOT. Per audit round 10: "
                            f"M-008 is not explained yet, only narrowed."
                        )


def test_metric_inventory_has_required_m008_fields():
    """The metric_inventory.json must have the required machine-readable
    M-008 fields with the correct values."""
    inventory_path = REPO / "reports" / "phase4" / "metric_inventory.json"
    assert inventory_path.exists()

    inventory = json.loads(inventory_path.read_text())

    # Check the m008_quarantine_summary
    m008_summary = inventory.get("m008_quarantine_summary", {})

    for field, expected_value in REQUIRED_M008_FIELDS.items():
        actual = m008_summary.get(field)
        assert actual == expected_value, (
            f"m008_quarantine_summary.{field} must be {repr(expected_value)}, "
            f"got {repr(actual)}. Per audit round 10: the causal-attribution-open "
            f"state must be machine-readable."
        )

    # Check the per-metric record
    metrics = inventory.get("metrics", [])
    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None, "M-008 must be in the inventory"

    quarantine = m008.get("quarantine", {})
    determinism = quarantine.get("determinism_analysis", {})

    for field, expected_value in REQUIRED_M008_FIELDS.items():
        actual = determinism.get(field)
        assert actual == expected_value, (
            f"M-008 quarantine.determinism_analysis.{field} must be "
            f"{repr(expected_value)}, got {repr(actual)}."
        )


def test_phase4_status_has_required_m008_fields():
    """The PHASE_STATUS_phase4.json must have the required machine-readable
    M-008 fields in its m008_quarantine block."""
    status_path = REPO / "experiments" / "measurement_discrimination" / "PHASE_STATUS_phase4.json"
    assert status_path.exists()

    status = json.loads(status_path.read_text())
    m008 = status.get("m008_quarantine", {})

    for field, expected_value in REQUIRED_M008_FIELDS.items():
        actual = m008.get(field)
        assert actual == expected_value, (
            f"PHASE_STATUS_phase4.json m008_quarantine.{field} must be "
            f"{repr(expected_value)}, got {repr(actual)}."
        )


def test_phase3_status_does_not_explain_m008():
    """The PHASE_STATUS_phase3.json must not claim the M-008 discrepancy
    has been explained."""
    status_path = REPO / "experiments" / "measurement_discrimination" / "PHASE_STATUS_phase3.json"
    assert status_path.exists()

    status = json.loads(status_path.read_text())
    content = json.dumps(status).lower()

    for phrase in FORBIDDEN_CAUSAL_PHRASES:
        # Allow meta-references
        if phrase in content:
            # Check if it's in a meta-context
            lines_with_phrase = [
                line for line in content.split(",") if phrase in line
            ]
            for line in lines_with_phrase:
                meta_markers = [
                    "replaced", "forbidden", "implies", "does not",
                    "not claim", "must not", "verifies", "checks",
                    "per audit", "which implies",
                ]
                is_meta = any(marker in line for marker in meta_markers)
                if not is_meta:
                    pytest.fail(
                        f"PHASE_STATUS_phase3.json contains forbidden phrase "
                        f"'{phrase}' in a non-meta context. M-008 is not "
                        f"explained yet, only narrowed."
                    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
