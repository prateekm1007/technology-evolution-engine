#!/usr/bin/env python3
"""
discovery_substrate.py — Scientific Discovery Substrate

Per CEO Directive: build the infrastructure for a scientific discovery
loop, NOT the discovery engine itself.

This module defines the core data structures that a discovery engine
would operate on. No agents. No benchmarks. No discovery logic.
Just the auditable substrate.

The objects defined here:
  - DiscoveryCase: the atomic unit of a discovery attempt
  - Mechanism: a causal explanation node
  - TransferHypothesis: a cross-domain transfer candidate
  - Hypothesis: a testable scientific claim
  - Prediction: a falsifiable observable consequence
  - ExperimentProposal: a proposed test
  - DiscoveryFailure: a recorded failure with reusable lessons
  - PriorArtAssessment: a bounded novelty claim
  - ProvenanceNode / ProvenanceEdge: evidence chain
  - ExperimentManifest: reproducibility record
  - EpistemicState: the state machine for knowledge confidence

Key principle: knowledge and hypotheses are NEVER conflated.
HYPOTHESIZED can never auto-promote to ESTABLISHED.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
from pathlib import Path


# ============================================================================
# EPISTEMIC STATES — the confidence ladder
# ============================================================================

class EpistemicState(str, Enum):
    """Epistemic states for knowledge objects.
    
    State transitions require evidence. The system must NEVER
    auto-promote HYPOTHESIZED → ESTABLISHED.
    
    Valid transitions:
        OBSERVED → EXTRACTED → INFERRED → HYPOTHESIZED → PREDICTED
        → EXPERIMENTALLY_SUPPORTED → REPLICATED → ESTABLISHED
        
        Any state → REFUTED (failure is always possible)
        Any state → UNKNOWN (when evidence is insufficient)
    """
    OBSERVED = "OBSERVED"
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    HYPOTHESIZED = "HYPOTHESIZED"
    PREDICTED = "PREDICTED"
    EXPERIMENTALLY_SUPPORTED = "EXPERIMENTALLY_SUPPORTED"
    REPLICATED = "REPLICATED"
    ESTABLISHED = "ESTABLISHED"
    REFUTED = "REFUTED"
    UNKNOWN = "UNKNOWN"


# Valid state transitions (from → {allowed targets})
VALID_TRANSITIONS: Dict[EpistemicState, set] = {
    EpistemicState.OBSERVED: {EpistemicState.EXTRACTED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.EXTRACTED: {EpistemicState.INFERRED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.INFERRED: {EpistemicState.HYPOTHESIZED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.HYPOTHESIZED: {EpistemicState.PREDICTED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.PREDICTED: {EpistemicState.EXPERIMENTALLY_SUPPORTED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.EXPERIMENTALLY_SUPPORTED: {EpistemicState.REPLICATED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.REPLICATED: {EpistemicState.ESTABLISHED, EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.ESTABLISHED: {EpistemicState.REFUTED, EpistemicState.UNKNOWN},
    EpistemicState.REFUTED: set(),  # terminal
    EpistemicState.UNKNOWN: {s for s in EpistemicState if s != EpistemicState.UNKNOWN},
}


# ============================================================================
# PROVENANCE — every object traces to evidence
# ============================================================================

@dataclass
class ProvenanceNode:
    """A node in the provenance graph."""
    node_id: str
    node_type: str  # source_passage, mechanism, hypothesis, prediction, experiment, result, etc.
    content_hash: str  # SHA-256 of the content this node represents
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProvenanceEdge:
    """A directed edge in the provenance graph."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str  # DERIVES_FROM, SUPPORTS, CONTRADICTS, REFINES, etc.
    evidence: str  # description of why this edge exists
    actor: str  # who/what created this edge
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ProvenanceGraph:
    """A traversable provenance graph.
    
    A future reviewer should be able to ask:
        'Why does the system believe this?'
    and traverse the answer all the way to primary evidence.
    """
    def __init__(self):
        self.nodes: Dict[str, ProvenanceNode] = {}
        self.edges: List[ProvenanceEdge] = []
    
    def add_node(self, node: ProvenanceNode) -> None:
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: ProvenanceEdge) -> None:
        self.edges.append(edge)
    
    def trace_back(self, node_id: str) -> List[ProvenanceNode]:
        """Trace all ancestors of a node (why does the system believe this?)."""
        visited = set()
        result = []
        self._trace_back_recursive(node_id, visited, result)
        return result
    
    def _trace_back_recursive(self, node_id: str, visited: set, result: list) -> None:
        if node_id in visited:
            return
        visited.add(node_id)
        if node_id in self.nodes:
            result.append(self.nodes[node_id])
        for edge in self.edges:
            if edge.target_node_id == node_id and edge.source_node_id not in visited:
                self._trace_back_recursive(edge.source_node_id, visited, result)
    
    def to_dict(self) -> Dict:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }


