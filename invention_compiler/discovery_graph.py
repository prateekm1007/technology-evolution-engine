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
    - falsifiable_by: how to falsify this edge (Popper test, DR-23)
    - direction: INCREASES/DECREASES/CAUSES/ENABLES (Altshuller, DR-23)
    """
    source: str
    target: str
    relation_type: RelationType
    evidence: Evidence
    metadata: Dict[str, Any] = field(default_factory=dict)
    falsifiable_by: Optional[str] = None
    direction: Optional[str] = None  # "increases", "decreases", "causes", "enables"

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
        # Ensure nodes exist (preserve node_type if a typed node was already added)
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

        Per cycle 48 (Swanson meaningful): nodes are imported BEFORE edges so
        that node_type is preserved from the source CausalNode. Previously
        add_edge auto-created nodes with node_type="unknown", which made
        SwansonBridgeSearch's cross-type meaningfulness check always return 0.
        """
        from invention_compiler.causal_graph import EdgeTier, MechanismStatus

        # 1. Import NODES first, preserving node_type from CausalNode
        for nid, cnode in causal_graph.nodes.items():
            if nid not in self.nodes:
                # Determine which layer(s) this node participates in by scanning
                # edges in the causal graph. A node with no edges is still added
                # to the MECHANISM layer by default (DR-19 universal node model).
                participating_layers = set()
                for e in causal_graph.edges:
                    if e.source == nid or e.target == nid:
                        if e.tier == EdgeTier.VERIFIED:
                            participating_layers.add(RelationType.INTERVENTION)
                        elif e.tier == EdgeTier.ASSERTED:
                            participating_layers.add(RelationType.MECHANISM)
                        elif e.tier == EdgeTier.ASSOCIATIVE:
                            participating_layers.add(RelationType.ASSOCIATION)
                if not participating_layers:
                    participating_layers = {RelationType.MECHANISM}

                dnode = DiscoveryNode(
                    node_id=nid,
                    node_type=cnode.node_type,  # PRESERVE — was 'unknown' before
                    label=cnode.label,
                    properties=dict(cnode.properties) if hasattr(cnode, 'properties') else {},
                    layers=participating_layers,
                )
                self.add_node(dnode)
            else:
                # Node already exists — merge layers but preserve node_type
                self.nodes[nid].layers |= {RelationType.MECHANISM}
                if self.nodes[nid].node_type == "unknown" and cnode.node_type != "unknown":
                    self.nodes[nid].node_type = cnode.node_type
                if not self.nodes[nid].label or self.nodes[nid].label == nid:
                    self.nodes[nid].label = cnode.label

        # 2. Import EDGES
        for edge in causal_graph.edges:
            if edge.tier == EdgeTier.CONTRADICTED:
                continue  # excluded from discovery graph

            if edge.tier == EdgeTier.VERIFIED:
                rt = RelationType.INTERVENTION
                ev = Evidence(
                    provenance=str(edge.provenance),
                    source_count=len(edge.evidence) if edge.evidence else 1,
                    mechanism_status=edge.mechanism_status or MechanismStatus.DERIVED,
                )
            elif edge.tier == EdgeTier.ASSERTED:
                rt = RelationType.MECHANISM
                ev = Evidence(
                    provenance=str(edge.provenance),
                    source_count=1,
                    mechanism_status=MechanismStatus.ASSERTED,
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
                falsifiable_by=getattr(edge, 'falsifiable_by', None),
                direction=edge.direction if hasattr(edge, 'direction') else None,
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
            source_count=1,
            mechanism_status=MechanismStatus.OBSERVED if tracker.step_5_closeness_value and tracker.step_5_closeness_value > 0 else MechanismStatus.CONTRADICTED,
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


# ----------------------------------------------------------------------
# DR-21: Object-centric data model (Entity, Mechanism, Constraint, Law,
# Contradiction, Intervention, Experiment)
# ----------------------------------------------------------------------

@dataclass
class Entity:
    """An entity in the object-centric model (DR-21).
    
    Per the CEO's directive: move from document-centric to object-centric.
    An Entity is a canonical object (material, device, method) with
    aliases and provenance — not tied to a single document.
    """
    entity_id: str
    entity_type: str  # "material", "device", "method", "property", "application"
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    provenance: List[Evidence] = field(default_factory=list)


@dataclass
class MechanismObject:
    """A mechanism in the object-centric model (DR-21).
    
    Per Machamer/Darden/Craver (2000): a mechanism is entities and
    activities organized such that they produce a regular change from
    start to finish conditions.
    """
    mechanism_id: str
    entities: List[str] = field(default_factory=list)  # Entity IDs
    activities: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)  # start→finish states
    constraints: List[str] = field(default_factory=list)
    equations: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class Constraint:
    """A constraint in the object-centric model (DR-21).
    
    Per BACON (Langley et al. 1987): constraints are relationships
    between variables that limit the solution space.
    """
    variable_a: str
    variable_b: str
    relationship: str  # "increases", "decreases", "limits", "enables"
    mechanism_status: MechanismStatus = MechanismStatus.ASSERTED


