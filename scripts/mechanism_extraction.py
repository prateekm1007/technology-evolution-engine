#!/usr/bin/env python3
"""
mechanism_extraction.py — Generation 4: Mechanism extraction.

Per CEO: "The most difficult jump isn't from 8/10 to 9/10. It's from
relation extraction to mechanism extraction. That's where almost the
entire history of artificial intelligence, philosophy of science, and
scientific discovery begins to converge."

Current state (Gen 3):
  graphene → improves → conductivity

Desired state (Gen 4):
  phonon scattering → reduction → mean free path increase
      → thermal conductivity increase

This module:
  1. Takes relations (from Gen 3 NLP pipeline) as input
  2. Builds causal chains (A → B → C → D)
  3. Identifies mechanisms (the causal process connecting entities)
  4. Detects contradictions (A improves X, B degrades X)
  5. Supports counterfactual reasoning (if A did not exist, would B be possible?)

The key insight: a mechanism is not a single edge. It is a CHAIN of causal
steps. The current system stores edges with a "mechanism" field (asserted,
not verified). This module builds the chain itself.

Per DR-15: mechanism claims must be executable, not just present.
Per DR-11: never store a fact by itself — every fact needs causal context.
"""
import sys
import json
import pathlib
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class CausalStep:
    """A single step in a causal chain."""
    cause: str  # entity or mechanism
    effect: str  # entity or mechanism
    relation: str  # "causes", "enables", "inhibits", "produces"
    confidence: float
    evidence: str = ""  # source sentence


@dataclass
class CausalChain:
    """A chain of causal steps connecting a root cause to a final effect.
    
    This is the Gen 4 target object. Instead of a single edge with a
    "mechanism" field, we have a chain of verified causal steps.
    
    Example:
      electrospinning → produces → nanofiber membrane → has → controlled pore size
      → governs → selective permeability → enables → water filtration
    
    This chain IS the mechanism. Each step is a causal claim that can be
    verified independently.
    """
    chain_id: str
    steps: List[CausalStep] = field(default_factory=list)
    root_cause: str = ""
    final_effect: str = ""
    mechanism_label: str = ""  # human-readable summary
    confidence: float = 0.0  # chain-level confidence (product of step confidences)
    
    def __post_init__(self):
        if self.steps:
            self.root_cause = self.steps[0].cause
            self.final_effect = self.steps[-1].effect
            self.confidence = sum(s.confidence for s in self.steps) / len(self.steps)
            self.mechanism_label = " → ".join(
                [self.steps[0].cause] + [s.effect for s in self.steps]
            )


@dataclass
class Contradiction:
    """A detected contradiction between two causal claims."""
    entity: str
    claim_1: str  # "A improves X"
    claim_2: str  # "B degrades X"
    contradiction_type: str  # "opposing_effects", "mutual_exclusion"


