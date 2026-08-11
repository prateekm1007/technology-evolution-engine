"""
Mechanism Similarity Scorer V2 — calibrated scoring that doesn't create false negatives.

Categories:
  EXACT_MATCH: Proposal captures the exact mechanism
  MECHANISM_MATCH: Proposal captures the core mechanism, may use different words
  COMPONENT_MATCH: Proposal captures key components but misses the integration
  PARTIAL_INSIGHT: Proposal captures one important element
  FAILURE: Proposal is fundamentally different

The V1 scorer was too strict — it rated "RNA-guided Cas9 nuclease for genome editing" 
as MISSED when the actual discovery was "Cas9 + guide RNA = programmable DNA cleavage".
These are the same mechanism described differently.
"""
import json
import sys
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json, chat_text


SCORER_SYSTEM = """You are a mechanism similarity scorer for a scientific discovery engine.

Your job: Compare a PROPOSED mechanism to an ACTUAL historical discovery mechanism and score how well they match.

CRITICAL: You must recognize when two descriptions use different words for the SAME mechanism. This is the most common scoring error.

Scoring categories:
- EXACT_MATCH: The proposal captures the exact mechanism, possibly with different terminology
- MECHANISM_MATCH: The proposal captures the CORE mechanism (the key insight that made it a discovery), even if it misses implementation details
- COMPONENT_MATCH: The proposal captures KEY COMPONENTS of the discovery but misses the crucial integration or insight
- PARTIAL_INSIGHT: The proposal captures ONE important element but misses the core mechanism
- FAILURE: The proposal is fundamentally different from the actual discovery

EXAMPLES:
- Proposed: "RNA-guided Cas9 nuclease for genome editing"
  Actual: "Cas9 + guide RNA = programmable DNA cleavage in eukaryotes"
  Score: MECHANISM_MATCH (same mechanism, different words)

- Proposed: "Modified mRNA encoding viral spike proteins"
  Actual: "Nucleoside-modified mRNA + lipid nanoparticle delivery = vaccine"
  Score: COMPONENT_MATCH (captures mRNA modification but misses delivery component)

- Proposed: "Thermally stable DNA polymerase"
  Actual: "Thermal cycling + Taq polymerase = exponential DNA amplification"
  Score: COMPONENT_MATCH (captures the enzyme but misses the cycling concept)

Output JSON:
{
  "score": "EXACT_MATCH/MECHANISM_MATCH/COMPONENT_MATCH/PARTIAL_INSIGHT/FAILURE",
  "match_quality": 0.0-1.0,
  "core_mechanism_captured": true/false,
  "missing_components": ["list of missing elements"],
  "reasoning": "brief explanation"
}"""


def score_mechanism_similarity(proposed, actual, discovery_name=""):
    """Score similarity between proposed and actual mechanism."""
    prompt = f"""Discovery: {discovery_name}

Proposed mechanism: {proposed}
Actual mechanism: {actual}

Score the match. Remember: different words can describe the same mechanism."""

    result = chat_json(prompt, system=SCORER_SYSTEM, max_tokens=300)
    if not result:
        return {"score": "FAILURE", "match_quality": 0.0, "reasoning": "LLM failed"}

    return result


def rescore_backtest(backtest_file, output_file):
    """Re-score a backtest results file with the V2 scorer."""
    with open(backtest_file) as f:
        report = json.load(f)

    results = report.get("results", [])
    print(f"Re-scoring {len(results)} cases with V2 scorer...\n")

    for i, r in enumerate(results):
        proposed = r.get("proposed_mechanism", "")
        actual = r.get("actual_mechanism", "")
        name = r.get("name", "")

        print(f"  [{i+1}/{len(results)}] {name}...", end=" ", flush=True)

        score_result = score_mechanism_similarity(proposed, actual, name)

        r["v2_score"] = score_result.get("score", "FAILURE")
        r["v2_quality"] = score_result.get("match_quality", 0)
        r["v2_core_captured"] = score_result.get("core_mechanism_captured", False)
        r["v2_missing"] = score_result.get("missing_components", [])
        r["v2_reasoning"] = score_result.get("reasoning", "")

        print(f"{r['v2_score']} (q={r['v2_quality']}) core={r['v2_core_captured']}")
        time.sleep(1)

    # Summary
    v2_scores = Counter(r.get("v2_score", "FAILURE") for r in results)
    v2_avg = sum(r.get("v2_quality", 0) for r in results) / max(len(results), 1)
    v2_core = sum(1 for r in results if r.get("v2_core_captured", False))

    report["v2_summary"] = {
        "scores": dict(v2_scores),
        "avg_quality": round(v2_avg, 2),
        "core_mechanism_captured": v2_core,
        "core_mechanism_rate": f"{100*v2_core/max(len(results),1):.0f}%",
    }

    # Recovery rates
    exact_or_mechanism = v2_scores.get("EXACT_MATCH", 0) + v2_scores.get("MECHANISM_MATCH", 0)
    any_match = exact_or_mechanism + v2_scores.get("COMPONENT_MATCH", 0) + v2_scores.get("PARTIAL_INSIGHT", 0)

    report["v2_recovery"] = {
        "strict_recovery": f"{exact_or_mechanism}/{len(results)} ({100*exact_or_mechanism/max(len(results),1):.0f}%)",
        "lenient_recovery": f"{any_match}/{len(results)} ({100*any_match/max(len(results),1):.0f}%)",
        "core_captured": f"{v2_core}/{len(results)} ({100*v2_core/max(len(results),1):.0f}%)",
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n=== V2 SCORER RESULTS ===")
    print(f"  EXACT_MATCH: {v2_scores.get('EXACT_MATCH',0)}")
    print(f"  MECHANISM_MATCH: {v2_scores.get('MECHANISM_MATCH',0)}")
    print(f"  COMPONENT_MATCH: {v2_scores.get('COMPONENT_MATCH',0)}")
    print(f"  PARTIAL_INSIGHT: {v2_scores.get('PARTIAL_INSIGHT',0)}")
    print(f"  FAILURE: {v2_scores.get('FAILURE',0)}")
    print(f"  Avg quality: {v2_avg:.2f}")
    print(f"  Core mechanism captured: {v2_core}/{len(results)} ({100*v2_core/max(len(results),1):.0f}%)")
    print(f"\n  Strict recovery (EXACT+MECHANISM): {exact_or_mechanism}/{len(results)}")
    print(f"  Lenient recovery (any match): {any_match}/{len(results)}")
    print(f"\n  Saved: {output_file}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="discovery_fabric/evaluation/historical_backtest/backtest_results.json")
    parser.add_argument("--output", default="discovery_fabric/evaluation/scorer_v2/rescored_results.json")
    args = parser.parse_args()
    rescore_backtest(args.input, args.output)
