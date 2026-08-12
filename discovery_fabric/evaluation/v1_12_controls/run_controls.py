"""
V1.12 Validation Controls — hard-negative + LLM-leakage tests.

Experiment 1: Hard-negative control (false discoveries — does engine "rediscover" non-existent discoveries?)
Experiment 2: LLM-leakage test (LLM-only baseline — does architecture add value over LLM alone?)
"""
import json, sys, re, time, hashlib, random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from discovery_fabric.connectors.openrouter_llm import chat_text

BENCHMARK_FILE = REPO / "discovery_fabric/benchmarks/historical_benchmark_v2/dataset.json"
RESULTS_DIR = REPO / "discovery_fabric/evaluation/historical_backtest"
OUTPUT_DIR = REPO / "discovery_fabric/evaluation/v1_12_controls"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GEN_SYSTEM = "You are a scientific discovery engine. Given ONLY pre-discovery knowledge, propose a novel mechanism. Output JSON: {\"proposed_mechanism\":\"\",\"confidence\":0.0}"
SCORE_SYSTEM = "You are a mechanism similarity scorer. Score: EXACT_MATCH/MECHANISM_MATCH/COMPONENT_MATCH/PARTIAL_INSIGHT/FAILURE. Output JSON: {\"score\":\"\",\"quality\":0.0}"

def call_llm(prompt, system=GEN_SYSTEM, max_tokens=400):
    text = chat_text(prompt, system=system, max_tokens=max_tokens)
    if not text: return None
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try: return json.loads(match.group())
        except: pass
    return {"proposed_mechanism": text[:200] if text else "", "confidence": 0.0}

def score(proposed, actual, name=""):
    prompt = f'Compare:\nProposed: {proposed}\nActual: {actual}\nDiscovery: {name}\nScore: EXACT_MATCH/MECHANISM_MATCH/COMPONENT_MATCH/PARTIAL_INSIGHT/FAILURE\nOutput JSON: {{"score":"","quality":0.0}}'
    text = chat_text(prompt, system=SCORE_SYSTEM, max_tokens=150)
    if not text: return {"score":"FAILURE","quality":0.0}
    match = re.search(r'\{[^}]+\}', text)
    if match:
        try: return json.loads(match.group())
        except: pass
    return {"score":"FAILURE","quality":0.0}

def run_experiment2_llm_only(cases, n=15):
    """LLM-only baseline: same prompts, no architecture."""
    print(f"\n=== EXPERIMENT 2: LLM-ONLY BASELINE ({n} cases) ===")
    results = []
    for i, case in enumerate(cases[:n]):
        print(f"  [{i+1}/{n}] {case['name'][:40]}...", end=" ", flush=True)
        prompt = f"PRE-DISCOVERY KNOWLEDGE (cutoff: {case['cutoff']}):\n{case['known_before']}\n\nBased ONLY on pre-discovery knowledge, what novel mechanism would you propose?"
        proposal = call_llm(prompt)
        if not proposal:
            print("FAILED"); results.append({"name":case["name"],"score":"FAILURE","quality":0,"system":"llm_only"}); continue
        proposed = proposal.get("proposed_mechanism","")
        s = score(proposed, case["actual"], case["name"])
        results.append({"name":case["name"],"domain":case["domain"],"proposed":proposed[:200],"actual":case["actual"][:200],"score":s.get("score","FAILURE"),"quality":s.get("quality",0),"system":"llm_only"})
        print(f"{s.get('score','?')} (q={s.get('quality',0)})")
        time.sleep(1.5)
    return results

