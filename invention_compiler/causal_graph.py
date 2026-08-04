"""
Three-tier causal edge schema (DR-15 / F-061).

Per the external audit of cycle 29: "a system can satisfy 'has a
mechanism field' by writing a plausible-sounding sentence, without
that sentence being physically true. That's the software-architect
failure mode wearing a physicist's vocabulary."

This module defines the three-tier edge schema (verified, asserted,
associative) and the CausalEdge dataclass that every edge in the
graph SHALL use. The tier determines which downstream operations
(simulation, adjacency search, discovery queries) may use the edge.

Reused schema from Phase 15 (per Instruction 0):
- CAUSALITY_POLICY.md: the causality test ("If A did not exist, would B
  be impossible or significantly harder?") is the DR-11 edge definition.
- The evidence tiers (explicitly stated, directly implied, structurally
  inferred, speculative) are the basis for verified/asserted/associative.
- The inadmissible evidence list (embedding, co-occurrence, keyword) is
  the definition of associative tier.
- MECHANISM_REGISTRY_V2.md: the Mechanism interface (inputs, constraints,
  outputs, evidence) is the node schema.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from enum import Enum


class EdgeTier(str, Enum):
    """The three tiers of causal edge verification (DR-15)."""
    VERIFIED = "verified"       # Formula evaluated, matches evidence
    ASSERTED = "asserted"       # Mechanism present, not evaluated
    ASSOCIATIVE = "associative"  # No mechanism (keyword match)


@dataclass
class CausalEdge:
    """A causal edge in the discovery graph.

    Per DR-11: every edge carries a direction and a mechanism.
    Per DR-12: two nodes are connected ONLY if the edge carries a
    stated mechanism. Edges without a mechanism are ASSOCIATIVE.
    Per DR-15: the tier (verified/asserted/associative) determines
    which downstream operations may use the edge.

    Reused from Phase 15 MECHANISM_REGISTRY_V2.md:
    - inputs: the state variables that must be present for the
      mechanism to fire (Phase 15's `inputs` field).
    - constraints: the conditions that block the mechanism (Phase 15's
      `constraints` field).
    - evidence: cited sources (Phase 15's `evidence` field).
    """
    source: str                     # source node ID
    target: str                     # target node ID
    direction: str                  # "causes", "enables", "constrains", "prevents"
    mechanism: Optional[str]        # the physical/chemical/biological process
    evidence: List[str]            # cited sources (URLs, DOIs, patent IDs)
    tier: EdgeTier                 # verified, asserted, or associative
    formula: Optional[str]         # callable function reference (for verified tier)
    formula_inputs: Optional[Dict[str, Any]]  # inputs to the formula
    formula_output: Optional[float]           # computed output
    expected_output: Optional[float]          # source's stated output
    tolerance: Optional[float]                # acceptable diff
    falsifiable_by: Optional[str]             # how to falsify this edge
    what_does_this_change: Optional[str]      # DR-13: what this edge changes
    created_at: str                # ISO timestamp
    provenance: Dict[str, Any]     # source URL, retrieval date, etc.

    def is_discovery_capable(self) -> bool:
        """Can this edge be used in discovery queries?

        Per DR-15: only verified and asserted edges may be used.
        Associative edges are excluded from discovery per DR-11.
        """
        return self.tier in (EdgeTier.VERIFIED, EdgeTier.ASSERTED)

    def is_simulation_capable(self) -> bool:
        """Can this edge be used in causal simulation?

        Per DR-15: only verified edges may be used in simulation.
        Asserted edges cannot be simulated (mechanism not evaluated).
        """
        return self.tier == EdgeTier.VERIFIED

    def is_verified(self) -> bool:
        """Has this edge's mechanism been evaluated against evidence?"""
        return self.tier == EdgeTier.VERIFIED

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d


@dataclass
class CausalNode:
    """A node in the causal discovery graph.

    Per DR-13: every node carries a what_does_this_change field.
    A node that changes nothing is dead information — excluded
    from traversal.

    Reused from Phase 15 MECHANISM_REGISTRY_V2.md:
    - inputs: state variables that must be present
    - constraints: conditions that block the mechanism
    - outputs: what the mechanism produces
    - evidence: cited events/sources
    """
    node_id: str
    node_type: str                 # "material", "property", "mechanism", "application"
    label: str
    properties: Dict[str, Any]    # material properties, etc.
    what_does_this_change: List[str]  # DR-13: causal outputs
    what_changes_this: List[str]      # DR-13: causal inputs
    inputs: List[str]              # Phase 15: state variables required
    constraints: List[str]         # Phase 15: blocking conditions
    outputs: List[str]             # Phase 15: observable outputs
    evidence: List[str]            # Phase 15: cited sources
    provenance: Dict[str, Any]     # source URL, retrieval date, etc.

    def is_discovery_capable(self) -> bool:
        """Can this node participate in discovery traversal?

        Per DR-13: a node without what_does_this_change is dead
        information — it is excluded from traversal.
        """
        return len(self.what_does_this_change) > 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CausalGraph:
    """The causal discovery graph.

    A collection of CausalNode and CausalEdge objects with tier-based
    filtering. Discovery queries traverse only discovery-capable nodes
    and edges. Simulation propagates only along verified-tier edges.
    """
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)

    def add_node(self, node: CausalNode):
        self.nodes[node.node_id] = node

    def add_edge(self, edge: CausalEdge):
        self.edges.append(edge)

    def discovery_capable_nodes(self) -> List[CausalNode]:
        """Nodes that pass the DR-13 what_does_this_change filter."""
        return [n for n in self.nodes.values() if n.is_discovery_capable()]

    def discovery_capable_edges(self) -> List[CausalEdge]:
        """Edges that pass the DR-15 tier filter (verified + asserted)."""
        return [e for e in self.edges if e.is_discovery_capable()]

    def simulation_capable_edges(self) -> List[CausalEdge]:
        """Edges that pass the DR-15 simulation filter (verified only)."""
        return [e for e in self.edges if e.is_simulation_capable()]

    def causal_density(self) -> float:
        """The ratio of verified edges to total edges.

        This is the metric that measures how much of the graph is
        actually causal vs. how much is asserted or associative.
        A causal density of 0.0 means no edges are verified — the
        graph is entirely asserted/associative. A causal density
        of 1.0 means all edges are verified — the graph is fully
        causal.
        """
        if not self.edges:
            return 0.0
        verified = sum(1 for e in self.edges if e.is_verified())
        return verified / len(self.edges)

    def tier_counts(self) -> Dict[str, int]:
        """Count edges by tier."""
        counts = {"verified": 0, "asserted": 0, "associative": 0}
        for e in self.edges:
            counts[e.tier.value] += 1
        return counts

    def adjacency_search(self, source_node_id: str, target_node_type: str) -> List[str]:
        """Search for nodes reachable from source via discovery-capable edges.

        Per DR-15: only verified and asserted edges are traversed.
        Associative edges are excluded. Per DR-13: only nodes with
        what_does_this_change are included in RESULTS — but traversal
        goes through all nodes (dead nodes block the path if excluded
        from traversal, which would hide live nodes behind them).
        """
        visited = set()
        queue = [source_node_id]
        results = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for edge in self.discovery_capable_edges():
                if edge.source == current:
                    target = edge.target
                    if target not in visited:
                        # Add to queue for traversal (even if dead node)
                        queue.append(target)
                        # Add to results only if discovery-capable + matching type
                        node = self.nodes.get(target)
                        if node and node.is_discovery_capable():
                            if node.node_type == target_node_type:
                                results.append(target)

        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "tier_counts": self.tier_counts(),
            "causal_density": self.causal_density(),
        }
