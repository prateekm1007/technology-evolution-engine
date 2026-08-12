"""
arXiv connector — searches 2.4M+ preprints.

Free, no auth required.
Rate limit: 1 request per 3 seconds (recommended).
"""
import json
import urllib.request
import urllib.parse
import re
import xml.etree.ElementTree as ET
from typing import List
from ..normalization.evidence_schema import create_evidence_item

ARXIV_BASE = "http://export.arxiv.org/api/query"
UA = "DiscoveryFabric/1.0"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def search(query: str, max_results: int = 25, start: int = 0) -> List[dict]:
    """Search arXiv. Returns list of EvidenceItem dicts."""
    url = f"{ARXIV_BASE}?search_query=all:{urllib.parse.quote(query)}&start={start}&max_results={max_results}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
    except Exception:
        return []

    try:
        root = ET.fromstring(xml_data)
    except Exception:
        return []

    results = []
    for entry in root.findall("atom:entry", NS):
        arxiv_id = ""
        id_url = entry.find("atom:id", NS)
        if id_url is not None and id_url.text:
            arxiv_id = id_url.text.split("/abs/")[-1] if "/abs/" in id_url.text else id_url.text

        title = ""
        title_el = entry.find("atom:title", NS)
        if title_el is not None and title_el.text:
            title = " ".join(title_el.text.split())  # normalize whitespace

        abstract = ""
        summary = entry.find("atom:summary", NS)
        if summary is not None and summary.text:
            abstract = " ".join(summary.text.split())

        pub_date = ""
        published = entry.find("atom:published", NS)
        if published is not None and published.text:
            pub_date = published.text[:10]

        authors = []
        for author in entry.findall("atom:author", NS):
            name = author.find("atom:name", NS)
            if name is not None and name.text:
                authors.append(name.text)

        # DOI if available
        doi_el = entry.find("arxiv:doi", NS)
        doi = doi_el.text if doi_el is not None else None

        # Categories (arXiv classifications)
        classifications = []
        for cat in entry.findall("atom:category", NS):
            term = cat.get("term", "")
            if term:
                classifications.append({"scheme": "arxiv", "code": term})

        results.append(create_evidence_item(
            source="arxiv",
            source_id=arxiv_id,
            source_type="scientific",
            title=title,
            retrieval_method="arxiv_api",
            source_uri=f"https://arxiv.org/abs/{arxiv_id}",
            abstract=abstract if abstract else None,
            authors=authors if authors else None,
            publication_date=pub_date if pub_date else None,
            classifications=classifications if classifications else None,
            license="arXiv preprint license",
        ))

    return results
