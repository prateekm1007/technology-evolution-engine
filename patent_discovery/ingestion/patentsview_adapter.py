"""
Patent ingestion adapter — PatentsView API (USPTO).

Fetches patent records from the PatentsView research-grade API.
Returns structured patent records with claims, citations, classifications.

Coverage: US patents and published applications.
CN/IN coverage: partial via family linkage (US patents with CN/IN priority).

This is the PILOT ingestion adapter. It does NOT modify the North Star
frozen experiment or the independent scientific corpus.
"""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple


PATENTSVIEW_ENDPOINT = "https://api.patentsview.org/patents/query"
USER_AGENT = "PatentDiscoveryMining/1.0 (mailto:patent-discovery@example.org)"

# Technology domain → CPC classification code mapping
# Used for stratified sampling across 8 domains
DOMAIN_CPC_MAP = {
    "materials": ["B82Y", "C01", "C04", "C22", "C23"],
    "energy": ["F03", "F24", "H02", "H01M", "C10"],
    "mechanical_systems": ["F16", "F15", "B23", "B25", "F04"],
    "electronics": ["H01", "H03", "H05", "G11"],
    "computing_ai": ["G06", "G06N", "G06F", "G06T"],
    "biotechnology": ["C12", "C07K", "A61K", "A01"],
    "chemical_processes": ["C07", "C08", "C09", "B01"],
    "manufacturing": ["B29", "B22", "B23K", "B23P", "C25"],
}


def fetch_patentsview(query_body: dict, max_retries: int = 3, timeout: float = 30.0) -> Tuple[Optional[dict], str, Optional[dict]]:
    """Fetch from PatentsView API.

    Returns (data, status, response_meta) where status is:
    - "success" — got data
    - "no_results" — 200 but empty
    - "unavailable" — rate limited or timeout
    - "error" — non-recoverable
    """
    url = PATENTSVIEW_ENDPOINT
    body = json.dumps(query_body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                data = json.loads(raw)
                meta = {
                    "http_status": resp.status,
                    "response_size": len(raw),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                if not data.get("patents"):
                    return data, "no_results", meta
                return data, "success", meta

        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0 * (2 ** attempt))
                continue
            elif e.code == 400:
                return None, "error", {"http_status": 400, "error": str(e)[:200]}
            else:
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                return None, "error", {"http_status": e.code, "error": str(e)[:200]}

        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (2 ** attempt))
                    continue
            return None, "unavailable", {"error": str(e)[:200]}

        except socket.timeout:
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, "unavailable", {"error": "socket timeout"}

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return None, "error", {"error": f"{type(e).__name__}: {str(e)[:200]}"}

    return None, "unavailable", {"error": "max retries exceeded"}


def build_domain_query(cpc_prefix: str, page: int = 1, per_page: int = 25) -> dict:
    """Build a PatentsView query for a CPC classification prefix."""
    return {
        "q": {
            "_and": [
                {"cpc_section_id": {"text": cpc_prefix[:1]}},
                {"_text_any": {"patent_abstract": cpc_prefix}},
            ]
        },
        "f": [
            "patent_number",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "patent_type",
            "patent_kind",
            "inventors.inventor_name",
            "assignees.assignee_organization",
            "assignees.assignee_type",
            "cpcs.cpc_section_id",
            "cpcs.cpc_subsection_id",
            "cpcs.cpc_group_id",
            "cpcs.cpc_subgroup_id",
            "uspcs.uspc_main_class",
            "ipcs.ipc_section",
            "ipcs.ipc_subclass",
            "cited_patents.cited_patent_number",
            "cited_patents.cited_patent_date",
            "citing_patents.citing_patent_number",
            # Claims are large; request separately in a second pass for top candidates
        ],
        "o": {"per_page": per_page, "page": page},
        "s": [{"patent_date": "desc"}],
    }


