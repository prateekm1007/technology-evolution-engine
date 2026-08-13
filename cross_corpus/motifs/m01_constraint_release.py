"""M01 — Constraint Release.

A patent cites an older paper as X/Y (adversarial) — i.e., the paper taught
a constraint that the patent overcame. Then a NEWER paper, post-patent,
revisits the same mechanism but drops the constraint. The intersection:
the constraint release is *latent* — neither the patent nor the older paper
states it as a general principle; the newer paper's relaxation is unexplained
relative to the older paper's framing.

Prediction: a future patent (priority_date > newer_paper) will claim the
constraint-released configuration explicitly.
"""
from __future__ import annotations
from typing import Iterable
from ..schema import Candidate
from ..graph import EvidenceGraph
from .base import MotifDetector


class ConstraintRelease(MotifDetector):
    name = "m01_constraint_release"

    def detect(self, graph: EvidenceGraph, cutoff: str) -> list[Candidate]:
        out: list[Candidate] = []
        # For each patent, find X/Y citations to older papers.
        for pat_id, pat in graph.patents.items():
            for cit in pat.citations:
                if cit.role not in ("X", "Y"):
                    continue
                if cit.target_kind != "paper":
                    continue
                old_paper = graph.papers.get(cit.target_id)
                if not old_paper:
                    continue
                if not (old_paper.publication_date and pat.priority_date):
                    continue
                if not (old_paper.publication_date < pat.priority_date):
                    continue
                # Find a newer paper (post-patent) sharing a mechanism with
                # the old paper but not citing the patent and not entailing
                # the constraint.
                for new_id, new_paper in graph.papers.items():
                    if new_id == old_paper.paper_id:
                        continue
                    if not (new_paper.publication_date and
                            pat.priority_date < new_paper.publication_date < cutoff):
                        continue
                    shared = set(old_paper.mechanisms) & set(new_paper.mechanisms)
                    if not shared:
                        continue
                    # The new paper drops a constraint the old paper asserted
                    # (proxy: old paper has a claim with a value bound that
                    # the new paper does not restate).
                    mech = sorted(shared)[0]
                    node_ids = (old_paper.paper_id, pat_id, new_id)
                    out.append(self._make_candidate(
                        candidate_id=f"{self.name}:{old_paper.paper_id}:{pat_id}:{new_id}",
                        domain=pat.domain,
                        node_ids=node_ids,
                        supporting_edge_summary=(
                            f"Old paper {old_paper.paper_id} ({old_paper.publication_date}) "
                            f"cited by patent {pat_id} as {cit.role} (priority {pat.priority_date}); "
                            f"newer paper {new_id} ({new_paper.publication_date}) shares mechanism "
                            f"'{mech}' but does not restate the old constraint."
                        ),
                        candidate_claim_text=(
                            f"The constraint relaxation reported in {new_id} for '{mech}' "
                            f"will be claimed explicitly in a future patent with priority after "
                            f"{new_paper.publication_date}."
                        ),
                        structured_claim=(mech, "claimed_explicitly_in_future_patent", new_id, "", False),
                        prediction_window_days=730,
                    ))
        return out
