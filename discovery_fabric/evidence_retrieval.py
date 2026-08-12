"""
Discovery Fabric — Evidence Retrieval Runner.

Retrieves real scientific evidence objects from working sources.
Target: 10,000 real evidence objects, normalized, hashed, provenance-preserved.

Sources (operational):
- Crossref (150M+ works)
- arXiv (2.4M+ preprints)
- Europe PMC (40M+ biomedical)
- PubMed (36M+ biomedical)

Sources (rate-limited, will retry):
- OpenAlex (resets midnight UTC)
- Semantic Scholar (rate-limited)
"""
import json
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors import crossref, arxiv, europepmc, pubmed

EVIDENCE_DIR = REPO / "discovery_fabric/evidence"
REPORTS_DIR = REPO / "discovery_fabric/reports"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 40 queries across 8 domains × 5 sub-queries each
# Designed to produce diverse, real scientific evidence
DOMAIN_QUERIES = {
    "materials": [
        "nanoparticle composite synthesis",
        "photodetector materials 2D",
        "polymer self-assembly",
        "metal-organic framework",
        "biomaterials scaffold",
    ],
    "energy": [
        "lithium battery solid electrolyte",
        "solar cell perovskite",
        "hydrogen fuel cell catalyst",
        "supercapacitor graphene",
        "thermoelectric material",
    ],
    "biotechnology": [
        "CRISPR gene editing delivery",
        "protein engineering directed evolution",
        "synthetic biology metabolic pathway",
        "biomarker disease detection",
        "tissue engineering organ",
    ],
    "computing": [
        "neural network architecture transformer",
        "quantum computing error correction",
        "federated learning privacy",
        "reinforcement learning robotics",
        "edge computing optimization",
    ],
    "mechanical": [
        "additive manufacturing lattice",
        "robotic actuator soft",
        "vibration damping metamaterial",
        "tribology surface coating",
        "fatigue life prediction",
    ],
    "chemical": [
        "catalyst CO2 reduction",
        "electrochemical synthesis organic",
        "catalytic asymmetric hydrogenation",
        "flow chemistry continuous",
        "photocatalytic water splitting",
    ],
    "environmental": [
        "carbon capture adsorbent",
        "water treatment membrane",
        "biodegradable plastic",
        "air pollution sensor",
        "soil remediation microbial",
    ],
    "neuroscience": [
        "brain computer interface electrode",
        "neurodegenerative disease mechanism",
        "neural circuit mapping",
        "memory consolidation sleep",
        "neuroplasticity rehabilitation",
    ],
}

# Target: ~10,000 objects from 40 queries × 250 results each
RESULTS_PER_QUERY = {
    "crossref": 50,    # 40 × 50 = 2000
    "arxiv": 50,       # 40 × 50 = 2000
    "europepmc": 50,   # 40 × 50 = 2000
    "pubmed": 50,      # 40 × 50 = 2000
    # Total: ~8000 from 4 sources. OpenAlex + S2 when available would add 4000+ more.
}


