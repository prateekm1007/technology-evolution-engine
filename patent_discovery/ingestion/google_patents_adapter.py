"""
Patent ingestion adapter — Google Patents public search.

Uses the Google Patents public search endpoint (xhr/query) which returns
structured JSON covering US, CN, and IN patents.

Coverage:
- US patents (google.com/patent/US...)
- CN patents (google.com/patent/CN...)
- IN patents (google.com/patent/IN...)

This is the pilot ingestion adapter. It does NOT modify the North Star
frozen experiment or the independent scientific corpus.

Honesty note: Google Patents is a third-party aggregator. Per SOURCES.md,
the originating patent record (USPTO/CNIPA/IP India) remains the
authoritative source. Google Patents is used for programmatic access
because the authoritative sources do not provide public bulk APIs.
Manual verification against authoritative sources is required for
high-value candidates.
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import socket
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple


GOOGLE_PATENTS_SEARCH = "https://patents.google.com/xhr/query"
GOOGLE_PATENTS_PAGE = "https://patents.google.com/patent/{patent_id}/en"
USER_AGENT = "Mozilla/5.0 (compatible; PatentDiscoveryMining/1.0; +mailto:patent-discovery@example.org)"


def fetch_json(url: str, max_retries: int = 3, timeout: float = 20.0) -> Tuple[Optional[dict], str]:
    """Fetch JSON from a URL with retries."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return json.loads(raw), "success"
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0 * (2 ** attempt))
                continue
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, f"HTTP {e.code}"
        except (urllib.error.URLError, socket.timeout):
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, "unavailable"
        except Exception as e:
            return None, f"error: {type(e).__name__}: {str(e)[:100]}"
    return None, "max_retries"


