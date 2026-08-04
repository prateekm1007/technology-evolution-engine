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
    """The tiers of causal edge verification (DR-15, revised cycle 32).

    Four tiers: VERIFIED, ASSERTED, ASSOCIATIVE, CONTRADICTED.
    The CONTRADICTED tier (GAP-002, cycle 32 audit) distinguishes
    edges whose formula was executed and FAILED from edges that
    simply haven't been tested yet (ASSERTED). A CONTRADICTED edge
    is actively wrong — its stated expected_output does not match
    the formula's computed output.
    """
    VERIFIED = "verified"         # Formula evaluated, matches evidence
    ASSERTED = "asserted"         # Mechanism present, not yet evaluated
    ASSOCIATIVE = "associative"   # No mechanism (keyword match)
    CONTRADICTED = "contradicted"  # Formula evaluated, does NOT match (GAP-002)


class MechanismStatus(str, Enum):
    """The five states of mechanism validity (DR-15 revised, cycle 32).

    A mechanism is not valid merely because it is described. It is
    valid only if it satisfies one of:
      - observed: reproduced experimentally
      - simulated: numerically simulated
      - derived: derived from first principles
      - asserted: described but not verified (weakest state)
      - contradicted: formula executed, does NOT match stated output (GAP-002)

    Any mechanism lacking one of these five states is automatically
    downgraded to "asserted."
    """
    OBSERVED = "observed"       # reproduced experimentally
    SIMULATED = "simulated"     # numerically simulated
    DERIVED = "derived"         # derived from first principles
    ASSERTED = "asserted"       # described but not verified
    CONTRADICTED = "contradicted"  # formula executed, output does NOT match (GAP-002)


@dataclass
class Intervention:
    """An intervention specification (DR-16).

    A causal edge is valid only if an intervention can be specified.
    The fundamental question: "What happens if I change this?"
    """
    node: str                         # the node to intervene on
    intervention: str                 # what to change (e.g., "increase_5_percent")
    predicted_effect: str             # what the system predicts will happen
    expected_magnitude: Optional[str] # quantitative prediction (e.g., "2.5% increase in S")
    uncertainty: Optional[str]        # uncertainty band (e.g., "±0.5%")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Counterfactual:
    """A counterfactual specification (DR-17).

    Every causal statement must have a counterfactual:
      If X changes: Y changes.
      If X does not change: Y does not change.

    Without counterfactuals, the graph remains descriptive.
    """
    positive_case: str    # "If X changes: Y changes"
    negative_case: str    # "If X does not change: Y does not change"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentProposal:
    """The system's primary output: the next experiment (DR-18).

    The system's ultimate function is to answer: "What experiment
    should I perform tomorrow morning?" Every other output exists
    to serve this question.
    """
    prediction: str             # what the system predicts will happen
    intervention: Intervention  # what to change (DR-16)
    measurement: str            # what to measure and how
    falsification: str          # what result would falsify the prediction
    cost_usd: float             # what the experiment costs
    timeline_days: int          # how long it takes
    learning_if_pass: str       # what the system learns if prediction confirmed
    learning_if_fail: str       # what the system learns if prediction falsified

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class CausalEdge:
    """A causal edge in the discovery graph.

    Per DR-11: every edge carries a direction and a mechanism.
    Per DR-12: two nodes are connected ONLY if the edge carries a
    stated mechanism. Edges without a mechanism are ASSOCIATIVE.
    Per DR-15 (revised): the mechanism_status (observed/simulated/
    derived/asserted) determines validity.
    Per DR-16: a causal edge includes an intervention specification.
    Per DR-17: a causal edge includes a counterfactual.

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
    mechanism_status: Optional[MechanismStatus]  # DR-15 revised: observed/simulated/derived/asserted
    evidence: List[str]            # cited sources (URLs, DOIs, patent IDs)
    tier: EdgeTier                 # backwards-compat tier (derived from mechanism_status)
    formula: Optional[str]         # callable function reference (for derived/simulated)
    formula_inputs: Optional[Dict[str, Any]]  # inputs to the formula
    formula_output: Optional[float]           # computed output
    expected_output: Optional[float]          # source's stated output
    tolerance: Optional[float]                # acceptable diff
    falsifiable_by: Optional[str]             # how to falsify this edge
    what_does_this_change: Optional[str]      # DR-13: what this edge changes
    intervention: Optional[Intervention]      # DR-16: what happens if I change this
    counterfactual: Optional[Counterfactual]  # DR-17: what happens if I don't change this
    created_at: str                # ISO timestamp
    provenance: Dict[str, Any]     # source URL, retrieval date, etc.

    def is_discovery_capable(self) -> bool:
        """Can this edge be used in discovery queries?

        Per DR-15: only edges with a mechanism (any status) may be used.
        Associative edges (no mechanism) are excluded from discovery.
        CONTRADICTED edges (GAP-002) are excluded — they are actively wrong.
        Per DR-16: only edges with an intervention may be used for
        causal reasoning.
        """
        if self.tier in (EdgeTier.ASSOCIATIVE, EdgeTier.CONTRADICTED):
            return False
        # DR-16: causal reasoning requires intervention
        # But asserted-tier edges without intervention can still be
        # used for hypothesis generation (flagged)
        return self.tier in (EdgeTier.VERIFIED, EdgeTier.ASSERTED)

    def is_simulation_capable(self) -> bool:
        """Can this edge be used in causal simulation?

        Per DR-15 (revised): only observed/simulated/derived mechanisms
        may be used in simulation. "asserted" mechanisms cannot be
        simulated (not verified). "contradicted" mechanisms (GAP-002)
        are actively wrong and must never be simulated.
        """
        if self.tier in (EdgeTier.CONTRADICTED, EdgeTier.ASSOCIATIVE, EdgeTier.ASSERTED):
            return False
        if self.tier != EdgeTier.VERIFIED:
            return False
        # DR-15 revised: VERIFIED means observed/simulated/derived
        # (not just "asserted with a formula")
        if self.mechanism_status == MechanismStatus.ASSERTED:
            return False
        if self.mechanism_status == MechanismStatus.CONTRADICTED:
            return False
        return self.mechanism_status in (
            MechanismStatus.OBSERVED,
            MechanismStatus.SIMULATED,
            MechanismStatus.DERIVED,
        )

    def is_causal(self) -> bool:
        """Is this edge truly causal (not just a mechanism)?

        Per DR-16 + DR-17: a causal edge has BOTH an intervention
        specification AND a counterfactual. Without both, it is a
        mechanism (how it's connected) but not causality (what changes
        when you intervene).
        """
        return self.intervention is not None and self.counterfactual is not None

    def is_verified(self) -> bool:
        """Has this edge's mechanism been evaluated against evidence?"""
        return self.tier == EdgeTier.VERIFIED

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["mechanism_status"] = self.mechanism_status.value if self.mechanism_status else None
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
        """Count edges by tier (including CONTRADICTED per GAP-002)."""
        counts = {"verified": 0, "asserted": 0, "associative": 0, "contradicted": 0}
        for e in self.edges:
            if e.tier.value in counts:
                counts[e.tier.value] += 1
            else:
                counts[e.tier.value] = 1
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
