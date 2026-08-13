"""
Typed provenance for cross-source edges (Issue #5).

NO GENERIC `RELATED_TO`. Every edge has a typed predicate from a controlled
vocabulary. This is the antidote to "everything is connected to everything"
which destroys discovery signal.

Vocabulary:
  cites                  — document A cites document B (with EPO role X/Y/A/T/D/*)
  uses_material          — document A uses material B
  uses_mechanism         — document A invokes mechanism B
  uses_process           — document A uses process B
  validates              — document A experimentally validates claim B
  refutes                — document A experimentally refutes claim B
  implements             — code A implements algorithm/method B (from paper)
  extends                — document A extends work B
  derived_from           — document A is derived from data/method B
  reproduced_from        — document A reproduces result B
  failed_to_reproduce    — document A failed to reproduce result B
  cites_standard         — document A cites standard B as a constraint
  uses_dataset           — document A uses dataset B
  cites_failure          — document A cites failure record B as motivation
  product_of             — product A is the product of patent/standard B
  regulatory_basis_of    — standard/regulation A is the basis of product B
  funded                 — grant A funded document B
  author_of              — researcher A is author of document B
  affiliated_with        — researcher A is affiliated with org B
  translation_of         — document A is a translation of document B (multilingual)

Each edge carries:
  - source_node_id, target_node_id
  - predicate (from the vocabulary above)
  - evidence_tier (A-I per CONSTITUTION)
  - provenance_source_id (which source provided this edge)
  - confidence (0..1, or None if deterministic)
  - harvested_at (ISO timestamp)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import json


PREDICATES = {
    "cites", "uses_material", "uses_mechanism", "uses_process",
    "validates", "refutes", "implements", "extends", "derived_from",
    "reproduced_from", "failed_to_reproduce", "cites_standard",
    "uses_dataset", "cites_failure", "product_of", "regulatory_basis_of",
    "funded", "author_of", "affiliated_with", "translation_of",
}

# Predicates that cross the corpus boundary (paper <-> patent <-> ...)
CROSS_CORPUS_PREDICATES = {
    "cites", "implements", "extends", "derived_from",
    "reproduced_from", "failed_to_reproduce", "cites_standard",
    "uses_dataset", "cites_failure", "product_of", "regulatory_basis_of",
    "funded", "translation_of",
}

# Predicates that imply experimental/empirical evidence
EMPIRICAL_PREDICATES = {"validates", "refutes", "reproduced_from", "failed_to_reproduce"}


@dataclass(frozen=True)
class ProvenanceEdge:
    source_node_id: str
    target_node_id: str
    predicate: str
    evidence_tier: str           # A-I
    provenance_source_id: str    # which source provided this edge
    confidence: Optional[float] = None  # None if deterministic
    harvested_at: str = ""
    citation_role: Optional[str] = None  # X/Y/A/T/D/* if predicate=cites
    notes: str = ""

    def __post_init__(self):
        if self.predicate not in PREDICATES:
            raise ValueError(f"Unknown predicate: {self.predicate!r}. "
                             f"Allowed: {sorted(PREDICATES)}")
        if self.predicate == "cites" and self.citation_role is not None:
            if self.citation_role not in {"X", "Y", "A", "T", "D", "*"}:
                raise ValueError(f"Bad citation_role: {self.citation_role!r}")
        if self.evidence_tier not in "ABCDEFGHI":
            raise ValueError(f"Bad evidence_tier: {self.evidence_tier!r}")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Bad confidence: {self.confidence}")

    def is_cross_corpus(self) -> bool:
        return self.predicate in CROSS_CORPUS_PREDICATES

    def is_empirical(self) -> bool:
        return self.predicate in EMPIRICAL_PREDICATES

    def canonical_dict(self) -> dict:
        return {
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "predicate": self.predicate,
            "evidence_tier": self.evidence_tier,
            "provenance_source_id": self.provenance_source_id,
            "confidence": self.confidence,
            "harvested_at": self.harvested_at,
            "citation_role": self.citation_role,
            "notes": self.notes,
        }

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.canonical_dict(), sort_keys=True).encode()
        ).hexdigest()


def validate_edge(edge: ProvenanceEdge) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    if edge.predicate not in PREDICATES:
        errors.append(f"unknown predicate: {edge.predicate}")
    if edge.evidence_tier not in "ABCDEFGHI":
        errors.append(f"bad evidence_tier: {edge.evidence_tier}")
    if not edge.source_node_id or not edge.target_node_id:
        errors.append("missing node ids")
    if edge.predicate == "cites" and edge.citation_role is None:
        errors.append("cites edge requires citation_role (X/Y/A/T/D/*)")
    if edge.confidence is not None and not (0.0 <= edge.confidence <= 1.0):
        errors.append(f"confidence out of range: {edge.confidence}")
    return errors
