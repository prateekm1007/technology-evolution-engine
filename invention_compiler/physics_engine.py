"""
Physics Engine — feeds Layer 1 (First-principles analysis).

Extracts physics principles from the civilization graph that are
relevant to the problem's domain. Looks for `principle_*` nodes whose
domain matches the problem's domain, plus their prerequisite chains.

Input contract:
  - problem: dict with `domain` and `constraints`
  - graph: civilization graph (at construction)

Output contract (Layer 1 fragment, `physics` key):
  {
    "principles": [ {id, label, domain, constraints}, ... ],
    "constraint_load": float,
    "evidence": {...},
    "assumptions": [...],
    "falsification_criteria": str
  }
"""
from typing import Dict, Any, List


class PhysicsEngine:
    """Extracts physics principles from the graph for a problem."""

    # Keyword -> graph node-type hint. Used to disambiguate when
    # a node's domain doesn't directly match the problem's domain.
    PHYSICS_KEYWORDS = (
        "force", "energy", "field", "wave", "magnet", "electric",
        "thermodynamic", "fluid", "acoustic", "optic", "electromagnetic",
        "quantum", "mechanic", "inertia", "pressure", "velocity",
    )

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id = {n["id"]: n for n in self.nodes if "id" in n}

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        domain = problem.get("domain")
        # Find principle nodes whose domain matches OR whose label
        # contains a physics keyword.
        principles = []
        for n in self.nodes:
            if n.get("type") != "principle":
                continue
            label = (n.get("label") or "").lower()
            n_domain = n.get("domain")
            matches_domain = (domain is not None and n_domain == domain)
            matches_keyword = any(kw in label for kw in self.PHYSICS_KEYWORDS)
            if matches_domain or matches_keyword:
                principles.append({
                    "id": n["id"],
                    "label": n.get("label"),
                    "domain": n_domain,
                    "constraints": n.get("constraints", []),
                })

        # Constraint load: how binding is this principle set?
        # Computed as: average number of constraints per principle.
        constraint_counts = [len(p["constraints"]) for p in principles]
        avg = (sum(constraint_counts) / len(constraint_counts)
               if constraint_counts else 0.0)

        return {
            "principles": principles,
            "constraint_load": round(avg, 4),
            "evidence": {
                "principles_found": len(principles),
                "domain_filter": domain,
                "keyword_filter": self.PHYSICS_KEYWORDS,
            },
            "assumptions": [
                "Principle nodes in the graph are a representative sample "
                "of physics principles relevant to the problem.",
                "Constraint load is a proxy for technical difficulty, not "
                "a direct measurement.",
            ],
            "falsification_criteria": (
                "If an expert physicist identifies a principle required "
                "for the problem that is not in the graph, this engine "
                "has a coverage gap. The graph must be extended."
            ),
        }
