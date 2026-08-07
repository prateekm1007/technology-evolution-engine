#!/usr/bin/env python3
"""
dr93_proposal_evaluation.py — DR-93: Proposal Composer Evaluation (cycle 248).

Per CTO directive:
  "Does ProposalComposer actually produce scientifically meaningful
   BridgeProposals? Not 'does ProposalMatcher match them?' — those
   are different experiments.

   Measure: structural validity, scientific validity, discovery
   validity, proposal quality. Those measurements come BEFORE
   ProposalMatcher. Otherwise you may optimize matching against
   poor proposals."

This module evaluates the QUALITY of composed proposals, independent
of any benchmark score. Four dimensions:

1. STRUCTURAL VALIDITY: Does each proposal contain all required
   fields (mechanism, prediction, falsifier, assumptions)?

2. SCIENTIFIC VALIDITY: Is each proposal coherent, testable, and
   mechanistically plausible? (Evaluated via heuristic checks +
   structured scoring rubric)

3. DISCOVERY VALIDITY: Is the proposal already known, trivial, or
   genuinely novel? (Heuristic: does the shared entity appear in
   common scientific vocabulary?)

4. PROPOSAL QUALITY: Independent scoring of clarity, specificity,
   falsifiability. (Heuristic rubric — future: LLM judge or human)

HONEST WORDING (per CTO):
  "The path to testing trustworthiness is now available."
  NOT: "The path to trustworthiness is now clear."

  The Proposal Composer is generation 0 (entity → template → proposal).
  It is sufficient for proving the architecture. It is NOT sufficient
  for evaluating Proposal as the benchmark object. Eventually the
  composer should consume mechanisms, relations, constraints — not
  just entities.
"""
import sys
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audit.measurement_integrity.dr92_proposal_composer import (
    BridgeProposal, ProposalComposer,
)


# ============================================================================
# 1. STRUCTURAL VALIDITY
# ============================================================================

def check_structural_validity(proposal: BridgeProposal) -> Dict:
    """Check that a proposal has all required fields, non-empty and meaningful.

    Required fields:
    - shared_mechanism: ≥20 chars, contains the shared entity
    - necessary_assumptions: ≥1 assumption
    - prediction: ≥20 chars, contains "if"
    - alternative_explanations: ≥1 alternative
    - counterexample: ≥20 chars
    - falsification_experiment: ≥20 chars, contains "check" or "test"
    - confidence: 0-1
    - provenance: non-empty dict
    """
    checks = {
        "mechanism_present": len(proposal.shared_mechanism) >= 20,
        "mechanism_has_entity": bool(proposal.provenance.get("shared_entity", "") in proposal.shared_mechanism.lower()),
        "assumptions_present": len(proposal.necessary_assumptions) >= 1,
        "prediction_present": len(proposal.prediction) >= 20,
        "prediction_has_conditional": "if" in proposal.prediction.lower(),
        "alternatives_present": len(proposal.alternative_explanations) >= 1,
        "counterexample_present": len(proposal.counterexample) >= 20,
        "falsification_present": len(proposal.falsification_experiment) >= 20,
        "falsification_has_test": any(w in proposal.falsification_experiment.lower()
                                       for w in ["check", "test", "remove", "verify"]),
        "confidence_valid": 0 <= proposal.confidence <= 1,
        "provenance_present": len(proposal.provenance) >= 1,
        "source_clusters_present": len(proposal.source_cluster_a) >= 1 and len(proposal.source_cluster_b) >= 1,
    }

    passed = sum(checks.values())
    total = len(checks)
    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "valid": passed == total,
    }


# ============================================================================
# 2. SCIENTIFIC VALIDITY (heuristic rubric)
# ============================================================================