@dataclass
class Law:
    """A law in the object-centric model (DR-21).
    
    Per BACON: a law is a functional relationship between variables,
    derived from data or first principles.
    """
    law_id: str
    equation: str
    domain: str  # "thermodynamics", "electrochemistry", etc.
    assumptions: List[str] = field(default_factory=list)
    mechanism_status: MechanismStatus = MechanismStatus.ASSERTED


@dataclass
class Contradiction:
    """A contradiction in the object-centric model (DR-21).
    
    Per Altshuller/TRIZ: a contradiction exists when improving one
    parameter worsens another. Resolution is the core of invention.
    """
    contradiction_id: str
    improve: str  # parameter that improves
    worsen: str   # parameter that worsens
    mechanism: str  # what causes the contradiction
    resolution: Optional[str] = None  # how it was/would be resolved


@dataclass
class InterventionObject:
    """An intervention in the object-centric model (DR-21).
    
    Per Pearl: an intervention is a deliberate change to a variable
    to observe its causal effect.
    """
    intervention_id: str
    variable: str  # what to change
    change: str     # how to change it (e.g., "increase 5%")
    expected_effect: str  # what we predict will happen
    mechanism_status: MechanismStatus = MechanismStatus.ASSERTED


@dataclass
class ExperimentObject:
    """An experiment in the object-centric model (DR-21).
    
    Per Ross King (Robot Scientist Adam, 2009): a complete experiment
    has protocol, prediction, measurement, and outcome.
    """
    experiment_id: str
    protocol: str       # how to run it
    prediction: str     # what we expect
    measurement: str    # what to measure
    outcome: Optional[str] = None  # what actually happened (None = not yet run)


# ----------------------------------------------------------------------
# DR-20: The 3 core discovery algorithms
# ----------------------------------------------------------------------

