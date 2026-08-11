#!/usr/bin/env python3
"""Fetch real arxiv papers for 10x corpus scaling (Phase 5).

Per No-Gaming Rule (FA3): real documents only, no synthetic data.
"""
import sys, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET, time, re, json

ROOT = pathlib.Path(__file__).resolve().parents[1]
NS = {"atom": "http://www.w3.org/2005/Atom"}

QUERIES = [
    ("thermoelectric", "thermoelectric"),
    ("thermoelectric_2", "Seebeck coefficient"),
    ("radiative_cooling", "radiative cooling"),
    ("radiative_cooling_2", "passive cooling"),
    ("pcm", "phase change material"),
    ("pcm_2", "latent heat storage"),
    ("water_harvesting", "atmospheric water harvesting"),
    ("water_harvesting_2", "MOF water sorbent"),
    ("sodium_battery", "sodium ion battery"),
    ("sodium_battery_2", "hard carbon anode"),
    ("electrochemical", "electrochemical water splitting"),
    ("piezoelectric", "piezoelectric energy harvesting"),
    ("desalination", "desalination membrane"),
    ("CO2_capture", "direct air capture CO2"),
    ("hydrogen", "hydrogen production solar"),
]

def fetch_arxiv(query, max_results=30):
    base_url = "http://export.arxiv.org/api/query"
    params = {"search_query": f"all:{query}", "start": "0",
              "max_results": str(max_results), "sortBy": "relevance"}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "DiscoveryEngine/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return ET.fromstring(resp.read().decode("utf-8", errors="replace"))

def extract_paper(entry):
    title = entry.findtext("atom:title", default="", namespaces=NS)
    title = re.sub(r"\s+", " ", title).strip()
    summary = entry.findtext("atom:summary", default="", namespaces=NS)
    summary = re.sub(r"\s+", " ", summary).strip()
    arxiv_url = entry.findtext("atom:id", default="", namespaces=NS)
    arxiv_id = arxiv_url.rstrip("/").split("/")[-1]
    published = entry.findtext("atom:published", default="", namespaces=NS)
    authors = [a.findtext("atom:name", default="", namespaces=NS)
               for a in entry.findall("atom:author", namespaces=NS)]
    return {"arxiv_id": arxiv_id, "title": title, "abstract": summary,
            "url": arxiv_url, "published": published, "authors": authors}

def to_text(paper, domain):
    return (f"TITLE: {paper['title']}\nARXIV ID: {paper['arxiv_id']}\n"
            f"URL: {paper['url']}\nRETRIEVAL DATE: 2026-08-05\n"
            f"RETRIEVAL METHOD: arxiv.org API\nSOURCE VERIFICATION: arxiv API XML\n"
            f"DOMAIN HINT: {domain}\nAUTHORS: {'; '.join(paper['authors'][:5])}\n"
            f"PUBLISHED: {paper['published']}\n\nABSTRACT:\n{paper['abstract']}\n")

seen_ids = set()
fetched = []
for domain, query in QUERIES:
    print(f"=== {domain}: '{query}' ===")
    try:
        root = fetch_arxiv(query, max_results=30)
        entries = root.findall("atom:entry", namespaces=NS)
        print(f"  got {len(entries)} entries")
        for entry in entries:
            paper = extract_paper(entry)
            if paper["arxiv_id"] in seen_ids:
                continue
            if not paper["title"] or not paper["abstract"]:
                continue
            seen_ids.add(paper["arxiv_id"])
            fetched.append((paper, domain))
        time.sleep(3)
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\nTotal unique papers: {len(fetched)}")

out_dir = ROOT / "data" / "ingestion" / "corpus_10x"
out_dir.mkdir(parents=True, exist_ok=True)
written = 0
for paper, domain in fetched:
    fname = f"{paper['arxiv_id'].replace('/', '_')}.txt"
    (out_dir / fname).write_text(to_text(paper, domain), encoding="utf-8")
    written += 1
print(f"Wrote {written} files to {out_dir}")

# Write manifest
manifest = {"fetched_at": "2026-08-05", "queries": [q for _, q in QUERIES],
            "paper_count": written,
            "papers": [{"arxiv_id": p["arxiv_id"], "domain": d, "title": p["title"]}
                       for p, d in fetched]}
(out_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Manifest written")
