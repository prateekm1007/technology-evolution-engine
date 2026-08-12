"""
V1.13 GATE 2 — Leakage-Controlled Prediction Generator
=======================================================

Re-generates the 40 prediction receipts (10 cases × 4 configs) under a
strict evidence-only protocol:

  1. EVIDENCE-ONLY PROMPT
     The system prompt EXPLICITLY forbids the use of any knowledge outside
     the supplied evidence text. The model is told: "You may ONLY reason
     from the evidence text below. Do NOT use any prior knowledge of
     chemistry, biology, physics, history, or any specific case study you
     may have been trained on."

  2. POINT-ESTIMATE REQUIREMENT (NO BROAD RANGES)
     The model must output a single POINT ESTIMATE (a specific numeric value
     or a YES/NO binary), plus a TIGHT pre-registered tolerance. Broad
     ranges like "1-1000" or ">50" are explicitly forbidden.

     Allowed formats:
        - "predicted_value": 500, "tolerance_lower": 0.5, "tolerance_upper": 2.0
          (interpreted as: 500, falsified if observed < 250 or > 1000)
        - "predicted_value": "YES", "tolerance_lower": null, "tolerance_upper": null
          (binary: falsified if observed is NO)

     The tolerance bounds are MULTIPLICATIVE (ratio) bounds, not absolute.
     tolerance_lower=0.5 means "as low as half the predicted value is still OK".
     tolerance_upper=2.0 means "as high as double the predicted value is still OK".

     Hard constraint: tolerance_lower >= 0.25 AND tolerance_upper <= 4.0.
     Ranges outside these bounds are rejected as "range fitting".

  3. NO RETRIEVAL / NO AUXILIARY KNOWLEDGE
     The prompt contains ONLY the pre-outcome evidence text. No web search,
     no auxiliary corpus lookup. The model's parametric memory is the only
     leakage vector — and we document this limitation honestly.

  4. IDENTICAL BUDGETS / IDENTICAL CUTOFFS
     All 4 configs (B_llm_only, C_mechanism, F_full, D_random) use the same
     evidence, same cutoff date, same model, same max_tokens, same temperature.

LIMITATION (documented honestly):
     We cannot actually prevent the LLM from using its parametric memory.
     The model's training data post-dates every cutoff date in the benchmark.
     The evidence-only prompt is a SOFT constraint, not a hard one. This is
     documented in the report. A truly frozen setup would require either:
       (a) a model with a training cutoff earlier than every case's cutoff
           date (not available in this environment), or
       (b) a retrieval-only architecture with no parametric memory (not
           available in this environment).

     The Gate 2 evaluator measures the EMPIRICAL effect of the evidence-only
     prompt + point-estimate requirement, with the parametric-memory caveat
     documented in the report.

Backend: z-ai CLI (glm-4-plus). This is the only LLM backend available in
this environment. The OpenRouter API key is not set.
"""
from __future__ import annotations

import json
import re
import os
import sys
import time
import math
import hashlib
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from discovery_fabric.v1_13.prediction_receipt import create_receipt  # noqa: E402

BENCHMARK = REPO / "discovery_fabric/v1_13/benchmark_dataset.json"
CHECKPOINT = REPO / "discovery_fabric/v1_13_gate2/checkpoint.json"
OUTPUT = REPO / "discovery_fabric/v1_13_gate2/results.json"
RECEIPTS_DIR = REPO / "discovery_fabric/v1_13_gate2/receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_CALLS_PER_RUN = 12  # resumable
MAX_RETRIES = 2
TEMPERATURE = 0.3
INTER_CALL_DELAY = 3.0  # seconds between calls (rate-limit friendly)

# Hard constraints on tolerance bounds (multiplicative)
TOLERANCE_LOWER_MIN = 0.25  # predicted * 0.25 = lower bound
TOLERANCE_UPPER_MAX = 4.0   # predicted * 4.0 = upper bound

# ---------------------------------------------------------------------------
# Evidence-only system prompt (LEAKAGE CONTROL)
# ---------------------------------------------------------------------------