class SwansonBridgeSearch:
    """Algorithm 1: Swanson bridge search (DR-20).
    
    Per Don R. Swanson (1986): if A→B is established in one literature
    and B→C in another, and the two never cite each other, A→C is a
    discoverable-but-undiscovered connection.
    
    This is the algorithmic version of what the Apollo Test did by hand
    with Bi₂Te₃ (thermoelectric literature) and NRR catalysis.
    """
    
    @staticmethod
    def search(graph: DiscoveryGraph, max_depth: int = 3,
               require_disjoint: bool = False) -> List[Dict[str, Any]]:
        """Search for undiscovered bridges in the graph.

        Per Swanson (1986): if A→B is established in one literature
        and B→C in another, and the two literatures never cite each
        other, A→C is a discoverable-but-undiscovered connection.

        Args:
            graph: the discovery graph
            max_depth: maximum chain length to search
            require_disjoint: if True, only return bridges where a and c
                come from disjoint literatures (different source domains
                with no shared edges). This is Swanson's core insight —
                without it, the search is just path-finding, not discovery.

        Returns a list of {a, b, c, score, disjoint} where a→b and b→c exist
        but a→c does not.
        """
        bridges = []
        # Get all nodes that have outgoing edges
        nodes_with_outgoing = set()
        for subgraph in graph._subgraphs.values():
            for edge in subgraph.edges:
                nodes_with_outgoing.add(edge.source)
        
        for a in nodes_with_outgoing:
            # Get successors of a
            b_candidates = set()
            for subgraph in graph._subgraphs.values():
                for edge in subgraph.edges:
                    if edge.source == a:
                        b_candidates.add(edge.target)
            
            for b in b_candidates:
                # Get successors of b
                c_candidates = set()
                for subgraph in graph._subgraphs.values():
                    for edge in subgraph.edges:
                        if edge.source == b:
                            c_candidates.add(edge.target)
                
                for c in c_candidates:
                    if c == a:
                        continue
                    # Check if a→c already exists
                    a_to_c_exists = False
                    for subgraph in graph._subgraphs.values():
                        for edge in subgraph.edges:
                            if edge.source == a and edge.target == c:
                                a_to_c_exists = True
                                break
                        if a_to_c_exists:
                            break
                    
                    if not a_to_c_exists:
                        # Per cycle 148 (Test 1 fix): check literature disjointness.
                        # Swanson's core insight: the two literatures must NOT cite
                        # each other. Without this check, any path is a "bridge" —
                        # that's path-finding, not discovery.
                        is_disjoint = True
                        if require_disjoint:
                            # Check if a and c share any neighbors (literature overlap)
                            a_neighbors = set()
                            c_neighbors = set()
                            for subgraph3 in graph._subgraphs.values():
                                for edge3 in subgraph3.edges:
                                    if edge3.source == a:
                                        a_neighbors.add(edge3.target)
                                    if edge3.source == c:
                                        c_neighbors.add(edge3.target)
                                    if edge3.target == a:
                                        a_neighbors.add(edge3.source)
                                    if edge3.target == c:
                                        c_neighbors.add(edge3.source)
                            # If a and c share many neighbors, they're in the same
                            # literature (not disjoint). A true Swanson bridge connects
                            # two literatures that don't overlap.
                            shared_neighbors = a_neighbors & c_neighbors - {b}
                            is_disjoint = len(shared_neighbors) == 0

                            # Also check node properties for source_domain tags
                            try:
                                a_node = graph.get_node(a) or {}
                                c_node = graph.get_node(c) or {}
                                a_domain = a_node.get("source_domain", a_node.get("domain", ""))
                                c_domain = c_node.get("source_domain", c_node.get("domain", ""))
                                if a_domain and c_domain and a_domain == c_domain:
                                    is_disjoint = False  # same domain = not disjoint
                            except Exception:
                                pass

                        # Skip non-disjoint bridges if require_disjoint is True
                        if require_disjoint and not is_disjoint:
                            continue

                        # Score (cycle 54 fix, per Auditor Phase 1):
                        layer_weights = {
                            "equivalence": 0.1, "association": 0.2, "influence": 0.4,
                            "mechanism": 0.6, "intervention": 0.8, "observation": 1.0,
                        }
                        a_to_b_weight = 0.2
                        b_to_c_weight = 0.2
                        for subgraph2 in graph._subgraphs.values():
                            for edge2 in subgraph2.edges:
                                if edge2.source == a and edge2.target == b:
                                    rt = edge2.relation_type
                                    rt_str = rt.value if hasattr(rt, 'value') else str(rt)
                                    a_to_b_weight = layer_weights.get(rt_str, 0.2)
                                if edge2.source == b and edge2.target == c:
                                    rt = edge2.relation_type
                                    rt_str = rt.value if hasattr(rt, 'value') else str(rt)
                                    b_to_c_weight = layer_weights.get(rt_str, 0.2)
                        bridge_score = (a_to_b_weight + b_to_c_weight) / 2.0
                        # Boost score for disjoint bridges (genuine discovery)
                        if is_disjoint:
                            bridge_score *= 1.5
                        bridges.append({
                            "a": a,
                            "b": b,
                            "c": c,
                            "score": round(bridge_score, 4),
                            "a_to_b_layer": a_to_b_weight,
                            "b_to_c_layer": b_to_c_weight,
                            "disjoint": is_disjoint,
                            "description": f"{'[DISJOINT] ' if is_disjoint else ''}Bridge: {a} → {b} → {c} (a→c not connected)"
                        })
        
        return bridges


def _edge_type_sequence(graph: DiscoveryGraph, chain: List[str]) -> List[str]:
    """Get the sequence of edge relation_types along a chain.

    Per cycle 54 Gentner fix (Auditor Phase 1): Gentner's systematicity
    is about RELATIONAL structure, not just chain length. Two chains with
    the same edge-type sequence (e.g., [MECHANISM, MECHANISM, INTERVENTION])
    are structurally analogous; two with different sequences are not.

    Returns a list of relation_type values (as strings) for each consecutive
    pair in the chain. If no edge exists between two consecutive nodes,
    returns an empty list (the chain is invalid).
    """
    if len(chain) < 2:
        return []
    sequence = []
    for i in range(len(chain) - 1):
        src, tgt = chain[i], chain[i + 1]
        found = False
        for subgraph in graph._subgraphs.values():
            for edge in subgraph.edges:
                if edge.source == src and edge.target == tgt:
                    sequence.append(edge.relation_type.value
                                   if hasattr(edge.relation_type, 'value')
                                   else str(edge.relation_type))
                    found = True
                    break
            if found:
                break
        if not found:
            # No edge between consecutive nodes — invalid chain
            return []
    return sequence


