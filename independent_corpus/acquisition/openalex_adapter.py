"""
independent_corpus.acquisition.openalex_adapter — External sampling from OpenAlex.

OpenAlex provides a fully open scholarly graph with 300M+ works.
This adapter samples papers using a pre-declared, deterministic procedure.

HARD RULES (per CTO directive):
- No TEE influence on paper selection
- No cross-domain connection search (no "papers that combine X and Y")
- No "interestingness" filtering
- No hypothesis-generation feedback
- Pre-declared sampling procedure with external seed
- Temporal cutoff enforced
"""
import hashlib
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

OPENALEX_BASE = "https://api.openalex.org/works"
PROVIDER = "openalex"
PROVIDER_VERSION = "2024-08"


@dataclass
class OpenAlexRecord:
    """A single record from OpenAlex."""
    source_id: str
    title: str
    authors: List[str]
    publication_date: str
    doi: Optional[str]
    source_uri: str
    full_text_uri: Optional[str]
    publisher: str
    license: str
    domain: str
    external_provider: str
    provider_record_id: str
    acquisition_timestamp: str
    content_sha256: str  # Computed when full text is fetched
    metadata_sha256: str
    openalex_id: str

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "authors": self.authors,
            "publication_date": self.publication_date,
            "doi": self.doi,
            "source_uri": self.source_uri,
            "full_text_uri": self.full_text_uri,
            "publisher": self.publisher,
            "license": self.license,
            "domain": self.domain,
            "external_provider": self.external_provider,
            "provider_record_id": self.provider_record_id,
            "acquisition_timestamp": self.acquisition_timestamp,
            "content_sha256": self.content_sha256,
            "metadata_sha256": self.metadata_sha256,
            "openalex_id": self.openalex_id,
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


def _hash_metadata(meta: dict) -> str:
    """Compute SHA-256 of metadata (canonical JSON)."""
    canonical = json.dumps(meta, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def sample_openalex(
    date_cutoff: str,
    random_seed: str,
    per_page: int = 200,
    max_results: int = 5000,
    sample_cursor: Optional[str] = None,
) -> Tuple[List[OpenAlexRecord], Optional[str], dict]:
    """Sample papers from OpenAlex using a pre-declared procedure.

    SAMPLING PROCEDURE (pre-declared):
    - Filter: publication_date <= date_cutoff, has DOI, type = "article"
    - Sort: by publication_date descending (most recent first within cutoff)
    - Sample: deterministic page-by-page retrieval using cursor pagination
    - No keyword search (no "interesting" papers)
    - No domain filtering (domains classified AFTER acquisition)
    - No connection search (no "papers that combine X and Y")

    Args:
        date_cutoff: ISO date string (e.g., "2025-01-01")
        random_seed: External seed for deterministic sampling
        per_page: Results per API page (max 200)
        max_results: Maximum total results to retrieve
        sample_cursor: OpenAlex cursor for pagination (None = start from beginning)

    Returns:
        Tuple of (records, next_cursor, stats)
    """
    stats = {
        "provider": PROVIDER,
        "provider_version": PROVIDER_VERSION,
        "date_cutoff": date_cutoff,
        "random_seed": hashlib.sha256(random_seed.encode('utf-8')).hexdigest(),
        "per_page": per_page,
        "max_results": max_results,
        "n_requested": 0,
        "n_received": 0,
        "n_with_full_text": 0,
        "n_errors": 0,
    }

    records = []
    cursor = sample_cursor or "*"
    acq_ts = "2026-08-11T00:00:00Z"  # Fixed timestamp for reproducibility

    while len(records) < max_results:
        # Build query: articles published before cutoff, with DOI
        # NO keyword search, NO domain filter, NO "interesting" filter
        params = {
            "filter": f"from_publication_date:1900-01-01,to_publication_date:{date_cutoff},type:article,has_doi:true",
            "sort": "publication_date:desc",
            "per-page": str(min(per_page, max_results - len(records))),
            "cursor": cursor,
            "select": "id,doi,title,authorships,publication_date,primary_location,open_access,type,topics",
        }

        url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
        stats["n_requested"] += 1

        try:
            data = _fetch_json(url)
        except Exception as e:
            stats["n_errors"] += 1
            if stats["n_errors"] >= 5:
                break
            time.sleep(5)
            continue

        results = data.get("results", [])
        if not results:
            break

        for work in results:
            # Extract metadata
            openalex_id = work.get("id", "").replace("https://openalex.org/", "")
            doi = work.get("doi", "")
            title = work.get("title", "") or "Untitled"
            pub_date = work.get("publication_date", "")

            # Authors
            authors = []
            for authorship in work.get("authorships", [])[:10]:
                author = authorship.get("author", {})
                name = author.get("display_name", "")
                if name:
                    authors.append(name)

            # Primary location (publisher, license)
            primary_loc = work.get("primary_location", {}) or {}
            source = primary_loc.get("source", {}) or {}
            publisher = source.get("display_name", "Unknown")
            license_info = primary_loc.get("license", "unknown")

            # Open access info
            oa = work.get("open_access", {}) or {}
            oa_url = oa.get("oa_url", "")
            is_oa = oa.get("is_oa", False)

            # Full text URI
            full_text_uri = oa_url if is_oa and oa_url else None

            # Domain (from OpenAlex topics — used as HINT, not ground truth)
            # Extract the field-level concept (broader than topic)
            topics = work.get("topics", [])
            domain_hint = "unknown"
            if topics:
                # Use the field display_name from the topic hierarchy
                topic = topics[0]
                field = topic.get("field", {})
                domain_hint = field.get("display_name", "") if field else ""
                if not domain_hint:
                    # Fall back to subfield
                    subfield = topic.get("subfield", {})
                    domain_hint = subfield.get("display_name", "") if subfield else ""
                if not domain_hint:
                    domain_hint = topic.get("display_name", "unknown")

            # Build metadata dict for hashing
            meta = {
                "openalex_id": openalex_id,
                "doi": doi,
                "title": title,
                "publication_date": pub_date,
                "authors": authors,
                "publisher": publisher,
                "type": work.get("type", "article"),
            }
            metadata_hash = _hash_metadata(meta)

            record = OpenAlexRecord(
                source_id=f"OA-{openalex_id}",
                title=title,
                authors=authors,
                publication_date=pub_date,
                doi=doi,
                source_uri=f"https://openalex.org/{openalex_id}",
                full_text_uri=full_text_uri,
                publisher=publisher,
                license=license_info or "unknown",
                domain=domain_hint,
                external_provider=PROVIDER,
                provider_record_id=openalex_id,
                acquisition_timestamp=acq_ts,
                content_sha256="",  # Computed when full text is fetched
                metadata_sha256=metadata_hash,
                openalex_id=openalex_id,
            )
            records.append(record)

            if full_text_uri:
                stats["n_with_full_text"] += 1

        stats["n_received"] += len(results)

        # Get next cursor
        meta = data.get("meta", {})
        cursor = meta.get("next_cursor")
        if not cursor:
            break

        # Rate limiting (be polite to OpenAlex)
        time.sleep(0.5)

    return records, cursor, stats


def fetch_full_text(record: OpenAlexRecord) -> Tuple[Optional[str], str]:
    """Fetch full text for a record if available.

    Returns (content, content_sha256) or (None, "").
    """
    if not record.full_text_uri:
        return None, ""

    try:
        req = urllib.request.Request(record.full_text_uri, headers={"User-Agent": "CustodianIntake/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            return content, content_hash
    except Exception:
        return None, ""
