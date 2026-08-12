"""
PSCD-1 Round Scorer — deterministic, no LLM judge.

Scores predictions against outcomes using ONLY preregistered rules.
Computes: true/foil confirmation rates, net discovery signal, per-arm breakdown.
"""
import json
from dataclasses import dataclass


@dataclass
class PredictionScore:
    prediction_id: str
    arm: str
    case_id: str
    retrieval_negative: bool
    non_entailed: bool
    later_confirmed: bool
    is_foil: bool
    primary_endpoint_hit: bool
    score_state: str  # CONFIRMED | PARTIALLY_CONFIRMED | NOT_CONFIRMED | UNKNOWN | INVALID


def score_prediction(prediction: dict, outcome: dict) -> PredictionScore:
    """Score a single prediction against its outcome. Deterministic."""
    att = prediction.get("retrieval_negative_attestation", {})

    retrieval_negative = att.get("is_retrieval_negative", False)
    non_entailed = att.get("entailment_check_result") == "NOT_ENTAILED"
    later_confirmed = outcome.get("confirmed", False)
    is_foil = outcome.get("is_foil", False)

    # Primary endpoint: retrieval_negative + non_entailed + later_confirmed
    primary_endpoint_hit = retrieval_negative and non_entailed and later_confirmed

    # Score state
    if later_confirmed and retrieval_negative and non_entailed:
        score_state = "CONFIRMED"
    elif later_confirmed and (retrieval_negative or non_entailed):
        score_state = "PARTIALLY_CONFIRMED"
    elif not later_confirmed:
        score_state = "NOT_CONFIRMED"
    elif att.get("entailment_check_result") == "UNKNOWN":
        score_state = "UNKNOWN"  # NEVER convert UNKNOWN to CONFIRMED
    else:
        score_state = "INVALID"

    return PredictionScore(
        prediction_id=prediction.get("prediction_id", ""),
        arm=prediction.get("arm", ""),
        case_id=prediction.get("case_id", ""),
        retrieval_negative=retrieval_negative,
        non_entailed=non_entailed,
        later_confirmed=later_confirmed,
        is_foil=is_foil,
        primary_endpoint_hit=primary_endpoint_hit,
        score_state=score_state,
    )


def score_round(predictions: list[dict], outcomes: list[dict]) -> dict:
    """Score all predictions against outcomes. Returns per-arm + aggregate metrics."""
    # Match predictions to outcomes
    outcome_by_pred = {o.get("prediction_id", ""): o for o in outcomes}

    scores = []
    for pred in predictions:
        outcome = outcome_by_pred.get(pred.get("prediction_id", ""), {})
        if not outcome:
            scores.append({
                "prediction_id": pred.get("prediction_id", ""),
                "arm": pred.get("arm", ""),
                "score_state": "INVALID",
                "primary_endpoint_hit": False,
                "is_foil": False,
            })
        else:
            ps = score_prediction(pred, outcome)
            scores.append({
                "prediction_id": ps.prediction_id,
                "arm": ps.arm,
                "case_id": ps.case_id,
                "retrieval_negative": ps.retrieval_negative,
                "non_entailed": ps.non_entailed,
                "later_confirmed": ps.later_confirmed,
                "is_foil": ps.is_foil,
                "primary_endpoint_hit": ps.primary_endpoint_hit,
                "score_state": ps.score_state,
            })

    # Per-arm analysis
    arms = {}
    for s in scores:
        arm = s["arm"]
        if arm not in arms:
            arms[arm] = {"n": 0, "true_confirmed": 0, "foil_confirmed": 0,
                        "retrieval_negative": 0, "non_entailed": 0}
        arms[arm]["n"] += 1
        if s["primary_endpoint_hit"] and not s["is_foil"]:
            arms[arm]["true_confirmed"] += 1
        if s["primary_endpoint_hit"] and s["is_foil"]:
            arms[arm]["foil_confirmed"] += 1
        if s.get("retrieval_negative"):
            arms[arm]["retrieval_negative"] += 1
        if s.get("non_entailed"):
            arms[arm]["non_entailed"] += 1

    for arm, m in arms.items():
        m["true_confirmation_rate"] = m["true_confirmed"] / max(m["n"], 1)
        m["foil_confirmation_rate"] = m["foil_confirmed"] / max(m["n"], 1)
        m["net_discovery_rate"] = m["true_confirmation_rate"] - m["foil_confirmation_rate"]

    return {"scores": scores, "per_arm": arms}
