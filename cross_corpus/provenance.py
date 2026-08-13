"""
Provenance semantics for cross-corpus edges (Issue #4).

Implements the EPO citation-role taxonomy:
  X - novelty-killing prior art
  Y - inventive-step prior art (used in combination)
  A - background / state of the art
  T - theoretical (post-priority, explanatory)
  D - cited by applicant in the application
  * - other

These roles matter for discovery: a patent that cites a paper as X or Y is
*claiming that the paper teaches away from or anticipates the invention* —
a much stronger evidentiary relation than a generic A citation.

This module also handles NPL (non-patent literature) citations: scientific
papers cited as prior art in patent search reports. Per EPO statistics, NPL
appears in ~27.8% of search reports (and >50% in chemistry/biotech), so NPL
edges are first-class in the graph.
"""
from __future__ import annotations
from .schema import Citation, CITATION_ROLES


# Role strength for entailed-check weighting.
# X/Y are adversarial (patent office asserting the paper teaches the invention),
# D is applicant-asserted, A is background, T is explanatory, * is unknown.
ROLE_STRENGTH = {
    "X": "adversarial_strong",
    "Y": "adversarial_combination",
    "A": "background",
    "T": "explanatory",
    "D": "applicant_asserted",
    "*": "unknown",
}


def is_npl_citation(c: Citation) -> bool:
    """An NPL citation = a patent citing a paper (or other non-patent lit)."""
    return c.source_kind == "patent" and c.target_kind in ("paper", "npl")


def is_patent_to_patent(c: Citation) -> bool:
    return c.source_kind == "patent" and c.target_kind == "patent"


def is_paper_to_paper(c: Citation) -> bool:
    return c.source_kind == "paper" and c.target_kind == "paper"


def is_paper_to_patent(c: Citation) -> bool:
    """A scientific paper citing a patent (less common, but exists)."""
    return c.source_kind == "paper" and c.target_kind == "patent"


def cross_corpus_edge(c: Citation) -> bool:
    """True iff the citation crosses the paper/patent corpus boundary."""
    return (c.source_kind == "patent" and c.target_kind in ("paper", "npl")) or \
           (c.source_kind == "paper" and c.target_kind == "patent")


def strength(role: str) -> str:
    if role not in CITATION_ROLES:
        raise ValueError(f"Bad role: {role!r}")
    return ROLE_STRENGTH[role]


def provenance_qualifies_as_evidence(c: Citation) -> bool:
    """A citation qualifies as evidence of the *target* teaching the *source*.

    Adversarial (X/Y) and applicant-asserted (D) citations qualify: the patent
    office or applicant is on record that the target document is relevant to
    the invention. Background (A) and explanatory (T) citations are weaker and
    do NOT by themselves qualify — they are context, not evidence of teaching.

    UNKNOWN (*) never qualifies.
    """
    return c.role in ("X", "Y", "D")


def explain(c: Citation) -> str:
    base = {
        "X": "novelty-killing: the examiner asserts the target anticipates the claimed invention",
        "Y": "inventive-step: the examiner combines the target with others to deny inventive step",
        "A": "background: target is general state of the art, not asserted as teaching",
        "T": "theoretical: post-priority document cited for understanding the invention",
        "D": "applicant-asserted: cited by the applicant in the application",
        "*": "unclassified: role not stated",
    }[c.role]
    return f"{c.source_kind}:{c.source_id} -> {c.target_kind}:{c.target_id}  [{c.role}]  {base}"
