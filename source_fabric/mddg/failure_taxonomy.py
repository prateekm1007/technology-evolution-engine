"""
Medical Device Discovery Graph V1 — Failure Taxonomy (CTO directive #7).

18 controlled-vocabulary failure modes. Per CTO: "Do not invent these as facts
about individual devices; use them as controlled vocabulary and map real
evidence into them with provenance."
"""
from __future__ import annotations

FAILURE_MODES = {
    "MECHANICAL_FAILURE",
    "FATIGUE",
    "WEAR",
    "CORROSION",
    "DELAMINATION",
    "DEGRADATION",
    "BIOCOMPATIBILITY",
    "THROMBOSIS",
    "INFECTION",
    "SENSOR_DRIFT",
    "FALSE_POSITIVE",
    "FALSE_NEGATIVE",
    "THERMAL_DAMAGE",
    "BATTERY_FAILURE",
    "STERILIZATION_FAILURE",
    "MANUFACTURING_DEFECT",
    "SOFTWARE_FAILURE",
    "CLINICAL_ENDPOINT_FAILURE",
}


def is_valid_failure_mode(fm: str) -> bool:
    return fm in FAILURE_MODES


def classify_failure_from_text(text: str) -> list[str]:
    """Map real evidence text into failure-mode controlled vocabulary.

    This is a keyword-based classifier. Each match produces a failure-mode
    tag with provenance = the source text. Does NOT invent facts — it only
    maps explicit textual evidence to the controlled vocabulary.
    """
    text_lower = (text or "").lower()
    matches = []
    # Keyword mapping: each failure mode has a set of trigger phrases
    KEYWORD_MAP = {
        "MECHANICAL_FAILURE": ["mechanical failure", "fracture", "broke", "structural failure", "crack"],
        "FATIGUE": ["fatigue", "cyclic loading", "cyclic fatigue"],
        "WEAR": ["wear", "abrasion", "erosion"],
        "CORROSION": ["corrosion", "oxidation", "rust", "galvanic"],
        "DELAMINATION": ["delamination", "peeling", "separation", "debonding"],
        "DEGRADATION": ["degradation", "deterioration", "breakdown"],
        "BIOCOMPATIBILITY": ["biocompatibility", "foreign body", "inflammatory response", "rejection"],
        "THROMBOSIS": ["thrombosis", "thrombus", "clot", "embolism", "occlusion"],
        "INFECTION": ["infection", "sepsis", "bacterial", "contamination"],
        "SENSOR_DRIFT": ["sensor drift", "calibration drift", "signal drift", "baseline drift"],
        "FALSE_POSITIVE": ["false positive", "false alarm", "overdetection"],
        "FALSE_NEGATIVE": ["false negative", "missed detection", "underdetection"],
        "THERMAL_DAMAGE": ["thermal damage", "burn", "overheating", "heat injury"],
        "BATTERY_FAILURE": ["battery failure", "battery depletion", "battery fire", "battery explosion", "premature battery"],
        "STERILIZATION_FAILURE": ["sterilization failure", "sterility", "contaminated", "unsterile"],
        "MANUFACTURING_DEFECT": ["manufacturing defect", "production defect", "quality control", "defective"],
        "SOFTWARE_FAILURE": ["software failure", "software bug", "firmware", "programming error", "algorithm error"],
        "CLINICAL_ENDPOINT_FAILURE": ["endpoint failure", "primary endpoint not met", "efficacy failure", "failed to meet"],
    }
    for fm, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                matches.append(fm)
                break  # one match per failure mode
    return matches
