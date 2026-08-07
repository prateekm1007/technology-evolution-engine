#!/usr/bin/env python3
"""
dr93_5_independent_validation.py — DR-93.5: Independent Proposal Validation (cycle 249).

Per CTO directive:
  "Would an independent reviewer judge these proposals to be meaningful
   scientific hypotheses? The proposals should be evaluated independently
   of the Proposal Composer. No module validates itself."

Uses z-ai LLM as an INDEPENDENT evaluator (not the system that generated
the proposals). The LLM receives each proposal and scores it on:
  - Mechanistically coherent? (Yes/No/Partial)
  - Scientifically plausible? (Yes/No)
  - Falsifiable? (Yes/No)
  - Specific enough to test? (1-5)
  - Novel or already known? (Known/Incremental/Potentially novel)
  - Missing assumptions? (free text)
  - Major scientific flaw? (free text)

HONEST WORDING (per CTO):
  "5 proposals were not identified by the current heuristic as matching
   known examples; independent novelty assessment has not yet been
   performed." (NOT "5 potentially novel")

  This module performs that independent assessment.
"""
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer


def llm_evaluate_proposal(proposal: Dict) -> Dict:
    """Use z-ai LLM as an independent evaluator for one proposal.

    The LLM receives the proposal text and returns structured ratings.
    This is an INDEPENDENT evaluation — the LLM did not generate the
    proposal and has no knowledge of the Proposal Composer's logic.
    """
    prompt = f"""You are an independent scientific reviewer. Evaluate the following research bridge proposal.

PROPOSAL:
- Shared Mechanism: {proposal['shared_mechanism']}
- Necessary Assumptions: {', '.join(proposal['necessary_assumptions'])}
- Prediction: {proposal['prediction']}
- Alternative Explanations: {', '.join(proposal['alternative_explanations'])}
- Counterexample: {proposal['counterexample']}
- Falsification Experiment: {proposal['falsification_experiment']}
- Confidence: {proposal['confidence']}
- Shared Entity: {proposal['provenance'].get('shared_entity', 'unknown')}

Rate this proposal on the following criteria. Respond as JSON only:

{{
  "mechanistically_coherent": "Yes|No|Partial",
  "scientifically_plausible": "Yes|No",
  "falsifiable": "Yes|No",
  "specificity_score": 1-5,
  "novelty": "Known|Incremental|Potentially novel",
  "missing_assumptions": "brief text or none",
  "major_flaw": "brief text or none",
  "overall_quality": 1-5,
  "recommendation": "Accept|Revise|Reject"
}}"""

    try:
        result = subprocess.run(
            ["z-ai", "chat", "--prompt", prompt,
             "--system", "You are an independent scientific reviewer. Evaluate proposals honestly. Respond with JSON only."],
            capture_output=True, text=True, timeout=60
        )
        # z-ai CLI prints status messages before JSON output
        # Find the JSON object in stdout (starts with {)
        raw = result.stdout.strip()
        json_start = raw.find('{')
        if json_start < 0:
            return {"error": "No JSON in CLI output", "raw": raw[:500]}

        try:
            cli_response = json.loads(raw[json_start:])
            response = cli_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (json.JSONDecodeError, IndexError, KeyError):
            response = raw[json_start:]

        # Parse JSON from the response content (may be wrapped in ```json)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            evaluation = json.loads(json_str)
            return evaluation
        else:
            return {
                "error": "Could not parse JSON from LLM response",
                "raw_response": response[:500],
            }
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=" * 80)
    print("DR-93.5: Independent Proposal Validation (cycle 249)")
    print("LLM as independent scientific reviewer")
    print("NO MODULE VALIDATES ITSELF (per governance principle)")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    composer = ProposalComposer()

    # Compose proposals
    all_proposals = []
    for gold in GOLD_DISCOVERIES:
        ents_a = [e.text for e in pipeline.extract_entities(gold["source_snippet_a"])]
        ents_b = [e.text for e in pipeline.extract_entities(gold["source_snippet_b"])]
        proposals = composer.compose(ents_a, ents_b,
                                      source_a_id=gold.get("id", "a"),
                                      source_b_id=gold.get("id", "b"))
        all_proposals.extend(proposals)

    print(f"Total proposals to evaluate: {len(all_proposals)}")
    print()

    # Independent LLM evaluation
    print("=" * 80)
    print("INDEPENDENT LLM EVALUATION")
    print("=" * 80)
    print()

    results = []
    for i, p in enumerate(all_proposals):
        print(f"Evaluating proposal {i+1}/{len(all_proposals)}: {p.proposal_id}")
        print(f"  Entity: {p.provenance.get('shared_entity', '?')}")
        eval_result = llm_evaluate_proposal(p.to_dict())
        results.append({
            "proposal_id": p.proposal_id,
            "entity": p.provenance.get("shared_entity", ""),
            "evaluation": eval_result,
        })

        if "error" in eval_result:
            print(f"  ERROR: {eval_result['error']}")
        else:
            print(f"  Coherent: {eval_result.get('mechanistically_coherent', '?')}")
            print(f"  Plausible: {eval_result.get('scientifically_plausible', '?')}")
            print(f"  Falsifiable: {eval_result.get('falsifiable', '?')}")
            print(f"  Specificity: {eval_result.get('specificity_score', '?')}/5")
            print(f"  Novelty: {eval_result.get('novelty', '?')}")
            print(f"  Overall: {eval_result.get('overall_quality', '?')}/5")
            print(f"  Recommendation: {eval_result.get('recommendation', '?')}")
            if eval_result.get('major_flaw', 'none') != 'none':
                print(f"  Major flaw: {eval_result.get('major_flaw')}")
        print()

    # Aggregate
    print("=" * 80)
    print("AGGREGATE INDEPENDENT EVALUATION")
    print("=" * 80)
    print()

    n = len(results)
    valid = [r for r in results if "error" not in r.get("evaluation", {})]
    n_valid = len(valid)

    if n_valid == 0:
        print("No valid evaluations obtained. Check LLM availability.")
        return

    coherent = sum(1 for r in valid if r["evaluation"].get("mechanistically_coherent") in ["Yes", "Partial"])
    plausible = sum(1 for r in valid if r["evaluation"].get("scientifically_plausible") == "Yes")
    falsifiable = sum(1 for r in valid if r["evaluation"].get("falsifiable") == "Yes")
    known = sum(1 for r in valid if r["evaluation"].get("novelty") == "Known")
    incremental = sum(1 for r in valid if r["evaluation"].get("novelty") == "Incremental")
    novel = sum(1 for r in valid if r["evaluation"].get("novelty") == "Potentially novel")
    accept = sum(1 for r in valid if r["evaluation"].get("recommendation") == "Accept")
    reject = sum(1 for r in valid if r["evaluation"].get("recommendation") == "Reject")

    avg_quality = sum(r["evaluation"].get("overall_quality", 0) for r in valid) / n_valid
    avg_specificity = sum(r["evaluation"].get("specificity_score", 0) for r in valid) / n_valid

    print(f"Proposals evaluated: {n_valid}/{n}")
    print(f"Mechanistically coherent: {coherent}/{n_valid}")
    print(f"Scientifically plausible: {plausible}/{n_valid}")
    print(f"Falsifiable: {falsifiable}/{n_valid}")
    print(f"Average quality: {avg_quality:.2f}/5")
    print(f"Average specificity: {avg_specificity:.2f}/5")
    print()
    print(f"Novelty assessment (INDEPENDENT):")
    print(f"  Known: {known}/{n_valid}")
    print(f"  Incremental: {incremental}/{n_valid}")
    print(f"  Potentially novel: {novel}/{n_valid}")
    print()
    print(f"Recommendation: Accept={accept}, Reject={reject}, Revise={n_valid-accept-reject}")

    # Write permanent report
    print()
    print("=" * 80)
    print("PROPOSAL EVALUATION REPORT")
    print("=" * 80)

    report_path = Path(__file__).resolve().parents[2] / "PROPOSAL_EVALUATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# Proposal Evaluation Report\n\n")
        f.write("## DR-93.5: Independent LLM Validation\n\n")
        f.write(f"**Evaluator:** z-ai LLM (independent of Proposal Composer)\n")
        f.write(f"**Proposals evaluated:** {n_valid}/{n}\n")
        f.write(f"**Date:** cycle 249\n\n")
        f.write("## Aggregate Results\n\n")
        f.write(f"| Criterion | Result |\n|---|---|\n")
        f.write(f"| Mechanistically coherent | {coherent}/{n_valid} |\n")
        f.write(f"| Scientifically plausible | {plausible}/{n_valid} |\n")
        f.write(f"| Falsifiable | {falsifiable}/{n_valid} |\n")
        f.write(f"| Average quality | {avg_quality:.2f}/5 |\n")
        f.write(f"| Average specificity | {avg_specificity:.2f}/5 |\n")
        f.write(f"| Known | {known}/{n_valid} |\n")
        f.write(f"| Incremental | {incremental}/{n_valid} |\n")
        f.write(f"| Potentially novel | {novel}/{n_valid} |\n")
        f.write(f"| Accept | {accept}/{n_valid} |\n")
        f.write(f"| Reject | {reject}/{n_valid} |\n\n")
        f.write("## Per-Proposal Details\n\n")
        for r in valid:
            e = r["evaluation"]
            f.write(f"### {r['proposal_id']}: {r['entity']}\n\n")
            f.write(f"- Coherent: {e.get('mechanistically_coherent', '?')}\n")
            f.write(f"- Plausible: {e.get('scientifically_plausible', '?')}\n")
            f.write(f"- Falsifiable: {e.get('falsifiable', '?')}\n")
            f.write(f"- Specificity: {e.get('specificity_score', '?')}/5\n")
            f.write(f"- Novelty: {e.get('novelty', '?')}\n")
            f.write(f"- Overall: {e.get('overall_quality', '?')}/5\n")
            f.write(f"- Recommendation: {e.get('recommendation', '?')}\n")
            if e.get('missing_assumptions', 'none') != 'none':
                f.write(f"- Missing assumptions: {e.get('missing_assumptions')}\n")
            if e.get('major_flaw', 'none') != 'none':
                f.write(f"- Major flaw: {e.get('major_flaw')}\n")
            f.write("\n")

    print(f"Saved to {report_path}")

    # Save JSON
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    with open(reports_dir / "independent_proposal_validation.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved to reports/independent_proposal_validation.json")


if __name__ == "__main__":
    main()
