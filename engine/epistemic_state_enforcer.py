"""epistemic_state_enforcer.py — Machine-enforce metric epistemic states.

Per the 18-phase plan:
    "Phase 6: Enforce epistemic states"

Per audit round 11:
    "Phase 6 must enforce epistemic states mechanically, not merely
     create another report saying that the states exist."

Per MEASUREMENT_CONSTITUTION.md:
    "A metric that violates any rule is BLOCKED from use in capability
     claims until the violation is resolved."

This module provides the machine enforcement. Every access to a metric
for scientific use MUST pass through assert_metric_eligible_for_scientific_use().
If the metric is quarantined or not scientifically eligible, the call
raises MetricNotEligible and the scientific operation cannot proceed.

Epistemic states (per Phase 4/5):
    SCIENTIFICALLY_ELIGIBLE — metric may be used in scientific decisions
    REPRODUCED_IN_SHARED_RUN — matched in shared run, NOT independently verified
    QUARANTINED — regeneration failed, cannot be used for any purpose

Currently:
    0 metrics are SCIENTIFICALLY_ELIGIBLE
    37 metrics are REPRODUCED_IN_SHARED_RUN (provisional quarantine)
    1 metric is QUARANTINED (M-008, regeneration failed)

ALL 38 metrics are forbidden for scientific use until independently
regenerated. This module enforces that.

Usage in scientific code:

    from engine.epistemic_state_enforcer import assert_metric_eligible_for_scientific_use
    assert_metric_eligible_for_scientific_use("M-005")  # raises if not eligible

    # Only after this assertion passes may the metric be used in a
    # scientific decision.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


REPO = Path(__file__).resolve().parents[1]
QUARANTINE_MANIFEST = REPO / "reports" / "phase5" / "forbidden_metrics_quarantine.json"
PHASE4_INVENTORY = REPO / "reports" / "phase4" / "metric_inventory.json"


class MetricNotEligible(Exception):
    """Raised when a metric is accessed for scientific use but is not
    SCIENTIFICALLY_ELIGIBLE.

    This is a hard failure. The scientific operation cannot proceed.
    """


class MetricNotFound(Exception):
    """Raised when a metric ID is not found in the inventory."""


def _load_quarantine_manifest() -> dict:
    """Load the Phase 5 quarantine manifest."""
    if not QUARANTINE_MANIFEST.exists():
        return {"forbidden_metrics": []}
    return json.loads(QUARANTINE_MANIFEST.read_text())


def _load_phase4_inventory() -> dict:
    """Load the Phase 4 metric inventory."""
    if not PHASE4_INVENTORY.exists():
        return {"metrics": []}
    return json.loads(PHASE4_INVENTORY.read_text())


def get_metric_epistemic_state(metric_id: str) -> dict:
    """Get the epistemic state of a metric.

    Returns a dict with:
        metric_id: str
        scientifically_eligible: bool
        measurement_usability: str (QUARANTINED / REPRODUCED_IN_SHARED_RUN / etc.)
        regeneration_status: str
        shared_run_comparison: str
        independent_regeneration: bool
        forbidden_reasons: list[str]
        quarantine_severity: str (FULL / PROVISIONAL / NONE)
    """
    quarantine = _load_quarantine_manifest()
    for m in quarantine.get("forbidden_metrics", []):
        if m.get("metric_id") == metric_id:
            return {
                "metric_id": metric_id,
                "scientifically_eligible": m.get("scientifically_eligible", False),
                "measurement_usability": m.get("measurement_usability", "UNKNOWN"),
                "regeneration_status": m.get("regeneration_status", "UNKNOWN"),
                "shared_run_comparison": m.get("shared_run_comparison", "UNKNOWN"),
                "independent_regeneration": m.get("independent_regeneration", False),
                "forbidden_reasons": m.get("forbidden_reasons", []),
                "quarantine_severity": m.get("quarantine_severity", "UNKNOWN"),
            }

    # If not in quarantine manifest, check Phase 4 inventory
    inventory = _load_phase4_inventory()
    for m in inventory.get("metrics", []):
        if m.get("metric_id") == metric_id:
            return {
                "metric_id": metric_id,
                "scientifically_eligible": m.get("scientifically_eligible", False),
                "measurement_usability": m.get("measurement_usability", "UNKNOWN"),
                "regeneration_status": m.get("regeneration_status", "UNKNOWN"),
                "shared_run_comparison": m.get("shared_run_comparison", "UNKNOWN"),
                "independent_regeneration": m.get("independent_regeneration", False),
                "forbidden_reasons": [],
                "quarantine_severity": "NONE",
            }

    raise MetricNotFound(f"Metric {metric_id} not found in inventory or quarantine manifest")


def assert_metric_eligible_for_scientific_use(metric_id: str) -> None:
    """Assert that a metric is eligible for scientific use.

    Raises MetricNotEligible if the metric is:
    - Not SCIENTIFICALLY_ELIGIBLE (all 38 metrics currently fail this)
    - QUARANTINED (M-008)
    - Not independently regenerated (all 37 others)
    - Not in the inventory at all (MetricNotFound)

    This is the machine enforcement. Every scientific code path that
    accesses a metric MUST call this before using the metric value.
    """
    try:
        state = get_metric_epistemic_state(metric_id)
    except MetricNotFound:
        raise MetricNotEligible(
            f"Metric {metric_id} is not in the inventory. "
            f"Unknown metrics cannot be used in scientific decisions."
        )

    if not state["scientifically_eligible"]:
        reasons = state.get("forbidden_reasons", [])
        if not reasons:
            reasons = ["NOT_SCIENTIFICALLY_ELIGIBLE"]

        if state["quarantine_severity"] == "FULL":
            raise MetricNotEligible(
                f"Metric {metric_id} is FULLY QUARANTINED and cannot be used "
                f"in any scientific decision. Reasons: {reasons}. "
                f"Regeneration status: {state['regeneration_status']}. "
                f"This metric failed regeneration and its value is untrusted "
                f"until reconciled. Per MC-5/MC-6: no quarantined metric may "
                f"be used in capability claims."
            )
        elif state["quarantine_severity"] == "PROVISIONAL":
            raise MetricNotEligible(
                f"Metric {metric_id} is PROVISIONALLY QUARANTINED and cannot "
                f"be used in scientific decisions. Reasons: {reasons}. "
                f"The metric matched in a shared run but has NOT been "
                f"independently regenerated. Per the epistemic ladder: "
                f"REPRODUCED_IN_SHARED_RUN is not SCIENTIFICALLY_ELIGIBLE. "
                f"Independent regeneration is required before scientific use."
            )
        else:
            raise MetricNotEligible(
                f"Metric {metric_id} is not SCIENTIFICALLY_ELIGIBLE. "
                f"Reasons: {reasons}. "
                f"Current state: {state['measurement_usability']}. "
                f"Scientific use requires independent regeneration."
            )


def assert_metric_not_quarantined(metric_id: str) -> None:
    """Assert that a metric is not quarantined (but may still be provisional).

    This is a weaker check than assert_metric_eligible_for_scientific_use.
    It allows PROVISIONAL metrics but blocks FULLY QUARANTINED ones.

    Use this for non-scientific operations (e.g., inventory, reporting)
    where provisional metrics are acceptable but quarantined ones are not.
    """
    try:
        state = get_metric_epistemic_state(metric_id)
    except MetricNotFound:
        raise MetricNotEligible(
            f"Metric {metric_id} is not in the inventory."
        )

    if state["quarantine_severity"] == "FULL":
        raise MetricNotEligible(
            f"Metric {metric_id} is FULLY QUARANTINED. "
            f"Reasons: {state.get('forbidden_reasons', [])}. "
            f"Even non-scientific operations cannot use fully quarantined metrics."
        )


def list_eligible_metrics() -> list[str]:
    """List all metrics that are SCIENTIFICALLY_ELIGIBLE.

    Currently returns an empty list — no metric is eligible.
    """
    quarantine = _load_quarantine_manifest()
    eligible = []
    for m in quarantine.get("forbidden_metrics", []):
        if m.get("scientifically_eligible") is True:
            eligible.append(m.get("metric_id"))
    return eligible


def list_quarantined_metrics() -> list[str]:
    """List all metrics that are FULLY QUARANTINED."""
    quarantine = _load_quarantine_manifest()
    return [m.get("metric_id") for m in quarantine.get("forbidden_metrics", [])
            if m.get("quarantine_severity") == "FULL"]


def list_provisionally_quarantined_metrics() -> list[str]:
    """List all metrics that are PROVISIONALLY QUARANTINED."""
    quarantine = _load_quarantine_manifest()
    return [m.get("metric_id") for m in quarantine.get("forbidden_metrics", [])
            if m.get("quarantine_severity") == "PROVISIONAL"]


__all__ = [
    "MetricNotEligible",
    "MetricNotFound",
    "get_metric_epistemic_state",
    "assert_metric_eligible_for_scientific_use",
    "assert_metric_not_quarantined",
    "list_eligible_metrics",
    "list_quarantined_metrics",
    "list_provisionally_quarantined_metrics",
]


if __name__ == "__main__":
    import sys

    # CLI: python3 -m engine.epistemic_state_enforcer <metric_id>
    if len(sys.argv) < 2:
        print("Usage: python3 -m engine.epistemic_state_enforcer <metric_id>")
        print(f"  Eligible metrics: {list_eligible_metrics()}")
        print(f"  Quarantined metrics: {list_quarantined_metrics()}")
        print(f"  Provisionally quarantined: {len(list_provisionally_quarantined_metrics())} metrics")
        sys.exit(0)

    mid = sys.argv[1]
    try:
        assert_metric_eligible_for_scientific_use(mid)
        print(f"ELIGIBLE: {mid}")
        sys.exit(0)
    except MetricNotEligible as e:
        print(f"NOT ELIGIBLE: {mid}")
        print(str(e))
        sys.exit(1)