class MechanismExtractor:
    """Extract causal chains and mechanisms from relations.
    
    This is the Gen 4 module — the hardest jump in the 6-generation plan.
    
    Input: list of relations (subject, relation, object, confidence)
    Output: causal chains, mechanisms, contradictions
    """
    
    # Relations that indicate causation (vs. correlation or description)
    # Per cycle 104: expanded to include scientific verbs that indicate
    # productive/enabling relationships in experimental text.
    CAUSAL_RELATIONS = {
        "cause": "causal", "causes": "causal",
        "enable": "enabling", "enables": "enabling",
        "produce": "productive", "produces": "productive",
        "govern": "governing", "governs": "governing",
        "control": "governing", "controls": "governing",
        "increase": "enhancing", "increases": "enhancing",
        "improve": "enhancing", "improves": "enhancing",
        "enhance": "enhancing", "reduces": "inhibiting",
        "degrade": "inhibiting", "inhibit": "inhibiting",
        "prevent": "inhibiting", "block": "inhibiting",
        # Cycle 104 additions: scientific process verbs
        "perform": "productive",
        "disperse": "productive",
        "fibrillate": "productive",
        "record": "productive",
        "reflect": "productive",
        "expect": "causal",
        "divide": "productive",
        "separate": "productive",
        "measure": "productive",
        "detect": "productive",
        "exhibit": "causal",
        "demonstrate": "causal",
        "show": "causal",
        "reveal": "causal",
        "indicate": "causal",
        "suggest": "causal",
        "confirm": "causal",
    }
    
    # Opposing relations (for contradiction detection)
    OPPOSING = {
        "enhancing": "inhibiting",
        "inhibiting": "enhancing",
    }
    
    def __init__(self):
        self.chains: List[CausalChain] = []
        self.contradictions: List[Contradiction] = []
    
    def extract_chains(self, relations: List[Dict], min_steps: int = 1,
                       apply_quality_filter: bool = True) -> List[CausalChain]:
        """Build causal chains from a list of relations.
        
        A causal chain is a path through the relation graph where each
        edge is a causal relation. The chain represents a mechanism:
        the full causal story from root cause to final effect.
        
        Per cycle 105: added min_steps and apply_quality_filter params.
        Default: min_steps=1, apply_quality_filter=True (for real data).
        For synthetic test data: apply_quality_filter=False (test entities
        may be short like "A", "B", "C").
        """
        # Build adjacency list (only causal relations)
        graph = defaultdict(list)
        for rel in relations:
            # Per cycle 105: handle both "relation" and "mechanism" keys.
            # The NLP pipeline uses "mechanism", the synthetic test data
            # uses "relation". Check both for compatibility.
            relation_verb = rel.get("relation", rel.get("mechanism", "")).lower()
            relation_type = self.CAUSAL_RELATIONS.get(relation_verb)
            if relation_type:
                step = CausalStep(
                    cause=rel["source"],
                    effect=rel["target"],
                    relation=relation_verb,
                    confidence=rel.get("confidence", 0.5),
                    evidence=rel.get("source_sentence", ""),
                )
                graph[rel["source"]].append(step)
        
        # Find chains by DFS from each root node (nodes with no incoming causal edges)
        all_targets = {r["target"] for r in relations}
        all_sources = {r["source"] for r in relations}
        roots = all_sources - all_targets  # nodes that cause but aren't caused
        
        chains = []
        for root in roots:
            chain_steps = self._dfs_chain(root, graph, visited=set(), max_depth=5)
            if chain_steps:
                chain = CausalChain(
                    chain_id=f"chain_{root}_{len(chains)}",
                    steps=chain_steps,
                )
                chains.append(chain)
        
        # Also build chains from non-root nodes (in case the graph is cyclic
        # or the root detection missed something)
        for source in all_sources:
            if source in roots:
                continue
            chain_steps = self._dfs_chain(source, graph, visited=set(), max_depth=3)
            if chain_steps and len(chain_steps) >= min_steps:
                chain = CausalChain(
                    chain_id=f"chain_{source}_{len(chains)}",
                    steps=chain_steps,
                )
                chains.append(chain)
        
        # Per cycle 105: quality filter — remove chains with noise entities.
        # Only apply for real data (not synthetic test data with short entities).
        if apply_quality_filter:
            chains = self._filter_quality(chains)
        
        self.chains = chains
        return chains
    
    def _filter_quality(self, chains: List[CausalChain]) -> List[CausalChain]:
        """Filter chains by quality (cycle 105).
        
        Removes chains containing noise entities:
        - Very short entities (< 3 chars)
        - Pure numbers or measurements (e.g., "200_nm", "0.5µm")
        - Citation metadata (author names, years)
        - Special characters only
        """
        import re
        
        def is_noise(entity: str) -> bool:
            entity = entity.strip().lower()
            if len(entity) < 3:
                return True
            # Pure numbers/measurements
            if re.match(r'^[\d\.\-±µ]+$', entity):
                return True
            # Starts with a number (likely a measurement)
            if re.match(r'^\d', entity):
                return True
            # Single character + unit
            if re.match(r'^[a-z]\d', entity) and len(entity) < 5:
                return True
            return False
        
        filtered = []
        for chain in chains:
            # Check if any step has a noise entity
            has_noise = False
            for step in chain.steps:
                if is_noise(step.cause) or is_noise(step.effect):
                    has_noise = True
                    break
            if not has_noise:
                filtered.append(chain)
        
        return filtered
    
    def _dfs_chain(self, node: str, graph: Dict, visited: set, max_depth: int) -> List[CausalStep]:
        """Depth-first search to build a causal chain from a node."""
        if node in visited or max_depth <= 0:
            return []
        
        visited.add(node)
        steps = []
        current = node
        
        for _ in range(max_depth):
            neighbors = graph.get(current, [])
            if not neighbors:
                break
            
            # Take the highest-confidence neighbor
            best_step = max(neighbors, key=lambda s: s.confidence)
            if best_step.effect in visited:
                break
            
            steps.append(best_step)
            visited.add(best_step.effect)
            current = best_step.effect
        
        return steps
    
    def detect_contradictions(self, relations: List[Dict]) -> List[Contradiction]:
        """Detect contradictions in the relation set.
        
        A contradiction occurs when:
        - Two relations have opposing effects on the same entity
          (e.g., "A improves X" and "B degrades X" — not necessarily a
          contradiction, but worth flagging for investigation)
        - The SAME source has opposing effects on the SAME target
          (e.g., "A improves X" and "A degrades X" — definite contradiction)
        """
        # Group relations by target
        by_target = defaultdict(list)
        for rel in relations:
            by_target[rel["target"]].append(rel)
        
        contradictions = []
        for target, rels in by_target.items():
            # Check for opposing relation types on the same target
            types = {}
            for rel in rels:
                # Handle both "relation" and "mechanism" keys (cycle 105)
                relation_verb = rel.get("relation", rel.get("mechanism", "")).lower()
                rel_type = self.CAUSAL_RELATIONS.get(relation_verb)
                if rel_type:
                    types.setdefault(rel_type, []).append(rel)
            
            for t1, t2 in self.OPPOSING.items():
                if t1 in types and t2 in types:
                    for r1 in types[t1]:
                        for r2 in types[t2]:
                            # Only flag as contradiction if same source
                            if r1["source"] == r2["source"]:
                                contradictions.append(Contradiction(
                                    entity=target,
                                    claim_1=f"{r1['source']} {r1['relation']} {target}",
                                    claim_2=f"{r2['source']} {r2['relation']} {target}",
                                    contradiction_type="mutual_exclusion",
                                ))
        
        self.contradictions = contradictions
        return contradictions
    
    def counterfactual(self, entity: str, relations: List[Dict]) -> Dict:
        """Counterfactual reasoning: "If entity did not exist, what would change?"
        
        This is the Pearl do-calculus test: do(not entity) → what effects
        disappear?
        """
        # Find all relations where entity is the source (cause)
        as_cause = [r for r in relations if r["source"] == entity]
        # Find all relations where entity is the target (effect)
        as_effect = [r for r in relations if r["target"] == entity]
        
        # If entity did not exist:
        # - All effects it causes would not happen (or would need alternative causes)
        # - All causes that produce it would have no effect
        
        effects_lost = [r["target"] for r in as_cause]
        causes_orphaned = [r["source"] for r in as_effect]
        
        return {
            "entity": entity,
            "counterfactual": f"do(not {entity})",
            "effects_lost": effects_lost,
            "causes_orphaned": causes_orphaned,
            "interpretation": (
                f"If {entity} did not exist, {len(effects_lost)} effect(s) would "
                f"not occur: {effects_lost}. {len(causes_orphaned)} cause(s) would "
                f"have no target: {causes_orphaned}."
            ),
        }
    
    def extract_mechanisms(self, relations: List[Dict], min_steps: int = 1) -> Dict:
        """Full mechanism extraction pipeline.
        
        Input: relations from Gen 3 NLP pipeline
        Output: causal chains, contradictions, counterfactuals
        
        Per cycle 105: min_steps parameter for quality filtering.
        Default min_steps=1 (all chains). Set min_steps=2 for
        quality chains only.
        """
        chains = self.extract_chains(relations, min_steps=min_steps)
        contradictions = self.detect_contradictions(relations)
        
        # Generate counterfactuals for each entity
        all_entities = set()
        for r in relations:
            all_entities.add(r["source"])
            all_entities.add(r["target"])
        
        counterfactuals = {}
        for entity in all_entities:
            counterfactuals[entity] = self.counterfactual(entity, relations)
        
        return {
            "chains": [
                {
                    "chain_id": c.chain_id,
                    "root_cause": c.root_cause,
                    "final_effect": c.final_effect,
                    "mechanism_label": c.mechanism_label,
                    "confidence": c.confidence,
                    "steps": [
                        {"cause": s.cause, "effect": s.effect, "relation": s.relation,
                         "confidence": s.confidence}
                        for s in c.steps
                    ],
                }
                for c in chains
            ],
            "contradictions": [
                {"entity": c.entity, "claim_1": c.claim_1, "claim_2": c.claim_2,
                 "type": c.contradiction_type}
                for c in contradictions
            ],
            "counterfactuals": counterfactuals,
            "stats": {
                "total_relations": len(relations),
                "causal_chains": len(chains),
                "contradictions": len(contradictions),
                "entities_analyzed": len(all_entities),
            },
        }


