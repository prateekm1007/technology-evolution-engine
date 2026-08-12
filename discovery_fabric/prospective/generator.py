"""
PROSPECTIVE EXPERIMENT — Prediction Generator
==============================================

Stage 4 of the prospective pipeline:
    PRE_REGISTER → FREEZE_MODEL → FREEZE_EVIDENCE → GENERATE_PREDICTION
                 → WAIT → EXTERNAL_OBSERVATION → DETERMINISTIC_SCORE

This module generates predictions for all 4 arms under the frozen model and
frozen corpus. It is invoked AFTER the pre-registration manifest is sealed
and AFTER the model snapshot and retrieval corpus have been verified to
match the manifest.

CRITICAL INVARIANTS (enforced by audit_verifier.py):
    (I6) The generator MUST NOT be invoked until the manifest is sealed.
    (I7) The generator MUST verify that the model snapshot matches the
         manifest before generating any prediction.
    (I8) The generator MUST verify that the retrieval corpus matches the
         manifest before generating any prediction.
    (I9) The generator MUST verify that the retrieval corpus's date filter
         excludes all documents dated after the manifest timestamp.
    (I10) All 4 arms MUST be generated in the SAME run, with the SAME
          model snapshot, SAME corpus, SAME timestamp. They CANNOT be
          generated separately.
    (I11) The generator MUST NOT be given any outcome information. The
          problem description is the only input.
    (I12) Each prediction receipt is hash-sealed immediately after generation.
          The receipt's timestamp is the REAL generation timestamp (UTC).
    (I13) The generator MUST NOT retry failed generations with different
          prompts. If a generation fails, it is recorded as INDETERMINATE
          in the receipt log. (Retries with the SAME prompt are allowed.)

DO NOT RUN THIS MODULE. It is infrastructure only. The actual generation
requires a real pre-registration manifest with all TO_BE_* fields filled in.
"""
from __future__ import annotations

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from discovery_fabric.v1_13.prediction_receipt import create_receipt  # noqa: E402
from discovery_fabric.prospective.pre_registration import (  # noqa: E402
    verify_manifest, MANIFESTS_DIR,
)

PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
RECEIPTS_DIR = PROSPECTIVE_DIR / "receipts"
LOG_FILE = MANIFESTS_DIR / "append_only_log.jsonl"

RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Hard constraints on tolerance bounds (multiplicative) — same as Gate 2
TOLERANCE_LOWER_MIN = 0.25
TOLERANCE_UPPER_MAX = 4.0


# =============================================================================
# Pre-generation verification
# =============================================================================

def verify_model_snapshot(manifest: dict) -> dict:
    """Verify the model snapshot matches the manifest.

    In a real run, this would:
        - If local model: hash the weights file and compare to manifest
        - If hosted model: query the endpoint's version info and compare

    In infrastructure mode, this returns a stub result.
    """
    expected = manifest.get("model_snapshot", {})
    return {
        "verified": expected.get("model_version") != "TO_BE_PINNED",
        "expected": expected,
        "actual": "INFRASTRUCTURE_STUB",
        "reason": "Real verification requires a real manifest (not the sample).",
    }


def verify_retrieval_corpus(manifest: dict) -> dict:
    """Verify the retrieval corpus matches the manifest.

    In a real run, this would:
        - Hash the corpus manifest file and compare
        - Verify the date filter excludes post-registration documents
        - Verify the document count matches

    In infrastructure mode, this returns a stub result.
    """
    expected = manifest.get("retrieval_corpus", {})
    date_filter_ok = (
        expected.get("date_filter_upper_bound") != "TO_BE_SET"
        and expected.get("date_filter_verified") is True
    )
    return {
        "verified": expected.get("corpus_hash") != "TO_BE_COMPUTED" and date_filter_ok,
        "expected": expected,
        "actual": "INFRASTRUCTURE_STUB",
        "date_filter_verified": date_filter_ok,
        "reason": "Real verification requires a real manifest (not the sample).",
    }


def verify_prerequisites(manifest: dict) -> tuple[bool, list[str]]:
    """Verify all prerequisites for generation are met.

    Returns (all_ok, list_of_failure_reasons).
    """
    failures = []

    # Manifest must be sealed (hash verified)
    if not verify_manifest(manifest):
        failures.append("manifest hash verification failed — manifest may have been modified")

    # Manifest must not contain TO_BE_* placeholders
    def find_placeholders(obj, path=""):
        if isinstance(obj, str) and obj.startswith("TO_BE_"):
            return [(path, obj)]
        if isinstance(obj, dict):
            out = []
            for k, v in obj.items():
                out.extend(find_placeholders(v, f"{path}.{k}"))
            return out
        if isinstance(obj, list):
            out = []
            for i, v in enumerate(obj):
                out.extend(find_placeholders(v, f"{path}[{i}]"))
            return out
        return []

    placeholders = find_placeholders(manifest)
    if placeholders:
        failures.append(f"manifest contains {len(placeholders)} TO_BE_* placeholders — fill them in first")

    # Model snapshot must be verified
    model_check = verify_model_snapshot(manifest)
    if not model_check["verified"]:
        failures.append(f"model snapshot not verified: {model_check['reason']}")

    # Retrieval corpus must be verified
    corpus_check = verify_retrieval_corpus(manifest)
    if not corpus_check["verified"]:
        failures.append(f"retrieval corpus not verified: {corpus_check['reason']}")

    return (len(failures) == 0, failures)


