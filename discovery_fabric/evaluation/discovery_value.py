"""
Discovery Value Model — multi-dimensional scoring for discovery calibration.

The goal: "Given 100 generated opportunities, can the system rank the
historically important ones higher?"

Dimensions:
  novelty_pressure: How much does this break from existing knowledge?
  constraint_release: Does this remove a previously blocking constraint?
  market_need: Is there a real-world problem this solves?
  scientific_gap: Does this fill a known gap in understanding?
  implementation_readiness: Can this be tested with current technology?
  unexpectedness: Would experts be surprised if this worked?
  historical_similarity: Does this resemble known high-impact discoveries?
"""
import json
import sys
import re
import time
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_text


VALUE_SYSTEM = """You are a discovery value assessor for a scientific discovery engine.

Score each candidate on 7 dimensions (0-100 each):

1. novelty_pressure: How much does this break from existing knowledge? (0=incremental, 100=paradigm shift)
2. constraint_release: Does this remove a previously blocking constraint? (0=no constraint removed, 100=major bottleneck removed)
3. market_need: Is there a real-world problem this solves? (0=no clear need, 100=critical unmet need)
4. scientific_gap: Does this fill a known gap in understanding? (0=no gap, 100=fills major theoretical gap)
5. implementation_readiness: Can this be tested with current technology? (0=requires new tech, 100=testable today)
6. unexpectedness: Would experts be surprised if this worked? (0=expected, 100=completely unexpected)
7. historical_similarity: Does this resemble known high-impact discoveries? (0=no resemblance, 100=strongly resembles major breakthrough)

Also provide an overall assessment.

Output ONLY valid JSON:
{
  "novelty_pressure": 0,
  "constraint_release": 0,
  "market_need": 0,
  "scientific_gap": 0,
  "implementation_readiness": 0,
  "unexpectedness": 0,
  "historical_similarity": 0,
  "overall_assessment": "brief assessment of discovery value",
  "would_expert_fund": true/false,
  "funding_reasoning": "why an expert would or would not fund this"
}"""


def score_candidate(hypothesis, emergent_property, prediction, mechanism_a, mechanism_b):
    """Score a candidate on 7 discovery value dimensions."""
    prompt = f"""Candidate hypothesis: {hypothesis[:200]}
Emergent property: {emergent_property[:200]}
Prediction: {prediction[:200]}
Mechanism A: {mechanism_a[:100]}
Mechanism B: {mechanism_b[:100]}

Score this candidate on all 7 dimensions."""

    text = chat_text(prompt, system=VALUE_SYSTEM, max_tokens=400)
    if not text:
        return None

    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None


def score_all_candidates(candidates_file, output_file):
    """Score all candidates in a results file."""
    with open(candidates_file) as f:
        data = json.load(f)

    candidates = data.get("combinations", [])
    print(f"Scoring {len(candidates)} candidates...")

    scored = []
    for i, c in enumerate(candidates):
        print(f"  [{i+1}/{len(candidates)}] {c['id']}...", end=" ", flush=True)

        score = score_candidate(
            c.get("predicted_effect", ""),
            c.get("emergent_property", ""),
            c.get("predicted_effect", ""),
            c.get("invariant_a", ""),
            c.get("invariant_b", ""),
        )

        if score:
            c["discovery_value"] = score
            overall = (score.get("novelty_pressure",0) + score.get("constraint_release",0) +
                      score.get("market_need",0) + score.get("scientific_gap",0) +
                      score.get("implementation_readiness",0) + score.get("unexpectedness",0) +
                      score.get("historical_similarity",0)) / 7
            c["discovery_value_overall"] = round(overall, 1)
            print(f"score={overall:.0f} fund={score.get('would_expert_fund','?')}")
        else:
            c["discovery_value"] = None
            c["discovery_value_overall"] = 0
            print("FAILED")

        scored.append(c)
        time.sleep(1)

    # Sort by discovery value
    scored.sort(key=lambda c: c.get("discovery_value_overall", 0), reverse=True)

    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_scored": len(scored),
            "candidates": scored,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {output_file}")
    print(f"\n=== DISCOVERY VALUE RANKING ===")
    for i, c in enumerate(scored):
        dv = c.get("discovery_value", {})
        print(f"  {i+1}. {c['id']} — score={c.get('discovery_value_overall',0)} "
              f"fund={dv.get('would_expert_fund','?')} "
              f"novelty={dv.get('novelty_pressure','?')} "
              f"constraint={dv.get('constraint_release','?')} "
              f"unexpected={dv.get('unexpectedness','?')}")

    return scored


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="discovery_fabric/combinations/combination_results.json")
    parser.add_argument("--output", default="discovery_fabric/evaluation/discovery_value_scores.json")
    args = parser.parse_args()
    score_all_candidates(args.candidates, args.output)
