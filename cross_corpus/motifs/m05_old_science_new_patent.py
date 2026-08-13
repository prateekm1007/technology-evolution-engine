"""M05 — Old Science -> Later Enabling Patent.

An old scientific paper (priority_date far in past) reports a fundamental
mechanism. Much later, a patent family claims an *enabling* configuration of
that mechanism — turning the science into a technology. The intersection:
the patent enables what the science only described.

Prediction: a follow-on patent will appear extending the enabling configuration
to a new material in the same mechanism class.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class OldScienceNewPatent(MotifDetector):
    name = "m05_old_science_new_patent"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        from datetime import date
        from collections import defaultdict
        # Index papers by (domain, mech)
        papers_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for pid, p in graph.papers.items():
            for m in p.mechanisms:
                papers_by_cell[(p.domain, m)].append(pid)

        for pat_id, pat in graph.patents.items():
            pd = pat.priority_date or pat.publication_date
            if not pd or pd >= cutoff:
                continue
            if not pat.claims:
                continue
            pd_date = date.fromisoformat(pd)
            # Find the earliest paper >5 years older in each (domain, mech) cell
            # the patent belongs to. Emit ONE candidate per (patent, mech).
            for mech in pat.mechanisms:
                cell_papers = papers_by_cell.get((pat.domain, mech), [])
                # Find old papers (>5yr) not cited by the patent
                cited = {c.target_id for c in pat.citations}
                old_uncited = []
                for pid in cell_papers:
                    paper = graph.papers[pid]
                    if not paper.publication_date:
                        continue
                    pdate = date.fromisoformat(paper.publication_date)
                    if pdate >= pd_date:
                        continue
                    if (pd_date - pdate).days < 365 * 5:
                        continue
                    if pid in cited:
                        continue
                    old_uncited.append((paper.publication_date, pid))
                if not old_uncited:
                    continue
                # Pick the earliest (most foundational)
                old_uncited.sort()
                foundational_date, foundational_id = old_uncited[0]
                out.append(self._make_candidate(
                    candidate_id=f"{self.name}:{pat_id}:{mech}",
                    domain=pat.domain,
                    node_ids=(foundational_id, pat_id),
                    supporting_edge_summary=(
                        f"Foundational paper {foundational_id} ({foundational_date}) on '{mech}'; "
                        f"enabling patent {pat_id} (priority {pd}) turns it into technology "
                        f"without citing the foundational work. {len(old_uncited)} old papers "
                        f"in the cell are uncited."
                    ),
                    candidate_claim_text=(
                        f"A follow-on patent (priority > {pd}) will extend the enabling "
                        f"configuration of '{mech}' to a new material in domain '{pat.domain}'."
                    ),
                    structured_claim=(mech, "extended_to_new_material_in_future_patent",
                                      pat_id, pat.domain, False),
                    prediction_window_days=1095,
                ))
        return out