def _get_edge_predicates(graph: DiscoveryGraph, chain: List[str]) -> List[str]:
    """Get the sequence of edge PREDICATES (directions) along a chain.

    Per cycle 158 (Test 5 fix): Gentner's structure mapping compares
    RELATIONAL PREDICATES, not just edge layer types. The predicate is
    the actual relation verb (e.g., "causes", "enables", "determines"),
    stored in the edge's 'direction' field. This is different from
    _edge_type_sequence which returns the RelationType (mechanism,
    influence, etc.).

    Returns a list of direction/predicate strings for each consecutive
    pair in the chain. If no edge exists, returns empty list.
    """
    if len(chain) < 2:
        return []
    predicates = []
    for i in range(len(chain) - 1):
        src, tgt = chain[i], chain[i + 1]
        found = False
        for subgraph in graph._subgraphs.values():
            for edge in subgraph.edges:
                if edge.source == src and edge.target == tgt:
                    pred = getattr(edge, 'direction', None) or 'unknown'
                    predicates.append(pred.lower())
                    found = True
                    break
            if found:
                break
        if not found:
            return []
    return predicates


# Predicate similarity groups: predicates that serve similar causal roles
_PREDICATE_GROUPS = {
    "causal": {"causes", "produces", "generates", "creates", "induces", "triggers"},
    "enabling": {"enables", "facilitates", "allows", "permits", "promotes"},
    "modulating": {"increases", "enhances", "improves", "boosts", "decreases",
                   "reduces", "lowers", "inhibits", "suppresses", "prevents",
                   "minimizes", "maximizes", "optimizes", "affects"},
    "determining": {"determines", "governs", "controls", "regulates", "dictates"},
    "characterizing": {"exhibits", "shows", "displays", "demonstrates",
                       "characterizes", "compares"},
}


def _predicates_similar(pred_a: str, pred_b: str) -> bool:
    """Check if two predicates are in the same causal category.

    Per cycle 158: Gentner's structure mapping allows analogies between
    chains with similar (not identical) predicates. "causes" and "produces"
    are in the same causal category, so a chain [causes, enables] is
    analogous to [produces, allows] even though the exact verbs differ.
    """
    if pred_a == pred_b:
        return True
    for group in _PREDICATE_GROUPS.values():
        if pred_a in group and pred_b in group:
            return True
    return False


