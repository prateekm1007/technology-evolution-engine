#!/usr/bin/env python3
"""
dr92_proposal_composer.py — DR-92: Proposal Composer (cycle 247).

Per CTO directive:
  "Build the missing architectural layer: A Proposal Composer that
   transforms extracted scientific evidence into explicit, structured
   BridgeProposal objects.

   Do not build another matcher. Do not recalibrate scores yet.
   Do not resume DR-90. Build the Proposal Composer."

THE MISSING LAYER:

Current pipeline:
  Corpus → Entity extraction → Entity list → Entity matcher

Needed pipeline:
  Corpus → Entity extraction → Relations → Mechanisms →
  Constraints → Predictions → Falsifications → BridgeProposal

The Proposal Composer takes extracted entities, relations, and
mechanisms and COMPOSES them into structured BridgeProposal objects.
Each proposal has:
  - Source cluster A (entities from literature A)
  - Source cluster B (entities from literature B)
  - Shared mechanism (connecting concept)
  - Necessary assumptions
  - Prediction
  - Alternative explanations
  - Counterexample
  - Falsification experiment
  - Confidence
  - Provenance

This is NOT a new matcher. It's a GENERATOR — it produces the
discovery objects that richer matchers can then evaluate.

HONEST STATUS:
  - This is the FIRST version of the Proposal Composer.
  - The proposals are composed from extracted entities + relations
    using heuristic rules (not LLM-generated).
  - The proposals are STRUCTURED (have all required fields) but may
    not be scientifically deep (the mechanisms are template-based).
  - This is a PREREQUISITE for fairly testing Objects B-E from
    Phase VI.6.
"""
import sys
import re
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ============================================================================
# BRIDGE PROPOSAL (the output of the Composer)
# ============================================================================

@dataclass
class BridgeProposal:
    """A structured scientific bridge proposal.

    This is the object that richer matchers (Phase VI.6 Objects B-E)
    expect. The Proposal Composer generates these from extracted
    entities + relations + mechanisms.
    """
    proposal_id: str
    source_cluster_a: List[str]     # entities from literature A
    source_cluster_b: List[str]     # entities from literature B
    shared_mechanism: str           # "X connects A to B via Y"
    necessary_assumptions: List[str]  # ["X is present in both domains"]
    prediction: str                 # "if X holds, then Y"
    alternative_explanations: List[str]  # ["coincidence"]
    counterexample: str             # "if X is removed, Y disappears"
    falsification_experiment: str   # "test X in isolation"
    confidence: float               # 0-1
    provenance: Dict[str, str]      # {component: source}

    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "source_cluster_a": self.source_cluster_a,
            "source_cluster_b": self.source_cluster_b,
            "shared_mechanism": self.shared_mechanism,
            "necessary_assumptions": self.necessary_assumptions,
            "prediction": self.prediction,
            "alternative_explanations": self.alternative_explanations,
            "counterexample": self.counterexample,
            "falsification_experiment": self.falsification_experiment,
            "confidence": self.confidence,
            "provenance": self.provenance,
        }


# ============================================================================
# PROPOSAL COMPOSER
# ============================================================================