# ============================================================================
# MECHANISM — causal explanation node
# ============================================================================

class MechanismNodeType(str, Enum):
    SYSTEM = "system"
    MATERIAL = "material"
    PROCESS = "process"
    PROPERTY = "property"
    CONDITION = "condition"
    CONSTRAINT = "constraint"
    MECHANISM = "mechanism"
    EFFECT = "effect"
    MEASUREMENT = "measurement"
    FAILURE_MODE = "failure_mode"
    DESIGN_VARIABLE = "design_variable"


class MechanismEdgeType(str, Enum):
    CAUSES = "CAUSES"
    ENABLES = "ENABLES"
    INHIBITS = "INHIBITS"
    MODULATES = "MODULATES"
    CORRELATES_WITH = "CORRELATES_WITH"
    REQUIRES = "REQUIRES"
    CONSTRAINS = "CONSTRAINS"
    PRODUCES = "PRODUCES"
    FAILS_UNDER = "FAILS_UNDER"
    TRANSFERS_TO = "TRANSFERS_TO"


@dataclass
class MechanismNode:
    """A node in the mechanism graph."""
    node_id: str
    node_type: MechanismNodeType
    label: str
    description: str = ""
    epistemic_state: EpistemicState = EpistemicState.OBSERVED
    provenance: List[str] = field(default_factory=list)  # source references
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["node_type"] = self.node_type.value
        d["epistemic_state"] = self.epistemic_state.value
        return d


@dataclass
class MechanismEdge:
    """A directed edge in the mechanism graph."""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: MechanismEdgeType
    confidence: float = 0.0  # 0-1, but NEVER collapse provenance into just this
    evidence: List[str] = field(default_factory=list)  # source passages
    epistemic_state: EpistemicState = EpistemicState.OBSERVED
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["edge_type"] = self.edge_type.value
        d["epistemic_state"] = self.epistemic_state.value
        return d


class MechanismGraph:
    """A graph of mechanisms, not just entities.
    
    The eventual discovery engine should primarily operate on mechanisms,
    not on raw entity overlap.
    """
    def __init__(self):
        self.nodes: Dict[str, MechanismNode] = {}
        self.edges: List[MechanismEdge] = []
    
    def add_node(self, node: MechanismNode) -> None:
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: MechanismEdge) -> None:
        self.edges.append(edge)
    
    def get_neighbors(self, node_id: str, edge_type: Optional[MechanismEdgeType] = None) -> List[MechanismNode]:
        """Get neighbors of a node, optionally filtered by edge type."""
        neighbor_ids = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    neighbor_ids.add(edge.target_id)
            elif edge.target_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    neighbor_ids.add(edge.source_id)
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]
    
    def to_dict(self) -> Dict:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
        }


# ============================================================================
# TRANSFER HYPOTHESIS — the missing object from Stage -1
# ============================================================================

@dataclass
class TransferHypothesis:
    """A cross-domain mechanism transfer candidate.
    
    This is the conceptual object that discover_shared_entities() was missing.
    Instead of asking 'do these papers share an entity?', this asks
    'can a mechanism operating under these conditions transfer into
    a different system under these constraints?'
    """
    transfer_id: str
    source_domain: str = ""
    source_mechanism: str = ""
    source_conditions: List[str] = field(default_factory=list)
    target_domain: str = ""
    target_problem: str = ""
    transferred_principle: str = ""
    required_translation: str = ""  # what must change for the transfer to work
    expected_effect: str = ""
    boundary_conditions: List[str] = field(default_factory=list)  # where it WON'T work
    failure_conditions: List[str] = field(default_factory=list)
    testable_prediction: str = ""
    epistemic_state: EpistemicState = EpistemicState.HYPOTHESIZED
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["epistemic_state"] = self.epistemic_state.value
        d["provenance"] = self.provenance.to_dict()
        return d


# ============================================================================
# HYPOTHESIS — testable scientific claim
# ============================================================================

