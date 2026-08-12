#!/usr/bin/env python3
"""
Resumable ablation runner — survives interruption via checkpointing.
Run repeatedly until complete. Each run processes a few items then exits.

Usage:
  python3 ablation_resumable.py
  (run again if interrupted — it resumes from checkpoint)

Configurations:
  B: LLM-only (raw prompt)
  D: Mechanism + constraints
  F: Full system

Each config × 10 real + 10 false = 60 generation calls + 60 scoring calls = 120 total.
"""
import json, sys, re, time, os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")
from discovery_fabric.connectors.openrouter_llm import chat_text

BENCHMARK = REPO / "discovery_fabric/benchmarks/historical_benchmark_v2/dataset.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/ablation_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/ablation_results.json"

MAX_CALLS_PER_RUN = 8  # process 8 LLM calls per invocation, then save and exit
SCORE_SYS = 'You are a STRICT mechanism similarity scorer. Score: MECHANISM_MATCH/COMPONENT_MATCH/NO_MATCH. Output JSON: {"score":"","quality":0.0}'
GEN_SYS = 'Output JSON: {"proposed_mechanism":"","confidence":0.0}'

CONFIGS = {
    'B_llm_only': lambda c: f'PRE-DISCOVERY (cutoff: {c["cutoff"]}):\n{c["known_before"]}\n\nWhat novel mechanism would you propose?',
    'D_mech_constraints': lambda c: f'PRE-DISCOVERY:\nKnown: {c["known_before"]}\n\nIdentify: 1) Core mechanism, 2) Constraints, 3) What overcomes them. Propose mechanism.',
    'F_full': lambda c: f'PRE-DISCOVERY (cutoff: {c["cutoff"]}):\n{c["known_before"]}\n\nAnalyze invariant principles, constraints, mechanism combination, constraint release. Propose with prediction and falsification.',
}

PROMPTS_FALSE = {
    'B_llm_only': lambda known: f'PRE-DISCOVERY:\n{known}\n\nWhat novel mechanism would you propose?',
    'D_mech_constraints': lambda known: f'PRE-DISCOVERY:\nKnown: {known}\n\nIdentify core mechanism, constraints, and what overcomes them. Propose.',
    'F_full': lambda known: f'PRE-DISCOVERY:\n{known}\n\nAnalyze invariants, constraints, combination, constraint release. Propose with prediction.',
}

FALSE_GEN_SYS = 'Create a plausible but NEVER-made discovery. Output JSON: {"name":"","actual":"","known_before":""}'

def call(prompt, sys_prompt=GEN_SYS, mt=400):
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

def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'false_discoveries': [],  # generated false discoveries (shared across configs)
        'results': {},  # {config: {real: [...], false: [...]}}
        'completed': [],  # list of "config|type|index" strings
        'calls_this_run': 0,
    }

def save_checkpoint(cp):
    cp['calls_this_run'] = 0
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)

