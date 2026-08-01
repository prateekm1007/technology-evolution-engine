"""
Analogy Engine — feeds Layer 0 (Opportunity definition).

Discovers cross-domain analogies for a given problem. Wraps the
existing CrossDomainSynthesizer (product/discovery/synthesizer.py)
so the compiler gets the benefit of cross-domain pair-finding
without re-implementing it.

Input contract:
  - problem: dict with at least `domain` and `constraints` keys
  - graph: the civilization graph (passed at construction)

Output contract (Layer 0 fragment):
  {
    "analogies": [
      {
        "node_a": {...},
        "node_b": {...},
        "structural_overlap_score": float,
        "evidence": {...}
      }, ...
    ],
    "evidence": {...},
    "assumptions": [...],
    "falsification_criteria": str
  }
"""
from typing import Dict, Any, List
import sys
import pathlib

# Allow imports of product.discovery.synthesizer from the parent package.
_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from product.discovery.synthesizer import CrossDomainSynthesizer


class AnalogyEngine:
    """Finds cross-domain analogies for a problem."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.synth = CrossDomainSynthesizer(graph)

    def find_analogies(self, problem: Dict[str, Any],
                        top_k: int = 5) -> Dict[str, Any]:
        domain = problem.get("domain")
        # If the problem names a domain, scope the search to nodes in
        # that domain; otherwise search the whole graph.
        domain_filter = [domain] if domain else None
        result = self.synth.discover(top_k=top_k,
                                      domain_filter=domain_filter)
        # If the in-domain search found nothing, fall back to the
        # full graph so the compiler always has some analogies to
        # reason about.
        if not result["candidates"] and domain_filter is not None:
            result = self.synth.discover(top_k=top_k)

        return {
            "analogies": result["candidates"],
            "evidence": {
                "total_pairs_evaluated": result["total_pairs_evaluated"],
                "excluded_already_connected": result["excluded_already_connected"],
                "domain_filter_applied": domain_filter,
            },
            "assumptions": [
                "Cross-domain analogies are useful starting points, not "
                "guarantees of feasibility.",
                "Structural overlap (shared prerequisites, shared constraints, "
                "common ancestors) is a proxy for combinability, not a proof "
                "of combinability.",
            ],
            "falsification_criteria": (
                "If, after N verification cycles, candidates surfaced by "
                "this engine fail to produce a viable invention more than "
                "50% of the time, the structural-overlap prior is wrong and "
                "must be recalibrated. N >= 20 cycles is the minimum "
                "sample size."
            ),
        }
