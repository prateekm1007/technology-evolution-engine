"""
NOVELTY_RECOVERY_V1 — OpenAIRE adapter.

OpenAIRE Graph API: https://api.openaire.eu/search/

This is a RECOVERY adapter, NOT a frozen-trial adapter.
- Separate evidence namespace from the frozen 3-database trial
- Same 182 pairs, same 4 frozen query types
- Classifies every result: SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR
- Never converts UNAVAILABLE to NO_RESULTS
- Records provider, query, timestamp, response hash, evidence URI

Does NOT produce D3. Output is evidence for the custodian only.
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


OPENAIRE_BASE = "https://api.openaire.eu/search"
USER_AGENT = "NoveltyRecovery/1.0 (mailto:novelty-recovery@example.org)"


def _fetch_with_backoff(url: str, max_retries: int = 4, base_delay: float = 2.0,
                        timeout: float = 30.0) -> Tuple[Optional[dict], str, Optional[dict]]:
    """Fetch JSON with exponential backoff.

    Returns (data, status, headers) where status is:
    - "success"     — got data
    - "no_results"  — got 200 response but no results
    - "unavailable" — rate limited or timeout after retries
    - "error"       — non-recoverable error
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


def search_openaire(query_text: str, max_results: int = 10) -> dict:
    """Search OpenAIRE Graph API for publications matching the query.

    Returns a recovery result dict with:
      provider, status, result_count, result_ids, result_titles, result_dois,
      result_dates, response_hash, evidence_uri, timestamp, retry_count, error
    """
    params = urllib.parse.urlencode({
        "keywords": query_text,
        "size": max_results,
        "format": "json",
    })
    url = f"{OPENAIRE_BASE}/publications?{params}"

    data, status, headers = _fetch_with_backoff(url)

    result = {
        "provider": "openaire",
        "query_text": query_text,
        "url": url,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": None,  # SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR
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

    # Capture rate-limit headers
    if headers:
        for k, v in headers.items():
            lk = k.lower()
            if "rate" in lk or "retry" in lk or "x-app" in lk:
                result["rate_limit_headers"][k] = v

    if status == "error":
        result["status"] = "ERROR"
        result["error"] = "OpenAIRE returned non-recoverable error"
        return result

    if status == "unavailable":
        result["status"] = "UNAVAILABLE"
        result["error"] = "OpenAIRE unavailable after retries (timeout or 429)"
        return result

    if status == "no_results":
        result["status"] = "NO_RESULTS"
        result["result_count"] = 0
        result["response_hash"] = hashlib.sha256(b"").hexdigest()
        return result

    # success — parse OpenAIRE JSON
    try:
        # OpenAIRE response structure: response.results.result (list or single obj)
        # When no results, response.results is None (NOT empty dict)
        root = data.get("response", {}) if isinstance(data, dict) else {}
        results_root = root.get("results") if isinstance(root, dict) else None
        if results_root is None:
            # No results field — treat as NO_RESULTS
            result["status"] = "NO_RESULTS"
            result["result_count"] = 0
            result["response_hash"] = hashlib.sha256(b"").hexdigest()
            return result

        raw_results = results_root.get("result", []) if isinstance(results_root, dict) else []

        # Normalize: if single result, OpenAIRE returns dict not list
        if isinstance(raw_results, dict):
            raw_results = [raw_results]
        if not isinstance(raw_results, list):
            raw_results = []

        result["result_count"] = len(raw_results)
        result["status"] = "SUCCESS" if len(raw_results) > 0 else "NO_RESULTS"

        for r in raw_results[:max_results]:
            try:
                # Each result has 'header' and 'metadata'
                header = r.get("header", {})
                metadata = r.get("metadata", {})
                oaf = metadata.get("oaf:entity", {})
                oaf_root = oaf.get("oaf:result", {}) if isinstance(oaf, dict) else {}

                # OpenAIRE internal identifier
                obj_id = header.get("objIdentifier") or oaf_root.get("originalId") or ""

                # Title
                titles = oaf_root.get("title", [])
                if isinstance(titles, dict):
                    titles = [titles]
                title_value = ""
                if titles and isinstance(titles, list) and len(titles) > 0:
                    title_value = titles[0].get("$", "") or titles[0].get("__value", "") or ""

                # DOI — find in pid class
                pid = oaf_root.get("pid", [])
                if isinstance(pid, dict):
                    pid = [pid]
                doi = ""
                for p in pid:
                    if isinstance(p, dict):
                        cl = p.get("@classid", "")
                        if cl == "doi":
                            doi = p.get("$", "") or ""
                            break

                # Date
                date_value = oaf_root.get("dateofacceptance", {})
                if isinstance(date_value, dict):
                    date_value = date_value.get("$", "") or date_value.get("__value", "")
                elif not isinstance(date_value, str):
                    date_value = ""

                result["result_ids"].append(obj_id)
                result["result_titles"].append(title_value)
                result["result_dois"].append(doi)
                result["result_dates"].append(date_value)
            except Exception:
                result["result_ids"].append("")
                result["result_titles"].append("")
                result["result_dois"].append("")
                result["result_dates"].append("")

        # Response hash — canonical JSON of captured result fields
        canonical = json.dumps({
            "ids": result["result_ids"],
            "titles": result["result_titles"],
            "dois": result["result_dois"],
        }, sort_keys=True, separators=(",", ":"))
        result["response_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = f"Parse failure: {type(e).__name__}: {str(e)[:200]}"

    return result


if __name__ == "__main__":
    # Smoke test — ONE harmless query, not a frozen query
    r = search_openaire("photodetector materials review", max_results=2)
    print(json.dumps(r, indent=2))