def run_experiment1_false_discoveries(cases, n=15):
    """Hard-negative: generate plausible but never-made discoveries, then test recovery."""
    print(f"\n=== EXPERIMENT 1: HARD-NEGATIVE CONTROL ({n} cases) ===")
    print("  Generating false discoveries...")
    false_discoveries = []
    for i, case in enumerate(cases[:n]):
        prompt = f"Domain: {case['domain']}, Pattern: {case['pattern']}, Known: {case['known_before']}\n\nCreate a discovery that SOUNDS plausible but was NEVER made. Output JSON: {{\"name\":\"\",\"actual\":\"the false mechanism\",\"known_before\":\"{case['known_before']}\"}}"
        result = call_llm(prompt, system="Output ONLY JSON.", max_tokens=250)
        if result:
            result["id"] = f"FD-{i+1:03d}"
            false_discoveries.append(result)
        time.sleep(1)
    
    print(f"  Generated {len(false_discoveries)} false discoveries")
    print("  Testing false discovery recovery...")
    
    results = []
    for i, fd in enumerate(false_discoveries):
        print(f"  [{i+1}/{len(false_discoveries)}] {fd.get('name','?')[:40]}...", end=" ", flush=True)
        prompt = f"PRE-DISCOVERY KNOWLEDGE:\n{fd.get('known_before','')}\n\nWhat novel mechanism would you propose?"
        proposal = call_llm(prompt)
        if not proposal:
            print("FAILED"); results.append({"name":fd.get("name",""),"score":"FAILURE","quality":0}); continue
        proposed = proposal.get("proposed_mechanism","")
        actual = fd.get("actual","")
        s = score(proposed, actual, fd.get("name",""))
        results.append({"name":fd.get("name",""),"proposed":proposed[:200],"false_actual":actual[:200],"score":s.get("score","FAILURE"),"quality":s.get("quality",0)})
        print(f"{s.get('score','?')} (q={s.get('quality',0)})")
        time.sleep(1.5)
    return results

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] V1.12 Validation Controls")
    with open(BENCHMARK_FILE) as f:
        cases = json.load(f)
    print(f"  Cases: {len(cases)}")
    
    # Load V1.11 full system results
    v1_11_file = RESULTS_DIR / "benchmark_results_v1_11.json"
    v1_11 = json.load(open(v1_11_file)) if v1_11_file.exists() else None
    if v1_11:
        full_strict = v1_11["score_distribution"].get("EXACT_MATCH",0) + v1_11["score_distribution"].get("MECHANISM_MATCH",0)
        full_total = v1_11["total_cases"]
        print(f"  V1.11 full system: {full_strict}/{full_total} ({100*full_strict/full_total:.0f}%)")
    
    # Experiment 1: False discoveries
    false_results = run_experiment1_false_discoveries(cases, n=15)
    false_scores = Counter(r["score"] for r in false_results)
    false_strict = false_scores.get("EXACT_MATCH",0) + false_scores.get("MECHANISM_MATCH",0)
    false_rate = false_strict / max(len(false_results), 1)
    
    # Experiment 2: LLM-only
    llm_results = run_experiment2_llm_only(cases, n=15)
    llm_scores = Counter(r["score"] for r in llm_results)
    llm_strict = llm_scores.get("EXACT_MATCH",0) + llm_scores.get("MECHANISM_MATCH",0)
    llm_rate = llm_strict / max(len(llm_results), 1)
    
    # Comparison
    print(f"\n=== V1.12 CONTROL COMPARISON ===")
    if v1_11:
        full_rate = full_strict / full_total
        print(f"  Full system (V1.11): {full_strict}/{full_total} ({100*full_rate:.0f}%)")
    print(f"  LLM-only:             {llm_strict}/{len(llm_results)} ({100*llm_rate:.0f}%)")
    print(f"  False discovery:      {false_strict}/{len(false_results)} ({100*false_rate:.0f}%)")
    
    print(f"\n=== INTERPRETATION ===")
    if v1_11:
        if llm_rate >= full_rate * 0.9:
            print(f"  ⚠️ LLM-only ({100*llm_rate:.0f}%) ≈ full system ({100*full_rate:.0f}%)")
            print(f"  → Architecture may NOT add value. 96% likely explained by LLM leakage.")
            arch_adds = False
        else:
            print(f"  ✅ Full system ({100*full_rate:.0f}%) > LLM-only ({100*llm_rate:.0f}%)")
            print(f"  → Architecture DOES add value")
            arch_adds = True
    else:
        arch_adds = "UNKNOWN"
    
    if false_rate > 0.3:
        print(f"  ⚠️ False discovery recovery ({100*false_rate:.0f}%) high → plausible narratives not discoveries")
        false_control = "WEAK"
    else:
        print(f"  ✅ False discovery recovery ({100*false_rate:.0f}%) low → engine doesn't fabricate matches")
        false_control = "STRONG"
    
    # Save
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "full_system_recovery": v1_11["strict_recovery"] if v1_11 else "N/A",
        "llm_only_recovery": f"{llm_strict}/{len(llm_results)} ({100*llm_rate:.0f}%)",
        "false_discovery_recovery": f"{false_strict}/{len(false_results)} ({100*false_rate:.0f}%)",
        "architecture_adds_value": arch_adds,
        "false_discovery_control": false_control,
        "leakage_risk": "HIGH" if llm_rate >= 0.8 else "MODERATE" if llm_rate >= 0.5 else "LOW",
        "false_discovery_results": false_results,
        "llm_only_results": llm_results,
    }
    
    with open(OUTPUT_DIR / "v1_12_control_report.json", 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT_DIR / 'v1_12_control_report.json'}")

if __name__ == "__main__":
    main()
