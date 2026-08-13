"""M09 – Jurisdictional Divergence.

The same DOCDB patent family is granted in jurisdiction A with claim set X
but rejected/limited in jurisdiction B (proxy: family has members in A and B
but B-member has fewer/smaller claims, or B-member was withdrawn). The
intersection: the divergence reflects an unexplained jurisdiction-specific
constraint.

Prediction: a future paper will articulate the technical reason for the
jurisdictional divergence.
"""
from __future__ import annotations
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class JurisdictionalDivergence(MotifDetector):
    name = "m09_jurisdictional_divergence"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        for fid, fam in graph.families.items():
            if len(fam.jurisdictions) < 2:
                continue
            members = [graph.patents[mid] for mid in fam.member_patent_ids
                       if mid in graph.patents]
            if len(members) < 2:
                continue
            # Find members with divergent claim counts (proxy for divergence)
            claim_counts = sorted([(len(m.claims), m.patent_id, m.jurisdictions) for m in members])
            if claim_counts[-1][0] - claim_counts[0][0] < 2:
                continue  # not divergent enough
            small = claim_counts[0]
            big = claim_counts[-1]
            out.append(self._make_candidate(
                candidate_id=f"{self.name}:{fid}",
                domain=fam.domain,
                node_ids=(fid, small[1], big[1]),
                supporting_edge_summary=(
                    f"Family {fid} granted in {big[2]} with {big[0]} claims but "
                    f"limited/withdrawn in {small[2]} with {small[0]} claims. "
                    f"Divergence is unexplained."
                ),
                candidate_claim_text=(
                    f"A future paper will articulate the technical reason for the jurisdictional "
                    f"divergence in family {fid}."
                ),
                structured_claim=(fid, "jurisdictional_divergence_explained_in_future_paper",
                                  small[1], big[1], False),
                prediction_window_days=1095,
            ))
        return out
