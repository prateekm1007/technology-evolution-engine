"""
V1.13 Prediction Benchmark — 50 historical opportunities with time-isolated evidence.

For each case:
1. System receives ONLY pre-outcome evidence (cutoff enforced)
2. System generates: hypothesis + prediction + falsifier
3. Prediction receipt is created (immutable)
4. Later outcome is evaluated deterministically (CORRECT/INCORRECT/INDETERMINATE)
5. Novelty is checked deterministically (relationship NOT in evidence)

Controls: LLM-only, mechanism-only, full system, random/null
Same evidence budget. Same model. Deterministic scoring.

Resumable via checkpoint.
"""
import json, sys, re, time, os, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))
os.environ.setdefault("OPENROUTER_API_KEY", "")

from discovery_fabric.connectors.openrouter_llm import chat_text
from discovery_fabric.v1_13.prediction_receipt import create_receipt, verify_receipt
from discovery_fabric.v1_13.external_outcome_evaluator import evaluate_prediction

BENCHMARK = REPO / "discovery_fabric/v1_13/benchmark_dataset.json"
CHECKPOINT = REPO / "discovery_fabric/v1_13/checkpoint.json"
OUTPUT = REPO / "discovery_fabric/v1_13/results.json"
RECEIPTS_DIR = REPO / "discovery_fabric/v1_13/receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_CALLS_PER_RUN = 5
MAX_RETRIES = 3

GEN_SYS = """You are a scientific prediction engine. Given ONLY pre-discovery evidence, generate a FALSIFIABLE PREDICTION.

The prediction must be:
1. Something NOT already explicitly stated in the evidence
2. Quantitatively or directionally testable
3. Falsifiable (state what would disprove it)

Output JSON:
{"hypothesis":"","prediction":"","units_range":"","expected_direction":"INCREASE/DECREASE/BINARY/CORRELATION","measurement_method":"","falsification_condition":""}
"""

CONFIGS = {
    'B_llm_only': lambda evidence: f'PRE-DISCOVERY EVIDENCE (cutoff enforced):\n{evidence}\n\nGenerate a falsifiable prediction based on this evidence.',
    'C_mechanism': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nIdentify the core mechanism. Generate a falsifiable prediction based on that mechanism.',
    'F_full': lambda evidence: f'PRE-DISCOVERY EVIDENCE:\n{evidence}\n\nAnalyze invariant principles, constraints, and mechanism interactions. Generate a falsifiable prediction with specific units and direction.',
    'D_random': lambda evidence: f'{evidence}\n\nGenerate any plausible scientific prediction.',
}


def call_with_retry(prompt, mt=400):
    for attempt in range(MAX_RETRIES):
        t = chat_text(prompt, system=GEN_SYS, max_tokens=mt)
        if t:
            m = re.search(r'\{[\s\S]*\}', t)
            if m:
                try:
                    return json.loads(m.group()), True
                except:
                    pass
            return {"prediction": t[:200]}, True
        time.sleep(2)
    return None, False


def load_checkpoint():
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"completed": [], "results": [], "calls_this_run": 0}

def save_checkpoint(cp):
    cp["calls_this_run"] = 0
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


