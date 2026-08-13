#!/usr/bin/env python
"""
Source Fabric CLI entrypoint (Issue #5).

Usage:
    python -m source_fabric.run_fabric            # offline mode (default)
    python -m source_fabric.run_fabric --live      # attempts live harvest
                                                   # (requires credentials;
                                                   #  will fail without them)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from source_fabric.orchestrator import run_fabric, forensic_audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default=str(Path(__file__).parent / "reports"))
    ap.add_argument("--live", action="store_true",
                    help="Attempt live harvest (requires credentials in env vars). "
                         "Without this flag, the fabric runs in OFFLINE mode: "
                         "structural validation only, no live HTTP calls.")
    args = ap.parse_args()

    if args.live:
        print("FATAL: --live mode requires credentials. Offline mode only for now.")
        print("To enable live harvest, set environment variables for each source:")
        print("  OPENALEX_EMAIL, CROSSREF_API_TOKEN, EPO_OPS_KEY, EPO_OPS_SECRET,")
        print("  GITHUB_TOKEN, ZENODO_TOKEN, NIST_API_KEY, ...")
        sys.exit(2)

    print("Running source fabric in OFFLINE mode (no live HTTP calls).")
    result = run_fabric(Path(args.output_dir))

    print("\n=== FABRIC STATE ===")
    state = result["state"]
    print(json.dumps({
        "fabric_id": state["fabric_id"],
        "total_sources": state["total_sources"],
        "primary_sources": state["primary_sources"],
        "aggregator_sources": state["aggregator_sources"],
        "total_domains": state["total_domains"],
        "total_universes": state["total_universes"],
        "structural_validation_pass": state["structural_validation_pass"],
        "structural_validation_fail": state["structural_validation_fail"],
        "live_check_performed": state["live_check_performed"],
        "real_data_seal": state["real_data_seal"],
        "is_scientific_result": state["is_scientific_result"],
        "snapshot_created": state["snapshot_created"],
        "snapshot_verified": state["snapshot_verified"],
        "provenance_vocabulary_size": state["provenance_vocabulary_size"],
        "cross_corpus_predicates": state["cross_corpus_predicates"],
        "empirical_predicates": state["empirical_predicates"],
        "supported_languages_count": state["supported_languages_count"],
        "cross_evidence_motif_count": state["cross_evidence_motif_count"],
    }, indent=2, default=str))

    # Forensic audit
    audit = forensic_audit(Path(result["report_path"]))
    print("\n=== FORENSIC AUDIT ===")
    print(f"PASSED: {audit['passed']}")
    for c in audit["checks"]:
        status = "PASS" if c["passed"] else "FAIL"
        print(f"  [{status}] {c['check']}")
        if not c["passed"]:
            print(f"         reason: {c.get('reason','')}")

    if not audit["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
