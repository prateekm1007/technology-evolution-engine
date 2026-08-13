"""M06 – Two Papers + Two Patent Families.

Two papers in different (sub-)domains report the same mechanism achieving a
similar property; two patent families (one in each domain) independently claim
the same. The intersection: the convergence is unexplained — neither paper
cites the other, neither patent family cites the other. The latent hypothesis:
a *third* configuration combining both will appear.

Prediction: a future document (paper or patent) will combine the two
configurations.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class TwoPapersTwoFamilies(MotifDetector):
    name = "m06_two_papers_two_families"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        from collections import defaultdict
        # Index by (domain, mech) so convergence is cross-domain on the SAME mech
        fam_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for fid, fam in graph.families.items():
            for mid in fam.member_patent_ids:
                pat = graph.patents.get(mid)
                if pat:
                    for m in pat.mechanisms:
                        fam_by_cell[(pat.domain, m)].append(fid)
        paper_by_cell: dict[tuple[str, str], list[str]] = defaultdict(list)
        for pid, p in graph.papers.items():
            for m in p.mechanisms:
                paper_by_cell[(p.domain, m)].append(pid)

        # Find mechanisms that appear in >=2 different domains (cross-domain convergence)
        mechs_to_domains: dict[str, set[str]] = defaultdict(set)
        for (domain, mech) in paper_by_cell:
            if paper_by_cell[(domain, mech)]:
                mechs_to_domains[mech].add(domain)
        for (domain, mech) in fam_by_cell:
            if fam_by_cell[(domain, mech)]:
                mechs_to_domains[mech].add(domain)

        for mech, domains in mechs_to_domains.items():
            if len(domains) < 2:
                continue
            domain_list = sorted(domains)
            # For each pair of domains, pick one paper and one family from each
            for i in range(len(domain_list)):
                for j in range(i + 1, len(domain_list)):
                    d1, d2 = domain_list[i], domain_list[j]
                    p1_list = paper_by_cell.get((d1, mech), [])
                    p2_list = paper_by_cell.get((d2, mech), [])
                    f1_list = fam_by_cell.get((d1, mech), [])
                    f2_list = fam_by_cell.get((d2, mech), [])
                    if not (p1_list and p2_list and f1_list and f2_list):
                        continue
                    # Pick one of each (earliest)
                    p1 = min(p1_list, key=lambda pid: graph.papers[pid].publication_date or "9999")
                    p2 = min(p2_list, key=lambda pid: graph.papers[pid].publication_date or "9999")
                    f1 = f1_list[0]
                    f2 = f2_list[0]
                    # Check papers don't cite each other
                    pp1 = graph.papers[p1]; pp2 = graph.papers[p2]
                    if any(c.target_id == p2 for c in pp1.citations) or \
                       any(c.target_id == p1 for c in pp2.citations):
                        continue
                    out.append(self._make_candidate(
                        candidate_id=f"{self.name}:{mech}:{d1}:{d2}",
                        domain=d1,
                        node_ids=(p1, p2, f1, f2),
                        supporting_edge_summary=(
                            f"Two papers ({p1} in {d1}, {p2} in {d2}) on '{mech}' "
                            f"and two patent families ({f1}, {f2}) independently claim it; "
                            f"no cross-citation. Cross-domain convergence is unexplained."
                        ),
                        candidate_claim_text=(
                            f"A future document will combine the {d1} and {d2} "
                            f"configurations of '{mech}'."
                        ),
                        structured_claim=(mech, "combined_cross_domain_in_future_document",
                                          f"{p1}+{p2}", f"{f1}+{f2}", False),
                        prediction_window_days=1095,
                    ))
        return out
