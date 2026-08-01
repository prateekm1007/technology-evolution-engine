"""
Chemistry Engine — feeds Layer 1 (First-principles analysis).

Extracts chemistry-relevant nodes (materials, polymers, membranes,
catalysts, electrodes, etc.) from the civilization graph.

Input contract: same as PhysicsEngine.
Output contract: Layer 1 fragment, `chemistry` key.
"""
from typing import Dict, Any, List


class ChemistryEngine:
    """Extracts chemistry-relevant nodes for a problem."""

    CHEMISTRY_KEYWORDS = (
        "polymer", "membrane", "catalyst", "electrode", "chemical",
        "molecular", "ionic", "oxidation", "reduction", "electrochem",
        "photochem", "synthesis", "alloy", "ceramic", "composite",
        "semiconductor", "electrolyte", "membrane", "crystal",
    )

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        domain = problem.get("domain")
        nodes = []
        for n in self.nodes:
            label = (n.get("label") or "").lower()
            n_domain = n.get("domain")
            matches_domain = (domain is not None and n_domain == domain)
            matches_keyword = any(kw in label for kw in self.CHEMISTRY_KEYWORDS)
            ntype = n.get("type", "")
            is_material_like = ntype in ("component", "principle", "process")
            if (matches_domain or matches_keyword) and is_material_like:
                nodes.append({
                    "id": n["id"],
                    "label": n.get("label"),
                    "type": ntype,
                    "domain": n_domain,
                    "constraints": n.get("constraints", []),
                })
        return {
            "materials_and_processes": nodes,
            "evidence": {
                "nodes_found": len(nodes),
                "domain_filter": domain,
                "keyword_filter": self.CHEMISTRY_KEYWORDS,
            },
            "assumptions": [
                "Chemistry-relevant nodes are approximated by keyword match "
                "on node labels. This will miss nodes whose chemistry is "
                "implicit in their function.",
            ],
            "falsification_criteria": (
                "If a chemistry literature search for the problem domain "
                "surfaces materials or processes not present in this "
                "engine's output, the keyword filter is too narrow."
            ),
        }
