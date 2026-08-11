"""
novelty_audit.search.search_executor — Execute frozen queries against independent databases.

Executes pre-registered, frozen queries against:
1. OpenAlex (broad scholarly)
2. Semantic Scholar (independent scholarly graph)
3. Crossref (DOI/metadata corroboration)

NO TEE. NO LLM. NO human judgment. Pure API retrieval.

Failed APIs → UNAVAILABLE (never treated as zero results).
Search failures → never interpreted as novelty.
"""
import hashlib
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from novelty_audit.search.query_generator import SearchQuery


@dataclass
class SearchResult:
    """Result of a single search query."""
    search_id: str  # Same as query_id
    pair_id: str
    database: str
    query_text: str
    query_hash: str
    search_timestamp: str  # Real UTC
    result_count: int
    result_ids: List[str]  # Top result IDs (DOIs or database IDs)
    result_titles: List[str]  # Top result titles (for custodian review)
    retrieval_method: str  # "api" or "unavailable"
    result_manifest_hash: str  # Hash of result set
    status: str  # "SUCCESS" or "UNAVAILABLE"

    def to_dict(self) -> dict:
        return {
            "search_id": self.search_id,
            "pair_id": self.pair_id,
            "database": self.database,
            "query_text": self.query_text,
            "query_hash": self.query_hash,
            "search_timestamp": self.search_timestamp,
            "result_count": self.result_count,
            "result_ids": self.result_ids,
            "result_titles": self.result_titles,
            "retrieval_method": self.retrieval_method,
            "result_manifest_hash": self.result_manifest_hash,
            "status": self.status,
        }


def _fetch_json(url: str, timeout: int = 15) -> Optional[dict]:
    """Fetch JSON from URL. Returns None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NoveltyAudit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _hash_results(result_ids: List[str], result_titles: List[str]) -> str:
    """Hash the result set for integrity."""
    # Handle None values in results
    safe_ids = [str(r) if r is not None else "" for r in result_ids]
    safe_titles = [str(t) if t is not None else "" for t in result_titles]
    data = json.dumps({"ids": sorted(safe_ids), "titles": sorted(safe_titles)},
                      sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def search_openalex(query: str, max_results: int = 10) -> Tuple[List[str], List[str], int]:
    """Search OpenAlex. Returns (result_ids, result_titles, total_count)."""
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": str(max_results),
        "select": "id,doi,title",
    })
    url = f"https://api.openalex.org/works?{params}"
    data = _fetch_json(url)

    if data is None:
        return [], [], -1  # -1 = UNAVAILABLE

    results = data.get("results", [])
    total = data.get("meta", {}).get("count", 0)

    ids = [r.get("doi", r.get("id", "")) for r in results]
    titles = [r.get("title", "") for r in results]

    return ids, titles, total


def search_semantic_scholar(query: str, max_results: int = 10) -> Tuple[List[str], List[str], int]:
    """Search Semantic Scholar. Returns (result_ids, result_titles, total_count)."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": str(max_results),
        "fields": "title,externalIds",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    data = _fetch_json(url, timeout=20)

    if data is None:
        return [], [], -1

    results = data.get("data", [])
    total = data.get("total", len(results))

    ids = []
    titles = []
    for r in results:
        ext_ids = r.get("externalIds", {})
        paper_id = ext_ids.get("DOI", r.get("paperId", ""))
        ids.append(paper_id)
        titles.append(r.get("title", ""))

    return ids, titles, total


def search_crossref(query: str, max_results: int = 10) -> Tuple[List[str], List[str], int]:
    """Search Crossref. Returns (result_ids, result_titles, total_count)."""
    params = urllib.parse.urlencode({
        "query": query,
        "rows": str(max_results),
        "select": "DOI,title",
    })
    url = f"https://api.crossref.org/works?{params}"
    data = _fetch_json(url, timeout=20)

    if data is None:
        return [], [], -1

    items = data.get("message", {}).get("items", [])
    total = data.get("message", {}).get("total-results", len(items))

    ids = []
    titles = []
    for item in items:
        doi = item.get("DOI", "")
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        ids.append(doi)
        titles.append(title)

    return ids, titles, total


# Database adapter mapping
SEARCH_ADAPTERS = {
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "crossref": search_crossref,
}


def execute_search(query: SearchQuery, max_results: int = 10) -> SearchResult:
    """Execute a single frozen query against its target database.

    Failed APIs → UNAVAILABLE (never treated as zero results).
    """
    db = query.database
    adapter = SEARCH_ADAPTERS.get(db)

    if adapter is None:
        return SearchResult(
            search_id=query.query_id, pair_id=query.pair_id, database=db,
            query_text=query.query_text, query_hash=query.query_hash,
            search_timestamp=datetime.now(timezone.utc).isoformat(),
            result_count=0, result_ids=[], result_titles=[],
            retrieval_method="no_adapter", result_manifest_hash="",
            status="UNAVAILABLE",
        )

    ids, titles, total = adapter(query.query_text, max_results)

    if total == -1:
        # API failure — UNAVAILABLE, NOT zero results
        return SearchResult(
            search_id=query.query_id, pair_id=query.pair_id, database=db,
            query_text=query.query_text, query_hash=query.query_hash,
            search_timestamp=datetime.now(timezone.utc).isoformat(),
            result_count=0, result_ids=[], result_titles=[],
            retrieval_method="api_failed", result_manifest_hash="",
            status="UNAVAILABLE",
        )

    result_hash = _hash_results(ids, titles)

    return SearchResult(
        search_id=query.query_id, pair_id=query.pair_id, database=db,
        query_text=query.query_text, query_hash=query.query_hash,
        search_timestamp=datetime.now(timezone.utc).isoformat(),
        result_count=total, result_ids=ids, result_titles=titles,
        retrieval_method="api", result_manifest_hash=result_hash,
        status="SUCCESS",
    )