@dataclass
class Hypothesis:
    """A testable scientific hypothesis.
    
    Every hypothesis must include a falsifier — what observation
    would prove it wrong. This prevents unfalsifiable prose.
    """
    hypothesis_id: str
    claim: str  # falsifiable statement, not a number
    mechanism: str  # causal explanation
    evidence: List[str] = field(default_factory=list)  # supporting evidence references
    assumptions: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)  # prediction IDs
    expected_failure_modes: List[str] = field(default_factory=list)
    novelty_rationale: str = ""  # why this might be new
    testability: str = ""  # how it could be tested
    falsifier: str = ""  # what observation would prove it wrong
    epistemic_state: EpistemicState = EpistemicState.HYPOTHESIZED
    parent_hypothesis_ids: List[str] = field(default_factory=list)
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["epistemic_state"] = self.epistemic_state.value
        d["provenance"] = self.provenance.to_dict()
        return d


# ============================================================================
# PREDICTION — falsifiable observable consequence
# ============================================================================

@dataclass
class Prediction:
    """A falsifiable prediction derived from a hypothesis.
    
    The critical field is 'falsifier' — what observation would
    prove the hypothesis wrong.
    """
    prediction_id: str
    hypothesis_id: str
    observable: str = ""  # what to measure
    expected_direction: str = ""  # increase, decrease, appear, disappear, etc.
    expected_magnitude: str = ""  # estimated size of effect
    conditions: List[str] = field(default_factory=list)  # under what conditions
    baseline: str = ""  # comparison baseline
    falsifier: str = ""  # what observation would refute the hypothesis
    uncertainty: float = 0.0  # 0-1
    epistemic_state: EpistemicState = EpistemicState.PREDICTED
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["epistemic_state"] = self.epistemic_state.value
        return d


# ============================================================================
# EXPERIMENT PROPOSAL — proposed test
# ============================================================================

@dataclass
class ExperimentProposal:
    """A proposed experiment to test a hypothesis.
    
    The engine should eventually optimize experiments not merely for
    expected success but for expected information gain per unit cost/time.
    """
    experiment_id: str
    hypothesis_id: str
    objective: str
    independent_variables: List[str] = field(default_factory=list)
    dependent_variables: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    baseline: str = ""
    procedure: str = ""
    expected_result: str = ""
    falsification_condition: str = ""  # what result would falsify
    sample_requirements: str = ""
    safety_constraints: List[str] = field(default_factory=list)
    estimated_cost: str = ""  # not a number yet — premature optimization
    estimated_duration: str = ""
    information_gain: str = ""  # qualitative for now
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# EXPERIMENT MANIFEST — reproducibility
# ============================================================================

@dataclass
class ExperimentManifest:
    """Content-addressed reproducibility record.
    
    Every discovery case should be reproducible from this manifest.
    """
    code_sha: str
    knowledge_sha: str
    model: str = ""
    model_version: str = ""
    prompt_sha: str = ""
    input_sha: str = ""
    configuration_sha: str = ""
    environment: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    random_seed: Optional[int] = None
    tools: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_hash(self) -> str:
        """Content-addressed hash of the manifest."""
        d = self.to_dict()
        # Remove timestamp from hash computation (it changes each time)
        d.pop("timestamp", None)
        content = json.dumps(d, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# DISCOVERY FAILURE — reusable negative knowledge
# ============================================================================

class FailureType(str, Enum):
    RECOGNITION_LEAKAGE = "RECOGNITION_LEAKAGE"
    SEMANTIC_LEAKAGE = "SEMANTIC_LEAKAGE"
    PRIOR_ART = "PRIOR_ART"
    UNSUPPORTED_MECHANISM = "UNSUPPORTED_MECHANISM"
    NON_TESTABLE = "NON_TESTABLE"
    FAILED_PREDICTION = "FAILED_PREDICTION"
    EXPERIMENTAL_FAILURE = "EXPERIMENTAL_FAILURE"
    REPLICATION_FAILURE = "REPLICATION_FAILURE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DOMAIN_TRANSFER_FAILURE = "DOMAIN_TRANSFER_FAILURE"
    CONTROL_OUTPERFORMED = "CONTROL_OUTPERFORMED"


@dataclass
class DiscoveryFailure:
    """A recorded failure with reusable lessons.
    
    Do not hide failures. A world-class discovery engine should become
    better partly by accumulating knowledge about what kinds of ideas
    do not work.
    """
    failure_id: str
    failure_type: FailureType
    hypothesis_id: str = ""
    case_id: str = ""
    why_rejected: str = ""
    evidence: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    failure_mode: str = ""
    reusable_lesson: str = ""  # what to avoid next time
    related_hypotheses: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["failure_type"] = self.failure_type.value
        return d


# ============================================================================
# PRIOR ART ASSESSMENT — bounded novelty claim
# ============================================================================

class NoveltyStatus(str, Enum):
    NOVEL_AS_OF_CUTOFF = "NOVEL_AS_OF_CUTOFF"
    PRIOR_ART_FOUND = "PRIOR_ART_FOUND"
    PARTIAL_PRECEDENT = "PARTIAL_PRECEDENT"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass
class PriorArtAssessment:
    """A bounded novelty claim.
    
    The service must never claim 'this has never existed.'
    It can only make bounded evidence-based claims.
    """
    assessment_id: str
    hypothesis_id: str
    status: NoveltyStatus = NoveltyStatus.NOT_EVALUATED
    search_scope: List[str] = field(default_factory=list)  # databases searched
    queries: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)  # sources screened
    matched_prior_art: List[str] = field(default_factory=list)
    similarity: str = ""  # qualitative for now
    review_required: bool = True
    confidence: float = 0.0
    cutoff: str = ""  # date cutoff
    reviewer: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ============================================================================