class GentnerStructureMapping:
    """Algorithm 2: Gentner structure mapping (DR-20).
    
    Per Dedre Gentner (1983): good analogies transfer relational
    structure (causal chains), not surface features (shared attributes).
    
    Instead of comparing A ↔ X (surface), compare:
        A → B → C → D against X → Y → Z → W
    and score by structural overlap (systematicity).
    """
    
    @staticmethod
    def find_analogous_chains(graph: DiscoveryGraph, min_chain_length: int = 2) -> List[Dict[str, Any]]:
        """Find structurally analogous chains in the graph.
        
        Returns chains that share relational structure but connect
        different entities.
        
        Per cycle 64 (Gentner rewrite): uses chain indexing by
        (length, edge_type_sequence) to achieve O(n log n) instead of O(n²).
        Chains are grouped by structural signature, and only chains with
        the same signature are compared. This avoids the O(chains²) pairwise
        comparison that timed out at 631 edges (cycle 63).
        """
        # Step 1: Extract all chains of length >= min_chain_length
        # Per cycle 54: search ALL subgraphs (not just MECHANISM)
        chains = []
        for subgraph in graph._subgraphs.values():
            if not hasattr(subgraph, 'edges'):
                continue
            for start_node in subgraph.nodes:
                visited = set()
                queue = [(start_node, [start_node])]
                while queue:
                    current, path = queue.pop(0)
                    if len(path) >= min_chain_length:
                        chains.append(path)
                    if current in visited:
                        continue
                    visited.add(current)
                    for edge in subgraph.edges:
                        if edge.source == current and edge.target not in visited:
                            queue.append((edge.target, path + [edge.target]))
        
        # Step 2: Compute structural signature for each chain
        # Signature = (length, tuple(edge_type_sequence))
        # Chains with the same signature are structurally similar candidates
        from collections import defaultdict
        chain_signatures = []  # list of (signature, chain, edge_types)
        for chain in chains:
            edge_types = _edge_type_sequence(graph, chain)
            if not edge_types:
                continue  # invalid chain (missing edges)
            signature = (len(chain), tuple(edge_types))
            chain_signatures.append((signature, chain, edge_types))
        
        # Step 3: Group chains by signature (O(n) with dict)
        groups = defaultdict(list)
        for sig, chain, edge_types in chain_signatures:
            groups[sig].append((chain, edge_types))
        
        # Step 4: Compare only within groups (O(k²) per group, where k = group size)
        # This is O(sum(k²)) instead of O(n²). For a sparse graph with many
        # distinct signatures, sum(k²) << n².
        analogies = []
        for sig, group_chains in groups.items():
            if len(group_chains) < 2:
                continue  # need ≥2 chains with same signature to find analogies
            
            # Compare within this group only
            for i in range(len(group_chains)):
                for j in range(i + 1, len(group_chains)):
                    chain_a = group_chains[i][0]
                    chain_b = group_chains[j][0]
                    edge_types_a = group_chains[i][1]
                    edge_types_b = group_chains[j][1]

                    # Same length (guaranteed by grouping)
                    # Check no shared nodes (different domains)
                    shared = set(chain_a) & set(chain_b)
                    if len(shared) == 0:
                        # Per cycle 141 (auditor fix): systematicity was hardcoded
                        # to 1.0 because chains are pre-grouped by signature. This
                        # produced 215K+ noise analogies with identical scores.
                        # Fix: compute actual partial overlap — the fraction of
                        # edge types that match at corresponding positions, plus
                        # a node-similarity bonus for chains with similar node
                        # types (not just same edge signature).
                        matching_edges = sum(1 for a, b in zip(edge_types_a, edge_types_b) if a == b)
                        edge_overlap = matching_edges / len(edge_types_a) if edge_types_a else 0.0

                        # Per cycle 158 (Test 5 fix): RELATIONAL structure mapping.
                        # The auditor said "edge-type-sequence + no-shared-nodes is
                        # a similarity proxy, not relational structure mapping."
                        # The fix: compare actual PREDICATES (the direction field:
                        # "causes", "enables", "determines"), not just edge layer
                        # types (mechanism, influence, etc.).
                        # Gentner's structure mapping theory: analogies are about
                        # relational predicates, not attributes. Two chains are
                        # analogous if they share the same RELATIONS in the same
                        # order, connecting different entities.
                        predicate_overlap = 0.0
                        try:
                            preds_a = _get_edge_predicates(graph, chain_a)
                            preds_b = _get_edge_predicates(graph, chain_b)
                            if preds_a and preds_b:
                                matching_preds = sum(1 for a, b in zip(preds_a, preds_b)
                                                     if a == b or _predicates_similar(a, b))
                                predicate_overlap = matching_preds / len(preds_a)
                        except Exception:
                            predicate_overlap = 0.0

                        # Node similarity: check if nodes at corresponding positions
                        # share type information (not identity — they're in different
                        # domains). This distinguishes meaningful analogies from
                        # arbitrary same-signature pairs.
                        node_type_overlap = 0.0
                        try:
                            for na, nb in zip(chain_a, chain_b):
                                ta = graph.get_node(na) or {}
                                tb = graph.get_node(nb) or {}
                                if ta.get("type") == tb.get("type"):
                                    node_type_overlap += 1.0
                            node_type_overlap = node_type_overlap / len(chain_a) if chain_a else 0.0
                        except Exception:
                            node_type_overlap = 0.0

                        # Systematicity = weighted combination of edge overlap,
                        # predicate overlap, and node type overlap.
                        # Per cycle 158: predicate_overlap is the Gentner-specific
                        # component — it measures whether the actual RELATIONS
                        # (not just edge layer types) match between chains.
                        systematicity = round(
                            0.3 * edge_overlap +
                            0.4 * predicate_overlap +
                            0.3 * node_type_overlap, 4)

                        # Only keep analogies with meaningful overlap (not noise)
                        if systematicity >= 0.3:
                            analogies.append({
                                "chain_a": chain_a,
                                "chain_b": chain_b,
                                "systematicity": systematicity,
                                "edge_types_a": edge_types_a,
                                "edge_types_b": edge_types_b,
                                "description": f"Structural analogy: {' → '.join(chain_a)} vs {' → '.join(chain_b)}"
                            })
        
        return analogies


