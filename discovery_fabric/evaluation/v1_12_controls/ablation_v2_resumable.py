#!/usr/bin/env python3
"""
V1.12 Ablation V2 — properly separates API failures from scientific failures.

Key fixes from V1:
- Retry on failure (3 attempts per LLM call)
- Only score completed (non-failed) cases
- Same 30 cases per config, identical inputs
- Report generation_success_rate separately from discovery_recovery_rate
- Checkpoint after every single case
- Resume from checkpoint on re-run

Usage: run repeatedly until "ALL COMPLETE" appears.
"""
import json, sys, re, time, os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")
from discovery_fabric.connectors.openrouter_llm import chat_text

BENCHMARK = REPO / "discovery_fabric/benchmarks/historical_benchmark_v2/dataset.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/ablation_v2_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/ablation_v2_results.json"

MAX_CALLS_PER_RUN = 6  # 6 LLM calls per invocation (3 generation retries + 3 scoring retries worst case)
MAX_RETRIES = 3
NUM_CASES = 30  # 30 real cases per config

SCORE_SYS = 'You are a STRICT mechanism similarity scorer. Score: MECHANISM_MATCH/COMPONENT_MATCH/NO_MATCH. Output JSON: {"score":"","quality":0.0}'
GEN_SYS = 'Output JSON: {"proposed_mechanism":"","confidence":0.0}'

CONFIGS = {
    'B_llm_only': lambda c: f'PRE-DISCOVERY (cutoff: {c["cutoff"]}):\n{c["known_before"]}\n\nWhat novel mechanism would you propose?',
    'C_mechanism': lambda c: f'PRE-DISCOVERY:\nKnown mechanism: {c["known_before"]}\n\nIdentify the core mechanism that could be transferred or combined. What specific mechanism would you propose?',
    'D_mech_constraints': lambda c: f'PRE-DISCOVERY:\nKnown: {c["known_before"]}\n\nIdentify: 1) Core mechanism, 2) Constraints, 3) What overcomes them. Propose mechanism.',
    'E_combination': lambda c: f'PRE-DISCOVERY:\nKnown: {c["known_before"]}\n\nIdentify two independently validated mechanisms that could COMBINE to create emergent capability. What combination would you propose?',
    'F_full': lambda c: f'PRE-DISCOVERY (cutoff: {c["cutoff"]}):\n{c["known_before"]}\n\nAnalyze invariant principles, constraints, mechanism combination, constraint release. Propose with prediction and falsification.',
}


def call_with_retry(prompt, sys_prompt=GEN_SYS, mt=400):
    """Call LLM with retry. Returns (result, success)."""
    for attempt in range(MAX_RETRIES):
        t = chat_text(prompt, system=sys_prompt, max_tokens=mt)
        if t:
            m = re.search(r'\{[\s\S]*\}', t)
            if m:
                try:
                    return json.loads(m.group()), True
                except:
                    pass
            return {'proposed_mechanism': t[:200]}, True
        time.sleep(2)
    return None, False


