"""
NOVELTY_RECOVERY_V1 — Recovery search runner.

Executes the SAME 182 pairs × SAME 4 frozen query types against
RECOVERY providers (OpenAIRE + OpenCitations) — NOT the frozen
3-database universe (OpenAlex / Semantic Scholar / Crossref).

Hard guarantees:
- Does NOT modify the frozen 728-query manifest.
- Does NOT change the 182-pair allocation.
- Does NOT alter D1-D4 definitions.
- Does NOT call recovery results "authoritative."
- Does NOT produce D3. Output is evidence for the custodian only.
- Classifies every result SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR.
- Never converts UNAVAILABLE to NO_RESULTS.
- Records provider, query, timestamp, response hash, evidence URI.
- Persistent checkpoint — resume-safe.
- Separate evidence namespace from frozen trial.
"""
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from novelty_audit.recovery.adapters.openaire import search_openaire
from novelty_audit.recovery.adapters.opencitations import (
    search_opencitations_keyword,
    opencitations_citation_lookup,
)


# === Paths ===
FROZEN_QUERY_MANIFEST = REPO / "novelty_audit/reports/frozen_query_manifest.json"
EVIDENCE_PACKET = REPO / "independent_corpus/reports/pairability_evidence_complete_blind_packet.json"

RECOVERY_DIR = REPO / "novelty_audit/recovery"
RECOVERY_REPORTS = RECOVERY_DIR / "reports"
RECOVERY_EVIDENCE = RECOVERY_DIR / "evidence"
RECOVERY_RESULT_MANIFESTS = RECOVERY_EVIDENCE / "result_manifests"

CHECKPOINT_PATH = RECOVERY_REPORTS / "recovery_v1_checkpoint.json"
RESULTS_PATH = RECOVERY_REPORTS / "recovery_v1_results.json"
PACKET_PATH = RECOVERY_REPORTS / "recovery_v1_evidence_packet.json"
AGGREGATE_PATH = RECOVERY_REPORTS / "recovery_v1_aggregate.json"
MANIFEST_PATH = RECOVERY_REPORTS / "recovery_v1_query_manifest.json"

# Create directories
for p in [RECOVERY_REPORTS, RECOVERY_EVIDENCE, RECOVERY_RESULT_MANIFESTS]:
    p.mkdir(parents=True, exist_ok=True)


# === Frozen query types ===
QUERY_TYPES = ["direct", "reverse", "domain_bridge", "mechanism_transfer"]

# Recovery providers
RECOVERY_PROVIDERS = ["openaire", "opencitations"]


def load_frozen_query_manifest() -> dict:
    """Load the frozen 728-query manifest. DO NOT MODIFY."""
    with open(FROZEN_QUERY_MANIFEST) as f:
        return json.load(f)


def load_evidence_packet() -> dict:
    """Load the 182-pair evidence packet (titles, abstracts, DOIs)."""
    with open(EVIDENCE_PACKET) as f:
        return json.load(f)


