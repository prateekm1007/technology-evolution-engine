"""
Discovery-Structure Benchmark V1 — Runner

Key difference from mechanism-reconstruction benchmark:
1. Generator receives ONLY relation_blind_evidence (no components, no pattern, no name)
2. Scorer uses DISCOVERY_STRUCTURE_MATCH (judges relationship, not component repetition)
3. Evidence manifests with hashes for every case
4. Matched fabricated counterfactuals

Resumable via checkpoint. Run repeatedly until complete.
"""
import json, sys, re, time, os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")
from discovery_fabric.connectors.openrouter_llm import chat_text

BENCHMARK = REPO / "discovery_fabric/benchmarks/discovery_structure_v1/dataset.json"
CHECKPOINT = REPO / "discovery_fabric/evaluation/v1_12_controls/dsb_checkpoint.json"
OUTPUT = REPO / "discovery_fabric/evaluation/v1_12_controls/dsb_results.json"
MANIFEST_DIR = REPO / "discovery_fabric/benchmarks/discovery_structure_v1/manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

MAX_CALLS_PER_RUN = 6
MAX_RETRIES = 3
NUM_CASES = 10  # 10 real + 10 false = 20 cases × 5 configs = 100 payloads

GEN_SYS = 'Output JSON: {"proposed_mechanism":"","proposed_relationship":"","confidence":0.0}'

SCORE_SYS = """You are a DISCOVERY STRUCTURE scorer. You receive a PROPOSAL and a TARGET. You do NOT know if the target is real or fabricated.

Your job: Determine if the proposal captures the RELATIONSHIP or INSIGHT that makes the target a discovery — NOT just whether it mentions the same components.

Two scoring dimensions:

1. MECHANISM_MATCH: Does the proposal mention the same mechanisms/components? (easier)
2. DISCOVERY_STRUCTURE_MATCH: Does the proposal identify the SAME RELATIONSHIP, COMBINATION, CONSTRAINT RELEASE, or INSIGHT that makes the target a discovery?

DISCOVERY_STRUCTURE_MATCH criteria:
- For combination discoveries: Does the proposal identify the COMBINATION of components, not just the components themselves?
- For constraint inversion: Does the proposal identify the INVERSION of approach, not just the problem?
- For contradiction resolution: Does the proposal identify how to RESOLVE the contradiction, not just that it exists?
- For mechanism transfer: Does the proposal identify the TRANSFER application, not just the source mechanism?

Score: YES (captures the discovery relationship) / PARTIAL (captures components but misses relationship) / NO (misses both)

Output ONLY JSON: {"mechanism_match":"YES/PARTIAL/NO","discovery_structure_match":"YES/PARTIAL/NO","quality":0.0,"reasoning":""}"""

CONFIGS = {
    'B_llm_only': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nWhat novel mechanism or relationship would you propose that is NOT already explicitly stated in the evidence?',
    'C_mechanism': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nIdentify the core mechanism that could be transferred or combined. What specific NEW relationship or combination would you propose that is not already stated?',
    'D_mech_constraints': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nIdentify: 1) What constraints limit progress, 2) What relationship or combination could overcome them. Propose a mechanism that is NOT already stated in the evidence.',
    'E_combination': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nIdentify two independently validated mechanisms that could COMBINE to create an emergent capability NOT described in the evidence. What combination would you propose?',
    'F_full': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nAnalyze: What invariant principles exist? What constraints block progress? What two mechanisms could combine to create something new? What constraint could be released? Propose a mechanism with prediction and falsification that is NOT already stated in the evidence.',
}

FALSE_GEN_SYS = 'Create a plausible but NEVER-made discovery relationship. It must sound like a real breakthrough but must not be an actual discovery. Output JSON: {"name":"","withheld_relationship":"","relation_blind_evidence":"","actual":""}'


def call_with_retry(prompt, sys_prompt=GEN_SYS, mt=400):
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
    for attempt in range(MAX_RETRIES):
        t = chat_text(f'PROPOSAL: {proposed[:250]}\nTARGET: {target[:250]}\n\nScore both dimensions.', system=SCORE_SYS, max_tokens=200)
        if t:
            m = re.search(r'\{[^}]+\}', t)
            if m:
                try:
                    return json.loads(m.group()), True
                except:
                    pass
        time.sleep(2)
    return {'mechanism_match': 'NO', 'discovery_structure_match': 'NO', 'quality': 0.0}, False


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'false_cases': [],
        'results': {c: {} for c in CONFIGS},
        'calls_this_run': 0,
    }


def save_checkpoint(cp):
    cp['calls_this_run'] = 0
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


