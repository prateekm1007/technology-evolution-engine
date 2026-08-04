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
    def search(graph: DiscoveryGraph, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Search for undiscovered bridges in the graph.
        
        Returns a list of {a, b, c, score} where a→b and b→c exist
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
                        bridges.append({
                            "a": a,
                            "b": b,
                            "c": c,
                            "score": 1.0,  # simple score: exists = 1.0
                            "description": f"Undiscovered bridge: {a} → {b} → {c} (but {a} → {c} not connected)"
                        })
        
        return bridges


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
        """
        # Extract all chains of length >= min_chain_length
        chains = []
        for subgraph in graph._subgraphs.values():
            if not isinstance(subgraph, MechanismGraph):
                continue
            # BFS from each node
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
        
        # Compare chains for structural similarity
        analogies = []
        for i, chain_a in enumerate(chains):
            for j, chain_b in enumerate(chains):
                if i >= j:
                    continue
                # Same length = structural match candidate
                if len(chain_a) == len(chain_b):
                    # Check no shared nodes (different domains)
                    shared = set(chain_a) & set(chain_b)
                    if len(shared) == 0:
                        analogies.append({
                            "chain_a": chain_a,
                            "chain_b": chain_b,
                            "systematicity": len(chain_a) / max(len(chain_a), 1),
                            "description": f"Structural analogy: {' → '.join(chain_a)} vs {' → '.join(chain_b)}"
                        })
        
        return analogies


class AltshullerContradictionSearch:
    """Algorithm 3: Altshuller contradiction search (DR-20).
    
    Per Genrich Altshuller (TRIZ): contradictions exist when improving
    one parameter worsens another. Resolution is the core of invention.
    Search the graph for contradictions and find analogous resolutions.
    """
    
    @staticmethod
    def find_contradictions(graph: DiscoveryGraph) -> List[Contradiction]:
        """Find contradictions in the graph.
        
        A contradiction exists when:
          - Edge A→B says "increases"
          - Edge A→C says "decreases"
          - B and C are both desirable
        """
        contradictions = []
        # Look for nodes with both "increases" and "decreases" outgoing edges
        node_effects = {}  # node → {target → direction}
        for subgraph in graph._subgraphs.values():
            for edge in subgraph.edges:
                if edge.source not in node_effects:
                    node_effects[edge.source] = {}
                direction = "unknown"
                # Check direction field first (populated by edge extractor)
                if hasattr(edge, 'direction') and edge.direction:
                    direction = edge.direction
                # Also check metadata for "increases"/"decreases"
                elif "increases" in str(edge.metadata).lower():
                    direction = "increases"
                elif "decreases" in str(edge.metadata).lower():
                    direction = "decreases"
                node_effects[edge.source][edge.target] = direction
        
        for source, effects in node_effects.items():
            increases = [t for t, d in effects.items() if d == "increases"]
            decreases = [t for t, d in effects.items() if d == "decreases"]
            for inc in increases:
                for dec in decreases:
                    contradictions.append(Contradiction(
                        contradiction_id=f"CONTR-{source}-{inc}-{dec}",
                        improve=inc,
                        worsen=dec,
                        mechanism=f"Changing {source} improves {inc} but worsens {dec}",
                        resolution=None,
                    ))
        
        return contradictions
