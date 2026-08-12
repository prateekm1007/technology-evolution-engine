"""
novelty_audit.search.novelty_audit_runner_v1_1 — V1.1 runner with resume.

V1.1 fixes:
- Executes against ALL 3 declared databases
- Persistent checkpoint (resume from exact position)
- Separate SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR
- Full result manifests
- Per-query-type reporting
- Mechanical D2 coverage computation
- D3 = PENDING_CUSTODIAN (forbidden from automation)

Does NOT change frozen queries. Does NOT change 182 pairs. Does NOT use TEE.
"""
import json
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from novelty_audit.search.search_executor_v1_1 import (
    execute_search_v11,
    SearchResultV11,
    SEARCH_ADAPTERS_V11,
)


CHECKPOINT_PATH = Path("novelty_audit/reports/v1_1_checkpoint.json")
RESULTS_PATH = Path("novelty_audit/reports/v1_1_search_results.json")
PACKET_PATH = Path("novelty_audit/reports/v1_1_custodian_novelty_packet.json")
AGGREGATE_PATH = Path("novelty_audit/reports/v1_1_search_aggregate.json")


def load_checkpoint() -> dict:
    """Load checkpoint for resume."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"completed_queries": [], "results": []}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def run_novelty_audit_v1_1(
    query_manifest_path: Path,
    evidence_packet_path: Path,
    output_dir: Path,
    max_results_per_query: int = 10,
    delay_between_queries: float = 0.3,
) -> dict:
    """Run V1.1 novelty audit with all 3 databases and resume."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load frozen query manifest (DO NOT MODIFY)
    with open(query_manifest_path) as f:
        query_manifest = json.load(f)

    all_queries = query_manifest["queries"]
    manifest_hash = query_manifest["manifest_hash"]

    # Load evidence packet for pair info
    with open(evidence_packet_path) as f:
        packet = json.load(f)
    pairs = packet["pairs"]
    universe_hash = packet["universe_manifest_hash"]
    evidence_hash = packet.get("packet_hash", "")

    # The frozen manifest has queries for 'openalex' only.
    # V1.1 must execute against ALL 3 databases.
    # We expand the query list: for each frozen query, create 2 new entries
    # (semantic_scholar, crossref) with new query_ids.
    # The ORIGINAL frozen queries remain unchanged.
    expanded_queries = []
    for q in all_queries:
        # Keep original (openalex)
        expanded_queries.append(q)
        # Add semantic_scholar
        expanded_queries.append({
            "query_id": q["query_id"].replace("-openalex", "-semantic_scholar"),
            "pair_id": q["pair_id"],
            "query_type": q["query_type"],
            "database": "semantic_scholar",
            "query_text": q["query_text"],
            "query_hash": q["query_hash"],  # Same text → same hash
        })
        # Add crossref
        expanded_queries.append({
            "query_id": q["query_id"].replace("-openalex", "-crossref"),
            "pair_id": q["pair_id"],
            "query_type": q["query_type"],
            "database": "crossref",
            "query_text": q["query_text"],
            "query_hash": q["query_hash"],
        })

    total_queries = len(expanded_queries)
    print(f"=== PAIRABILITY_NOVELTY_AUDIT_V1.1 ===")
    print(f"Universe hash: {universe_hash[:32]}...")
    print(f"Frozen query manifest: {manifest_hash[:32]}...")
    print(f"Original queries (frozen): {len(all_queries)}")
    print(f"Expanded queries (3 databases): {total_queries}")
    print(f"Databases: openalex, semantic_scholar, crossref")
    print()

    # Load checkpoint for resume
    checkpoint = load_checkpoint()
    completed_ids = set(checkpoint["completed_queries"])
    existing_results = checkpoint["results"]

    print(f"Resuming: {len(completed_ids)} queries already completed")
    remaining = [q for q in expanded_queries if q["query_id"] not in completed_ids]
    print(f"Remaining: {len(remaining)} queries")
    print()

    # Execute searches
    all_results = list(existing_results)  # Start with existing
    status_counts = Counter(r.get("status", "UNKNOWN") for r in all_results)

    for idx, query in enumerate(remaining):
        if (idx + 1) % 50 == 0:
            print(f"  {idx+1}/{len(remaining)}... (S={status_counts.get('SUCCESS',0)}, "
                  f"NR={status_counts.get('NO_RESULTS',0)}, "
                  f"U={status_counts.get('UNAVAILABLE',0)}, "
                  f"E={status_counts.get('ERROR',0)})", flush=True)

        result = execute_search_v11(query, max_results=max_results_per_query)
        result_dict = result.to_dict()
        all_results.append(result_dict)
        status_counts[result.status] += 1
        completed_ids.add(query["query_id"])

        # Checkpoint every 20 queries
        if (len(completed_ids) % 20) == 0:
            checkpoint = {"completed_queries": list(completed_ids), "results": all_results}
            save_checkpoint(checkpoint)

        time.sleep(delay_between_queries)

    # Final checkpoint
    checkpoint = {"completed_queries": list(completed_ids), "results": all_results}
    save_checkpoint(checkpoint)

    print(f"\n=== SEARCH EXECUTION COMPLETE ===")
    print(f"Total queries: {total_queries}")
    print(f"Success: {status_counts.get('SUCCESS', 0)}")
    print(f"No results: {status_counts.get('NO_RESULTS', 0)}")
    print(f"Unavailable: {status_counts.get('UNAVAILABLE', 0)}")
    print(f"Error: {status_counts.get('ERROR', 0)}")
    print()

    # Save full search results
    with open(RESULTS_PATH, 'w') as f:
        json.dump({
            "total_queries": total_queries,
            "frozen_query_manifest_hash": manifest_hash,
            "results": all_results,
        }, f, indent=2)

    # Build D1-D4 packages per pair
    print("Building D1-D4 evidence packages...")
    pair_results = defaultdict(list)
    for r in all_results:
        pair_results[r["pair_id"]].append(r)

    d_packages = []
    for pair in pairs:
        pair_id = pair["source_a_id"] + "_" + pair["source_b_id"]
        results = pair_results.get(pair_id, [])

        # D1: Full evidence (NOT truncated)
        d1_evidence = []
        for r in results:
            if r["status"] == "SUCCESS":
                for i in range(len(r["result_ids"])):
                    d1_evidence.append({
                        "database": r["database"],
                        "result_id": r["result_ids"][i] if i < len(r["result_ids"]) else "",
                        "title": r["result_titles"][i] if i < len(r["result_titles"]) else "",
                        "doi": r["result_dois"][i] if i < len(r["result_dois"]) else "",
                        "date": r["result_dates"][i] if i < len(r["result_dates"]) else "",
                        "query_type": r["query_type"],
                        "query_hash": r["query_hash"],
                        "rank": i + 1,
                    })

        # D2: Mechanical coverage computation
        declared_dbs = {"openalex", "semantic_scholar", "crossref"}
        db_results = defaultdict(list)
        for r in results:
            db_results[r["database"]].append(r)

        db_coverage = {}
        for db in declared_dbs:
            db_res = db_results.get(db, [])
            successful = sum(1 for r in db_res if r["status"] in ("SUCCESS", "NO_RESULTS"))
            total_db = len(db_res)
            db_coverage[db] = {
                "queries_declared": total_db,
                "queries_successful": successful,
                "queries_unavailable": sum(1 for r in db_res if r["status"] == "UNAVAILABLE"),
                "queries_error": sum(1 for r in db_res if r["status"] == "ERROR"),
                "availability": successful / total_db if total_db > 0 else 0.0,
            }

        total_declared = sum(v["queries_declared"] for v in db_coverage.values())
        total_successful = sum(v["queries_successful"] for v in db_coverage.values())
        overall_coverage = total_successful / total_declared if total_declared > 0 else 0.0

        # Per query type
        qt_stats = defaultdict(lambda: {"success": 0, "no_results": 0, "unavailable": 0, "error": 0, "total": 0})
        for r in results:
            qt_stats[r["query_type"]]["total"] += 1
            if r["status"] == "SUCCESS":
                qt_stats[r["query_type"]]["success"] += 1
            elif r["status"] == "NO_RESULTS":
                qt_stats[r["query_type"]]["no_results"] += 1
            elif r["status"] == "UNAVAILABLE":
                qt_stats[r["query_type"]]["unavailable"] += 1
            else:
                qt_stats[r["query_type"]]["error"] += 1

        d_packages.append({
            "pair_id": pair_id,
            "source_a_id": pair["source_a_id"],
            "source_b_id": pair["source_b_id"],
            "D1": "PENDING_CUSTODIAN",
            "D1_evidence": d1_evidence,  # Full, NOT truncated
            "D2": "PENDING_CUSTODIAN",
            "D2_record": {
                "databases_searched": list(declared_dbs),
                "database_coverage": db_coverage,
                "overall_coverage": round(overall_coverage, 4),
                "total_queries_declared": total_declared,
                "total_queries_successful": total_successful,
                "per_query_type": dict(qt_stats),
            },
            "D3": "PENDING_CUSTODIAN",
            "D4": {
                "databases": list(declared_dbs),
                "query_manifest_hash": manifest_hash,
                "search_protocol": "PAIRABILITY_NOVELTY_AUDIT_V1.1",
                "max_results_per_query": max_results_per_query,
            },
            "search_complete": True,
        })

    # Build custodian packet
    custodian_packet = {
        "packet_type": "CUSTODIAN_NOVELTY_PACKET_V1_1",
        "packet_version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "universe_manifest_hash": universe_hash,
        "evidence_packet_hash": evidence_hash,
        "query_manifest_hash": manifest_hash,
        "pair_count": len(pairs),
        "query_count": total_queries,
        "databases_used": list(SEARCH_ADAPTERS_V11.keys()),
        "status_summary": dict(status_counts),
        "rules": [
            "D1, D2, D3 are PENDING_CUSTODIAN — no automated novelty label.",
            "D3 allowed values: ESTABLISHED, NOT_ESTABLISHED, INDETERMINATE.",
            "D1=NO alone does NOT establish S-TASK.",
            "UNAVAILABLE is NOT zero results — it is a search failure.",
            "NO_RESULTS is zero results from a successful search.",
            "D2 coverage is mechanical, not a scientific judgment.",
            "No TEE access. No benchmark construction. No taxonomy changes.",
        ],
        "pairs": d_packages,
    }

    canonical = json.dumps(custodian_packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    custodian_packet["packet_hash"] = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    with open(PACKET_PATH, 'w') as f:
        json.dump(custodian_packet, f, indent=2)

    # Aggregate report
    pairs_with_results = sum(1 for p in d_packages if p["D1_evidence"])
    pairs_no_results = sum(1 for p in d_packages if not p["D1_evidence"])
    pairs_full_coverage = sum(1 for p in d_packages if p["D2_record"]["overall_coverage"] == 1.0)
    pairs_partial_coverage = sum(1 for p in d_packages if 0 < p["D2_record"]["overall_coverage"] < 1.0)
    pairs_no_coverage = sum(1 for p in d_packages if p["D2_record"]["overall_coverage"] == 0.0)

    aggregate = {
        "report_type": "NOVELTY_AUDIT_V1_1_AGGREGATE",
        "pair_count": len(pairs),
        "query_count": total_queries,
        "status_summary": dict(status_counts),
        "pairs_with_search_results": pairs_with_results,
        "pairs_with_no_results": pairs_no_results,
        "pairs_full_coverage": pairs_full_coverage,
        "pairs_partial_coverage": pairs_partial_coverage,
        "pairs_no_coverage": pairs_no_coverage,
        "note": "D3=PENDING_CUSTODIAN for all pairs. UNAVAILABLE ≠ zero results.",
    }

    with open(AGGREGATE_PATH, 'w') as f:
        json.dump(aggregate, f, indent=2)

    print(f"\n=== V1.1 SUMMARY ===")
    print(f"Pairs: {len(pairs)}")
    print(f"Queries: {total_queries}")
    print(f"Success: {status_counts.get('SUCCESS', 0)}")
    print(f"No results: {status_counts.get('NO_RESULTS', 0)}")
    print(f"Unavailable: {status_counts.get('UNAVAILABLE', 0)}")
    print(f"Error: {status_counts.get('ERROR', 0)}")
    print(f"\nPairs with results: {pairs_with_results}")
    print(f"Pairs with no results: {pairs_no_results}")
    print(f"Full D2 coverage: {pairs_full_coverage}")
    print(f"Partial D2 coverage: {pairs_partial_coverage}")
    print(f"No D2 coverage: {pairs_no_coverage}")
    print(f"\nD3 = PENDING_CUSTODIAN for all {len(pairs)} pairs.")
    print(f"Packet hash: {custodian_packet['packet_hash'][:32]}...")
    print(f"\nCODER WORK COMPLETE. Custodian takes over.")

    return aggregate


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--output", default="novelty_audit/reports")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()

    run_novelty_audit_v1_1(
        query_manifest_path=Path(args.manifest),
        evidence_packet_path=Path(args.packet),
        output_dir=Path(args.output),
        max_results_per_query=args.max_results,
        delay_between_queries=args.delay,
    )
