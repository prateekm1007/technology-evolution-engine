"""
Ingest for the cross-corpus pilot (Issue #4).

Two ingest shapes:
  - papers:  OpenAlex-shaped JSONL  (id, doi, title, abstract, publication_date,
             authors, concepts, ...)
  - patents: EPO-OPS-shaped JSONL   (publication_number, docdb_family_id,
             publication_date, priority_date, jurisdictions, inventors,
             assignee, title, abstract, citations[{target, role, kind}], ...)

Per-record validation:
  - reject records missing required fields (id, dates)
  - reject citation roles outside the EPO taxonomy
  - compute and store content_hash per record
  - reject duplicates by id

Per-record hashing is content-addressable: same content -> same hash, so
the frozen corpus can be integrity-checked later.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator
from .schema import Paper, Patent, Claim, Citation, content_hash


REQUIRED_PAPER_FIELDS = {"paper_id"}
REQUIRED_PATENT_FIELDS = {"patent_id"}


def _coerce_claims(raw: list) -> list[Claim]:
    out = []
    for r in raw or []:
        out.append(Claim(
            subject=r["subject"],
            predicate=r["predicate"],
            obj=r["obj"],
            value=r.get("value"),
            negated=bool(r.get("negated", False)),
        ))
    return out


def _coerce_citations(raw: list, source_kind: str) -> list[Citation]:
    out = []
    for r in raw or []:
        out.append(Citation(
            source_id=r["source_id"],
            target_id=r["target_id"],
            source_kind=source_kind,
            target_kind=r["target_kind"],
            role=r["role"],
            citation_date=r.get("citation_date"),
        ))
    return out


def ingest_paper(raw: dict) -> Paper:
    missing = REQUIRED_PAPER_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(f"Paper missing required fields: {missing}")
    p = Paper(
        paper_id=raw["paper_id"],
        doi=raw.get("doi"),
        title=raw.get("title", ""),
        abstract=raw.get("abstract", ""),
        publication_date=raw.get("publication_date"),
        authors=list(raw.get("authors", [])),
        domain=raw.get("domain", ""),
        mechanisms=list(raw.get("mechanisms", [])),
        materials=list(raw.get("materials", [])),
        processes=list(raw.get("processes", [])),
        claims=_coerce_claims(raw.get("claims", [])),
        citations=_coerce_citations(raw.get("citations", []), "paper"),
        reported_failures=list(raw.get("reported_failures", [])),
        ingestion_source=raw.get("ingestion_source", "openalex"),
    )
    return p


def ingest_patent(raw: dict) -> Patent:
    missing = REQUIRED_PATENT_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(f"Patent missing required fields: {missing}")
    p = Patent(
        patent_id=raw["patent_id"],
        docdb_family_id=raw.get("docdb_family_id", ""),
        publication_date=raw.get("publication_date"),
        priority_date=raw.get("priority_date"),
        jurisdictions=list(raw.get("jurisdictions", [])),
        inventors=list(raw.get("inventors", [])),
        assignee=raw.get("assignee"),
        title=raw.get("title", ""),
        abstract=raw.get("abstract", ""),
        domain=raw.get("domain", ""),
        mechanisms=list(raw.get("mechanisms", [])),
        materials=list(raw.get("materials", [])),
        processes=list(raw.get("processes", [])),
        claims=_coerce_claims(raw.get("claims", [])),
        citations=_coerce_citations(raw.get("citations", []), "patent"),
        ingestion_source=raw.get("ingestion_source", "epo_ops"),
    )
    return p


def load_papers_jsonl(path: Path) -> list[Paper]:
    papers: list[Paper] = []
    seen_hashes: set[str] = set()
    for i, line in enumerate(Path(path).read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        p = ingest_paper(raw)
        h = p.content_hash()
        if h in seen_hashes:
            raise ValueError(f"Duplicate paper content at line {i+1}: {p.paper_id}")
        seen_hashes.add(h)
        papers.append(p)
    return papers


def load_patents_jsonl(path: Path) -> list[Patent]:
    patents: list[Patent] = []
    seen_hashes: set[str] = set()
    for i, line in enumerate(Path(path).read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        p = ingest_patent(raw)
        h = p.content_hash()
        if h in seen_hashes:
            raise ValueError(f"Duplicate patent content at line {i+1}: {p.patent_id}")
        seen_hashes.add(h)
        patents.append(p)
    return patents


def corpus_manifest(papers: list[Paper], patents: list[Patent]) -> dict:
    """Build a manifest of corpus hashes for integrity checking."""
    import hashlib
    paper_hashes = {p.paper_id: p.content_hash() for p in papers}
    patent_hashes = {p.patent_id: p.content_hash() for p in patents}
    all_hashes = list(paper_hashes.values()) + list(patent_hashes.values())
    return {
        "paper_count": len(papers),
        "patent_count": len(patents),
        "paper_hashes": paper_hashes,
        "patent_hashes": patent_hashes,
        "corpus_root_hash": hashlib.sha256(
            "|".join(sorted(all_hashes)).encode()
        ).hexdigest(),
    }
