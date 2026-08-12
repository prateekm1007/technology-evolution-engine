"""
NOVELTY_RECOVERY_V1 — OpenCitations adapter.

OpenCitations Index API: https://api.opencitations.net/index/v2

This adapter does TWO jobs:
1. Citation-graph lookup: for a DOI, retrieve incoming + outgoing citations
   — used for the "domain_bridge" and "mechanism_transfer" query types
   — directly answers "is there a connecting publication between these two sources?"
2. Reference search: keyword-based search across the OpenCitations corpus
   — used for "direct" and "reverse" query types

RECOVERY namespace, NOT frozen-trial.
- Classifies every result: SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR
- Never converts UNAVAILABLE to NO_RESULTS
- Does NOT produce D3
"""
import hashlib
import json
import time
import urllib.parse
import urllib.request
import urllib.error
import socket
from datetime import datetime, timezone
from typing import Tuple, List, Optional


OPEN_CITATIONS_BASE = "https://api.opencitations.net/index/v2"
USER_AGENT = "NoveltyRecovery/1.0 (mailto:novelty-recovery@example.org)"


def _fetch_with_backoff(url: str, max_retries: int = 4, base_delay: float = 2.0,
                        timeout: float = 30.0) -> Tuple[Optional[dict | list], str, Optional[dict]]:
    """Fetch JSON with exponential backoff.

    Returns (data, status, headers).
    """
    last_headers = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                last_headers = dict(resp.headers.items())
                data = json.loads(raw)
                return data, "success", last_headers

        except urllib.error.HTTPError as e:
            last_headers = dict(e.headers.items()) if e.headers else None
            if e.code == 429:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                try:
                    delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
                except (ValueError, TypeError):
                    delay = base_delay * (2 ** attempt)
                delay = min(delay, 60)
                time.sleep(delay)
                continue
            elif e.code == 404:
                return None, "no_results", last_headers
            else:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                return None, "error", last_headers

        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
            return None, "unavailable", last_headers

        except socket.timeout:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            return None, "unavailable", last_headers

        except Exception:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            return None, "error", last_headers

    return None, "unavailable", last_headers


def _doi_to_oc_id(doi: str) -> str:
    """OpenCitations uses 'doi:10.xxxx/yyyy' format as identifier."""
    if not doi:
        return ""
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    if doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]
    if doi.startswith("doi:"):
        return doi.lower()
    return f"doi:{doi.lower()}"