def build_patent_detail_query(patent_number: str) -> dict:
    """Build a query to fetch full details including claims for a single patent."""
    return {
        "q": {"patent_number": patent_number},
        "f": [
            "patent_number",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "patent_type",
            "patent_kind",
            "patent_application_number",
            "patent_application_date",
            "inventors.inventor_name",
            "assignees.assignee_organization",
            "assignees.assignee_type",
            "cpcs.cpc_section_id",
            "cpcs.cpc_subsection_id",
            "cpcs.cpc_group_id",
            "cpcs.cpc_subgroup_id",
            "ipcs.ipc_section",
            "ipcs.ipc_subclass",
            "cited_patents.cited_patent_number",
            "cited_patents.cited_patent_date",
            "citing_patents.citing_patent_number",
            "claims.claim_text",
            "claims.claim_number",
            "claims.dependent_on",
        ],
        "o": {"per_page": 1},
    }


def normalize_patent_record(raw: dict) -> dict:
    """Normalize a PatentsView patent record into our schema."""
    patent = {
        "patent_id": raw.get("patent_number", ""),
        "title": raw.get("patent_title", ""),
        "abstract": raw.get("patent_abstract", ""),
        "patent_date": raw.get("patent_date", ""),
        "patent_type": raw.get("patent_type", ""),
        "patent_kind": raw.get("patent_kind", ""),
        "application_number": raw.get("patent_application_number", ""),
        "application_date": raw.get("patent_application_date", ""),
        "country": "US",
        "inventors": [],
        "assignees": [],
        "classifications": {
            "cpc": [],
            "ipc": [],
        },
        "cited_patents": [],
        "citing_patents": [],
        "claims": [],
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "PatentsView",
    }

    # Inventors
    for inv in raw.get("inventors", []):
        if isinstance(inv, dict) and inv.get("inventor_name"):
            patent["inventors"].append(inv["inventor_name"])

    # Assignees
    for asg in raw.get("assignees", []):
        if isinstance(asg, dict):
            patent["assignees"].append({
                "name": asg.get("assignee_organization", ""),
                "type": asg.get("assignee_type", ""),
            })

    # CPC classifications
    for cpc in raw.get("cpcs", []):
        if isinstance(cpc, dict):
            patent["classifications"]["cpc"].append({
                "section": cpc.get("cpc_section_id", ""),
                "subsection": cpc.get("cpc_subsection_id", ""),
                "group": cpc.get("cpc_group_id", ""),
                "subgroup": cpc.get("cpc_subgroup_id", ""),
            })

    # IPC classifications
    for ipc in raw.get("ipcs", []):
        if isinstance(ipc, dict):
            patent["classifications"]["ipc"].append({
                "section": ipc.get("ipc_section", ""),
                "subclass": ipc.get("ipc_subclass", ""),
            })

    # Cited patents (backward citations)
    for cited in raw.get("cited_patents", []):
        if isinstance(cited, dict) and cited.get("cited_patent_number"):
            patent["cited_patents"].append({
                "patent_number": cited["cited_patent_number"],
                "date": cited.get("cited_patent_date", ""),
            })

    # Citing patents (forward citations)
    for citing in raw.get("citing_patents", []):
        if isinstance(citing, dict) and citing.get("citing_patent_number"):
            patent["citing_patents"].append({
                "patent_number": citing["citing_patent_number"],
            })

    # Claims (if fetched in detail query)
    for claim in raw.get("claims", []):
        if isinstance(claim, dict):
            patent["claims"].append({
                "number": claim.get("claim_number", 0),
                "text": claim.get("claim_text", ""),
                "dependent_on": claim.get("dependent_on", None),
            })

    return patent


def compute_patent_hash(patent: dict) -> str:
    """Compute SHA-256 hash of the patent record (excluding the hash itself)."""
    canonical = json.dumps(patent, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # Smoke test — fetch 2 patents from a single CPC prefix
    q = build_domain_query("G06N", page=1, per_page=2)
    data, status, meta = fetch_patentsview(q)
    print(f"status: {status}")
    print(f"meta: {meta}")
    if data and data.get("patents"):
        for p in data["patents"][:2]:
            np = normalize_patent_record(p)
            print(f"\npatent_id: {np['patent_id']}")
            print(f"title: {np['title'][:80]}")
            print(f"date: {np['patent_date']}")
            print(f"cited count: {len(np['cited_patents'])}")
            print(f"citing count: {len(np['citing_patents'])}")
            print(f"hash: {compute_patent_hash(np)[:32]}")
