"""
V1.11 Full 50-Discovery Blind Benchmark

Runs all 50 historical discoveries through:
1. Pre-discovery evidence prompt (no future info)
2. V2 scorer calibration

Checkpoint after every case. Resume-safe.
"""
import json
import sys
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_json, chat_text

BENCHMARK_FILE = REPO / "discovery_fabric/benchmarks/historical_benchmark_v2/dataset.json"
CHECKPOINT_FILE = REPO / "discovery_fabric/evaluation/historical_backtest/v1_11_checkpoint.json"
OUTPUT_FILE = REPO / "discovery_fabric/evaluation/historical_backtest/benchmark_results_v1_11.json"

GEN_SYSTEM = """You are a scientific discovery engine. Given ONLY pre-discovery knowledge, propose a novel mechanism.
Output JSON: {"proposed_mechanism":"","mechanism_combination":"","constraint_to_overcome":"","predicted_effect":"","confidence":0.0}"""

SCORE_SYSTEM = """You are a mechanism similarity scorer. Compare proposed vs actual mechanism.
Score: EXACT_MATCH, MECHANISM_MATCH, COMPONENT_MATCH, PARTIAL_INSIGHT, or FAILURE.
- MECHANISM_MATCH = same core mechanism, different words
- COMPONENT_MATCH = captures key components but misses integration
Output ONLY JSON: {"score":"","quality":0.0,"reasoning":""}"""


def generate_proposal(case):
    """Generate a discovery proposal from pre-discovery evidence only."""
    prompt = f"""PRE-DISCOVERY KNOWLEDGE (cutoff: {case['cutoff']}):

Known mechanisms and evidence:
{case['known_before']}

Available research threads:
{chr(10).join(f'- {s}' for s in case.get('pre_discovery_sources', case.get('missing', '').split(';')))}

Based ONLY on pre-discovery knowledge, what novel mechanism would you propose?"""

    text = chat_text(prompt, system=GEN_SYSTEM, max_tokens=400)
    if not text:
        return None
    
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"proposed_mechanism": text[:200], "confidence": 0.0}


