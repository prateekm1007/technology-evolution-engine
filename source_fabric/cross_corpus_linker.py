"""
Phase 8 — Cross-corpus linkage (Issue #5).

8 EXPLICIT edge types. NO generic RELATED_TO.

  DIRECT_ID_MATCH       — the same identifier appears in both corpora
                          (e.g. a DOI cited in a patent's NPL section)
  OFFICE_CITATION       — patent office examiner citation (X/Y/A/T/D)
  BIBLIOGRAPHIC_MATCH   — title/author/year match between paper and patent
  AUTHOR_INVENTOR_MATCH — the same person is an author on a paper and an
                          inventor on a patent
  AFFILIATION_MATCH     — the same organization appears on both
  SEMANTIC_MATCH        — embedding-based similarity (always carries a score
                          and NEVER substitutes for a direct citation)
  TOPIC_ALIGNMENT       — shared CPC/IPC code ↔ OpenAlex concept
  INFERRED_BRIDGE       — a hypothesis edge; must be flagged as inferred
                          and never promoted to "confirmed" without direct
                          evidence

Every edge carries:
  - edge_type (from the 8 above)
  - source_node_id, target_node_id
  - evidence_tier (A-I per CONSTITUTION)
  - confidence (0..1; None if deterministic)
  - provenance_source_id (which source provided this edge)
  - is_inferred (bool) — True for INFERRED_BRIDGE and SEMANTIC_MATCH
  - notes
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import hashlib
import json


CROSS_CORPUS_EDGE_TYPES = {
    "DIRECT_ID_MATCH",
    "OFFICE_CITATION",
    "BIBLIOGRAPHIC_MATCH",
    "AUTHOR_INVENTOR_MATCH",
    "AFFILIATION_MATCH",
    "SEMANTIC_MATCH",
    "TOPIC_ALIGNMENT",
    "INFERRED_BRIDGE",
}

# Edges that are deterministic (do not carry a confidence score)
DETERMINISTIC_EDGES = {
    "DIRECT_ID_MATCH",      # the ID is the ID
    "OFFICE_CITATION",      # the examiner made the citation
}

# Edges that are inferred (must be flagged)
INFERRED_EDGE_TYPES = {
    "SEMANTIC_MATCH",       # embedding-based — always inferred
    "INFERRED_BRIDGE",      # by definition
    "BIBLIOGRAPHIC_MATCH",  # fuzzy match — inferred
}


@dataclass(frozen=True)
class CrossCorpusEdge:
    edge_id: str
    edge_type: str
    source_node_id: str          # e.g. "paper:openalex:W1234"
    target_node_id: str          # e.g. "patent:EP:EP1234567B1"
    evidence_tier: str           # A-I per CONSTITUTION
    confidence: Optional[float] = None
    provenance_source_id: str = ""
    is_inferred: bool = False
    notes: str = ""
    citation_role: Optional[str] = None  # X/Y/A/T/D/* for OFFICE_CITATION

    def __post_init__(self):
        if self.edge_type not in CROSS_CORPUS_EDGE_TYPES:
            raise ValueError(f"Bad edge_type: {self.edge_type!r}. "
                             f"Allowed: {sorted(CROSS_CORPUS_EDGE_TYPES)}")
        if self.edge_type in DETERMINISTIC_EDGES and self.confidence is not None:
            # deterministic edges should not carry confidence
            object.__setattr__(self, "confidence", None)
        if self.edge_type in INFERRED_EDGE_TYPES and not self.is_inferred:
            object.__setattr__(self, "is_inferred", True)
        if self.edge_type == "OFFICE_CITATION" and self.citation_role is None:
            raise ValueError("OFFICE_CITATION requires citation_role (X/Y/A/T/D/*)")
        if self.evidence_tier not in "ABCDEFGHI":
            raise ValueError(f"Bad evidence_tier: {self.evidence_tier!r}")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Bad confidence: {self.confidence}")

    def canonical_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.canonical_dict(), sort_keys=True).encode()
        ).hexdigest()


def make_edge(edge_type: str, source_node_id: str, target_node_id: str,
              evidence_tier: str, *, confidence: Optional[float] = None,
              provenance_source_id: str = "", notes: str = "",
              citation_role: Optional[str] = None) -> CrossCorpusEdge:
    """Construct a cross-corpus edge. Automatically sets is_inferred for
    inferred edge types. Rejects generic RELATED_TO."""
    if edge_type == "RELATED_TO":
        raise ValueError("RELATED_TO is FORBIDDEN. Use one of the 8 typed edges.")
    eid = f"edge:{hashlib.sha256(f'{edge_type}|{source_node_id}|{target_node_id}'.encode()).hexdigest()[:12]}"
    return CrossCorpusEdge(
        edge_id=eid, edge_type=edge_type,
        source_node_id=source_node_id, target_node_id=target_node_id,
        evidence_tier=evidence_tier, confidence=confidence,
        provenance_source_id=provenance_source_id,
        is_inferred=(edge_type in INFERRED_EDGE_TYPES),
        notes=notes, citation_role=citation_role,
    )


def validate_cross_corpus_edge(edge: CrossCorpusEdge) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    if edge.edge_type not in CROSS_CORPUS_EDGE_TYPES:
        errors.append(f"bad edge_type: {edge.edge_type}")
    if edge.edge_type == "OFFICE_CITATION" and not edge.citation_role:
        errors.append("OFFICE_CITATION requires citation_role")
    if edge.edge_type in INFERRED_EDGE_TYPES and not edge.is_inferred:
        errors.append(f"{edge.edge_type} must be is_inferred=True")
    if edge.edge_type in DETERMINISTIC_EDGES and edge.confidence is not None:
        errors.append(f"{edge.edge_type} must not carry confidence (deterministic)")
    if edge.confidence is not None and not (0.0 <= edge.confidence <= 1.0):
        errors.append(f"confidence out of range: {edge.confidence}")
    if not edge.source_node_id or not edge.target_node_id:
        errors.append("missing node ids")
    if edge.edge_type == "RELATED_TO":
        errors.append("RELATED_TO is FORBIDDEN")
    return errors
