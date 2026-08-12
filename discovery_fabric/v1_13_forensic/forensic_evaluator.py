"""
V1.13 FORENSIC CORRECTION EVALUATOR
====================================

Purpose:
    Re-evaluate the FROZEN V1.13 prediction receipts under stricter, forensically
    corrected criteria. The original V1.13 results (results.json) are preserved
    unchanged. This evaluator produces a separate v1_13_forensic/results.json.

    The original V1.13 scoring was too lenient:
      - A prediction was CORRECT if direction matched AND value fell in a broad
        range (e.g., ">50 cycles" matched against the observed 500 → CORRECT).
      - "Novelty" was a 60% term-overlap heuristic — too weak to detect that a
        hypothesis was merely a restatement of the evidence.

Forensic corrections applied (per directive 2026-08-12):

  1. FIELD RENAMES
       pre_registration_timestamp -> simulation_registration_date
       Add: evaluation_type = "HISTORICAL_RETROSPECTIVE_BACKTEST"
     Rationale: this is a backtest simulated AS OF the cutoff date, not a real
     pre-registration. Naming must not overclaim pre-registration status.

  2. FOUR SEPARATED DIMENSIONS (no longer collapsed into one verdict)
       (a) directional_correctness      : CORRECT / INCORRECT / NA
       (b) quantitative_accuracy         : WITHIN_TOLERANCE / OUT_OF_TOLERANCE /
                                            NON_NUMERIC / NO_PREDICTION /
                                            INDETERMINATE  + calibration_error
       (c) falsifiability                : FALSIFIABLE / NOT_FALSIFIABLE
       (d) prediction_specificity        : SPECIFIC / VAGUE

  3. STRICTER CORRECTNESS
       A prediction is no longer CORRECT just because its broad range contains
       the historical result. We require:
         - direction match AND
         - a pre-specified quantitative tolerance/range AND
         - observed value within that tolerance AND
         - calibration_error <= STRICT_CALIBRATION_THRESHOLD (default 0.50)
       BINARY predictions require exact YES/NO match.
       The original broad-range match is preserved as a SEPARATE field
       (legacy_broad_range_match) for transparency, but does NOT drive the
       forensic verdict.

  4. INFORMATION-CONTENT TEST
       Determine whether the proposed relationship is already LOGICALLY IMPLIED
       by the supplied evidence. If yes -> RECONSTRUCTION, not DISCOVERY.
       Two sub-checks (both deterministic, no LLM):
         (a) is_explicit_in_evidence: key noun-phrases + relational verb of the
             hypothesis appear together in the evidence (near-verbatim).
         (b) is_trivially_entailed_by_evidence: the prediction introduces no new
             entity AND no new mechanism AND no new relational structure beyond
             what the evidence already states.
       Classification:
         RECONSTRUCTION   if (a) OR (b) is True
         DISCOVERY_CANDIDATE otherwise

  5. DISCOVERY_PREDICTION_SCORE (binary, all-or-nothing)
       A receipt scores DISCOVERY_PREDICTION_SCORE = 1.0 ONLY if ALL of:
         - not_explicit_in_evidence        = True
         - not_trivially_entailed_by_evidence = True
         - falsifiable                     = True
         - quantitatively_specific         = True
         - later_independently_observed    = True
           (which itself requires directional_correctness=CORRECT AND
            quantitative_accuracy=WITHIN_TOLERANCE under the stricter rule)
       Otherwise 0.0.

  6. NO NEW MODULES
       No temporal-reasoning module. No negative-knowledge module. No patent
       expansion. No new discovery architecture. This evaluator only re-scores
       existing receipts.

This evaluator is 100% deterministic and reproducible. No LLM judge.
"""
from __future__ import annotations

import json
import re
import hashlib
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
V1_13_DIR = REPO / "discovery_fabric" / "v1_13"
FORENSIC_DIR = REPO / "discovery_fabric" / "v1_13_forensic"
RECEIPTS_DIR = V1_13_DIR / "receipts"
BENCHMARK = V1_13_DIR / "benchmark_dataset.json"
RESULTS_OUT = FORENSIC_DIR / "results.json"
REPORT_OUT = FORENSIC_DIR / "V1_13_FORENSIC_CORRECTION_REPORT.md"

