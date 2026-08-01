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
        # GAP 2+7 FIX: track target selection metadata for the evidence block.
        self._last_target_selection = {
            "method": "not_run",
            "relevance_score": 0.0,
            "novel_relative_to_graph": False,
        }

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
        # A1 FIX (per external auditor): was e.get("target") == target,
        # which counts edges WHERE target IS THE TARGET of the edge.
        # But prerequisite edges go FROM target TO its prereqs:
        #   source=target_node, target=prereq_node
        # So we should count the target's OUTGOING prereq edges:
        #   e.get("source") == target
        prereqs_of_target = [
            e for e in self.edges
            if e.get("source") == target
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
        # A1 FIX (per external auditor): the walrus operator was
        # setting target to the PREREQUISITE's id, not the TARGET
        # node's id. This caused _classify_edge_causally to count
        # the prereq's incoming edges instead of the target's
        # outgoing prerequisite edges.
        for p in prereqs:
            p["causal_classification"] = self._classify_edge_causally(
                source=p["id"],
                target=target_node_id,  # FIXED: was target_id if (target_id := p.get("id")) else target_node_id
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
                # GAP 2+7 FIX: expose target selection metadata so the
                # relevance-scored selection is auditable.
                "target_selection": self._last_target_selection,
                "novel_relative_to_graph": self._last_target_selection.get(
                    "novel_relative_to_graph", False),
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
        """GAP 2+7 FIX: problem-aware relevance-scored target selection.

        Before the fix, this method picked the first system node in the
        matching domain, or the first system node period. This was
        arbitrary for novel inventions not in the civilization_graph.
        Worse, system nodes in this graph have NO prerequisites, so the
        causal classifications were always all-zero (Gap 7).

        The fix scores every node in the graph by relevance to the
        problem AND by whether the node has prerequisites:
          - domain match (highest weight: 3 points)
          - constraint keyword overlap (medium weight: 1 point per match)
          - problem-text keyword overlap (low weight: 0.5 points per match)
          - node type preference (system > industry > component: 2/1/0.5)
          - HAS PREREQUISITES bonus (NEW: +2.0 if the node has prereqs)
            This is the key Gap 7 fix: prefer nodes with prereqs so the
            causal classification has something to classify.

        Returns the highest-scoring node id. If the highest score is
        below a threshold (1.0), the invention is "novel relative to
        the graph" — this is informative, not a failure.
        """
        domain = problem.get("domain", "")
        problem_text = (problem.get("problem") or "").lower()
        constraints = [str(c).lower() for c in problem.get("constraints", [])]

        # Pre-compute which nodes have prerequisites (Gap 7 fix).
        # A node "has prerequisites" if it is the SOURCE of a
        # requires/depends_on edge (i.e., the node depends on something
        # else). The LineageMapper walks these outgoing edges.
        nodes_with_prereqs = set()
        for e in self.edges:
            if e.get("relationship") in ("requires", "depends_on"):
                nodes_with_prereqs.add(e.get("source"))

        # Keyword sets for matching against node labels.
        problem_keywords = set(
            w for w in problem_text.replace(",", " ").replace(".", " ").split()
            if len(w) > 3
        )
        constraint_keywords = set()
        for c in constraints:
            constraint_keywords.update(
                w for w in c.replace("_", " ").split() if len(w) > 2
            )

        best_id = None
        best_score = 0.0
        for n in self.nodes:
            score = 0.0
            n_domain = n.get("domain", "")
            n_label = (n.get("label") or "").lower()
            n_type = n.get("type", "")
            n_id = n.get("id", "").lower()

            # Domain match (highest weight).
            if domain and n_domain == domain:
                score += 3.0

            # Constraint keyword overlap (medium weight).
            for kw in constraint_keywords:
                if kw in n_label or kw in n_id:
                    score += 1.0

            # Problem-text keyword overlap (low weight).
            for kw in problem_keywords:
                if kw in n_label or kw in n_id:
                    score += 0.5

            # Node type preference: prefer nodes that are specific
            # enough to have prerequisites. System nodes get a type
            # bonus but DON'T have prerequisites in this graph, so the
            # has-prereqs bonus (below) is what differentiates.
            type_bonus = {"system": 2.0, "industry": 1.5,
                          "subdomain": 1.5, "component": 1.0,
                          "process": 1.0, "principle": 0.5}.get(n_type, 0.0)
            score += type_bonus

            # GAP 7 FIX: prefer nodes that HAVE prerequisites. This is
            # the key fix: without this bonus, the system picks nodes
            # with no prereqs, and the causal classification is all-zero.
            if n.get("id") in nodes_with_prereqs:
                score += 2.0

            if score > best_score:
                best_score = score
                best_id = n.get("id")

        # Determine selection method and novelty.
        if best_score >= 5.0:
            method = "relevance_scored_domain_match_with_prereqs"
            novel = False
        elif best_score >= 3.0:
            method = "relevance_scored_domain_match"
            novel = False
        elif best_score >= 1.0:
            method = "relevance_scored_keyword_match"
            novel = False
        elif best_id is not None:
            method = "relevance_scored_low_confidence"
            novel = True
        else:
            method = "no_target_found"
            novel = True

        self._last_target_selection = {
            "method": method,
            "relevance_score": round(best_score, 4),
            "novel_relative_to_graph": novel,
            "threshold_for_confident_match": 5.0,
            "threshold_for_domain_match": 3.0,
            "threshold_for_any_match": 1.0,
            "has_prerequisites_bonus": 2.0,
        }
        return best_id

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
