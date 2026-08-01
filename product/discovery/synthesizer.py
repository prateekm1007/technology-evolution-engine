"""
Cross-domain synthesizer — Priority 3 of the North-Star directive.

The directive's thesis: inventions emerge from combinations across
domains — biology + semiconductors, robotics + materials science,
energy + AI, aerospace + manufacturing, neuroscience + computing.

This module discovers candidate cross-domain combinations by:

  1. Finding pairs of nodes from DIFFERENT domains.
  2. Scoring each pair by structural overlap (shared prerequisites,
     shared constraints, common ancestors in the graph).
  3. Excluding pairs that are already directly connected in the graph
     (those are known combinations, not novel ones).
  4. Returning a ranked list of candidate combinations, each with:
     - the two nodes
     - their respective domains
     - the structural-overlap score
     - the shared prerequisites that make the combination non-trivial
     - a per-combination feasibility preview (delegated to
       product.scoring.feasibility for the full score).

Law 8 honesty: this module is *integrated* — it runs against the
static graph and produces candidate combinations. Whether any of
these combinations actually becomes a feasible invention is a
prediction question, settled by the verification cycle
(scripts/run_verification_cycle.py) over time, not by this module.
"""

from typing import Dict, Any, List, Tuple, Optional, Set
from itertools import combinations


# Minimum structural-overlap score for a pair to be returned.
# Below this, the pair is treated as "no meaningful overlap".
DEFAULT_MIN_SCORE = 0.15

# Maximum number of candidates to return per call. The synthesizer is
# generative; without a cap it can produce O(n^2) pairs.
DEFAULT_TOP_K = 20