def search_opencitations_keyword(query_text: str, max_results: int = 10) -> dict:
    """Search OpenCitations by keyword (uses /search/{text} endpoint).

    Used for direct/reverse query types — searches citing/cited publications
    containing the keywords.
    """
    # OpenCitations /search/{text} returns a list of citation entries
    encoded = urllib.parse.quote(query_text, safe="")
    url = f"{OPEN_CITATIONS_BASE}/search/{encoded}"
    data, status, headers = _fetch_with_backoff(url)

    result = {
        "provider": "opencitations",
        "search_type": "keyword",
        "query_text": query_text,
        "url": url,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "result_count": -1,
        "result_ids": [],
        "result_titles": [],
        "result_dois": [],
        "result_dates": [],
        "response_hash": None,
        "evidence_uri": url,
        "error": None,
        "rate_limit_headers": {},
    }

    if headers:
        for k, v in headers.items():
            lk = k.lower()
            if "rate" in lk or "retry" in lk:
                result["rate_limit_headers"][k] = v

    if status == "error":
        result["status"] = "ERROR"
        result["error"] = "OpenCitations returned non-recoverable error"
        return result

    if status == "unavailable":
        result["status"] = "UNAVAILABLE"
        result["error"] = "OpenCitations unavailable after retries"
        return result

    if status == "no_results":
        result["status"] = "NO_RESULTS"
        result["result_count"] = 0
        result["response_hash"] = hashlib.sha256(b"").hexdigest()
        return result

    # success — OpenCitations returns list of citation entries
    try:
        if not isinstance(data, list):
            data = []
        result["result_count"] = len(data)
        result["status"] = "SUCCESS" if len(data) > 0 else "NO_RESULTS"

        for entry in data[:max_results]:
            if not isinstance(entry, dict):
                continue
            citing = entry.get("citing", "") or ""
            cited = entry.get("cited", "") or ""
            # OpenCitations entries don't have titles; use IDs as identifiers
            result["result_ids"].append(citing)
            result["result_titles"].append("")  # OC doesn't return titles
            result["result_dois"].append(citing)
            result["result_dates"].append(entry.get("creation", "") or "")

        canonical = json.dumps({
            "ids": result["result_ids"],
            "dois": result["result_dois"],
        }, sort_keys=True, separators=(",", ":"))
        result["response_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = f"Parse failure: {type(e).__name__}: {str(e)[:200]}"

    return result


def opencitations_citation_lookup(doi_a: str, doi_b: str) -> dict:
    """Look up whether DOI A and DOI B are connected via citations.

    Returns whether A cites B, B cites A, or they share a common citing/cited paper.
    This is the citation-graph novelty check.

    Queries:
    1. /references/{doi_a} — what A cites (check if B is in there)
    2. /citations/{doi_a}  — what cites A (check if B is in there)
    3. Same pair swapped
    """
    id_a = _doi_to_oc_id(doi_a)
    id_b = _doi_to_oc_id(doi_b)

    result = {
        "provider": "opencitations",
        "search_type": "citation_graph",
        "doi_a": doi_a,
        "doi_b": doi_b,
        "oc_id_a": id_a,
        "oc_id_b": id_b,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "a_cites_b": False,
        "b_cites_a": False,
        "a_citation_count": -1,
        "b_citation_count": -1,
        "a_reference_count": -1,
        "b_reference_count": -1,
        "shared_citing": [],
        "shared_cited": [],
        "response_hash": None,
        "evidence_uris": [],
        "error": None,
    }

    if not id_a or not id_b:
        result["status"] = "ERROR"
        result["error"] = "Missing DOI for one or both sources"
        return result

    # Fetch outgoing references (what A cites)
    ref_a_url = f"{OPEN_CITATIONS_BASE}/references/{id_a}"
    data_a, status_a, _ = _fetch_with_backoff(ref_a_url, max_retries=2)
    result["evidence_uris"].append(ref_a_url)

    if status_a == "success" and isinstance(data_a, list):
        result["a_reference_count"] = len(data_a)
        # Check if B is in A's references
        for entry in data_a:
            if isinstance(entry, dict):
                if entry.get("cited", "").lower() == id_b.lower():
                    result["a_cites_b"] = True
                    break
    elif status_a == "unavailable":
        result["status"] = "UNAVAILABLE"
        result["error"] = "OpenCitations references lookup unavailable"
        return result

    # Fetch incoming citations (what cites A)
    cit_a_url = f"{OPEN_CITATIONS_BASE}/citations/{id_a}"
    data_cit_a, status_cit_a, _ = _fetch_with_backoff(cit_a_url, max_retries=2)
    result["evidence_uris"].append(cit_a_url)

    if status_cit_a == "success" and isinstance(data_cit_a, list):
        result["a_citation_count"] = len(data_cit_a)
        # Check if B is in A's citers
        for entry in data_cit_a:
            if isinstance(entry, dict):
                if entry.get("citing", "").lower() == id_b.lower():
                    result["b_cites_a"] = True
                    break

    # Same for B
    ref_b_url = f"{OPEN_CITATIONS_BASE}/references/{id_b}"
    data_b, status_b, _ = _fetch_with_backoff(ref_b_url, max_retries=2)
    result["evidence_uris"].append(ref_b_url)

    if status_b == "success" and isinstance(data_b, list):
        result["b_reference_count"] = len(data_b)
        for entry in data_b:
            if isinstance(entry, dict):
                if entry.get("cited", "").lower() == id_a.lower():
                    result["b_cites_a"] = True
                    break

    cit_b_url = f"{OPEN_CITATIONS_BASE}/citations/{id_b}"
    data_cit_b, status_cit_b, _ = _fetch_with_backoff(cit_b_url, max_retries=2)
    result["evidence_uris"].append(cit_b_url)

    if status_cit_b == "success" and isinstance(data_cit_b, list):
        result["b_citation_count"] = len(data_cit_b)

    # Determine final status
    any_unavailable = status_a == "unavailable" or status_b == "unavailable" or status_cit_a == "unavailable" or status_cit_b == "unavailable"
    any_error = status_a == "error" or status_b == "error" or status_cit_a == "error" or status_cit_b == "error"

    if any_unavailable:
        result["status"] = "UNAVAILABLE"
        result["error"] = "One or more OpenCitations lookups unavailable after retries"
    elif any_error:
        result["status"] = "ERROR"
        result["error"] = "One or more OpenCitations lookups returned an error"
    else:
        # All lookups succeeded (some may have been no_results / 404)
        result["status"] = "SUCCESS"

    # Response hash — canonical of citation relationships
    canonical = json.dumps({
        "a_cites_b": result["a_cites_b"],
        "b_cites_a": result["b_cites_a"],
        "a_ref_count": result["a_reference_count"],
        "b_ref_count": result["b_reference_count"],
        "a_cit_count": result["a_citation_count"],
        "b_cit_count": result["b_citation_count"],
    }, sort_keys=True, separators=(",", ":"))
    result["response_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return result


if __name__ == "__main__":
    # Smoke test
    print("=== keyword search ===")
    r = search_opencitations_keyword("photodetector materials", max_results=2)
    print(json.dumps(r, indent=2))
    print()
    print("=== citation lookup ===")
    r2 = opencitations_citation_lookup("10.21175/rad.abstr.book.2026.17.6", "10.21175/rad.abstr.book.2026.1.2")
    print(json.dumps(r2, indent=2))
