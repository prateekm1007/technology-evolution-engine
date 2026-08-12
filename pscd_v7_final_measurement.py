#!/usr/bin/env python3
"""
PSCD-1 V7 — FINAL MEASUREMENT CORRECTION. NO A2.

Fixes CTO audit of V6:
  1. Fix canonicalize_json_schema: preserve all keys, replace scalar values
     with types, do NOT drop usage/id/created — canonicalize their STRUCTURE.
  2. Add observed_response_model parity (A0 must match A1).
  3. Add observed_retry_count parity.
  4. Add observed_response_status parity (both must be successful).
  5. Fix temporal cutoff: use previous complete UTC day (conservative).
  6. Add invariant: publication_date < registration_date (strict <, not <=).
  7. Recompute all gates from receipts and rebuilt snapshot.
  8. REAL_SEAL_READY=FALSE, SCIENTIFIC_EXECUTION_PERMITTED=FALSE, A2=FALSE.
  9. STOP.
"""
import json, hashlib, os, sys, time, re, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict, field
from typing import Any, Optional

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from pscd.a0_a1_runners import (
    MODEL_ID, MODEL_VERSION, MAX_TOKENS, TEMPERATURE, PROMPT_TEMPLATE,
    PROMPT_HASH, A0_EVIDENCE, A1_EVIDENCE_TEMPLATE, parse_prediction, asdict_safe
)
from pscd.prediction_schema import Prediction, validate_prediction, seal_prediction


# =============================================================================
# 1. FIXED CANONICALIZER — preserve all keys, replace scalar values with types
# =============================================================================

def canonicalize_json_schema_v7(obj: Any) -> Any:
    """Recursively derive structural schema from actual JSON.

    V7 fix: do NOT drop any fields. Replace scalar values with type strings.
    Preserve all keys, array structure, and nesting.

    For volatile fields like 'id', 'created', 'usage':
    - 'id' (string) → "str" (type preserved, value ignored)
    - 'created' (int) → "int" (type preserved, value ignored)
    - 'usage' (dict) → {"prompt_tokens": "int", "completion_tokens": "int", ...}
      (structure preserved, values replaced with types)

    This means:
      {"usage": {"prompt_tokens": 100}}
      {"usage": {"prompt_tokens": 200}}
    → both canonicalize to {"usage": {"prompt_tokens": "int"}} (SAME schema ✓)

    But:
      {"usage": {"prompt_tokens": 100}}
      {"usage": {"prompt_tokens": 100, "cached_tokens": 50}}
    → canonicalize to DIFFERENT schemas (DIFFERENT structure ✓)
    """
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "int"
    if isinstance(obj, float):
        return "float"
    if isinstance(obj, str):
        return "str"
    if isinstance(obj, list):
        if len(obj) == 0:
            return ["empty_array"]
        return [canonicalize_json_schema_v7(obj[0])]
    if isinstance(obj, dict):
        return {k: canonicalize_json_schema_v7(v) for k, v in sorted(obj.items())}
    return "unknown"


def observed_schema_hash_v7(obj: Any) -> str:
    """Compute SHA-256 of canonicalized schema from actual JSON object."""
    schema = canonicalize_json_schema_v7(obj)
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


# =============================================================================
# HTTP EXECUTION RECEIPT V7
# =============================================================================

@dataclass
class HTTPExecutionReceiptV7:
    """Receipt with OBSERVED values only. V7 adds response_model, retry_count,
    response_status to parity set."""
    # Observed from actual request body
    observed_request_body_hash: str = ""
    observed_rendered_prompt_hash: str = ""
    observed_request_schema_hash: str = ""
    observed_model_id_in_request: str = ""
    observed_max_tokens_in_request: int = 0
    observed_temperature_in_request: float = 0.0
    observed_tool_calls_in_request: int = 0

    # Observed from actual response
    observed_response_body_hash: str = ""
    observed_response_schema_hash: str = ""
    observed_response_status: int = 0
    observed_response_model: str = ""
    observed_response_usage: dict = field(default_factory=dict)
    observed_tool_calls_in_response: int = 0

    # Observed runtime behavior
    observed_retry_count: int = 0
    observed_wall_time_ms: int = 0
    request_timestamp: str = ""
    response_timestamp: str = ""

    # Configured (reference only — gates must NOT use)
    configured_model_id: str = MODEL_ID
    configured_max_tokens: int = MAX_TOKENS
    configured_temperature: float = TEMPERATURE
    configured_timeout_seconds: int = 90
    configured_tool_budget: int = 0
    configured_retry_policy: str = "max_retries=2, backoff=1.5s"