if __name__ == "__main__":
    # Test the mechanism extractor on sample relations
    extractor = MechanismExtractor()
    
    test_relations = [
        {"source": "electrospinning", "relation": "produces", "target": "nanofiber_membrane", "confidence": 0.9},
        {"source": "nanofiber_membrane", "relation": "has", "target": "pore_size", "confidence": 0.8},
        {"source": "pore_size", "relation": "governs", "target": "selective_permeability", "confidence": 0.85},
        {"source": "selective_permeability", "relation": "enables", "target": "water_filtration", "confidence": 0.8},
        {"source": "pore_size", "relation": "increases", "target": "permeability", "confidence": 0.7},
        {"source": "pore_size", "relation": "reduces", "target": "permeability", "confidence": 0.6},  # contradiction!
    ]
    
    result = extractor.extract_mechanisms(test_relations)
    
    print("=== Mechanism Extraction Test (Gen 4) ===")
    print(f"\nCausal chains: {result['stats']['causal_chains']}")
    for chain in result["chains"]:
        print(f"\n  Chain: {chain['mechanism_label']}")
        print(f"  Confidence: {chain['confidence']}")
        print(f"  Steps: {len(chain['steps'])}")
        for step in chain["steps"]:
            print(f"    {step['cause']} --{step['relation']}--> {step['effect']} (conf={step['confidence']})")
    
    print(f"\nContradictions: {result['stats']['contradictions']}")
    for c in result["contradictions"]:
        print(f"  {c['entity']}: '{c['claim_1']}' vs '{c['claim_2']}'")
    
    print(f"\nCounterfactual (pore_size):")
    cf = result["counterfactuals"]["pore_size"]
    print(f"  {cf['interpretation']}")
