"""M04 — Paper Failure -> Patent Workaround.

A scientific paper reports a FAILURE (reports_failures field) of a specific
material/mechanism combination. A later patent in the same cell claims to
achieve the property the paper failed at, but does not cite the paper (no
acknowledgment of the failure). The intersection: the patent's claim is
in tension with the paper's failure report.

Prediction: a future paper will either (a) replicate the patent's claimed
workaround, or (b) report that the workaround also fails.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class PaperFailurePatentWorkaround(MotifDetector):
    name = "m04_paper_failure_patent_workaround"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        for paper_id, paper in graph.papers.items():
            if not paper.reported_failures:
                continue
            if not paper.publication_date or paper.publication_date >= cutoff:
                continue
            for pat_id, pat in graph.patents.items():
                pd = pat.priority_date or pat.publication_date
                if not pd or pd <= paper.publication_date:
                    continue
                shared_mech = set(paper.mechanisms) & set(pat.mechanisms)
                shared_mat = set(paper.materials) & set(pat.materials)
                if not (shared_mech and shared_mat):
                    continue
                # Check the patent does NOT cite the paper
                cites_paper = any(c.target_id == paper_id for c in pat.citations)
                if cites_paper:
                    continue
                mech = sorted(shared_mech)[0]
                mat = sorted(shared_mat)[0]
                out.append(self._make_candidate(
                    candidate_id=f"{self.name}:{paper_id}:{pat_id}",
                    domain=paper.domain,
                    node_ids=(paper_id, pat_id),
                    supporting_edge_summary=(
                        f"Paper {paper_id} ({paper.publication_date}) reports failure of "
                        f"({mech}, {mat}); patent {pat_id} (priority {pd}) claims to achieve "
                        f"the same cell but does not cite the failure report."
                    ),
                    candidate_claim_text=(
                        f"A future paper will either replicate the patent {pat_id} workaround "
                        f"for ({mech}, {mat}) or report that the workaround also fails."
                    ),
                    structured_claim=(mat, "workaround_replicated_or_fails_in_future_paper",
                                      pat_id, mech, False),
                    prediction_window_days=730,
                ))
        return out
