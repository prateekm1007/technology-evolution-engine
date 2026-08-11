#!/usr/bin/env python3
"""Fetch real arxiv papers for 50x corpus scaling (Phase 5).

Per No-Gaming Rule (FA3): real documents only, no synthetic data.
Target: ~1,500 additional papers to reach ~2,000 total.
"""
import sys, pathlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET, time, re, json

ROOT = pathlib.Path(__file__).resolve().parents[1]
NS = {"atom": "http://www.w3.org/2005/Atom"}

QUERIES = [
    "thermoelectric", "Seebeck coefficient", "radiative cooling", "passive cooling",
    "phase change material", "latent heat", "water harvesting", "MOF",
    "sodium battery", "hard carbon", "water splitting", "hydrogen",
    "piezoelectric", "desalination", "CO2 capture", "supercapacitor",
    "fuel cell", "electrocatalysis", "photocatalysis", "perovskite",
    "battery anode", "battery cathode", "electrolyte", "solid state battery",
    "thermal management", "heat transfer", "solar cell", "photovoltaic",
    "thermoelectric generator", "ZT figure merit", "nanoparticle",
    "nanocomposite", "thin film", "ceramic", "polymer electrolyte",
    "carbon nanotube", "graphene oxide", "metal oxide", "semiconductor",
    "catalyst", "electrode", "supercapacitor", "energy storage",
    "hydrogen storage", "ammonia synthesis", "nitrogen fixation",
    "battery thermal", "insulation", "thermal conductivity",
    "solar absorber", "selective surface", "Stirling engine",
]

def fetch_arxiv(query, max_results=50, start=0):
    base_url = "http://export.arxiv.org/api/query"
    params = {"search_query": f"all:{query}", "start": str(start),
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
    return {"arxiv_id": arxiv_id, "title": title, "abstract": summary,
            "url": arxiv_url, "published": published}

def to_text(paper, domain):
    return (f"TITLE: {paper['title']}\nARXIV ID: {paper['arxiv_id']}\n"
            f"URL: {paper['url']}\nRETRIEVAL DATE: 2026-08-05\n"
            f"RETRIEVAL METHOD: arxiv.org API\nSOURCE VERIFICATION: arxiv API XML\n"
            f"DOMAIN HINT: {domain}\nPUBLISHED: {paper['published']}\n\nABSTRACT:\n{paper['abstract']}\n")

out_dir = ROOT / "data" / "ingestion" / "corpus_50x"
out_dir.mkdir(parents=True, exist_ok=True)

# Load existing IDs to avoid duplicates
seen_ids = set()
for d in ["papers", "patents", "radiative_cooling", "sib_corpus", "real", "corpus_10x"]:
    p = ROOT / "data" / "ingestion" / d
    if p.exists():
        for f in p.glob("*.txt"):
            seen_ids.add(f.stem)

print(f"Existing papers: {len(seen_ids)}")
fetched = 0

for query in QUERIES:
    print(f"=== {query} ===")
    try:
        root = fetch_arxiv(query, max_results=50)
        entries = root.findall("atom:entry", namespaces=NS)
        for entry in entries:
            paper = extract_paper(entry)
            if paper["arxiv_id"] in seen_ids:
                continue
            if not paper["title"] or not paper["abstract"]:
                continue
            seen_ids.add(paper["arxiv_id"])
            fname = f"{paper['arxiv_id'].replace('/', '_')}.txt"
            (out_dir / fname).write_text(to_text(paper, query), encoding="utf-8")
            fetched += 1
        print(f"  got {len(entries)} entries, total fetched: {fetched}")
        time.sleep(3)
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\nTotal new papers fetched: {fetched}")
print(f"Total unique papers across all corpora: {len(seen_ids)}")
