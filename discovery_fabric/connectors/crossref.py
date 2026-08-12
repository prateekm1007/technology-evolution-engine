"""
Crossref connector — searches 150M+ scientific works.

Free, no auth required (polite pool with mailto in User-Agent).
Rate limit: ~50 req/s polite pool.
"""
import json
import urllib.request
import urllib.parse
import time
from typing import List
from ..normalization.evidence_schema import create_evidence_item

CROSSREF_BASE = "https://api.crossref.org/works"
UA = "DiscoveryFabric/1.0 (mailto:discovery-fabric@example.org)"


def search(query: str, rows: int = 25, offset: int = 0) -> List[dict]:
    """Search Crossref. Returns list of EvidenceItem dicts."""
    url = f"{CROSSREF_BASE}?rows={rows}&offset={offset}&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    items = data.get("message", {}).get("items", [])
    results = []
    for item in items:
        doi = item.get("DOI", "")
        title = (item.get("title", [""]) or [""])[0] if item.get("title") else ""
        abstract = item.get("abstract", "") or ""

        # Authors
        authors = []
        for a in item.get("author", []):
            name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if name:
                authors.append(name)

        # Date
        pub_date = ""
        if item.get("published", {}).get("date-parts"):
            dp = item["published"]["date-parts"][0]
            if dp:
                pub_date = "-".join(str(p) for p in dp)

        # References/citations
        refs = []
        for ref in item.get("reference", []):
            if ref.get("DOI"):
                refs.append(ref["DOI"])

        results.append(create_evidence_item(
            source="crossref",
            source_id=doi or item.get("URL", ""),
            source_type="scientific",
            title=title,
            retrieval_method="crossref_rest_api",
            source_uri=f"https://doi.org/{doi}" if doi else item.get("URL", ""),
            abstract=abstract if abstract else None,
            authors=authors if authors else None,
            organizations=[item.get("publisher", "")] if item.get("publisher") else None,
            publication_date=pub_date if pub_date else None,
            references=refs if refs else None,
            license=item.get("license", [{}])[0].get("URL", "") if item.get("license") else None,
        ))

    return results
