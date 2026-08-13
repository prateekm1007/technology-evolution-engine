"""M02 — Paper -> Patent Gap.

A scientific paper reports a capability (e.g., a material achieves property X
at value Y) but no patent family in the same domain+mechanism space claims it.
The intersection: the paper teaches the result; the patent corpus is silent.
The candidate: a future patent will claim exactly this.

Prediction: a patent family with priority_date > paper.publication_date will
appear in the same (domain, mechanism) cell with a claim matching the paper's.
"""
from __future__ import annotations
from typing import Iterable
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class PaperPatentGap(MotifDetector):
    name = "m02_paper_patent_gap"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        # Index patents by (domain, mechanism) and (domain, mechanism, material)
        from collections import defaultdict
        pat_by_dom_mech: dict[tuple[str, str], list[str]] = defaultdict(list)
        pat_by_dom_mech_mat: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        for pid, p in graph.patents.items():
            for m in p.mechanisms:
                pat_by_dom_mech[(p.domain, m)].append(pid)
                for mat in p.materials:
                    pat_by_dom_mech_mat[(p.domain, m, mat)].append(pid)

        for paper_id, paper in graph.papers.items():
            if not paper.publication_date or paper.publication_date >= cutoff:
                continue
            # Require the paper has at least one claim (a real result, not just a mention)
            if not paper.claims:
                continue
            for mech in paper.mechanisms:
                for mat in paper.materials:
                    # There must be patent activity in the (domain, mech) cell
                    # — otherwise the "gap" is trivial (no one is patenting here at all)
                    cell_patents = pat_by_dom_mech.get((paper.domain, mech), [])
                    if not cell_patents:
                        continue
                    # But no later patent claims the specific (domain, mech, mat)
                    later_claiming = []
                    for pid in pat_by_dom_mech_mat.get((paper.domain, mech, mat), []):
                        p = graph.patents[pid]
                        pd = p.priority_date or p.publication_date
                        if pd and pd > paper.publication_date:
                            later_claiming.append(pid)
                    if later_claiming:
                        continue  # gap closed for this material
                    out.append(self._make_candidate(
                        candidate_id=f"{self.name}:{paper_id}:{mech}:{mat}",
                        domain=paper.domain,
                        node_ids=(paper_id,),
                        supporting_edge_summary=(
                            f"Paper {paper_id} ({paper.publication_date}) reports ({mech}, {mat}) "
                            f"in domain '{paper.domain}'; {len(cell_patents)} patents exist in the "
                            f"({paper.domain}, {mech}) cell but none with later priority claims "
                            f"material '{mat}'."
                        ),
                        candidate_claim_text=(
                            f"A patent family with priority_date > {paper.publication_date} will appear "
                            f"in domain '{paper.domain}' claiming ({mech}, {mat})."
                        ),
                        structured_claim=(mat, "appears_in_future_patent", paper_id, mech, False),
                        prediction_window_days=730,
                    ))
        return out