def score_proposal(proposed, actual, name):
    """Score proposal against actual discovery using V2 scorer."""
    prompt = f'Compare:\nProposed: {proposed}\nActual: {actual}\n\nDiscovery: {name}\nScore: EXACT_MATCH/MECHANISM_MATCH/COMPONENT_MATCH/PARTIAL_INSIGHT/FAILURE\nOutput JSON: {{"score":"","quality":0.0,"reasoning":""}}'
    
    text = chat_text(prompt, system=SCORE_SYSTEM, max_tokens=150)
    if not text:
        return {"score": "FAILURE", "quality": 0.0, "reasoning": "LLM failed"}
    
    match = re.search(r'\{[^}]+\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"score": "FAILURE", "quality": 0.0, "reasoning": "parse failed"}


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed": [], "results": []}


def save_checkpoint(cp):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.11 Full 50-Discovery Blind Benchmark\n")
    
    with open(BENCHMARK_FILE) as f:
        cases = json.load(f)
    
    cp = load_checkpoint()
    completed_ids = set(cp["completed"])
    
    print(f"  Total cases: {len(cases)}")
    print(f"  Already completed: {len(completed_ids)}")
    print(f"  Remaining: {len(cases) - len(completed_ids)}")
    
    for i, case in enumerate(cases):
        cid = case["id"]
        if cid in completed_ids:
            continue
        
        print(f"  [{i+1}/{len(cases)}] {case['name']} ({case['domain']}/{case['pattern']})...", end=" ", flush=True)
        
        # Step 1: Generate proposal from pre-discovery evidence
        proposal = generate_proposal(case)
        
        if not proposal:
            print("GEN FAILED")
            result = {
                "discovery_id": cid, "name": case["name"], "domain": case["domain"],
                "pattern": case["pattern"], "cutoff_date": case["cutoff"],
                "prediction": "LLM_FAILED", "actual": case["actual"],
                "score_category": "FAILURE", "quality_score": 0.0,
            }
        else:
            proposed_mechanism = proposal.get("proposed_mechanism", "")
            combination = proposal.get("mechanism_combination", "")
            constraint = proposal.get("constraint_to_overcome", "")
            prediction = proposal.get("predicted_effect", "")
            confidence = proposal.get("confidence", 0.0)
            
            # Step 2: Score with V2 scorer
            score = score_proposal(proposed_mechanism, case["actual"], case["name"])
            
            result = {
                "discovery_id": cid, "name": case["name"], "domain": case["domain"],
                "pattern": case["pattern"], "cutoff_date": case["cutoff"],
                "prediction": proposed_mechanism[:200],
                "mechanism_combination": combination[:200],
                "constraint_identified": constraint[:200],
                "predicted_effect": prediction[:200],
                "actual_discovery": case["actual"][:200],
                "score_category": score.get("score", "FAILURE"),
                "quality_score": score.get("quality", 0.0),
                "scorer_reasoning": score.get("reasoning", "")[:150],
                "confidence": confidence,
            }
            
            print(f"{result['score_category']} (q={result['quality_score']})")
        
        cp["results"].append(result)
        cp["completed"].append(cid)
        save_checkpoint(cp)
        
        time.sleep(1.5)
    
    # Final analysis
    results = cp["results"]
    scores = Counter(r["score_category"] for r in results)
    by_domain = {}
    for r in results:
        d = r["domain"]
        if d not in by_domain:
            by_domain[d] = {"total": 0, "EXACT_MATCH": 0, "MECHANISM_MATCH": 0, 
                           "COMPONENT_MATCH": 0, "PARTIAL_INSIGHT": 0, "FAILURE": 0}
        by_domain[d]["total"] += 1
        by_domain[d][r["score_category"]] += 1
    
    by_pattern = {}
    for r in results:
        p = r["pattern"]
        if p not in by_pattern:
            by_pattern[p] = {"total": 0, "EXACT_MATCH": 0, "MECHANISM_MATCH": 0,
                            "COMPONENT_MATCH": 0, "PARTIAL_INSIGHT": 0, "FAILURE": 0}
        by_pattern[p]["total"] += 1
        by_pattern[p][r["score_category"]] += 1
    
    avg_quality = sum(r["quality_score"] for r in results) / max(len(results), 1)
    strict_recovery = scores.get("EXACT_MATCH", 0) + scores.get("MECHANISM_MATCH", 0)
    any_recovery = strict_recovery + scores.get("COMPONENT_MATCH", 0) + scores.get("PARTIAL_INSIGHT", 0)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark_version": "V1.11",
        "scorer_version": "V2",
        "total_cases": len(results),
        "score_distribution": dict(scores),
        "strict_recovery": f"{strict_recovery}/{len(results)} ({100*strict_recovery/len(results):.0f}%)",
        "any_recovery": f"{any_recovery}/{len(results)} ({100*any_recovery/len(results):.0f}%)",
        "avg_quality": round(avg_quality, 2),
        "by_domain": by_domain,
        "by_pattern": by_pattern,
        "results": results,
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== V1.11 BENCHMARK RESULTS ===")
    print(f"  Total: {len(results)}")
    print(f"  EXACT_MATCH: {scores.get('EXACT_MATCH',0)} ({100*scores.get('EXACT_MATCH',0)/len(results):.0f}%)")
    print(f"  MECHANISM_MATCH: {scores.get('MECHANISM_MATCH',0)} ({100*scores.get('MECHANISM_MATCH',0)/len(results):.0f}%)")
    print(f"  COMPONENT_MATCH: {scores.get('COMPONENT_MATCH',0)} ({100*scores.get('COMPONENT_MATCH',0)/len(results):.0f}%)")
    print(f"  PARTIAL_INSIGHT: {scores.get('PARTIAL_INSIGHT',0)} ({100*scores.get('PARTIAL_INSIGHT',0)/len(results):.0f}%)")
    print(f"  FAILURE: {scores.get('FAILURE',0)} ({100*scores.get('FAILURE',0)/len(results):.0f}%)")
    print(f"  Strict recovery: {strict_recovery}/{len(results)} ({100*strict_recovery/len(results):.0f}%)")
    print(f"  Any recovery: {any_recovery}/{len(results)} ({100*any_recovery/len(results):.0f}%)")
    print(f"  Avg quality: {avg_quality:.2f}")
    print(f"\n  By domain:")
    for d, s in sorted(by_domain.items()):
        sr = s["EXACT_MATCH"] + s["MECHANISM_MATCH"]
        print(f"    {d}: {sr}/{s['total']} strict ({100*sr/s['total']:.0f}%)")
    print(f"\n  By pattern:")
    for p, s in sorted(by_pattern.items()):
        sr = s["EXACT_MATCH"] + s["MECHANISM_MATCH"]
        print(f"    {p}: {sr}/{s['total']} strict ({100*sr/max(s['total'],1):.0f}%)")
    print(f"\n  Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
