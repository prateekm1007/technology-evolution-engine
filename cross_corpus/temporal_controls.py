"""
Temporal controls for the cross-corpus pilot (Issue #4).

Rules (mirroring PSCD-1's conservative cutoff):
  1. Cutoff = previous complete UTC day at the time of pilot freeze.
     Strict < : a document dated on or after the registration date is
     NOT eligible evidence.
  2. Patent priority_date is the authoritative "when did this invention exist"
     date. publication_date is when it became public. For evidence availability
     at cutoff, we use min(priority_date, publication_date) — but the
     *invention* date (priority) governs whether it can be cited as prior art
     against a later patent.
  3. Predictions are anchored to the cutoff. The prediction window starts at
     cutoff and ends at cutoff + prediction_window_days.
  4. Outcome verification may only use documents whose date is in
     [cutoff, cutoff + prediction_window_days]. Documents before cutoff were
     already in the evidence subgraph (potential leakage). Documents after the
     window are not yet checkable.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from .schema import Paper, Patent


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def previous_complete_utc_day() -> str:
    """Conservative cutoff: the most recent complete UTC day."""
    return (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()


@dataclass(frozen=True)
class TemporalCutoff:
    cutoff: str           # ISO date; evidence must be strictly before this
    registered_at: str    # ISO timestamp when cutoff was frozen

    def is_eligible_evidence(self, doc_date: Optional[str]) -> bool:
        if not doc_date:
            return False
        return doc_date < self.cutoff

    def is_in_prediction_window(self, doc_date: Optional[str],
                                 window_days: int) -> bool:
        if not doc_date:
            return False
        end = (date.fromisoformat(self.cutoff) +
               timedelta(days=window_days)).isoformat()
        return self.cutoff <= doc_date <= end

    def is_future(self, doc_date: Optional[str]) -> bool:
        if not doc_date:
            return False
        end_window = (date.fromisoformat(self.cutoff) +
                      timedelta(days=365)).isoformat()  # arbitrary far future
        return doc_date > end_window


def paper_evidence_date(p: Paper) -> Optional[str]:
    return p.publication_date


def patent_evidence_date(p: Patent) -> Optional[str]:
    """The date the invention became *available as evidence*.

    For prior-art purposes, priority_date governs. For "did this document
    exist publicly at cutoff", publication_date governs. We use the earlier
    of the two for evidence availability — conservative (favor eligibility).
    """
    candidates = [d for d in (p.priority_date, p.publication_date) if d]
    if not candidates:
        return None
    return min(candidates)


def check_no_future_leakage(papers, patents, cutoff: TemporalCutoff) -> dict:
    """Verify no document is dated on/after the cutoff (would be a leakage)."""
    violations = []
    for p in papers:
        d = paper_evidence_date(p)
        if d and not cutoff.is_eligible_evidence(d):
            violations.append({"id": p.paper_id, "date": d, "kind": "paper"})
    for p in patents:
        d = patent_evidence_date(p)
        if d and not cutoff.is_eligible_evidence(d):
            violations.append({"id": p.patent_id, "date": d, "kind": "patent"})
    return {
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations[:20],
    }
