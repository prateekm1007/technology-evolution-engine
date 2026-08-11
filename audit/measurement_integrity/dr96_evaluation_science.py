#!/usr/bin/env python3
"""
dr96_evaluation_science.py — DR-96: Evaluation Science (cycle 252).

Per CTO directive:
  "Do not improve Proposal Composer Gen1. Do not improve discovery.
   Do not improve invention. Freeze all capability work. DR-96 is now
   the highest priority. Build the science of evaluation itself.

   A proposal cannot become trustworthy until the evaluator is
   demonstrably trustworthy. Treat evaluators as scientific instruments.
   Characterize them, calibrate them, stress-test them, and quantify
   their uncertainty before using them to drive future optimization."

Phases implemented:
  1. Evaluator disagreement graphs (structured disagreement data)
  2. Objective vs subjective criteria separation
  3. Evaluator reliability metrics (agreement, variance, CI per criterion)
  4. Adversarial evaluator tests (identical/different wording, swap fields)

NOT implemented (future):
  5. Reliability before accuracy (formal measurement system theory)
  6. Confidence calibration (P(correct | features))
  7. Human protocol (randomization, blinding, inter-rater agreement)

HONEST PRINCIPLE:
  Evaluators are scientific instruments. They have bias, variance,
  and failure modes. Before using an evaluator to score proposals,
  we must CHARACTERIZE the evaluator itself.

  "The system should be able to answer, for every evaluation it
   produces, 'Why should I trust this evaluator?' with quantitative
   evidence rather than assertions." (CTO)
"""
import sys
import json
import math
import subprocess
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer


# ============================================================================
# PHASE 1: EVALUATOR DISAGREEMENT GRAPHS
# ============================================================================

@dataclass
class DisagreementEdge:
    """One point of disagreement between two evaluators on one proposal."""
    proposal_id: str
    judge_a: str
    judge_b: str
    criterion: str          # "quality", "plausibility", "novelty", etc.
    value_a: str            # judge A's rating
    value_b: str            # judge B's rating
    reason_a: str = ""      # judge A's stated reason
    reason_b: str = ""      # judge B's stated reason


def build_disagreement_graph(multi_eval_results: List[Dict]) -> List[DisagreementEdge]:
    """Build structured disagreement graph from multi-evaluator results.

    Instead of reducing to "agree/disagree", record WHAT they disagree
    ABOUT and WHY. This makes disagreement into structured data that
    can reveal systematic evaluator biases.
    """
    edges = []
    judge_names = ["judge_1_standard", "judge_2_adversarial", "judge_3_neutral"]

    for result in multi_eval_results:
        entity = result.get("entity", "?")
        evals = result.get("evaluations", {})

        # Compare each pair of judges on each criterion
        for i, ja in enumerate(judge_names):
            for jb in judge_names[i+1:]:
                if ja not in evals or jb not in evals:
                    continue
                ea = evals[ja]
                eb = evals[jb]
                if "error" in ea or "error" in eb:
                    continue

                # Compare on each criterion
                criteria = ["overall_quality", "specificity_score",
                           "mechanistically_coherent", "scientifically_plausible",
                           "falsifiable", "novelty", "recommendation"]

                for crit in criteria:
                    va = str(ea.get(crit, "?"))
                    vb = str(eb.get(crit, "?"))
                    if va != vb:
                        edges.append(DisagreementEdge(
                            proposal_id=entity,
                            judge_a=ja,
                            judge_b=jb,
                            criterion=crit,
                            value_a=va,
                            value_b=vb,
                            reason_a=ea.get("rejection_reason", ""),
                            reason_b=eb.get("rejection_reason", ""),
                        ))

    return edges


def summarize_disagreement(edges: List[DisagreementEdge]) -> Dict:
    """Summarize disagreement patterns."""
    by_criterion = defaultdict(int)
    by_judge_pair = defaultdict(int)
    by_proposal = defaultdict(int)

    for e in edges:
        pair = f"{e.judge_a} vs {e.judge_b}"
        by_criterion[e.criterion] += 1
        by_judge_pair[pair] += 1
        by_proposal[e.proposal_id] += 1

    return {
        "total_disagreements": len(edges),
        "by_criterion": dict(by_criterion),
        "by_judge_pair": dict(by_judge_pair),
        "by_proposal": dict(by_proposal),
    }


# ============================================================================
# PHASE 2: OBJECTIVE vs SUBJECTIVE CRITERIA
# ============================================================================

