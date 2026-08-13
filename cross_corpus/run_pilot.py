#!/usr/bin/env python
"""
Cross-corpus pilot CLI entrypoint (Issue #4).

Usage:
    python -m cross_corpus.run_pilot                # run on fixtures
    python -m cross_corpus.run_pilot --real-data     # MUST fail (no real data seal)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from cross_corpus.ingest import load_papers_jsonl, load_patents_jsonl, corpus_manifest
from cross_corpus.orchestrator import run_pilot
from cross_corpus.forensic import forensic_audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures-dir", default=str(Path(__file__).parent / "fixtures"))
    ap.add_argument("--output-dir", default=str(Path(__file__).parent / "reports"))
    ap.add_argument("--real-data", action="store_true",
                    help="Assert real data seal (will fail on synthetic fixtures)")
    args = ap.parse_args()

    fdir = Path(args.fixtures_dir)
    odir = Path(args.output_dir)
    papers = load_papers_jsonl(fdir / "papers.jsonl")
    patents = load_patents_jsonl(fdir / "patents.jsonl")
    print(f"Loaded {len(papers)} papers + {len(patents)} patents from {fdir}")

    # real_data_seal can only be True if real OpenAlex/EPO data was ingested.
    # On synthetic fixtures, we FORBID real_data_seal=True.
    real_data_seal = bool(args.real_data)
    if real_data_seal:
        # Check: every record must have ingestion_source != 'synthetic_fixture'
        synthetic_papers = [p for p in papers if p.ingestion_source == "synthetic_fixture"]
        synthetic_patents = [p for p in patents if p.ingestion_source == "synthetic_fixture"]
        if synthetic_papers or synthetic_patents:
            print("FATAL: --real-data requested but corpus contains synthetic_fixture records.")
            print(f"  synthetic papers: {len(synthetic_papers)}")
            print(f"  synthetic patents: {len(synthetic_patents)}")
            print("  REAL_DATA_SEAL cannot be issued on synthetic fixtures.")
            sys.exit(2)

    # Use a cutoff that's AFTER all fixture dates (fixtures end ~2024-01-01).
    # The pilot cutoff is the previous complete UTC day, but since fixtures
    # are backdated to 2015-2024, we use a fixed cutoff of 2024-06-01 so all
    # fixtures are eligible evidence. This is documented in the preregistration.
    cutoff = "2024-06-01"

    result = run_pilot(papers, patents, cutoff=cutoff,
                       real_data_seal=real_data_seal, output_dir=odir)
    print("\n=== PILOT RESULT ===")
    print(json.dumps({
        "final_state": result["state"]["state"],
        "decision": result["state"].get("decision"),
        "candidates_total": result["state"].get("graph_stats"),
        "retrieval_negative_count": result["state"].get("retrieval_negative_count"),
        "null_control_results": result["state"].get("null_control_results"),
        "is_scientific_result": result["state"].get("is_scientific_result"),
        "real_data_seal": result["state"].get("real_data_seal"),
        "forensic_audit_passed": result["forensic_audit"]["passed"],
        "result_package_path": result["result_package_path"],
    }, indent=2, default=str))

    if not result["forensic_audit"]["passed"]:
        print("\nFORENSIC AUDIT FAILED:")
        for c in result["forensic_audit"]["checks"]:
            if not c["passed"]:
                print(f"  - {c['check']}: {c.get('reason','')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