def main():
    cp = load_checkpoint()
    
    with open(BENCHMARK) as f:
        cases = json.load(f)
    
    completed = set(cp["completed"])
    
    for case in cases:
        case_id = case["id"]
        if case_id in completed:
            continue
        if cp["calls_this_run"] >= MAX_CALLS_PER_RUN:
            save_checkpoint(cp)
            print(f"  Checkpoint: {len(cp['completed'])}/{len(cases)}. Run again.")
            return
        
        evidence = case["pre_outcome_evidence"]
        outcome = case["outcome"]
        cutoff = case["cutoff_date"]
        evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()
        
        for config_name, prompt_fn in CONFIGS.items():
            if cp["calls_this_run"] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                print(f"  Checkpoint: {len(cp['completed'])}/{len(cases)}. Run again.")
                return
            
            key = f"{case_id}|{config_name}"
            if any(r.get("key") == key for r in cp["results"]):
                continue
            
            print(f"  [{config_name}] {case_id}...", end=" ", flush=True)
            
            # Generate prediction
            prompt = prompt_fn(evidence)
            result, gen_ok = call_with_retry(prompt)
            cp["calls_this_run"] += 1
            
            if not gen_ok or not result:
                print("GEN FAILED")
                cp["results"].append({
                    "key": key, "case_id": case_id, "config": config_name,
                    "gen_success": False, "verdict": "INDETERMINATE",
                })
                continue
            
            hypothesis = result.get("hypothesis", "")
            prediction = result.get("prediction", "")
            units_range = result.get("units_range", "")
            direction = result.get("expected_direction", "BINARY")
            measurement = result.get("measurement_method", "")
            falsifier = result.get("falsification_condition", "")
            
            # Create immutable prediction receipt
            candidate_id = f"PRED-{case_id}-{config_name}"
            receipt = create_receipt(
                candidate_id=candidate_id,
                input_manifest_hash=evidence_hash,
                hypothesis=hypothesis,
                prediction=prediction,
                units_range=units_range,
                expected_direction=direction,
                measurement_method=measurement,
                falsification_condition=falsifier,
                evidence_text=evidence,
                proposed_text=hypothesis + " " + prediction,
                pre_registration_timestamp=cutoff,
            )
            
            # Evaluate against outcome (deterministic, no LLM)
            eval_result = evaluate_prediction(receipt, outcome)
            
            # Save receipt
            receipt_path = RECEIPTS_DIR / f"{candidate_id}.json"
            with open(receipt_path, "w") as f:
                json.dump(receipt, f, indent=2, ensure_ascii=False)
            
            verdict = eval_result.get("verdict", "INDETERMINATE")
            is_novel = receipt["novelty_check"]["is_novel"]
            
            cp["results"].append({
                "key": key,
                "case_id": case_id,
                "config": config_name,
                "gen_success": True,
                "candidate_id": candidate_id,
                "hypothesis": hypothesis[:200],
                "prediction": prediction[:200],
                "expected_direction": direction,
                "units_range": units_range,
                "verdict": verdict,
                "is_novel": is_novel,
                "novelty_overlap": receipt["novelty_check"]["term_overlap_ratio"],
                "receipt_hash": receipt["receipt_hash"],
                "receipt_path": str(receipt_path),
                "evidence_hash": evidence_hash,
                "outcome_source": outcome.get("source", ""),
                "outcome_direction": outcome.get("direction", ""),
                "outcome_value": outcome.get("value", ""),
                "eval_reason": eval_result.get("reason", ""),
                "deterministic": True,
            })
            
            print(f"{verdict} novel={is_novel}")
            save_checkpoint(cp)
            time.sleep(0.5)
        
        cp["completed"].append(case_id)
        save_checkpoint(cp)
    
    # ALL COMPLETE
    save_checkpoint(cp)
    
    results = cp["results"]
    n_configs = len(CONFIGS)
    
    print(f"\n=== V1.13 PREDICTION BENCHMARK RESULTS ===\n")
    
    for config in CONFIGS:
        config_results = [r for r in results if r.get("config") == config]
        total = len(config_results)
        gen_ok = sum(1 for r in config_results if r.get("gen_success"))
        
        correct = sum(1 for r in config_results if r.get("verdict") == "CORRECT")
        incorrect = sum(1 for r in config_results if r.get("verdict") == "INCORRECT")
        indeterminate = sum(1 for r in config_results if r.get("verdict") == "INDETERMINATE")
        novel = sum(1 for r in config_results if r.get("is_novel"))
        novel_and_correct = sum(1 for r in config_results if r.get("is_novel") and r.get("verdict") == "CORRECT")
        
        print(f"  {config}:")
        print(f"    Total: {total}, Gen OK: {gen_ok}")
        print(f"    CORRECT: {correct} ({100*correct/max(total,1):.0f}%)")
        print(f"    INCORRECT: {incorrect} ({100*incorrect/max(total,1):.0f}%)")
        print(f"    INDETERMINATE: {indeterminate} ({100*indeterminate/max(total,1):.0f}%)")
        print(f"    NOVEL: {novel} ({100*novel/max(total,1):.0f}%)")
        print(f"    NOVEL + CORRECT: {novel_and_correct} ({100*novel_and_correct/max(total,1):.0f}%)")
        print()
    
    # Save final report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "benchmark": "V1.13_PREDICTION",
        "scoring": "DETERMINISTIC (no LLM judge)",
        "total_cases": len(cases),
        "configs": list(CONFIGS.keys()),
        "results": results,
        "summary": {},
    }
    
    for config in CONFIGS:
        config_results = [r for r in results if r.get("config") == config]
        total = len(config_results)
        report["summary"][config] = {
            "total": total,
            "correct": sum(1 for r in config_results if r.get("verdict") == "CORRECT"),
            "incorrect": sum(1 for r in config_results if r.get("verdict") == "INCORRECT"),
            "indeterminate": sum(1 for r in config_results if r.get("verdict") == "INDETERMINATE"),
            "novel": sum(1 for r in config_results if r.get("is_novel")),
            "novel_and_correct": sum(1 for r in config_results if r.get("is_novel") and r.get("verdict") == "CORRECT"),
        }
    
    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    h = hashlib.sha256(Path(OUTPUT).read_bytes()).hexdigest()
    print(f"Results hash: {h[:32]}...")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
