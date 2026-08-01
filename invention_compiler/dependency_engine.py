"""
Dependency Engine — feeds Layer 2 (Dependency graph).

Wraps the existing LineageMapper (product/lineage/mapper.py) so the
compiler gets the prerequisite chain without re-implementing it.

Output contract (Layer 2 fragment):
  {
    "prerequisites": [...],            # tree from LineageMapper
    "adjacent_technologies": [...],    # nodes pointing INTO the target
    "required_materials": [...],       # prereqs with type=component
    "required_infrastructure": [...],  # prereqs with type=system/industry
    "missing_capabilities": [...],     # prereq ids NOT in the graph
    "regulatory_constraints": [...],   # prereqs with 'regulation' constraint
  }
"""
from typing import Dict, Any, List
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from product.lineage.mapper import LineageMapper


class DependencyEngine:
    """Walks the prerequisite chain of an invention's target node."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.mapper = LineageMapper(graph)

    def analyze(self, problem: Dict[str, Any],
                target_node_id: str = None) -> Dict[str, Any]:
        """If `target_node_id` is None, pick the first system node in
        the problem's domain."""
        if target_node_id is None:
            target_node_id = self._pick_target(problem)
        if target_node_id is None:
            return self._empty_layer2(reason="no target node found")
        chain = self.mapper.prerequisite_chain(target_node_id)
        flat = chain.get("flat_chain", [])

        # Categorize prerequisites.
        prereqs = [p for p in flat if p.get("depth", 0) > 0]
        required_materials = [
            p for p in prereqs if p.get("type") == "component"
        ]
        required_infrastructure = [
            p for p in prereqs if p.get("type") in ("system", "industry")
        ]
        missing = [
            {"id": p["id"], "label": p.get("label", p["id"]),
             "depth": p.get("depth", 0)}
            for p in prereqs if p.get("missing")
        ]
        regulatory = [
            {"id": p["id"], "label": p.get("label", p["id"]),
             "constraints": [c for c in (p.get("constraints") or [])
                             if "regulation" in str(c).lower() or
                             "safety" in str(c).lower()]}
            for p in prereqs
        ]
        regulatory = [r for r in regulatory if r["constraints"]]

        # Adjacent technologies: nodes pointing INTO the target (the
        # target's "siblings" — things that solve similar problems).
        adjacent = self._adjacent_nodes(target_node_id)

        return {
            "prerequisites": prereqs,
            "adjacent_technologies": adjacent,
            "required_materials": required_materials,
            "required_infrastructure": required_infrastructure,
            "missing_capabilities": missing,
            "regulatory_constraints": regulatory,
            "evidence": {
                "target_node_id": target_node_id,
                "chain_depth": chain.get("chain_depth", 0),
                "prerequisite_count": len(prereqs),
                "missing_count": len(missing),
                "classification": chain.get("classification", {}),
            },
            "assumptions": [
                "The target node is selected by best-effort domain match. "
                "If the problem names a technology not in the graph, this "
                "engine falls back to the first system node it finds.",
                "Adjacent technologies are defined as nodes pointing INTO "
                "the target. This captures 'alternative approaches' but "
                "not 'competitor technologies'.",
            ],
            "falsification_criteria": (
                "If an expert identifies a prerequisite or alternative "
                "approach not in this engine's output, the graph has a "
                "coverage gap or the target selection heuristic is wrong."
            ),
        }

    def _pick_target(self, problem: Dict[str, Any]) -> str:
        domain = problem.get("domain")
        # Prefer system nodes whose domain matches.
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system" and n.get("domain") == domain:
                return n["id"]
        # Fallback: any system node.
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system":
                return n["id"]
        # Last resort: any node with the matching domain.
        for n in self.graph.get("nodes", []):
            if n.get("domain") == domain:
                return n["id"]
        return None

    def _adjacent_nodes(self, target_id: str) -> List[Dict[str, Any]]:
        """Nodes pointing INTO the target — alternative approaches."""
        by_id = {n["id"]: n for n in self.graph.get("nodes", [])}
        adjacent = []
        seen = set()
        for e in self.graph.get("edges", []):
            if e.get("target") == target_id:
                src_id = e.get("source")
                if src_id in by_id and src_id not in seen:
                    n = by_id[src_id]
                    adjacent.append({
                        "id": n["id"],
                        "label": n.get("label"),
                        "type": n.get("type"),
                        "relationship": e.get("relationship"),
                    })
                    seen.add(src_id)
        return adjacent

    def _empty_layer2(self, reason: str) -> Dict[str, Any]:
        return {
            "prerequisites": [],
            "adjacent_technologies": [],
            "required_materials": [],
            "required_infrastructure": [],
            "missing_capabilities": [],
            "regulatory_constraints": [],
            "evidence": {"reason": reason},
            "assumptions": [],
            "falsification_criteria": "N/A — no target identified.",
        }