def run_retrieval(max_runtime_seconds: int = 2400):
    """Retrieve evidence objects from all working sources."""
    print(f"[{datetime.now(timezone.utc).isoformat()}] Discovery Fabric evidence retrieval starting")
    print(f"  target: ~{sum(v * 40 for v in RESULTS_PER_QUERY.values())} evidence objects")
    print(f"  max runtime: {max_runtime_seconds}s")

    all_evidence = []
    retrieval_log = []
    t_start = time.time()

    evidence_file = EVIDENCE_DIR / "evidence.jsonl"
    log_file = REPORTS_DIR / "retrieval_log.jsonl"

    with open(evidence_file, "w") as ef, open(log_file, "w") as lf:
        for domain, queries in DOMAIN_QUERIES.items():
            for query in queries:
                if time.time() - t_start > max_runtime_seconds:
                    print(f"\n[TIME LIMIT] Stopping at {len(all_evidence)} evidence objects")
                    break

                print(f"\n[{domain}] query: {query}")

                # Crossref
                if time.time() - t_start > max_runtime_seconds:
                    break
                print(f"  crossref...", end=" ", flush=True)
                try:
                    items = crossref.search(query, rows=RESULTS_PER_QUERY["crossref"])
                    for item in items:
                        item["domain"] = domain
                        item["query"] = query
                        ef.write(json.dumps(item, ensure_ascii=False) + "\n")
                        all_evidence.append(item)
                    log_entry = {"source": "crossref", "domain": domain, "query": query, "count": len(items), "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"{len(items)} items")
                except Exception as e:
                    log_entry = {"source": "crossref", "domain": domain, "query": query, "count": 0, "status": "error", "error": str(e)[:100], "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"ERROR: {str(e)[:60]}")
                time.sleep(0.3)

                # arXiv
                if time.time() - t_start > max_runtime_seconds:
                    break
                print(f"  arxiv...", end=" ", flush=True)
                try:
                    items = arxiv.search(query, max_results=RESULTS_PER_QUERY["arxiv"])
                    for item in items:
                        item["domain"] = domain
                        item["query"] = query
                        ef.write(json.dumps(item, ensure_ascii=False) + "\n")
                        all_evidence.append(item)
                    log_entry = {"source": "arxiv", "domain": domain, "query": query, "count": len(items), "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"{len(items)} items")
                except Exception as e:
                    log_entry = {"source": "arxiv", "domain": domain, "query": query, "count": 0, "status": "error", "error": str(e)[:100], "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"ERROR: {str(e)[:60]}")
                time.sleep(3.5)  # arXiv rate limit: 1 req per 3 sec

                # Europe PMC
                if time.time() - t_start > max_runtime_seconds:
                    break
                print(f"  europepmc...", end=" ", flush=True)
                try:
                    items, _ = europepmc.search(query, page_size=RESULTS_PER_QUERY["europepmc"])
                    for item in items:
                        item["domain"] = domain
                        item["query"] = query
                        ef.write(json.dumps(item, ensure_ascii=False) + "\n")
                        all_evidence.append(item)
                    log_entry = {"source": "europepmc", "domain": domain, "query": query, "count": len(items), "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"{len(items)} items")
                except Exception as e:
                    log_entry = {"source": "europepmc", "domain": domain, "query": query, "count": 0, "status": "error", "error": str(e)[:100], "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"ERROR: {str(e)[:60]}")
                time.sleep(0.3)

                # PubMed
                if time.time() - t_start > max_runtime_seconds:
                    break
                print(f"  pubmed...", end=" ", flush=True)
                try:
                    items = pubmed.search(query, retmax=RESULTS_PER_QUERY["pubmed"])
                    for item in items:
                        item["domain"] = domain
                        item["query"] = query
                        ef.write(json.dumps(item, ensure_ascii=False) + "\n")
                        all_evidence.append(item)
                    log_entry = {"source": "pubmed", "domain": domain, "query": query, "count": len(items), "status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"{len(items)} items")
                except Exception as e:
                    log_entry = {"source": "pubmed", "domain": domain, "query": query, "count": 0, "status": "error", "error": str(e)[:100], "timestamp": datetime.now(timezone.utc).isoformat()}
                    lf.write(json.dumps(log_entry) + "\n")
                    retrieval_log.append(log_entry)
                    print(f"ERROR: {str(e)[:60]}")
                time.sleep(0.5)

            if time.time() - t_start > max_runtime_seconds:
                break

    # Deduplicate by id
    seen_ids = set()
    unique = []
    for e in all_evidence:
        eid = e.get("id", "")
        if eid and eid not in seen_ids:
            seen_ids.add(eid)
            unique.append(e)

    elapsed = time.time() - t_start
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_retrieved": len(all_evidence),
        "unique_evidence": len(unique),
        "by_source": dict(Counter(e["source"] for e in unique)),
        "by_domain": dict(Counter(e.get("domain", "?") for e in unique)),
        "with_abstract": sum(1 for e in unique if e.get("abstract") and e["abstract"] != "UNAVAILABLE"),
        "with_authors": sum(1 for e in unique if e.get("authors") and e["authors"] != "UNAVAILABLE"),
        "with_publication_date": sum(1 for e in unique if e.get("publication_date") and e["publication_date"] != "UNAVAILABLE"),
        "elapsed_seconds": round(elapsed, 1),
        "retrieval_calls": len(retrieval_log),
        "successful_calls": sum(1 for r in retrieval_log if r["status"] == "success"),
        "failed_calls": sum(1 for r in retrieval_log if r["status"] != "success"),
    }

    print(f"\n[{datetime.now(timezone.utc).isoformat()}] RETRIEVAL COMPLETE")
    print(f"  total retrieved: {stats['total_retrieved']}")
    print(f"  unique evidence: {stats['unique_evidence']}")
    print(f"  by source: {stats['by_source']}")
    print(f"  by domain: {stats['by_domain']}")
    print(f"  with abstract: {stats['with_abstract']}")
    print(f"  elapsed: {stats['elapsed_seconds']}s")

    with open(REPORTS_DIR / "retrieval_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    return stats, unique


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-runtime", type=int, default=2400)
    args = parser.parse_args()
    run_retrieval(max_runtime_seconds=args.max_runtime)
