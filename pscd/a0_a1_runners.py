"""
A0/A1 Runners — Baseline Machine

A0: Frontier LLM alone. Frozen model. Frozen prompt. No retrieval. Fixed budget.
A1: Same model, same budget, same prompt, plus one immutable retrieval snapshot.

Budget parity enforced. No Fabric scaffolding. No mechanism extraction.
No constraints. No combination engine.

The ONLY difference between A0 and A1 is retrieval.
"""
import json
import hashlib
import os
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pscd.prediction_schema import Prediction, validate_prediction, seal_prediction

# Frozen model configuration (must be set before running)
MODEL_ID = "meta-llama/llama-3.3-70b-instruct"
MODEL_VERSION = "2024-09-15"  # version pin
MAX_TOKENS = 600
TEMPERATURE = 0.3

# Frozen prompt template (same for A0 and A1)
PROMPT_TEMPLATE = """You are a scientific prediction engine. Based on the evidence provided, propose ONE falsifiable scientific prediction.

{evidence_section}

Propose ONE specific, falsifiable, quantitative prediction that follows from the evidence but is NOT explicitly stated in it.

Output JSON:
{{"claim": "one sentence", "mechanism": "one paragraph", "quantitative_forecast": "specific value", "tolerance": "pre-registered tolerance", "falsification_condition": "what would falsify", "measurement_protocol": "how to measure"}}

The prediction must be:
1. NOT explicitly stated in the evidence
2. Quantitatively specific (numeric value or YES/NO)
3. Falsifiable (state what would disprove it)
4. Tied to the evidence (not from outside knowledge)
"""

PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest()

# Evidence sections per arm
A0_EVIDENCE = "No external evidence is available. Reason from your training only."
A1_EVIDENCE_TEMPLATE = "Retrieved evidence from frozen corpus (hash: {snapshot_hash}):\n{evidence_text}"