# DISCOVERY CASE — the atomic unit
# ============================================================================

@dataclass
class DiscoveryCase:
    """The atomic unit of a discovery attempt.
    
    Every discovery candidate is a durable, immutable evidence object.
    Supports incomplete hypotheses — scientific discovery frequently
    begins with 'something here might matter.'
    """
    case_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engine_version: str = ""
    knowledge_snapshot: str = ""  # hash of knowledge state
    input_sources: List[str] = field(default_factory=list)
    input_domains: List[str] = field(default_factory=list)
    mechanisms: List[str] = field(default_factory=list)  # mechanism node IDs
    constraints: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    candidate_relationship: str = ""
    candidate_mechanism: str = ""
    candidate_hypothesis: str = ""  # hypothesis ID
    predictions: List[str] = field(default_factory=list)  # prediction IDs
    proposed_experiment: str = ""  # experiment ID
    prior_art_status: str = NoveltyStatus.NOT_EVALUATED.value
    novelty_status: str = NoveltyStatus.NOT_EVALUATED.value
    validation_status: EpistemicState = EpistemicState.UNKNOWN
    evidence: List[str] = field(default_factory=list)
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    parent_cases: List[str] = field(default_factory=list)
    derived_cases: List[str] = field(default_factory=list)
    failure_state: Optional[str] = None  # failure ID if failed
    manifest: Optional[ExperimentManifest] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["validation_status"] = self.validation_status.value if isinstance(self.validation_status, EpistemicState) else self.validation_status
        d["provenance"] = self.provenance.to_dict()
        if self.manifest:
            d["manifest"] = self.manifest.to_dict()
        return d


# ============================================================================
# DISCOVERY STATE MACHINE — auditable state transitions
# ============================================================================

class DiscoveryState(str, Enum):
    """States in the discovery lifecycle."""
    RAW_EVIDENCE = "RAW_EVIDENCE"
    STRUCTURED_KNOWLEDGE = "STRUCTURED_KNOWLEDGE"
    MECHANISM = "MECHANISM"
    TRANSFER_HYPOTHESIS = "TRANSFER_HYPOTHESIS"
    CANDIDATE_DISCOVERY = "CANDIDATE_DISCOVERY"
    GATE_A = "GATE_A"
    GATE_B = "GATE_B"
    GATE_C = "GATE_C"
    TESTABLE_HYPOTHESIS = "TESTABLE_HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    RESULT = "RESULT"
    REPLICATION = "REPLICATION"
    VALIDATED_DISCOVERY = "VALIDATED_DISCOVERY"
    INVENTION_CANDIDATE = "INVENTION_CANDIDATE"
    FAILED = "FAILED"


