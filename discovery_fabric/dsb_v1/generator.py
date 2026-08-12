"""
DSB V1 — Generator
===================

Runs the 4 arms (LLM_only, mechanism_only, combination, full_system) on all
20 cases (10 real + 10 fabricated) via OpenRouter.

Total: 20 cases × 4 arms = 80 generations.

Resumable via checkpoint. Each generation is hash-sealed and saved to
receipts/. The leakage audit MUST pass before any generation runs.

Backend: OpenRouter (meta-llama/llama-3.3-70b-instruct). Reads
OPENROUTER_API_KEY from env.

CRITICAL INVARIANTS:
  (G1) The leakage audit MUST pass for ALL 80 payloads before any generation.
  (G2) Each generation is hash-sealed immediately after generation.
  (G3) The generator never sees case_id, name_internal, breakthrough_relationship,
       withheld_facts, forbidden_terms, future_terminology, answer_mechanism,
       constraint_release, historical_source, or cutoff_date.
  (G4) The same model + temperature + max_tokens is used for all 4 arms.
  (G5) Failed generations are recorded as INDETERMINATE — no retries with
       different prompts.
"""
import json
import os
import re
import sys
import time
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.case_schema import load_case
from discovery_fabric.dsb_v1.payload_builder import build_payload, build_payload_text, verify_payload
from discovery_fabric.dsb_v1.leakage_audit import audit_all_payloads

DSB_DIR = REPO / "discovery_fabric/dsb_v1"
REAL_DIR = DSB_DIR / "cases/real"
FAB_DIR = DSB_DIR / "cases/fabricated"
RECEIPTS_DIR = DSB_DIR / "receipts"
CHECKPOINT_PATH = DSB_DIR / "logs/checkpoint.json"
LOG_FILE = DSB_DIR / "logs/generation_log.jsonl"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

ARMS = ["LLM_only", "mechanism_only", "combination", "full_system"]
MODEL = "meta-llama/llama-3.3-70b-instruct"
TEMPERATURE = 0.3
MAX_TOKENS = 600
MAX_CALLS_PER_RUN = 12  # resumable
MAX_RETRIES = 2
INTER_CALL_DELAY = 2.0  # seconds between calls (rate-limit friendly)


# =============================================================================
# OpenRouter backend
# =============================================================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(prompt: str, system: str = None) -> str | None:
    """Call OpenRouter and return the assistant's text response."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL, data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://discovery-fabric.local",
            "X-Title": "DSB V1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError):
        return None


def parse_generation(text: str) -> dict | None:
    """Parse the LLM response as JSON. Returns None on failure."""
    if not text:
        return None
    text = text.strip().strip("`").strip()
    if text.startswith("json"):
        text = text[4:].strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


def call_with_retry(prompt: str, system: str) -> tuple[dict | None, str | None]:
    """Call OpenRouter with retry. Returns (parsed_result, raw_text_or_error)."""
    for attempt in range(MAX_RETRIES):
        text = call_openrouter(prompt, system)
        if text:
            parsed = parse_generation(text)
            if parsed:
                return parsed, text
            # Got text but couldn't parse — return raw
            return None, text[:500]
        time.sleep(INTER_CALL_DELAY)
    return None, None


# =============================================================================
# Receipt creation
# =============================================================================

SYSTEM_PROMPT = (
    "You are a scientific analyst. You reason only from the facts provided. "
    "You do not use any prior knowledge of specific named discoveries, named "
    "scientists, or named products. You produce strictly JSON output."
)


def generate_receipt(case: dict, arm: str) -> dict:
    """Generate one prediction receipt for (case, arm)."""
    payload = build_payload(case, arm)
    # Verify payload hash
    if not verify_payload(payload):
        raise RuntimeError(f"payload hash verification failed for {payload['payload_id']}")

    prompt = build_payload_text(payload)

    parsed, raw_text = call_with_retry(prompt, SYSTEM_PROMPT)

    generation_success = parsed is not None
    generation_timestamp = datetime.now(timezone.utc).isoformat()

    receipt = {
        "schema_version": "1.0.0",
        "receipt_type": "DSB_V1_GENERATION",
        "receipt_id": f"RECEIPT-{case['case_id']}-{arm}",
        "case_id": case["case_id"],  # internal, used for bookkeeping
        "arm": arm,
        "payload_id": payload["payload_id"],
        "payload_hash": payload["payload_hash"],
        "model": MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "generation_timestamp": generation_timestamp,
        "generation_success": generation_success,
        "proposed_relationship": parsed.get("proposed_relationship", "") if parsed else "",
        "mechanism": parsed.get("mechanism", "") if parsed else "",
        "constraint_released": parsed.get("constraint_released", "") if parsed else "",
        "predicted_quantitative_outcome": parsed.get("predicted_quantitative_outcome", "") if parsed else "",
        "raw_response": raw_text,
    }

    # Seal the receipt
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt["receipt_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return receipt


def save_receipt(receipt: dict) -> Path:
    """Save a sealed receipt to receipts/."""
    path = RECEIPTS_DIR / f"{receipt['receipt_id']}.json"
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    return path


def verify_receipt(receipt: dict) -> bool:
    """Verify a receipt's hash."""
    stored = receipt.get("receipt_hash")
    if not stored:
        return False
    r = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    canonical = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    computed = hashlib.sha256(canonical.encode()).hexdigest()
    return computed == stored