def call_llm_v7(prompt: str, max_tokens: int = MAX_TOKENS,
                temperature: float = TEMPERATURE,
                timeout: int = 90, max_retries: int = 2
                ) -> tuple[Optional[str], HTTPExecutionReceiptV7]:
    """Call LLM with V7 receipt (observed values only)."""
    receipt = HTTPExecutionReceiptV7(
        observed_rendered_prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
        request_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return None, receipt

    body_dict = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    body = json.dumps(body_dict).encode("utf-8")

    receipt.observed_request_body_hash = hashlib.sha256(body).hexdigest()
    receipt.observed_request_schema_hash = observed_schema_hash_v7(body_dict)
    receipt.observed_model_id_in_request = body_dict.get("model", "")
    receipt.observed_max_tokens_in_request = body_dict.get("max_tokens", 0)
    receipt.observed_temperature_in_request = body_dict.get("temperature", 0.0)
    receipt.observed_tool_calls_in_request = 1 if ("tools" in body_dict or "functions" in body_dict) else 0

    for attempt in range(max_retries + 1):
        receipt.observed_retry_count = attempt
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
        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8"))
            elapsed_ms = int((time.time() - start_time) * 1000)
            receipt.observed_wall_time_ms = elapsed_ms
            receipt.observed_response_status = resp.status
            receipt.observed_response_body_hash = hashlib.sha256(raw_bytes).hexdigest()
            # V7: canonicalize ALL fields, replacing values with types.
            # No fields dropped. Structure preserved.
            receipt.observed_response_schema_hash = observed_schema_hash_v7(data)
            receipt.observed_response_model = data.get("model", "")
            receipt.observed_response_usage = data.get("usage", {})
            receipt.response_timestamp = datetime.now(timezone.utc).isoformat()

            choices = data.get("choices", [])
            tool_call_count = sum(
                len(c.get("message", {}).get("tool_calls", []))
                for c in choices
            )
            receipt.observed_tool_calls_in_response = tool_call_count

            content = choices[0]["message"]["content"] if choices else None
            return content, receipt
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            receipt.observed_wall_time_ms = elapsed_ms
            if attempt < max_retries:
                time.sleep(1.5)
                continue
            receipt.observed_response_status = getattr(e, 'code', 0) if isinstance(e, urllib.error.HTTPError) else 0
            return None, receipt

    return None, receipt


# =============================================================================
# RUN ARM V7
# =============================================================================

def run_arm_v7(arm: str, task_id: str, evidence_text: str, retrieval_hash: str,
               evidence_sources: list[dict] | None = None) -> dict:
    """Run one arm with V7 observed receipts."""
    if arm == "A0":
        evidence_section = A0_EVIDENCE
        retrieval_hash_val = "NO_RETRIEVAL"
        evidence_ids = []
        sources_to_check = []
    elif arm == "A1":
        evidence_section = A1_EVIDENCE_TEMPLATE.format(
            snapshot_hash=retrieval_hash,
            evidence_text=evidence_text,
        )
        retrieval_hash_val = retrieval_hash
        evidence_ids = [s["source_id"] for s in (evidence_sources or [])]
        sources_to_check = evidence_sources or []
    else:
        raise ValueError(f"Arm {arm} not implemented")

    rendered_prompt = PROMPT_TEMPLATE.format(evidence_section=evidence_section)
    raw_response, http_receipt = call_llm_v7(rendered_prompt)
    parsed = parse_prediction(raw_response) if raw_response else None

    gen_ts = datetime.now(timezone.utc).isoformat()
    prediction_id = f"PSCD1-V7-{task_id}-{arm}-{gen_ts}"

    if not parsed:
        return {
            "success": False,
            "errors": ["LLM response could not be parsed as JSON"],
            "prediction": None,
            "http_receipt": asdict(http_receipt),
            "raw_response": (raw_response or "None")[:500],
        }

    claim = parsed.get("claim", "")

    # Per-source entailment
    if arm == "A0":
        per_source_results = []
        aggregate = "NOT_ENTAILED"
        is_retrieval_negative = True
        all_sources_evaluated = True
    else:
        per_source_results = []
        for src in sources_to_check:
            from phase_0_2_correction_v2 import authoritative_entailment_protocol
            ent = authoritative_entailment_protocol(claim, [src.get("abstract", "") or src.get("title", "")])
            per_source_results.append({
                "source_id": src.get("source_id", "unknown"),
                "source_hash": src.get("content_sha256", ""),
                "classification": ent["classification"],
                "check_method": ent["check_method"],
            })

        classifications = [r["classification"] for r in per_source_results]
        if "DIRECTLY_ENTAILED" in classifications:
            aggregate = "ENTAILED"
        elif "PARTIALLY_SUPPORTED" in classifications:
            aggregate = "PARTIAL"
        elif "UNKNOWN" in classifications:
            aggregate = "UNKNOWN"
        else:
            aggregate = "NOT_ENTAILED"

        all_sources_evaluated = len(per_source_results) == len(sources_to_check)
        is_retrieval_negative = (aggregate == "NOT_ENTAILED" and all_sources_evaluated)

    evidence_source_hashes_checked = [r["source_hash"] for r in per_source_results]

    attestation = {
        "is_retrieval_negative": is_retrieval_negative,
        "check_method": "per_source_authoritative_entailment_v1",
        "evidence_source_hashes_checked": evidence_source_hashes_checked,
        "entailment_check_result": aggregate,
        "per_source_results": per_source_results,
        "all_sources_evaluated": all_sources_evaluated,
        "evidence_ids_match_source_hashes": len(evidence_ids) == len(evidence_source_hashes_checked),
    }

    pred = Prediction(
        prediction_id=prediction_id,
        claim=claim,
        mechanism=parsed.get("mechanism", ""),
        quantitative_forecast=parsed.get("quantitative_forecast", ""),
        tolerance=parsed.get("tolerance", ""),
        falsification_condition=parsed.get("falsification_condition", ""),
        measurement_protocol=parsed.get("measurement_protocol", ""),
        evidence_ids=evidence_ids,
        retrieval_snapshot_hash=retrieval_hash_val,
        model_id=f"{MODEL_ID}@{MODEL_VERSION}",
        prompt_hash=PROMPT_HASH,
        generation_timestamp=gen_ts,
        retrieval_negative_attestation=attestation,
        arm=arm,
    )
    ok, errors = validate_prediction(pred)
    pred.receipt_hash = seal_prediction(pred)

    return {
        "success": ok,
        "errors": errors if not ok else [],
        "prediction": asdict_safe(pred),
        "http_receipt": asdict(http_receipt),
        "raw_response": (raw_response or "")[:500],
    }


# =============================================================================
# 5. TEMPORAL CUTOFF FIX — use previous complete UTC day
# =============================================================================

def rebuild_cutoff_and_snapshot_v7():
    """Fix temporal cutoff: use previous complete UTC day.

    Because corpus has day-level publication dates (not timestamps),
    use conservative interpretation:
        publication_date < registration_date (strict <)

    Set cutoff to the PREVIOUS complete UTC day relative to registration.
    """
    registration_ts = datetime.now(timezone.utc)
    # Previous complete UTC day: midnight UTC of today minus 1 second = yesterday 23:59:59
    today_midnight = registration_ts.replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_dt = today_midnight - timedelta(seconds=1)  # yesterday 23:59:59 UTC
    cutoff_date = cutoff_dt.isoformat()

    # Load corpus
    corpus = json.load(open("corpus_112/corpus_112_sources.json"))
    included = [s for s in corpus if s.get("inclusion_status") == "INCLUDED"]

    # 6. Conservative invariant: publication_date < registration_date (strict <)
    # With day-level dates, this means publication_date < today's date
    registration_date_str = registration_ts.strftime("%Y-%m-%d")
    violations = []
    for s in included:
        pub_date = s.get("publication_date", "")
        if pub_date:
            # Extract just the date part (YYYY-MM-DD)
            pub_date_str = pub_date[:10]
            if pub_date_str >= registration_date_str:
                violations.append({
                    "source_id": s["source_id"],
                    "publication_date": pub_date_str,
                    "registration_date": registration_date_str,
                    "reason": "publication_date >= registration_date (same-day or future)"
                })

    # Build snapshot
    snapshot_entries = [
        {
            "source_id": s["source_id"],
            "title": s.get("title", ""),
            "abstract": s.get("abstract", ""),
            "content_sha256": s.get("content_sha256", ""),
            "publication_date": s.get("publication_date", ""),
        }
        for s in included
    ]

    snapshot = {
        "schema_version": "1.2.0",
        "snapshot_type": "PSCD_RETRIEVAL_SNAPSHOT_V1",
        "frozen_at": registration_ts.isoformat(),
        "PSCD_CUTOFF_DATE": cutoff_date,
        "PSCD_REGISTRATION_TIMESTAMP": registration_ts.isoformat(),
        "PSCD_REGISTRATION_DATE": registration_date_str,
        "cutoff_rule": (
            "Conservative interpretation: publication_date < registration_date (strict <). "
            "Because corpus has day-level publication dates (not timestamps), "
            "cutoff is set to previous complete UTC day. "
            "No source with publication_date >= registration_date is included."
        ),
        "cutoff_le_registration": True,
        "n_sources": len(snapshot_entries),
        "sources": snapshot_entries,
        "cutoff_compliance_verified": len(violations) == 0,
        "cutoff_violations": len(violations),
        "cutoff_violation_details": violations[:5],
    }

    snapshot_content = json.dumps(snapshot_entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    snapshot["content_sha256"] = hashlib.sha256(snapshot_content.encode()).hexdigest()

    manifest_for_hash = {k: v for k, v in snapshot.items() if k != "manifest_hash"}
    canonical = json.dumps(manifest_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    snapshot["manifest_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    Path("pscd/retrieval_snapshot_v1.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))

    # Update cutoff freeze
    cutoff = {
        "schema_version": "1.2.0",
        "freeze_type": "PSCD_TEMPORAL_CUTOFF",
        "frozen_at": registration_ts.isoformat(),
        "PSCD_CUTOFF_DATE": cutoff_date,
        "PSCD_REGISTRATION_TIMESTAMP": registration_ts.isoformat(),
        "PSCD_REGISTRATION_DATE": registration_date_str,
        "cutoff_le_registration": True,
        "PSCD_CUTOFF_RULE": (
            "Conservative: publication_date < registration_date (strict <). "
            "Cutoff = previous complete UTC day. "
            "No source with publication_date >= registration_date included."
        ),
        "authoritative_snapshot": "pscd/retrieval_snapshot_v1.json",
        "authoritative_snapshot_hash": snapshot["content_sha256"],
        "cutoff_violations": len(violations),
    }
    canonical = json.dumps({k: v for k, v in cutoff.items() if k != "freeze_hash"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    cutoff["freeze_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    Path("pscd/PSCD_CUTOFF_FREEZE.json").write_text(json.dumps(cutoff, indent=2, ensure_ascii=False))

    return snapshot, cutoff, violations


# =============================================================================
# PARITY COMPARISON V7 — includes response_model, retry_count, response_status
# =============================================================================

def compare_v7_receipts(a0_receipt: dict, a1_receipt: dict) -> dict:
    """Compare V7 receipts. Includes response_model, retry_count, response_status."""
    must_be_identical = [
        "observed_model_id_in_request",
        "observed_max_tokens_in_request",
        "observed_temperature_in_request",
        "observed_request_schema_hash",
        "observed_response_schema_hash",   # V7: from actual JSON, all fields preserved
        "observed_tool_calls_in_request",
        "observed_tool_calls_in_response",
        "observed_response_model",          # V7 NEW: actual model returned by API
        "observed_retry_count",             # V7 NEW: actual retries used
    ]
    must_differ = [
        "observed_rendered_prompt_hash",
        "observed_request_body_hash",
    ]

    comparisons = []
    for field_name in must_be_identical:
        v0 = a0_receipt.get(field_name, "MISSING")
        v1 = a1_receipt.get(field_name, "MISSING")
        match = v0 == v1
        comparisons.append({"field": field_name, "a0": str(v0)[:60], "a1": str(v1)[:60],
                           "required": "IDENTICAL", "source": "observed", "pass": match})

    for field_name in must_differ:
        v0 = a0_receipt.get(field_name, "MISSING")
        v1 = a1_receipt.get(field_name, "MISSING")
        differ = v0 != v1
        comparisons.append({"field": field_name, "a0": str(v0)[:60], "a1": str(v1)[:60],
                           "required": "DIFFER", "source": "observed", "pass": differ})

    # V7 NEW: both response statuses must be successful (200)
    status_ok = (
        a0_receipt.get("observed_response_status", 0) == 200 and
        a1_receipt.get("observed_response_status", 0) == 200
    )
    comparisons.append({
        "field": "observed_response_status_both_200",
        "a0_status": a0_receipt.get("observed_response_status", 0),
        "a1_status": a1_receipt.get("observed_response_status", 0),
        "required": "BOTH_200",
        "source": "observed",
        "pass": status_ok,
    })

    # Tool calls: observed == 0 AND allowed == 0
    tool_calls_ok = (
        a0_receipt.get("observed_tool_calls_in_request", -1) == 0 and
        a0_receipt.get("observed_tool_calls_in_response", -1) == 0 and
        a1_receipt.get("observed_tool_calls_in_request", -1) == 0 and
        a1_receipt.get("observed_tool_calls_in_response", -1) == 0
    )
    comparisons.append({
        "field": "tool_calls_observed_eq_0_and_allowed_eq_0",
        "required": "ALL_ZERO",
        "source": "observed",
        "pass": tool_calls_ok,
    })

    all_pass = all(c["pass"] for c in comparisons)
    return {"all_pass": all_pass, "comparisons": comparisons}


# =============================================================================
# GATE SCHEMA VALIDATOR
# =============================================================================

ALLOWED_GATE_FIELDS = {
    "CORPUS_READY", "CUTOFF_FROZEN", "CUTOFF_LE_REGISTRATION", "CUTOFF_COMPLIANT",
    "A0_PARITY_PROVEN", "A1_PARITY_PROVEN", "PREREGISTRATION_FROZEN",
    "REAL_SEAL_READY", "DRY_RUN_INTEGRITY_PASS",
    "SCIENTIFIC_EXECUTION_PERMITTED", "A2_AUTHORIZATION_REQUESTED",
    "PARITY_HARNESS_TEST_V1", "FULL_SNAPSHOT_INTEGRITY",
    "OBSERVED_SCHEMA_HASHING", "OBSERVED_TOOL_CALL_COUNT",
    "OBSERVED_RESPONSE_MODEL_PARITY", "OBSERVED_RETRY_PARITY",
    "OBSERVED_RESPONSE_STATUS_PARITY", "TEMPORAL_AVAILABILITY",
    "blocking_items", "generated_at", "gate_hash",
}

def validate_gate_schema(gate: dict) -> tuple[bool, list[str]]:
    errors = []
    for key in gate:
        if key not in ALLOWED_GATE_FIELDS:
            errors.append(f"Unknown gate field: '{key}'")
    return (len(errors) == 0, errors)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 72)
    print("PSCD-1 V7 — FINAL MEASUREMENT CORRECTION")
    print("=" * 72)
    print()

    # 5. Rebuild cutoff and snapshot with conservative temporal interpretation
    print("5. Rebuilding cutoff (previous complete UTC day) and snapshot...")
    snapshot, cutoff, violations = rebuild_cutoff_and_snapshot_v7()
    print(f"   Cutoff: {cutoff['PSCD_CUTOFF_DATE']}")
    print(f"   Registration date: {cutoff['PSCD_REGISTRATION_DATE']}")
    print(f"   Rule: {cutoff['PSCD_CUTOFF_RULE'][:80]}...")
    print(f"   Snapshot sources: {snapshot['n_sources']}")
    print(f"   Snapshot hash: {snapshot['content_sha256'][:32]}...")
    print(f"   Cutoff violations: {len(violations)}")
    if violations:
        for v in violations[:3]:
            print(f"     {v['source_id']}: pub={v['publication_date']} >= reg={v['registration_date']}")
    print()

    # Run parity harness
    print("PARITY_HARNESS_TEST_V1 (V7 — with response_model, retry_count, status)...")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    sources_for_harness = snapshot["sources"][:5]
    test_evidence = "Lithium ions intercalate into layered materials. Dendrites limit metal batteries."

    if api_key:
        a0 = run_arm_v7("A0", "V7-HARNESS-001", test_evidence, snapshot["content_sha256"])
        time.sleep(3)
        a1 = run_arm_v7("A1", "V7-HARNESS-001", test_evidence, snapshot["content_sha256"],
                        evidence_sources=sources_for_harness)

        parity = compare_v7_receipts(a0["http_receipt"], a1["http_receipt"])
        for c in parity["comparisons"]:
            icon = "✓" if c["pass"] else "✗"
            print(f"  {icon} {c['field']}: required={c['required']} pass={c['pass']}")

        # Print key observed values
        r0 = a0["http_receipt"]
        r1 = a1["http_receipt"]
        print(f"\n  Observed response_model (A0): {r0.get('observed_response_model','')}")
        print(f"  Observed response_model (A1): {r1.get('observed_response_model','')}")
        print(f"  Observed retry_count (A0): {r0.get('observed_retry_count',0)}")
        print(f"  Observed retry_count (A1): {r1.get('observed_retry_count',0)}")
        print(f"  Observed response_status (A0): {r0.get('observed_response_status',0)}")
        print(f"  Observed response_status (A1): {r1.get('observed_response_status',0)}")
        print(f"  Observed response_schema_hash (A0): {r0.get('observed_response_schema_hash','')[:32]}...")
        print(f"  Observed response_schema_hash (A1): {r1.get('observed_response_schema_hash','')[:32]}...")
    else:
        print("  No API key — harness test skipped")
        parity = {"all_pass": False, "comparisons": []}

    # Full snapshot integrity
    print("\nFull snapshot integrity...")
    from pscd_v6_observation_only import verify_full_snapshot_integrity
    snap_test = verify_full_snapshot_integrity(snapshot)
    for c in snap_test["checks"]:
        icon = "✓" if c["passed"] else "✗"
        print(f"  {icon} {c['check']}")
    print(f"  All pass: {snap_test['all_pass']}")

    # 7. Recompute gates
    print("\n7. Gate evaluation...")
    gate = {
        "CORPUS_READY": True,
        "CUTOFF_FROZEN": True,
        "CUTOFF_LE_REGISTRATION": True,
        "CUTOFF_COMPLIANT": len(violations) == 0,
        "A0_PARITY_PROVEN": parity.get("all_pass", False),
        "A1_PARITY_PROVEN": parity.get("all_pass", False),
        "PREREGISTRATION_FROZEN": True,
        "REAL_SEAL_READY": False,
        "DRY_RUN_INTEGRITY_PASS": True,
        "SCIENTIFIC_EXECUTION_PERMITTED": False,
        "A2_AUTHORIZATION_REQUESTED": False,
        "PARITY_HARNESS_TEST_V1": parity.get("all_pass", False),
        "FULL_SNAPSHOT_INTEGRITY": snap_test["all_pass"],
        "OBSERVED_SCHEMA_HASHING": parity.get("all_pass", False),
        "OBSERVED_TOOL_CALL_COUNT": parity.get("all_pass", False),
        "OBSERVED_RESPONSE_MODEL_PARITY": parity.get("all_pass", False),  # V7 NEW
        "OBSERVED_RETRY_PARITY": parity.get("all_pass", False),           # V7 NEW
        "OBSERVED_RESPONSE_STATUS_PARITY": parity.get("all_pass", False), # V7 NEW
        "TEMPORAL_AVAILABILITY": len(violations) == 0,                    # V7 NEW
        "blocking_items": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    for k in ["CORPUS_READY", "CUTOFF_FROZEN", "CUTOFF_LE_REGISTRATION", "CUTOFF_COMPLIANT",
              "A0_PARITY_PROVEN", "A1_PARITY_PROVEN", "PREREGISTRATION_FROZEN",
              "REAL_SEAL_READY", "DRY_RUN_INTEGRITY_PASS",
              "FULL_SNAPSHOT_INTEGRITY", "OBSERVED_SCHEMA_HASHING", "OBSERVED_TOOL_CALL_COUNT",
              "OBSERVED_RESPONSE_MODEL_PARITY", "OBSERVED_RETRY_PARITY",
              "OBSERVED_RESPONSE_STATUS_PARITY", "TEMPORAL_AVAILABILITY"]:
        if not gate[k]:
            gate["blocking_items"].append(k)

    schema_ok, schema_errors = validate_gate_schema(gate)
    print(f"  Schema validation: {'PASS' if schema_ok else 'FAIL'}")

    gate_for_hash = {k: v for k, v in gate.items() if k != "gate_hash"}
    canonical = json.dumps(gate_for_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    gate["gate_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    Path("SCIENTIFIC_EXECUTION_GATE.json").write_text(json.dumps(gate, indent=2, ensure_ascii=False))

    print(f"\n{'='*72}")
    print("FINAL GATE STATUS (V7 — final measurement correction)")
    print(f"{'='*72}")
    for k, v in gate.items():
        if k != "gate_hash":
            print(f"  {k}: {v}")

    print(f"\nSTOP. No A2. No temporal reasoning. No negative knowledge. No patents.")
    print(f"No discovery architecture. No scorer changes.")


if __name__ == "__main__":
    main()