def score_with_retry(proposed, target):
    """Score with retry. Returns (result, success)."""
    for attempt in range(MAX_RETRIES):
        t = chat_text(f'PROPOSAL: {proposed[:200]}\nTARGET: {target[:200]}\nScore.', system=SCORE_SYS, max_tokens=150)
        if t:
            m = re.search(r'\{[^}]+\}', t)
            if m:
                try:
                    return json.loads(m.group()), True
                except:
                    pass
        time.sleep(2)
    return {'score': 'NO_MATCH', 'quality': 0.0}, False


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'results': {c: {} for c in CONFIGS},  # {config: {case_id: result}}
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
    
    test_cases = cases[:NUM_CASES]
    
    for config_name, prompt_fn in CONFIGS.items():
        for i, case in enumerate(test_cases):
            case_id = case['id']
            
            # Skip if already completed
            if case_id in cp['results'][config_name]:
                continue
            
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                total_done = sum(len(cp['results'][c]) for c in CONFIGS)
                print(f"  Checkpoint: {total_done}/{len(CONFIGS)*NUM_CASES} cases. Run again.")
                return
            
            print(f"  [{config_name}] {i+1}/{NUM_CASES}: {case['name'][:35]}...", end=" ", flush=True)
            
            # Generate proposal with retry
            proposal, gen_success = call_with_retry(prompt_fn(case))
            cp['calls_this_run'] += 1
            
            if not gen_success:
                print("GEN FAILED (after retries)")
                cp['results'][config_name][case_id] = {
                    'name': case['name'],
                    'gen_success': False,
                    'score': None,  # Not scored — API failure
                    'quality': None,
                }
                save_checkpoint(cp)
                continue
            
            proposed = proposal.get('proposed_mechanism', '')
            
            # Score with retry
            score_result, score_success = score_with_retry(proposed, case['actual'])
            cp['calls_this_run'] += 1
            
            if not score_success:
                print("SCORE FAILED (after retries)")
                cp['results'][config_name][case_id] = {
                    'name': case['name'],
                    'gen_success': True,
                    'proposed': proposed[:200],
                    'actual': case['actual'][:200],
                    'score': None,  # Generation succeeded but scoring failed
                    'quality': None,
                }
                save_checkpoint(cp)
                continue
            
            cp['results'][config_name][case_id] = {
                'name': case['name'],
                'domain': case['domain'],
                'pattern': case['pattern'],
                'gen_success': True,
                'score_success': True,
                'proposed': proposed[:200],
                'actual': case['actual'][:200],
                'score': score_result.get('score', 'NO_MATCH'),
                'quality': score_result.get('quality', 0.0),
            }
            
            print(f"{score_result.get('score','?')} (q={score_result.get('quality',0)})")
            save_checkpoint(cp)
            time.sleep(0.5)
    
    # ALL COMPLETE — compute results
    save_checkpoint(cp)
    
    print("\n=== ABLATION V2 COMPLETE ===\n")
    
    final = {}
    for config in CONFIGS:
        all_results = list(cp['results'][config].values())
        gen_succeeded = [r for r in all_results if r.get('gen_success')]
        fully_completed = [r for r in all_results if r.get('score_success')]
        
        gen_rate = len(gen_succeeded) / len(all_results) if all_results else 0
        completed_scores = Counter(r['score'] for r in fully_completed if r.get('score'))
        strict = completed_scores.get('MECHANISM_MATCH', 0)
        any_match = strict + completed_scores.get('COMPONENT_MATCH', 0)
        
        final[config] = {
            'total_cases': len(all_results),
            'gen_success_count': len(gen_succeeded),
            'gen_success_rate': f'{100*gen_rate:.0f}%',
            'scored_count': len(fully_completed),
            'mechanism_match': strict,
            'component_match': completed_scores.get('COMPONENT_MATCH', 0),
            'no_match': completed_scores.get('NO_MATCH', 0),
            'recovery_rate_strict': f'{100*strict/max(len(fully_completed),1):.0f}%',
            'recovery_rate_any': f'{100*any_match/max(len(fully_completed),1):.0f}%',
            'avg_quality': round(sum(r.get('quality',0) for r in fully_completed) / max(len(fully_completed),1), 2),
        }
        
        print(f"  {config}:")
        print(f"    Gen success: {len(gen_succeeded)}/{len(all_results)} ({100*gen_rate:.0f}%)")
        print(f"    Scored: {len(fully_completed)}")
        print(f"    MECHANISM_MATCH: {strict} ({100*strict/max(len(fully_completed),1):.0f}%)")
        print(f"    COMPONENT_MATCH: {completed_scores.get('COMPONENT_MATCH',0)}")
        print(f"    NO_MATCH: {completed_scores.get('NO_MATCH',0)}")
        print(f"    Avg quality: {final[config]['avg_quality']}")
        print()
    
    # Compare LLM-only vs full system
    llm = final['B_llm_only']
    full = final['F_full']
    
    llm_strict_rate = llm['mechanism_match'] / max(llm['scored_count'], 1)
    full_strict_rate = full['mechanism_match'] / max(full['scored_count'], 1)
    advantage = full_strict_rate - llm_strict_rate
    
    print(f"  ARCHITECTURE ADVANTAGE: {100*advantage:+.0f}pp")
    print(f"    LLM-only: {100*llm_strict_rate:.0f}% ({llm['mechanism_match']}/{llm['scored_count']})")
    print(f"    Full: {100*full_strict_rate:.0f}% ({full['mechanism_match']}/{full['scored_count']})")
    
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'scorer': 'V3_BLINDED',
        'cases_per_config': NUM_CASES,
        'configs': final,
        'architecture_advantage_pp': round(100*advantage, 1),
        'llm_only_recovery': f"{100*llm_strict_rate:.0f}%",
        'full_system_recovery': f"{100*full_strict_rate:.0f}%",
        'raw_results': {c: list(cp['results'][c].values()) for c in CONFIGS},
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