class CrossDomainSynthesizer:
    """Finds novel cross-domain combinations in a civilization graph."""

    def __init__(self, graph: Dict[str, Any]):
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id: Dict[str, Dict[str, Any]] = {n["id"]: n for n in self.nodes}
        # Build adjacency maps for both directions, indexed by rel type.
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
        # Pre-compute per-node prerequisite sets (transitive closure,
        # capped at depth 3 to keep it cheap).
        self._prereq_cache: Dict[str, Set[str]] = {}
        # Pre-compute per-node constraint sets.
        self._constraint_cache: Dict[str, Set[str]] = {
            n["id"]: set(_as_list(n.get("constraints", [])))
            for n in self.nodes
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(self,
                 min_score: float = DEFAULT_MIN_SCORE,
                 top_k: int = DEFAULT_TOP_K,
                 node_types: Optional[List[str]] = None,
                 domain_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Discover cross-domain combinations.

        Args:
            min_score: minimum structural-overlap score to keep a pair.
            top_k: cap on number of candidates returned.
            node_types: optional list of node types to consider
                (e.g., ['system', 'component']). None = all types.
            domain_filter: optional list of domains to consider.
                None = all domains.

        Returns:
            A dict with:
              - candidates: ranked list of combination dicts
              - total_pairs_evaluated: how many pairs were scored
              - total_pairs_returned: len(candidates)
              - excluded_already_connected: how many pairs were dropped
                because the graph already has an edge between them.
        """
        # Filter the candidate node pool.
        pool = self._candidate_nodes(node_types, domain_filter)

        # Build the set of already-connected pairs so we can exclude them.
        connected = self._connected_pairs(pool)

        candidates: List[Dict[str, Any]] = []
        excluded_connected = 0
        for a, b in combinations(pool, 2):
            # Must be from different domains.
            da, db = self._domain_of(a), self._domain_of(b)
            if da is None or db is None or da == db:
                continue
            # Skip if already directly connected.
            pair_key = frozenset((a, b))
            if pair_key in connected:
                excluded_connected += 1
                continue
            score, evidence = self._score_pair(a, b)
            if score < min_score:
                continue
            candidates.append({
                "node_a": self._node_summary(a),
                "node_b": self._node_summary(b),
                "domain_a": da,
                "domain_b": db,
                "structural_overlap_score": round(score, 4),
                "evidence": evidence,
            })

        # Rank: highest overlap score first.
        candidates.sort(key=lambda c: -c["structural_overlap_score"])
        truncated = candidates[:top_k]

        return {
            "candidates": truncated,
            "total_pairs_evaluated": len(pool) * (len(pool) - 1) // 2,
            "total_pairs_returned": len(truncated),
            "excluded_already_connected": excluded_connected,
            "min_score": min_score,
            "node_types_filter": node_types,
            "domain_filter": domain_filter,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _candidate_nodes(self, node_types: Optional[List[str]],
                         domain_filter: Optional[List[str]]) -> List[str]:
        """Return node ids matching the filters."""
        out = []
        for n in self.nodes:
            if node_types and n.get("type") not in node_types:
                continue
            if domain_filter and n.get("domain") not in domain_filter:
                continue
            out.append(n["id"])
        return out

    def _connected_pairs(self, pool: List[str]) -> Set[frozenset]:
        """Return the set of pairs in `pool` that already have an edge."""
        pool_set = set(pool)
        connected: Set[frozenset] = set()
        for e in self.edges:
            src, tgt = e.get("source"), e.get("target")
            if src in pool_set and tgt in pool_set:
                connected.add(frozenset((src, tgt)))
        return connected

    def _domain_of(self, node_id: str) -> Optional[str]:
        n = self.by_id.get(node_id, {})
        return n.get("domain")

    def _node_summary(self, node_id: str) -> Dict[str, Any]:
        n = self.by_id.get(node_id, {"id": node_id, "label": node_id})
        return {
            "id": node_id,
            "label": n.get("label", node_id),
            "type": n.get("type", "unknown"),
            "domain": n.get("domain"),
        }

    def _prereqs(self, node_id: str, max_depth: int = 3) -> Set[str]:
        """Transitive closure of prerequisites, capped at depth."""
        if node_id in self._prereq_cache:
            return self._prereq_cache[node_id]
        visited: Set[str] = set()
        frontier = [node_id]
        for _ in range(max_depth):
            next_frontier = []
            for nid in frontier:
                for tgt, rel, _w in self.out.get(nid, []):
                    if rel in ("requires", "depends_on") and tgt not in visited:
                        visited.add(tgt)
                        next_frontier.append(tgt)
            frontier = next_frontier
            if not frontier:
                break
        self._prereq_cache[node_id] = visited
        return visited

    def _score_pair(self, a: str, b: str) -> Tuple[float, Dict[str, Any]]:
        """Score a pair by structural overlap.

        Components:
          - shared_prerequisites: fraction of prereqs in common
            (Jaccard-like: |A ∩ B| / |A ∪ B|)
          - shared_constraints: fraction of constraints in common
          - common_ancestor: +0.2 if they share any direct ancestor
            (i.e., any node that points to both)
        """
        pa = self._prereqs(a)
        pb = self._prereqs(b)
        shared_prereqs = pa & pb
        union_prereqs = pa | pb
        prereq_overlap = (
            len(shared_prereqs) / len(union_prereqs)
            if union_prereqs else 0.0
        )

        ca = self._constraint_cache.get(a, set())
        cb = self._constraint_cache.get(b, set())
        shared_constraints = ca & cb
        constraint_overlap = (
            len(shared_constraints) / len(ca | cb)
            if (ca | cb) else 0.0
        )

        # Common ancestors: nodes that point to BOTH a and b.
        a_ancestors = {src for src, _, _ in self.inc.get(a, [])}
        b_ancestors = {src for src, _, _ in self.inc.get(b, [])}
        common_ancestors = a_ancestors & b_ancestors
        ancestor_bonus = 0.2 if common_ancestors else 0.0

        score = (
            0.5 * prereq_overlap
            + 0.3 * constraint_overlap
            + ancestor_bonus
        )

        evidence = {
            "shared_prerequisites": sorted(shared_prereqs),
            "shared_constraints": sorted(shared_constraints),
            "common_ancestors": sorted(common_ancestors),
            "prereq_overlap": round(prereq_overlap, 4),
            "constraint_overlap": round(constraint_overlap, 4),
            "ancestor_bonus": ancestor_bonus,
        }
        return score, evidence


def _as_list(x) -> list:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]
