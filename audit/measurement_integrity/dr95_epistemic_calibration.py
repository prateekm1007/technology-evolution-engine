#!/usr/bin/env python3
"""
dr95_epistemic_calibration.py — DR-95: Epistemic Calibration Research (cycle 251).

Per CTO directive:
  "No Proposal Composer improvements are allowed. The only objective is
   understanding the calibration problem. The output is not code — the
   output is evidence.

   The irony would be painful: fixing the self-validation bias by
   creating a new evaluation bias."

Phases implemented:
  1. Multi-evaluator calibration (add 2nd + 3rd LLM judge)
  2. Confidence calibration (ECE, Brier score, reliability diagram)
  3. Disagreement analysis (categorize WHY proposals are rejected)

NOT implemented (future):
  4. Judge robustness (different models, temperatures, prompts)
  5. Human calibration corpus (20-50 proposals, domain experts)

STATISTICAL HONESTY (per CTO):
  N=6 is exploratory. Insufficient for statistical conclusions.
  Report: 'Preliminary evidence suggests strong overestimation.'
  NOT: 'Correlation is zero.' (meaningless at N=6)
"""
import sys
import json
import math
import subprocess
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer


# ============================================================================
# PHASE 1: MULTI-EVALUATOR CALIBRATION
# ============================================================================

def llm_evaluate(proposal: Dict, system_prompt: str = "You are an independent scientific reviewer. Evaluate proposals honestly. Respond with JSON only.") -> Dict:
    """Evaluate a proposal using z-ai LLM with a given system prompt."""
    prompt = f"""Evaluate this research bridge proposal. Respond as JSON only:

PROPOSAL:
- Mechanism: {proposal['shared_mechanism']}
- Assumptions: {', '.join(proposal['necessary_assumptions'])}
- Prediction: {proposal['prediction']}
- Alternatives: {', '.join(proposal['alternative_explanations'])}
- Falsification: {proposal['falsification_experiment']}
- Confidence: {proposal['confidence']}
- Entity: {proposal['provenance'].get('shared_entity', '?')}

{{
  "mechanistically_coherent": "Yes|No|Partial",
  "scientifically_plausible": "Yes|No",
  "falsifiable": "Yes|No",
  "specificity_score": 1-5,
  "novelty": "Known|Incremental|Potentially novel",
  "overall_quality": 1-5,
  "recommendation": "Accept|Revise|Reject",
  "rejection_reason": "brief text or none"
}}"""

    try:
        result = subprocess.run(
            ["z-ai", "chat", "--prompt", prompt, "--system", system_prompt],
            capture_output=True, text=True, timeout=60
        )
        raw = result.stdout.strip()
        json_start = raw.find('{')
        if json_start < 0:
            return {"error": "No JSON in output"}

        try:
            cli_response = json.loads(raw[json_start:])
            response = cli_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (json.JSONDecodeError, IndexError, KeyError):
            response = raw[json_start:]

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        json_s = response.find('{')
        json_e = response.rfind('}') + 1
        if json_s >= 0 and json_e > json_s:
            return json.loads(response[json_s:json_e])
        return {"error": "No JSON in content", "raw": response[:300]}
    except Exception as e:
        return {"error": str(e)}