class AltshullerContradictionSearch:
    """Algorithm 3: Altshuller contradiction search (DR-20).

    Per Genrich Altshuller (TRIZ): contradictions exist when improving
    one parameter worsens another. Resolution is the core of invention.
    Search the graph for contradictions and find analogous resolutions.

    Per cycle 147 (auditor Test 6 fix): added the 40 TRIZ inventive
    principles and a resolution selector. The auditor found that
    'resolution is always None — identifies, never resolves.' Now
    each contradiction gets a TRIZ principle recommendation based on
    the contradiction matrix (which principle resolves which pair of
    conflicting parameters).
    """

    # The 40 TRIZ Inventive Principles (Altshuller, 1984)
    TRIZ_PRINCIPLES = {
        1: "Segmentation — divide an object into independent parts",
        2: "Taking out — separate the interfering part or property",
        3: "Local quality — make each part perform in optimal conditions",
        4: "Asymmetry — change symmetric to asymmetric",
        5: "Merging — combine similar objects or operations",
        6: "Universality — make a part perform multiple functions",
        7: "Nested doll — contain one object inside another",
        8: "Anti-weight — counteract weight with lift/buoyancy",
        9: "Preliminary anti-action — pre-stress or pre-load opposite to undesired",
        10: "Preliminary action — perform required action beforehand",
        11: "Beforehand cushioning — prepare emergency measures",
        12: "Equipotentiality — eliminate need to raise/lower",
        13: "The other way round — invert the action or object",
        14: "Spheroidality — use curves/rotary motion instead of linear",
        15: "Dynamicity — make object adaptable or mobile",
        16: "Partial or excessive actions — do slightly less/more than ideal",
        17: "Another dimension — use a different axis/layer",
        18: "Mechanical vibration — use oscillation/ultrasound/resonance",
        19: "Periodic action — use pulses instead of continuous",
        20: "Continuity of useful action — eliminate idle time",
        21: "Skipping — do harmful action fast to avoid harm",
        22: "Convert harm into benefit — use the negative for positive",
        23: "Feedback — use feedback to improve control",
        24: "Intermediary — use an intermediary carrier/substance",
        25: "Self-service — make the object serve/repair itself",
        26: "Copying — use copies instead of fragile originals",
        27: "Cheap short-lived objects — replace with disposable",
        28: "Mechanics substitution — replace mechanical with sensory/optical/acoustic",
        29: "Pneumatics/hydraulics — use gas/liquid instead of solid",
        30: "Flexible shells/thin films — use flexibility instead of rigidity",
        31: "Porous materials — add pores/cavities to reduce weight",
        32: "Color changes — change color/transparency/opacity",
        33: "Homogeneity — make interacting objects same material",
        34: "Discarding/recovering — discard used parts, recover after use",
        35: "Parameter changes — change physical state/density/conductivity",
        36: "Phase transitions — use effects from phase changes (latent heat, volume change)",
        37: "Thermal expansion — use expansion/contraction from heat",
        38: "Strong oxidants — use enriched oxygen/ozone",
        39: "Inert atmosphere — use vacuum/inert gas to prevent harm",
        40: "Composite materials — use composites instead of homogeneous",
    }

    # Simplified contradiction matrix: maps (improve_type, worsen_type) → [principle numbers]
    # Based on Altshuller's 39×39 matrix (simplified to common engineering pairs)
    CONTRADICTION_MATRIX = {
        # (improve, worsen) → recommended principles
        ("strength", "weight"): [40, 26, 27, 1],  # composites, copying, cheap disposable, segmentation
        ("strength", "complexity"): [1, 35, 29, 25],  # segmentation, parameter change, pneumatics, self-service
        ("temperature", "energy"): [25, 36, 19, 35],  # self-service, phase transition, periodic, parameter change
        ("power", "weight"): [35, 10, 2, 34],  # parameter change, preliminary, take out, discarding
        ("power", "heat"): [36, 35, 21, 39],  # phase transition, parameter change, skipping, inert atmosphere
        ("speed", "accuracy"): [10, 35, 16, 28],  # preliminary, parameter change, excessive, mechanics substitution
        ("efficiency", "complexity"): [35, 1, 5, 15],  # parameter change, segmentation, merging, dynamicity
        ("efficiency", "cost"): [35, 10, 16, 25],  # parameter change, preliminary, excessive, self-service
        ("durability", "weight"): [40, 26, 27, 1],  # composites, copying, disposable, segmentation
        ("durability", "complexity"): [1, 35, 29, 15],  # segmentation, parameter change, pneumatics, dynamicity
        ("conductivity", "strength"): [35, 33, 40, 1],  # parameter change, homogeneity, composites, segmentation
        ("conductivity", "weight"): [35, 31, 40, 28],  # parameter change, porous, composites, mechanics substitution
    }

    @staticmethod
    def _resolve_contradiction(improve: str, worsen: str, source: str) -> Optional[str]:
        """Select a TRIZ principle to resolve a contradiction.

        Per cycle 147: replaces 'resolution = None' with actual TRIZ
        principle recommendation. Uses the contradiction matrix to select
        the most applicable principle, with keyword matching to find the
        closest (improve, worsen) pair.

        Per cycle 174: each resolution now includes a CONCRETE physical
        implementation suggestion, not just a principle name.
        """
        # Per cycle 179: add step-by-step implementation procedures
        IMPLEMENTATION_STEPS = {
            40: ["1. Identify the load-bearing component", "2. Select fiber material (carbon/glass/Kevlar)", "3. Select matrix (epoxy/polyimide)", "4. Design layup orientation", "5. Manufacture via prepreg/autoclave"],
            35: ["1. Identify the parameter to change", "2. Determine available phase states (solid/liquid/gas/plasma)", "3. Select the state that improves the target without worsening the other", "4. Implement the phase change (e.g., add porosity via foaming)"],
            1: ["1. Identify the conflicting functions", "2. Determine which function needs each property", "3. Design separate modules for each function", "4. Add interface between modules"],
            33: ["1. Identify the two interacting components", "2. Determine their current materials", "3. Select a common material that satisfies both functions", "4. Redesign both components in the common material"],
            31: ["1. Identify the heavy component", "2. Determine if internal volume is available", "3. Design hollow/porous structure", "4. Verify structural integrity is maintained"],
            10: ["1. Identify the parameter that needs pre-conditioning", "2. Determine the desired initial state", "3. Design a pre-conditioning mechanism (pre-stress/pre-heat/pre-load)", "4. Integrate into the system startup sequence"],
            36: ["1. Identify the thermal management need", "2. Select a PCM with appropriate transition temperature", "3. Calculate required PCM mass from latent heat", "4. Integrate PCM into the thermal path"],
            25: ["1. Identify the parameter to self-regulate", "2. Find a physical effect that responds to that parameter", "3. Design a feedback mechanism (e.g., thermal expansion → valve)", "4. Calibrate the self-regulation threshold"],
        }

        # Per cycle 174: concrete implementation suggestions per principle
        CONCRETE_IMPLEMENTATIONS = {
            40: "Use fiber-reinforced composites (e.g., carbon fiber + polymer matrix) to increase strength without adding weight",
            35: f"Change the material phase (e.g., solid to porous, crystalline to amorphous) to modify {improve} without affecting {worsen}",
            1: "Separate the conflicting functions into different modules or layers (e.g., multilayer coating)",
            33: "Use the same base material for both components (e.g., both parts aluminum) to eliminate interface mismatch",
            31: "Add porosity or hollow structures to reduce weight while maintaining structural integrity",
            10: "Pre-condition the system before operation (e.g., pre-stress, pre-heat, pre-load) to shift the operating point",
            36: "Use a phase-change material (e.g., PCM) to exploit latent heat for thermal management without energy input",
            25: "Design the system to self-regulate (e.g., thermal expansion actuates a valve) for automatic maintenance",
        }

        improve_lower = improve.lower()
        worsen_lower = worsen.lower()

        # Try to match against the contradiction matrix
        for (imp_key, wor_key), principles in AltshullerContradictionSearch.CONTRADICTION_MATRIX.items():
            if imp_key in improve_lower and wor_key in worsen_lower:
                # Return the top recommended principle
                top_principle = principles[0]
                desc = AltshullerContradictionSearch.TRIZ_PRINCIPLES.get(top_principle, "unknown")
                impl = CONCRETE_IMPLEMENTATIONS.get(top_principle, "")
                steps = IMPLEMENTATION_STEPS.get(top_principle, [])
                steps_str = " | ".join(steps) if steps else ""
                return f"TRIZ Principle {top_principle}: {desc}. Implementation: {impl}. Steps: {steps_str}"

        if "tradeoff" in worsen_lower or "via" in worsen_lower:
            impl = CONCRETE_IMPLEMENTATIONS.get(33, "")
            steps = IMPLEMENTATION_STEPS.get(33, [])
            steps_str = " | ".join(steps) if steps else ""
            return f"TRIZ Principle 33: Homogeneity — {impl}. Steps: {steps_str}"
        else:
            impl = CONCRETE_IMPLEMENTATIONS.get(35, "")
            steps = IMPLEMENTATION_STEPS.get(35, [])
            steps_str = " | ".join(steps) if steps else ""
            return f"TRIZ Principle 35: Parameter changes — {impl}. Steps: {steps_str}"

    @staticmethod
    def find_contradictions(graph: DiscoveryGraph,
                             causal_graph: Optional[Any] = None) -> List[Contradiction]:
        """Find contradictions in the graph.

        Two types of contradictions (TRIZ):
        Type 1 (same-source): Edge A→B "increases" AND Edge A→C "decreases"
          — changing one parameter improves one thing but worsens another
        Type 2 (cross-source): Edge A→C "increases" AND Edge B→C "decreases"
          — two different materials have opposite effects on the same property
          — this is a materials tradeoff: use A for improvement, but B (already
            in the system) causes degradation

        Per cycle 55 (DR-25, F-061 closure): if causal_graph is provided,
        exclude CONTRADICTED and ASSOCIATIVE edges from contradiction detection.
        Only VERIFIED + ASSERTED edges participate — this stops keyword-match
        edges from being counted as contradictions.

        Per cycle 147: each contradiction now gets a TRIZ principle resolution
        (was always None before).
        """
        contradictions = []
        # Build a set of (source, target) pairs to exclude (CONTRADICTED/ASSOCIATIVE)
        excluded_pairs = set()
        if causal_graph is not None:
            from invention_compiler.causal_graph import EdgeTier
            for edge in causal_graph.edges:
                if edge.tier in (EdgeTier.CONTRADICTED, EdgeTier.ASSOCIATIVE):
                    excluded_pairs.add((edge.source, edge.target))
        # Look for nodes with both "increases" and "decreases" outgoing edges
        node_effects = {}  # node → {target → direction}
        for subgraph in graph._subgraphs.values():
            for edge in subgraph.edges:
                # Skip excluded edges (CONTRADICTED/ASSOCIATIVE) per DR-25
                if (edge.source, edge.target) in excluded_pairs:
                    continue
                if edge.source not in node_effects:
                    node_effects[edge.source] = {}
                direction = "unknown"
                # Check direction field first (populated by edge extractor)
                if hasattr(edge, 'direction') and edge.direction:
                    direction = edge.direction
                    # Liberal interpretation for contradiction detection:
                    # causes/enables/produces = increases (A→B means increasing A increases B)
                    if direction in ("causes", "enables", "produces"):
                        direction = "increases"
                # Also check metadata for "increases"/"decreases"
                elif "increases" in str(edge.metadata).lower():
                    direction = "increases"
                elif "decreases" in str(edge.metadata).lower():
                    direction = "decreases"
                node_effects[edge.source][edge.target] = direction

        # Type 1: Same-source contradictions (changing X improves Y but worsens Z)
        for source, effects in node_effects.items():
            increases = [t for t, d in effects.items() if d == "increases"]
            decreases = [t for t, d in effects.items() if d == "decreases"]
            for inc in increases:
                for dec in decreases:
                    resolution = AltshullerContradictionSearch._resolve_contradiction(inc, dec, source)
                    contradictions.append(Contradiction(
                        contradiction_id=f"CONTR-T1-{source}-{inc}-{dec}",
                        improve=inc,
                        worsen=dec,
                        mechanism=f"Changing {source} improves {inc} but worsens {dec}",
                        resolution=resolution,
                    ))

        # Type 2: Cross-source contradictions (A increases C, B decreases C)
        # Build reverse map: target → {source → direction}
        target_effects = {}  # target → {source → direction}
        for source, effects in node_effects.items():
            for target, direction in effects.items():
                if target not in target_effects:
                    target_effects[target] = {}
                target_effects[target][source] = direction

        for target, sources in target_effects.items():
            increasers = [s for s, d in sources.items() if d == "increases"]
            decreasers = [s for s, d in sources.items() if d == "decreases"]
            for inc_src in increasers:
                for dec_src in decreasers:
                    resolution = AltshullerContradictionSearch._resolve_contradiction(
                        f"{target} (via {inc_src})", f"{target} (via {dec_src})", inc_src)
                    contradictions.append(Contradiction(
                        contradiction_id=f"CONTR-T2-{inc_src}-{dec_src}-{target}",
                        improve=f"{target} (via {inc_src})",
                        worsen=f"{target} (via {dec_src})",
                        mechanism=f"{inc_src} increases {target} but {dec_src} decreases it — materials tradeoff",
                        resolution=resolution,
                    ))

        return contradictions
