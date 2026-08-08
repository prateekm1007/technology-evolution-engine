"""Tests: Phase 4 regeneration epistemic accounting (audit round 8).

Per audit round 8:

    "REGENERATED_AND_MATCHED is still too strong. It conventionally means
     'independently regenerated and compared.' But what actually happened
     was one fresh aggregate computation where 36/38 matched."

    "Add a machine test that rejects INDEPENDENTLY_REGENERATED or equivalent
     claims when the only evidence is an aggregate/shared-run artifact."

The valid two-dimensional state is:
    regeneration_status: NOT_INDEPENDENTLY_VERIFIED | FAILED
    shared_run_comparison: MATCHED | MISMATCHED
    independent_regeneration: false (for all — no independent regen done)

Forbidden:
    regeneration_status: PASSED, REGENERATED_AND_MATCHED, INDEPENDENTLY_REGENERATED
    (unless independent_regeneration=true with per-metric artifact)
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO / "reports" / "phase4" / "metric_inventory.json"

VALID_REGENERATION_STATUSES = {
    "NOT_INDEPENDENTLY_VERIFIED",
    "FAILED",
}

VALID_SHARED_RUN_COMPARISONS = {
    "MATCHED",
    "MISMATCHED",
}

FORBIDDEN_REGENERATION_STATUSES = {
    "PASSED",
    "PASS",
    "VERIFIED",
    "REPRODUCED",
    "REGENERATED_AND_MATCHED",  # forbidden per round 8 — too strong
    "INDEPENDENTLY_REGENERATED",  # forbidden unless independent_regeneration=true
    "INDEPENDENTLY_REGENERATED_AND_MATCHED",
}


def test_no_unsupported_regeneration_claims():
    """The metric inventory must NOT use 'PASSED', 'REGENERATED_AND_MATCHED',
    or 'INDEPENDENTLY_REGENERATED' as regeneration_status.

    These conventionally mean 'independently regenerated and compared,'
    but Phase 3 was a shared aggregate run, not independent per-metric
    regeneration. Per audit round 8, the status must be self-explanatory
    without caveats.
    """
    assert INVENTORY_PATH.exists(), "metric_inventory.json must exist"

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        status = metric.get("regeneration_status", "")

        for forbidden in FORBIDDEN_REGENERATION_STATUSES:
            assert status != forbidden, (
                f"Metric {mid} has regeneration_status={repr(status)}. "
                f"The value {repr(forbidden)} is forbidden per audit round 8. "
                f"It conventionally means 'independently regenerated' but Phase 3 "
                f"was a shared aggregate run. Use NOT_INDEPENDENTLY_VERIFIED "
                f"or FAILED instead. "
                f"Governing principle: matching in a shared run is necessary "
                f"but not sufficient for independent reproducibility."
            )

        assert status in VALID_REGENERATION_STATUSES, (
            f"Metric {mid} has regeneration_status={repr(status)}. "
            f"Must be one of {VALID_REGENERATION_STATUSES}."
        )


def test_shared_run_comparison_is_separate_field():
    """Every metric must have shared_run_comparison as a SEPARATE field
    from regeneration_status. The two dimensions must not be conflated.

    Per audit round 8:
        "Use a distinct state... or, even cleaner:
         REPRODUCTION_STATUS = NOT_INDEPENDENTLY_VERIFIED
         SHARED_RUN_COMPARISON = MATCHED"
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        src = metric.get("shared_run_comparison")

        assert src is not None, (
            f"Metric {mid} missing shared_run_comparison field. "
            f"This must be a separate field from regeneration_status."
        )
        assert src in VALID_SHARED_RUN_COMPARISONS, (
            f"Metric {mid} has shared_run_comparison={repr(src)}. "
            f"Must be one of {VALID_SHARED_RUN_COMPARISONS}."
        )


