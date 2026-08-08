#!/usr/bin/env python3
"""phase4_metric_inventory.py — Inventory EVERY measurement metric (Phase 4).

Per audit authorization (round 6):

    "Phase 4 may inventory M-008. It may NOT silently certify M-008.
     The inventory should explicitly include:
       Current stored value
       Fresh regenerated value
       Regeneration status
       Historical provenance
       Measurement usability
       Used for scientific decision
       Value deleted?

    M-008 gets explicit QUARANTINED status — no repair, no deletion,
    no averaging."

This script produces a machine-readable inventory of all 38 measurement
metrics (M-001 through M-306), with full provenance for each and
explicit quarantine status for M-008.

The inventory is derived from:
  - reports/bootstrap_statistics.json (committed results)
  - programs/A_metrology/bootstrap_statistics.py (computation definitions)
  - programs/A_metrology/MeasurementEngineSpecification.md (spec)
  - reports/phase3/regeneration_result.json (regeneration status from Phase 3)

Output: reports/phase4/metric_inventory.json
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUTPUT = REPO / "reports" / "phase4" / "metric_inventory.json"


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip()


def load_committed_bootstrap():
    """Load the committed bootstrap_statistics.json."""
    path = REPO / "reports" / "bootstrap_statistics.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_phase3_results():
    """Load Phase 3 regeneration results."""
    path = REPO / "reports" / "phase3" / "regeneration_result.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def build_metric_inventory(committed_bootstrap, phase3_results):
    """Build the full metric inventory from committed data and Phase 3 results."""

    # Build a lookup of Phase 3 regeneration status by metric_id
    phase3_by_metric = {}
    if phase3_results:
        for test in phase3_results.get("tests", []):
            if test.get("test") == "bootstrap_all_metrics":
                for m in test.get("mismatches", []):
                    mid = m.get("metric_id")
                    if mid:
                        phase3_by_metric[mid] = {
                            "regeneration_status": "FAILED",
                            "mismatch_detail": m,
                        }

    # The full metric inventory (38 metrics)
    # For each metric, record: definition location, inputs, computation, stored result, regeneration status
    metrics = []
    for entry in committed_bootstrap.get("results", []):
        mid = entry.get("metric_id")

        # Determine regeneration status
        if mid in phase3_by_metric:
            regen_status = "FAILED"
            regen_detail = phase3_by_metric[mid]["mismatch_detail"]
        else:
            regen_status = "NOT_TESTED_INDIVIDUALLY"
            # If bootstrap overall passed for this metric, mark as PASSED
            if phase3_results:
                for test in phase3_results.get("tests", []):
                    if test.get("test") == "bootstrap_all_metrics" and test.get("verdict") == "PASS":
                        regen_status = "PASSED"
                        break
                    elif test.get("test") == "bootstrap_all_metrics" and test.get("verdict") == "FAIL":
                        # Bootstrap overall failed, but this specific metric wasn't in mismatches
                        # So it passed individual comparison
                        regen_status = "PASSED"

        # Determine if this metric is on the critical path for matcher discrimination
        critical_path_metrics = {"M-004", "M-005", "M-006", "M-007", "M-008", "M-010", "M-011", "M-012", "M-013", "M-015"}
        is_critical = mid in critical_path_metrics

        # M-008 special quarantine status
        if mid == "M-008":
            measurement_usability = "QUARANTINED"
            used_for_scientific_decision = "NO"
            value_deleted = "NO"
            value_replaced = "NO"
            values_averaged = "NO"
            historical_provenance = "PENDING_INVESTIGATION"
            investigation_required = [
                "identify provenance of committed 0.9189",
                "identify exact input dataset/hash",
                "identify exact code commit",
                "identify dependency lock",
                "identify RNG implementation/environment",
                "reproduce historical computation",
                "classify cause",
            ]
        else:
            measurement_usability = "ACTIVE"
            used_for_scientific_decision = "YES" if is_critical else "NO"
            value_deleted = "NO"
            value_replaced = "NO"
            values_averaged = "NO"
            historical_provenance = "COMMITTED"
            investigation_required = []

        metric_record = {
            "metric_id": mid,
            "metric_name": entry.get("metric_name", ""),
            "stored_result": {
                "point_estimate": entry.get("point_estimate"),
                "bootstrap_mean": entry.get("bootstrap_mean"),
                "bootstrap_std": entry.get("bootstrap_std"),
                "ci_95_lower": entry.get("ci_95_lower"),
                "ci_95_upper": entry.get("ci_95_upper"),
                "ci_95_width": entry.get("ci_95_width"),
                "n": entry.get("n"),
                "n_resamples": entry.get("n_resamples"),
                "seed": entry.get("seed"),
            },
            "definition_location": {
                "spec": "programs/A_metrology/MeasurementEngineSpecification.md",
                "computation": "programs/A_metrology/bootstrap_statistics.py",
                "committed_results": "reports/bootstrap_statistics.json",
            },
            "inputs": _get_metric_inputs(mid),
            "computation": _get_metric_computation(mid),
            "regeneration_status": regen_status,
            "fresh_regenerated_value": regen_detail.get("fresh") if mid in phase3_by_metric else None,
            "critical_path_for_matcher_discrimination": is_critical,
            "measurement_usability": measurement_usability,
            "used_for_scientific_decision": used_for_scientific_decision,
            "value_deleted": value_deleted,
            "value_replaced": value_replaced,
            "values_averaged": values_averaged,
            "historical_provenance": historical_provenance,
        }

        if investigation_required:
            metric_record["investigation_required"] = investigation_required

        if mid == "M-008":
            metric_record["quarantine_note"] = (
                "M-008 is quarantined per audit round 6. The FP floor does not regenerate "
                "(fresh=0.8889 vs committed=0.9189, diff=0.030). No retroactive repair. "
                "No deletion. No replacement. No averaging. The discrepancy must be causally "
                "attributed before M-008 can be trusted. Per MC-5, M-008 (FP floor > 5% "
                "blocks discovery claims) is the single most critical metric for the "
                "matcher discrimination study."
            )

        metrics.append(metric_record)

    return metrics


def _get_metric_inputs(mid):
    """Return the inputs for each metric category."""
    if mid.startswith("M-0") or mid.startswith("M-01") or mid.startswith("M-016"):
        return {
            "gold_set": "GOLD_DISCOVERIES (N=20, benchmarks/discovery_capability_benchmark.py:105-328)",
            "entity_pool": "all_entities (NLP-extracted from 40 source snippets, fixed at module load)",
            "synonym_map": "BRIDGE_SYNONYMS (EMPTY since cycle 270, discovery_capability_benchmark.py:68)",
            "matchers": "m_exact, m_token, m_synonym (falls back to m_token), m_fuzzy",
        }
    elif mid.startswith("M-10"):
        return {
            "source": "benchmarks/reports/gen{1..5}_pr_score.json",
            "description": "Per-generation invention pipeline P/R scores",
        }
    elif mid.startswith("M-20"):
        return {
            "source": "BLIND_SUITE[10:] (10 held-out blind problems, BLIND-011..020)",
            "training": "BLIND_SUITE[:10] (BLIND-001..010) for composite synthesis",
        }
    elif mid.startswith("M-30"):
        return {
            "source": "reports/tier2_review_aggregated.json, reports/tier2_review_responses.csv, reports/dr95_calibration_research.json, reports/calibration_study.json",
            "description": "AI surrogate evaluation and calibration data",
        }
    return {"source": "UNKNOWN"}


def _get_metric_computation(mid):
    """Return the computation description for each metric."""
    computations = {
        "M-001": "Exact F1 (all entities) — strict string equality matching",
        "M-002": "Token F1 (all entities) — substring + shared token matching",
        "M-003": "Fuzzy F1 (all entities) — fuzzy string matching",
        "M-004": "Synonym F1 (all entities) — synonym-aware matching (now falls back to token since BRIDGE_SYNONYMS emptied)",
        "M-005": "Discovery F1 (shared, synonym, DR-91) — F1 = 2*recall/(1+recall), the headline discovery metric",
        "M-006": "Recognition F1 (all, synonym, DR-91) — recognition metric for inflation diagnosis",
        "M-007": "Proposal-locus inflation — difference between M-006 and M-005",
        "M-008": "FP floor (synonym match) — F1 of RANDOM candidates against gold pool. SHOULD be near 0 for a discriminating matcher. Currently 0.9189 = matcher does NOT discriminate.",
        "M-009": "UNSAFE synonyms count — count of circular/gold-derived synonyms (now 0)",
        "M-010": "Per-proposal F1 (honest, lenient, ALL shared) — honest per-proposal F1",
        "M-011": "Per-proposal F1 (strict, honest) — strict per-proposal F1",
        "M-012": "Aggregate F1 (DR-91 convention) — formula-inflated aggregate",
        "M-013": "Aggregate F1 (honest convention) — honest aggregate F1",
        "M-014": "BM25 baseline recall@1 (lenient) — oracle-assisted BM25 baseline",
        "M-015": "Random baseline F1 (lenient) — random 2-gram candidate baseline",
        "M-016": "Frequency baseline F1 (lenient) — frequency-based baseline",
    }
    if mid in computations:
        return computations[mid]
    if mid.startswith("M-10"):
        return f"{mid} — per-generation invention pipeline F1"
    if mid.startswith("M-20"):
        return f"{mid} — search/l5b held-out evaluation"
    if mid.startswith("M-30"):
        return f"{mid} — AI surrogate evaluation / calibration metric"
    return "UNKNOWN"


def main():
    print("Phase 4: Measurement Metric Inventory")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Git HEAD: {git_head()}")
    print()

    committed = load_committed_bootstrap()
    if not committed:
        print("ERROR: Could not load committed bootstrap_statistics.json")
        return 1

    phase3 = load_phase3_results()

    metrics = build_metric_inventory(committed, phase3)

    # Summary statistics
    total = len(metrics)
    quarantined = sum(1 for m in metrics if m["measurement_usability"] == "QUARANTINED")
    critical_path = sum(1 for m in metrics if m["critical_path_for_matcher_discrimination"])
    regen_failed = sum(1 for m in metrics if m["regeneration_status"] == "FAILED")
    regen_passed = sum(1 for m in metrics if m["regeneration_status"] == "PASSED")

    print(f"Total metrics inventoried: {total}")
    print(f"Quarantined: {quarantined}")
    print(f"Critical path for matcher discrimination: {critical_path}")
    print(f"Regeneration PASSED: {regen_passed}")
    print(f"Regeneration FAILED: {regen_failed}")

    inventory = {
        "phase": 4,
        "phase_name": "Inventory every measurement metric",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "summary": {
            "total_metrics": total,
            "quarantined": quarantined,
            "critical_path_for_matcher_discrimination": critical_path,
            "regeneration_passed": regen_passed,
            "regeneration_failed": regen_failed,
            "regeneration_not_tested": total - regen_passed - regen_failed,
        },
        "m008_quarantine_summary": {
            "metric_id": "M-008",
            "metric_name": "FP floor / false-positive floor",
            "current_stored_value": 0.9189,
            "fresh_regenerated_value": 0.8889,
            "regeneration_status": "FAILED",
            "measurement_usability": "QUARANTINED",
            "used_for_scientific_decision": "NO",
            "value_deleted": "NO",
            "value_replaced": "NO",
            "values_averaged": "NO",
            "note": "M-008 is the single most critical metric. It is the FP floor — if random candidates score near 1.0, the matcher does not discriminate. Current value 0.9189 is ~18x above the 0.05 acceptance threshold. It does not regenerate (fresh=0.8889). Per MC-5, M-008 blocks ALL discovery claims. It is quarantined until the regeneration discrepancy is causally attributed.",
        },
        "metrics": metrics,
        "critical_path_metrics": [m["metric_id"] for m in metrics if m["critical_path_for_matcher_discrimination"]],
        "no_retroactive_repair": True,
        "no_value_deletion": True,
        "no_value_replacement": True,
        "no_value_averaging": True,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(inventory, indent=2, default=str))
    print(f"\nInventory written to {OUTPUT}")
    print(f"\nM-008 status: {inventory['m008_quarantine_summary']['measurement_usability']}")
    print(f"M-008 used for scientific decision: {inventory['m008_quarantine_summary']['used_for_scientific_decision']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