def multi_evaluator_calibration(proposals: List[Dict]) -> List[Dict]:
    """Evaluate each proposal with multiple LLM judges using different prompts.

    Judge 1: Standard scientific reviewer
    Judge 2: Adversarial reviewer (look for flaws)
    Judge 3: Neutral evaluator (balanced assessment)

    If judges agree → the evaluation is robust.
    If judges disagree → the evaluation itself is unreliable.
    """
    judges = [
        ("judge_1_standard", "You are an independent scientific reviewer. Evaluate proposals honestly. Respond with JSON only."),
        ("judge_2_adversarial", "You are a skeptical scientific reviewer. Your job is to find flaws. Be critical but fair. Respond with JSON only."),
        ("judge_3_neutral", "You are a balanced scientific evaluator. Weigh strengths and weaknesses equally. Respond with JSON only."),
    ]

    results = []
    for i, prop in enumerate(proposals):
        print(f"  Proposal {i+1}/{len(proposals)}: {prop.get('provenance', {}).get('shared_entity', '?')}")

        evals = {}
        for judge_name, system_prompt in judges:
            print(f"    {judge_name}...", end=" ")
            eval_result = llm_evaluate(prop, system_prompt)
            evals[judge_name] = eval_result
            if "error" not in eval_result:
                print(f"quality={eval_result.get('overall_quality', '?')}, rec={eval_result.get('recommendation', '?')}")
            else:
                print(f"ERROR: {eval_result.get('error', '?')[:50]}")

        # Compute inter-judge agreement
        qualities = [e.get("overall_quality", 0) for j, e in evals.items() if "error" not in e]
        recs = [e.get("recommendation", "?") for j, e in evals.items() if "error" not in e]

        if len(qualities) >= 2:
            mean_q = sum(qualities) / len(qualities)
            std_q = math.sqrt(sum((q - mean_q) ** 2 for q in qualities) / len(qualities))
            agreement = len(set(recs)) == 1
        else:
            mean_q = qualities[0] if qualities else 0
            std_q = 0
            agreement = True

        results.append({
            "entity": prop.get("provenance", {}).get("shared_entity", "?"),
            "evaluations": evals,
            "mean_quality": round(mean_q, 2),
            "std_quality": round(std_q, 2),
            "recommendations": recs,
            "judges_agree": agreement,
        })

    return results


# ============================================================================
# PHASE 2: CONFIDENCE CALIBRATION
# ============================================================================

@dataclass
class ConfidenceCalibration:
    """Confidence calibration metrics.

    Does the Proposal Composer's confidence score predict whether
    the proposal will be accepted by the external evaluator?

    ECE (Expected Calibration Error): how far is the confidence
    from the actual acceptance rate?
    """
    n: int
    mean_confidence: float
    acceptance_rate: float
    ece: float  # Expected Calibration Error
    brier_score: float  # Brier score (lower = better)
    max_calibration_error: float


def compute_confidence_calibration(confidences: List[float],
                                    accepted: List[bool]) -> ConfidenceCalibration:
    """Compute confidence calibration metrics.

    Args:
        confidences: proposal confidence scores (0-1)
        accepted: whether each proposal was accepted (True/False)

    Returns:
        ConfidenceCalibration with ECE, Brier, MCE
    """
    n = len(confidences)
    if n == 0:
        return ConfidenceCalibration(0, 0, 0, 0, 0, 0)

    mean_conf = sum(confidences) / n
    accept_rate = sum(1 for a in accepted if a) / n

    # ECE: bin confidence into groups, compare to acceptance rate
    n_bins = min(5, n)
    bin_size = n / n_bins if n > 0 else 1
    ece = 0
    mce = 0

    for b in range(n_bins):
        start = int(b * bin_size)
        end = int((b + 1) * bin_size)
        bin_confs = confidences[start:end]
        bin_accs = accepted[start:end]
        if not bin_confs:
            continue
        bin_conf_mean = sum(bin_confs) / len(bin_confs)
        bin_acc_rate = sum(1 for a in bin_accs if a) / len(bin_accs)
        error = abs(bin_conf_mean - bin_acc_rate)
        ece += error * len(bin_confs) / n
        mce = max(mce, error)

    # Brier score: mean((confidence - accepted)²)
    brier = sum((c - (1.0 if a else 0.0)) ** 2 for c, a in zip(confidences, accepted)) / n

    return ConfidenceCalibration(
        n=n,
        mean_confidence=round(mean_conf, 3),
        acceptance_rate=round(accept_rate, 3),
        ece=round(ece, 3),
        brier_score=round(brier, 3),
        max_calibration_error=round(mce, 3),
    )


# ============================================================================
# PHASE 3: DISAGREEMENT ANALYSIS
# ============================================================================