DISCOVERY_TRANSITIONS: Dict[DiscoveryState, set] = {
    DiscoveryState.RAW_EVIDENCE: {DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.FAILED},
    DiscoveryState.STRUCTURED_KNOWLEDGE: {DiscoveryState.MECHANISM, DiscoveryState.FAILED},
    DiscoveryState.MECHANISM: {DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.FAILED},
    DiscoveryState.TRANSFER_HYPOTHESIS: {DiscoveryState.CANDIDATE_DISCOVERY, DiscoveryState.FAILED},
    DiscoveryState.CANDIDATE_DISCOVERY: {DiscoveryState.GATE_A, DiscoveryState.FAILED},
    DiscoveryState.GATE_A: {DiscoveryState.GATE_B, DiscoveryState.FAILED},
    DiscoveryState.GATE_B: {DiscoveryState.GATE_C, DiscoveryState.FAILED},
    DiscoveryState.GATE_C: {DiscoveryState.TESTABLE_HYPOTHESIS, DiscoveryState.FAILED},
    DiscoveryState.TESTABLE_HYPOTHESIS: {DiscoveryState.EXPERIMENT, DiscoveryState.FAILED},
    DiscoveryState.EXPERIMENT: {DiscoveryState.RESULT, DiscoveryState.FAILED},
    DiscoveryState.RESULT: {DiscoveryState.REPLICATION, DiscoveryState.FAILED},
    DiscoveryState.REPLICATION: {DiscoveryState.VALIDATED_DISCOVERY, DiscoveryState.FAILED},
    DiscoveryState.VALIDATED_DISCOVERY: {DiscoveryState.INVENTION_CANDIDATE, DiscoveryState.FAILED},
    DiscoveryState.INVENTION_CANDIDATE: {DiscoveryState.FAILED},  # can still fail
    DiscoveryState.FAILED: set(),  # terminal
}


@dataclass
class StateTransition:
    """A recorded state transition with full audit trail."""
    from_state: DiscoveryState
    to_state: DiscoveryState
    actor: str  # who/what performed the transition
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    code_sha: str = ""  # commit SHA of the code that performed the transition
    evidence: str = ""  # why this transition is justified
    reason: str = ""  # what triggered it
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["from_state"] = self.from_state.value
        d["to_state"] = self.to_state.value
        return d


class DiscoveryStateMachine:
    """Manages state transitions for a discovery case.
    
    Every transition needs: actor, timestamp, code SHA, evidence, reason.
    Invalid transitions raise ValueError.
    """
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.current_state: DiscoveryState = DiscoveryState.RAW_EVIDENCE
        self.history: List[StateTransition] = []
    
    def transition(self, to_state: DiscoveryState, actor: str,
                   code_sha: str = "", evidence: str = "", reason: str = "") -> StateTransition:
        """Attempt a state transition. Raises ValueError if invalid."""
        if to_state not in DISCOVERY_TRANSITIONS.get(self.current_state, set()):
            raise ValueError(
                f"Invalid transition: {self.current_state.value} → {to_state.value}. "
                f"Valid targets from {self.current_state.value}: "
                f"{[s.value for s in DISCOVERY_TRANSITIONS.get(self.current_state, set())]}"
            )
        
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            actor=actor,
            code_sha=code_sha,
            evidence=evidence,
            reason=reason,
        )
        self.history.append(transition)
        self.current_state = to_state
        return transition
    
    def can_transition(self, to_state: DiscoveryState) -> bool:
        return to_state in DISCOVERY_TRANSITIONS.get(self.current_state, set())
    
    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "current_state": self.current_state.value,
            "history": [t.to_dict() for t in self.history],
        }


# ============================================================================
# DISCOVERY LEDGER — append-only, no deletions
# ============================================================================