def test_independent_regeneration_is_false_for_all():
    """No metric may have independent_regeneration=true.

    Phase 3 was a shared aggregate run. No metric has been independently
    regenerated. Per audit round 8, point 5: add independent_regeneration=false
    to all shared-run metrics.
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        ir = metric.get("independent_regeneration")

        assert ir is False, (
            f"Metric {mid} has independent_regeneration={repr(ir)}. "
            f"No metric has been independently regenerated. Phase 3 was a "
            f"shared aggregate run. independent_regeneration must be false."
        )


def test_shared_run_cannot_claim_independent_regeneration():
    """If a metric's evidence source is an aggregate/shared-run artifact,
    it must NOT claim independent regeneration.

    This is the core audit round 8 test. A shared-run artifact
    (reports/phase3/regeneration_result.json from bootstrap_all_metrics)
    cannot prove independent per-metric regeneration.
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        evidence = metric.get("regeneration_evidence", {})
        artifact = evidence.get("fresh_output_artifact", "")
        independent = metric.get("independent_regeneration", False)

        # If the artifact is the shared Phase 3 aggregate output,
        # independent_regeneration must be false
        if "phase3/regeneration_result" in artifact:
            assert independent is False, (
                f"Metric {mid} claims independent_regeneration=true but its "
                f"evidence artifact is {artifact} — a shared aggregate run "
                f"output. A shared-run artifact cannot prove independent "
                f"per-metric regeneration. Per audit round 8: the governing "
                f"principle is that absence of a failed regeneration is not "
                f"evidence of successful regeneration."
            )


def test_no_metric_is_scientifically_eligible():
    """No metric may be scientifically_eligible=true.

    Scientific eligibility requires INDEPENDENT regeneration, not just
    shared-run matching. No metric has been independently regenerated.
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        eligible = metric.get("scientifically_eligible", False)

        assert eligible is False, (
            f"Metric {mid} is scientifically_eligible=true. No metric has "
            f"been independently regenerated. Scientific eligibility requires "
            f"independent per-metric regeneration, not shared-run matching."
        )


def test_m008_is_quarantined_with_mismatched_shared_run():
    """M-008 must be QUARANTINED with regeneration_status=FAILED and
    shared_run_comparison=MISMATCHED."""
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None, "M-008 must be in the inventory"
    assert m008["regeneration_status"] == "FAILED"
    assert m008["shared_run_comparison"] == "MISMATCHED"
    assert m008["measurement_usability"] == "QUARANTINED"
    assert m008["scientifically_eligible"] is False
    assert m008["used_for_scientific_decision"] == "NO"
    assert m008["independent_regeneration"] is False

    quarantine = m008.get("quarantine", {})
    assert quarantine.get("value_deleted") == "NO"
    assert quarantine.get("value_replaced") == "NO"
    assert quarantine.get("values_averaged") == "NO"


def test_provenance_declared_vs_verified_distinction():
    """Every metric must have provenance.provenance_declared and
    provenance.provenance_verified as separate fields.

    provenance_verified must be false — no metric has been
    cryptographically verified.
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    for metric in metrics:
        mid = metric.get("metric_id", "?")
        provenance = metric.get("provenance", {})

        assert "provenance_declared" in provenance, (
            f"Metric {mid} missing provenance.provenance_declared"
        )
        assert "provenance_verified" in provenance, (
            f"Metric {mid} missing provenance.provenance_verified"
        )
        assert provenance["provenance_verified"] is False, (
            f"Metric {mid} has provenance_verified=true. No metric has been "
            f"independently provenance-verified. Declared provenance is not "
            f"verified provenance."
        )


def test_m008_rng_topology_recorded():
    """M-008 must have its RNG topology recorded per audit round 8, point 9."""
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None
    quarantine = m008.get("quarantine", {})
    determinism = quarantine.get("determinism_analysis", {})

    assert "rng_topology" in determinism, "M-008 must have rng_topology recorded"
    rng = determinism["rng_topology"]
    assert "module-scoped" in rng["rng_instance"], (
        f"M-008 rng_instance must mention 'module-scoped', got: {rng['rng_instance']}"
    )
    assert rng["seed"] == 42
    assert "consumes RNG state" in rng["point_estimate_call"]
    assert "continue the SAME RNG stream" in rng["bootstrap_calls"]

    # RNG modification prohibition must be recorded
    assert "rng_modification_prohibition" in determinism, (
        "M-008 must record rng_modification_prohibition per audit round 8, point 8"
    )