def fetch_html(url: str, max_retries: int = 3, timeout: float = 20.0) -> Tuple[Optional[str], str]:
    """Fetch HTML from a URL with retries."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace"), "success"
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0 * (2 ** attempt))
                continue
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, f"HTTP {e.code}"
        except (urllib.error.URLError, socket.timeout):
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, "unavailable"
        except Exception as e:
            return None, f"error: {type(e).__name__}: {str(e)[:100]}"
    return None, "max_retries"


def search_patents(query: str, num: int = 10, page: int = 0, country: str = "") -> Tuple[List[dict], str]:
    """Search patents via Google Patents.

    Args:
        query: search query string
        num: number of results per page
        page: page number (0-indexed)
        country: optional country filter (US, CN, IN, or empty for all)
            Note: Google Patents API does not reliably filter by country.
            We filter results post-hoc by patent_id prefix.

    Returns:
        (list of patent result dicts, status string)
    """
    # Build query URL
    q = query
    # Note: country: filter in Google Patents query syntax is unreliable.
    # We fetch without it and filter post-hoc by patent_id prefix.

    url = f"{GOOGLE_PATENTS_SEARCH}?url={urllib.parse.quote(f'q={urllib.parse.quote(q)}&num={num}&page={page}')}&exp="

    data, status = fetch_json(url)
    if status != "success" or not data:
        return [], status

    results = []
    clusters = data.get("results", {}).get("cluster", [])
    for cluster in clusters:
        for result in cluster.get("result", []):
            patent = result.get("patent", {})
            results.append({
                "patent_id": patent.get("publication_number", ""),
                "title": re.sub(r"<[^>]+>", "", patent.get("title", "")).strip(),
                "snippet": re.sub(r"<[^>]+>", "", patent.get("snippet", "")).strip(),
                "priority_date": patent.get("priority_date", ""),
                "filing_date": patent.get("filing_date", ""),
                "grant_date": patent.get("grant_date", ""),
                "publication_date": patent.get("publication_date", ""),
                "inventor": patent.get("inventor", ""),
                "assignee": patent.get("assignee", ""),
                "language": patent.get("language", ""),
                "id": result.get("id", ""),
            })

    return results, "success"


def fetch_patent_detail(patent_id: str) -> Tuple[Optional[dict], str]:
    """Fetch full patent details from Google Patents page.

    Extracts metadata from <meta> tags and claims/description from page content.
    """
    url = GOOGLE_PATENTS_PAGE.format(patent_id=urllib.parse.quote(patent_id))
    html, status = fetch_html(url)
    if status != "success" or not html:
        return None, status

    patent = {
        "patent_id": patent_id,
        "country": patent_id[:2] if len(patent_id) >= 2 else "",
        "title": "",
        "abstract": "",
        "filing_date": "",
        "grant_date": "",
        "publication_date": "",
        "priority_date": "",
        "inventors": [],
        "assignees": [],
        "classifications": {"cpc": [], "ipc": []},
        "cited_patents": [],
        "citing_patents": [],
        "claims": [],
        "description_excerpt": "",
        "source": "Google Patents",
        "source_url": url,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Extract from <meta> tags
    meta_pattern = r'<meta\s+name="([^"]+)"\s+content="([^"]*)"\s*(?:scheme="([^"]*)")?'
    for match in re.finditer(meta_pattern, html):
        name, content, scheme = match.groups()
        content = content.strip()

        if name == "DC.type" and content == "patent":
            continue
        elif name == "DC.date" and scheme == "dateSubmitted":
            patent["filing_date"] = content
        elif name == "DC.date" and scheme == "issue":
            patent["grant_date"] = content
        elif name == "DC.date" and scheme == "publication":
            patent["publication_date"] = content
        elif name == "DC.contributor" and scheme == "inventor":
            patent["inventors"].append(content)
        elif name == "DC.contributor" and scheme == "assignee":
            patent["assignees"].append(content)
        elif name == "DC.relation" and scheme == "references":
            # Cited patent: "US:1234567" or "CN:1212143:A"
            patent["cited_patents"].append(content)
        elif name == "citation_patent_application_number":
            patent["application_number"] = content
        elif name == "citation_patent_number":
            patent["citation_patent_number"] = content

    # Extract title from <title> tag
    title_match = re.search(r"<title>([^<]+)</title>", html)
    if title_match:
        raw_title = title_match.group(1).strip()
        # Remove patent ID prefix: "US11234567B2 - Title - Google Patents"
        if " - " in raw_title:
            parts = raw_title.split(" - ", 2)
            if len(parts) >= 2:
                patent["title"] = parts[1].strip()
        else:
            patent["title"] = raw_title

    # Extract abstract
    abstract_match = re.search(r'<section[^>]*itemprop="abstract"[^>]*>(.*?)</section>', html, re.DOTALL)
    if abstract_match:
        abstract = re.sub(r"<[^>]+>", "", abstract_match.group(1)).strip()
        patent["abstract"] = abstract[:2000]  # cap at 2000 chars

    # Extract claims (first 5 to keep size manageable)
    claims_section = re.search(r'<section[^>]*itemprop="claims"[^>]*>(.*?)</section>', html, re.DOTALL)
    if claims_section:
        claims_html = claims_section.group(1)
        # Each claim is in a <div class="claim">
        claim_divs = re.findall(r'<div\s+class="claim"[^>]*>(.*?)</div>\s*(?=<div\s+class="claim"|</section>)', claims_html, re.DOTALL)
        for i, claim_html in enumerate(claim_divs[:10]):
            claim_text = re.sub(r"<[^>]+>", "", claim_html).strip()
            if claim_text:
                patent["claims"].append({
                    "number": i + 1,
                    "text": claim_text[:2000],  # cap each claim at 2000 chars
                })

    # Extract description excerpt (first 1000 chars)
    desc_section = re.search(r'<section[^>]*itemprop="description"[^>]*>(.*?)</section>', html, re.DOTALL)
    if desc_section:
        desc = re.sub(r"<[^>]+>", "", desc_section.group(1)).strip()
        patent["description_excerpt"] = desc[:1000]

    # Extract CPC classifications
    cpc_pattern = r'<li\s+itemprop="classifications"[^>]*>\s*<span\s+itemprop="CPC"[^>]*>([^<]+)</span>'
    for match in re.finditer(cpc_pattern, html):
        cpc_code = match.group(1).strip()
        if cpc_code:
            patent["classifications"]["cpc"].append(cpc_code)

    # Extract IPC classifications
    ipc_pattern = r'<li\s+itemprop="classifications"[^>]*>\s*<span\s+itemprop="IPC"[^>]*>([^<]+)</span>'
    for match in re.finditer(ipc_pattern, html):
        ipc_code = match.group(1).strip()
        if ipc_code:
            patent["classifications"]["ipc"].append(ipc_code)

    # Compute hash
    canonical = json.dumps(patent, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    patent["record_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return patent, "success"


if __name__ == "__main__":
    # Smoke test
    print("=== SEARCH TEST ===")
    results, status = search_patents("photodetector materials", num=3)
    print(f"status: {status}")
    print(f"results: {len(results)}")
    for r in results[:2]:
        print(f"  {r['patent_id']}: {r['title'][:60]}")

    print()
    print("=== DETAIL TEST ===")
    if results:
        detail, dstatus = fetch_patent_detail(results[0]["patent_id"])
        print(f"status: {dstatus}")
        if detail:
            print(f"patent_id: {detail['patent_id']}")
            print(f"title: {detail['title'][:80]}")
            print(f"inventors: {detail['inventors'][:3]}")
            print(f"assignees: {detail['assignees'][:3]}")
            print(f"cpc: {detail['classifications']['cpc'][:5]}")
            print(f"cited count: {len(detail['cited_patents'])}")
            print(f"claims count: {len(detail['claims'])}")
            print(f"abstract: {detail['abstract'][:200]}")
            print(f"hash: {detail['record_hash'][:32]}")
