"""M07 – Three Papers + One Patent.

Three independent papers (no cross-citations) report the same mechanism
across three different materials in the same domain. A single patent claims
a *fourth* material configuration using the same mechanism. The intersection:
the patent's choice of fourth material is not explained by the three papers;
the latent hypothesis is that a *fifth* material in the same series will appear.

Structural signature (not exhaustive combination): for each (domain, mechanism)
cell, find the set of papers with distinct materials. If >=3 such papers exist
(with no cross-citations among them) AND >=1 patent in the cell claims a
different material, emit ONE candidate per (cell, patent).
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class ThreePapersOnePatent(MotifDetector):
    name = "m07_three_papers_one_patent"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        from collections import defaultdict
        papers_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for pid, p in graph.papers.items():
            for m in p.mechanisms:
                papers_by_cell[(p.domain, m)].append(pid)
        patents_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for pid, p in graph.patents.items():
            for m in p.mechanisms:
                patents_by_cell[(p.domain, m)].append(pid)

        for (domain, mech), paper_ids in papers_by_cell.items():
            if len(paper_ids) < 3:
                continue
            # Group papers by their material set; pick one representative per
            # distinct material so we get "3 papers with 3 different materials".
            by_mat: dict[str, list[str]] = defaultdict(list)
            for pid in paper_ids:
                p = graph.papers[pid]
                for mat in p.materials:
                    by_mat[mat].append(pid)
            distinct_mats = [m for m, lst in by_mat.items() if lst]
            if len(distinct_mats) < 3:
                continue
            # Pick one paper per material (the earliest)
            distinct_mats_sorted = sorted(distinct_mats,
                                          key=lambda m: min(graph.papers[p].publication_date or "9999"
                                                            for p in by_mat[m]))
            chosen = []
            for m in distinct_mats_sorted[:5]:  # cap at 5 materials
                # earliest paper for this material
                rep = min(by_mat[m], key=lambda pid: graph.papers[pid].publication_date or "9999")
                chosen.append((m, rep))
            if len(chosen) < 3:
                continue
            # Check independence: no cross-citations among the chosen papers
            chosen_ids = {pid for _, pid in chosen}
            independent = True
            for _, pid in chosen:
                p = graph.papers[pid]
                if any(c.target_id in chosen_ids and c.target_id != pid for c in p.citations):
                    independent = False
                    break
            if not independent:
                continue
            # Patents in the same cell with a DIFFERENT material from the chosen 3
            chosen_mats = {m for m, _ in chosen[:3]}
            cell_patents = patents_by_cell.get((domain, mech), [])
            for pat_id in cell_patents:
                pat = graph.patents[pat_id]
                pat_mats = set(pat.materials)
                if pat_mats & chosen_mats:
                    continue  # patent uses one of the already-studied materials
                if not pat_mats:
                    continue
                node_ids = tuple([pid for _, pid in chosen[:3]] + [pat_id])
                out.append(self._make_candidate(
                    candidate_id=f"{self.name}:{domain}:{mech}:{pat_id}",
                    domain=domain,
                    node_ids=node_ids,
                    supporting_edge_summary=(
                        f"Three independent papers ({', '.join(pid for _, pid in chosen[:3])}) "
                        f"on '{mech}' across materials {sorted(chosen_mats)}; "
                        f"patent {pat_id} claims a fourth material {sorted(pat_mats)}. "
                        f"A fifth material is latent."
                    ),
                    candidate_claim_text=(
                        f"A future document will report '{mech}' on a fifth material in "
                        f"the same series in domain '{domain}'."
                    ),
                    structured_claim=(mech, "appears_on_fifth_material_in_future_document",
                                      pat_id, domain, False),
                    prediction_window_days=1095,
                ))
        return out