def main():
    cp = load_checkpoint()
    
    with open(BENCHMARK) as f:
        cases = json.load(f)
    
    real_cases = cases[:10]
    
    # Generate false discoveries if not done
    if len(cp['false_discoveries']) < 10:
        print("Generating false discoveries...")
        for i in range(len(cp['false_discoveries']), 10):
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                print(f"  Checkpoint saved. {len(cp['false_discoveries'])}/10 false discoveries. Run again.")
                return
            case = cases[i % len(cases)]
            r = call(f'Domain: {case["domain"]}. Create a plausible but NEVER-made discovery. Output: {{"name":"","actual":"","known_before":"{case["known_before"]}"}}', sys_prompt='Output ONLY JSON.', mt=250)
            if r:
                cp['false_discoveries'].append(r)
                print(f"  [{i+1}/10] {r.get('name','?')[:50]}")
            cp['calls_this_run'] += 1
            time.sleep(1)
        save_checkpoint(cp)
    
    false_cases = cp['false_discoveries']
    
    # Initialize results structure
    for config in CONFIGS:
        if config not in cp['results']:
            cp['results'][config] = {'real': [None]*10, 'false': [None]*10}
    
    # Process items
    for config_name, prompt_fn in CONFIGS.items():
        # Real discoveries
        for i, case in enumerate(real_cases):
            key = f"{config_name}|real|{i}"
            if key in cp['completed']:
                continue
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                done = sum(1 for v in cp['results'].values() for x in v['real']+v['false'] if x is not None)
                print(f"  Checkpoint: {done}/60 items done. Run again.")
                return
            
            print(f"  [{config_name}] real {i+1}/10: {case['name'][:35]}...", end=" ", flush=True)
            p = call(prompt_fn(case))
            cp['calls_this_run'] += 1
            if not p:
                print("GEN FAILED")
                cp['results'][config_name]['real'][i] = {'name':case['name'],'score':'NO_MATCH','q':0}
                cp['completed'].append(key)
                continue
            proposed = p.get('proposed_mechanism','')
            s = score(proposed, case['actual'])
            cp['calls_this_run'] += 1
            cp['results'][config_name]['real'][i] = {'name':case['name'],'proposed':proposed[:150],'actual':case['actual'][:150],'score':s.get('score','NO_MATCH'),'q':s.get('quality',0)}
            cp['completed'].append(key)
            print(f"{s.get('score','?')} (q={s.get('quality',0)})")
            time.sleep(0.5)
        
        # False discoveries
        for i, fd in enumerate(false_cases):
            key = f"{config_name}|false|{i}"
            if key in cp['completed']:
                continue
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                done = sum(1 for v in cp['results'].values() for x in v['real']+v['false'] if x is not None)
                print(f"  Checkpoint: {done}/60 items done. Run again.")
                return
            
            known = fd.get('known_before','')
            actual = fd.get('actual','')
            print(f"  [{config_name}] false {i+1}/10: {fd.get('name','?')[:35]}...", end=" ", flush=True)
            p = call(PROMPTS_FALSE[config_name](known))
            cp['calls_this_run'] += 1
            if not p:
                print("GEN FAILED")
                cp['results'][config_name]['false'][i] = {'name':fd.get('name',''),'score':'NO_MATCH','q':0}
                cp['completed'].append(key)
                continue
            proposed = p.get('proposed_mechanism','')
            s = score(proposed, actual)
            cp['calls_this_run'] += 1
            cp['results'][config_name]['false'][i] = {'name':fd.get('name',''),'proposed':proposed[:150],'target':actual[:150],'score':s.get('score','NO_MATCH'),'q':s.get('quality',0)}
            cp['completed'].append(key)
            print(f"{s.get('score','?')} (q={s.get('quality',0)})")
            time.sleep(0.5)
    
    # All done — compute final results
    save_checkpoint(cp)
    
    print("\n=== ABLATION COMPLETE ===\n")
    final = {}
    for config in CONFIGS:
        real = cp['results'][config]['real']
        false = cp['results'][config]['false']
        real_scores = Counter(r['score'] for r in real if r)
        false_scores = Counter(r['score'] for r in false if r)
        real_strict = real_scores.get('MECHANISM_MATCH',0)
        false_strict = false_scores.get('MECHANISM_MATCH',0)
        final[config] = {
            'real_strict': real_strict, 'real_total': len(real),
            'real_rate': f'{100*real_strict/len(real):.0f}%',
            'false_strict': false_strict, 'false_total': len(false),
            'false_rate': f'{100*false_strict/len(false):.0f}%',
            'real_scores': dict(real_scores), 'false_scores': dict(false_scores),
            'real_details': real, 'false_details': false,
        }
        print(f"  {config}:")
        print(f"    Real: {real_strict}/{len(real)} ({100*real_strict/len(real):.0f}%)")
        print(f"    False: {false_strict}/{len(false)} ({100*false_strict/len(false):.0f}%)")
    
    llm_real = final['B_llm_only']['real_strict'] / final['B_llm_only']['real_total']
    full_real = final['F_full']['real_strict'] / final['F_full']['real_total']
    advantage = full_real - llm_real
    
    print(f"\n  Architecture advantage: {100*advantage:.0f}pp")
    print(f"  False positive rate (full): {final['F_full']['false_rate']}")
    
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'scorer': 'V3_BLINDED',
        'configs': final,
        'architecture_advantage_pp': round(100*advantage, 1),
        'false_positive_rate': final['F_full']['false_rate'],
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT}")

if __name__ == "__main__":
    main()