# =============================================================================
# Checkpoint management
# =============================================================================

def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {"completed_keys": [], "calls_this_run": 0}


def save_checkpoint(cp: dict) -> None:
    cp["calls_this_run"] = 0
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


def append_log(entry: dict) -> None:
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# =============================================================================
# Main generation loop
# =============================================================================

def main():
    """Generate receipts for all (case, arm) pairs.

    The leakage audit MUST pass before any generation runs.
    """
    print("=" * 72)
    print("DSB V1 — GENERATOR")
    print("=" * 72)
    print()

    # ---- Step 1: Run leakage audit. MUST pass. ----
    print("Running leakage audit on all 80 payloads...")
    audit_result = audit_all_payloads()
    print(f"  Payloads: {audit_result['n_payloads']}")
    print(f"  PASS: {audit_result['n_pass']}")
    print(f"  FAIL: {audit_result['n_fail']}")
    if not audit_result["overall_pass"]:
        print("\nABORTING: leakage audit failed. Fix case definitions before generating.")
        return
    print("  Overall: PASS\n")

    # ---- Step 2: Load all cases ----
    cases = []
    for d in [REAL_DIR, FAB_DIR]:
        for case_path in sorted(d.glob("DSB-*.json")):
            cases.append(load_case(case_path))
    print(f"Loaded {len(cases)} cases ({len(list(REAL_DIR.glob('*.json')))} real + {len(list(FAB_DIR.glob('*.json')))} fabricated)")

    # ---- Step 3: Generate receipts (resumable) ----
    cp = load_checkpoint()
    completed = set(cp["completed_keys"])

    n_generated = 0
    for case in cases:
        for arm in ARMS:
            key = f"{case['case_id']}|{arm}"
            if key in completed:
                continue
            if cp["calls_this_run"] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                print(f"\n  Checkpoint: {len(cp['completed_keys'])}/80. Run again to continue.")
                return

            print(f"  [{arm}] {case['case_id']}...", end=" ", flush=True)
            try:
                receipt = generate_receipt(case, arm)
            except Exception as e:
                print(f"ERROR: {e}")
                continue
            cp["calls_this_run"] += 1

            save_receipt(receipt)
            append_log({
                "timestamp": receipt["generation_timestamp"],
                "receipt_id": receipt["receipt_id"],
                "case_id": case["case_id"],
                "arm": arm,
                "success": receipt["generation_success"],
                "receipt_hash": receipt["receipt_hash"],
            })
            cp["completed_keys"].append(key)
            save_checkpoint(cp)

            status = "OK" if receipt["generation_success"] else "PARSE_FAIL"
            print(f"{status}")
            n_generated += 1
            time.sleep(INTER_CALL_DELAY)

    save_checkpoint(cp)
    print(f"\nGeneration complete. {n_generated} new receipts generated.")
    print(f"Total receipts: {len(cp['completed_keys'])}/80")
    print(f"Receipts dir: {RECEIPTS_DIR}")


if __name__ == "__main__":
    main()
