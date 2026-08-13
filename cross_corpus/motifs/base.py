"""Motif detector base class (Issue #4)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from ..schema import Candidate
from ..graph import EvidenceGraph


class MotifDetector(ABC):
    """A motif detector finds cross-corpus intersection patterns.

    Each detector returns a list of Candidate objects. Detectors must:
      - only use nodes available in the time-anchored subgraph (the caller
        passes the already-frozen subgraph)
      - produce falsifiable, machine-checkable `predicted_outcome`s
      - encode the structured claim as "subject|predicate|obj|value|negated"
        in `predicted_outcome` so the entailed-check can parse it
    """
    name: str = "abstract"

    @abstractmethod
    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        ...

    def _make_candidate(self, *, candidate_id: str, domain: str,
                        node_ids: tuple[str, ...],
                        supporting_edge_summary: str,
                        candidate_claim_text: str,
                        structured_claim: tuple,
                        prediction_window_days: int = 365,
                        generated_at: str = "") -> Candidate:
        subject, predicate, obj, value, negated = structured_claim
        # Pack the structured claim into predicted_outcome for the entailed
        # check to parse. The human-readable falsifiable statement is in
        # candidate_claim_text.
        encoded = f"{subject}|{predicate}|{obj}|{value or ''}|{negated}"
        from datetime import datetime, timezone
        ts = generated_at or datetime.now(timezone.utc).isoformat()
        return Candidate(
            candidate_id=candidate_id,
            motif=self.name,
            domain=domain,
            node_ids=node_ids,
            supporting_edge_summary=supporting_edge_summary,
            candidate_claim_text=candidate_claim_text,
            predicted_outcome=encoded,
            prediction_window_days=prediction_window_days,
            generated_at=ts,
        )