GEN_SYS = """You are a scientific prediction engine operating under STRICT EVIDENCE-ONLY protocol.

CRITICAL RULES:
1. You may ONLY reason from the evidence text provided in the user message.
2. Do NOT use any prior knowledge of chemistry, biology, physics, history,
   specific materials, specific technologies, or any specific case study.
3. Do NOT use knowledge of which historical experiments succeeded or failed.
4. Do NOT pattern-match to known discoveries (e.g., lithium-ion batteries,
   PCR, CRISPR, mRNA vaccines). Treat the evidence as if from an unfamiliar
   world.
5. Your prediction must be a CONSEQUENCE of the evidence — a relation that
   is not explicitly stated but follows from combining the evidence.

OUTPUT FORMAT (JSON only, no markdown, no commentary):
{
  "hypothesis": "one-sentence proposed relationship not explicit in evidence",
  "prediction": "specific quantitative or binary prediction",
  "predicted_value": <number or "YES" or "NO">,
  "tolerance_lower": <float between 0.25 and 1.0, e.g. 0.5>,
  "tolerance_upper": <float between 1.0 and 4.0, e.g. 2.0>,
  "expected_direction": "INCREASE" | "DECREASE" | "BINARY",
  "measurement_method": "how to measure the prediction",
  "falsification_condition": "what specific result would falsify this"
}

FORBIDDEN:
- Broad ranges like "1-1000" or ">50" or "10-30%" — these are range-fitting.
- Vague predictions without a specific numeric value.
- Predictions that simply restate the evidence.
- Predictions that name a specific known technology (e.g., "AlexNet",
  "LiCoO2-graphite battery") — these betray parametric memory leakage.

The tolerance bounds are MULTIPLICATIVE. If predicted_value=100 and
tolerance_lower=0.5, tolerance_upper=2.0, the prediction is "100, falsified
if observed < 50 or > 200".
"""

CONFIG_PROMPTS = {
    "B_llm_only": lambda evidence: f"""EVIDENCE (cutoff enforced — use ONLY this text):
---
{evidence}
---
Based ONLY on the evidence above, propose ONE falsifiable quantitative prediction. Output JSON only.""",

    "C_mechanism": lambda evidence: f"""EVIDENCE:
---
{evidence}
---
Identify the CORE MECHANISM in the evidence above (a process, reaction, or
relational structure). Then propose ONE falsifiable quantitative prediction
that follows from THAT MECHANISM. Output JSON only.""",

    "F_full": lambda evidence: f"""EVIDENCE:
---
{evidence}
---
Identify (a) invariant principles, (b) operational constraints, and (c) mechanism
interactions in the evidence above. Then propose ONE falsifiable quantitative
prediction with a specific point estimate and tight tolerance. Output JSON only.""",

    "D_random": lambda evidence: f"""EVIDENCE:
---
{evidence}
---
Propose ANY plausible scientific prediction that follows from the evidence
above. The prediction should be specific and falsifiable. Output JSON only.""",
}


# ---------------------------------------------------------------------------
# z-ai CLI wrapper
# ---------------------------------------------------------------------------