def build_recovery_query_manifest(frozen_manifest: dict, evidence_packet: dict) -> dict:
    """Build the recovery query manifest from frozen queries.

    The recovery manifest uses the SAME query_text as the frozen manifest
    (the keywords are database-agnostic). It generates new query_ids tagged
    with the recovery provider.

    For OpenCitations, we ALSO add a citation-graph lookup per pair
    (using the pair's DOIs) — this is a separate query type specific to
    the citation-graph recovery.
    """
    pairs_by_id = {p["source_a_id"] + "_" + p["source_b_id"]: p for p in evidence_packet["pairs"]}

    recovery_queries = []
    for fq in frozen_manifest["queries"]:
        pair_id = fq["pair_id"]
        for provider in RECOVERY_PROVIDERS:
            if provider == "openaire":
                # OpenAIRE gets all 4 query types (keyword search)
                new_qid = fq["query_id"].replace("-openalex", "-openaire")
                recovery_queries.append({
                    "query_id": new_qid,
                    "pair_id": pair_id,
                    "query_type": fq["query_type"],
                    "database": "openaire",
                    "query_text": fq["query_text"],
                    "query_hash": fq["query_hash"],
                    "frozen_query_ref": fq["query_id"],
                })
            elif provider == "opencitations":
                # OpenCitations gets the keyword-search query types (direct, reverse)
                # (domain_bridge and mechanism_transfer don't translate to keyword search)
                if fq["query_type"] in ("direct", "reverse"):
                    new_qid = fq["query_id"].replace("-openalex", "-opencitations")
                    recovery_queries.append({
                        "query_id": new_qid,
                        "pair_id": pair_id,
                        "query_type": fq["query_type"],
                        "database": "opencitations",
                        "query_text": fq["query_text"],
                        "query_hash": fq["query_hash"],
                        "frozen_query_ref": fq["query_id"],
                        "search_type": "keyword",
                    })

    # Add OpenCitations citation-graph lookups — one per pair
    # This is the citation-graph novelty check unique to OpenCitations
    for pair in evidence_packet["pairs"]:
        pair_id = pair["source_a_id"] + "_" + pair["source_b_id"]
        doi_a = pair.get("doi_a") or ""
        doi_b = pair.get("doi_b") or ""
        # Only add if we have DOIs
        if doi_a and doi_b:
            recovery_queries.append({
                "query_id": f"Q-{pair_id}-citation_graph-opencitations",
                "pair_id": pair_id,
                "query_type": "citation_graph",
                "database": "opencitations",
                "query_text": f"citation_lookup:{doi_a} <-> {doi_b}",
                "query_hash": hashlib.sha256(f"{doi_a}|{doi_b}".encode()).hexdigest(),
                "frozen_query_ref": None,  # not in frozen manifest
                "search_type": "citation_graph",
                "doi_a": doi_a,
                "doi_b": doi_b,
            })

    # Compute manifest hash (canonical JSON of recovery_queries, sorted)
    canonical = json.dumps(recovery_queries, sort_keys=True, separators=(",", ":"))
    manifest_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "manifest_type": "novelty_recovery_v1_query_manifest",
        "manifest_version": "1.0",
        "rule": "Recovery queries derived from FROZEN 728-query manifest. Same 182 pairs. Same 4 query types. Recovery providers: OpenAIRE + OpenCitations. Does NOT modify frozen manifest.",
        "frozen_manifest_hash": frozen_manifest["manifest_hash"],
        "evidence_packet_hash": evidence_packet["packet_hash"],
        "recovery_providers": RECOVERY_PROVIDERS,
        "query_count": len(recovery_queries),
        "manifest_hash": manifest_hash,
        "queries": recovery_queries,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "RECOVERY NAMESPACE. Not authoritative. Does not produce D3. Evidence for custodian only.",
    }


def save_recovery_manifest(manifest: dict):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"completed_query_ids": [], "results": []}


def save_checkpoint(checkpoint: dict):
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(checkpoint, f, indent=2)


def execute_query(query: dict) -> dict:
    """Execute a single recovery query. Returns recovery result dict."""
    provider = query["database"]
    qtype = query["query_type"]

    if provider == "openaire":
        result = search_openaire(query["query_text"], max_results=10)
        return {
            "query_id": query["query_id"],
            "pair_id": query["pair_id"],
            "query_type": qtype,
            "provider": "openaire",
            "query_text": query["query_text"],
            "query_hash": query["query_hash"],
            "frozen_query_ref": query.get("frozen_query_ref"),
            **result,
        }

    elif provider == "opencitations":
        if query.get("search_type") == "citation_graph":
            result = opencitations_citation_lookup(query["doi_a"], query["doi_b"])
            return {
                "query_id": query["query_id"],
                "pair_id": query["pair_id"],
                "query_type": qtype,
                "provider": "opencitations",
                "query_text": query["query_text"],
                "query_hash": query["query_hash"],
                "frozen_query_ref": query.get("frozen_query_ref"),
                **result,
            }
        else:
            # keyword search
            result = search_opencitations_keyword(query["query_text"], max_results=10)
            return {
                "query_id": query["query_id"],
                "pair_id": query["pair_id"],
                "query_type": qtype,
                "provider": "opencitations",
                "query_text": query["query_text"],
                "query_hash": query["query_hash"],
                "frozen_query_ref": query.get("frozen_query_ref"),
                **result,
            }

    return {
        "query_id": query["query_id"],
        "pair_id": query["pair_id"],
        "query_type": qtype,
        "provider": provider,
        "query_text": query["query_text"],
        "query_hash": query["query_hash"],
        "frozen_query_ref": query.get("frozen_query_ref"),
        "status": "ERROR",
        "error": f"Unknown provider: {provider}",
    }