class ProposalComposer:
    """Transforms extracted evidence into structured BridgeProposal objects.

    Input: entities from literature A + entities from literature B
           + shared entities + relations + mechanisms
    Output: List[BridgeProposal]

    The composer:
    1. Identifies SHARED entities (appear in both A and B)
    2. For each shared entity, constructs a BridgeProposal:
       - shared_mechanism: "The [entity] connects [domain_a] to [domain_b]"
       - necessary_assumptions: ["[entity] is a real scientific concept",
                                  "[entity] is relevant to both domains"]
       - prediction: "If [entity] is important to domain A, it should
                       also be important to domain B"
       - alternative_explanations: ["coincidence", "shared vocabulary"]
       - counterexample: "If [entity] is removed from the analysis,
                          the cross-domain connection should disappear"
       - falsification_experiment: "Check if [entity] appears in
                                    non-cross-domain papers"
       - confidence: based on entity frequency and specificity
       - provenance: which sources support each component

    This is HEURISTIC (not LLM-based). The proposals are structurally
    complete but scientifically shallow. Future versions will use
    the mechanism extractor and relation extractor for richer proposals.
    """

    def __init__(self):
        self.proposals: List[BridgeProposal] = []

    def compose(self, entities_a: List[str], entities_b: List[str],
                source_a_id: str = "source_a",
                source_b_id: str = "source_b") -> List[BridgeProposal]:
        """Compose BridgeProposals from extracted entities.

        Args:
            entities_a: list of entity strings from literature A
            entities_b: list of entity strings from literature B
            source_a_id: identifier for source A
            source_b_id: identifier for source B

        Returns:
            List of BridgeProposal objects (one per shared entity)
        """
        # Canonicalize
        canon_a = {self._canon(e) for e in entities_a}
        canon_b = {self._canon(e) for e in entities_b}

        # Find shared entities
        shared = canon_a & canon_b

        proposals = []
        for i, entity in enumerate(sorted(shared)):
            if len(entity) < 4:  # skip very short
                continue

            # Count frequency in each source
            freq_a = sum(1 for e in entities_a if self._canon(e) == entity)
            freq_b = sum(1 for e in entities_b if self._canon(e) == entity)

            # Confidence based on frequency (more frequent = more confident)
            confidence = min(1.0, (freq_a + freq_b) / 10.0)

            proposal = BridgeProposal(
                proposal_id=f"PROP-{i+1:03d}",
                source_cluster_a=[e for e in entities_a if self._canon(e) == entity][:5],
                source_cluster_b=[e for e in entities_b if self._canon(e) == entity][:5],
                shared_mechanism=f"The concept '{entity}' appears in both "
                                 f"source A and source B, suggesting a cross-domain "
                                 f"connection mediated by {entity}",
                necessary_assumptions=[
                    f"'{entity}' is a meaningful scientific concept",
                    f"'{entity}' is relevant to both source domains",
                    "The co-occurrence is not purely coincidental",
                ],
                prediction=f"If '{entity}' is a genuine cross-domain bridge, "
                           f"then papers in domain A that discuss '{entity}' "
                           f"should share mechanistic connections with papers "
                           f"in domain B that discuss '{entity}'",
                alternative_explanations=[
                    "The co-occurrence is coincidental (shared vocabulary)",
                    f"'{entity}' is a common scientific term with no specific "
                    f"cross-domain significance",
                    "The entity extraction produced a false positive",
                ],
                counterexample=f"If '{entity}' is removed from the shared entity "
                               f"set, the cross-domain connection should weaken "
                               f"or disappear",
                falsification_experiment=f"Check if '{entity}' appears with similar "
                                         f"frequency in non-cross-domain paper pairs. "
                                         f"If it does, the bridge is not specific",
                confidence=round(confidence, 3),
                provenance={
                    "entities_a": source_a_id,
                    "entities_b": source_b_id,
                    "shared_entity": entity,
                },
            )
            proposals.append(proposal)

        self.proposals.extend(proposals)
        return proposals

    def _canon(self, text: str) -> str:
        """Canonicalize text."""
        t = text.lower().strip()
        t = re.sub(r'[\s\-]+', '_', t)
        t = re.sub(r'[^a-z0-9_]', '', t)
        t = re.sub(r'_+', '_', t)
        return t.strip('_')


# ============================================================================
# TEST: compose proposals from gold discovery snippets
# ============================================================================

def main():
    print("=" * 80)
    print("DR-92: Proposal Composer (cycle 247)")
    print("Transforms extracted entities into structured BridgeProposal objects")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    composer = ProposalComposer()

    all_proposals = []

    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])

        entities_a = [e.text for e in ents_a]
        entities_b = [e.text for e in ents_b]

        proposals = composer.compose(entities_a, entities_b,
                                      source_a_id=gold.get("id", "a"),
                                      source_b_id=gold.get("id", "b"))
        all_proposals.extend(proposals)

        print(f"Gold: {gold['bridge']}")
        print(f"  Entities A: {len(entities_a)}, B: {len(entities_b)}")
        print(f"  Shared: {len(proposals)} proposals composed")
        if proposals:
            p = proposals[0]
            print(f"  Example proposal: {p.proposal_id}")
            print(f"    Mechanism: {p.shared_mechanism[:80]}...")
            print(f"    Prediction: {p.prediction[:80]}...")
            print(f"    Falsification: {p.falsification_experiment[:80]}...")
            print(f"    Confidence: {p.confidence}")
        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total gold discoveries: {len(GOLD_DISCOVERIES)}")
    print(f"Total proposals composed: {len(all_proposals)}")

    # Check: do proposals contain the gold bridge?
    gold_canon = [composer._canon(g["bridge"]) for g in GOLD_DISCOVERIES]
    proposal_entities = [p.provenance.get("shared_entity", "") for p in all_proposals]

    matches = 0
    for gb in gold_canon:
        for pe in proposal_entities:
            if gb in pe or pe in gb:
                matches += 1
                break

    print(f"Gold bridges found in proposals: {matches}/{len(GOLD_DISCOVERIES)}")
    print(f"Recall (proposal-level): {matches/len(GOLD_DISCOVERIES):.4f}")
    print()

    # Save proposals
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    reports_dir.mkdir(exist_ok=True)
    with open(reports_dir / "composed_proposals.json", "w") as f:
        json.dump([p.to_dict() for p in all_proposals], f, indent=2)
    print(f"Saved {len(all_proposals)} proposals to reports/composed_proposals.json")

    print()
    print("=" * 80)
    print("NEXT STEP")
    print("=" * 80)
    print()
    print("Now that proposals EXIST, re-run Phase VI.6 to test whether")
    print("the Proposal matcher can fairly evaluate them (vs the entity")
    print("matcher that was the only testable object before).")


if __name__ == "__main__":
    main()