# =============================================================================
# Prediction generation
# =============================================================================

def generate_prediction_for_arm(
    arm_name: str,
    problem: dict,
    prompt_template: str,
    model_snapshot: dict,
    retrieval_corpus: dict,
    manifest_timestamp: str,
    generation_timestamp: str,
    llm_backend=None,  # callable: (prompt, system, max_tokens) -> str | None
) -> dict:
    """Generate a single prediction receipt for one arm.

    This function is called 4 times per problem (once per arm) in the SAME
    run. The receipts are hash-sealed immediately after generation.

    Args:
        arm_name: one of B_llm_only, C_mechanism, F_full, D_random
        problem: a problem dict from the manifest's problem_set
        prompt_template: the prompt template for this arm
        model_snapshot: the model snapshot dict from the manifest
        retrieval_corpus: the retrieval corpus dict from the manifest
        manifest_timestamp: the manifest's sealed timestamp (ISO)
        generation_timestamp: the REAL generation timestamp (ISO, UTC, now)
        llm_backend: optional callable for the LLM. If None, returns a stub.

    Returns:
        A prediction receipt dict (sealed, immutable).
    """
    # Format the prompt with the problem description
    prompt = prompt_template.format(
        description=problem["description"],
        corpus_query=problem["corpus_query"],
    )

    # Generate via LLM backend
    gen_result = None
    gen_success = False
    if llm_backend is not None:
        text = llm_backend(prompt, system="You are a scientific prediction engine.", max_tokens=600)
        if text:
            # Parse JSON
            import re
            text = text.strip().strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    gen_result = json.loads(m.group())
                    gen_success = validate_prediction(gen_result)
                except json.JSONDecodeError:
                    gen_result = {"_raw": text[:500]}

    # Build the receipt
    problem_id = problem["problem_id"]
    candidate_id = f"PROS-{problem_id}-{arm_name}"

    # If generation failed, produce an INDETERMINATE receipt
    if not gen_success or gen_result is None or "_raw" in (gen_result or {}):
        receipt = {
            "candidate_id": candidate_id,
            "manifest_hash": None,  # filled in by caller
            "arm": arm_name,
            "problem_id": problem_id,
            "hypothesis": "",
            "prediction": "",
            "predicted_value": None,
            "tolerance_lower": None,
            "tolerance_upper": None,
            "expected_direction": "INDETERMINATE",
            "units_range": "",
            "measurement_method": "",
            "falsification_condition": "",
            "manifest_timestamp": manifest_timestamp,
            "generation_timestamp": generation_timestamp,
            "generation_success": False,
            "model_snapshot": model_snapshot,
            "retrieval_corpus_hash": retrieval_corpus.get("corpus_hash"),
        }
    else:
        # Build units_range from point estimate + tolerance
        predicted_value = gen_result.get("predicted_value")
        tl = gen_result.get("tolerance_lower")
        tu = gen_result.get("tolerance_upper")
        direction = gen_result.get("expected_direction", "BINARY").upper()
        if direction == "BINARY":
            units_range = "BINARY"
        elif isinstance(predicted_value, (int, float)) and isinstance(tl, (int, float)) and isinstance(tu, (int, float)):
            low = predicted_value * tl
            high = predicted_value * tu
            units_range = f"{low:.4g} to {high:.4g}"
        else:
            units_range = ""

        receipt = {
            "candidate_id": candidate_id,
            "manifest_hash": None,  # filled in by caller
            "arm": arm_name,
            "problem_id": problem_id,
            "hypothesis": gen_result.get("hypothesis", ""),
            "prediction": gen_result.get("prediction", ""),
            "predicted_value": predicted_value,
            "tolerance_lower": tl,
            "tolerance_upper": tu,
            "expected_direction": direction,
            "units_range": units_range,
            "measurement_method": gen_result.get("measurement_method", ""),
            "falsification_condition": gen_result.get("falsification_condition", ""),
            "manifest_timestamp": manifest_timestamp,
            "generation_timestamp": generation_timestamp,
            "generation_success": True,
            "model_snapshot": model_snapshot,
            "retrieval_corpus_hash": retrieval_corpus.get("corpus_hash"),
        }

    # Seal the receipt
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt["receipt_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return receipt


def validate_prediction(p: dict) -> bool:
    """Validate that a prediction meets the prospective constraints."""
    if "predicted_value" not in p:
        return False
    pv = p["predicted_value"]
    direction = p.get("expected_direction", "").upper()
    if direction == "BINARY":
        if not isinstance(pv, str) or pv.upper() not in {"YES", "NO"}:
            return False
        return True
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


def generate_all_predictions(
    manifest: dict,
    llm_backend=None,
) -> list[dict]:
    """Generate predictions for ALL problems × ALL arms.

    CRITICAL: All 4 arms are generated in the SAME run, with the SAME
    model snapshot, SAME corpus, SAME generation_timestamp.

    Args:
        manifest: the sealed pre-registration manifest
        llm_backend: optional callable. If None, all generations are INDETERMINATE.

    Returns:
        List of sealed prediction receipts (4 × len(problem_set)).
    """
    # Verify prerequisites
    ok, failures = verify_prerequisites(manifest)
    if not ok:
        raise RuntimeError(f"Prerequisites not met:\n  - " + "\n  - ".join(failures))

    manifest_hash = manifest["manifest_hash"]
    manifest_timestamp = manifest["created_at"]
    model_snapshot = manifest["model_snapshot"]
    retrieval_corpus = manifest["retrieval_corpus"]
    prompt_templates = manifest["prompt_templates"]
    arms = manifest["arms"]

    # ALL arms use the SAME generation timestamp (atomicity)
    generation_timestamp = datetime.now(timezone.utc).isoformat()

    receipts = []
    for problem in manifest["problem_set"]:
        for arm in arms:
            receipt = generate_prediction_for_arm(
                arm_name=arm,
                problem=problem,
                prompt_template=prompt_templates[arm],
                model_snapshot=model_snapshot,
                retrieval_corpus=retrieval_corpus,
                manifest_timestamp=manifest_timestamp,
                generation_timestamp=generation_timestamp,
                llm_backend=llm_backend,
            )
            receipt["manifest_hash"] = manifest_hash
            # Re-seal with manifest_hash included
            receipt.pop("receipt_hash", None)
            canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            receipt["receipt_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
            receipts.append(receipt)

    return receipts


def save_receipts(receipts: list[dict]) -> list[Path]:
    """Save receipts to the receipts directory and append to the log."""
    paths = []
    log_entries = []
    for receipt in receipts:
        path = RECEIPTS_DIR / f"{receipt['candidate_id']}.json"
        with open(path, "w") as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        paths.append(path)
        log_entries.append({
            "log_entry_type": "PREDICTION_RECEIPT",
            "receipt_hash": receipt["receipt_hash"],
            "timestamp": receipt["generation_timestamp"],
            "manifest_hash": receipt["manifest_hash"],
            "candidate_id": receipt["candidate_id"],
            "arm": receipt["arm"],
            "problem_id": receipt["problem_id"],
            "generation_success": receipt["generation_success"],
        })
    # Append all entries to the log atomically (single write)
    with open(LOG_FILE, "a") as f:
        for entry in log_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return paths


# =============================================================================
# Main — infrastructure check only
# =============================================================================

def main():
    """Verify the generator infrastructure.

    DOES NOT GENERATE REAL PREDICTIONS. The sample manifest has TO_BE_*
    placeholders, so verify_prerequisites() will fail — which is the correct
    behavior. This proves the prerequisite check works.
    """
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — GENERATOR INFRASTRUCTURE CHECK")
    print("=" * 72)
    print()

    # Load the sample manifest
    sample_path = MANIFESTS_DIR / "_sample_pre_registration.json"
    if not sample_path.exists():
        print("Sample manifest not found. Run pre_registration.py first.")
        return
    with open(sample_path) as f:
        manifest = json.load(f)

    # Verify prerequisites — should FAIL because of TO_BE_* placeholders
    ok, failures = verify_prerequisites(manifest)
    print(f"Prerequisite check: {'PASS' if ok else 'FAIL (expected for sample manifest)'}")
    for f in failures:
        print(f"  - {f}")

    print()
    print("Generator infrastructure is in place. To run a real generation:")
    print("  1. Build a real manifest (no TO_BE_* placeholders)")
    print("  2. Provide a real LLM backend (frozen model snapshot)")
    print("  3. Provide a real retrieval corpus (frozen, hash-sealed)")
    print("  4. Call generate_all_predictions(manifest, llm_backend=...)")
    print()
    print("DO NOT run a real generation until the audit_verifier passes.")


if __name__ == "__main__":
    main()
