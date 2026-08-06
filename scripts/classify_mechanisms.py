#!/usr/bin/env python3
"""
classify_mechanisms.py — DR-42: Mechanism/status classification.

Per docs/EXTRACTION_ARCHITECTURE.md step 5:
  Tag every edge with a mechanism/status tier.
  No edge enters the graph without a status tag and provenance.

Status levels (weakest to strongest):
  associative          — co-occurrence, no causal claim
  asserted             — causal claim made, not verified
  plausibility-checked — checked against physics/chemistry
  verified             — confirmed by independent observation
  contradicted         — refuted by evidence

Chain status = weakest step in the chain.
Contradicted edges never promote.
"""
import sys
import pathlib
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.extract_relations import ExtractedRelationWithProvenance
from scripts.mechanism_extraction import CausalStep, CausalChain


class MechanismClassifier:
    """DR-42: Classify mechanism status for edges and chains.
    
    Rules:
    1. Every edge gets a status (never missing).
    2. Chain status = weakest step in the chain.
    3. Contradicted edges never promote (a chain with a contradicted
       step is contradicted, regardless of other steps).
    4. Verified requires provenance (source_id + retrieval_timestamp).
    """
    
    STATUS_ORDER = [
        "contradicted",      # -1: refuted
        "associative",       #  0: co-occurrence
        "asserted",          #  1: causal claim
        "plausibility-checked",  #  2: checked against physics
        "verified",          #  3: confirmed by observation
    ]
    
    STATUS_RANK = {s: i for i, s in enumerate(STATUS_ORDER)}
    
    def classify_edge(self, relation_verb: str, has_provenance: bool = False) -> str:
        """Classify a single edge's mechanism status.
        
        Args:
            relation_verb: the lemmatized relation verb
            has_provenance: whether the edge has source provenance
        
        Returns: status string
        """
        from scripts.extract_relations import CAUSAL_RELATIONS
        
        verb_lower = relation_verb.lower()
        relation_type = CAUSAL_RELATIONS.get(verb_lower)
        
        if relation_type:
            return "asserted"
        else:
            return "associative"
    
    def classify_chain(self, steps: List[CausalStep]) -> str:
        """Classify a chain's status (weakest step rule).
        
        Per DR-42: chain status = weakest step.
        Contradicted edges never promote: if any step is contradicted,
        the chain is contradicted.
        """
        if not steps:
            return "associative"
        
        # Check for contradicted first (overrides everything)
        for step in steps:
            if step.status == "contradicted":
                return "contradicted"
        
        # Find the weakest non-contradicted status
        weakest = "verified"  # start with strongest
        for step in steps:
            step_rank = self.STATUS_RANK.get(step.status, 0)
            weakest_rank = self.STATUS_RANK.get(weakest, 0)
            if step_rank < weakest_rank:
                weakest = step.status
        
        return weakest
    
    def promote_to_plausibility_checked(self, edge_status: str,
                                         physics_check_passed: bool) -> str:
        """Promote an edge to plausibility-checked if physics check passes.
        
        Only asserted edges can be promoted to plausibility-checked.
        Contradicted edges never promote.
        """
        if edge_status == "contradicted":
            return "contradicted"
        if edge_status == "asserted" and physics_check_passed:
            return "plausibility-checked"
        return edge_status
    
    def promote_to_verified(self, edge_status: str,
                             has_independent_observation: bool,
                             has_provenance: bool) -> str:
        """Promote an edge to verified if independently observed.
        
        Per DR-42: verified requires provenance.
        Contradicted edges never promote.
        """
        if edge_status == "contradicted":
            return "contradicted"
        if not has_provenance:
            return edge_status  # can't verify without provenance
        if edge_status in ("asserted", "plausibility-checked") and has_independent_observation:
            return "verified"
        return edge_status
    
    def mark_contradicted(self, edge_status: str) -> str:
        """Mark an edge as contradicted.
        
        Per DR-42: once contradicted, always contradicted.
        """
        return "contradicted"
    
    def validate_no_missing_status(self, edges: List[ExtractedRelationWithProvenance]) -> List[str]:
        """Validate that no edge is missing a status.
        
        Returns list of error messages (empty if all valid).
        """
        errors = []
        for i, edge in enumerate(edges):
            if not edge.status:
                errors.append(f"Edge {i}: missing status")
            elif edge.status not in self.STATUS_RANK:
                errors.append(f"Edge {i}: invalid status '{edge.status}'")
        return errors
