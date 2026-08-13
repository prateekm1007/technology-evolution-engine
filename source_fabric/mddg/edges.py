"""
Medical Device Discovery Graph V1 — 3-Tier Typed Edges (CTO directive #4, #5).

3 edge tiers:
  Tier A — STRUCTURAL: exact identifiers, citations, priority chains,
           product codes, regulatory identifiers. Deterministic.
  Tier B — SUBSTANTIVE: explicitly stated mechanism, material, failure,
           clinical endpoint, or design relation. Requires textual evidence.
  Tier C — INFERRED: semantic matching, graph inference, analogy, temporal
           proximity. NEVER masquerades as Tier A/B.

Per CTO: "Tier C must never masquerade as Tier A/B."
Per CTO: "Do not use RELATED_TO."

Every edge has 9 mandatory fields:
  relation_type, source, target, provenance, source_field, retrieval_time,
  temporal_validity, derivation_method, evidence_status
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


# =====================================================================
# 20+ JUSTIFIED TYPED RELATIONSHIPS (directive #4)
# =====================================================================

# Tier A — STRUCTURAL (deterministic, identifier-based)
TIER_A_RELATIONS = {
    "DEVICE_HAS_PRODUCT_CODE",
    "DEVICE_HAS_510K",
    "DEVICE_HAS_PMA",
    "DEVICE_HAS_DENOVO",
    "PATENT_HAS_PRIORITY",
    "PATENT_CITES_PAPER",
    "DEVICE_MANUFACTURED_BY",
    "TRIAL_HAS_ENDPOINT",
    "TRIAL_HAS_OUTCOME",
}

# Tier B — SUBSTANTIVE (explicitly stated in text)
TIER_B_RELATIONS = {
    "PAPER_DESCRIBES_MECHANISM",
    "PAPER_REPORTS_MATERIAL",
    "PATENT_DISCLOSES_MECHANISM",
    "PATENT_CLAIMS_DEVICE",
    "DEVICE_HAS_TRIAL",
    "DEVICE_HAS_ADVERSE_EVENT",
    "DEVICE_HAS_RECALL",
    "RECALL_HAS_FAILURE_MODE",
    "ADVERSE_EVENT_HAS_FAILURE_MODE",
    "PAPER_EXPLAINS_FAILURE",
    "MECHANISM_ADDRESSES_FAILURE",
    "STANDARD_CONSTRAINS_DEVICE",
}

# Tier C — INFERRED (never evidence)
TIER_C_RELATIONS = {
    "SEMANTIC_SIMILARITY",
    "TEMPORAL_PROXIMITY",
    "GRAPH_INFERENCE",
    "ANALOGY",
}

ALL_MDDG_RELATIONS = TIER_A_RELATIONS | TIER_B_RELATIONS | TIER_C_RELATIONS


def get_tier(relation_type: str) -> str:
    if relation_type in TIER_A_RELATIONS:
        return "A"
    if relation_type in TIER_B_RELATIONS:
        return "B"
    if relation_type in TIER_C_RELATIONS:
        return "C"
    raise ValueError(f"Unknown relation_type: {relation_type!r}")


def is_evidence(relation_type: str) -> bool:
    """Tier A and B are evidence. Tier C is NEVER evidence."""
    return get_tier(relation_type) in ("A", "B")


# =====================================================================
# Missing-link states (directive #6)
# =====================================================================

MISSING_LINK_STATES = {
    "UNKNOWN",
    "NOT_FOUND",
    "NOT_APPLICABLE",
    "SOURCE_NOT_AVAILABLE",
}


@dataclass(frozen=True)
class MDDGEdge:
    """A typed medical-device graph edge with 9 mandatory fields."""
    edge_id: str
    relation_type: str
    source: str                    # source entity canonical_id
    target: str                    # target entity canonical_id
    provenance: str                # URI / source reference
    source_field: str              # which field of the source this derives from
    retrieval_time: str            # ISO timestamp
    temporal_validity: str         # "valid" | "expired" | "unknown"
    derivation_method: str         # "exact_id_match" | "text_extraction" | "semantic" | etc.
    evidence_status: str           # "EVIDENCE" | "SEARCH_ONLY" | "MISSING"
    tier: str = ""                 # "A" | "B" | "C" (derived from relation_type)
    confidence: Optional[float] = None
    notes: str = ""

    def __post_init__(self):
        if self.relation_type not in ALL_MDDG_RELATIONS:
            raise ValueError(f"Bad relation_type: {self.relation_type!r}")
        tier = get_tier(self.relation_type)
        object.__setattr__(self, "tier", tier)
        # Tier C is NEVER evidence
        if tier == "C":
            object.__setattr__(self, "evidence_status", "SEARCH_ONLY")
        elif self.evidence_status not in ("EVIDENCE", "SEARCH_ONLY", "MISSING"):
            raise ValueError(f"Bad evidence_status: {self.evidence_status!r}")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Bad confidence: {self.confidence}")
        if self.relation_type == "RELATED_TO":
            raise ValueError("RELATED_TO is FORBIDDEN")

    def canonical_dict(self) -> dict:
        return asdict(self)

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.canonical_dict(), sort_keys=True).encode()
        ).hexdigest()


def make_mddg_edge(relation_type: str, source: str, target: str, *,
                   provenance: str, source_field: str, retrieval_time: str,
                   temporal_validity: str, derivation_method: str,
                   evidence_status: str = "EVIDENCE",
                   confidence: Optional[float] = None,
                   notes: str = "") -> MDDGEdge:
    eid = f"mddg:{hashlib.sha256(f'{relation_type}|{source}|{target}'.encode()).hexdigest()[:12]}"
    return MDDGEdge(
        edge_id=eid, relation_type=relation_type,
        source=source, target=target,
        provenance=provenance, source_field=source_field,
        retrieval_time=retrieval_time, temporal_validity=temporal_validity,
        derivation_method=derivation_method, evidence_status=evidence_status,
        confidence=confidence, notes=notes,
    )


@dataclass(frozen=True)
class MissingLink:
    """A missing link in a device lifecycle. Never filled by inference."""
    source: str
    expected_target_type: str      # e.g. "PATENT" | "CLINICAL_TRIAL" | "ADVERSE_EVENT"
    state: str                     # UNKNOWN | NOT_FOUND | NOT_APPLICABLE | SOURCE_NOT_AVAILABLE
    notes: str = ""

    def __post_init__(self):
        if self.state not in MISSING_LINK_STATES:
            raise ValueError(f"Bad missing-link state: {self.state!r}")