def run_recovery(max_runtime_seconds: int = 1800, delay_between_queries: float = 0.5):
    """Execute recovery search with persistent checkpoint."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] NOVELTY_RECOVERY_V1 starting")
    print(f"  frozen manifest hash: see manifest")
    print(f"  recovery providers: {RECOVERY_PROVIDERS}")
    print(f"  max_runtime: {max_runtime_seconds}s")
    print(f"  delay between queries: {delay_between_queries}s")

    # Load frozen manifest (DO NOT MODIFY)
    frozen = load_frozen_query_manifest()
    print(f"  frozen queries: {frozen['query_count']}")
    print(f"  frozen manifest hash: {frozen['manifest_hash']}")

    # Load evidence packet (182 pairs)
    evidence = load_evidence_packet()
    print(f"  pairs: {evidence['pair_count']}")

    # Build recovery query manifest
    recovery_manifest = build_recovery_query_manifest(frozen, evidence)
    print(f"  recovery queries: {recovery_manifest['query_count']}")
    print(f"  recovery manifest hash: {recovery_manifest['manifest_hash']}")

    # Save recovery manifest
    save_recovery_manifest(recovery_manifest)
    print(f"  recovery manifest saved: {MANIFEST_PATH}")

    # Load checkpoint
    checkpoint = load_checkpoint()
    completed = set(checkpoint["completed_query_ids"])
    print(f"  checkpoint: {len(completed)} already completed")

    # Filter remaining queries
    remaining = [q for q in recovery_manifest["queries"] if q["query_id"] not in completed]
    print(f"  remaining: {len(remaining)} queries")

    # Execute
    t_start = time.time()
    results = checkpoint["results"]

    for i, query in enumerate(remaining):
        if time.time() - t_start > max_runtime_seconds:
            print(f"\n[{datetime.now(timezone.utc).isoformat()}] Max runtime reached. Checkpoint saved.")
            break

        try:
            result = execute_query(query)
        except Exception as e:
            result = {
                "query_id": query["query_id"],
                "pair_id": query["pair_id"],
                "query_type": query["query_type"],
                "provider": query["database"],
                "query_text": query["query_text"],
                "query_hash": query["query_hash"],
                "frozen_query_ref": query.get("frozen_query_ref"),
                "status": "ERROR",
                "error": f"Runner exception: {type(e).__name__}: {str(e)[:200]}",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }

        results.append(result)
        checkpoint["completed_query_ids"].append(query["query_id"])
        checkpoint["results"] = results

        # Save checkpoint every 10 queries
        if (i + 1) % 10 == 0:
            save_checkpoint(checkpoint)

        # Progress log
        elapsed = time.time() - t_start
        done = len(results)
        status_counter = Counter(r["status"] for r in results)
        print(f"  [{done}/{len(recovery_manifest['queries'])}] {elapsed:.1f}s elapsed | "
              f"{query['query_id'][:60]} | {result['status']} | "
              f"counts: {dict(status_counter)}")

        time.sleep(delay_between_queries)

    # Final save
    save_checkpoint(checkpoint)

    # Build aggregate
    status_counts = Counter(r["status"] for r in results)
    provider_status = {}
    for r in results:
        p = r["provider"]
        if p not in provider_status:
            provider_status[p] = Counter()
        provider_status[p][r["status"]] += 1

    aggregate = {
        "report_type": "novelty_recovery_v1_aggregate",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "recovery_manifest_hash": recovery_manifest["manifest_hash"],
        "frozen_manifest_hash": frozen["manifest_hash"],
        "total_queries_attempted": len(results),
        "total_queries_in_manifest": recovery_manifest["query_count"],
        "status_counts": dict(status_counts),
        "provider_status": {p: dict(c) for p, c in provider_status.items()},
        "rule": "Recovery namespace. Not authoritative. No D3 produced. Evidence for custodian only.",
    }

    with open(AGGREGATE_PATH, "w") as f:
        json.dump(aggregate, f, indent=2)

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] Recovery run complete.")
    print(f"  total attempted: {len(results)} / {recovery_manifest['query_count']}")
    print(f"  status counts: {dict(status_counts)}")
    print(f"  provider status: {dict({p: dict(c) for p, c in provider_status.items()})}")
    print(f"  results: {RESULTS_PATH}")
    print(f"  aggregate: {AGGREGATE_PATH}")
    print(f"  checkpoint: {CHECKPOINT_PATH}")

    return aggregate


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-runtime", type=int, default=1800, help="Max runtime in seconds")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between queries (s)")
    args = parser.parse_args()
    run_recovery(max_runtime_seconds=args.max_runtime, delay_between_queries=args.delay)