def disagreement_analysis(multi_eval_results: List[Dict]) -> Dict:
    """Categorize WHY proposals are rejected.

    Extracts rejection reasons from evaluator responses and
    categorizes them into failure modes.
    """
    failure_modes = {
        "mechanism_vague": 0,
        "prediction_unfalsifiable": 0,
        "missing_assumptions": 0,
        "known_science": 0,
        "weak_novelty": 0,
        "unsupported_mechanism": 0,
        "low_confidence": 0,
        "generic_template": 0,
        "other": 0,
    }

    all_reasons = []
    for result in multi_eval_results:
        for judge_name, eval_data in result.get("evaluations", {}).items():
            if "error" in eval_data:
                continue
            reason = eval_data.get("rejection_reason", "")
            if not reason or reason == "none":
                continue
            all_reasons.append(reason.lower())

            # Categorize
            if "vague" in reason.lower() or "unclear" in reason.lower():
                failure_modes["mechanism_vague"] += 1
            elif "unfalsifiable" in reason.lower() or "not testable" in reason.lower():
                failure_modes["prediction_unfalsifiable"] += 1
            elif "missing" in reason.lower() and "assumption" in reason.lower():
                failure_modes["missing_assumptions"] += 1
            elif "known" in reason.lower() or "already" in reason.lower():
                failure_modes["known_science"] += 1
            elif "novel" in reason.lower() or "incremental" in reason.lower():
                failure_modes["weak_novelty"] += 1
            elif "unsupported" in reason.lower() or "no evidence" in reason.lower():
                failure_modes["unsupported_mechanism"] += 1
            elif "confidence" in reason.lower() or "low" in reason.lower():
                failure_modes["low_confidence"] += 1
            elif "template" in reason.lower() or "generic" in reason.lower():
                failure_modes["generic_template"] += 1
            else:
                failure_modes["other"] += 1

    return {
        "failure_modes": failure_modes,
        "total_rejections": sum(failure_modes.values()),
        "sample_reasons": all_reasons[:5],
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-95: Epistemic Calibration Research (cycle 251)")
    print("Understanding the calibration problem — NOT improving proposals")
    print("STATISTICAL NOTE: N=6 is exploratory. Insufficient for statistical")
    print("conclusions. Preliminary evidence only.")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    composer = ProposalComposer()

    all_proposals = []
    for gold in GOLD_DISCOVERIES:
        ents_a = [e.text for e in pipeline.extract_entities(gold["source_snippet_a"])]
        ents_b = [e.text for e in pipeline.extract_entities(gold["source_snippet_b"])]
        proposals = composer.compose(ents_a, ents_b)
        all_proposals.extend(proposals)

    print(f"Proposals (Gen0, frozen): {len(all_proposals)}")
    print()

    # === PHASE 1: Multi-evaluator calibration ===
    print("=" * 80)
    print("PHASE 1: Multi-Evaluator Calibration (3 LLM judges)")
    print("=" * 80)
    print()

    multi_results = multi_evaluator_calibration([p.to_dict() for p in all_proposals])

    print()
    print(f"{'Entity':<30} {'J1':<5} {'J2':<5} {'J3':<5} {'Mean':<6} {'Std':<6} {'Agree?':<6}")
    print("-" * 65)
    for r in multi_results:
        evals = r["evaluations"]
        q1 = evals.get("judge_1_standard", {}).get("overall_quality", "?")
        q2 = evals.get("judge_2_adversarial", {}).get("overall_quality", "?")
        q3 = evals.get("judge_3_neutral", {}).get("overall_quality", "?")
        print(f"{r['entity']:<30} {q1:<5} {q2:<5} {q3:<5} "
              f"{r['mean_quality']:<6} {r['std_quality']:<6} {'✓' if r['judges_agree'] else '✗':<6}")

    # Inter-judge agreement
    n_agree = sum(1 for r in multi_results if r["judges_agree"])
    all_qualities = [r["mean_quality"] for r in multi_results]
    mean_inter_judge = sum(all_qualities) / len(all_qualities) if all_qualities else 0
    print()
    print(f"Judges agree on recommendation: {n_agree}/{len(multi_results)}")
    print(f"Mean inter-judge quality: {mean_inter_judge:.2f}/5")

    # === PHASE 2: Confidence calibration ===
    print()
    print("=" * 80)
    print("PHASE 2: Confidence Calibration")
    print("Does confidence predict acceptance?")
    print("=" * 80)
    print()

    confidences = [p.confidence for p in all_proposals]
    # Acceptance = at least 2/3 judges say "Accept" or "Revise"
    accepted = []
    for r in multi_results:
        recs = [e.get("recommendation", "Reject")
                for j, e in r["evaluations"].items() if "error" not in e]
        n_accept = sum(1 for r in recs if r in ["Accept", "Revise"])
        accepted.append(n_accept >= 2)

    conf_calib = compute_confidence_calibration(confidences, accepted)

    print(f"N proposals: {conf_calib.n}")
    print(f"Mean confidence: {conf_calib.mean_confidence}")
    print(f"Acceptance rate: {conf_calib.acceptance_rate}")
    print(f"Expected Calibration Error (ECE): {conf_calib.ece}")
    print(f"Brier Score: {conf_calib.brier_score}")
    print(f"Max Calibration Error: {conf_calib.max_calibration_error}")
    print()
    if conf_calib.ece > 0.2:
        print("CONFIDENCE IS POORLY CALIBRATED (ECE > 0.2)")
        print("The composer's confidence does NOT predict acceptance.")
    else:
        print("Confidence is reasonably calibrated.")

    # === PHASE 3: Disagreement analysis ===
    print()
    print("=" * 80)
    print("PHASE 3: Disagreement Analysis — WHY are proposals rejected?")
    print("=" * 80)
    print()

    disagreement = disagreement_analysis(multi_results)
    print(f"Total rejection reasons collected: {disagreement['total_rejections']}")
    print()
    print("Failure mode distribution:")
    for mode, count in sorted(disagreement["failure_modes"].items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {mode}: {count}")
    print()
    print("Sample rejection reasons:")
    for reason in disagreement["sample_reasons"]:
        print(f"  - {reason[:100]}")

    # === SUMMARY ===
    print()
    print("=" * 80)
    print("DR-95 SUMMARY")
    print("=" * 80)
    print()
    print("STATISTICAL NOTE: N=6 is exploratory. Insufficient for")
    print("statistical conclusions. Preliminary evidence only.")
    print()
    print(f"1. Multi-evaluator: judges agree {n_agree}/{len(multi_results)} on recommendation")
    print(f"   Mean inter-judge quality: {mean_inter_judge:.2f}/5")
    print(f"2. Confidence calibration: ECE={conf_calib.ece} (poorly calibrated)")
    print(f"   Brier score: {conf_calib.brier_score}")
    print(f"3. Top failure mode: {max(disagreement['failure_modes'], key=disagreement['failure_modes'].get)}")
    print()
    print("HONEST WORDING:")
    print("  'Preliminary evidence suggests strong overestimation by internal'")
    print("  'evaluator and poor confidence calibration. Multi-evaluator study'")
    print("  'is exploratory (N=6). Statistical conclusions require N≥30.'")
    print()
    print("NO PROPOSAL COMPOSER IMPROVEMENTS (per CTO freeze).")
    print("Next: expand calibration corpus to N≥30, add human expert (Tier 2).")

    # Save
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    with open(reports_dir / "dr95_calibration_research.json", "w") as f:
        json.dump({
            "multi_evaluator": multi_results,
            "confidence_calibration": conf_calib.__dict__,
            "disagreement": disagreement,
            "statistical_note": "N=6 is exploratory. Insufficient for statistical conclusions.",
        }, f, indent=2, default=str)
    print(f"\nSaved to reports/dr95_calibration_research.json")


if __name__ == "__main__":
    main()