def test_m008_determinism_statement_is_conditional_not_causal():
    """M-008's determinism statement must be conditional (not claim the
    cause of the discrepancy has been identified).

    Per audit round 8, point 10:
        "Do not claim the cause of the 0.9189 → 0.8889 discrepancy has
         been identified."
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())
    metrics = inventory.get("metrics", [])

    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None
    quarantine = m008.get("quarantine", {})
    determinism = quarantine.get("determinism_analysis", {})

    # The determinism statement must be conditional
    statement = determinism.get("determinism_statement", "")
    assert "CONDITIONAL ON" in statement or "conditional on" in statement, (
        "M-008 determinism statement must be conditional, not absolute"
    )

    # Must explicitly state what has NOT been established
    not_established = determinism.get("what_has_NOT_been_established", "")
    assert "NOT been identified" in not_established or "not been identified" in not_established, (
        "M-008 must explicitly state that the cause has NOT been identified"
    )


def test_m008_causal_attribution_not_claimed():
    """M-008 must NOT claim the cause of the discrepancy has been established.

    Per audit round 9:
        "Replace 'The discrepancy from input change' with 'The discrepancy
         is consistent with at least one effective-input or environment
         difference; causal attribution remains open.'"

    The repository must distinguish:
        DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS (true)
    from:
        CAUSE_OF_DISCREPANCY_ESTABLISHED (must be false)

    And M-008 must be marked RECONCILIATION_OPEN.
    """
    assert INVENTORY_PATH.exists()

    inventory = json.loads(INVENTORY_PATH.read_text())

    # Check the m008_quarantine_summary
    m008_summary = inventory.get("m008_quarantine_summary", {})
    assert m008_summary.get("CAUSE_OF_DISCREPANCY_ESTABLISHED") is False, (
        "M-008 must have CAUSE_OF_DISCREPANCY_ESTABLISHED=false. "
        "Causal attribution has NOT been established. The discrepancy is "
        "consistent with at least one effective-input or environment "
        "difference, but the specific cause has not been identified."
    )
    assert m008_summary.get("DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS") is True, (
        "M-008 must have DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS=true. "
        "This is the narrow claim the evidence supports."
    )
    assert m008_summary.get("RECONCILIATION_STATUS") == "RECONCILIATION_OPEN", (
        "M-008 must have RECONCILIATION_STATUS=RECONCILIATION_OPEN. "
        "The discrepancy has not been reconciled."
    )

    # Check the per-metric determinism_analysis
    metrics = inventory.get("metrics", [])
    m008 = None
    for m in metrics:
        if m.get("metric_id") == "M-008":
            m008 = m
            break

    assert m008 is not None
    quarantine = m008.get("quarantine", {})
    determinism = quarantine.get("determinism_analysis", {})

    assert determinism.get("CAUSE_OF_DISCREPANCY_ESTABLISHED") is False, (
        "M-008 determinism_analysis must have CAUSE_OF_DISCREPANCY_ESTABLISHED=false"
    )
    assert determinism.get("DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS") is True, (
        "M-008 determinism_analysis must have DETERMINISTIC_UNDER_IDENTICAL_EFFECTIVE_INPUTS=true"
    )
    assert determinism.get("RECONCILIATION_STATUS") == "RECONCILIATION_OPEN", (
        "M-008 determinism_analysis must have RECONCILIATION_STATUS=RECONCILIATION_OPEN"
    )

    # Check that the wording does NOT claim the cause has been identified
    determinism_text = json.dumps(determinism).lower()
    forbidden_phrases = [
        "discrepancy must come from",
        "must come from a change in",
        "discrepancy from input change",
        "cause has been identified",
        "cause is",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in determinism_text, (
            f"M-008 determinism analysis contains forbidden phrase '{phrase}'. "
            f"This implies causal attribution has been established, which it has NOT. "
            f"Per audit round 9: use 'consistent with at least one effective-input "
            f"or environment difference; causal attribution remains open.'"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
