"""
novelty_audit.search.novelty_audit_runner — Main runner for the novelty audit.

Executes:
1. Load 182 frozen pairs from evidence-complete packet
2. Generate deterministic queries (frozen before execution)
3. Execute searches against independent databases
4. Produce D1-D4 evidence packages (D3=PENDING_CUSTODIAN)
5. Produce custodian novelty packet

NO TEE. NO LLM. NO automated NOVEL label. NO benchmark construction.
"""
import json
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "custodian"))

from novelty_audit.search.query_generator import (
    generate_queries_for_pair,
    freeze_queries,
)
from novelty_audit.search.search_executor import (
    execute_search,
    SearchResult,
)


def run_novelty_audit(
    evidence_packet_path: Path,
    output_dir: Path,
    max_results_per_query: int = 5,
    delay_between_queries: float = 0.5,
) -> dict:
    """Run the full novelty audit on 182 frozen pairs.

    Args:
        evidence_packet_path: Path to pairability_evidence_complete_blind_packet.json
        output_dir: Output directory
        max_results_per_query: Max results to retrieve per query
        delay_between_queries: Delay in seconds (rate limiting)

    Returns:
        Aggregate report
    """
    # Step 1: Load frozen evidence packet
    with open(evidence_packet_path) as f:
        packet = json.load(f)

    pairs = packet["pairs"]
    universe_hash = packet["universe_manifest_hash"]
    packet_hash = packet.get("packet_hash", "")

    print(f"=== PAIRABILITY_NOVELTY_AUDIT_V1 ===")
    print(f"Universe hash: {universe_hash[:32]}...")
    print(f"Evidence packet hash: {packet_hash[:32]}...")
    print(f"Pairs: {len(pairs)}")
    print()

    # Step 2: Generate ALL queries BEFORE any search (frozen)
    print("Step 1: Generating queries (frozen before execution)...")
    all_queries = []
    for pair in pairs:
        queries = generate_queries_for_pair(
            pair_id=pair["source_a_id"] + "_" + pair["source_b_id"],
            title_a=pair["title_a"],
            abstract_a=pair.get("abstract_a", ""),
            title_b=pair["title_b"],
            abstract_b=pair.get("abstract_b", ""),
            domain_a=pair["domain_a"],
            domain_b=pair["domain_b"],
        )
        all_queries.extend(queries)

    query_manifest = freeze_queries(all_queries)
    print(f"  Queries generated: {len(all_queries)}")
    print(f"  Query manifest hash: {query_manifest['manifest_hash'][:32]}...")
    print()

    # Save frozen query manifest
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    query_manifest_path = output_dir / "frozen_query_manifest.json"
    with open(query_manifest_path, 'w') as f:
        json.dump(query_manifest, f, indent=2)
    print(f"  Frozen query manifest saved: {query_manifest_path}")
    print()

    # Step 3: Execute searches
    print(f"Step 2: Executing {len(all_queries)} searches...")
    all_results = []
    success_count = 0
    unavailable_count = 0

    for idx, query in enumerate(all_queries):
        if (idx + 1) % 50 == 0:
            print(f"  {idx+1}/{len(all_queries)}... (success={success_count}, unavailable={unavailable_count})")

        result = execute_search(query, max_results=max_results_per_query)
        all_results.append(result)

        if result.status == "SUCCESS":
            success_count += 1
        else:
            unavailable_count += 1

        time.sleep(delay_between_queries)

    print(f"\n  Searches complete: {len(all_results)}")
    print(f"  Success: {success_count}")
    print(f"  Unavailable: {unavailable_count}")
    print()

    # Step 4: Build D1-D4 evidence packages per pair
    print("Step 3: Building D1-D4 evidence packages...")
    pair_results = {}  # pair_id → list of SearchResult
    for result in all_results:
        if result.pair_id not in pair_results:
            pair_results[result.pair_id] = []
        pair_results[result.pair_id].append(result)

    d_packages = []
    for pair in pairs:
        pair_id = pair["source_a_id"] + "_" + pair["source_b_id"]
        results = pair_results.get(pair_id, [])

        # D2: Search adequacy record
        d2_record = {
            "databases_searched": list(set(r.database for r in results)),
            "queries_executed": len(results),
            "queries_successful": sum(1 for r in results if r.status == "SUCCESS"),
            "queries_unavailable": sum(1 for r in results if r.status == "UNAVAILABLE"),
            "search_timestamps": [r.search_timestamp for r in results],
            "result_counts": {r.database: r.result_count for r in results if r.status == "SUCCESS"},
            "query_hashes": [r.query_hash for r in results],
            "result_manifest_hashes": [r.result_manifest_hash for r in results if r.result_manifest_hash],
        }

        # D4: Search universe description
        d4_record = {
            "databases": list(set(r.database for r in results)),
            "query_types": list(set(r.query_text[:50] for r in results)),
            "max_results_per_query": max_results_per_query,
            "search_protocol": "PAIRABILITY_NOVELTY_AUDIT_V1",
            "query_manifest_hash": query_manifest["manifest_hash"],
        }

        # D1: Retrieved evidence (for custodian review)
        d1_evidence = []
        for r in results:
            if r.status == "SUCCESS":
                for i, (rid, rtitle) in enumerate(zip(r.result_ids, r.result_titles)):
                    d1_evidence.append({
                        "database": r.database,
                        "result_id": rid,
                        "title": rtitle,
                        "query_type": r.search_id.split("-")[2] if "-" in r.search_id else "unknown",
                    })

        package = {
            "pair_id": pair_id,
            "source_a_id": pair["source_a_id"],
            "source_b_id": pair["source_b_id"],
            "D1": "PENDING_CUSTODIAN",
            "D1_evidence": d1_evidence[:20],  # Top 20 results for custodian review
            "D2": "PENDING_CUSTODIAN",
            "D2_record": d2_record,
            "D3": "PENDING_CUSTODIAN",
            "D4": d4_record,
            "search_complete": True,
        }
        d_packages.append(package)

    print(f"  D packages built: {len(d_packages)}")
    print()

    # Step 5: Build custodian novelty packet
    print("Step 4: Building custodian novelty packet...")
    custodian_packet = {
        "packet_type": "CUSTODIAN_NOVELTY_PACKET_V1",
        "packet_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "universe_manifest_hash": universe_hash,
        "evidence_packet_hash": packet_hash,
        "query_manifest_hash": query_manifest["manifest_hash"],
        "pair_count": len(pairs),
        "query_count": len(all_queries),
        "search_success_count": success_count,
        "search_unavailable_count": unavailable_count,
        "databases_used": list(SEARCH_ADAPTERS.keys()),
        "rules": [
            "D1, D2, D3 are PENDING_CUSTODIAN — no automated novelty label.",
            "D3 allowed values: ESTABLISHED, NOT_ESTABLISHED, INDETERMINATE.",
            "D1=NO alone does NOT establish S-TASK.",
            "Search failures (UNAVAILABLE) are NOT interpreted as novelty.",
            "Failed APIs are recorded as UNAVAILABLE, never as zero results.",
            "No TEE access. No benchmark construction. No taxonomy changes.",
        ],
        "pairs": d_packages,
    }

    # Hash the custodian packet (excluding the hash itself)
    canonical = json.dumps(custodian_packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    custodian_packet["packet_hash"] = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    # Save
    packet_path = output_dir / "custodian_novelty_packet.json"
    with open(packet_path, 'w') as f:
        json.dump(custodian_packet, f, indent=2)

    # Save search results (custodian-only, for audit trail)
    results_path = output_dir / "search_results_detailed.json"
    with open(results_path, 'w') as f:
        json.dump({
            "result_count": len(all_results),
            "results": [r.to_dict() for r in all_results],
        }, f, indent=2)

    # Save aggregate report
    db_stats = Counter()
    status_stats = Counter()
    for r in all_results:
        db_stats[r.database] += 1
        status_stats[r.status] += 1

    # Per-pair summary
    pairs_with_results = sum(1 for p in d_packages if p["D1_evidence"])
    pairs_no_results = sum(1 for p in d_packages if not p["D1_evidence"])
    pairs_all_unavailable = sum(1 for p in d_packages if p["D2_record"]["queries_successful"] == 0)

    aggregate = {
        "report_type": "NOVELTY_AUDIT_AGGREGATE_V1",
        "universe_manifest_hash": universe_hash,
        "pair_count": len(pairs),
        "query_count": len(all_queries),
        "search_success": success_count,
        "search_unavailable": unavailable_count,
        "database_distribution": dict(db_stats.most_common()),
        "status_distribution": dict(status_stats.most_common()),
        "pairs_with_search_results": pairs_with_results,
        "pairs_with_no_results": pairs_no_results,
        "pairs_all_queries_unavailable": pairs_all_unavailable,
        "note": "D3=PENDING_CUSTODIAN for all pairs. No automated novelty label.",
        "warning": "UNAVAILABLE searches are NOT zero results. They are search failures.",
    }

    aggregate_path = output_dir / "search_aggregate.json"
    with open(aggregate_path, 'w') as f:
        json.dump(aggregate, f, indent=2)

    print(f"  Custodian packet: {packet_path}")
    print(f"  Search results: {results_path}")
    print(f"  Aggregate report: {aggregate_path}")
    print()

    # Print summary
    print("=== SUMMARY ===")
    print(f"Pairs: {len(pairs)}")
    print(f"Queries: {len(all_queries)}")
    print(f"Search success: {success_count}")
    print(f"Search unavailable: {unavailable_count}")
    print(f"Pairs with results: {pairs_with_results}")
    print(f"Pairs with no results: {pairs_no_results}")
    print(f"Pairs all unavailable: {pairs_all_unavailable}")
    print()
    print("D3 = PENDING_CUSTODIAN for all 182 pairs.")
    print("No automated novelty label. No benchmark construction. No TEE.")
    print()
    print("CODER WORK COMPLETE. Custodian takes over.")

    return aggregate


# Import here to avoid circular import
from novelty_audit.search.search_executor import SEARCH_ADAPTERS


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, help="Path to evidence-complete blind packet")
    parser.add_argument("--output", default="novelty_audit/reports", help="Output directory")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    run_novelty_audit(
        evidence_packet_path=Path(args.packet),
        output_dir=Path(args.output),
        max_results_per_query=args.max_results,
        delay_between_queries=args.delay,
    )
