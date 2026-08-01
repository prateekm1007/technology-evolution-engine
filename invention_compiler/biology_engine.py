"""
Biology Engine — feeds Layer 1 (First-principles analysis).

Extracts biology-relevant nodes (biomaterials, biosensors, biological
processes, biomedical systems) from the civilization graph.
"""
from typing import Dict, Any, List


class BiologyEngine:
    BIOLOGY_KEYWORDS = (
        "bio", "cell", "membrane", "enzyme", "protein", "genetic",
        "genomic", "neural", "tissue", "implant", "medical",
        "diagnostic", "biosensor", "biomaterial", "organic",
    )

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        domain = problem.get("domain")
        nodes = []
        for n in self.nodes:
            label = (n.get("label") or "").lower()
            n_domain = n.get("domain")
            matches_domain = (domain is not None and n_domain == domain)
            matches_keyword = any(kw in label for kw in self.BIOLOGY_KEYWORDS)
            if matches_domain or matches_keyword:
                nodes.append({
                    "id": n["id"],
                    "label": n.get("label"),
                    "type": n.get("type"),
                    "domain": n_domain,
                })
        return {
            "biological_components": nodes,
            "evidence": {
                "nodes_found": len(nodes),
                "domain_filter": domain,
                "keyword_filter": self.BIOLOGY_KEYWORDS,
            },
            "assumptions": [
                "Biological relevance is approximated by keyword match on "
                "node labels. This is a coarse filter.",
            ],
            "falsification_criteria": (
                "If a biological literature search for the problem surfaces "
                "components not present in this engine's output, the "
                "keyword filter is too narrow."
            ),
        }
