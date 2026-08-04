"""
Discovery Graph Architecture — 6-layer discovery graph (DR-19).

Per CEO directive: "seamlessly make this our discovery mechanism
architecture and integrate all our moving parts into this."

This module implements the 6-layer Discovery Graph:

  Layer 0: IdentityGraph      (EQUIVALENCE — same-thing identity)
  Layer 1: SimilarityGraph    (ASSOCIATION — resemblance, no causal claim)
  Layer 2: InfluenceGraph     (INFLUENCE — probable directional effect)
  Layer 3: MechanismGraph      (MECHANISM — explanatory causal chain)
  Layer 4: CausalGraph         (INTERVENTION — deliberate causal manipulation)
  Layer 5: ExperimentGraph     (OBSERVATION — prediction vs. reality)

Key principle: "Never let the graph inherit the limitations of the
data source. Patents are one view of reality. Reality itself is the graph."

This module integrates with the existing causal_graph.py:
  - CausalEdge → maps to Layer 4 (INTERVENTION) edges
  - CausalNode → maps to Layer 3 (MECHANISM) and Layer 4 nodes
  - The 4-tier EdgeTier schema → maps to Evidence flags
  - The 5-state MechanismStatus → maps to Evidence booleans
  - ClosedLoopTracker → maps to Layer 5 (OBSERVATION) edges
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum

# Import MechanismStatus at module level (needed for Evidence default value)
from invention_compiler.causal_graph import MechanismStatus


# ----------------------------------------------------------------------
# RelationType: the 6-layer edge schema
# ----------------------------------------------------------------------

class RelationType(Enum):
    """The six relation types in the Discovery Graph.

    Each layer answers a distinct epistemic question. Conflating them
    destroys the ability to reason about what kind of claim an edge
    is making.
    """
    EQUIVALENCE = "equivalence"     # Layer 0 — same-thing identity
    ASSOCIATION = "association"     # Layer 1 — resemblance, no causal claim
    INFLUENCE = "influence"         # Layer 2 — probable directional effect
    MECHANISM = "mechanism"         # Layer 3 — explanatory causal chain
    INTERVENTION = "intervention"   # Layer 4 — deliberate causal manipulation
    OBSERVATION = "observation"     # Layer 5 — prediction vs. reality


# ----------------------------------------------------------------------
# Evidence: replacing scalar weights
# ----------------------------------------------------------------------

@dataclass
class Evidence:
    """Evidence object — every edge carries one instead of a scalar weight.

    Per Law 27 (forbidden language): NO numerical confidence. The old
    `confidence: float` field was a Law 27 violation (cycle 37 audit,
    L27-VIO). It has been removed.

    Per cycle 37 audit (TAX-COL): the 4 booleans (observed/simulated/
    derived/experimental) collided with MechanismStatus's 5 values.
    They have been replaced with a single `mechanism_status` field
    that uses the unified taxonomy.

    Ranking is derived from source_count + mechanism_status, not from
    a fabricated float. An edge with mechanism_status=OBSERVED and
    source_count=5 ranks higher than one with ASSERTED and source_count=1.
    """
    provenance: str                              # "USPTO citation", "DFT simulation", "lab measurement"
    source_count: int = 1                        # number of independent supporting sources
    mechanism_status: MechanismStatus = MechanismStatus.ASSERTED  # unified taxonomy

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mechanism_status"] = self.mechanism_status.value
        return d

    @classmethod
    def from_mechanism_status(cls, status: MechanismStatus,
                               provenance: str = "",
                               source_count: int = 1) -> "Evidence":
        """Create Evidence from the unified MechanismStatus taxonomy."""
        return cls(
            provenance=provenance,
            source_count=source_count,
            mechanism_status=status,
        )


# ----------------------------------------------------------------------
# DiscoveryEdge: universal edge type across all 6 layers
# ----------------------------------------------------------------------

@dataclass
class DiscoveryEdge:
    """A universal edge in the Discovery Graph.

    Every edge carries:
    - source: source node ID
    - target: target node ID
    - relation_type: which of the 6 layers this edge belongs to
    - evidence: Evidence object (replaces scalar weight)
    - metadata: layer-specific data (e.g., mechanism string, intervention spec)
    """
    source: str
    target: str
    relation_type: RelationType
    evidence: Evidence
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["relation_type"] = self.relation_type.value
        return d


# ----------------------------------------------------------------------
# DiscoveryNode: universal node type across all 6 layers
# ----------------------------------------------------------------------

@dataclass
class DiscoveryNode:
    """A universal node in the Discovery Graph.

    A node can appear in multiple layers — e.g., a material might have
    MECHANISM edges (band gap → mobility) and INFLUENCE edges (patent
    citation). The node is the same entity; the edges are in different
    subgraphs.
    """
    node_id: str
    node_type: str           # "patent", "paper", "material", "mechanism", "experiment"
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    layers: Set[RelationType] = field(default_factory=set)  # which layers this node appears in
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["layers"] = [l.value for l in self.layers]
        return d


# ----------------------------------------------------------------------
# Typed subgraphs
# ----------------------------------------------------------------------

class SubGraph:
    """A typed subgraph for one relation type.

    Each subgraph holds edges of a single RelationType. This separation
    ensures that algorithms appropriate for one layer (e.g., union-find
    for EQUIVALENCE, nearest-neighbor for ASSOCIATION) don't leak into
    other layers.
    """
    def __init__(self, relation_type: RelationType):
        self.relation_type = relation_type
        self.edges: List[DiscoveryEdge] = []
        self.nodes: Dict[str, DiscoveryNode] = {}

    def add_edge(self, edge: DiscoveryEdge):
        assert edge.relation_type == self.relation_type, (
            f"Edge relation_type {edge.relation_type} does not match "
            f"subgraph type {self.relation_type}"
        )
        self.edges.append(edge)

    def register_entity_link(self, node_id: str, entity_id: str):
        """Link a node (e.g., patent) to a canonical entity (e.g., material)."""
        self.entity_links[node_id] = entity_id

    def add_node(self, node: DiscoveryNode):
        if node.node_id not in self.nodes:
            self.nodes[node.node_id] = node
        else:
            # Merge layers
            self.nodes[node.node_id].layers |= node.layers

    def edges_from(self, node_id: str) -> List[DiscoveryEdge]:
        return [e for e in self.edges if e.source == node_id]

    def edges_to(self, node_id: str) -> List[DiscoveryEdge]:
        return [e for e in self.edges if e.target == node_id]


class IdentityGraph(SubGraph):
    def resolve_canonical_entities(self) -> Dict[str, str]:
        """Resolve equivalence classes to canonical entities.
        Returns a map from node_id → canonical_id.
        """
        # Union-find for transitive closure
        parent = {}
        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        for edge in self.edges:
            union(edge.source, edge.target)
        return {n: find(n) for n in parent}
    """Layer 0: EQUIVALENCE — same-thing identity.

    Uses union-find / connected-components to resolve canonical entities.
    Nodes linked by EQUIVALENCE edges are the SAME entity and should be
    merged for canonical reference.
    """
    def __init__(self):
        super().__init__(RelationType.EQUIVALENCE)

    def find_canonical(self, node_id: str) -> str:
        """Find the canonical (representative) node for a given node."""
        # Simple union-find: follow equivalence edges to the root
        visited = set()
        current = node_id
        while current not in visited:
            visited.add(current)
            edges = self.edges_from(current) + self.edges_to(current)
            parents = [e.target if e.source == current else e.source for e in edges]
            if not parents:
                return current
            current = parents[0]  # follow first parent
        return current


class SimilarityGraph(SubGraph):
    def find_neighbors(self, node_id: str) -> List[str]:
        """Find all nodes connected to node_id by similarity edges."""
        neighbors = []
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.append(edge.target)
            elif edge.target == node_id:
                neighbors.append(edge.source)
        return list(set(neighbors))
    """Layer 1: ASSOCIATION — resemblance, no causal claim.

    Uses nearest-neighbor / clustering. These edges must NEVER be
    silently treated as evidence of influence or causality.
    """
    def __init__(self):
        super().__init__(RelationType.ASSOCIATION)


class InfluenceGraph(SubGraph):
    def get_outgoing(self, node_id: str) -> List[DiscoveryEdge]:
        """Get all directed edges going OUT from node_id."""
        return [e for e in self.edges if e.source == node_id]
    """Layer 2: INFLUENCE — probable directional effect.

    Uses directed graph centrality and citation-flow analysis.
    Citation graphs are NOT causal graphs — influence is correlational.
    """
    def __init__(self):
        super().__init__(RelationType.INFLUENCE)


class MechanismGraph(SubGraph):
    def trace_chain(self, start_id: str, end_id: str) -> List[str]:
        """Trace a mechanism chain from start_id to end_id. Returns node IDs."""
        visited = set()
        queue = [(start_id, [start_id])]
        while queue:
            current, path = queue.pop(0)
            if current == end_id:
                return path
            if current in visited:
                continue
            visited.add(current)
            for edge in self.edges:
                if edge.source == current and edge.target not in visited:
                    queue.append((edge.target, path + [edge.target]))
        return []
        

    """Layer 3: MECHANISM — explanatory causal chain.

    Grounded in domain science (materials science, physics, chemistry).
    Independent of any single patent or paper. These edges explain HOW
    something works, not WHETHER it was cited.
    """
    def __init__(self):
        super().__init__(RelationType.MECHANISM)


class CausalGraphLayer(SubGraph):
    def get_intervention_edges(self) -> List[DiscoveryEdge]:
        """Get all intervention edges."""
        return [e for e in self.edges if e.relation_type == RelationType.INTERVENTION]
    """Layer 4: INTERVENTION — deliberate causal manipulation.

    Maps to the existing CausalEdge/CausalGraph from causal_graph.py.
    These edges assert "if I do X, Y will happen" — causal, ideally
    quantified, dose-response.
    """
    def __init__(self):
        super().__init__(RelationType.INTERVENTION)


class ExperimentGraph(SubGraph):
    def get_observations(self) -> List[DiscoveryEdge]:
        """Get all observation edges."""
        return [e for e in self.edges if e.relation_type == RelationType.OBSERVATION]
    """Layer 5: OBSERVATION — prediction vs. reality.

    Maps to the ClosedLoopTracker from experimentation_layer/scoping.py.
    These edges record that a prediction was tested against reality and
    either confirmed, refuted, or partially supported. This is what
    allows the graph to LEARN rather than just accumulate.
    """
    def __init__(self):
        super().__init__(RelationType.OBSERVATION)


# ----------------------------------------------------------------------
# DiscoveryGraph: the composed graph
# ----------------------------------------------------------------------

class DiscoveryGraph:
    """The composed 6-layer Discovery Graph.

    Coordinates six typed subgraphs. Supports cross-layer queries that
    traverse multiple relation types in a single path.

    Cross-layer queries are the point:
        US patent → citation → Chinese patent → scientific paper →
        material → mechanism → experiment

    This traversal crosses InfluenceGraph (citation), MechanismGraph
    (material → mechanism), and ExperimentGraph (validation).
    """

    def __init__(self):
        self.identity = IdentityGraph()
        self.similarity = SimilarityGraph()
        self.influence = InfluenceGraph()
        self.mechanism = MechanismGraph()
        self.causal = CausalGraphLayer()
        self.experiment = ExperimentGraph()
        self.nodes: Dict[str, DiscoveryNode] = {}
        self.entity_links: Dict[str, str] = {}  # node_id → canonical entity_id

        # Map for cross-layer lookup
        self._subgraphs = {
            RelationType.EQUIVALENCE: self.identity,
            RelationType.ASSOCIATION: self.similarity,
            RelationType.INFLUENCE: self.influence,
            RelationType.MECHANISM: self.mechanism,
            RelationType.INTERVENTION: self.causal,
            RelationType.OBSERVATION: self.experiment,
        }

    def register_entity_link(self, node_id: str, entity_id: str):
        """Link a node (e.g., patent) to a canonical entity (e.g., material)."""
        self.entity_links[node_id] = entity_id

    def add_node(self, node: DiscoveryNode):
        """Add a node to the graph. The node appears in the specified layers."""
        if node.node_id not in self.nodes:
            self.nodes[node.node_id] = node
        else:
            self.nodes[node.node_id].layers |= node.layers
        # Add to each subgraph where the node appears
        for layer in node.layers:
            self._subgraphs[layer].add_node(node)

    def add_edge(self, edge: DiscoveryEdge):
        """Add an edge to the appropriate subgraph based on its relation_type."""
        subgraph = self._subgraphs[edge.relation_type]
        subgraph.add_edge(edge)
        # Ensure nodes exist
        for nid in (edge.source, edge.target):
            if nid not in self.nodes:
                self.nodes[nid] = DiscoveryNode(
                    node_id=nid, node_type="unknown", label=nid,
                    layers={edge.relation_type}
                )
            else:
                self.nodes[nid].layers.add(edge.relation_type)
            self._subgraphs[edge.relation_type].add_node(self.nodes[nid])

    def cross_layer_query(self, start_node: str, target_layer: RelationType,
                           max_depth: int = 10) -> List[Tuple[str, List[DiscoveryEdge]]]:
        """Query across multiple layers to find paths from start to target_layer.

        Traverses ALL subgraphs to find paths from the start node to any
        node in the target layer. Returns a list of (end_node, path) tuples.

        Example: cross_layer_query("US1234567", RelationType.OBSERVATION)
        might find: patent → citation → paper → mechanism → experiment
        """
        results = []
        visited = set()
        queue = [(start_node, [])]

        while queue and len(results) < 50:  # cap results
            current_id, path = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Check if this node is in the target layer
            node = self.nodes.get(current_id)
            if node and target_layer in node.layers and len(path) > 0:
                results.append((current_id, path))

            if len(path) >= max_depth:
                continue

            # Traverse all subgraphs from this node
            for subgraph in self._subgraphs.values():
                for edge in subgraph.edges_from(current_id):
                    if edge.target not in visited:
                        queue.append((edge.target, path + [edge]))

        return results

    def import_causal_graph(self, causal_graph):
        """Import edges from an existing CausalGraph (causal_graph.py).

        Maps:
        - CausalEdge with tier=VERIFIED → INTERVENTION + Evidence(mechanism_status=DERIVED)
        - CausalEdge with tier=ASSERTED → MECHANISM + Evidence(mechanism_status=ASSERTED)
        - CausalEdge with tier=ASSOCIATIVE → ASSOCIATION + Evidence(mechanism_status=ASSERTED)
        - CausalEdge with tier=CONTRADICTED → excluded
        - CausalEdge with tier=CONTRADICTED → excluded
        """
        from invention_compiler.causal_graph import EdgeTier, MechanismStatus

        for edge in causal_graph.edges:
            if edge.tier == EdgeTier.CONTRADICTED:
                continue  # excluded from discovery graph

            if edge.tier == EdgeTier.VERIFIED:
                rt = RelationType.INTERVENTION
                ev = Evidence(
                    provenance=str(edge.provenance),
                    confidence=0.8,
                    source_count=len(edge.evidence) if edge.evidence else 1,
                    observed=edge.mechanism_status == MechanismStatus.OBSERVED,
                    simulated=edge.mechanism_status == MechanismStatus.SIMULATED,
                    derived=edge.mechanism_status == MechanismStatus.DERIVED,
                    experimental=edge.mechanism_status == MechanationStatus.OBSERVED,
                )
            elif edge.tier == EdgeTier.ASSERTED:
                rt = RelationType.MECHANISM
                ev = Evidence(
                    provenance=str(edge.provenance),
                    confidence=0.3,
                    source_count=1,
                    observed=False, simulated=False, derived=False, experimental=False,
                )
            elif edge.tier == EdgeTier.ASSOCIATIVE:
                rt = RelationType.ASSOCIATION
                ev = Evidence(
                    provenance="keyword_match",
                    mechanism_status=MechanismStatus.ASSERTED,
                    source_count=1,
                )
            else:
                continue

            self.add_edge(DiscoveryEdge(
                source=edge.source,
                target=edge.target,
                relation_type=rt,
                evidence=ev,
                metadata={"mechanism": edge.mechanism} if edge.mechanism else {},
            ))

    def import_experiment_result(self, tracker):
        """Import a closed-loop experiment result as an OBSERVATION edge.

        Maps the ClosedLoopTracker's 5-step record to an OBSERVATION edge:
        - source: the prediction node
        - target: the observation node
        - evidence: mechanism_status=OBSERVED (validated by experiment)
        """
        from experimentation_layer.scoping import ClosedLoopTracker

        if not tracker.is_closed_loop():
            return

        ev = Evidence(
            provenance=f"EXP-001 experiment: {tracker.experiment_id}",
            confidence=0.9 if tracker.step_5_closeness_value > 0 else 0.1,
            source_count=1,
            observed=True,
            experimental=True,
        )

        self.add_edge(DiscoveryEdge(
            source=f"prediction_{tracker.experiment_id}",
            target=f"observation_{tracker.experiment_id}",
            relation_type=RelationType.OBSERVATION,
            evidence=ev,
            metadata={
                "closeness_value": tracker.step_5_closeness_value,
                "root_cause": tracker.step_3_root_cause_evidence,
                "learning": tracker.step_5_closeness_value > 0,
            },
        ))

    def layer_summary(self) -> Dict[str, Any]:
        """Return a summary of all 6 layers."""
        summary = {}
        for rt, sg in self._subgraphs.items():
            summary[rt.value] = {
                "nodes": len(sg.nodes),
                "edges": len(sg.edges),
            }
        summary["total_nodes"] = len(self.nodes)
        summary["total_edges"] = sum(len(sg.edges) for sg in self._subgraphs.values())
        return summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layers": self.layer_summary(),
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": {
                rt.value: [e.to_dict() for e in sg.edges]
                for rt, sg in self._subgraphs.items()
            },
        }
