"""M03 — Patent -> Science Gap.

A patent claims a capability (material+process achieving a property) but no
scientific paper in the same (domain, mechanism, material) cell subsequently
publishes an independent verification. The intersection: the patent teaches
the result; the science corpus is silent (no replication, no refutation).

Prediction: a future paper will publish on the same (domain, mechanism,
material) cell, either confirming or refuting the patent claim.
"""
from __future__ import annotations
from typing import Iterable
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class PatentScienceGap(MotifDetector):
    name = "m03_patent_science_gap"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        from collections import defaultdict
        paper_by_dom_mech: dict[tuple[str, str], list[str]] = defaultdict(list)
        paper_by_dom_mech_mat: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        for pid, p in graph.papers.items():
            for m in p.mechanisms:
                paper_by_dom_mech[(p.domain, m)].append(pid)
                for mat in p.materials:
                    paper_by_dom_mech_mat[(p.domain, m, mat)].append(pid)

        for pat_id, pat in graph.patents.items():
            pd = pat.priority_date or pat.publication_date
            if not pd or pd >= cutoff:
                continue
            # Require the patent has at least one claim
            if not pat.claims:
                continue
            for mech in pat.mechanisms:
                for mat in pat.materials:
                    # There must be science activity in the (domain, mech) cell
                    cell_papers = paper_by_dom_mech.get((pat.domain, mech), [])
                    if not cell_papers:
                        continue
                    # But no later paper addresses the specific (domain, mech, mat)
                    later_papers = [pid for pid in paper_by_dom_mech_mat.get((pat.domain, mech, mat), [])
                                    if graph.papers[pid].publication_date
                                    and graph.papers[pid].publication_date > pd]
                    if later_papers:
                        continue
                    out.append(self._make_candidate(
                        candidate_id=f"{self.name}:{pat_id}:{mech}:{mat}",
                        domain=pat.domain,
                        node_ids=(pat_id,),
                        supporting_edge_summary=(
                            f"Patent {pat_id} (priority {pd}) claims ({mech}, {mat}) "
                            f"in domain '{pat.domain}'; {len(cell_papers)} papers exist in the "
                            f"({pat.domain}, {mech}) cell but none published after the patent "
                            f"addresses material '{mat}'."
                        ),
                        candidate_claim_text=(
                            f"A scientific paper published after {pd} will address the cell "
                            f"(domain={pat.domain}, mechanism={mech}, material={mat})."
                        ),
                        structured_claim=(mat, "addressed_in_future_paper", pat_id, mech, False),
                        prediction_window_days=730,
                    ))
        return out
