"""
PubMed E-utilities connector — searches 36M+ biomedical citations.

Free, no auth required (3 req/s without API key).
"""
import json
import urllib.request
import urllib.parse
import time
from typing import List
from ..normalization.evidence_schema import create_evidence_item

PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
UA = "DiscoveryFabric/1.0"


def search_ids(query: str, retmax: int = 25) -> List[str]:
    """Search PubMed for PMIDs."""
    url = f"{PUBMED_ESEARCH}?db=pubmed&term={urllib.parse.quote(query)}&retmax={retmax}&retmode=json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_summaries(pmids: List[str]) -> List[dict]:
    """Fetch summary records for a list of PMIDs."""
    if not pmids:
        return []
    time.sleep(0.4)  # respect 3 req/s limit
    url = f"{PUBMED_ESUMMARY}?db=pubmed&id={','.join(pmids)}&retmode=json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    results = []
    result = data.get("result", {})
    for pmid in pmids:
        item = result.get(pmid, {})
        if not item:
            continue

        title = item.get("title", "")
        pub_date = item.get("pubdate", "")

        authors = []
        for author in item.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name)

        journal = item.get("fulljournalname", "")
        doi = ""
        for aid in item.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")

        results.append(create_evidence_item(
            source="pubmed",
            source_id=pmid,
            source_type="scientific",
            title=title,
            retrieval_method="pubmed_eutils",
            source_uri=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            authors=authors if authors else None,
            organizations=[journal] if journal else None,
            publication_date=pub_date if pub_date else None,
            license="PubMed",
        ))

    return results


def search(query: str, retmax: int = 25) -> List[dict]:
    """Search PubMed. Returns list of EvidenceItem dicts."""
    pmids = search_ids(query, retmax)
    if not pmids:
        return []
    return fetch_summaries(pmids)
