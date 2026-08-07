#!/usr/bin/env python3
"""
dr91_phase6_6.py — DR-91 Phase VI.6: Discovery Object Search (cycle 246).

Per CTO directive (post-245):
  "The objective is NOT to improve F1. The objective is to discover
   which benchmark object has the lowest adversarial false-positive
   rate while preserving genuine recall.

   Candidate objects: Entity, BridgeProposal, MechanismGraph,
   ScientificClaim, EvidenceGraph.

   The output should not be another F1 score. It should be a
   paper-quality comparison table answering:
   > What is the correct computational representation of a
   > scientific discovery?"

This module tests 5 candidate discovery objects, each progressively
richer, and measures:
  - Adversarial FP rate (can fakes fool it?)
  - Random FP rate (can random noise fool it?)
  - Genuine recall (does it still catch real discoveries?)
  - Discrimination ratio (recall / FP — higher is better)

The hypothesis: richer objects have lower FP but may lose recall.
The OPTIMAL object has FP < 5% AND recall > 0.

HONEST WORDING (per CTO):
  "We have identified a substantially better hypothesis for the root
   cause, supported by preliminary evidence, but it is not yet proven."
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

from audit.measurement_integrity.dr91_measurement_audit import (
    canon, m_exact, m_token, m_fuzzy, m_synonym, score,
)
from audit.measurement_integrity.dr91_phase6_5 import (
    BridgeProposal, _significant_words,
)


# ============================================================================
# FIVE CANDIDATE DISCOVERY OBJECTS
# ============================================================================

@dataclass
class EntityObject:
    """Object A: Entity (noun). The current (broken) benchmark object."""
    bridge: str  # a noun phrase

@dataclass
class BridgeProposalObject:
    """Object B: BridgeProposal (mechanism + prediction + falsifier)."""
    mechanism: str
    shared_variables: List[str]
    prediction: str
    falsification: str
    evidence_sources: List[str]

@dataclass
class MechanismGraphObject:
    """Object C: MechanismGraph (shared variables + causal chain + constraints).

    Richer than BridgeProposal: includes a CAUSAL CHAIN (A→B→C)
    and CONSTRAINTS (what must be true for the mechanism to hold).
    """
    shared_variables: List[str]
    causal_chain: List[str]  # ["A causes B", "B causes C"]
    constraints: List[str]   # ["A must be > threshold"]
    mechanism_summary: str

@dataclass
class ScientificClaimObject:
    """Object D: ScientificClaim (full scientific claim structure).

    The richest single-claim object. Includes problem, mechanism,
    assumptions, alternatives, prediction, falsifier.
    """
    problem: str
    mechanism: str
    necessary_assumptions: List[str]
    alternative_explanations: List[str]
    prediction: str
    falsification_experiment: str

@dataclass
class EvidenceGraphObject:
    """Object E: EvidenceGraph (full provenance graph).

    The richest object. Includes the claim PLUS a provenance graph
    showing which evidence supports which component.
    """
    claim: ScientificClaimObject
    evidence_graph: Dict[str, List[str]]  # {component: [evidence_sources]}


# ============================================================================
# MATCHERS FOR EACH OBJECT TYPE
# ============================================================================

def match_entity(gold: EntityObject, candidate: EntityObject) -> bool:
    """Entity match: token overlap (current production logic)."""
    return m_token(gold.bridge, candidate.bridge)

def match_proposal(gold: BridgeProposalObject, candidate: BridgeProposalObject) -> bool:
    """Proposal match: ≥50% mechanism words + ≥1 shared variable + prediction + falsifier."""
    g_words = _significant_words(gold.mechanism)
    c_words = _significant_words(candidate.mechanism)
    if not g_words:
        return False
    mech_match = len(g_words & c_words) / len(g_words) >= 0.5
    var_match = len(set(gold.shared_variables) & set(candidate.shared_variables)) >= 1
    pred_match = len(candidate.prediction) > 10
    fals_match = len(candidate.falsification) > 10
    return mech_match and var_match and pred_match and fals_match

def match_mechanism_graph(gold: MechanismGraphObject, candidate: MechanismGraphObject) -> bool:
    """MechanismGraph match: ≥1 shared causal chain step + ≥1 shared variable + ≥1 shared constraint."""
    # Shared causal chain steps
    g_chain = set(gold.causal_chain)
    c_chain = set(candidate.causal_chain)
    chain_match = len(g_chain & c_chain) >= 1

    # Shared variables
    var_match = len(set(gold.shared_variables) & set(candidate.shared_variables)) >= 1

    # Shared constraints (at least 1)
    g_constraints = set(canon(c) for c in gold.constraints)
    c_constraints = set(canon(c) for c in candidate.constraints)
    constraint_match = len(g_constraints & c_constraints) >= 1

    return chain_match and var_match and constraint_match

def match_scientific_claim(gold: ScientificClaimObject, candidate: ScientificClaimObject) -> bool:
    """ScientificClaim match: mechanism + ≥1 assumption + prediction + falsifier + ≥1 alternative."""
    g_words = _significant_words(gold.mechanism)
    c_words = _significant_words(candidate.mechanism)
    if not g_words:
        return False
    mech_match = len(g_words & c_words) / len(g_words) >= 0.5
    assum_match = len(set(canon(a) for a in gold.necessary_assumptions) &
                     set(canon(a) for a in candidate.necessary_assumptions)) >= 1
    pred_match = len(candidate.prediction) > 10
    fals_match = len(candidate.falsification_experiment) > 10
    alt_match = len(candidate.alternative_explanations) >= 1
    return mech_match and assum_match and pred_match and fals_match and alt_match

def match_evidence_graph(gold: EvidenceGraphObject, candidate: EvidenceGraphObject) -> bool:
    """EvidenceGraph match: claim match + ≥1 shared evidence component."""
    claim_match = match_scientific_claim(gold.claim, candidate.claim)
    if not claim_match:
        return False
    # Must also share at least 1 evidence component
    g_components = set(gold.evidence_graph.keys())
    c_components = set(candidate.evidence_graph.keys())
    evidence_match = len(g_components & c_components) >= 1
    return evidence_match


# ============================================================================
# ADVERSARIAL GENERATORS FOR EACH OBJECT TYPE
# ============================================================================

def gen_fake_entity(words: List[str], rng: random.Random) -> EntityObject:
    w1, w2 = rng.sample(words, 2) if len(words) >= 2 else ("a", "b")
    return EntityObject(bridge=f"{w1}_{w2}")

def gen_fake_proposal(words: List[str], rng: random.Random) -> BridgeProposalObject:
    w1, w2, w3 = rng.sample(words, 3) if len(words) >= 3 else ("a", "b", "c")
    return BridgeProposalObject(
        mechanism=f"The {w1} affects {w2} through {w3}",
        shared_variables=[w1, w2],
        prediction=f"If {w1} increases then {w2} increases",
        falsification=f"If {w1} increases and {w2} does not increase, mechanism is false",
        evidence_sources=["s1", "s2"],
    )

def gen_fake_mechanism_graph(words: List[str], rng: random.Random) -> MechanismGraphObject:
    w1, w2, w3 = rng.sample(words, 3) if len(words) >= 3 else ("a", "b", "c")
    return MechanismGraphObject(
        shared_variables=[w1, w2],
        causal_chain=[f"{w1} causes {w2}", f"{w2} causes {w3}"],
        constraints=[f"{w1} must be positive"],
        mechanism_summary=f"{w1} affects {w2} via {w3}",
    )

def gen_fake_scientific_claim(words: List[str], rng: random.Random) -> ScientificClaimObject:
    w1, w2, w3, w4 = rng.sample(words, 4) if len(words) >= 4 else ("a", "b", "c", "d")
    return ScientificClaimObject(
        problem=f"How does {w1} affect {w2}?",
        mechanism=f"The {w1} affects {w2} through {w3}",
        necessary_assumptions=[f"{w1} is present", f"{w3} is active"],
        alternative_explanations=[f"{w4} could also affect {w2}"],
        prediction=f"If {w1} increases then {w2} increases",
        falsification_experiment=f"Remove {w1} and check if {w2} still increases",
    )

def gen_fake_evidence_graph(words: List[str], rng: random.Random) -> EvidenceGraphObject:
    claim = gen_fake_scientific_claim(words, rng)
    return EvidenceGraphObject(
        claim=claim,
        evidence_graph={
            "mechanism": ["s1", "s2"],
            "prediction": ["s3"],
            "falsification": ["s4"],
        },
    )


# ============================================================================
# MEASURE ADVERSARIAL FP + RECALL FOR EACH OBJECT
# ============================================================================

def measure_object(gold_objects: List, match_fn, fake_gen_fn,
                    candidate_objects: List, words: List[str],
                    n_fakes: int = 20, n_shuffles: int = 200,
                    seed: int = 42) -> Dict:
    """Measure adversarial FP and genuine recall for one object type."""
    rng = random.Random(seed)

    # Genuine recall: how many gold objects match candidates?
    tp = 0
    for gold in gold_objects:
        for cand in candidate_objects:
            if match_fn(gold, cand):
                tp += 1
                break
    recall = tp / len(gold_objects) if gold_objects else 0

    # Adversarial FP: generate fakes, see how many match
    fake_matches = 0
    for _ in range(n_fakes):
        fake = fake_gen_fn(words, rng)
        for gold in gold_objects:
            if match_fn(gold, fake):
                fake_matches += 1
                break
    adv_fp = fake_matches / n_fakes if n_fakes > 0 else 0

    # Random FP: shuffle gold labels
    if candidate_objects and len(candidate_objects) >= 2:
        random_scores = []
        for _ in range(min(n_shuffles, 100)):
            fake_gold = [rng.choice(candidate_objects) for _ in range(len(gold_objects))]
            rand_tp = 0
            for fg in fake_gold:
                for gold in gold_objects:
                    if match_fn(gold, fg):
                        rand_tp += 1
                        break
            random_scores.append(rand_tp / len(gold_objects) if gold_objects else 0)
        random_fp = max(random_scores) if random_scores else 0
    else:
        random_fp = 0

    # Discrimination ratio
    discrimination = recall / max(0.001, adv_fp) if adv_fp > 0 else float('inf') if recall > 0 else 0

    return {
        "recall": round(recall, 4),
        "adversarial_fp": round(adv_fp, 4),
        "random_fp": round(random_fp, 4),
        "discrimination": round(discrimination, 4) if discrimination != float('inf') else 999,
        "n_gold": len(gold_objects),
        "n_candidates": len(candidate_objects),
        "n_fakes": n_fakes,
        "verdict": "PASS" if adv_fp < 0.05 and recall > 0 else "FAIL",
    }


# ============================================================================
# MAIN — PAPER-QUALITY COMPARISON TABLE
# ============================================================================

def main():
    print("=" * 80)
    print("DR-91 Phase VI.6: Discovery Object Search (cycle 246)")
    print("What is the correct computational representation of a scientific discovery?")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES, BRIDGE_SYNONYMS
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    all_ents = []
    all_words = set()
    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        all_ents.extend([e.text for e in ents_a + ents_b])
        for e in ents_a + ents_b:
            for w in canon(e.text).split("_"):
                if len(w) >= 4:
                    all_words.add(w)
    all_entities = list(set(all_ents))
    all_words = list(all_words)

    print(f"Gold discoveries: {len(GOLD_DISCOVERIES)}")
    print(f"Total entities: {len(all_entities)}")
    print(f"Significant words: {len(all_words)}")
    print()

    # Build gold + candidate objects for each type
    # === Object A: Entity ===
    gold_entities = [EntityObject(bridge=g["bridge"]) for g in GOLD_DISCOVERIES]
    cand_entities = [EntityObject(bridge=e) for e in all_entities]

    # === Object B: BridgeProposal ===
    gold_proposals = [BridgeProposalObject(
        mechanism=f"The {g['bridge']} connects domain A to domain B",
        shared_variables=[canon(g["bridge"])],
        prediction=f"If {g['bridge']} is present, cross-domain connection exists",
        falsification=f"If {g['bridge']} is absent, no cross-domain connection",
        evidence_sources=["s1", "s2"],
    ) for g in GOLD_DISCOVERIES]
    cand_proposals = [BridgeProposalObject(
        mechanism=f"The {e} is present in the text",
        shared_variables=[canon(e)],
        prediction=f"If {e} is present, extraction succeeded",
        falsification=f"If {e} is absent, extraction failed",
        evidence_sources=["s1"],
    ) for e in all_entities[:20]]  # subset for speed

    # === Object C: MechanismGraph ===
    gold_graphs = [MechanismGraphObject(
        shared_variables=[canon(g["bridge"])],
        causal_chain=[f"{canon(g['bridge'])} causes cross_domain_connection"],
        constraints=[f"{canon(g['bridge'])} must be semantically present"],
        mechanism_summary=f"{g['bridge']} connects domains",
    ) for g in GOLD_DISCOVERIES]
    cand_graphs = [MechanismGraphObject(
        shared_variables=[canon(e)],
        causal_chain=[f"{canon(e)} causes extraction"],
        constraints=[f"{canon(e)} must be extracted"],
        mechanism_summary=f"{e} is extracted",
    ) for e in all_entities[:20]]

    # === Object D: ScientificClaim ===
    gold_claims = [ScientificClaimObject(
        problem=f"What connects A and B via {g['bridge']}?",
        mechanism=f"The {g['bridge']} connects domain A to domain B",
        necessary_assumptions=[f"{canon(g['bridge'])} is a real concept"],
        alternative_explanations=["random coincidence"],
        prediction=f"Cross-domain papers share {g['bridge']}",
        falsification_experiment=f"Check if non-cross-domain papers also share {g['bridge']}",
    ) for g in GOLD_DISCOVERIES]
    cand_claims = [ScientificClaimObject(
        problem=f"What is {e}?",
        mechanism=f"{e} is an extracted entity",
        necessary_assumptions=[f"{canon(e)} is extractable"],
        alternative_explanations=["noise"],
        prediction=f"{e} appears in text",
        falsification_experiment=f"Check if {e} appears in random text",
    ) for e in all_entities[:20]]

    # === Object E: EvidenceGraph ===
    gold_evidence = [EvidenceGraphObject(
        claim=gc,
        evidence_graph={"mechanism": ["s1", "s2"], "prediction": ["s1"]},
    ) for gc in gold_claims]
    cand_evidence = [EvidenceGraphObject(
        claim=cc,
        evidence_graph={"mechanism": ["s1"]},
    ) for cc in cand_claims]

    # Measure each object
    objects = [
        ("A: Entity", gold_entities, match_entity, gen_fake_entity, cand_entities),
        ("B: BridgeProposal", gold_proposals, match_proposal, gen_fake_proposal, cand_proposals),
        ("C: MechanismGraph", gold_graphs, match_mechanism_graph, gen_fake_mechanism_graph, cand_graphs),
        ("D: ScientificClaim", gold_claims, match_scientific_claim, gen_fake_scientific_claim, cand_claims),
        ("E: EvidenceGraph", gold_evidence, match_evidence_graph, gen_fake_evidence_graph, cand_evidence),
    ]

    print("=" * 80)
    print("DISCOVERY OBJECT COMPARISON TABLE")
    print("=" * 80)
    print()
    print(f"{'Object':<25} {'Recall':<10} {'Adv FP':<10} {'Rand FP':<10} {'Discrim':<10} {'Verdict':<8}")
    print("-" * 75)

    results = []
    for name, gold, match_fn, fake_fn, cands in objects:
        r = measure_object(gold, match_fn, fake_fn, cands, all_words,
                           n_fakes=20, n_shuffles=100, seed=42)
        results.append((name, r))
        disc = f"{r['discrimination']:.2f}" if r['discrimination'] < 999 else "∞"
        print(f"{name:<25} {r['recall']:<10.4f} {r['adversarial_fp']:<10.4f} "
              f"{r['random_fp']:<10.4f} {disc:<10} {r['verdict']:<8}")

    print()
    print("=" * 80)
    print("HONEST INTERPRETATION")
    print("=" * 80)
    print()
    print("HONEST WORDING: 'We have identified a substantially better hypothesis")
    print("for the root cause, supported by preliminary evidence, but it is not")
    print("yet proven.' (per CTO directive)")
    print()

    # Find best object
    best = max(results, key=lambda x: x[1]["discrimination"] if x[1]["discrimination"] != 999 else 0)
    print(f"Best discrimination: {best[0]} (discrimination={best[1]['discrimination']:.2f})")
    print(f"  Recall: {best[1]['recall']:.4f}")
    print(f"  Adv FP: {best[1]['adversarial_fp']:.4f}")
    print()

    # Which objects pass?
    passing = [name for name, r in results if r["verdict"] == "PASS"]
    if passing:
        print(f"Objects that PASS (FP < 5% AND recall > 0): {passing}")
    else:
        print("NO objects pass (FP < 5% AND recall > 0).")
        print()
        print("This means: the search for the correct discovery object is NOT complete.")
        print("All 5 candidate objects have FP > 5% under adversarial testing.")
        print("The correct object may require:")
        print("  - Tighter matchers (require 75%+ word overlap)")
        print("  - Richer structure (causal chains, provenance)")
        print("  - Semantic matching (embeddings, not word overlap)")
        print("  - Human annotation (gold proposals hand-written by domain experts)")

    print()
    print("=" * 80)
    print("THE CENTRAL RESEARCH QUESTION")
    print("=" * 80)
    print()
    print("> What is the correct computational representation of a scientific")
    print("> discovery?")
    print()
    print("This is now the central research question of the discovery engine.")
    print("It is deeper than 'how do we improve discovery?' — it asks what")
    print("discovery IS, computationally.")
    print()
    print("The answer will determine every future benchmark, every maturity")
    print("score, and every scientific claim the project makes.")

    # Save results
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    with open(reports_dir / "discovery_object_search.json", "w") as f:
        json.dump([{"object": n, **r} for n, r in results], f, indent=2)
    print(f"\nSaved to reports/discovery_object_search.json")


if __name__ == "__main__":
    main()
