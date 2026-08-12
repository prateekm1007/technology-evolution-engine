"""
PROSPECTIVE EXPERIMENT — Deterministic Scorer
==============================================

Stage 7 of the prospective pipeline:
    PRE_REGISTER → FREEZE_MODEL → FREEZE_EVIDENCE → GENERATE_PREDICTION
                 → WAIT → EXTERNAL_OBSERVATION → DETERMINISTIC_SCORE

This module scores prediction receipts against external observations.
The scorer is 100% deterministic — no LLM judge. It reuses the Gate 2
evaluator's logic (information-content test + quantitative accuracy).

The scorer is INVOKED ONLY AFTER all observations have been collected.
It applies the pre-registered analysis plan (frozen BEFORE any outcomes
were observed).

CRITICAL INVARIANTS (enforced by audit_verifier.py):
    (I20) The scorer MUST NOT be invoked until ALL observations for the
          cohort are collected.
    (I21) The scorer MUST use the analysis plan from the pre-registration
          manifest. It MUST NOT use a different analysis plan.
    (I22) The scorer is deterministic: identical inputs produce identical
          outputs (modulo timestamp).
    (I23) The scorer's output is hash-sealed and appended to the log.

DO NOT RUN THIS MODULE until the observation window has closed and all
observations are collected.
"""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))

from discovery_fabric.v1_13_gate2.deterministic_entailment_test import classify_prediction  # noqa: E402

PROSPECTIVE_DIR = REPO / "discovery_fabric/prospective"
RECEIPTS_DIR = PROSPECTIVE_DIR / "receipts"
OBSERVATIONS_DIR = PROSPECTIVE_DIR / "observations"
SCORES_DIR = PROSPECTIVE_DIR / "scores"
LOG_FILE = PROSPECTIVE_DIR / "manifests" / "append_only_log.jsonl"

SCORES_DIR.mkdir(parents=True, exist_ok=True)

STRICT_CALIBRATION_THRESHOLD = 0.50  # default; overridden by analysis_plan


# =============================================================================
# Scoring logic (reuses Gate 2 evaluator approach)
# =============================================================================