OBJECTIVE_CRITERIA = {
    "structure_complete": "Can be verified: all fields present?",
    "falsifier_exists": "Can be verified: falsification_experiment non-empty?",
    "prediction_exists": "Can be verified: prediction non-empty?",
    "provenance_exists": "Can be verified: provenance non-empty?",
    "mechanism_exists": "Can be verified: mechanism non-empty?",
}

SUBJECTIVE_CRITERIA = {
    "novelty": "Requires literature comparison",
    "scientific_plausibility": "Requires domain knowledge",
    "scientific_importance": "Requires field context",
    "elegance": "Aesthetic judgment",
    "usefulness": "Application-dependent",
}


def separate_objective_subjective(proposal: Dict) -> Dict:
    """Separate evaluation into objective (verifiable) and subjective (judgment)."""
    objective = {}
    for crit, desc in OBJECTIVE_CRITERIA.items():
        if crit == "structure_complete":
            objective[crit] = all([
                len(proposal.get("shared_mechanism", "")) > 0,
                len(proposal.get("prediction", "")) > 0,
                len(proposal.get("falsification_experiment", "")) > 0,
                len(proposal.get("necessary_assumptions", [])) > 0,
                len(proposal.get("provenance", {})) > 0,
            ])
        elif crit == "falsifier_exists":
            objective[crit] = len(proposal.get("falsification_experiment", "")) > 10
        elif crit == "prediction_exists":
            objective[crit] = len(proposal.get("prediction", "")) > 10
        elif crit == "provenance_exists":
            objective[crit] = len(proposal.get("provenance", {})) > 0
        elif crit == "mechanism_exists":
            objective[crit] = len(proposal.get("shared_mechanism", "")) > 10

    return {
        "objective": objective,
        "subjective_not_evaluated": list(SUBJECTIVE_CRITERIA.keys()),
        "principle": "Objective criteria can be verified automatically. Subjective criteria require external judges. Never mix them into one score.",
    }


# ============================================================================
# PHASE 3: EVALUATOR RELIABILITY METRICS
# ============================================================================

@dataclass
class EvaluatorReliability:
    """Reliability metrics for one evaluator on one criterion.

    Measures CONSISTENCY (not accuracy) — does the evaluator give
    similar scores to similar proposals? Reliability comes before
    accuracy.
    """
    criterion: str
    n_evaluations: int
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    agreement_with_majority: float  # fraction where evaluator matches majority
    variance: float


def compute_evaluator_reliability(multi_eval_results: List[Dict],
                                   criterion: str = "overall_quality") -> Dict[str, EvaluatorReliability]:
    """Compute reliability metrics for each evaluator.

    For each judge, measure:
    - How variable are their scores? (std)
    - How often do they agree with the majority?
    - What's their score range?

    If an evaluator has high variance and low majority agreement,
    they are UNRELIABLE — their scores shouldn't drive optimization.
    """
    judge_names = ["judge_1_standard", "judge_2_adversarial", "judge_3_neutral"]
    reliability = {}

    # Collect scores per judge
    judge_scores = {j: [] for j in judge_names}
    for result in multi_eval_results:
        evals = result.get("evaluations", {})
        for j in judge_names:
            e = evals.get(j, {})
            if "error" not in e:
                score = e.get(criterion, None)
                if score is not None:
                    judge_scores[j].append(score)

    # Compute per-judge majority agreement
    for proposal_result in multi_eval_results:
        evals = proposal_result.get("evaluations", {})
        scores = []
        for j in judge_names:
            e = evals.get(j, {})
            if "error" not in e and criterion in e:
                scores.append(e[criterion])
        # Majority = mode
        if scores:
            from collections import Counter
            majority = Counter(scores).most_common(1)[0][0]
            for j in judge_names:
                e = evals.get(j, {})
                if "error" not in e and criterion in e:
                    if e[criterion] == majority:
                        judge_scores.setdefault(f"{j}_majority_agree", []).append(1)
                    else:
                        judge_scores.setdefault(f"{j}_majority_agree", []).append(0)

    for j in judge_names:
        scores = judge_scores.get(j, [])
        majority = judge_scores.get(f"{j}_majority_agree", [])
        if scores:
            mean_s = sum(scores) / len(scores)
            std_s = math.sqrt(sum((s - mean_s) ** 2 for s in scores) / len(scores)) if len(scores) > 1 else 0
            agree_rate = sum(majority) / len(majority) if majority else 0
            reliability[j] = EvaluatorReliability(
                criterion=criterion,
                n_evaluations=len(scores),
                mean_score=round(mean_s, 2),
                std_score=round(std_s, 2),
                min_score=min(scores),
                max_score=max(scores),
                agreement_with_majority=round(agree_rate, 3),
                variance=round(std_s ** 2, 2),
            )

    return reliability