class DiscoveryLedger:
    """Append-only ledger of all discovery candidates.
    
    No deletion of failures. No silent relabeling.
    A failed candidate remains in the ledger forever.
    """
    def __init__(self):
        self.cases: Dict[str, DiscoveryCase] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.predictions: Dict[str, Prediction] = {}
        self.experiments: Dict[str, ExperimentProposal] = {}
        self.failures: Dict[str, DiscoveryFailure] = {}
        self.prior_art: Dict[str, PriorArtAssessment] = {}
        self.transfers: Dict[str, TransferHypothesis] = {}
        self.mechanisms: Dict[str, MechanismGraph] = {}
        self.state_machines: Dict[str, DiscoveryStateMachine] = {}
    
    def register_case(self, case: DiscoveryCase) -> None:
        self.cases[case.case_id] = case
        self.state_machines[case.case_id] = DiscoveryStateMachine(case.case_id)
    
    def register_hypothesis(self, hyp: Hypothesis) -> None:
        self.hypotheses[hyp.hypothesis_id] = hyp
    
    def register_prediction(self, pred: Prediction) -> None:
        self.predictions[pred.prediction_id] = pred
    
    def register_experiment(self, exp: ExperimentProposal) -> None:
        self.experiments[exp.experiment_id] = exp
    
    def register_failure(self, failure: DiscoveryFailure) -> None:
        self.failures[failure.failure_id] = failure
    
    def register_prior_art(self, assessment: PriorArtAssessment) -> None:
        self.prior_art[assessment.assessment_id] = assessment
    
    def register_transfer(self, transfer: TransferHypothesis) -> None:
        self.transfers[transfer.transfer_id] = transfer
    
    def get_case_history(self, case_id: str) -> List[StateTransition]:
        if case_id in self.state_machines:
            return self.state_machines[case_id].history
        return []
    
    def get_failures_for_hypothesis(self, hypothesis_id: str) -> List[DiscoveryFailure]:
        return [f for f in self.failures.values() if f.hypothesis_id == hypothesis_id]
    
    def get_lineage(self, case_id: str) -> Dict:
        """Get parent and derived cases for lineage tracing."""
        case = self.cases.get(case_id)
        if not case:
            return {}
        return {
            "case_id": case_id,
            "parents": case.parent_cases,
            "derived": case.derived_cases,
        }
    
    def to_dict(self) -> Dict:
        return {
            "cases": {k: v.to_dict() for k, v in self.cases.items()},
            "hypotheses": {k: v.to_dict() for k, v in self.hypotheses.items()},
            "predictions": {k: v.to_dict() for k, v in self.predictions.items()},
            "experiments": {k: v.to_dict() for k, v in self.experiments.items()},
            "failures": {k: v.to_dict() for k, v in self.failures.items()},
            "prior_art": {k: v.to_dict() for k, v in self.prior_art.items()},
            "transfers": {k: v.to_dict() for k, v in self.transfers.items()},
            "state_machines": {k: v.to_dict() for k, v in self.state_machines.items()},
        }


# ============================================================================
# INVENTION CANDIDATE — schema only, no implementation
# ============================================================================

@dataclass
class InventionCandidate:
    """Schema for converting a validated discovery into an invention.
    
    Do NOT implement invention claims yet. Build the schema only.
    """
    invention_id: str
    discovery_id: str
    problem: str = ""
    mechanism: str = ""
    design_principle: str = ""
    design_variables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    predicted_advantage: str = ""
    baseline: str = ""
    novelty_status: str = NoveltyStatus.NOT_EVALUATED.value
    prototype_specification: str = ""
    test_plan: str = ""
    failure_modes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# HYPOTHESIS ENGINE INTERFACE — definition only, no implementation
# ============================================================================

# The interface that a future hypothesis engine would implement.
# Do NOT implement this now. Just define the contract.

HYPOTHESIS_ENGINE_INTERFACE = """
# Hypothesis Engine Interface (contract only, not implemented)

def generate_hypotheses(context: DiscoveryCase) -> List[Hypothesis]:
    \"\"\"Generate candidate hypotheses from a discovery case.
    
    Each hypothesis must include:
        - claim (falsifiable statement)
        - mechanism (causal explanation)
        - evidence (supporting references)
        - assumptions
        - predictions
        - expected_failure_modes
        - novelty_rationale
        - testability
        - falsifier (what would prove it wrong)
    
    The interface must support multiple hypotheses.
    Never force the system to return one "best" invention.
    \"\"\"
    raise NotImplementedError("Hypothesis engine not yet implemented")


def rank_experiments(candidates: List[ExperimentProposal]) -> List[ExperimentProposal]:
    \"\"\"Rank experiments by expected information gain per unit cost.
    
    Do NOT create a fixed magic score. Represent dimensions separately:
        - novelty
        - expected_information_gain
        - testability
        - cost
        - time
        - risk
        - uncertainty
        - potential_impact
    
    Do not collapse them prematurely.
    \"\"\"
    raise NotImplementedError("Experiment ranking not yet implemented")


def assess_prior_art(hypothesis: Hypothesis) -> PriorArtAssessment:
    \"\"\"Assess prior art for a hypothesis.
    
    Must never claim 'this has never existed.'
    Can only make bounded evidence-based claims.
    \"\"\"
    raise NotImplementedError("Prior art service not yet implemented")
"""