# Re-validate receipts from the original V1.13 prediction_receipt module.
import sys
sys.path.insert(0, str(REPO))
from discovery_fabric.v1_13.prediction_receipt import verify_receipt  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EVALUATION_TYPE = "HISTORICAL_RETROSPECTIVE_BACKTEST"
STRICT_CALIBRATION_THRESHOLD = 0.50  # |pred - obs| / |obs| <= 0.50 to be "within tolerance"
FALSIFIER_MIN_LEN = 20               # falsification_condition must be substantive
SPECIFICITY_MIN_NUMERIC_BOUNDS = 2   # need >=2 numeric bounds (low, high) for SPECIFIC

# A pre-specified tolerance must be tight enough to be falsifiable in practice.
# A "range" like [1, 1000] spanning three orders of magnitude is degenerate —
# it would be "satisfied" by almost any outcome and is therefore not a real
# quantitative prediction. We enforce:
#   - For percentage-like ranges (0 <= low < high <= 100): high/low <= 5
#     (e.g., 15-30% passes; 1-100% fails)
#   - For absolute ranges (low > 0): high/low <= 10
#     (e.g., 500-1000 cycles passes; 1-1000 fails)
#   - For ranges with low == 0: (high - low) / max(high, 1e-9) <= 0.9
#     (e.g., 0-10 passes; 0-1000 fails)
RANGE_SPREAD_MAX_PCT = 5.0      # high/low <= 5 for percentage ranges
RANGE_SPREAD_MAX_ABS = 10.0     # high/low <= 10 for absolute ranges
RANGE_FRACTIONAL_MAX_ZERO_LOW = 0.9  # (high-low)/high <= 0.9 when low == 0

STOPWORDS = {
    "the", "that", "this", "with", "from", "have", "been", "would", "could",
    "should", "which", "their", "there", "these", "those", "what", "when",
    "where", "while", "about", "into", "upon", "will", "shall", "may",
    "might", "must", "can", "also", "such", "same", "more", "most", "some",
    "than", "then", "they", "them", "these", "those", "very", "much", "many",
    "both", "either", "neither", "each", "every", "any", "all", "none",
    "above", "below", "between", "through", "during", "before", "after",
    "since", "until", "without", "within", "across", "along", "among",
    "behind", "beyond", "around", "against", "toward", "towards",
    "because", "although", "though", "unless", "whether", "however",
    "therefore", "thus", "hence", "moreover", "nevertheless", "nonetheless",
    "accordingly", "consequently", "furthermore", "meanwhile", "besides",
    "indeed", "instead", "otherwise", "rather", "yet", "and", "but", "or",
    "not", "no", "yes", "only", "just", "even", "still", "already",
    "using", "used", "use", "uses", "via", "per", "etc",
}

# Relational verbs that, if present in BOTH evidence and hypothesis at the
# same subject-object slot, strongly suggest the relationship is explicit.
RELATIONAL_VERBS = {
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had",
    "does", "do", "did",
    "can", "could", "will", "would",
    "shows", "show", "showed", "shown",
    "demonstrates", "demonstrate", "demonstrated",
    "enables", "enable", "enabled",
    "produces", "produce", "produced",
    "contains", "contain", "contained",
    "involves", "involve", "involved",
    "exhibits", "exhibit", "exhibited",
    "achieves", "achieve", "achieved",
    "allows", "allow", "allowed",
    "supports", "support", "supported",
    "requires", "require", "required",
    "causes", "cause", "caused",
    "increases", "increase", "increased",
    "decreases", "decrease", "decreased",
    "reduces", "reduce", "reduced",
    "improves", "improve", "improved",
    "prevents", "prevent", "prevented",
    "triggers", "trigger", "triggered",
    "induces", "induce", "induced",
    "suppresses", "suppress", "suppressed",
    "blocks", "block", "blocked",
    "intercalates", "intercalate",
    "reversibly", "reversible", "reversibility",
}


# ---------------------------------------------------------------------------
# Helpers — text analysis
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z][a-z0-9_-]{2,}\b", (text or "").lower())


def _content_terms(text: str) -> set[str]:
    return set(_tokenize(text)) - STOPWORDS


