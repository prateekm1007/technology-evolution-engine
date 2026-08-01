"""
Dependency Module — feeds Layer 2 (Dependency graph).

Per CTO review #2 (commit `02d7658`), upgraded from "connections" to
"causal relationships". The module now classifies each prerequisite
edge as:

  - necessary: the target cannot exist without this prerequisite.
  - sufficient: this prerequisite alone enables the target (rare).
  - contributing: this prerequisite helps but is not strictly required.
  - unknown: the graph doesn't carry enough information to classify.

And it supports counterfactual analysis: "if prerequisite X were
absent, would the target still be viable?" — answered by simulating
the removal of X from the prerequisite chain and checking if the
remaining prerequisites still cover the target's constraints.

Wraps the existing LineageMapper for the structural walk; adds the
causal layer on top.
"""
from typing import Dict, Any, List, Set
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from product.lineage.mapper import LineageMapper


class DependencyModule:
    """Walks the prerequisite chain and classifies edges causally."""

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.mapper = LineageMapper(graph)
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id = {n["id"]: n for n in self.nodes if "id" in n}

    # ------------------------------------------------------------------
    # Causal classification
    # ------------------------------------------------------------------

    def _classify_edge_causally(self, source: str, target: str,
                                 rel: str) -> str:
        """Classify the edge source->target as necessary / sufficient /
        contributing / unknown based on the graph structure.

        Heuristic:
          - If target has only ONE prerequisite (this source), it's NECESSARY.
          - If source's `type` is `principle` or `process`, it's NECESSARY
            (you can't have a system without its underlying principle).
          - If source's `type` is `component` and there are multiple
            components, each is CONTRIBUTING (one can be substituted).
          - If `relationship` is `requires` (strong), lean necessary.
          - If `relationship` is `depends_on` (weaker), lean contributing.
          - Otherwise UNKNOWN.
        """
        # Count the target's prerequisites.
        prereqs_of_target = [
            e for e in self.edges
            if e.get("target") == target
            and (e.get("relationship") in ("requires", "depends_on"))
        ]
        source_node = self.by_id.get(source, {})
        source_type = source_node.get("type", "")

        if rel == "requires":
            if len(prereqs_of_target) == 1:
                return "necessary"
            if source_type in ("principle", "process"):
                return "necessary"
            return "contributing"
        elif rel == "depends_on":
            if source_type in ("principle", "process"):
                return "necessary"
            return "contributing"
        elif rel == "preceded_by":
            return "contributing"  # historical, not causal-necessary
        return "unknown"

    # ------------------------------------------------------------------
    # Counterfactual analysis
    # ------------------------------------------------------------------

    def _counterfactual(self, target_id: str,
                         prereqs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """For each prerequisite, ask: if this prereq were absent, would
        the target still have its constraints covered?

        We approximate "constraints covered" by checking if any OTHER
        prerequisite in the chain carries the same constraint keywords.
        If yes, the removed prereq was CONTRIBUTING. If no, it was
        NECESSARY.
        """
        # Collect all constraints across all prereqs.
        all_constraints: Dict[str, List[str]] = {}
        for p in prereqs:
            for c in (p.get("constraints") or []):
                ck = str(c).lower()
                all_constraints.setdefault(ck, []).append(p["id"])

        results = []
        for p in prereqs:
            removed_id = p["id"]
            removed_constraints = [str(c).lower() for c in (p.get("constraints") or [])]
            # For each of this prereq's constraints, is there another
            # prereq that also carries it?
            uncovered = []
            for c in removed_constraints:
                others = [pid for pid in all_constraints.get(c, [])
                          if pid != removed_id]
                if not others:
                    uncovered.append(c)
            if uncovered:
                impact = "necessary_for_constraints"
                removed_constraints_block = uncovered
            else:
                impact = "substitutable"
                removed_constraints_block = []
            results.append({
                "prerequisite_id": removed_id,
                "prerequisite_label": p.get("label", removed_id),
                "removal_impact": impact,
                "constraints_lost_if_removed": removed_constraints_block,
                "what_changed": (
                    f"If prerequisite '{p.get('label', removed_id)}' were "
                    f"absent, the target would lose coverage for "
                    f"{len(removed_constraints_block)} constraint(s): "
                    f"{removed_constraints_block}."
                ),
                "predicted_outcome_if_changed": (
                    "target_viable" if impact == "substitutable"
                    else "target_not_viable"
                ),
            })
        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, problem: Dict[str, Any],
                target_node_id: str = None) -> Dict[str, Any]:
        if target_node_id is None:
            target_node_id = self._pick_target(problem)
        if target_node_id is None:
            return self._empty_layer2(reason="no target node found")

        chain = self.mapper.prerequisite_chain(target_node_id)
        flat = chain.get("flat_chain", [])
        prereqs = [p for p in flat if p.get("depth", 0) > 0]

        # Add causal classification to each prereq.
        for p in prereqs:
            p["causal_classification"] = self._classify_edge_causally(
                source=p["id"],
                target=target_id if (target_id := p.get("id")) else target_node_id,
                rel=p.get("relationship") or "depends_on",
            )

        # Counterfactual analysis.
        counterfactual = self._counterfactual(target_node_id, prereqs)

        required_materials = [p for p in prereqs if p.get("type") == "component"]
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

        adjacent = self._adjacent_nodes(target_node_id)

        return {
            "prerequisites": prereqs,
            "adjacent_technologies": adjacent,
            "required_materials": required_materials,
            "required_infrastructure": required_infrastructure,
            "missing_capabilities": missing,
            "regulatory_constraints": regulatory,
            "counterfactual_analysis": counterfactual,
            "evidence": {
                "target_node_id": target_node_id,
                "chain_depth": chain.get("chain_depth", 0),
                "prerequisite_count": len(prereqs),
                "missing_count": len(missing),
                "classification": chain.get("classification", {}),
                "causal_classifications": {
                    "necessary": sum(1 for p in prereqs
                                     if p["causal_classification"] == "necessary"),
                    "sufficient": sum(1 for p in prereqs
                                      if p["causal_classification"] == "sufficient"),
                    "contributing": sum(1 for p in prereqs
                                        if p["causal_classification"] == "contributing"),
                    "unknown": sum(1 for p in prereqs
                                   if p["causal_classification"] == "unknown"),
                },
            },
            "assumptions": [
                "Causal classification is heuristic: principle/process prereqs "
                "are 'necessary'; component prereqs are 'contributing' if "
                "multiple exist. This is a prior; real causal analysis "
                "requires domain expertise.",
                "Counterfactual analysis approximates 'viability' by checking "
                "constraint coverage: if removing a prereq leaves some "
                "constraint uncovered by any other prereq, the removed "
                "prereq was necessary. This is a proxy for true viability.",
            ],
            "falsification_criteria": (
                "If an expert identifies a prerequisite as necessary that "
                "this engine classified as contributing (or vice versa), "
                "the causal-classification heuristic is wrong for that edge "
                "type."
            ),
        }

    def _pick_target(self, problem: Dict[str, Any]) -> str:
        domain = problem.get("domain")
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system" and n.get("domain") == domain:
                return n["id"]
        for n in self.graph.get("nodes", []):
            if n.get("type") == "system":
                return n["id"]
        for n in self.graph.get("nodes", []):
            if n.get("domain") == domain:
                return n["id"]
        return None

    def _adjacent_nodes(self, target_id: str) -> List[Dict[str, Any]]:
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
            "counterfactual_analysis": [],
            "evidence": {"reason": reason},
            "assumptions": [],
            "falsification_criteria": "N/A — no target identified.",
        }