def check_scientific_validity(proposal: BridgeProposal) -> Dict:
    """Heuristic check: is the proposal coherent, testable, plausible?

    This is NOT a substitute for domain expert evaluation. It's a
    structured rubric that catches obvious failures.

    Dimensions:
    - COHERENT: the mechanism, prediction, and falsification are
      internally consistent (they reference the same entity)
    - TESTABLE: the prediction can be tested (has a conditional + outcome)
    - PLAUSIBLE: the mechanism is not obviously absurd (template-based,
      so this is weak — future: LLM judge)
    - SPECIFIC: the falsification is specific (not just "check if X")
    """
    entity = proposal.provenance.get("shared_entity", "")

    # COHERENT: entity appears in mechanism, prediction, and falsification
    coherent = (entity in proposal.shared_mechanism.lower() and
                entity in proposal.prediction.lower() and
                entity in proposal.falsification_experiment.lower())

    # TESTABLE: prediction has conditional structure
    testable = "if" in proposal.prediction.lower() and "then" in proposal.prediction.lower()

    # PLAUSIBLE: mechanism is not empty or trivially short
    plausible = len(proposal.shared_mechanism) >= 30

    # SPECIFIC: falsification mentions a concrete action
    specific_actions = ["check", "remove", "test", "verify", "measure", "compare"]
    specific = any(a in proposal.falsification_experiment.lower() for a in specific_actions)

    # NON_TRIVIAL: the entity is not a common stopword
    trivial_words = {"the", "this", "that", "with", "from", "have", "been",
                     "study", "research", "analysis", "result", "method",
                     "approach", "system", "process", "model", "data"}
    non_trivial = entity not in trivial_words and len(entity) >= 4

    scores = {
        "coherent": coherent,
        "testable": testable,
        "plausible": plausible,
        "specific": specific,
        "non_trivial": non_trivial,
    }

    passed = sum(scores.values())
    return {
        "scores": scores,
        "passed": passed,
        "total": len(scores),
        "scientific_valid": passed >= 4,  # at least 4/5
    }


# ============================================================================
# 3. DISCOVERY VALIDITY (heuristic novelty check)
# ============================================================================

def check_discovery_validity(proposal: BridgeProposal,
                              gold_bridges: List[str]) -> Dict:
    """Check whether the proposal is known, trivial, or novel.

    KNOWN: the shared entity matches a gold bridge
    TRIVIAL: the entity is a common scientific term
    NOVEL: neither known nor trivial
    """
    entity = proposal.provenance.get("shared_entity", "")

    # KNOWN: matches a gold bridge
    known = False
    for gb in gold_bridges:
        gb_canon = gb.lower().replace(" ", "_")
        if entity in gb_canon or gb_canon in entity:
            known = True
            break

    # TRIVIAL: very common scientific terms
    common_terms = {"temperature", "pressure", "energy", "mass", "volume",
                    "density", "velocity", "force", "power", "efficiency",
                    "performance", "structure", "material", "surface",
                    "interface", "reaction", "transfer", "conductivity",
                    "stability", "capacity"}
    trivial = entity in common_terms

    if known:
        classification = "KNOWN"
    elif trivial:
        classification = "TRIVIAL"
    else:
        classification = "POTENTIALLY_NOVEL"

    return {
        "classification": classification,
        "known": known,
        "trivial": trivial,
        "entity": entity,
    }


# ============================================================================
# 4. PROPOSAL QUALITY (heuristic scoring rubric)
# ============================================================================

