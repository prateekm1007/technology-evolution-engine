"""
V5 Patent Family Reconstruction (Issue #5 V5, directive A).

Per CTO: "Do not count a document as a family. Implement explicit family
reconstruction using priority/application relationships where the source
supports them."

The allenai/us-patents dataset does NOT provide priority/application data
(it only has corpus_id, filing_date, patent_type, text). Therefore we
CANNOT reconstruct true DOCDB families from this source.

What we CAN do:
  1. Group patents by filing_date + first-words-of-title as a PROXY family
     (clearly labeled as "PROXY_FAMILY", not "DOCDB_FAMILY")
  2. Count patent documents honestly as PATENT_DOCUMENTS, not families
  3. Report PATENT_FAMILIES_RECONSTRUCTED = 0 for HuggingFace (honest)

True family reconstruction requires:
  - EPO OPS (priority claims + family member lookup) — needs OAuth
  - USPTO ODP (family linkage data) — needs API key
  - Google Patents BigQuery (family_id field) — needs Google auth

Until one of those is operational, PATENT_FAMILIES_RECONSTRUCTED stays 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
import hashlib


@dataclass
class PatentFamily:
    """A reconstructed patent family. May be PROXY (heuristic) or DOCDB (authoritative)."""
    family_id: str
    family_type: str           # "DOCDB_FAMILY" | "PROXY_FAMILY" | "SINGLETON"
    member_document_ids: list[str] = field(default_factory=list)
    reconstruction_method: str = ""   # "priority_chain" | "title_date_proxy" | "single"
    earliest_filing_date: str = ""
    notes: str = ""


def reconstruct_families_proxy(patent_records: list[dict]) -> list[PatentFamily]:
    """Reconstruct PROXY families using filing_date + title-prefix heuristic.

    This is NOT a true DOCDB family reconstruction. It groups patents that
    share the same filing_date AND the first 5 significant words of the title.
    This is a heuristic for identifying continuation/divisional chains.

    Returns PatentFamily objects with family_type="PROXY_FAMILY".
    Singles (no match) are returned as family_type="SINGLETON".
    """
    groups: dict[str, list[str]] = defaultdict(list)
    STOP = {"the", "a", "an", "of", "for", "and", "in", "with", "to", "on",
            "method", "system", "device", "apparatus", "comprising"}

    for rec in patent_records:
        filing_date = rec.get("filing_date", "")
        title = (rec.get("title", "") or "").lower()
        # Extract first 5 significant words
        words = [w.strip(".,;:!?()[]") for w in title.split()]
        sig_words = [w for w in words if len(w) >= 4 and w not in STOP][:5]
        if not sig_words or not filing_date:
            # singleton — cannot group
            key = f"single:{rec.get('patent_id', '')}"
            groups[key].append(rec.get("patent_id", ""))
        else:
            key = f"{filing_date}:{':'.join(sig_words)}"
            groups[key].append(rec.get("patent_id", ""))

    families: list[PatentFamily] = []
    for key, members in groups.items():
        if len(members) == 1:
            families.append(PatentFamily(
                family_id=f"fam:PROXY:{hashlib.sha256(key.encode()).hexdigest()[:12]}",
                family_type="SINGLETON",
                member_document_ids=members,
                reconstruction_method="single",
                notes="No other patent shared filing_date + title prefix",
            ))
        else:
            # find earliest filing date among members
            dates = [patent_records[i].get("filing_date", "") for i, r in enumerate(patent_records)
                     if r.get("patent_id") in members]
            earliest = min(dates) if dates else ""
            families.append(PatentFamily(
                family_id=f"fam:PROXY:{hashlib.sha256(key.encode()).hexdigest()[:12]}",
                family_type="PROXY_FAMILY",
                member_document_ids=members,
                reconstruction_method="title_date_proxy",
                earliest_filing_date=earliest,
                notes="PROXY family — heuristic grouping by filing_date + title prefix. "
                      "NOT a DOCDB family. True family reconstruction requires "
                      "EPO OPS / USPTO ODP / Google Patents BigQuery.",
            ))
    return families


def count_family_stats(families: list[PatentFamily]) -> dict:
    """Return honest family statistics."""
    proxy = [f for f in families if f.family_type == "PROXY_FAMILY"]
    singletons = [f for f in families if f.family_type == "SINGLETON"]
    docdb = [f for f in families if f.family_type == "DOCDB_FAMILY"]
    return {
        "PATENT_FAMILIES_RECONSTRUCTED": len(docdb),  # 0 for HuggingFace (honest)
        "PROXY_FAMILIES": len(proxy),                 # heuristic groupings
        "SINGLETONS": len(singletons),                # ungrouped documents
        "TOTAL_FAMILY_GROUPS": len(families),
        "RECONSTRUCTION_METHOD": "title_date_proxy (NOT DOCDB)",
        "HONEST_NOTE": "True DOCDB family reconstruction requires EPO OPS / USPTO ODP / "
                       "Google Patents BigQuery. HuggingFace allenai/us-patents does not "
                       "provide priority/application data, so PATENT_FAMILIES_RECONSTRUCTED = 0.",
    }
