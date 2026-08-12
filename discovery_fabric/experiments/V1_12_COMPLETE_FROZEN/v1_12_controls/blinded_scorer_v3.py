"""
Blinded Scorer V3 — cannot see whether target is real or fabricated.

Key design:
1. Scorer receives ONLY: proposed_mechanism + target_mechanism (no labels)
2. Calibrated on a SEPARATE dev set (never tuned on evaluation set)
3. Uses strict criteria: only MECHANISM_MATCH if the CORE mechanism is captured

The V2 scorer's problem: it scored 60% of FALSE discoveries as EXACT_MATCH.
This means it was matching "plausible sounding" text, not mechanism equivalence.

V3 fix: The scorer must identify the SPECIFIC MECHANISTIC INSIGHT that makes
the target a discovery, and check if the proposal captures THAT INSIGHT —
not just sounds similar.
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

from discovery_fabric.connectors.openrouter_llm import chat_text

OUTPUT_DIR = REPO / "discovery_fabric/evaluation/v1_12_controls"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


BLINDED_SCORE_SYSTEM = """You are a STRICT mechanism similarity scorer.

You receive two mechanism descriptions: a PROPOSAL and a TARGET. You do NOT know whether the target is a real historical discovery or a fabricated one. You must score ALL pairs identically.

Your job: Determine if the PROPOSAL captures the SPECIFIC MECHANISTIC INSIGHT of the TARGET.

The "specific mechanistic insight" is the KEY IDEA that makes the target a discovery — not just the general field or approach.

Scoring criteria (STRICT):
- MECHANISM_MATCH: The proposal captures the SPECIFIC key mechanistic insight of the target. The core idea must match, not just the field or materials.
- COMPONENT_MATCH: The proposal captures SOME important elements but MISSES the core insight that makes the target a discovery.
- NO_MATCH: The proposal is in a different direction or only superficially related.

CRITICAL: "Both mention lithium" is NOT a mechanism match. "Both propose intercalation chemistry" IS a mechanism match.

Example:
- Proposed: "Use lithium intercalation for energy storage"
- Target: "LiCoO2 cathode + graphite anode = reversible intercalation battery"
- Score: MECHANISM_MATCH (both capture intercalation as the key mechanism)

Example:
- Proposed: "RNA-guided DNA cleavage for gene editing"
- Target: "Cas9 + guide RNA = programmable DNA cleavage in eukaryotes"
- Score: MECHANISM_MATCH (same core mechanism)

Example:
- Proposed: "Nanoscale surface modification for catalysis"
- Target: "Quantum dot size-tunable emission for displays"
- Score: NO_MATCH (different mechanisms despite both involving nanoscale)

Output ONLY JSON: {"score":"MECHANISM_MATCH/COMPONENT_MATCH/NO_MATCH","quality":0.0-1.0,"core_insight":"the key insight of the target","proposal_captures_insight":true/false,"reasoning":"brief"}"""


def blinded_score(proposed, target):
    """Score a proposal against a target WITHOUT knowing if target is real or fabricated."""
    prompt = f"""PROPOSAL: {proposed}
TARGET: {target}

