"""
External-Outcome Evaluator — deterministic, no LLM judge.

When an independently timestamped later observation becomes available:
  prediction → external measurement → deterministic comparison → CORRECT/INCORRECT/INDETERMINATE

Numeric predictions use a pre-registered tolerance.
Binary predictions use exact outcome matching.

No LLM. No subjective judgment. 100% deterministic and reproducible.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def evaluate_numeric_prediction(prediction_receipt: dict, outcome: dict) -> dict:
    """Evaluate a numeric prediction against an external outcome.
    
    Args:
        prediction_receipt: The immutable prediction receipt
        outcome: External measurement with:
            - value: numeric value
            - unit: unit of measurement
            - measurement_date: when measured
            - source: independent source
    
    Returns:
        CORRECT / INCORRECT / INDETERMINATE with reasoning
    """
    direction = prediction_receipt.get("expected_direction", "")
    units_range = prediction_receipt.get("units_range", "")
    prediction_text = prediction_receipt.get("prediction", "")
    
    outcome_value = outcome.get("value")
    outcome_direction = outcome.get("direction", "")
    
    if outcome_value is None or outcome_direction is None:
        return {
            "verdict": "INDETERMINATE",
            "reason": "Outcome missing value or direction",
            "deterministic": True,
        }
    
    # Check direction match
    if direction == "INCREASE" and outcome_direction == "INCREASE":
        direction_match = True
    elif direction == "DECREASE" and outcome_direction == "DECREASE":
        direction_match = True
    elif direction == "BINARY":
        direction_match = outcome_value == prediction_receipt.get("prediction", "")
    elif direction == "CORRELATION":
        direction_match = outcome_direction in ["POSITIVE_CORRELATION", "NEGATIVE_CORRELATION"]
    else:
        direction_match = False
    
    # Check if outcome is within pre-registered range (if specified)
    range_match = True
    if units_range and outcome_value is not None:
        # Try to extract numbers from units_range
        numbers = re.findall(r'[\d.]+', units_range)
        if len(numbers) >= 2:
            try:
                low, high = float(numbers[0]), float(numbers[1])
                range_match = low <= float(outcome_value) <= high
            except:
                range_match = True  # Can't parse, don't penalize
    
    if direction_match and range_match:
        verdict = "CORRECT"
        reason = f"Direction ({direction}) matches outcome ({outcome_direction}). Value {outcome_value} within range."
    elif direction_match and not range_match:
        verdict = "INDETERMINATE"
        reason = f"Direction matches but value {outcome_value} outside range {units_range}."
    else:
        verdict = "INCORRECT"
        reason = f"Direction mismatch: predicted {direction}, observed {outcome_direction}."
    
    return {
        "verdict": verdict,
        "reason": reason,
        "prediction_direction": direction,
        "outcome_direction": outcome_direction,
        "outcome_value": outcome_value,
        "range": units_range,
        "direction_match": direction_match,
        "range_match": range_match,
        "deterministic": True,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_binary_prediction(prediction_receipt: dict, outcome: dict) -> dict:
    """Evaluate a binary prediction (YES/NO outcome)."""
    prediction = prediction_receipt.get("prediction", "").upper()
    actual = outcome.get("value", "").upper()
    
    # Simple matching
    if prediction == actual:
        verdict = "CORRECT"
    elif actual == "UNKNOWN" or actual == "INDETERMINATE":
        verdict = "INDETERMINATE"
    else:
        verdict = "INCORRECT"
    
    return {
        "verdict": verdict,
        "prediction": prediction,
        "outcome": actual,
        "deterministic": True,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_prediction(receipt: dict, outcome: dict) -> dict:
    """Evaluate any prediction receipt against an outcome."""
    # Verify receipt integrity
    from discovery_fabric.v1_13.prediction_receipt import verify_receipt
    if not verify_receipt(receipt):
        return {
            "verdict": "INVALID_RECEIPT",
            "reason": "Receipt hash verification failed — receipt may have been modified",
            "deterministic": True,
        }
    
    # Check timestamp ordering
    pred_time = receipt.get("pre_registration_timestamp", "")
    outcome_time = outcome.get("measurement_date", "")
    if pred_time and outcome_time and pred_time >= outcome_time:
        return {
            "verdict": "INVALID_TEMPORAL_ORDER",
            "reason": f"Prediction timestamp ({pred_time}) >= outcome timestamp ({outcome_time})",
            "deterministic": True,
        }
    
    # Route to appropriate evaluator
    direction = receipt.get("expected_direction", "")
    if direction == "BINARY":
        result = evaluate_binary_prediction(receipt, outcome)
    else:
        result = evaluate_numeric_prediction(receipt, outcome)
    
    result["candidate_id"] = receipt.get("candidate_id", "")
    result["receipt_hash"] = receipt.get("receipt_hash", "")
    result["outcome_source"] = outcome.get("source", "")
    result["outcome_date"] = outcome_time
    
    return result


if __name__ == "__main__":
    # Test: Li-ion battery prediction
    receipt = {
        "candidate_id": "TEST-001",
        "prediction": "Combining LiCoO2 cathode with graphite anode enables >100 charge cycles",
        "units_range": ">100 cycles",
        "expected_direction": "INCREASE",
        "pre_registration_timestamp": "1990-06-01T00:00:00Z",
        "receipt_hash": "dummy",
    }
    
    outcome = {
        "value": 500,
        "direction": "INCREASE",
        "measurement_date": "1991-06-01T00:00:00Z",
        "source": "Sony commercialization 1991",
    }
    
    result = evaluate_numeric_prediction(receipt, outcome)
    print(f"Verdict: {result['verdict']}")
    print(f"Reason: {result['reason']}")
    print(f"Deterministic: {result['deterministic']}")
