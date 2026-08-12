"""
Patent Discovery Mining — Pilot Runner.

Fetches 500 patent families across:
- 8 technology domains (materials, energy, mechanical, electronics, computing/AI, biotech, chemical, manufacturing)
- 3 countries (US, CN, IN)

Outputs:
- patent_discovery/families/pilot_patents.jsonl  — all fetched patents
- patent_discovery/families/pilot_families.json  — family-deduplicated
- patent_discovery/reports/PILOT_INGESTION_REPORT_V1.md

This is INFRASTRUCTURE VALIDATION, not scientific evidence of discovery.
"""
import json
import time
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from patent_discovery.ingestion.google_patents_adapter import (
    search_patents,
    fetch_patent_detail,
)

PILOT_DIR = REPO / "patent_discovery"
FAMILIES_DIR = PILOT_DIR / "families"
REPORTS_DIR = PILOT_DIR / "reports"

# 8 domains × 3 countries × ~21 patents = ~504 patents
# Each domain gets a representative query
DOMAIN_QUERIES = {
    "materials": "advanced materials synthesis nanoparticle composite",
    "energy": "battery energy storage lithium ion solid state",
    "mechanical_systems": "mechanical actuator gear transmission system",
    "electronics": "semiconductor circuit transistor integrated",
    "computing_ai": "machine learning neural network deep learning",
    "biotechnology": "biotechnology gene editing CRISPR enzyme",
    "chemical_processes": "chemical process catalyst reaction synthesis",
    "manufacturing": "manufacturing additive 3D printing fabrication",
}

COUNTRIES = ["US", "CN", "IN"]
PER_DOMAIN_PER_COUNTRY = 21  # 8 × 3 × 21 = 504 target


def run_pilot(max_runtime_seconds: int = 2400, detail_fetch_ratio: float = 0.4):
    """Run the 500-family pilot.

    Args:
        max_runtime_seconds: hard time limit
        detail_fetch_ratio: fraction of search results to fetch full details for
            (details are expensive; we sample to keep pilot tractable)
    """
    print(f"[{datetime.now(timezone.utc).isoformat()}] PATENT DISCOVERY PILOT starting")
    print(f"  target: {len(DOMAIN_QUERIES)} domains × {len(COUNTRIES)} countries × {PER_DOMAIN_PER_COUNTRY} patents = {len(DOMAIN_QUERIES) * len(COUNTRIES) * PER_DOMAIN_PER_COUNTRY}")
    print(f"  max runtime: {max_runtime_seconds}s")
    print(f"  detail fetch ratio: {detail_fetch_ratio}")
    print()

    all_patents = []
    search_log = []
    t_start = time.time()

    for domain, query in DOMAIN_QUERIES.items():
        for country in COUNTRIES:
            if time.time() - t_start > max_runtime_seconds:
                print(f"\n[TIME LIMIT] Stopping at {len(all_patents)} patents")
                break

            print(f"[{domain}/{country}] searching: {query[:50]}...")

            # Search — fetch multiple pages if needed
            # Google Patents returns ~100 results max per page; we filter post-hoc by country prefix
            domain_country_patents = []
            page = 0
            max_pages = 4  # up to 400 results to filter from
            while len(domain_country_patents) < PER_DOMAIN_PER_COUNTRY and page < max_pages:
                if time.time() - t_start > max_runtime_seconds:
                    break

                results, status = search_patents(query, num=100, page=page, country=country)
                search_log.append({
                    "domain": domain,
                    "country": country,
                    "page": page,
                    "query": query,
                    "status": status,
                    "results_count": len(results),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                if status != "success" or not results:
                    break

                for r in results:
                    if len(domain_country_patents) >= PER_DOMAIN_PER_COUNTRY:
                        break
                    # Filter by country prefix (post-hoc)
                    pid = r.get("patent_id", "")
                    if pid.startswith(country):
                        r["domain"] = domain
                        r["search_country"] = country
                        domain_country_patents.append(r)

                page += 1
                time.sleep(0.5)  # respectful delay

            # Fetch details for a sample of the search results
            detail_count = max(1, int(len(domain_country_patents) * detail_fetch_ratio))
            for i, patent_summary in enumerate(domain_country_patents):
                if time.time() - t_start > max_runtime_seconds:
                    break

                if i < detail_count:
                    print(f"  [detail {i+1}/{detail_count}] {patent_summary['patent_id']}")
                    detail, dstatus = fetch_patent_detail(patent_summary["patent_id"])
                    if dstatus == "success" and detail:
                        detail["domain"] = domain
                        detail["search_country"] = country
                        all_patents.append(detail)
                    else:
                        # Fall back to search summary
                        patent_summary["detail_status"] = dstatus
                        all_patents.append(patent_summary)
                    time.sleep(0.3)  # respectful delay
                else:
                    # Just use search summary
                    patent_summary["detail_status"] = "skipped"
                    all_patents.append(patent_summary)

            print(f"  collected: {len(domain_country_patents)} ({detail_count} with details)")

        if time.time() - t_start > max_runtime_seconds:
            print(f"\n[TIME LIMIT] Stopping")
            break

    # Save raw patents
    FAMILIES_DIR.mkdir(parents=True, exist_ok=True)
    with open(FAMILIES_DIR / "pilot_patents.jsonl", "w") as f:
        for p in all_patents:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Save search log
    with open(REPORTS_DIR / "pilot_search_log.json", "w") as f:
        json.dump(search_log, f, indent=2, ensure_ascii=False)

    # Family deduplication (by patent_id — true family dedup would use priority numbers)
    seen_ids = set()
    unique_patents = []
    for p in all_patents:
        pid = p.get("patent_id", "")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_patents.append(p)

    # Stats
    elapsed = time.time() - t_start
    stats = {
        "total_search_results": len(all_patents),
        "unique_patents": len(unique_patents),
        "with_details": sum(1 for p in unique_patents if p.get("claims")),
        "without_details": sum(1 for p in unique_patents if not p.get("claims")),
        "by_country": dict(Counter(p.get("patent_id", "")[:2] for p in unique_patents)),
        "by_domain": dict(Counter(p.get("domain", "unknown") for p in unique_patents)),
        "by_country_domain": {
            d: dict(Counter(p.get("patent_id", "")[:2] for p in unique_patents if p.get("domain") == d))
            for d in DOMAIN_QUERIES
        },
        "elapsed_seconds": round(elapsed, 1),
        "search_calls": len(search_log),
        "search_successes": sum(1 for s in search_log if s["status"] == "success"),
        "search_failures": sum(1 for s in search_log if s["status"] != "success"),
    }

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] PILOT COMPLETE")
    print(f"  total patents: {stats['total_search_results']}")
    print(f"  unique patents: {stats['unique_patents']}")
    print(f"  with full details: {stats['with_details']}")
    print(f"  by country: {stats['by_country']}")
    print(f"  by domain: {stats['by_domain']}")
    print(f"  elapsed: {stats['elapsed_seconds']}s")

    with open(REPORTS_DIR / "pilot_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    # Save unique patents as the family file
    with open(FAMILIES_DIR / "pilot_families.json", "w") as f:
        json.dump({
            "pilot_type": "patent_discovery_pilot_v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_patents": len(unique_patents),
            "patents": unique_patents,
        }, f, indent=2, ensure_ascii=False)

    return stats, unique_patents


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-runtime", type=int, default=2400, help="Max runtime in seconds")
    parser.add_argument("--detail-ratio", type=float, default=0.4, help="Fraction to fetch full details")
    args = parser.parse_args()
    run_pilot(max_runtime_seconds=args.max_runtime, detail_fetch_ratio=args.detail_ratio)