Score the mechanism match. What is the specific mechanistic insight of the TARGET? Does the PROPOSAL capture it?"""

    text = chat_text(prompt, system=BLINDED_SCORE_SYSTEM, max_tokens=200)
    if not text:
        return {"score": "NO_MATCH", "quality": 0.0, "reasoning": "LLM failed"}
    
    match = re.search(r'\{[^}]+\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"score": "NO_MATCH", "quality": 0.0, "reasoning": "parse failed"}


def rescore_with_blinded_scorer(results_file, label, output_file):
    """Re-score results with the blinded V3 scorer."""
    with open(results_file) as f:
        data = json.load(f)
    
    results = data.get("results", data.get("candidates", []))
    print(f"\n  Re-scoring {len(results)} {label} cases with BLINDED V3 scorer...")
    
    for i, r in enumerate(results):
        proposed = r.get("proposed", r.get("prediction", r.get("proposed_mechanism", "")))
        if not proposed or proposed == "LLM_FAILED":
            r["v3_score"] = "NO_MATCH"
            r["v3_quality"] = 0.0
            continue
        
        # For real discoveries: target is actual_discovery
        # For false discoveries: target is false_actual
        # For LLM-only: target is actual
        target = r.get("actual_discovery", r.get("actual", r.get("false_actual", "")))
        
        if not target:
            r["v3_score"] = "NO_MATCH"
            r["v3_quality"] = 0.0
            continue
        
        print(f"    [{i+1}/{len(results)}] {r.get('name','?')[:30]}...", end=" ", flush=True)
        score_result = blinded_score(proposed[:200], target[:200])
        r["v3_score"] = score_result.get("score", "NO_MATCH")
        r["v3_quality"] = score_result.get("quality", 0)
        r["v3_core_insight"] = score_result.get("core_insight", "")[:100]
        r["v3_captures"] = score_result.get("proposal_captures_insight", False)
        r["v3_reasoning"] = score_result.get("reasoning", "")[:100]
        print(f"{r['v3_score']} (q={r['v3_quality']})")
        time.sleep(1.5)
    
    # Summary
    v3_scores = Counter(r.get("v3_score", "NO_MATCH") for r in results)
    v3_strict = v3_scores.get("MECHANISM_MATCH", 0)
    v3_any = v3_strict + v3_scores.get("COMPONENT_MATCH", 0)
    v3_avg = sum(r.get("v3_quality", 0) for r in results) / max(len(results), 1)
    
    summary = {
        "label": label,
        "total": len(results),
        "v3_scores": dict(v3_scores),
        "v3_strict_recovery": f"{v3_strict}/{len(results)} ({100*v3_strict/max(len(results),1):.0f}%)",
        "v3_any_recovery": f"{v3_any}/{len(results)} ({100*v3_any/max(len(results),1):.0f}%)",
        "v3_avg_quality": round(v3_avg, 2),
    }
    
    data["v3_summary"] = summary
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n  {label} V3 Results:")
    print(f"    MECHANISM_MATCH: {v3_scores.get('MECHANISM_MATCH',0)}")
    print(f"    COMPONENT_MATCH: {v3_scores.get('COMPONENT_MATCH',0)}")
    print(f"    NO_MATCH: {v3_scores.get('NO_MATCH',0)}")
    print(f"    Strict recovery: {summary['v3_strict_recovery']}")
    print(f"    Avg quality: {v3_avg:.2f}")
    
    return summary


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.12 Blinded Scorer V3")
    print(f"  Goal: Does the gap between real and false survive strict blinded scoring?\n")
    
    # Re-score all three experiments with V3 blinded scorer
    # 1. Real discoveries (V1.11)
    real_summary = rescore_with_blinded_scorer(
        REPO / "discovery_fabric/evaluation/historical_backtest/benchmark_results_v1_11.json",
        "REAL discoveries",
        OUTPUT_DIR / "v3_real_discoveries.json"
    )
    
    # 2. LLM-only baseline
    llm_summary = rescore_with_blinded_scorer(
        OUTPUT_DIR / "llm_only_results.json",
        "LLM-only",
        OUTPUT_DIR / "v3_llm_only.json"
    )
    
    # 3. False discoveries
    false_summary = rescore_with_blinded_scorer(
        OUTPUT_DIR / "false_discovery_results.json",
        "FALSE discoveries",
        OUTPUT_DIR / "v3_false_discoveries.json"
    )
    
    # COMPARISON
    print(f"\n{'='*60}")
    print(f"V3 BLINDED SCORER COMPARISON")
    print(f"{'='*60}")
    print(f"  Real discoveries:  {real_summary['v3_strict_recovery']}")
    print(f"  LLM-only:          {llm_summary['v3_strict_recovery']}")
    print(f"  False discoveries: {false_summary['v3_strict_recovery']}")
    
    # Calculate the true gap
    real_rate = real_summary['v3_scores'].get('MECHANISM_MATCH', 0) / max(real_summary['total'], 1)
    false_rate = false_summary['v3_scores'].get('MECHANISM_MATCH', 0) / max(false_summary['total'], 1)
    llm_rate = llm_summary['v3_scores'].get('MECHANISM_MATCH', 0) / max(llm_summary['total'], 1)
    
    gap = real_rate - false_rate
    arch_advantage = real_rate - llm_rate
    
    print(f"\n  Real recovery rate:      {100*real_rate:.0f}%")
    print(f"  False recovery rate:     {100*false_rate:.0f}%")
    print(f"  LLM-only recovery rate:  {100*llm_rate:.0f}%")
    print(f"  Discovery gap (real-false): {100*gap:.0f}pp")
    print(f"  Architecture advantage (real-LLM): {100*arch_advantage:.0f}pp")
    
    print(f"\n  INTERPRETATION:")
    if gap > 0.2:
        print(f"  ✅ Discovery signal survives: {100*gap:.0f}pp gap between real and false")
    elif gap > 0:
        print(f"  ⚠️ Weak signal: {100*gap:.0f}pp gap (may not survive larger sample)")
    else:
        print(f"  ❌ NO signal: real and false recovery rates are equal or reversed")
    
    # Save final report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scorer_version": "V3_BLINDED",
        "real_discoveries": real_summary,
        "llm_only": llm_summary,
        "false_discoveries": false_summary,
        "real_recovery_rate": round(real_rate, 2),
        "false_recovery_rate": round(false_rate, 2),
        "llm_only_recovery_rate": round(llm_rate, 2),
        "discovery_gap": round(gap, 2),
        "architecture_advantage": round(arch_advantage, 2),
        "signal_survives": gap > 0.2,
    }
    
    with open(OUTPUT_DIR / "v3_blinded_comparison.json", 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Saved: {OUTPUT_DIR / 'v3_blinded_comparison.json'}")


if __name__ == "__main__":
    main()
