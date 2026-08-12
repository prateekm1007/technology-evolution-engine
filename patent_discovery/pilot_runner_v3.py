"""
Patent Discovery Mining — Pilot Runner V3.

REALITY CHECK: Direct patent APIs (Google Patents, PatentsView, EPO OPS)
are all rate-limited or blocked in this environment. OpenAlex budget is
exhausted (429). Crossref is operational.

APPROACH: Use Crossref to find patent-analysis and patent-related literature
across 8 technology domains. This is NOT the same as mining patents directly,
but it demonstrates the full pipeline:
  ingestion → family dedup → mechanism extraction → graph → discovery modes

The pilot is HONESTLY LABELED as using Crossref patent-literature as a proxy.
A production system would use direct patent APIs (USPTO/CNIPA/IP India) which
require either:
  - Different rate limits
  - API keys
  - Bulk data access arrangements
  - On-premise deployment

The infrastructure built here (graph schema, discovery modes, prior-art
firewall, scoring) is patent-source-agnostic and will work with real patent
data when API access is available.
"""
import json
import time
import hashlib
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

PILOT_DIR = REPO / "patent_discovery"
FAMILIES_DIR = PILOT_DIR / "families"
REPORTS_DIR = PILOT_DIR / "reports"

# 8 domains × ~63 records each = 504 target
DOMAIN_QUERIES = {
    "materials": "patent nanoparticle composite material synthesis",
    "energy": "patent lithium battery solid state electrolyte",
    "mechanical_systems": "patent gear transmission actuator mechanism",
    "electronics": "patent semiconductor transistor circuit integrated",
    "computing_ai": "patent neural network machine learning",
    "biotechnology": "patent CRISPR gene editing enzyme",
    "chemical_processes": "patent catalyst chemical reaction synthesis",
    "manufacturing": "patent additive manufacturing 3D printing",
}

PER_DOMAIN = 63  # 8 × 63 = 504
UA = "PatentDiscoveryMining/1.0 (mailto:patent-discovery@example.org)"


def search_crossref(query: str, rows: int = 100, offset: int = 0) -> tuple:
    """Search Crossref for patent-related literature."""
    url = f"https://api.crossref.org/works?rows={rows}&offset={offset}&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        items = data.get("message", {}).get("items", [])
        return items, "success"
    except Exception as e:
        return [], f"error: {type(e).__name__}: {str(e)[:100]}"