def _entities(text: str) -> set[str]:
    """Capitalized terms + multi-word technical nouns (heuristic)."""
    text = text or ""
    caps = set(re.findall(r"\b([A-Z][a-zA-Z0-9]{2,})\b", text))
    # Filter sentence-initial common words heuristically by length >=4
    caps = {c for c in caps if len(c) >= 4}
    # Lowercase content terms that look like technical nouns (>=5 chars)
    technical = {t for t in _content_terms(text) if len(t) >= 5}
    return caps | technical


def _numeric_bounds(text: str) -> tuple[float, float] | None:
    """Extract a (low, high) numeric range from a string like '>50', '10-30', '>= 100'."""
    text = text or ""
    # Range form: "10-30" or "10 to 30"
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|\u2013)\s*(-?\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    # Lower-bound form: ">50", ">= 50", "greater than 50", "above 50"
    m = re.search(r"(?:>=?|greater than|above|more than|at least)\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        v = float(m.group(1))
        return v, math.inf
    # Upper-bound form: "<50", "<= 50", "less than 50", "below 50"
    m = re.search(r"(?:<=?|less than|below|under|at most)\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        v = float(m.group(1))
        return -math.inf, v
    # Point estimate
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    if len(nums) == 1:
        v = float(nums[0])
        return v, v
    return None


# ---------------------------------------------------------------------------
# Dimension (a) — Directional correctness
# ---------------------------------------------------------------------------

def score_directional_correctness(receipt: dict, outcome: dict) -> dict:
    pred_dir = (receipt.get("expected_direction") or "").upper()
    obs_dir = (outcome.get("direction") or "").upper()
    obs_val = outcome.get("value")

    if pred_dir == "BINARY":
        # For binary predictions, direction is the predicted YES/NO itself
        pred_text = (receipt.get("prediction") or "").upper()
        if obs_val is None:
            verdict = "NA"
            reason = "no outcome value"
        elif str(obs_val).upper() in ("YES", "NO"):
            # Check whether the prediction asserts YES or NO
            yes_asserted = bool(re.search(r"\b(yes|will|achieves|succeeds?|positive|enable[sd]?)\b", pred_text, re.I))
            no_asserted = bool(re.search(r"\b(no|not|fail|negative|cannot|does not)\b", pred_text, re.I))
            obs_yes = str(obs_val).upper() == "YES"
            if obs_yes and yes_asserted and not no_asserted:
                verdict = "CORRECT"
            elif (not obs_yes) and no_asserted and not yes_asserted:
                verdict = "CORRECT"
            elif yes_asserted == obs_yes:
                verdict = "CORRECT"
            else:
                verdict = "INCORRECT"
            reason = f"predicted_binary={'YES' if yes_asserted else 'NO' if no_asserted else 'AMBIGUOUS'} observed={obs_val}"
        else:
            verdict = "NA"
            reason = f"non-binary outcome value: {obs_val}"
        return {"verdict": verdict, "reason": reason, "predicted_direction": pred_dir,
                "observed_direction": obs_dir}

    # INCREASE / DECREASE / CORRELATION
    if pred_dir == obs_dir:
        return {"verdict": "CORRECT", "reason": f"direction match: {pred_dir}",
                "predicted_direction": pred_dir, "observed_direction": obs_dir}
    if pred_dir and obs_dir:
        return {"verdict": "INCORRECT",
                "reason": f"direction mismatch: predicted {pred_dir} observed {obs_dir}",
                "predicted_direction": pred_dir, "observed_direction": obs_dir}
    return {"verdict": "NA", "reason": "missing direction",
            "predicted_direction": pred_dir, "observed_direction": obs_dir}


# ---------------------------------------------------------------------------
# Dimension (b) — Quantitative accuracy (stricter than broad-range)
# ---------------------------------------------------------------------------

def score_quantitative_accuracy(receipt: dict, outcome: dict) -> dict:
    units_range = receipt.get("units_range") or ""
    obs_val = outcome.get("value")
    direction = (receipt.get("expected_direction") or "").upper()

    # BINARY predictions: quantitative accuracy reduces to YES/NO exact match
    if direction == "BINARY":
        if obs_val is None:
            return {"verdict": "NO_PREDICTION", "calibration_error": None,
                    "pre_specified_tolerance": None, "observed_value": None}
        pred_text = (receipt.get("prediction") or "").upper()
        yes_asserted = bool(re.search(r"\b(yes|will|achieves?|succeeds?|positive|enable[sd]?)\b", pred_text, re.I))
        no_asserted = bool(re.search(r"\b(no|not|fail|negative|cannot|does not)\b", pred_text, re.I))
        pred_yes = yes_asserted and not no_asserted
        obs_yes = str(obs_val).upper() == "YES"
        if pred_yes == obs_yes:
            return {"verdict": "WITHIN_TOLERANCE", "calibration_error": 0.0,
                    "pre_specified_tolerance": "BINARY exact match",
                    "observed_value": obs_val}
        return {"verdict": "OUT_OF_TOLERANCE", "calibration_error": 1.0,
                "pre_specified_tolerance": "BINARY exact match",
                "observed_value": obs_val}

    # Numeric predictions
    bounds = _numeric_bounds(units_range)
    if bounds is None:
        # No numeric range anywhere in units_range -> prediction is non-specific
        return {"verdict": "NON_NUMERIC", "calibration_error": None,
                "pre_specified_tolerance": None, "observed_value": obs_val}

    low, high = bounds
    if obs_val is None or not isinstance(obs_val, (int, float)):
        return {"verdict": "INDETERMINATE", "calibration_error": None,
                "pre_specified_tolerance": [low, high],
                "observed_value": obs_val}

    obs = float(obs_val)
    in_range = (low <= obs <= high)

    # Calibration error: relative distance from nearest bound (or 0 if inside)
    if in_range:
        cal_err = 0.0
    else:
        # Distance from nearest bound, normalized by |obs|
        if obs < low:
            dist = low - obs
        else:
            dist = obs - high
        cal_err = dist / max(abs(obs), 1e-9)

    verdict = "WITHIN_TOLERANCE" if (in_range and cal_err <= STRICT_CALIBRATION_THRESHOLD) else "OUT_OF_TOLERANCE"
    return {"verdict": verdict,
            "calibration_error": round(cal_err, 4),
            "pre_specified_tolerance": [low, high],
            "observed_value": obs,
            "strict_calibration_threshold": STRICT_CALIBRATION_THRESHOLD}


# ---------------------------------------------------------------------------
# Dimension (c) — Falsifiability
# ---------------------------------------------------------------------------

def score_falsifiability(receipt: dict) -> dict:
    falsifier = (receipt.get("falsification_condition") or "").strip()
    if len(falsifier) < FALSIFIER_MIN_LEN:
        return {"verdict": "NOT_FALSIFIABLE",
                "reason": f"falsification_condition too short ({len(falsifier)} chars)"}
    # Must contain a specific outcome language (numeric bound, comparison, or
    # explicit negation like "if X then falsified")
    has_comparison = bool(re.search(r"(>=?|<=?|less than|more than|above|below|under|over|>|<)", falsifier, re.I))
    has_negation = bool(re.search(r"\b(not|no|fail|fals|negative|absence|cannot|does not|disprove)\b", falsifier, re.I))
    has_numeric = bool(re.search(r"\d+", falsifier))
    if has_comparison or has_negation or has_numeric:
        return {"verdict": "FALSIFIABLE", "reason": "falsification_condition specifies a testable outcome"}
    return {"verdict": "NOT_FALSIFIABLE",
            "reason": "falsification_condition lacks specific testable outcome"}


# ---------------------------------------------------------------------------
# Dimension (d) — Prediction specificity (pre-specified quantitative tolerance)
# ---------------------------------------------------------------------------

def score_prediction_specificity(receipt: dict) -> dict:
    units_range = receipt.get("units_range") or ""
    direction = (receipt.get("expected_direction") or "").upper()
    measurement = (receipt.get("measurement_method") or "").strip()

    if direction == "BINARY":
        # Binary predictions are "specific" if the prediction asserts a clear
        # YES/NO and the measurement method is described.
        if len(measurement) >= 10:
            return {"verdict": "SPECIFIC", "reason": "binary prediction with measurement method"}
        return {"verdict": "VAGUE", "reason": "binary prediction without measurement method"}

    bounds = _numeric_bounds(units_range)
    if bounds is None:
        return {"verdict": "VAGUE", "reason": "no numeric range pre-specified"}
    low, high = bounds
    if math.isinf(low) and math.isinf(high):
        return {"verdict": "VAGUE", "reason": "no numeric range pre-specified"}
    if math.isinf(low) or math.isinf(high):
        # One-sided bound (e.g., ">50"). Counts as SPECIFIC only if the bound
        # is finite — a one-sided open range is a directional claim, not a
        # quantitative tolerance.
        return {"verdict": "VAGUE",
                "reason": "one-sided bound only — directional, not quantitative tolerance"}

    # Two finite bounds = pre-specified quantitative tolerance — but enforce
    # range-spread to reject degenerate ranges like [1, 1000] that would be
    # satisfied by almost any outcome.
    is_percentage = (0 <= low < high <= 100) and ("%" in units_range or "percent" in units_range.lower())
    if low == 0:
        spread_ratio = (high - low) / max(high, 1e-9)
        spread_ok = spread_ratio <= RANGE_FRACTIONAL_MAX_ZERO_LOW
        spread_reason = f"zero-low range fractional spread = {spread_ratio:.2f} (max {RANGE_FRACTIONAL_MAX_ZERO_LOW})"
    elif is_percentage:
        spread_ratio = high / max(low, 1e-9)
        spread_ok = spread_ratio <= RANGE_SPREAD_MAX_PCT
        spread_reason = f"percentage range high/low = {spread_ratio:.2f} (max {RANGE_SPREAD_MAX_PCT})"
    else:
        spread_ratio = high / max(low, 1e-9)
        spread_ok = spread_ratio <= RANGE_SPREAD_MAX_ABS
        spread_reason = f"absolute range high/low = {spread_ratio:.2f} (max {RANGE_SPREAD_MAX_ABS})"

    if not spread_ok:
        return {"verdict": "VAGUE",
                "reason": f"degenerate range [{low}, {high}] — {spread_reason}"}

    return {"verdict": "SPECIFIC",
            "reason": f"pre-specified tolerance [{low}, {high}] — {spread_reason}"}


# ---------------------------------------------------------------------------
# Information-content test — DISCOVERY vs RECONSTRUCTION
# ---------------------------------------------------------------------------

def information_content_test(receipt: dict, evidence: str) -> dict:
    """Determine whether the proposed relationship is already logically
    implied by the supplied evidence.

    Two sub-checks:
      (a) is_explicit_in_evidence: key noun-phrases + relational verb of the
          hypothesis appear together in the evidence (near-verbatim).
      (b) is_trivially_entailed_by_evidence: the prediction introduces no new
          entity AND no new relational structure beyond the evidence.

    Classification:
      RECONSTRUCTION       if (a) OR (b) is True
      DISCOVERY_CANDIDATE  otherwise
    """
    hypothesis = receipt.get("hypothesis") or ""
    prediction = receipt.get("prediction") or ""
    proposed = f"{hypothesis} {prediction}"
    evidence = evidence or ""
    ev_lower = evidence.lower()
    prop_lower = proposed.lower()

    # ---- (a) is_explicit_in_evidence ----
    prop_entities = _entities(proposed)
    ev_entities = _entities(evidence)
    # Capitalized entities (proper nouns, chemicals, model names) carry more weight
    prop_caps = {e for e in prop_entities if e and e[0].isupper()}
    ev_caps = {e for e in ev_entities if e and e[0].isupper()}
    new_caps = prop_caps - ev_caps  # entities proposed but NOT in evidence
    new_technical = (prop_entities - ev_entities) - prop_caps  # new technical nouns

    # Hypothesis verb
    prop_verbs = set(_tokenize(prop_lower)) & RELATIONAL_VERBS
    ev_verbs = set(_tokenize(ev_lower)) & RELATIONAL_VERBS
    shared_verbs = prop_verbs & ev_verbs

    # If hypothesis is essentially a noun-phrase reordering of entities
    # already in evidence AND shares a relational verb, classify explicit.
    prop_terms = _content_terms(prop_lower)
    ev_terms = _content_terms(ev_lower)
    if prop_terms:
        term_overlap_ratio = len(prop_terms & ev_terms) / len(prop_terms)
    else:
        term_overlap_ratio = 0.0

    # Stricter than V1.13's 0.6 threshold: require BOTH (i) high term overlap
    # AND (ii) no new proper-noun entity AND (iii) at least one shared
    # relational verb.
    is_explicit = (
        term_overlap_ratio >= 0.70
        and len(new_caps) == 0
        and len(shared_verbs) >= 1
    )

    # ---- (b) is_trivially_entailed_by_evidence ----
    # The prediction introduces no NEW entity AND no NEW mechanism beyond
    # what the evidence already states. We use a relaxed notion of "entity"
    # here (all content terms >=5 chars) to catch synonyms.
    new_entities_combined = (prop_entities - ev_entities)
    # Filter out generic terms
    generic = {"prediction", "hypothesis", "evidence", "outcome", "result",
               "method", "value", "data", "system", "approach", "study",
               "research", "analysis", "test", "experiment", "measurement"}
    new_entities_combined -= generic

    is_trivially_entailed = (
        len(new_caps) == 0
        and len(new_entities_combined) <= 2  # allow at most 2 minor new terms
        and term_overlap_ratio >= 0.55
    )

    classification = "RECONSTRUCTION" if (is_explicit or is_trivially_entailed) else "DISCOVERY_CANDIDATE"

    return {
        "classification": classification,
        "is_explicit_in_evidence": is_explicit,
        "is_trivially_entailed_by_evidence": is_trivially_entailed,
        "term_overlap_ratio": round(term_overlap_ratio, 4),
        "new_proper_nouns_in_proposal": sorted(new_caps),
        "new_technical_terms_in_proposal": sorted(list(new_entities_combined - new_caps))[:10],
        "shared_relational_verbs": sorted(shared_verbs),
    }


# ---------------------------------------------------------------------------
# DISCOVERY_PREDICTION_SCORE (all-or-nothing)
# ---------------------------------------------------------------------------

def score_discovery_prediction(receipt: dict, outcome: dict, evidence: str) -> dict:
    info = information_content_test(receipt, evidence)
    dir_score = score_directional_correctness(receipt, outcome)
    quant_score = score_quantitative_accuracy(receipt, outcome)
    fals_score = score_falsifiability(receipt)
    spec_score = score_prediction_specificity(receipt)

    not_explicit = not info["is_explicit_in_evidence"]
    not_trivially_entailed = not info["is_trivially_entailed_by_evidence"]
    falsifiable = fals_score["verdict"] == "FALSIFIABLE"
    quant_specific = spec_score["verdict"] == "SPECIFIC"
    later_observed = (
        dir_score["verdict"] == "CORRECT"
        and quant_score["verdict"] == "WITHIN_TOLERANCE"
    )

    all_pass = all([not_explicit, not_trivially_entailed, falsifiable,
                    quant_specific, later_observed])

    return {
        "DISCOVERY_PREDICTION_SCORE": 1.0 if all_pass else 0.0,
        "criteria": {
            "not_explicit_in_evidence": not_explicit,
            "not_trivially_entailed_by_evidence": not_trivially_entailed,
            "falsifiable": falsifiable,
            "quantitatively_specific": quant_specific,
            "later_independently_observed": later_observed,
        },
        "all_pass": all_pass,
        "information_content": info,
        "directional_correctness": dir_score,
        "quantitative_accuracy": quant_score,
        "falsifiability": fals_score,
        "prediction_specificity": spec_score,
    }


# ---------------------------------------------------------------------------
# Forensic re-evaluation over all receipts
# ---------------------------------------------------------------------------

def load_benchmark() -> dict[str, dict]:
    with open(BENCHMARK) as f:
        cases = json.load(f)
    return {c["id"]: c for c in cases}


def forensic_field_renames(receipt: dict) -> dict:
    """Apply directive 1: rename pre_registration_timestamp ->
    simulation_registration_date; add evaluation_type."""
    r = dict(receipt)  # shallow copy
    if "pre_registration_timestamp" in r:
        r["simulation_registration_date"] = r.pop("pre_registration_timestamp")
    r["evaluation_type"] = EVALUATION_TYPE
    return r


def evaluate_all() -> dict:
    benchmark = load_benchmark()
    receipts = sorted(RECEIPTS_DIR.glob("PRED-*.json"))

    results = []
    for receipt_path in receipts:
        with open(receipt_path) as f:
            original_receipt = json.load(f)

        # Verify receipt integrity (immutable hash)
        integrity_ok = verify_receipt(original_receipt)

        # Apply forensic field renames (does NOT modify the original file)
        receipt = forensic_field_renames(original_receipt)

        # Parse case_id and config from candidate_id: "PRED-PB-001-B_llm_only"
        cid = receipt.get("candidate_id", "")
        m = re.match(r"PRED-(PB-\d+)-(\w+)", cid)
        if not m:
            continue
        case_id, config = m.group(1), m.group(2)
        case = benchmark.get(case_id)
        if not case:
            continue

        evidence = case.get("pre_outcome_evidence", "")
        outcome = case.get("outcome", {})

        discovery = score_discovery_prediction(receipt, outcome, evidence)

        # Also compute the legacy "broad range match" for transparency
        # (this is what the original V1.13 used to declare CORRECT).
        legacy_broad_range_match = _legacy_broad_range_match(receipt, outcome)

        results.append({
            "key": f"{case_id}|{config}",
            "case_id": case_id,
            "case_name": case.get("name", ""),
            "config": config,
            "candidate_id": cid,
            "receipt_integrity_ok": integrity_ok,
            "simulation_registration_date": receipt.get("simulation_registration_date"),
            "evaluation_type": receipt.get("evaluation_type"),
            "hypothesis": receipt.get("hypothesis", "")[:300],
            "prediction": receipt.get("prediction", "")[:300],
            "units_range": receipt.get("units_range", ""),
            "expected_direction": receipt.get("expected_direction", ""),
            "outcome_source": outcome.get("source", ""),
            "outcome_value": outcome.get("value"),
            "outcome_direction": outcome.get("direction", ""),
            "outcome_measurement_date": outcome.get("measurement_date"),
            "DISCOVERY_PREDICTION_SCORE": discovery["DISCOVERY_PREDICTION_SCORE"],
            "criteria": discovery["criteria"],
            "all_pass": discovery["all_pass"],
            "information_content": discovery["information_content"],
            "directional_correctness": discovery["directional_correctness"],
            "quantitative_accuracy": discovery["quantitative_accuracy"],
            "falsifiability": discovery["falsifiability"],
            "prediction_specificity": discovery["prediction_specificity"],
            "legacy_broad_range_match": legacy_broad_range_match,
            "receipt_hash": receipt.get("receipt_hash", ""),
        })

    # ---- Summary by config ----
    configs = sorted({r["config"] for r in results})
    summary = {}
    for cfg in configs:
        cfg_results = [r for r in results if r["config"] == cfg]
        n = len(cfg_results)
        summary[cfg] = {
            "n": n,
            "discovery_score_1": sum(1 for r in cfg_results if r["DISCOVERY_PREDICTION_SCORE"] == 1.0),
            "discovery_score_1_pct": round(100 * sum(1 for r in cfg_results if r["DISCOVERY_PREDICTION_SCORE"] == 1.0) / max(n, 1), 1),
            "directional_correct": sum(1 for r in cfg_results if r["directional_correctness"]["verdict"] == "CORRECT"),
            "quantitative_within_tolerance": sum(1 for r in cfg_results if r["quantitative_accuracy"]["verdict"] == "WITHIN_TOLERANCE"),
            "falsifiable": sum(1 for r in cfg_results if r["falsifiability"]["verdict"] == "FALSIFIABLE"),
            "quantitatively_specific": sum(1 for r in cfg_results if r["prediction_specificity"]["verdict"] == "SPECIFIC"),
            "reconstruction": sum(1 for r in cfg_results if r["information_content"]["classification"] == "RECONSTRUCTION"),
            "discovery_candidate": sum(1 for r in cfg_results if r["information_content"]["classification"] == "DISCOVERY_CANDIDATE"),
            "legacy_broad_range_correct": sum(1 for r in cfg_results if r["legacy_broad_range_match"]),
            "legacy_broad_range_correct_pct": round(100 * sum(1 for r in cfg_results if r["legacy_broad_range_match"]) / max(n, 1), 1),
        }

    # ---- Per-criterion pass rate across all configs ----
    criterion_pass = {}
    for crit in ["not_explicit_in_evidence", "not_trivially_entailed_by_evidence",
                 "falsifiable", "quantitatively_specific", "later_independently_observed"]:
        criterion_pass[crit] = sum(1 for r in results if r["criteria"].get(crit))

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": EVALUATION_TYPE,
        "benchmark": "V1.13_PREDICTION_FORENSIC_CORRECTION",
        "scoring": "DETERMINISTIC (no LLM judge) — forensic re-evaluation of frozen V1.13 receipts",
        "strict_calibration_threshold": STRICT_CALIBRATION_THRESHOLD,
        "total_cases": len(benchmark),
        "total_receipts": len(results),
        "configs": configs,
        "criterion_pass_count_across_all_receipts": criterion_pass,
        "summary_by_config": summary,
        "results": results,
    }
    return report


def _legacy_broad_range_match(receipt: dict, outcome: dict) -> bool:
    """Replicate the original V1.13 lenient rule: CORRECT if direction matches
    AND (no range parsable OR value within broad range)."""
    direction = (receipt.get("expected_direction") or "").upper()
    obs_dir = (outcome.get("direction") or "").upper()
    obs_val = outcome.get("value")
    units_range = receipt.get("units_range") or ""

    if direction == "BINARY":
        pred_text = (receipt.get("prediction") or "").upper()
        yes_asserted = bool(re.search(r"\b(yes|will|achieves?|succeeds?|positive|enable[sd]?)\b", pred_text, re.I))
        no_asserted = bool(re.search(r"\b(no|not|fail|negative|cannot|does not)\b", pred_text, re.I))
        obs_yes = str(obs_val).upper() == "YES"
        pred_yes = yes_asserted and not no_asserted
        return pred_yes == obs_yes

    if direction != obs_dir:
        return False
    if obs_val is None or not isinstance(obs_val, (int, float)):
        return False
    bounds = _numeric_bounds(units_range)
    if bounds is None:
        return True  # original code: "Can't parse, don't penalize"
    low, high = bounds
    return low <= float(obs_val) <= high


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    FORENSIC_DIR.mkdir(parents=True, exist_ok=True)
    report = evaluate_all()

    with open(RESULTS_OUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    h = hashlib.sha256(RESULTS_OUT.read_bytes()).hexdigest()
    print(f"=" * 72)
    print(f"V1.13 FORENSIC CORRECTION — RE-EVALUATION COMPLETE")
    print(f"=" * 72)
    print(f"Receipts re-evaluated: {report['total_receipts']}")
    print(f"Strict calibration threshold: {report['strict_calibration_threshold']}")
    print(f"Results: {RESULTS_OUT}")
    print(f"Hash: {h[:32]}...")
    print()
    print(f"PER-CRITERION PASS COUNT (out of {report['total_receipts']} receipts):")
    for crit, cnt in report["criterion_pass_count_across_all_receipts"].items():
        print(f"  {crit:42s}: {cnt:3d}  ({100*cnt/report['total_receipts']:.1f}%)")
    print()
    print(f"SUMMARY BY CONFIG (forensic, stricter):")
    print(f"  {'config':<14} {'n':>3} {'DPS=1':>6} {'DPS%':>6} {'dir':>4} {'quant':>6} {'fals':>5} {'spec':>5} {'recon':>6} {'disc':>5} {'legacy%':>8}")
    for cfg, s in report["summary_by_config"].items():
        print(f"  {cfg:<14} {s['n']:>3} {s['discovery_score_1']:>6} {s['discovery_score_1_pct']:>5.1f}% "
              f"{s['directional_correct']:>4} {s['quantitative_within_tolerance']:>6} "
              f"{s['falsifiable']:>5} {s['quantitatively_specific']:>5} "
              f"{s['reconstruction']:>6} {s['discovery_candidate']:>5} "
              f"{s['legacy_broad_range_correct_pct']:>7.1f}%")
    print()
    print("Note: DPS=1 requires ALL of: not_explicit, not_trivially_entailed,")
    print("      falsifiable, quantitatively_specific, later_independently_observed.")
    print("      'legacy%' = original V1.13 lenient broad-range CORRECT rate.")


if __name__ == "__main__":
    main()