def create_manifest(case, config, generator_input, withheld):
    """Create machine-verifiable evidence manifest for a case."""
    manifest = {
        'case_id': case['id'],
        'config': config,
        'cutoff_date': case['cutoff_date'],
        'generator_input_hash': hashlib.sha256(generator_input.encode()).hexdigest(),
        'withheld_answer_hash': hashlib.sha256(withheld.encode()).hexdigest(),
        'exposed_fields': ['relation_blind_evidence'],
        'withheld_fields': ['name', 'actual_discovery', 'withheld_relationship', 'withheld_components', 'pattern'],
        'generator_input_length': len(generator_input),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    return manifest


def main():
    cp = load_checkpoint()
    
    with open(BENCHMARK) as f:
        cases = json.load(f)
    
    real_cases = cases[:NUM_CASES]
    
    # Generate false cases if needed
    if len(cp['false_cases']) < NUM_CASES:
        print("Generating fabricated counterfactual discoveries...")
        for i in range(len(cp['false_cases']), NUM_CASES):
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                print(f"  Checkpoint: {len(cp['false_cases'])}/{NUM_CASES} false cases. Run again.")
                return
            real_case = cases[i % len(cases)]
            prompt = f'Domain: {real_case["domain"]}, Pattern: {real_case["pattern"]}\nCreate a plausible but NEVER-made discovery. It must sound like a real breakthrough but must NOT be an actual discovery. Match this evidence density and terminology level:\n{real_case["relation_blind_evidence"][:100]}\n\nOutput JSON: {{"name":"","relation_blind_evidence":"","withheld_relationship":"","actual_discovery":""}}'
            r, ok = call_with_retry(prompt, sys_prompt='Output ONLY JSON.', mt=300)
            cp['calls_this_run'] += 1
            if ok and r:
                r['id'] = f'FD-{i+1:03d}'
                r['cutoff_date'] = real_case['cutoff_date']
                r['domain'] = real_case['domain']
                r['pattern'] = real_case['pattern']
                r['is_false'] = True
                cp['false_cases'].append(r)
                print(f"  [{i+1}/{NUM_CASES}] {r.get('name','?')[:50]}")
            save_checkpoint(cp)
    
    false_cases = cp['false_cases']
    all_cases = [('real', c) for c in real_cases] + [('false', c) for c in false_cases]
    
    # Process each case × config
    for case_type, case in all_cases:
        case_id = case['id']
        evidence = case.get('relation_blind_evidence', case.get('known_before', ''))
        withheld = case.get('withheld_relationship', case.get('actual_discovery', case.get('actual', '')))
        target = case.get('actual_discovery', case.get('actual', ''))
        
        for config_name, prompt_fn in CONFIGS.items():
            key = f"{case_id}|{config_name}"
            if key in cp['results'].get(config_name, {}):
                continue
            if case_id in cp['results'].get(config_name, {}):
                continue
            
            if cp['calls_this_run'] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                total = sum(len(cp['results'][c]) for c in CONFIGS)
                print(f"  Checkpoint: {total}/{len(all_cases)*len(CONFIGS)} cases. Run again.")
                return
            
            print(f"  [{config_name}] {case_type} {case_id}...", end=" ", flush=True)
            
            # Build generator input (ONLY evidence, nothing else)
            generator_input = prompt_fn(evidence)
            
            # Generate proposal
            proposal, gen_ok = call_with_retry(generator_input)
            cp['calls_this_run'] += 1
            
            if not gen_ok:
                print("GEN FAILED")
                if config_name not in cp['results']:
                    cp['results'][config_name] = {}
                cp['results'][config_name][case_id] = {
                    'case_id': case_id, 'case_type': case_type, 'config': config_name,
                    'gen_success': False, 'score_success': False,
                    'mechanism_match': None, 'discovery_structure_match': None, 'quality': None,
                }
                save_checkpoint(cp)
                continue
            
            proposed = proposal.get('proposed_mechanism', '') + ' ' + proposal.get('proposed_relationship', '')
            
            # Score with DISCOVERY_STRUCTURE_MATCH
            score_result, score_ok = score_with_retry(proposed, target)
            cp['calls_this_run'] += 1
            
            # Create manifest
            manifest = create_manifest(case, config_name, generator_input, withheld)
            
            if config_name not in cp['results']:
                cp['results'][config_name] = {}
            
            cp['results'][config_name][case_id] = {
                'case_id': case_id,
                'case_type': case_type,
                'config': config_name,
                'gen_success': True,
                'score_success': score_ok,
                'proposed': proposed[:250],
                'target': target[:250],
                'mechanism_match': score_result.get('mechanism_match', 'NO') if score_ok else None,
                'discovery_structure_match': score_result.get('discovery_structure_match', 'NO') if score_ok else None,
                'quality': score_result.get('quality', 0.0) if score_ok else None,
                'manifest': manifest,
            }
            
            dsm = score_result.get('discovery_structure_match', '?') if score_ok else 'FAILED'
            mm = score_result.get('mechanism_match', '?') if score_ok else 'FAILED'
            print(f"DSM={dsm} MM={mm}")
            save_checkpoint(cp)
            time.sleep(0.5)
    
    # ALL COMPLETE
    save_checkpoint(cp)
    
    print("\n=== DISCOVERY STRUCTURE BENCHMARK V1 COMPLETE ===\n")
    
    # Compute results
    final = {}
    for config in CONFIGS:
        all_results = list(cp['results'][config].values())
        real = [r for r in all_results if r.get('case_type') == 'real']
        false = [r for r in all_results if r.get('case_type') == 'false']
        
        real_scored = [r for r in real if r.get('score_success')]
        false_scored = [r for r in false if r.get('score_success')]
        
        # ITT: failures = NO
        real_itt_dsm = sum(1 for r in real if r.get('discovery_structure_match') == 'YES')
        false_itt_dsm = sum(1 for r in false if r.get('discovery_structure_match') == 'YES')
        real_itt_mm = sum(1 for r in real if r.get('mechanism_match') == 'YES')
        
        # PP: scored only
        real_pp_dsm = sum(1 for r in real_scored if r.get('discovery_structure_match') == 'YES')
        false_pp_dsm = sum(1 for r in false_scored if r.get('discovery_structure_match') == 'YES')
        
        final[config] = {
            'real_total': len(real),
            'real_scored': len(real_scored),
            'real_gen_failures': sum(1 for r in real if not r.get('gen_success')),
            'real_score_failures': sum(1 for r in real if r.get('gen_success') and not r.get('score_success')),
            'false_total': len(false),
            'false_scored': len(false_scored),
            'real_itt_dsm': real_itt_dsm,
            'real_itt_dsm_rate': f'{100*real_itt_dsm/max(len(real),1):.0f}%',
            'real_pp_dsm': real_pp_dsm,
            'real_pp_dsm_rate': f'{100*real_pp_dsm/max(len(real_scored),1):.0f}%',
            'real_itt_mm': real_itt_mm,
            'real_itt_mm_rate': f'{100*real_itt_mm/max(len(real),1):.0f}%',
            'false_itt_dsm': false_itt_dsm,
            'false_itt_dsm_rate': f'{100*false_itt_dsm/max(len(false),1):.0f}%',
            'false_pp_dsm': false_pp_dsm,
            'fpr_dsm': f'{100*false_itt_dsm/max(len(false),1):.0f}%',
        }
        
        print(f"  {config}:")
        print(f"    Real DSM ITT: {real_itt_dsm}/{len(real)} ({100*real_itt_dsm/max(len(real),1):.0f}%)")
        print(f"    Real DSM PP:  {real_pp_dsm}/{len(real_scored)} ({100*real_pp_dsm/max(len(real_scored),1):.0f}%)")
        print(f"    Real MM ITT:  {real_itt_mm}/{len(real)} ({100*real_itt_mm/max(len(real),1):.0f}%)")
        print(f"    False DSM FPR: {false_itt_dsm}/{len(false)} ({100*false_itt_dsm/max(len(false),1):.0f}%)")
        print(f"    Gen failures: {final[config]['real_gen_failures']}, Score failures: {final[config]['real_score_failures']}")
        print()
    
    # Compare
    llm_dsm = final['B_llm_only']['real_itt_dsm_rate']
    full_dsm = final['F_full']['real_itt_dsm_rate']
    llm_fpr = final['B_llm_only']['fpr_dsm']
    full_fpr = final['F_full']['fpr_dsm']
    
    print(f"  ARCHITECTURE COMPARISON (ITT, DISCOVERY_STRUCTURE_MATCH):")
    print(f"    LLM-only: real={llm_dsm}, FPR={llm_fpr}")
    print(f"    Full:     real={full_dsm}, FPR={full_fpr}")
    
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'benchmark': 'DISCOVERY_STRUCTURE_V1',
        'scorer': 'V3_BLINDED + DISCOVERY_STRUCTURE_MATCH',
        'total_cases': len(all_cases),
        'configs': final,
        'raw_results': {c: list(cp['results'][c].values()) for c in CONFIGS},
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