def normalize_crossref_to_patent_record(item: dict, domain: str) -> dict:
    """Normalize a Crossref record into our patent-like schema."""
    doi = item.get("DOI", "")
    title = (item.get("title", [""]) or [""])[0] if item.get("title") else ""
    abstract = item.get("abstract", "") or ""
    if abstract and len(abstract) > 2000:
        abstract = abstract[:2000] + "..."

    # Authors
    authors = []
    for a in item.get("author", []):
        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if name:
            authors.append(name)

    # Date
    date_val = ""
    if item.get("published", {}).get("date-parts"):
        dp = item["published"]["date-parts"][0]
        if dp:
            date_val = "-".join(str(p) for p in dp)

    # References (cited patents proxy)
    cited = []
    for ref in item.get("reference", []):
        if ref.get("DOI"):
            cited.append({"patent_number": ref["DOI"], "date": ""})

    # Country inference from Crossref — not a true patent country
    # We assign country based on publisher location if available, else "XX"
    country = "XX"
    publisher = item.get("publisher", "").lower()
    if "elsevier" in publisher or "ieee" in publisher or "acm" in publisher:
        country = "US"  # publisher country, NOT patent country
    elif "springer" in publisher or "wiley" in publisher:
        country = "EU"
    elif "cn" in publisher.lower() or "china" in publisher.lower():
        country = "CN"

    record = {
        "patent_id": f"CR-{doi}" if doi else f"CR-{hashlib.sha256(title.encode()).hexdigest()[:12]}",
        "title": title,
        "abstract": abstract,
        "filing_date": date_val,
        "grant_date": "",
        "publication_date": date_val,
        "country": country,
        "inventors": authors,
        "assignees": [{"name": item.get("publisher", ""), "type": "publisher"}],
        "classifications": {"cpc": [], "ipc": []},
        "cited_patents": cited,
        "citing_patents": [],
        "claims": [],
        "description_excerpt": abstract[:500] if abstract else "",
        "domain": domain,
        "source": "Crossref (patent-literature proxy)",
        "source_url": f"https://doi.org/{doi}" if doi else "",
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "honest_label": "PATENT_LITERATURE_PROXY — not a direct patent record. Direct patent APIs were unavailable in this environment.",
    }

    # Compute hash
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    record["record_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return record


def run_pilot_v3(max_runtime_seconds: int = 300):
    """Run pilot using Crossref as patent-literature proxy."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] PATENT DISCOVERY PILOT V3 starting")
    print(f"  source: Crossref (patent-literature proxy)")
    print(f"  target: {len(DOMAIN_QUERIES)} domains × {PER_DOMAIN} records = {len(DOMAIN_QUERIES) * PER_DOMAIN}")
    print(f"  max runtime: {max_runtime_seconds}s")
    print(f"  HONEST LABEL: This is patent-LITERATURE, not direct patent records.")
    print()

    all_records = []
    fetch_log = []
    t_start = time.time()

    for domain, query in DOMAIN_QUERIES.items():
        if time.time() - t_start > max_runtime_seconds:
            break

        print(f"[{domain}] searching: {query[:50]}...")

        collected = 0
        offset = 0
        while collected < PER_DOMAIN and offset < 200:
            if time.time() - t_start > max_runtime_seconds:
                break

            items, status = search_crossref(query, rows=min(100, PER_DOMAIN - collected), offset=offset)
            fetch_log.append({
                "domain": domain,
                "query": query,
                "offset": offset,
                "status": status,
                "results_count": len(items),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            if status != "success" or not items:
                break

            for item in items:
                if collected >= PER_DOMAIN:
                    break
                record = normalize_crossref_to_patent_record(item, domain)
                all_records.append(record)
                collected += 1

            offset += len(items)
            time.sleep(0.5)

        print(f"  collected: {collected}")

    # Save
    FAMILIES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(FAMILIES_DIR / "pilot_patents.jsonl", "w") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(REPORTS_DIR / "pilot_fetch_log.json", "w") as f:
        json.dump(fetch_log, f, indent=2, ensure_ascii=False)

    # Deduplicate by patent_id
    seen_ids = set()
    unique = []
    for r in all_records:
        pid = r.get("patent_id", "")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique.append(r)

    elapsed = time.time() - t_start
    stats = {
        "total_fetched": len(all_records),
        "unique_records": len(unique),
        "with_abstract": sum(1 for r in unique if r.get("abstract")),
        "with_citations": sum(1 for r in unique if r.get("cited_patents")),
        "by_domain": dict(Counter(r.get("domain", "?") for r in unique)),
        "by_country": dict(Counter(r.get("country", "?") for r in unique)),
        "fetch_calls": len(fetch_log),
        "fetch_successes": sum(1 for f in fetch_log if f["status"] == "success"),
        "elapsed_seconds": round(elapsed, 1),
        "source": "Crossref (patent-literature proxy)",
        "honest_label": "PATENT_LITERATURE_PROXY — direct patent APIs were unavailable",
    }

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] PILOT V3 COMPLETE")
    print(f"  total fetched: {stats['total_fetched']}")
    print(f"  unique: {stats['unique_records']}")
    print(f"  with abstract: {stats['with_abstract']}")
    print(f"  with citations: {stats['with_citations']}")
    print(f"  by domain: {stats['by_domain']}")
    print(f"  by country: {stats['by_country']}")
    print(f"  elapsed: {stats['elapsed_seconds']}s")

    with open(REPORTS_DIR / "pilot_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    with open(FAMILIES_DIR / "pilot_families.json", "w") as f:
        json.dump({
            "pilot_type": "patent_discovery_pilot_v3_crossref_proxy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_records": len(unique),
            "honest_label": "PATENT_LITERATURE_PROXY — Crossref records about patents, not direct patent records",
            "records": unique,
        }, f, indent=2, ensure_ascii=False)

    return stats, unique


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-runtime", type=int, default=300)
    args = parser.parse_args()
    run_pilot_v3(max_runtime_seconds=args.max_runtime)
