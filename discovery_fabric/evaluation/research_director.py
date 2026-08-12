"""
Expert Funding Simulation — "Would an expert fund this?"

Asks: "You are a senior scientist deciding whether to allocate $10M research funding."
This is the calibration question — not "is this wrong?" but "is this worth pursuing?"
"""
import json
import sys
import re
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_text


FUNDING_SYSTEM = """You are a senior scientist on a research funding committee deciding whether to allocate $10M to this project.

You must be brutally honest. Most proposals are NOT worth funding.

Consider:
- Is the mechanism scientifically sound?
- Is the experiment feasible?
- Is the potential impact worth $10M?
- Is there a clear path from hypothesis to validation?
- What is the biggest risk?

Output ONLY valid JSON:
{
  "fund": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "2-3 sentence assessment",
  "missing_evidence": "what evidence is needed before funding",
  "critical_experiment": "the one experiment that would prove/disprove this",
  "impact_if_successful": "LOW/MEDIUM/HIGH/TRANSFORMATIONAL",
  "risk_level": "LOW/MEDIUM/HIGH/EXTREME"
}"""


def evaluate_funding(candidate):
    """Evaluate whether an expert would fund this candidate."""
    hyp = candidate.get("predicted_effect", "")
    emergent = candidate.get("emergent_property", "")
    conditions = candidate.get("required_conditions", [])
    measurement = candidate.get("measurement_method", "")
    failure = candidate.get("failure_condition", "")
    domains = candidate.get("source_domains", [])

    prompt = f"""Project: {emergent[:200]}
Hypothesis: {hyp[:200]}
Domains: {domains}
Required conditions: {conditions}
Measurement method: {measurement[:150]}
Failure condition: {failure[:150]}

Would you fund this with $10M?"""

    text = chat_text(prompt, system=FUNDING_SYSTEM, max_tokens=300)
    if not text:
        return None

    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None
    return None


if __name__ == "__main__":
    import json
    with open("discovery_fabric/combinations/combination_results.json") as f:
        data = json.load(f)

    candidates = data.get("combinations", [])
    print(f"Evaluating funding for {len(candidates)} candidates...\n")

    results = []
    for i, c in enumerate(candidates):
        print(f"  [{i+1}/{len(candidates)}] {c['id']}...", end=" ", flush=True)
        funding = evaluate_funding(c)
        if funding:
            c["funding_evaluation"] = funding
            print(f"fund={funding.get('fund','?')} conf={funding.get('confidence','?')} impact={funding.get('impact_if_successful','?')}")
        else:
            print("FAILED")
        results.append(c)
        time.sleep(1)

    with open("discovery_fabric/evaluation/funding_evaluations.json", "w") as f:
        json.dump({"candidates": results}, f, indent=2, ensure_ascii=False)

    print(f"\n=== FUNDING DECISIONS ===")
    for c in results:
        fe = c.get("funding_evaluation", {})
        print(f"  {c['id']}: fund={fe.get('fund','?')} impact={fe.get('impact_if_successful','?')} risk={fe.get('risk_level','?')}")
        print(f"    {fe.get('reasoning','')[:100]}")
