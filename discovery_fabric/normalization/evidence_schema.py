"""
Discovery Fabric — Normalized EvidenceItem schema.

Every retrieved object from any source is normalized to this schema.
Missing fields are UNAVAILABLE, never fabricated.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


UNAVAILABLE = "UNAVAILABLE"


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 of content string (UTF-8)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_record_hash(record: dict) -> str:
    """Compute SHA-256 of canonical JSON of record (excluding record_hash itself)."""
    r = {k: v for k, v in record.items() if k != "record_hash"}
    canonical = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_evidence_item(
    source: str,
    source_id: str,
    source_type: str,  # "scientific" or "patent"
    title: str,
    retrieval_method: str,
    source_uri: str,
    **fields,
) -> dict:
    """Create a normalized EvidenceItem.

    All fields not provided default to UNAVAILABLE.
    """
    # Build content hash from available text content
    content_parts = []
    for f in ["title", "abstract", "full_text"]:
        v = fields.get(f)
        if v and v != UNAVAILABLE and isinstance(v, str):
            content_parts.append(v)
    content_hash = compute_content_hash(" ".join(content_parts)) if content_parts else UNAVAILABLE

    item = {
        "id": f"{source}:{source_id}",
        "source_type": source_type,
        "source": source,
        "source_id": source_id,
        "jurisdiction": fields.get("jurisdiction", UNAVAILABLE),
        "title": title or UNAVAILABLE,
        "abstract": fields.get("abstract", UNAVAILABLE),
        "claims": fields.get("claims", UNAVAILABLE),
        "full_text": fields.get("full_text", UNAVAILABLE),
        "citations": fields.get("citations", UNAVAILABLE),
        "references": fields.get("references", UNAVAILABLE),
        "authors": fields.get("authors", UNAVAILABLE),
        "inventors": fields.get("inventors", UNAVAILABLE),
        "organizations": fields.get("organizations", UNAVAILABLE),
        "classifications": fields.get("classifications", UNAVAILABLE),
        "publication_date": fields.get("publication_date", UNAVAILABLE),
        "priority_date": fields.get("priority_date", UNAVAILABLE),
        "family_id": fields.get("family_id", UNAVAILABLE),
        "license": fields.get("license", UNAVAILABLE),
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "content_hash": content_hash,
        "retrieval_method": retrieval_method,
        "source_uri": source_uri,
        "provenance": {
            "source": source,
            "source_id": source_id,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "method": retrieval_method,
            "uri": source_uri,
        },
    }

    item["record_hash"] = compute_record_hash(item)
    return item