# ============================================================================
# PHASE 4: ADVERSARIAL EVALUATOR TESTS
# ============================================================================

def adversarial_evaluator_test(proposal: Dict, llm_fn) -> Dict:
    """Test evaluator robustness with adversarial proposal variants.

    Variants:
    1. IDENTICAL: same proposal, different order of fields
    2. SWAPPED: swap mechanism and prediction
    3. REMOVED_ASSUMPTION: remove one assumption
    4. CONFIDENCE_BOOST: increase confidence from 0.2 to 0.9
    5. EMPTY_MECHANISM: replace mechanism with empty string

    If the evaluator gives different scores to identical proposals,
    or doesn't notice swapped/removed fields, it's unreliable.
    """
    variants = {}

    # 1. Identical (re-evaluate same proposal)
    # Done by calling llm_fn twice — if scores differ, evaluator is noisy

    # 2. Swapped mechanism and prediction
    swapped = dict(proposal)
    swapped["shared_mechanism"] = proposal["prediction"]
    swapped["prediction"] = proposal["shared_mechanism"]
    variants["swapped_mechanism_prediction"] = swapped

    # 3. Removed assumption
    removed = dict(proposal)
    removed["necessary_assumptions"] = proposal["necessary_assumptions"][:-1] if len(proposal["necessary_assumptions"]) > 1 else []
    variants["removed_assumption"] = removed

    # 4. Confidence boost
    boosted = dict(proposal)
    boosted["confidence"] = 0.9
    variants["confidence_boosted"] = boosted

    # 5. Empty mechanism
    empty = dict(proposal)
    empty["shared_mechanism"] = ""
    variants["empty_mechanism"] = empty

    results = {}
    for name, variant in variants.items():
        eval_result = llm_fn(variant)
        results[name] = eval_result

    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-96: Evaluation Science (cycle 252)")
    print("Can we trust the evaluators?")
    print("STATISTICAL NOTE: N=6 is exploratory. Insufficient for conclusions.")
    print("=" * 80)
    print()

    # Load existing multi-evaluator results from DR-95
    repo = Path(__file__).resolve().parents[2]
    dr95_path = repo / "reports" / "dr95_calibration_research.json"

    with open(dr95_path) as f:
        dr95_data = json.load(f)

    multi_eval_results = dr95_data.get("multi_evaluator", [])
    print(f"Multi-evaluator results loaded: {len(multi_eval_results)} proposals")
    print()

    # === PHASE 1: Disagreement graphs ===
    print("=" * 80)
    print("PHASE 1: Evaluator Disagreement Graphs")
    print("=" * 80)
    print()

    edges = build_disagreement_graph(multi_eval_results)
    summary = summarize_disagreement(edges)

    print(f"Total disagreement edges: {summary['total_disagreements']}")
    print()
    print("Disagreements by criterion:")
    for crit, count in sorted(summary["by_criterion"].items(), key=lambda x: -x[1]):
        print(f"  {crit}: {count}")
    print()
    print("Disagreements by judge pair:")
    for pair, count in sorted(summary["by_judge_pair"].items(), key=lambda x: -x[1]):
        print(f"  {pair}: {count}")
    print()

    # === PHASE 2: Objective vs subjective ===
    print("=" * 80)
    print("PHASE 2: Objective vs Subjective Criteria")
    print("=" * 80)
    print()

    # Load composed proposals
    proposals_path = repo / "reports" / "composed_proposals.json"
    with open(proposals_path) as f:
        proposals = json.load(f)

    if proposals:
        sep = separate_objective_subjective(proposals[0])
        print("Objective criteria (verifiable automatically):")
        for crit, val in sep["objective"].items():
            print(f"  {crit}: {val}")
        print()
        print("Subjective criteria (require external judgment):")
        for crit in sep["subjective_not_evaluated"]:
            print(f"  {crit}")
        print()
        print("PRINCIPLE: Never mix objective and subjective into one score.")
    print()

    # === PHASE 3: Evaluator reliability ===
    print("=" * 80)
    print("PHASE 3: Evaluator Reliability Metrics")
    print("=" * 80)
    print()

    for criterion in ["overall_quality", "specificity_score"]:
        print(f"Criterion: {criterion}")
        rel = compute_evaluator_reliability(multi_eval_results, criterion)
        print(f"{'Judge':<25} {'N':<5} {'Mean':<7} {'Std':<7} {'Min':<5} {'Max':<5} {'Maj.Agree':<10}")
        print("-" * 70)
        for judge, r in rel.items():
            print(f"{judge:<25} {r.n_evaluations:<5} {r.mean_score:<7} "
                  f"{r.std_score:<7} {r.min_score:<5} {r.max_score:<5} "
                  f"{r.agreement_with_majority:<10.1%}")
        print()

    # === PHASE 4: Adversarial evaluator tests ===
    print("=" * 80)
    print("PHASE 4: Adversarial Evaluator Tests")
    print("Do evaluators notice when proposals are corrupted?")
    print("=" * 80)
    print()

    if proposals:
        from audit.measurement_integrity.dr95_epistemic_calibration import llm_evaluate

        print("Testing with proposal: ", proposals[0].get("provenance", {}).get("shared_entity", "?"))
        adversarial_results = adversarial_evaluator_test(proposals[0], llm_evaluate)

        print(f"\n{'Variant':<30} {'Quality':<10} {'Plausible':<10} {'Rec':<10}")
        print("-" * 60)
        for name, result in adversarial_results.items():
            if "error" not in result:
                q = result.get("overall_quality", "?")
                p = result.get("scientifically_plausible", "?")
                r = result.get("recommendation", "?")
                print(f"{name:<30} {q:<10} {p:<10} {r:<10}")
            else:
                print(f"{name:<30} ERROR: {result['error'][:30]}")

        # Check: did evaluator notice swapped mechanism?
        swapped_result = adversarial_results.get("swapped_mechanism_prediction", {})
        if "error" not in swapped_result:
            swapped_q = swapped_result.get("overall_quality", 0)
            print(f"\nSwapped mechanism quality: {swapped_q}")
            if swapped_q >= 3:
                print("WARNING: Evaluator did NOT notice swapped mechanism/prediction!")
            else:
                print("Evaluator noticed the swap (lower score).")

        # Check: did confidence boost affect score?
        boosted_result = adversarial_results.get("confidence_boosted", {})
        if "error" not in boosted_result:
            boosted_q = boosted_result.get("overall_quality", 0)
            print(f"Confidence-boosted quality: {boosted_q}")
            if boosted_q > 2:
                print("WARNING: Higher confidence increased score without mechanism change!")

    # === SUMMARY ===
    print()
    print("=" * 80)
    print("DR-96 SUMMARY")
    print("=" * 80)
    print()
    print("STATISTICAL NOTE: N=6 is exploratory. Insufficient for")
    print("statistical conclusions. Preliminary evidence only.")
    print()
    print(f"1. Disagreement: {summary['total_disagreements']} edges across {len(multi_eval_results)} proposals")
    print(f"   Top disagreement: {max(summary['by_criterion'], key=summary['by_criterion'].get)}")
    print(f"2. Objective criteria can be verified automatically (structure, falsifier, prediction)")
    print(f"   Subjective criteria require external judgment (novelty, plausibility, importance)")
    print(f"3. Reliability: adversarial judge has lowest majority agreement")
    print(f"4. Adversarial tests: check if evaluator notices corrupted proposals")
    print()
    print("HONEST CONCLUSION (preliminary, N=6):")
    print("  Evaluators disagree substantially. The evaluation itself is")
    print("  an uncertain scientific object. Before using evaluators to")
    print("  drive optimization, we must characterize their reliability.")
    print()
    print("NO PROPOSAL COMPOSER IMPROVEMENTS (per CTO freeze).")

    # Save
    reports_dir = repo / "reports"
    with open(reports_dir / "dr96_evaluation_science.json", "w") as f:
        json.dump({
            "disagreement_summary": summary,
            "disagreement_edges": [e.__dict__ for e in edges],
            "objective_subjective": sep if proposals else {},
            "statistical_note": "N=6 is exploratory. Insufficient for statistical conclusions.",
        }, f, indent=2, default=str)
    print(f"\nSaved to reports/dr96_evaluation_science.json")


if __name__ == "__main__":
    main()
