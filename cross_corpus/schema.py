"""
Cross-Corpus Science x Patent Discovery Graph — Schema (Issue #4).

Dataclasses for the unified evidence graph. Every record is hashable and
hash-pinned. Provenance is first-class: citations carry EPO X/Y/A/T/D roles,
not a generic "related" edge.

INVARIANTS:
  - Every node has a stable canonical id and a content hash.
  - publication_date and priority_date are immutable once ingested.
  - Citations carry a `role` from the EPO citation taxonomy.
  - Claims are atomic (one assertion per claim) so the not-entailed check
    is deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from typing import Optional
import hashlib
import json


# --- EPO citation role taxonomy (register.epo.org/help, citeddocuments) ---
#   X  - novelty-killing (cited against novelty)
#   Y  - inventive-step (combined with others against inventive step)
#   A  - background / general state of the art
#   T  - theoretical / written-after-priority but relevant for understanding
#   D  - cited by the applicant in the application
#   *  - other / unclassified
CITATION_ROLES = {"X", "Y", "A", "T", "D", "*"}

# Domains covered by the pilot (10).
PILOT_DOMAINS = [
    "battery_electrochemistry",
    "perovskite_photovoltaics",
    "crispr_gene_editing",
    "mrna_therapeutics",
    "solid_state_lighting",
    "carbon_capture",
    "hydrogen_electrocatalysis",
    "neuromorphic_computing",
    "topological_insulators",
    "additive_manufacturing",
]


def _canonical_json(obj) -> str:
    """Stable JSON for hashing — sorted keys, no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(obj) -> str:
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


def _parse_date(s) -> Optional[str]:
    if s is None:
        return None
    if isinstance(s, date):
        return s.isoformat()
    if isinstance(s, datetime):
        return s.date().isoformat()
    s = str(s).strip()
    if not s:
        return None
    # Accept YYYY-MM-DD or YYYY-MM-DDThh:mm:ss...
    return s[:10]


@dataclass(frozen=True)
class Citation:
    """A citation from one document to another, with an EPO role.

    `source_kind` / `target_kind` in {paper, patent, npl}.
    NPL = non-patent literature (scientific paper cited as prior art in
    a patent search report).
    """
    source_id: str
    target_id: str
    source_kind: str   # paper | patent
    target_kind: str   # paper | patent | npl
    role: str          # X | Y | A | T | D | *
    citation_date: Optional[str] = None  # ISO date when citation was recorded

    def __post_init__(self):
        if self.role not in CITATION_ROLES:
            raise ValueError(f"Bad citation role: {self.role!r}")
        if self.source_kind not in ("paper", "patent"):
            raise ValueError(f"Bad source_kind: {self.source_kind!r}")
        if self.target_kind not in ("paper", "patent", "npl"):
            raise ValueError(f"Bad target_kind: {self.target_kind!r}")

    def key(self) -> str:
        return f"{self.source_id}->{self.target_id}:{self.role}"


@dataclass(frozen=True)
class Claim:
    """Atomic assertion. One predicate per claim so entailment is decidable.

    predicate is a controlled vocabulary token, e.g.:
      increases_conductivity, decreases_degradation, enables_synthesis,
      inhibits_growth, requires_temperature_le, reports_failure_of,
      cannot_combine_with, ...
    """
    subject: str       # e.g. "material:Li7La3Zr2O12"
    predicate: str     # controlled token
    obj: str           # e.g. "property:ionic_conductivity"
    value: Optional[str] = None   # e.g. ">1e-4 S/cm at 25C"
    negated: bool = False         # True => claim asserts the predicate is FALSE

    def text(self) -> str:
        neg = "NOT " if self.negated else ""
        v = f" [{self.value}]" if self.value else ""
        return f"{neg}{self.subject} {self.predicate} {self.obj}{v}"


@dataclass
class Paper:
    paper_id: str               # canonical id, e.g. "paper:OAlex:W1234"
    doi: Optional[str] = None
    title: str = ""
    abstract: str = ""
    publication_date: Optional[str] = None   # ISO date
    authors: list[str] = field(default_factory=list)
    domain: str = ""
    mechanisms: list[str] = field(default_factory=list)   # e.g. ["intercalation"]
    materials: list[str] = field(default_factory=list)    # e.g. ["LiCoO2"]
    processes: list[str] = field(default_factory=list)    # e.g. ["sol-gel"]
    claims: list[Claim] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    reported_failures: list[str] = field(default_factory=list)  # free-text failure notes
    ingestion_source: str = "openalex"   # provenance of the record itself

    def kind(self) -> str:
        return "paper"

    def node_id(self) -> str:
        return self.paper_id

    def canonical_dict(self) -> dict:
        d = asdict(self)
        # claims -> list of text form for stable hashing
        d["claims"] = [c.text() for c in self.claims]
        d["citations"] = [c.key() for c in self.citations]
        return d

    def content_hash(self) -> str:
        return content_hash(self.canonical_dict())


@dataclass
class Patent:
    patent_id: str             # e.g. "patent:EP:EP1234567B1"
    docdb_family_id: str = ""  # INPADOC/DOCDB simple-family id
    publication_date: Optional[str] = None
    priority_date: Optional[str] = None     # earliest priority
    jurisdictions: list[str] = field(default_factory=list)  # [EP, US, JP, ...]
    inventors: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    title: str = ""
    abstract: str = ""
    domain: str = ""
    mechanisms: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    processes: list[str] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)  # includes NPL (paper-target) citations
    ingestion_source: str = "epo_ops"

    def kind(self) -> str:
        return "patent"

    def node_id(self) -> str:
        return self.patent_id

    def canonical_dict(self) -> dict:
        d = asdict(self)
        d["claims"] = [c.text() for c in self.claims]
        d["citations"] = [c.key() for c in self.citations]
        return d

    def content_hash(self) -> str:
        return content_hash(self.canonical_dict())


@dataclass
class PatentFamily:
    """A DOCDB simple family — all members share the same priority."""
    family_id: str             # e.g. "fam:DOCDB:12345678"
    member_patent_ids: list[str] = field(default_factory=list)
    earliest_priority_date: Optional[str] = None
    jurisdictions: list[str] = field(default_factory=list)
    domain: str = ""

    def canonical_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        return content_hash(self.canonical_dict())


@dataclass(frozen=True)
class Candidate:
    """A cross-corpus intersection candidate produced by a motif detector."""
    candidate_id: str
    motif: str                       # one of the 10 motif names
    domain: str
    node_ids: tuple[str, ...]        # nodes forming the intersection
    supporting_edge_summary: str     # human-readable summary of the subgraph
    candidate_claim_text: str        # the candidate assertion (to be tested)
    predicted_outcome: str           # falsifiable, machine-checkable outcome
    prediction_window_days: int      # how long until outcome is checkable
    generated_at: str                # ISO timestamp

    def canonical_dict(self) -> dict:
        d = asdict(self)
        d["node_ids"] = list(self.node_ids)
        return d

    def content_hash(self) -> str:
        return content_hash(self.canonical_dict())
