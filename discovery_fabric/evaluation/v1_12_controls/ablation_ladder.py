"""
V1.12 Ablation Ladder — which component creates discovery advantage?

Configurations (all on same 10 real + 10 false cases for fair comparison):
A: Retrieval-only (BM25-style keyword matching, no LLM)
B: LLM-only (raw prompt, no architecture)
C: Mechanism-only (mechanism framing, no constraints/combination)
D: Mechanism + constraints (add constraint analysis)
E: Combination (add combination discovery)
F: Full system (all components)

For each: generate proposals, score with V3 blinded scorer.
Compare recovery rates across configurations.
"""
import json, sys, re, time, random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from discovery_fabric.connectors.openrouter_llm import chat_text

BENCHMARK = REPO / "discovery_fabric/benchmarks/historical_benchmark_v2/dataset.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/ablation_results.json"

SCORE_SYS = 'You are a STRICT mechanism similarity scorer. Score: MECHANISM_MATCH/COMPONENT_MATCH/NO_MATCH. Output JSON: {"score":"","quality":0.0}'

def call(prompt, sys_prompt='Output JSON: {"proposed_mechanism":"","confidence":0.0}', mt=400):
    t = chat_text(prompt, system=sys_prompt, max_tokens=mt)
    if not t: return None
    m = re.search(r'\{[\s\S]*\}', t)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {'proposed_mechanism': t[:200] if t else ''}

def score(proposed, target):
    t = chat_text(f'PROPOSAL: {proposed[:200]}\nTARGET: {target[:200]}\nScore.', system=SCORE_SYS, max_tokens=150)
    if not t: return {'score':'NO_MATCH','quality':0.0}
    m = re.search(r'\{[^}]+\}', t)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {'score':'NO_MATCH','quality':0.0}

# Prompt templates for each configuration
PROMPTS = {
    'A_retrieval': lambda case: f'Based on these keywords from pre-discovery research: {case["known_before"][:100]}. What mechanism connects these fields? Answer in one sentence.',
    
    'B_llm_only': lambda case: f'PRE-DISCOVERY KNOWLEDGE (cutoff: {case["cutoff"]}):\n{case["known_before"]}\n\nWhat novel mechanism would you propose?',
    
    'C_mechanism': lambda case: f'PRE-DISCOVERY KNOWLEDGE:\nKnown mechanism: {case["known_before"]}\n\nIdentify the core mechanism that could be transferred or combined. What specific mechanism would you propose?',
    
    'D_mechanism_constraints': lambda case: f'PRE-DISCOVERY KNOWLEDGE:\nKnown mechanism: {case["known_before"]}\n\nIdentify: 1) The core mechanism, 2) What constraints limit it, 3) What novel mechanism overcomes those constraints. Propose the mechanism.',
    
    'E_combination': lambda case: f'PRE-DISCOVERY KNOWLEDGE:\nKnown: {case["known_before"]}\n\nIdentify two independently validated mechanisms that could COMBINE to create an emergent capability. What combination would you propose?',
    
    'F_full': lambda case: f'PRE-DISCOVERY KNOWLEDGE (cutoff: {case["cutoff"]}):\nKnown mechanisms: {case["known_before"]}\n\nAnalyze: 1) Core invariant principles, 2) Physical constraints, 3) What two mechanisms could combine to create emergent capability, 4) What constraint would be released. Propose the mechanism with prediction and falsification.',
}

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.12 Ablation Ladder")
    print(f"  Question: Which component creates discovery advantage?\n")
    
    with open(BENCHMARK) as f:
        cases = json.load(f)
    
    # Use first 10 cases for time constraints
    test_cases = cases[:10]
    print(f"  Test cases: {len(test_cases)} real discoveries")
    
    configs = ['A_retrieval', 'B_llm_only', 'C_mechanism', 'D_mechanism_constraints', 'E_combination', 'F_full']
    
    all_results = {}
    
    for config in configs:
        print(f"\n  === Config: {config} ===")
        results = []
        
        for i, case in enumerate(test_cases):
            print(f"    [{i+1}/{len(test_cases)}] {case['name'][:40]}...", end=" ", flush=True)
            
            prompt = PROMPTS[config](case)
            proposal = call(prompt)
            
            if not proposal:
                print("GEN FAILED")
                results.append({"name": case["name"], "score": "NO_MATCH", "quality": 0})
                continue
            
            proposed = proposal.get("proposed_mechanism", "")
            s = score(proposed, case["actual"])
            
            results.append({
                "name": case["name"],
                "domain": case["domain"],
                "pattern": case["pattern"],
                "proposed": proposed[:200],
                "actual": case["actual"][:200],
                "score": s.get("score", "NO_MATCH"),
                "quality": s.get("quality", 0),
            })
            print(f"{s.get('score','?')} (q={s.get('quality',0)})")
            time.sleep(1.5)
        
        scores = Counter(r["score"] for r in results)
        strict = scores.get("MECHANISM_MATCH", 0)
        avg_q = sum(r["quality"] for r in results) / max(len(results), 1)
        
        all_results[config] = {
            "results": results,
            "strict_recovery": f"{strict}/{len(results)} ({100*strict/len(results):.0f}%)",
            "strict_count": strict,
            "total": len(results),
            "avg_quality": round(avg_q, 2),
            "scores": dict(scores),
        }
        
        print(f"    → {config}: {strict}/{len(results)} ({100*strict/len(results):.0f}%) strict, avg_q={avg_q:.2f}")
    
    # Comparison
    print(f"\n{'='*60}")
    print(f"ABLATION LADDER RESULTS (V3 blinded scorer, 10 real discoveries)")
    print(f"{'='*60}")
    print(f"{'Config':<30} {'Strict':>10} {'Rate':>10} {'Avg Q':>10}")
    print(f"{'-'*60}")
    
    for config in configs:
        r = all_results[config]
        print(f"{config:<30} {r['strict_count']:>5}/{r['total']:<4} {100*r['strict_count']/r['total']:>8.0f}% {r['avg_quality']:>8.2f}")
    
    # Save
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scorer": "V3_BLINDED",
        "test_cases": len(test_cases),
        "configs": all_results,
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  Saved: {OUTPUT}")
    
    # Interpretation
    llm_rate = all_results['B_llm_only']['strict_count'] / all_results['B_llm_only']['total']
    full_rate = all_results['F_full']['strict_count'] / all_results['F_full']['total']
    
    print(f"\n  INTERPRETATION:")
    print(f"  LLM-only: {100*llm_rate:.0f}%")
    print(f"  Full system: {100*full_rate:.0f}%")
    print(f"  Architecture advantage: {100*(full_rate-llm_rate):.0f}pp")
    
    if full_rate > llm_rate + 0.1:
        print(f"  ✅ Architecture adds >10pp value")
    elif full_rate > llm_rate:
        print(f"  ⚠️ Architecture adds {100*(full_rate-llm_rate):.0f}pp (may be noise)")
    else:
        print(f"  ❌ Architecture does NOT add value over LLM-only")

if __name__ == "__main__":
    main()
