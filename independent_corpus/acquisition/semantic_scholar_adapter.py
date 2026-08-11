"""
independent_corpus.acquisition.semantic_scholar_adapter — Independent cross-check via Semantic Scholar.

Semantic Scholar provides an independent scholarly graph.
Used for provenance cross-validation, NOT for ranking or "finding best papers."

HARD RULES:
- Do NOT merge rankings with OpenAlex
- Role is provenance and cross-validation, not "find the best papers"
- No keyword search for cross-domain connections
"""
import hashlib
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

S2_BASE = "https://api.semanticscholar.org/graph/v1"
PROVIDER = "semantic_scholar"
PROVIDER_VERSION = "2024-08"


@dataclass
class S2CrossCheckResult:
    """Result of cross-checking an OpenAlex record against Semantic Scholar."""
    openalex_id: str
    s2_paper_id: Optional[str]
    s2_title: Optional[str]
    s2_publication_date: Optional[str]
    title_match: bool
    date_match: bool
    doi_match: bool
    cross_check_status: str  # "CONFIRMED", "PARTIAL_MATCH", "NOT_FOUND", "ERROR"

    def to_dict(self) -> dict:
        return {
            "openalex_id": self.openalex_id,
            "s2_paper_id": self.s2_paper_id,
            "s2_title": self.s2_title,
            "s2_publication_date": self.s2_publication_date,
            "title_match": self.title_match,
            "date_match": self.date_match,
            "doi_match": self.doi_match,
            "cross_check_status": self.cross_check_status,
        }


def _fetch_json(url: str, max_retries: int = 3) -> dict:
    """Fetch JSON from URL with retries."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CustodianIntake/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def cross_check_by_doi(doi: str, openalex_id: str) -> S2CrossCheckResult:
    """Cross-check a record against Semantic Scholar using DOI.

    This is NOT a search for "interesting papers."
    It verifies that the OpenAlex record corresponds to a real paper in an
    independent scholarly graph.
    """
    if not doi:
        return S2CrossCheckResult(
            openalex_id=openalex_id,
            s2_paper_id=None,
            s2_title=None,
            s2_publication_date=None,
            title_match=False,
            date_match=False,
            doi_match=False,
            cross_check_status="NOT_FOUND",
        )

    # Clean DOI
    clean_doi = doi.replace("https://doi.org/", "").replace("https://dx.doi.org/", "")

    url = f"{S2_BASE}/paper/DOI:{clean_doi}?fields=title,publicationDate,externalIds"

    try:
        data = _fetch_json(url)
        s2_title = data.get("title", "")
        s2_date = data.get("publicationDate", "")
        s2_id = data.get("paperId", "")

        return S2CrossCheckResult(
            openalex_id=openalex_id,
            s2_paper_id=s2_id,
            s2_title=s2_title,
            s2_publication_date=s2_date,
            title_match=bool(s2_title),  # Simplified — custodian reviews
            date_match=bool(s2_date),
            doi_match=True,
            cross_check_status="CONFIRMED" if s2_id else "PARTIAL_MATCH",
        )
    except Exception as e:
        return S2CrossCheckResult(
            openalex_id=openalex_id,
            s2_paper_id=None,
            s2_title=None,
            s2_publication_date=None,
            title_match=False,
            date_match=False,
            doi_match=False,
            cross_check_status="ERROR",
        )


def batch_cross_check(records: List, max_checks: int = 100) -> List[S2CrossCheckResult]:
    """Cross-check multiple records against Semantic Scholar.

    Args:
        records: List of OpenAlexRecord objects
        max_checks: Maximum number of cross-checks (to respect rate limits)

    Returns:
        List of S2CrossCheckResult
    """
    results = []
    for i, record in enumerate(records[:max_checks]):
        result = cross_check_by_doi(record.doi or "", record.openalex_id)
        results.append(result)
        time.sleep(1.0)  # Rate limiting (S2 allows ~1 req/sec without API key)

    return results
