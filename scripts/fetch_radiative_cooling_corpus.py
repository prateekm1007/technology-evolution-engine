#!/usr/bin/env python3
"""
Fetch 25 arxiv papers on radiative cooling for cross-domain discovery.

Per cycle 48 task 3: 'Fetch cross-domain corpus — 20+ N2 fixation or
radiative cooling papers'.

Choice: radiative cooling — it provides rich mechanistic analogies to
existing corpus (PCM/thermal management, Stefan-Boltzmann, BaSO4 already
in patterns). The cross-domain bridge hypothesis: radiative cooling papers
will share concepts (thermal radiation, sub-ambient, emissivity) with
existing thermoelectric/battery-thermal-management content, but the
applications are different. This should produce non-obvious Swanson
bridges.

Uses the arxiv API (http://export.arxiv.org/api/query). Real papers,
real abstracts, real arxiv IDs. No fabrication.

Output: data/ingestion/radiative_cooling/<arxiv_id>.txt
Format matches existing data/ingestion/papers/*.txt files.
"""
import sys
import pathlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "ingestion" / "radiative_cooling"

# arxiv atom namespace
NS = {"atom": "http://www.w3.org/2005/Atom"}

# Search query: radiative cooling papers in applied physics / optics / materials
# Sort by relevance, fetch 30 to allow for some misses
QUERY = "radiative cooling sub-ambient emissivity"
MAX_RESULTS = 30


def fetch_arxiv_results(query: str, max_results: int = 30, start: int = 0):
    """Query the arxiv API and return parsed XML root."""
    base_url = "http://export.arxiv.org/api/query"
    # arxiv search_query syntax: all="some terms" (with quotes for exact phrase)
    # urlencode handles space-to-+ conversion correctly
    search_query = f'all:"{query}"'
    params = {
        "search_query": search_query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    print(f"  fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "DiscoveryEngine/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return ET.fromstring(body)


def extract_paper_text(entry) -> dict:
    """Extract a normalized paper dict from an arxiv atom <entry>."""
    title = entry.findtext("atom:title", default="", namespaces=NS)
    title = re.sub(r"\s+", " ", title).strip()
    summary = entry.findtext("atom:summary", default="", namespaces=NS)
    summary = re.sub(r"\s+", " ", summary).strip()
    arxiv_url = entry.findtext("atom:id", default="", namespaces=NS)
    # arxiv id is the last path component
    arxiv_id = arxiv_url.rstrip("/").split("/")[-1]
    published = entry.findtext("atom:published", default="", namespaces=NS)
    authors = [a.findtext("atom:name", default="", namespaces=NS)
               for a in entry.findall("atom:author", namespaces=NS)]
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "abstract": summary,
        "url": arxiv_url,
        "published": published,
        "authors": authors,
    }


def to_text_file(paper: dict) -> str:
    """Render the paper dict in the canonical ingestion text format."""
    authors_str = "; ".join(paper["authors"][:5])
    return (
        f"TITLE: {paper['title']}\n"
        f"ARXIV ID: {paper['arxiv_id']}\n"
        f"URL: {paper['url']}\n"
        f"RETRIEVAL DATE: 2026-08-05\n"
        f"RETRIEVAL METHOD: arxiv.org API (export.arxiv.org/api/query)\n"
        f"SOURCE VERIFICATION: arxiv API XML response (PR-19)\n"
        f"DOMAIN HINT: radiative cooling\n"
        f"AUTHORS: {authors_str}\n"
        f"PUBLISHED: {paper['published']}\n"
        f"\n"
        f"ABSTRACT:\n"
        f"{paper['abstract']}\n"
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUT_DIR}")

    # Try multiple queries to ensure topic diversity
    queries = [
        "radiative cooling",
        "passive daytime radiative cooling",
        "radiative cooling paint",
        "radiative cooling metamaterial",
        "radiative sky cooling",
        "sub-ambient radiative cooling",
        "radiative cooling polymer",
        "radiative cooling nanoparticle",
        "daytime radiative cooling film",
        "radiative cooling cooling power",
    ]

    seen_ids = set()
    fetched = []

    for q in queries:
        print(f"\n=== Query: {q} ===")
        try:
            root = fetch_arxiv_results(q, max_results=20)
        except Exception as e:
            print(f"  ERROR fetching query '{q}': {e}")
            continue
        entries = root.findall("atom:entry", namespaces=NS)
        print(f"  got {len(entries)} entries")
        for entry in entries:
            try:
                paper = extract_paper_text(entry)
            except Exception as e:
                print(f"    skip (parse error): {e}")
                continue
            if paper["arxiv_id"] in seen_ids:
                continue
            if not paper["title"] or not paper["abstract"]:
                continue
            # Skip non-radiative-cooling hits (arxiv returns loose matches)
            text = (paper["title"] + " " + paper["abstract"]).lower()
            if "radiative cooling" not in text and "radiant cooling" not in text and "sky cooling" not in text:
                continue
            # Exclude astrophysics / atmospheric science / numerical modeling papers
            # that mention "radiative cooling" but are not materials-focused PDRC
            EXCLUDE_TERMS = [
                "galactic", "accretion", "black hole", "mhd simulation", "mhd ",
                "astrophys", "interstellar", "saber", "no radiative cooling",
                "no emission", "timed/", "shock", "clump", "numerical simulation",
                "cosmolog", "galaxy", "nebula", "star formation", "ionized",
                "clump", "radiative cooling function", "cooling function",
                "atomic cooling", "superconducting resonator",
                "double-clad fiber", "fiber amplifier",
                "radiative transfer", "radiative equilibrium",
                "mean precipitation", "climate model",
            ]
            if any(term in text for term in EXCLUDE_TERMS):
                continue
            # Require at least one MATERIALS / PDRC indicator
            MATERIALS_TERMS = [
                "sub-ambient", "subambient", "ambient temperature", "cooling power",
                "emissivity", "paint", "coating", "film", "metamaterial",
                "pdrc", "sky window", "thermal radiation", "passive cooling",
                "solar reflectance", "nanoparticle", "polymer", "porous",
                "thermal management", "photonic",
            ]
            if not any(term in text for term in MATERIALS_TERMS):
                continue
            seen_ids.add(paper["arxiv_id"])
            fetched.append(paper)
        time.sleep(3)  # arxiv asks for 3s between requests
        if len(fetched) >= 30:
            print(f"  reached target of 30 papers, stopping early")
            break

    print(f"\nTotal unique radiative-cooling papers fetched: {len(fetched)}")

    # Write files
    written = 0
    for paper in fetched:
        out_path = OUT_DIR / f"{paper['arxiv_id'].replace('/', '_')}.txt"
        out_path.write_text(to_text_file(paper), encoding="utf-8")
        written += 1
        print(f"  wrote {out_path.name} — {paper['title'][:80]}")

    print(f"\nWrote {written} files to {OUT_DIR}")

    # Write a manifest
    manifest_path = OUT_DIR / "_manifest.json"
    import json
    manifest = {
        "fetched_at": "2026-08-05",
        "query_strategy": queries,
        "paper_count": written,
        "papers": [
            {"arxiv_id": p["arxiv_id"], "title": p["title"], "url": p["url"]}
            for p in fetched
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest: {manifest_path}")


if __name__ == "__main__":
    main()