def score_proposal_quality(proposal: BridgeProposal) -> Dict:
    """Score proposal quality on 4 dimensions (1-5 scale).

    Dimensions:
    - CLARITY: is the mechanism understandable?
    - SPECIFICITY: is the prediction specific (not generic)?
    - FALSIFIABILITY: is the falsification experiment concrete?
    - COMPLETENESS: are all fields meaningfully populated?
    """
    entity = proposal.provenance.get("shared_entity", "")

    # CLARITY (1-5): mechanism length and specificity
    mech_len = len(proposal.shared_mechanism)
    clarity = min(5, max(1, mech_len // 40))

    # SPECIFICITY (1-5): prediction mentions specific entity + outcome
    spec_score = 1
    if entity in proposal.prediction.lower():
        spec_score += 1
    if "should" in proposal.prediction.lower() or "must" in proposal.prediction.lower():
        spec_score += 1
    if len(proposal.prediction) > 60:
        spec_score += 1
    if "domain" in proposal.prediction.lower():
        spec_score += 1
    specificity = min(5, spec_score)

    # FALSIFIABILITY (1-5): falsification has concrete action
    fals_score = 1
    actions = ["check", "test", "remove", "verify", "measure", "compare"]
    if any(a in proposal.falsification_experiment.lower() for a in actions):
        fals_score += 2
    if "non-cross-domain" in proposal.falsification_experiment.lower():
        fals_score += 1
    if len(proposal.falsification_experiment) > 60:
        fals_score += 1
    falsifiability = min(5, fals_score)

    # COMPLETENESS (1-5): all fields have meaningful content
    comp_score = 0
    if len(proposal.shared_mechanism) > 30: comp_score += 1
    if len(proposal.necessary_assumptions) >= 2: comp_score += 1
    if len(proposal.alternative_explanations) >= 1: comp_score += 1
    if len(proposal.counterexample) > 30: comp_score += 1
    if proposal.confidence > 0: comp_score += 1
    completeness = comp_score

    overall = (clarity + specificity + falsifiability + completeness) / 4

    return {
        "clarity": clarity,
        "specificity": specificity,
        "falsifiability": falsifiability,
        "completeness": completeness,
        "overall": round(overall, 2),
    }


# ============================================================================
# MAIN — evaluate all composed proposals
# ============================================================================

def main():
    print("=" * 80)
    print("DR-93: Proposal Composer Evaluation (cycle 248)")
    print("Are the composed proposals scientifically meaningful?")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    composer = ProposalComposer()

    # Compose proposals from all gold discoveries
    all_proposals = []
    for gold in GOLD_DISCOVERIES:
        ents_a = [e.text for e in pipeline.extract_entities(gold["source_snippet_a"])]
        ents_b = [e.text for e in pipeline.extract_entities(gold["source_snippet_b"])]
        proposals = composer.compose(ents_a, ents_b,
                                      source_a_id=gold.get("id", "a"),
                                      source_b_id=gold.get("id", "b"))
        all_proposals.extend(proposals)

    print(f"Total proposals composed: {len(all_proposals)}")
    print()

    gold_bridges = [g["bridge"] for g in GOLD_DISCOVERIES]

    # Evaluate each proposal
    print("=" * 80)
    print("PER-PROPOSAL EVALUATION")
    print("=" * 80)
    print()
    print(f"{'ID':<10} {'Entity':<25} {'Struct':<8} {'Sci':<8} {'Disc':<15} {'Quality':<8}")
    print("-" * 75)

    results = []
    for p in all_proposals:
        struct = check_structural_validity(p)
        sci = check_scientific_validity(p)
        disc = check_discovery_validity(p, gold_bridges)
        qual = score_proposal_quality(p)

        results.append({
            "proposal_id": p.proposal_id,
            "entity": p.provenance.get("shared_entity", ""),
            "structural": struct,
            "scientific": sci,
            "discovery": disc,
            "quality": qual,
        })

        print(f"{p.proposal_id:<10} {p.provenance.get('shared_entity', ''):<25} "
              f"{struct['passed']}/{struct['total']:<8} "
              f"{sci['passed']}/{sci['total']:<8} "
              f"{disc['classification']:<15} "
              f"{qual['overall']:<8.2f}")

    # Aggregate
    print()
    print("=" * 80)
    print("AGGREGATE EVALUATION")
    print("=" * 80)
    print()

    n = len(results)
    if n == 0:
        print("No proposals to evaluate.")
        return

    struct_valid = sum(1 for r in results if r["structural"]["valid"])
    sci_valid = sum(1 for r in results if r["scientific"]["scientific_valid"])
    known = sum(1 for r in results if r["discovery"]["classification"] == "KNOWN")
    trivial = sum(1 for r in results if r["discovery"]["classification"] == "TRIVIAL")
    novel = sum(1 for r in results if r["discovery"]["classification"] == "POTENTIALLY_NOVEL")
    avg_quality = sum(r["quality"]["overall"] for r in results) / n

    print(f"Total proposals: {n}")
    print(f"Structurally valid: {struct_valid}/{n} ({struct_valid/n:.1%})")
    print(f"Scientifically valid: {sci_valid}/{n} ({sci_valid/n:.1%})")
    print(f"Discovery classification:")
    print(f"  KNOWN:           {known}/{n}")
    print(f"  TRIVIAL:         {trivial}/{n}")
    print(f"  POTENTIALLY_NOVEL: {novel}/{n}")
    print(f"Average quality: {avg_quality:.2f}/5.0")
    print()

    # Verdict
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    if struct_valid == n and sci_valid >= n * 0.8:
        print("PROPOSALS ARE STRUCTURALLY SOUND AND SCIENTIFICALLY COHERENT.")
        print("The Proposal Composer (generation 0) produces valid proposals.")
        print("Next: rerun Phase VI.6 with these proposals for fair comparison.")
    elif struct_valid < n:
        print(f"STRUCTURAL ISSUES: {n - struct_valid}/{n} proposals missing required fields.")
        print("The composer needs improvement before proposals can be benchmarked.")
    else:
        print(f"SCIENTIFIC ISSUES: {n - sci_valid}/{n} proposals fail scientific validity.")
        print("The proposals are structurally complete but not scientifically coherent.")

    print()
    print("HONEST WORDING: 'The path to testing trustworthiness is now available.'")
    print("NOT: 'The path to trustworthiness is now clear.'")
    print()
    print("The Proposal Composer is generation 0 (entity → template → proposal).")
    print("Future: consume mechanisms, relations, constraints — not just entities.")

    # Save
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    with open(reports_dir / "proposal_evaluation.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to reports/proposal_evaluation.json")


if __name__ == "__main__":
    main()
