"""
Europe PMC connector — searches 40M+ biomedical publications.

Free, no auth required.
Rate limit: reasonable use (no documented hard limit).
"""
import json
import urllib.request
import urllib.parse
from typing import List
from ..normalization.evidence_schema import create_evidence_item

EUROPEPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
UA = "DiscoveryFabric/1.0"


def search(query: str, page_size: int = 25, cursor_mark: str = "*") -> tuple:
    """Search Europe PMC. Returns (list of EvidenceItem dicts, next_cursor_mark)."""
    url = f"{EUROPEPMC_BASE}?query={urllib.parse.quote(query)}&format=json&pageSize={page_size}&cursorMark={urllib.parse.quote(cursor_mark)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return [], "*"

    next_cursor = data.get("nextCursorMark", "*")
    results = []
    for item in data.get("resultList", {}).get("result", []):
        pmid = item.get("pmid", "")
        doi = item.get("doi", "")
        source_id = doi or pmid or item.get("id", "")

        title = item.get("title", "")
        abstract = item.get("abstractText", "") or ""

        # Authors
        author_str = item.get("authorString", "")
        authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []

        pub_date = ""
        if item.get("pubYear"):
            pub_date = item["pubYear"]
        if item.get("firstPublicationDate"):
            pub_date = item["firstPublicationDate"][:10]

        # Journal/org
        journal = item.get("journalTitle", "")

        results.append(create_evidence_item(
            source="europepmc",
            source_id=source_id,
            source_type="scientific",
            title=title,
            retrieval_method="europepmc_rest_api",
            source_uri=f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/MED/{pmid}" if pmid else "",
            abstract=abstract if abstract else None,
            authors=authors if authors else None,
            organizations=[journal] if journal else None,
            publication_date=pub_date if pub_date else None,
            license=item.get("license", "") if item.get("license") else None,
        ))

    return results, next_cursor
