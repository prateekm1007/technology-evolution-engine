#!/usr/bin/env python3
"""phase5_quarantine_forbidden_metrics.py — Quarantine forbidden metrics (Phase 5).

Per the 18-phase plan:
    "Phase 5: Quarantine forbidden metrics"

Per STOP_BUILDING.md:
    - Benchmark tuning is forbidden permanently (No-Gaming Rule)
    - Score improvements without capability improvement are forbidden (Prime Directive)

Per MEASUREMENT_CONSTITUTION.md:
    - MC-5: FP floor > 5% blocks discovery claims (M-008 is the FP floor)
    - MC-6: No metric may be silently altered
    - MC-7: No naked numbers (every score needs full provenance)
    - MC-8: Bootstrap uncertainty required

Per Phase 4 findings:
    - M-008: QUARANTINED (REGENERATION_FAILED, RECONCILIATION_OPEN)
    - 37 other metrics: NOT_INDEPENDENTLY_VERIFIED (shared_run_comparison=MATCHED)
    - 0 metrics: SCIENTIFICALLY_ELIGIBLE

Phase 5 identifies ALL metrics that are FORBIDDEN for scientific use:
    1. M-008 — quarantined (regeneration failed)
    2. All 37 others — not independently verified (shared-run only)
    3. Any metric that violates MC-5/MC-6/MC-7/MC-8

The quarantine is machine-enforced. No forbidden metric may be used in
any scientific decision until it becomes SCIENTIFICALLY_ELIGIBLE (which
requires independent regeneration, not shared-run matching).

Output: reports/phase5/forbidden_metrics_quarantine.json
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUTPUT = REPO / "reports" / "phase5" / "forbidden_metrics_quarantine.json"


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip()


def load_phase4_inventory():
    """Load the Phase 4 metric inventory."""
    path = REPO / "reports" / "phase4" / "metric_inventory.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_compliance_report():
    """Load the historical measurement constitution compliance report."""
    path = REPO / "reports" / "measurement_constitution_m8.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def identify_forbidden_metrics(phase4_inventory, compliance_report):
    """Identify all metrics forbidden for scientific use.

    A metric is FORBIDDEN for scientific use if ANY of:
    1. regeneration_status = FAILED (quarantined, e.g., M-008)
    2. independent_regeneration = false (not independently verified)
    3. scientifically_eligible = false
    4. measurement_usability = QUARANTINED

    Since Phase 4 established that ALL 38 metrics have:
    - independent_regeneration = false
    - scientifically_eligible = false

    ALL 38 metrics are forbidden for scientific use until independently
    regenerated. This is the honest epistemic state.
    """
    metrics = phase4_inventory.get("metrics", [])
    forbidden = []

    for m in metrics:
        mid = m.get("metric_id")
        reasons = []

        if m.get("regeneration_status") == "FAILED":
            reasons.append("REGENERATION_FAILED")

        if m.get("independent_regeneration") is False:
            reasons.append("NOT_INDEPENDENTLY_REGENERATED")

        if m.get("scientifically_eligible") is False:
            reasons.append("NOT_SCIENTIFICALLY_ELIGIBLE")

        if m.get("measurement_usability") == "QUARANTINED":
            reasons.append("QUARANTINED")

        if m.get("shared_run_comparison") == "MISMATCHED":
            reasons.append("SHARED_RUN_MISMATCHED")

        # All metrics are forbidden until independently regenerated
        forbidden.append({
            "metric_id": mid,
            "metric_name": m.get("metric_name", ""),
            "forbidden_for_scientific_use": True,
            "forbidden_reasons": reasons,
            "current_epistemic_level": m.get("epistemic_level", "UNKNOWN"),
            "regeneration_status": m.get("regeneration_status"),
            "shared_run_comparison": m.get("shared_run_comparison"),
            "independent_regeneration": m.get("independent_regeneration"),
            "scientifically_eligible": m.get("scientifically_eligible"),
            "measurement_usability": m.get("measurement_usability"),
            "critical_path_for_matcher_discrimination": m.get("critical_path_for_matcher_discrimination", False),
            "quarantine_severity": "FULL" if m.get("measurement_usability") == "QUARANTINED" else "PROVISIONAL",
        })

    return forbidden


def main():
    print("Phase 5: Quarantine Forbidden Metrics")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Git HEAD: {git_head()}")
    print()

    phase4 = load_phase4_inventory()
    if not phase4:
        print("ERROR: Could not load Phase 4 metric inventory")
        return 1

    compliance = load_compliance_report()

    forbidden = identify_forbidden_metrics(phase4, compliance)

    # Summary
    total = len(forbidden)
    fully_quarantined = sum(1 for f in forbidden if f["quarantine_severity"] == "FULL")
    provisionally_quarantined = sum(1 for f in forbidden if f["quarantine_severity"] == "PROVISIONAL")
    critical_path_forbidden = sum(1 for f in forbidden if f["critical_path_for_matcher_discrimination"])

    print(f"Total metrics: {total}")
    print(f"Fully quarantined (regeneration failed): {fully_quarantined}")
    print(f"Provisionally quarantined (not independently verified): {provisionally_quarantined}")
    print(f"Critical path metrics forbidden: {critical_path_forbidden}")
    print(f"Metrics eligible for scientific use: 0")

    result = {
        "phase": 5,
        "phase_name": "Quarantine forbidden metrics",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "summary": {
            "total_metrics": total,
            "fully_quarantined": fully_quarantined,
            "provisionally_quarantined": provisionally_quarantined,
            "critical_path_forbidden": critical_path_forbidden,
            "scientifically_eligible": 0,
            "note": "ALL 38 metrics are forbidden for scientific use. 1 is fully quarantined (M-008, regeneration failed). 37 are provisionally quarantined (not independently regenerated — shared-run matching only). 0 are scientifically eligible. No metric may be used in a scientific decision until independently regenerated.",
        },
        "quarantine_categories": {
            "FULL_QUARANTINE": {
                "description": "Metric failed regeneration. Historical value preserved but untrusted. Cannot be used for any purpose until reconciled.",
                "metrics": [f["metric_id"] for f in forbidden if f["quarantine_severity"] == "FULL"],
                "count": fully_quarantined,
            },
            "PROVISIONAL_QUARANTINE": {
                "description": "Metric matched in a shared run but has NOT been independently regenerated. Cannot be used for scientific decisions until independent regeneration passes.",
                "metrics": [f["metric_id"] for f in forbidden if f["quarantine_severity"] == "PROVISIONAL"],
                "count": provisionally_quarantined,
            },
        },
        "forbidden_metrics": forbidden,
        "compliance_report_status": {
            "historical_report": "reports/measurement_constitution_m8.json",
            "historical_verdict": compliance.get("gate_verdict", "UNKNOWN") if compliance else "NOT_FOUND",
            "historical_all_pass": compliance.get("all_metrics_pass", None) if compliance else None,
            "current_status": "STALE — the historical compliance report was generated before Phase 3 found the M-008 regeneration failure. It reports 304/304 checks PASS, but this is no longer accurate. M-008 is now quarantined. The compliance report must be regenerated after M-008 reconciliation.",
            "note": "The historical compliance report is preserved (MC-6: no metric may be silently altered). It is not modified or deleted. It is marked STALE because it does not reflect the current epistemic state.",
        },
        "machine_enforced": True,
        "no_retroactive_repair": True,
        "no_value_deletion": True,
        "no_value_replacement": True,
        "no_value_averaging": True,
        "governing_principle": "No metric may be used in a scientific decision until it is SCIENTIFICALLY_ELIGIBLE, which requires independent regeneration (not shared-run matching). Absence of a failed regeneration is not evidence of successful regeneration.",
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, default=str))
    print(f"\nQuarantine manifest written to {OUTPUT}")
    print(f"\nAll {total} metrics are forbidden for scientific use until independently regenerated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
