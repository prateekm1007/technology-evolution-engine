"""M10 – Unexplained Bridge.

A paper and a patent share TWO or more materials/mechanisms/processes but
have NO citation edge in either direction (no paper-cites-patent, no
patent-cites-paper). The intersection: the shared features form an
*unexplained bridge* — neither document acknowledges the other.

Prediction: a future document will close the bridge by citing both.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class UnexplainedBridge(MotifDetector):
    name = "m10_unexplained_bridge"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        # An "unexplained bridge" is surprising only when the paper and patent
        # are in DIFFERENT domains but share features (cross-domain convergence
        # with no citation). Same-domain sharing is expected and not a bridge.
        for paper_id, paper in graph.papers.items():
            if not paper.publication_date or paper.publication_date >= cutoff:
                continue
            paper_feats = set(paper.materials) | set(paper.mechanisms)
            if len(paper_feats) < 2:
                continue
            for pat_id, pat in graph.patents.items():
                if pat.domain == paper.domain:
                    continue  # same-domain sharing is not a bridge
                pat_feats = set(pat.materials) | set(pat.mechanisms)
                shared = paper_feats & pat_feats
                # Require at least 1 shared mechanism AND 1 shared material
                # (cross-domain convergence on both axis is the surprising case)
                shared_mech = set(paper.mechanisms) & set(pat.mechanisms)
                shared_mat = set(paper.materials) & set(pat.materials)
                if not (shared_mech and shared_mat):
                    continue
                # no citation either direction
                if any(c.target_id == pat_id for c in paper.citations):
                    continue
                if any(c.target_id == paper_id for c in pat.citations):
                    continue
                out.append(self._make_candidate(
                    candidate_id=f"{self.name}:{paper_id}:{pat_id}",
                    domain=paper.domain,
                    node_ids=(paper_id, pat_id),
                    supporting_edge_summary=(
                        f"Paper {paper_id} (domain {paper.domain}) and patent {pat_id} "
                        f"(domain {pat.domain}) share mechanism {sorted(shared_mech)} and "
                        f"material {sorted(shared_mat)} across domains, with no citation "
                        f"in either direction."
                    ),
                    candidate_claim_text=(
                        f"A future document will cite both {paper_id} and {pat_id}, closing "
                        f"the cross-domain unexplained bridge."
                    ),
                    structured_claim=(paper_id, "bridged_with_in_future_document",
                                      pat_id, ",".join(sorted(shared)), False),
                    prediction_window_days=730,
                ))
        return out