def score_receipt(
    receipt: dict,
    observation: dict,
    evidence_object: dict | None,
    analysis_plan: dict,
    manifest: dict | None = None,
) -> dict:
    """Score a single receipt against a single observation.

    Args:
        receipt: prediction receipt (sealed)
        observation: external observation (sealed)
        evidence_object: structured evidence extracted from the frozen corpus
            (used for the information-content test). May be None if the
            problem has no associated evidence.
        analysis_plan: the pre-registered analysis plan
        manifest: the pre-registration manifest (for timestamp-constraint checks).
            If provided, the scorer REFUSES to score if timestamp constraints
            are violated.

    Returns:
        Score record (sealed).
    """
    # NEW (Forensic Gate): refuse evaluation if timestamp constraints violated
    if manifest is not None:
        from discovery_fabric.prospective.observation_window import verify_evaluation_timestamp_constraints
        ts_ok, ts_failures = verify_evaluation_timestamp_constraints(receipt, observation, manifest)
        if not ts_ok:
            score = {
                "schema_version": "1.0.0",
                "score_type": "DETERMINISTIC_REFUSED",
                "candidate_id": receipt.get("candidate_id"),
                "problem_id": receipt.get("problem_id"),
                "arm": receipt.get("arm"),
                "receipt_hash": receipt.get("receipt_hash"),
                "observation_hash": observation.get("observation_hash"),
                "manifest_hash": receipt.get("manifest_hash"),
                "final_classification": "EVALUATION_REFUSED",
                "DISCOVERY_PREDICTION_SCORE": 0.0,
                "information_content": {"classification": "EVALUATION_REFUSED",
                                        "information_content_score": None},
                "quantitative_accuracy": {"verdict": "EVALUATION_REFUSED",
                                          "calibration_error": None,
                                          "predicted": receipt.get("predicted_value"),
                                          "observed": observation.get("outcome_value"),
                                          "tolerance_bounds": None},
                "refusal_reasons": ts_failures,
                "scored_at": datetime.now(timezone.utc).isoformat(),
            }
            canonical = json.dumps(score, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            score["score_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
            return score

    cal_threshold = analysis_plan.get("calibration_threshold", STRICT_CALIBRATION_THRESHOLD)
    ic_threshold = analysis_plan.get("ic_threshold", 0.67)

    # Information-content test (if evidence object available)
    if evidence_object is not None:
        ic_result = classify_prediction(receipt, evidence_object)
        ic_class = ic_result["classification"]
        ic_score = ic_result["information_content_score"]
        # Treat PARTIALLY_NOVEL as RECONSTRUCTION (per Gate 2 protocol)
        if ic_class == "PARTIALLY_NOVEL":
            ic_class = "RECONSTRUCTION"
    else:
        ic_class = "NO_EVIDENCE_OBJECT"
        ic_score = 1.0
        ic_result = {"classification": ic_class, "information_content_score": ic_score,
                     "reason": "no evidence object available"}

    # Quantitative accuracy
    direction = (receipt.get("expected_direction") or "").upper()
    predicted = receipt.get("predicted_value")
    tl = receipt.get("tolerance_lower")
    tu = receipt.get("tolerance_upper")
    obs_val = observation.get("outcome_value")
    obs_dir = observation.get("outcome_direction")

    if not receipt.get("generation_success"):
        quant_verdict = "INDETERMINATE"
        cal_err = None
    elif direction == "BINARY":
        pred_str = str(predicted).upper()
        obs_str = str(obs_val).upper()
        if pred_str not in {"YES", "NO"} or obs_str not in {"YES", "NO"}:
            quant_verdict = "INDETERMINATE"
            cal_err = None
        elif pred_str == obs_str:
            quant_verdict = "CORRECT"
            cal_err = 0.0
        else:
            quant_verdict = "INCORRECT"
            cal_err = 1.0
    else:
        # Numeric
        if (not isinstance(predicted, (int, float))
            or not isinstance(obs_val, (int, float))
            or not isinstance(tl, (int, float))
            or not isinstance(tu, (int, float))):
            quant_verdict = "INDETERMINATE"
            cal_err = None
        else:
            low = predicted * tl
            high = predicted * tu
            in_range = low <= float(obs_val) <= high
            cal_err = abs(predicted - float(obs_val)) / max(abs(float(obs_val)), 1e-9)
            quant_verdict = "CORRECT" if (in_range and cal_err <= cal_threshold) else "INCORRECT"

    # Final classification (per Gate 2 protocol)
    if ic_class in ("RECONSTRUCTION", "PARTIALLY_NOVEL"):
        final = "RECONSTRUCTION"
    elif quant_verdict == "CORRECT":
        final = "CORRECT"
    elif quant_verdict == "INCORRECT":
        final = "INCORRECT"
    else:
        final = "INDETERMINATE"

    # DPS=1: GENUINE_NOVEL_PREDICTION AND CORRECT
    dps = 1.0 if (ic_class == "GENUINE_NOVEL_PREDICTION" and quant_verdict == "CORRECT") else 0.0

    score = {
        "schema_version": "1.0.0",
        "score_type": "DETERMINISTIC",
        "candidate_id": receipt.get("candidate_id"),
        "problem_id": receipt.get("problem_id"),
        "arm": receipt.get("arm"),
        "receipt_hash": receipt.get("receipt_hash"),
        "observation_hash": observation.get("observation_hash"),
        "manifest_hash": receipt.get("manifest_hash"),
        "final_classification": final,
        "DISCOVERY_PREDICTION_SCORE": dps,
        "information_content": {
            "classification": ic_class,
            "information_content_score": ic_score,
        },
        "quantitative_accuracy": {
            "verdict": quant_verdict,
            "calibration_error": round(cal_err, 4) if cal_err is not None else None,
            "predicted": predicted,
            "observed": obs_val,
            "tolerance_bounds": ([round(predicted * tl, 4), round(predicted * tu, 4)]
                                  if all(isinstance(x, (int, float)) for x in [predicted, tl, tu])
                                  else None),
        },
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }

    # Seal
    canonical = json.dumps(score, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    score["score_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return score


def score_all(
    receipts: list[dict],
    observations: list[dict],
    evidence_objects: dict[str, dict] | None,
    analysis_plan: dict,
    manifest: dict | None = None,
) -> list[dict]:
    """Score all receipts against their matching observations.

    Args:
        receipts: list of prediction receipts
        observations: list of observations (indexed by problem_id)
        evidence_objects: dict mapping problem_id -> structured evidence object
            (or None if no evidence available)
        analysis_plan: pre-registered analysis plan
        manifest: pre-registration manifest (for timestamp-constraint checks)

    Returns:
        List of sealed score records.
    """
    obs_by_problem = {o["problem_id"]: o for o in observations}
    scores = []
    for receipt in receipts:
        problem_id = receipt["problem_id"]
        obs = obs_by_problem.get(problem_id)
        if obs is None:
            # No observation for this problem — INDETERMINATE
            score = {
                "schema_version": "1.0.0",
                "score_type": "DETERMINISTIC",
                "candidate_id": receipt.get("candidate_id"),
                "problem_id": problem_id,
                "arm": receipt.get("arm"),
                "receipt_hash": receipt.get("receipt_hash"),
                "observation_hash": None,
                "manifest_hash": receipt.get("manifest_hash"),
                "final_classification": "INDETERMINATE",
                "DISCOVERY_PREDICTION_SCORE": 0.0,
                "information_content": {"classification": "NO_OBSERVATION",
                                        "information_content_score": None},
                "quantitative_accuracy": {"verdict": "INDETERMINATE",
                                          "calibration_error": None,
                                          "predicted": receipt.get("predicted_value"),
                                          "observed": None,
                                          "tolerance_bounds": None},
                "scored_at": datetime.now(timezone.utc).isoformat(),
            }
            canonical = json.dumps(score, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            score["score_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
            scores.append(score)
            continue

        ev_obj = None
        if evidence_objects is not None:
            ev_obj = evidence_objects.get(problem_id)
        score = score_receipt(receipt, obs, ev_obj, analysis_plan, manifest)
        scores.append(score)
    return scores


def save_scores(scores: list[dict]) -> Path:
    """Save all scores to a single file, append to log, and append each to
    the tamper-evident audit chain."""
    out_path = SCORES_DIR / "scores.json"
    with open(out_path, "w") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    # Append summary to log + audit chain
    from discovery_fabric.prospective.tamper_evident_chain import append_chain_entry
    for s in scores:
        entry = {
            "log_entry_type": "DETERMINISTIC_SCORE",
            "score_hash": s["score_hash"],
            "timestamp": s["scored_at"],
            "candidate_id": s["candidate_id"],
            "final_classification": s["final_classification"],
            "DPS": s["DISCOVERY_PREDICTION_SCORE"],
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # Append to tamper-evident audit chain
        append_chain_entry(
            entry_type="EVALUATION",
            payload_hash=s["score_hash"],
            metadata={
                "candidate_id": s["candidate_id"],
                "final_classification": s["final_classification"],
                "DPS": s["DISCOVERY_PREDICTION_SCORE"],
            },
        )
    return out_path


# =============================================================================
# Main — infrastructure check only
# =============================================================================

def main():
    """Verify the scorer infrastructure with synthetic data."""
    print("=" * 72)
    print("PROSPECTIVE EXPERIMENT — DETERMINISTIC SCORER INFRASTRUCTURE CHECK")
    print("=" * 72)
    print()

    # Synthetic receipt + observation
    receipt = {
        "candidate_id": "PROS-TEST-B_llm_only",
        "problem_id": "TEST",
        "arm": "B_llm_only",
        "receipt_hash": "dummy",
        "manifest_hash": "dummy_manifest",
        "predicted_value": 100,
        "tolerance_lower": 0.5,
        "tolerance_upper": 2.0,
        "expected_direction": "INCREASE",
        "generation_success": True,
        "hypothesis": "X will achieve higher Y than Z",
        "prediction": "X will reach 100 units",
        "units_range": "50 to 200",
    }
    observation = {
        "problem_id": "TEST",
        "observation_hash": "dummy_obs",
        "outcome_value": 110,
        "outcome_direction": "INCREASE",
        "measurement_date": "2027-06-01T00:00:00Z",
        "source_name": "synthetic_test",
    }
    analysis_plan = {
        "calibration_threshold": 0.50,
        "ic_threshold": 0.67,
    }

    score = score_receipt(receipt, observation, evidence_object=None, analysis_plan=analysis_plan)
    print(f"Synthetic score:")
    print(f"  candidate: {score['candidate_id']}")
    print(f"  final_classification: {score['final_classification']}")
    print(f"  DPS: {score['DISCOVERY_PREDICTION_SCORE']}")
    print(f"  quant_verdict: {score['quantitative_accuracy']['verdict']}")
    print(f"  cal_error: {score['quantitative_accuracy']['calibration_error']}")
    print(f"  score_hash: {score['score_hash'][:32]}...")

    print()
    print("Scorer infrastructure is in place. To run real scoring:")
    print("  1. Wait until ALL observations for the cohort are collected")
    print("  2. Extract structured evidence objects from the FROZEN corpus")
    print("  3. Call score_all(receipts, observations, evidence_objects, analysis_plan)")
    print("  4. Save scores and append to log")
    print()
    print("DO NOT score until the observation window has closed.")


if __name__ == "__main__":
    main()
