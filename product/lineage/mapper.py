"""
Invention Lineage Mapper (Phase 3) — Priority 2 of the North-Star directive.

Maps the prerequisite chain of an invention. The directive's example:

    technology A
            ↓
    technology B
            ↓
    technology C
            ↓
    commercial viability

The chain is built from edges of class `requires` / `depends_on` /
`preceded_by` in the civilization graph. Walks backward from a target
node to enumerate every prerequisite (direct and transitive), flags
which prerequisites are themselves missing from the graph, and
classifies each chain step by relationship type so callers can tell
"hard prerequisite" from "soft dependency" from "historical precedent".

Law 8 honesty: this module is *integrated* against the static graph
file. It is not verified for live prediction accuracy. The Law 8
verdict for the system as a whole is in
`evidence/reports/verification_report.json`.
"""

from typing import Dict, Any, List, Optional, Set, Tuple


# Relationship types that constitute a prerequisite chain.
# - requires / depends_on: the source cannot exist without the target.
# - preceded_by: the source historically followed the target; weaker,
#   but still part of the lineage.
PREREQUISITE_RELS = {"requires", "depends_on"}
LINEAGE_RELS = PREREQUISITE_RELS | {"preceded_by"}


class LineageMapper:
    """Maps prerequisite chains in a civilization graph.

    The mapper is graph-agnostic — it accepts a dict in the shape of
    `data/civilization_graph.json` (with `nodes` and `edges` lists).
    This decouples it from the GraphModel adapter, so it can be unit
    tested without loading the full backend.
    """

    def __init__(self, graph: Dict[str, Any]):
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id: Dict[str, Dict[str, Any]] = {n["id"]: n for n in self.nodes}
        # out_edges: source -> list of (target, rel, weight)
        self.out: Dict[str, List[Tuple[str, str, float]]] = {}
        self.inc: Dict[str, List[Tuple[str, str, float]]] = {}
        for e in self.edges:
            src = e.get("source")
            tgt = e.get("target")
            rel = e.get("relationship") or e.get("rel", "depends_on")
            w = float(e.get("weight", 1.0))
            if src is None or tgt is None:
                continue
            self.out.setdefault(src, []).append((tgt, rel, w))
            self.inc.setdefault(tgt, []).append((src, rel, w))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prerequisite_chain(self, target_id: str,
                           max_depth: int = 8) -> Dict[str, Any]:
        """Walk backward from `target_id`, collecting every prerequisite.

        Returns a tree-shaped structure where each node has:
          - id, label, type, domain
          - prerequisites: list of {node, weight, depth} dicts
          - missing: bool — True if the prerequisite id is not in the graph

        The walk is depth-bounded to avoid runaway recursion on cyclic
        graphs; cycles are broken by tracking visited ids per-path.
        """
        if target_id not in self.by_id:
            return {
                "target_id": target_id,
                "error": f"node {target_id} not in graph",
                "prerequisites": [],
            }
        visited: Set[str] = set()
        tree = self._walk_prereqs(target_id, depth=0, max_depth=max_depth,
                                   visited=visited)
        # Also collect the flat chain for callers that don't want a tree.
        flat = self._flatten_chain(tree)
        # Classify the chain by relationship type.
        classification = self._classify_chain(flat)
        # Identify missing prerequisites (ids referenced as targets but
        # not present as nodes).
        missing = [p for p in flat if p.get("missing")]
        return {
            "target_id": target_id,
            "target_label": self.by_id[target_id].get("label", target_id),
            "target_type": self.by_id[target_id].get("type"),
            "prerequisite_tree": tree,
            "flat_chain": flat,
            "missing_prerequisites": missing,
            "chain_depth": max((p["depth"] for p in flat), default=0),
            "classification": classification,
        }

    def commercial_viability_chain(self, target_id: str,
                                    max_depth: int = 8) -> Dict[str, Any]:
        """Like prerequisite_chain, but annotates the target as
        'commercial_viability' if the target itself is an industry or
        system node — i.e., the chain represents a path from raw
        prerequisites up to commercial viability:

            technology A -> technology B -> technology C -> commercial viability
        """
        chain = self.prerequisite_chain(target_id, max_depth=max_depth)
        # The target is the FIRST item in the flat chain (depth 0).
        if chain.get("flat_chain"):
            target_entry = chain["flat_chain"][0]
            if target_entry.get("type") in ("industry", "system"):
                target_entry["commercial_viability"] = True
                chain["commercial_viability_target"] = target_entry["id"]
        return chain

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _walk_prereqs(self, node_id: str, depth: int, max_depth: int,
                      visited: Set[str]) -> Dict[str, Any]:
        node = self.by_id.get(node_id, {"id": node_id, "label": node_id,
                                        "type": "unknown"})
        result = {
            "id": node_id,
            "label": node.get("label", node_id),
            "type": node.get("type", "unknown"),
            "domain": node.get("domain"),
            "depth": depth,
            "prerequisites": [],
        }
        if depth >= max_depth:
            return result
        if node_id in visited:
            result["cycle"] = True
            return result
        visited = visited | {node_id}
        # Look at edges where node_id is the source and the rel is a
        # prerequisite type — these are the things node_id depends on.
        for tgt, rel, weight in self.out.get(node_id, []):
            if rel not in PREREQUISISITE_RELS_CHECK(rel):
                continue
            missing = tgt not in self.by_id
            child = self._walk_prereqs(tgt, depth + 1, max_depth, visited)
            child["relationship"] = rel
            child["weight"] = weight
            child["missing"] = missing
            result["prerequisites"].append(child)
        return result

    def _flatten_chain(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """DFS flatten of the prerequisite tree. Each entry carries its
        depth and relationship to its parent."""
        flat: List[Dict[str, Any]] = []
        def _walk(node: Dict[str, Any], parent_depth: int):
            entry = {
                "id": node["id"],
                "label": node.get("label", node["id"]),
                "type": node.get("type", "unknown"),
                "domain": node.get("domain"),
                "depth": node.get("depth", 0),
                "relationship": node.get("relationship"),
                "weight": node.get("weight", 1.0),
                "missing": node.get("missing", False),
            }
            flat.append(entry)
            for child in node.get("prerequisites", []):
                _walk(child, node.get("depth", 0))
        _walk(tree, 0)
        return flat

    def _classify_chain(self, flat: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count chain hops by relationship type. Useful for telling
        'hard prereq chain' from 'historical lineage' at a glance."""
        counts: Dict[str, int] = {}
        for p in flat:
            rel = p.get("relationship") or "root"
            counts[rel] = counts.get(rel, 0) + 1
        return counts


# Trampoline to keep the helper name short and readable inside _walk_prereqs.
def PREREQUISISITE_RELS_CHECK(rel: str) -> Set[str]:
    """Return the set of relationship types that count as prerequisite
    edges for the chain walk. Isolated as a function so the test suite
    can monkey-patch it without rebuilding the mapper."""
    return PREREQUISITE_RELS


# Backwards-compat shim: the original module exposed a top-level
# `map_lineage(invention_id, graph)` function. Keep it so any existing
# caller keeps working, but route it through the new mapper.
def map_lineage(invention_id: str, graph: Dict[str, Any]) -> Dict[str, Any]:
    """Backwards-compatible entry point. Returns the prerequisite
    chain for `invention_id` in `graph`."""
    return LineageMapper(graph).prerequisite_chain(invention_id)