def call_zai(prompt: str, system: str, max_tokens: int = 600) -> str | None:
    """Call z-ai CLI and return the assistant's text response."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as f:
        out_path = f.name
    try:
        cmd = ["z-ai", "chat", "--prompt", prompt, "--system", system, "--output", out_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0:
            return None
        with open(out_path) as f:
            data = json.load(f)
        # The z-ai CLI returns the full chat completion response
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


def call_with_retry(prompt: str, system: str, mt: int = 600) -> tuple[dict | None, bool]:
    for attempt in range(MAX_RETRIES):
        text = call_zai(prompt, system, max_tokens=mt)
        if text:
            # Strip markdown fences
            text = text.strip().strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    parsed = json.loads(m.group())
                    # Validate tolerance bounds
                    if validate_prediction(parsed):
                        return parsed, True
                except json.JSONDecodeError:
                    pass
            # If JSON parse failed but we got text, return as raw
            return {"_raw": text[:500]}, True
        time.sleep(1.5)
    return None, False


def validate_prediction(p: dict) -> bool:
    """Validate that the prediction meets the leakage-control constraints."""
    if "predicted_value" not in p:
        return False
    pv = p["predicted_value"]
    direction = p.get("expected_direction", "").upper()

    if direction == "BINARY":
        if not isinstance(pv, str) or pv.upper() not in {"YES", "NO"}:
            return False
        return True

    # Numeric: must have predicted_value (number) + tolerance bounds
    if not isinstance(pv, (int, float)):
        return False
    tl = p.get("tolerance_lower")
    tu = p.get("tolerance_upper")
    if not isinstance(tl, (int, float)) or not isinstance(tu, (int, float)):
        return False
    if not (TOLERANCE_LOWER_MIN <= tl <= 1.0):
        return False
    if not (1.0 <= tu <= TOLERANCE_UPPER_MAX):
        return False
    return True


# ---------------------------------------------------------------------------
# Checkpoint management
# ---------------------------------------------------------------------------

def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"completed": [], "results": [], "calls_this_run": 0}


def save_checkpoint(cp: dict) -> None:
    cp["calls_this_run"] = 0
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def main() -> None:
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

        for config_name, prompt_fn in CONFIG_PROMPTS.items():
            if cp["calls_this_run"] >= MAX_CALLS_PER_RUN:
                save_checkpoint(cp)
                print(f"  Checkpoint: {len(cp['completed'])}/{len(cases)}. Run again.")
                return

            key = f"{case_id}|{config_name}"
            if any(r.get("key") == key for r in cp["results"]):
                continue

            print(f"  [{config_name}] {case_id}...", end=" ", flush=True)
            prompt = prompt_fn(evidence)
            result, gen_ok = call_with_retry(prompt, GEN_SYS)
            cp["calls_this_run"] += 1

            if not gen_ok or not result or "_raw" in result:
                print("GEN FAILED" if not gen_ok else "VALIDATION FAILED")
                cp["results"].append({
                    "key": key, "case_id": case_id, "config": config_name,
                    "gen_success": False, "failure_reason": "validation_failed_or_no_json",
                })
                save_checkpoint(cp)
                continue

            hypothesis = result.get("hypothesis", "")
            prediction = result.get("prediction", "")
            predicted_value = result.get("predicted_value")
            tl = result.get("tolerance_lower")
            tu = result.get("tolerance_upper")
            direction = result.get("expected_direction", "BINARY").upper()
            measurement = result.get("measurement_method", "")
            falsifier = result.get("falsification_condition", "")

            # Build a units_range string for receipt compatibility
            if direction == "BINARY":
                units_range = "BINARY"
            elif isinstance(predicted_value, (int, float)) and isinstance(tl, (int, float)) and isinstance(tu, (int, float)):
                low = predicted_value * tl
                high = predicted_value * tu
                units_range = f"{low:.4g} to {high:.4g}"
            else:
                units_range = ""

            candidate_id = f"PRED2-{case_id}-{config_name}"
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

            # Add Gate 2 specific fields (post-hoc, not part of immutable hash)
            receipt["gate2_predicted_value"] = predicted_value
            receipt["gate2_tolerance_lower"] = tl
            receipt["gate2_tolerance_upper"] = tu
            receipt["gate2_leakage_control"] = "evidence_only_prompt"
            receipt["gate2_backend"] = "z-ai-cli-glm-4-plus"

            # Save receipt
            receipt_path = RECEIPTS_DIR / f"{candidate_id}.json"
            with open(receipt_path, "w") as f:
                json.dump(receipt, f, indent=2, ensure_ascii=False)

            cp["results"].append({
                "key": key,
                "case_id": case_id,
                "config": config_name,
                "gen_success": True,
                "candidate_id": candidate_id,
                "predicted_value": predicted_value,
                "tolerance_lower": tl,
                "tolerance_upper": tu,
                "expected_direction": direction,
                "units_range": units_range,
                "receipt_path": str(receipt_path),
                "receipt_hash": receipt["receipt_hash"],
                "evidence_hash": evidence_hash,
            })
            print(f"OK pred={predicted_value} tol=[{tl},{tu}]")
            save_checkpoint(cp)
            time.sleep(INTER_CALL_DELAY)

        cp["completed"].append(case_id)
        save_checkpoint(cp)

    save_checkpoint(cp)
    print(f"\nGeneration complete: {len(cp['results'])} receipts.")
    print(f"Receipts saved to: {RECEIPTS_DIR}")


if __name__ == "__main__":
    main()
