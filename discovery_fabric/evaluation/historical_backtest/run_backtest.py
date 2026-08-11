"""
Historical Blind Backtest — can the engine rediscover known discoveries
using only pre-discovery evidence?
"""
import json, sys, re, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json

BENCHMARK_FILE = REPO / "discovery_fabric/benchmarks/historical_blind/dataset.json"
OUTPUT_DIR = REPO / "discovery_fabric/evaluation/historical_backtest"

BACKTEST_SYSTEM = """You are a scientific discovery engine. You are given ONLY information available BEFORE a discovery was made.

Your job: Given pre-discovery knowledge, what novel mechanism combination or transfer would you propose?

CRITICAL RULES:
1. You CANNOT see the discovery that was actually made.
2. Base your proposal ONLY on the pre-discovery evidence provided.
3. Propose a specific, testable mechanism — not a vague analogy.
4. Identify what CONSTRAINT needs to be overcome.
5. Predict what would happen if the mechanism works.

Output JSON:
{"proposed_mechanism":"","mechanism_combination":"","constraint_to_overcome":"","predicted_effect":"","experiment":"","confidence":0.0}"""


def run_case(case):
    name = case["name"]
    pre_sources = case["pre_discovery_sources"]
    known_before = case["known_mechanism_before"]
    actual = case["actual_breakthrough_mechanism"]
    pattern = case["discovery_pattern"]

    prompt = f"""PRE-DISCOVERY KNOWLEDGE (no future information available):

Known mechanisms and evidence:
{known_before}

Available research threads:
{chr(10).join(f'- {s}' for s in pre_sources)}

Based ONLY on the above pre-discovery knowledge, what novel mechanism combination or transfer would you propose as the most promising scientific opportunity?"""

    result = chat_json(prompt, system=BACKTEST_SYSTEM, max_tokens=600)
    if not result:
        return {"case_id": case["id"], "name": name, "score": "MISSED", "match_quality": 0, "reasoning": "LLM failed"}

    proposed = result.get("proposed_mechanism", "")
    combination = result.get("mechanism_combination", "")
    constraint = result.get("constraint_to_overcome", "")

    # Score against actual
    scoring_prompt = f"""Evaluate whether a proposed discovery matches the actual historical discovery.

Actual discovery: {name}
Actual mechanism: {actual}
Proposed mechanism: {proposed}
Proposed combination: {combination}

Score: FOUND (closely matches), PARTIAL (captures key elements), MISSED (does not match).
Output JSON: {{"score":"FOUND/PARTIAL/MISSED","match_quality":0.0-1.0,"reasoning":"brief"}}"""

    score_result = chat_json(scoring_prompt, max_tokens=200)
    score = "MISSED"
    quality = 0.0
    reasoning = ""

    if score_result:
        score = score_result.get("score", "MISSED")
        quality = score_result.get("match_quality", 0.0)
        reasoning = score_result.get("reasoning", "")

    return {
        "case_id": case["id"], "name": name, "discovery_pattern": pattern,
        "proposed_mechanism": proposed[:200], "proposed_combination": combination[:200],
        "constraint_identified": constraint[:200], "actual_mechanism": actual[:200],
        "score": score, "match_quality": quality, "reasoning": reasoning[:200],
        "confidence": result.get("confidence", 0),
    }


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Historical Blind Backtest V1.9\n")

    with open(BENCHMARK_FILE) as f:
        cases = json.load(f)
    print(f"  Cases: {len(cases)}")

    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] {case['name']} ({case['discovery_pattern']})...", end=" ", flush=True)
        r = run_case(case)
        results.append(r)
        print(f"{r['score']} (q={r['match_quality']})")
        time.sleep(2)

    scores = Counter(r["score"] for r in results)
    by_pattern = {}
    for r in results:
        p = r.get("discovery_pattern", "?")
        if p not in by_pattern: by_pattern[p] = {"FOUND":0,"PARTIAL":0,"MISSED":0,"total":0}
        by_pattern[p][r["score"]] += 1
        by_pattern[p]["total"] += 1

    avg_q = sum(r["match_quality"] for r in results) / max(len(results), 1)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(results), "scores": dict(scores),
        "avg_match_quality": round(avg_q, 2), "by_pattern": by_pattern, "results": results,
    }

    with open(OUTPUT_DIR / "backtest_results.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n=== RESULTS ===")
    print(f"  FOUND: {scores.get('FOUND',0)} | PARTIAL: {scores.get('PARTIAL',0)} | MISSED: {scores.get('MISSED',0)}")
    print(f"  Avg quality: {avg_q:.2f}")
    for p, s in by_pattern.items():
        print(f"  {p}: F={s['FOUND']} P={s['PARTIAL']} M={s['MISSED']} (n={s['total']})")
    print(f"  Saved: {OUTPUT_DIR / 'backtest_results.json'}")
    return report

if __name__ == "__main__":
    main()
