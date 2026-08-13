"""
Knowledge distance metrics (Issue #5).

Per CEO directive: "do not call high-distance candidates discoveries. Distance
is a search prioritization variable, not evidence of truth."

We compute six distance dimensions:
  - domain_distance: 0 (same) to 5 (different universe)
  - mechanism_distance: 0 (same mechanism) to 1 (no shared mechanisms)
  - temporal_distance: years between the two anchor dates
  - evidence_distance: 0 (same evidence type) to 1 (different types)
  - implementation_distance: 0 (same product/code) to 1 (no shared codebase)
  - constraint_distance: 0 (same constraints) to 1 (orthogonal constraints)

The aggregate distance is a weighted sum, used ONLY for ranking candidates
by "interestingness" — never as evidence that a candidate is correct.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Iterable
from .domain_map import domain_distance as _domain_distance


@dataclass
class KnowledgeDistance:
    domain_distance: int          # 0-5
    mechanism_distance: float     # 0.0-1.0
    temporal_distance_years: float
    evidence_distance: float      # 0.0-1.0
    implementation_distance: float  # 0.0-1.0
    constraint_distance: float    # 0.0-1.0
    aggregate: float              # weighted sum, 0.0-1.0

    def to_dict(self) -> dict:
        return {
            "domain_distance": self.domain_distance,
            "mechanism_distance": self.mechanism_distance,
            "temporal_distance_years": self.temporal_distance_years,
            "evidence_distance": self.evidence_distance,
            "implementation_distance": self.implementation_distance,
            "constraint_distance": self.constraint_distance,
            "aggregate": self.aggregate,
        }


# Weights for the aggregate. Sum = 1.0.
WEIGHTS = {
    "domain": 0.25,
    "mechanism": 0.20,
    "temporal": 0.15,
    "evidence": 0.20,
    "implementation": 0.10,
    "constraint": 0.10,
}


def compute_distance(*, domains_a: Iterable[str], domains_b: Iterable[str],
                     mechanisms_a: Iterable[str], mechanisms_b: Iterable[str],
                     date_a: str | None, date_b: str | None,
                     evidence_types_a: Iterable[str], evidence_types_b: Iterable[str],
                     implementations_a: Iterable[str] = (), implementations_b: Iterable[str] = (),
                     constraints_a: Iterable[str] = (), constraints_b: Iterable[str] = ()) -> KnowledgeDistance:
    """Compute the knowledge distance between two anchor sets.

    All inputs are iterables of strings. Empty iterables contribute max
    distance (we cannot prove similarity).
    """
    # Domain distance: max over all (a, b) pairs (most-distant pair governs)
    da = list(domains_a) or ["unknown"]
    db = list(domains_b) or ["unknown"]
    d_dom = max(_domain_distance(a, b) for a in da for b in db)
    # normalize 0-5 to 0.0-1.0
    d_dom_norm = d_dom / 5.0

    # Mechanism distance: 1 - Jaccard similarity of mechanism sets
    ma = set(mechanisms_a)
    mb = set(mechanisms_b)
    if not ma and not mb:
        d_mech = 1.0
    else:
        union = ma | mb
        if not union:
            d_mech = 1.0
        else:
            d_mech = 1.0 - (len(ma & mb) / len(union))

    # Temporal distance in years
    d_temp = 0.0
    if date_a and date_b:
        try:
            da_ = date.fromisoformat(date_a[:10])
            db_ = date.fromisoformat(date_b[:10])
            d_temp = abs((da_ - db_).days) / 365.25
        except Exception:
            d_temp = 0.0

    # Evidence distance: 0 if same type, 1 if different
    ea = set(evidence_types_a)
    eb = set(evidence_types_b)
    if not ea or not eb:
        d_ev = 1.0
    elif ea & eb:
        d_ev = 0.0
    else:
        d_ev = 1.0

    # Implementation distance: 1 - Jaccard of implementation sets (code/products)
    ia = set(implementations_a)
    ib = set(implementations_b)
    if not ia and not ib:
        d_impl = 1.0
    else:
        union = ia | ib
        if not union:
            d_impl = 1.0
        else:
            d_impl = 1.0 - (len(ia & ib) / len(union))

    # Constraint distance: 1 - Jaccard of constraint sets
    ca = set(constraints_a)
    cb = set(constraints_b)
    if not ca and not cb:
        d_con = 1.0
    else:
        union = ca | cb
        if not union:
            d_con = 1.0
        else:
            d_con = 1.0 - (len(ca & cb) / len(union))

    aggregate = (
        WEIGHTS["domain"] * d_dom_norm +
        WEIGHTS["mechanism"] * d_mech +
        WEIGHTS["temporal"] * min(d_temp / 10.0, 1.0) +  # cap at 10 years
        WEIGHTS["evidence"] * d_ev +
        WEIGHTS["implementation"] * d_impl +
        WEIGHTS["constraint"] * d_con
    )

    return KnowledgeDistance(
        domain_distance=d_dom,
        mechanism_distance=d_mech,
        temporal_distance_years=d_temp,
        evidence_distance=d_ev,
        implementation_distance=d_impl,
        constraint_distance=d_con,
        aggregate=aggregate,
    )