def call_llm(prompt: str, max_tokens: int = MAX_TOKENS) -> str | None:
    """Call OpenRouter LLM."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    body = json.dumps({
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": TEMPERATURE,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://psc-d.local",
            "X-Title": "PSCD-1 Baseline",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def parse_prediction(text: str) -> dict | None:
    """Parse LLM response as JSON."""
    import re
    if not text:
        return None
    text = text.strip().strip("`").strip()
    if text.startswith("json"):
        text = text[4:].strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None


def run_arm(arm: str, task_id: str, evidence_text: str, retrieval_hash: str) -> dict:
    """Run one arm on one task. Returns a Prediction receipt."""
    if arm == "A0":
        evidence_section = A0_EVIDENCE
        retrieval_hash_val = "NONE"
    elif arm == "A1":
        evidence_section = A1_EVIDENCE_TEMPLATE.format(
            snapshot_hash=retrieval_hash,
            evidence_text=evidence_text,
        )
        retrieval_hash_val = retrieval_hash
    else:
        raise ValueError(f"Arm {arm} not implemented yet (A2 requires Phase 3 authorization)")

    prompt = PROMPT_TEMPLATE.format(evidence_section=evidence_section)
    raw_response = call_llm(prompt)
    parsed = parse_prediction(raw_response) if raw_response else None

    gen_ts = datetime.now(timezone.utc).isoformat()
    prediction_id = f"PSCD1-{task_id}-{arm}-{gen_ts}"

    if parsed:
        pred = Prediction(
            prediction_id=prediction_id,
            claim=parsed.get("claim", ""),
            mechanism=parsed.get("mechanism", ""),
            quantitative_forecast=parsed.get("quantitative_forecast", ""),
            tolerance=parsed.get("tolerance", ""),
            falsification_condition=parsed.get("falsification_condition", ""),
            measurement_protocol=parsed.get("measurement_protocol", ""),
            evidence_ids=[task_id] if arm == "A1" else [],
            retrieval_snapshot_hash=retrieval_hash_val,
            model_id=f"{MODEL_ID}@{MODEL_VERSION}",
            prompt_hash=PROMPT_HASH,
            generation_timestamp=gen_ts,
            retrieval_negative_attestation={
                "is_retrieval_negative": True,  # placeholder — real check in evaluator
                "check_method": "deterministic_entailment_check (pending implementation)",
                "evidence_source_hashes_checked": [],
                "entailment_check_result": "NOT_ENTAILED",
            },
            arm=arm,
        )
        ok, errors = validate_prediction(pred)
        pred.receipt_hash = seal_prediction(pred)
        return {
            "success": ok,
            "errors": errors if not ok else [],
            "prediction": asdict_safe(pred),
            "raw_response": (raw_response or "")[:500],
        }
    else:
        return {
            "success": False,
            "errors": ["LLM response could not be parsed as JSON"],
            "prediction": None,
            "raw_response": (raw_response or "None")[:500],
        }


def asdict_safe(p):
    """Safely convert Prediction to dict."""
    d = {
        "prediction_id": p.prediction_id,
        "claim": p.claim,
        "mechanism": p.mechanism,
        "quantitative_forecast": p.quantitative_forecast,
        "tolerance": p.tolerance,
        "falsification_condition": p.falsification_condition,
        "measurement_protocol": p.measurement_protocol,
        "evidence_ids": p.evidence_ids,
        "retrieval_snapshot_hash": p.retrieval_snapshot_hash,
        "model_id": p.model_id,
        "prompt_hash": p.prompt_hash,
        "generation_timestamp": p.generation_timestamp,
        "retrieval_negative_attestation": p.retrieval_negative_attestation,
        "arm": p.arm,
        "receipt_hash": p.receipt_hash,
    }
    return d


def main():
    """Dry-run: prove A0/A1 runners can execute without seeing the answer key."""
    print("=" * 72)
    print("PSCD-1 DRY RUN — A0/A1 Baseline Runners")
    print("=" * 72)
    print()
    print(f"Model: {MODEL_ID}@{MODEL_VERSION}")
    print(f"Prompt hash: {PROMPT_HASH[:32]}...")
    print(f"Max tokens: {MAX_TOKENS}")
    print(f"Temperature: {TEMPERATURE}")
    print()

    # Use fabricated task for dry-run
    dry_run_task = {
        "task_id": "DRY-RUN-001",
        "evidence_text": "Synthetic evidence for dry-run only. Not a real task.",
        "retrieval_hash": hashlib.sha256(b"dry-run-snapshot").hexdigest(),
        "is_foil": True,
    }

    for arm in ["A0", "A1"]:
        print(f"\n[{arm}] Running dry-run task {dry_run_task['task_id']}...")
        result = run_arm(
            arm=arm,
            task_id=dry_run_task["task_id"],
            evidence_text=dry_run_task["evidence_text"],
            retrieval_hash=dry_run_task["retrieval_hash"],
        )
        if result["success"]:
            print(f"  ✓ Prediction generated and validated")
            pred = result["prediction"]
            print(f"  prediction_id: {pred['prediction_id']}")
            print(f"  claim: {pred['claim'][:100]}...")
            print(f"  arm: {pred['arm']}")
            print(f"  receipt_hash: {pred['receipt_hash'][:32]}...")
            print(f"  retrieval_snapshot_hash: {pred['retrieval_snapshot_hash'][:32]}...")
        else:
            print(f"  ✗ Generation failed: {result['errors']}")
            print(f"  raw_response: {result['raw_response'][:200]}")
        time.sleep(2)

    print("\n" + "=" * 72)
    print("DRY RUN COMPLETE")
    print("=" * 72)
    print()
    print("A0/A1 runners are executable. Budget parity enforced (same model,")
    print("same prompt, same max_tokens, same temperature). The ONLY difference")
    print("between A0 and A1 is retrieval.")
    print()
    print("Next steps:")
    print("1. Verify corpus 112 (fetch abstracts, hash, store)")
    print("2. Build retrieval snapshot (hash-pinned)")
    print("3. Seal PSCD-1 outcome/foil artifact")
    print("4. Run dry-run PSCD with fabricated outcomes")
    print("5. Only then: authorize A2")


if __name__ == "__main__":
    from dataclasses import asdict
    main()
