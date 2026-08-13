"""
V5 Typed Cross-Corpus Edges (Issue #5 V5, directive C).

Per CTO: "Delete/disable generic keyword-overlap edges as scientific edges.
Keyword overlap can be a search signal, but it must not be represented as a
scientific cross-corpus relationship."

10 typed edge types. Each edge carries: edge_type, source_record_id,
target_record_id, source_field, provenance_uri, confidence, creation_method.

SEMANTIC_SEARCH_CANDIDATE must NEVER be treated as evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


# =====================================================================
# 10 TYPED EDGE TYPES (directive C)
# =====================================================================

# EVIDENCE edges — represent real, verifiable connections
EVIDENCE_EDGE_TYPES = {
    "DIRECT_ID_MATCH",               # same identifier (DOI, patent number) in both corpora
    "EXPLICIT_PATENT_NPL_CITATION",  # patent cites paper as non-patent literature (with EPO role)
    "BIBLIOGRAPHIC_CITATION",        # paper cites patent in its reference list
    "AUTHOR_INVENTOR_LINK",          # same person is author on paper + inventor on patent
    "ASSIGNEE_INSTITUTION_LINK",     # patent assignee = paper author's institution
    "FAMILY_PRIORITY_LINK",          # patent family priority links two patents
    "CPC_IPC_ALIGNMENT",             # shared CPC/IPC classification code
    "MECHANISM_ALIGNMENT",           # shared explicit mechanism (controlled vocabulary)
}

# SEARCH-ONLY edges — never treated as evidence
SEARCH_ONLY_EDGE_TYPES = {
    "TEMPORAL_PROXIMITY",            # documents close in time (search signal only)
    "SEMANTIC_SEARCH_CANDIDATE",     # embedding/keyword similarity (search signal only)
}

ALL_V5_EDGE_TYPES = EVIDENCE_EDGE_TYPES | SEARCH_ONLY_EDGE_TYPES


@dataclass(frozen=True)
class TypedCrossCorpusEdge:
    """A typed cross-corpus edge with full provenance.

    Every edge carries 7 mandatory fields per directive C:
      edge_type, source_record_id, target_record_id, source_field,
      provenance_uri, confidence, creation_method
    """
    edge_id: str
    edge_type: str
    source_record_id: str
    target_record_id: str
    source_field: str             # which field of the source record this edge derives from
    provenance_uri: str           # URI of the source document/endpoint
    confidence: Optional[float]   # None for deterministic edges; 0..1 for inferred
    creation_method: str          # "exact_id_match" | "npl_citation_parse" | etc.
    is_evidence: bool = True      # False for SEARCH_ONLY edges
    evidence_class_source: str = ""
    evidence_class_target: str = ""
    notes: str = ""

    def __post_init__(self):
        if self.edge_type not in ALL_V5_EDGE_TYPES:
            raise ValueError(f"Bad edge_type: {self.edge_type!r}")
        # SEMANTIC_SEARCH_CANDIDATE and TEMPORAL_PROXIMITY are NEVER evidence
        if self.edge_type in SEARCH_ONLY_EDGE_TYPES:
            object.__setattr__(self, "is_evidence", False)
        else:
            object.__setattr__(self, "is_evidence", True)
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Bad confidence: {self.confidence}")

    def canonical_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.canonical_dict(), sort_keys=True).encode()
        ).hexdigest()


def make_typed_edge(edge_type: str, source_record_id: str, target_record_id: str,
                    *, source_field: str, provenance_uri: str,
                    confidence: Optional[float], creation_method: str,
                    evidence_class_source: str = "", evidence_class_target: str = "",
                    notes: str = "") -> TypedCrossCorpusEdge:
    """Construct a typed cross-corpus edge. Validates all fields."""
    eid = f"v5edge:{hashlib.sha256(f'{edge_type}|{source_record_id}|{target_record_id}'.encode()).hexdigest()[:12]}"
    return TypedCrossCorpusEdge(
        edge_id=eid, edge_type=edge_type,
        source_record_id=source_record_id, target_record_id=target_record_id,
        source_field=source_field, provenance_uri=provenance_uri,
        confidence=confidence, creation_method=creation_method,
        evidence_class_source=evidence_class_source,
        evidence_class_target=evidence_class_target,
        notes=notes,
    )


# =====================================================================
# Edge builders — each produces only REAL typed edges
# =====================================================================

def build_direct_id_matches(records: list[dict]) -> list[TypedCrossCorpusEdge]:
    """Build DIRECT_ID_MATCH edges: same DOI/patent-number appears in both corpora.

    This requires that a paper's DOI is explicitly referenced in a patent's
    text, or vice versa. We scan patent text for DOI patterns.
    """
    import re
    edges = []
    doi_pattern = re.compile(r'10\.\d{4,}/[^\s,;\"<>]+')
    papers = [r for r in records if r.get("evidence_class") == "SCIENTIFIC_OBSERVATION"]
    patents = [r for r in records if r.get("evidence_class") == "PATENT_DISCLOSURE"]
    # Index papers by DOI
    papers_by_doi = {}
    for p in papers:
        doi = p.get("doi", "").lower().strip()
        if doi:
            papers_by_doi[doi] = p
    # Scan patent text for DOIs
    for pat in patents:
        text = pat.get("fulltext", "") or pat.get("abstract", "") or pat.get("title", "")
        for m in doi_pattern.finditer(text):
            doi = m.group().lower().rstrip(".")
            if doi in papers_by_doi:
                paper = papers_by_doi[doi]
                edges.append(make_typed_edge(
                    "DIRECT_ID_MATCH",
                    source_record_id=pat["record_id"],
                    target_record_id=paper["record_id"],
                    source_field="fulltext",
                    provenance_uri=pat.get("source_uri", ""),
                    confidence=None,  # deterministic
                    creation_method="doi_regex_match",
                    evidence_class_source="PATENT_DISCLOSURE",
                    evidence_class_target="SCIENTIFIC_OBSERVATION",
                    notes=f"DOI {doi} found in patent text",
                ))
    return edges


def build_cpc_ipc_alignment(records: list[dict]) -> list[TypedCrossCorpusEdge]:
    """Build CPC_IPC_ALIGNMENT edges: patents sharing CPC/IPC classification codes.

    This is an EVIDENCE edge because classification codes are assigned by
    patent examiners — they represent authoritative topic alignment.
    """
    from collections import defaultdict
    edges = []
    patents = [r for r in records if r.get("evidence_class") == "PATENT_DISCLOSURE"]
    by_code: dict[str, list[dict]] = defaultdict(list)
    for p in patents:
        codes = p.get("classification_codes", [])
        if isinstance(codes, list):
            for c in codes:
                code = c if isinstance(c, str) else c.get("code", "")
                if code:
                    by_code[code].append(p)
    for code, group in by_code.items():
        if len(group) < 2:
            continue
        # Create edges between all pairs sharing this code
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                edges.append(make_typed_edge(
                    "CPC_IPC_ALIGNMENT",
                    source_record_id=group[i]["record_id"],
                    target_record_id=group[j]["record_id"],
                    source_field="classification_codes",
                    provenance_uri=group[i].get("source_uri", ""),
                    confidence=None,
                    creation_method="shared_cpc_ipc_code",
                    evidence_class_source="PATENT_DISCLOSURE",
                    evidence_class_target="PATENT_DISCLOSURE",
                    notes=f"shared code: {code}",
                ))
    return edges


def build_temporal_proximity(records: list[dict], *, window_days: int = 365) -> list[TypedCrossCorpusEdge]:
    """Build TEMPORAL_PROXIMITY edges: documents close in time.

    This is a SEARCH-ONLY edge (is_evidence=False). Used for search
    prioritization, never as evidence of a relationship.
    """
    from datetime import date, timedelta
    edges = []
    # Sort by date
    dated = [(r.get("date", ""), r) for r in records if r.get("date")]
    dated.sort(key=lambda x: x[0])
    for i, (d1, r1) in enumerate(dated):
        try:
            date1 = date.fromisoformat(d1[:10])
        except Exception:
            continue
        for j in range(i + 1, min(i + 50, len(dated))):  # look-ahead window
            d2, r2 = dated[j]
            try:
                date2 = date.fromisoformat(d2[:10])
            except Exception:
                continue
            delta = abs((date2 - date1).days)
            if delta > window_days:
                break
            if delta == 0:
                continue
            edges.append(make_typed_edge(
                "TEMPORAL_PROXIMITY",
                source_record_id=r1["record_id"],
                target_record_id=r2["record_id"],
                source_field="date",
                provenance_uri="",
                confidence=1.0 - (delta / window_days),
                creation_method="date_window",
                evidence_class_source=r1.get("evidence_class", ""),
                evidence_class_target=r2.get("evidence_class", ""),
                notes=f"delta_days={delta}",
            ))
    return edges


def build_semantic_search_candidates(records: list[dict], *,
                                     keyword_threshold: int = 5) -> list[TypedCrossCorpusEdge]:
    """Build SEMANTIC_SEARCH_CANDIDATE edges: keyword overlap between paper and patent.

    PER CTO DIRECTIVE: "SEMANTIC_SEARCH_CANDIDATE must NEVER be treated as evidence."
    These edges are is_evidence=False. They exist ONLY for search prioritization.
    """
    STOP = {"the", "a", "an", "of", "in", "for", "and", "with", "to", "on",
            "is", "are", "was", "were", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "must", "can", "this", "that", "these", "those",
            "it", "its", "as", "at", "by", "from", "or", "not", "no", "but",
            "if", "then", "else", "when", "where", "which", "who", "whom",
            "method", "system", "device", "apparatus", "comprising", "include",
            "includes", "including", "first", "second", "third", "one", "two",
            "three", "more", "less", "than", "about", "into", "through", "during",
            "between", "within", "without", "above", "below", "up", "down",
            "over", "under", "again", "further", "once", "here", "there",
            "all", "each", "every", "both", "few", "other", "some", "such",
            "only", "own", "same", "so", "very", "just", "now"}

    def extract_kw(rec: dict) -> set[str]:
        text = " ".join([
            rec.get("title", "") or "",
            rec.get("abstract", "") or "",
            (rec.get("fulltext", "") or "")[:500],
        ]).lower()
        return {w.strip(".,;:!?()[]{}\"'") for w in text.split()
                if len(w.strip(".,;:!?()[]{}\"'")) >= 4
                and w.strip(".,;:!?()[]{}\"'").lower() not in STOP
                and w.strip(".,;:!?()[]{}\"'").isalpha()}

    from collections import defaultdict
    edges = []
    papers = [r for r in records if r.get("evidence_class") == "SCIENTIFIC_OBSERVATION"]
    patents = [r for r in records if r.get("evidence_class") == "PATENT_DISCLOSURE"]
    # Index by domain
    papers_by_domain: dict[str, list] = defaultdict(list)
    patents_by_domain: dict[str, list] = defaultdict(list)
    for p in papers:
        d = p.get("domain", "")
        if d:
            papers_by_domain[d].append(p)
    for p in patents:
        d = p.get("domain", "")
        if d:
            patents_by_domain[d].append(p)
    for domain in papers_by_domain:
        dom_papers = papers_by_domain[domain]
        dom_patents = patents_by_domain.get(domain, [])
        p_kw = {p["record_id"]: extract_kw(p) for p in dom_papers}
        pat_kw = {p["record_id"]: extract_kw(p) for p in dom_patents}
        for paper in dom_papers:
            pkw = p_kw.get(paper["record_id"], set())
            if not pkw:
                continue
            for patent in dom_patents:
                kw = pat_kw.get(patent["record_id"], set())
                if not kw:
                    continue
                overlap = pkw & kw
                if len(overlap) >= keyword_threshold:
                    edges.append(make_typed_edge(
                        "SEMANTIC_SEARCH_CANDIDATE",
                        source_record_id=paper["record_id"],
                        target_record_id=patent["record_id"],
                        source_field="title+abstract",
                        provenance_uri="",
                        confidence=min(len(overlap) / 10.0, 1.0),
                        creation_method="keyword_overlap",
                        evidence_class_source="SCIENTIFIC_OBSERVATION",
                        evidence_class_target="PATENT_DISCLOSURE",
                        notes=f"keyword_overlap={len(overlap)}, domain={domain}",
                    ))
    return edges


def build_all_v5_edges(records: list[dict]) -> dict:
    """Build all V5 typed edges. Returns a dict with evidence and search-only edges separated."""
    direct = build_direct_id_matches(records)
    cpc = build_cpc_ipc_alignment(records)
    temporal = build_temporal_proximity(records)
    semantic = build_semantic_search_candidates(records)
    return {
        "evidence_edges": {
            "DIRECT_ID_MATCH": [e.canonical_dict() for e in direct],
            "CPC_IPC_ALIGNMENT": [e.canonical_dict() for e in cpc],
        },
        "search_only_edges": {
            "TEMPORAL_PROXIMITY": [e.canonical_dict() for e in temporal],
            "SEMANTIC_SEARCH_CANDIDATE": [e.canonical_dict() for e in semantic],
        },
        "summary": {
            "evidence_edge_count": len(direct) + len(cpc),
            "search_only_edge_count": len(temporal) + len(semantic),
            "by_type": {
                "DIRECT_ID_MATCH": len(direct),
                "CPC_IPC_ALIGNMENT": len(cpc),
                "TEMPORAL_PROXIMITY": len(temporal),
                "SEMANTIC_SEARCH_CANDIDATE": len(semantic),
            },
        },
    }
