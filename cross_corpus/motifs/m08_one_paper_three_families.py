"""M08 – One Paper + Three Patent Families.

A single paper reports a mechanism on one material. Three independent patent
families (no family cross-citation) each claim a *different* material variant.
The intersection: the three patents' divergence from the paper is unexplained.

Structural signature: for each (domain, mech) cell, if there is exactly 1
paper (or a small number) AND >=3 families with distinct materials, emit ONE
candidate per paper.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class OnePaperThreeFamilies(MotifDetector):
    name = "m08_one_paper_three_families"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        from collections import defaultdict
        papers_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for pid, p in graph.papers.items():
            for m in p.mechanisms:
                papers_by_cell[(p.domain, m)].append(pid)

        # Group families by (domain, mech) and collect their materials
        fam_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for fid, fam in graph.families.items():
            for mid in fam.member_patent_ids:
                pat = graph.patents.get(mid)
                if pat:
                    for m in pat.mechanisms:
                        fam_by_cell[(pat.domain, m)].append(fid)

        for (domain, mech), paper_ids in papers_by_cell.items():
            if not paper_ids:
                continue
            fams_in_cell = list(set(fam_by_cell.get((domain, mech), [])))
            if len(fams_in_cell) < 3:
                continue
            # Get distinct materials per family
            fam_mats: dict[str, set[str]] = {}
            for fid in fams_in_cell:
                members = [graph.patents[m] for m in graph.families[fid].member_patent_ids
                           if m in graph.patents]
                mats = set().union(*[set(m.materials) for m in members]) if members else set()
                if mats:
                    fam_mats[fid] = mats
            if len(fam_mats) < 3:
                continue
            # Need >=3 families with DIFFERENT materials
            distinct_fams = []
            seen_mats: set[str] = set()
            for fid in fams_in_cell:
                if fid not in fam_mats:
                    continue
                # family's material must be different from already-chosen
                if fam_mats[fid] & seen_mats:
                    continue
                distinct_fams.append(fid)
                seen_mats |= fam_mats[fid]
                if len(distinct_fams) >= 3:
                    break
            if len(distinct_fams) < 3:
                continue
            for paper_id in paper_ids:
                paper = graph.papers[paper_id]
                out.append(self._make_candidate(
                    candidate_id=f"{self.name}:{domain}:{mech}:{paper_id}",
                    domain=domain,
                    node_ids=(paper_id, distinct_fams[0], distinct_fams[1], distinct_fams[2]),
                    supporting_edge_summary=(
                        f"Paper {paper_id} reports '{mech}' on {paper.materials}; three "
                        f"independent families ({', '.join(distinct_fams[:3])}) each claim a "
                        f"different material variant. Divergence is unexplained."
                    ),
                    candidate_claim_text=(
                        f"A future paper will identify a design rule reconciling the three "
                        f"material variants of '{mech}' in domain '{domain}'."
                    ),
                    structured_claim=(mech, "design_rule_reconciling_three_variants_in_future_paper",
                                      paper_id, domain, False),
                    prediction_window_days=1095,
                ))
        return out
