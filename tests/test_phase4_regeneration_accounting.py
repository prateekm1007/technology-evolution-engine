"""Test: no unsupported regeneration_status=PASSED claims (audit round 7).

Per audit round 7:

    "Add a machine test that fails if regeneration_status=PASSED exists
     without a corresponding fresh-output artifact and comparison record."

    "The governing principle is: absence of a failed regeneration is not
     evidence of successful regeneration."

This test verifies that the metric inventory does NOT use 'PASSED' as a
regeneration_status. The valid values are:
    REGENERATED_AND_MATCHED (with fresh-output artifact + comparison record)
    REGENERATED_AND_FAILED
    NOT_INDEPENDENTLY_REGENERATED

The old 'PASSED' value is forbidden because it conflates 'produced by a
fresh run' with 'independently regenerated and compared'.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO / "reports" / "phase4" / "metric_inventory.json"

VALID_REGENERATION_STATUSES = {
    "REGENERATED_AND_MATCHED",
    "REGENERATED_AND_FAILED",
    "NOT_INDEPENDENTLY_REGENERATED",
}

FORBIDDEN_REGENERATION_STATUSES = {
    "PASSED",
    "PASS",
    "VERIFIED",
    "REPRODUCED",
}


def test_no_unsupported_regeneration_passed_claims():
    """The metric inventory must NOT use 'PASSED' as a regeneration_status.

    'PASSED' conflates 'produced by a fresh run' with 'independently
    regenerated and compared.' Per audit round 7, the governing principle
    is: absence of a failed regeneration is not evidence of successful
    regeneration.

    Valid values:
        REGENERATED_AND_MATCHED — fresh output matched committed (with artifact)
        REGENERATED_AND_FAILED — fresh output did not match
        NOT_INDEPENDENTLY_REGENERATED — no fresh-output comparison exists
    """
    assert INVENTORY_PATH.exists(), "metric_inventory.json must exist"

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        status = metric.get("regeneration_status", "")

        # Check for forbidden values
        for forbidden in FORBIDDEN_REGENERATION_STATUSES:
            assert status != forbidden, (
                f"Metric {mid} has regeneration_status={repr(status)}. "
                f"The value {repr(forbidden)} is forbidden per audit round 7. "
                f"Use REGENERATED_AND_MATCHED, REGENERATED_AND_FAILED, or "
                f"NOT_INDEPENDENTLY_REGENERATED instead. "
                f"Governing principle: absence of a failed regeneration is not "
                f"evidence of successful regeneration."
            )

        # Check that status is one of the valid values
        assert status in VALID_REGENERATION_STATUSES, (
            f"Metric {mid} has regeneration_status={repr(status)}. "
            f"Must be one of {VALID_REGENERATION_STATUSES}."
        )


def test_regenerated_and_matched_has_fresh_output_artifact():
    """Every metric marked REGENERATED_AND_MATCHED must have a
    regeneration_evidence.fresh_output_artifact pointing to an actual
    fresh-output comparison record."""
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        if metric.get("regeneration_status") == "REGENERATED_AND_MATCHED":
            mid = metric.get("metric_id", "?")
            evidence = metric.get("regeneration_evidence", {})
            artifact = evidence.get("fresh_output_artifact")

            assert artifact is not None, (
                f"Metric {mid} is REGENERATED_AND_MATCHED but has no "
                f"fresh_output_artifact in regeneration_evidence. "
                f"A matching claim requires a fresh-output comparison record."
            )

            # Verify the artifact exists on disk
            artifact_path = REPO / artifact
            assert artifact_path.exists(), (
                f"Metric {mid} references fresh_output_artifact={artifact} "
                f"but the file does not exist at {artifact_path}."
            )


def test_no_metric_is_scientifically_eligible_without_independent_regen():
    """No metric may be scientifically_eligible=true unless it has been
    independently regenerated (not just shared-context matched).

    Per audit round 7:
        "Only ACTIVE_VERIFIED should be eligible to support a scientific decision."
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        status = metric.get("regeneration_status", "")
        eligible = metric.get("scientifically_eligible", False)

        if eligible:
            # To be scientifically eligible, the metric must be
            # REGENERATED_AND_MATCHED AND have independent regeneration
            # (not shared context). Currently no metric meets this bar.
            assert status == "REGENERATED_AND_MATCHED", (
                f"Metric {mid} is scientifically_eligible=true but "
                f"regeneration_status={repr(status)}. Only "
                f"REGENERATED_AND_MATCHED metrics can be eligible."
            )
            # Even REGENERATED_AND_MATCHED is not enough — it must be
            # independently regenerated, not shared-context.
            evidence = metric.get("regeneration_evidence", {})
            caveat = evidence.get("caveat", "")
            assert "shared context" not in caveat.lower() or "independent" not in caveat.lower(), (
                f"Metric {mid} is scientifically_eligible=true but its "
                f"regeneration evidence has a shared-context caveat. "
                f"Scientific eligibility requires independent regeneration."
            )


def test_m008_is_quarantined():
    """M-008 must be QUARANTINED with no retroactive repair."""
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None, "M-008 must be in the inventory"
    assert m008["regeneration_status"] == "REGENERATED_AND_FAILED"
    assert m008["measurement_usability"] == "QUARANTINED"
    assert m008["scientifically_eligible"] is False
    assert m008["used_for_scientific_decision"] == "NO"

    quarantine = m008.get("quarantine", {})
    assert quarantine.get("value_deleted") == "NO"
    assert quarantine.get("value_replaced") == "NO"
    assert quarantine.get("values_averaged") == "NO"


def test_provenance_declared_vs_verified_distinction():
    """Every metric must have provenance.provenance_declared and
    provenance.provenance_verified as separate fields.

    Per audit round 7:
        "There is a crucial distinction: PROVENANCE_DECLARED vs PROVENANCE_VERIFIED."
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        provenance = metric.get("provenance", {})

        assert "provenance_declared" in provenance, (
            f"Metric {mid} missing provenance.provenance_declared field"
        )
        assert "provenance_verified" in provenance, (
            f"Metric {mid} missing provenance.provenance_verified field"
        )

        # provenance_verified must be false — no metric has been
        # cryptographically verified yet
        assert provenance["provenance_verified"] is False, (
            f"Metric {mid} has provenance_verified=true. No metric has been "
            f"independently provenance-verified yet. Declared provenance is not "
            f"verified provenance."
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
