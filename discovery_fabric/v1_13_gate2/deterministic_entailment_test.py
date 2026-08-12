"""
V1.13 GATE 2 — Deterministic Entailment Test (no LLM)
=====================================================

Given:
  - a structured evidence object (entities, mechanisms, causal_edges,
    combinations, constraints)
  - a prediction (hypothesis + units_range + expected_direction +
    falsification_condition)

Classify the prediction as:
    RECONSTRUCTION              if the prediction's relation graph is fully
                                encoded in the evidence's structured objects.
                                "Near-deterministic consequence of the supplied
                                evidence, even if the exact sentence/terms
                                never appear."

    GENUINE_NOVEL_PREDICTION    if the prediction introduces a genuinely new
                                relation: a new causal edge, a new combination,
                                a new constraint release, or a new entity
                                operating in a new mechanism.

Six sub-checks (all deterministic, all reproducible):

  (1) ENTITIES_PRESENT
        All proper-noun / chemical entities in the prediction appear in the
        evidence. NO new entities introduced.
        If TRUE → contributes to RECONSTRUCTION.

  (2) MECHANISMS_PRESENT
        All mechanism verbs in the prediction (intercalate, amplify, cut,
        block, etc.) appear in the evidence's mechanisms list.
        If TRUE → contributes to RECONSTRUCTION.

  (3) CAUSAL_EDGES_PRESENT
        Every (subject, verb_type, object) triple in the prediction maps to
        an existing causal edge in the evidence (modulo synonym matching on
        subject/object).
        If TRUE → contributes to RECONSTRUCTION.

  (4) COMBINATION_ALREADY_IMPLIED
        The prediction proposes a combination (X + Y → Z). Check whether
        the same pair {X, Y} already appears in the evidence's combinations
        list, OR whether both X and Y are independently attested in the
        evidence and the combination is a trivial conjunction.
        If TRUE → contributes to RECONSTRUCTION.

  (5) CONSTRAINT_ALREADY_STATED
        The prediction's quantitative constraint (e.g., ">100 cycles") is
        already stated in the evidence's constraints list, modulo unit
        equivalence.
        If TRUE → contributes to RECONSTRUCTION.

  (6) PREDICTION_DERIVABLE_WITHOUT_NEW_RELATION
        Composite check: if (1) AND (2) AND (3) all hold (i.e., the
        prediction introduces no new entity, no new mechanism, no new causal
        edge), then the prediction is derivable without a new relation.
        If TRUE → RECONSTRUCTION.

A prediction is RECONSTRUCTION if ANY of (3), (4), (5), (6) is True.
Otherwise it is GENUINE_NOVEL_PREDICTION.

Information-content score (continuous, 0.0 = full reconstruction, 1.0 =
fully novel):
    IC = 1 - (passes_encoding / 6)
    where passes_encoding = number of (1)-(6) that are True.

Final classification:
    IC < 0.34   → RECONSTRUCTION           (≥4 of 6 encoded)
    IC < 0.67   → PARTIALLY_NOVEL          (2-3 of 6 encoded)
    else        → GENUINE_NOVEL_PREDICTION (≤1 of 6 encoded)

For Gate 2 purposes, only GENUINE_NOVEL_PREDICTION qualifies as a candidate
discovery. PARTIALLY_NOVEL and RECONSTRUCTION both fail the information-
content test.
"""
from __future__ import annotations

import json
import re
import math
from pathlib import Path
from typing import Any

# Import entity extraction helpers from the structured_evidence_extractor
import sys
REPO = Path("/home/z/my-project/audit/technology-evolution-engine")
sys.path.insert(0, str(REPO))
from discovery_fabric.v1_13_gate2.structured_evidence_extractor import (  # noqa: E402
    extract_entities,
    extract_mechanisms_and_causal_edges,
    extract_combinations,
    extract_constraints,
    CAUSAL_VERBS,
    STOPWORDS,
)

# ---------------------------------------------------------------------------
# Synonym maps for fuzzy matching
# ---------------------------------------------------------------------------

# Tokens that should be treated as equivalent for entity matching
SYNONYMS = {
    # Battery domain
    "licoo2": "licoo2", "li-co-o2": "licoo2", "licoo-2": "licoo2",
    "graphite": "graphite", "carbon": "graphite",  # close enough for surface match
    "lithium": "lithium", "li": "lithium", "li-ion": "lithium",
    "lithium-ion": "lithium", "liion": "lithium",
    "battery": "battery", "batteries": "battery",
    "intercalation": "intercalation", "intercalate": "intercalation",
    "intercalates": "intercalation",
    "anode": "anode", "cathode": "cathode",
    "cycle": "cycle", "cycles": "cycle", "cycling": "cycle",
    "rechargeable": "rechargeable",
    # PCR / biology
    "dna": "dna", "polymerase": "polymerase",
    "primer": "primer", "primers": "primer",
    "amplification": "amplification", "amplify": "amplification",
    # ML
    "cnn": "cnn", "cnns": "cnn", "neural": "neural", "network": "network",
    "networks": "network", "neural-network": "neural-network",
    "neural-networks": "neural-network",
    "classifier": "classifier", "classifiers": "classifier",
    "training": "training", "train": "training",
    "error": "error", "errors": "error",
    # Generic
    "system": "system", "systems": "system",
    "material": "material", "materials": "material",
}


def _normalize_entity(e: str) -> str:
    e = e.lower().strip()
    e = re.sub(r"[^a-z0-9-]", "", e)
    return SYNONYMS.get(e, e)


def _entity_set(entities_list: list[str]) -> set[str]:
    return {_normalize_entity(e) for e in entities_list if e and len(e) >= 2}


def _tokenize_subject_object(s: str) -> set[str]:
    """Tokenize a subject/object string into normalized entities."""
    s = s.lower()
    # Split on whitespace and punctuation
    toks = re.findall(r"[a-z][a-z0-9_-]{2,}", s)
    return {_normalize_entity(t) for t in toks if t not in STOPWORDS and len(t) >= 3}


# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------

def check_1_entities_present(prediction_entities: set[str],
                              evidence_entities: set[str]) -> dict:
    """(1) ENTITIES_PRESENT: all prediction entities in evidence?"""
    new_entities = prediction_entities - evidence_entities
    # Filter out very generic terms that shouldn't count as "new"
    generic = {"predicted", "value", "result", "outcome", "method", "approach",
               "study", "analysis", "test", "experiment", "measurement"}
    new_entities = {e for e in new_entities if e not in generic}
    return {
        "check": "ENTITIES_PRESENT",
        "passed": len(new_entities) == 0,
        "new_entities_in_prediction": sorted(new_entities),
    }


def check_2_mechanisms_present(prediction_text: str,
                                evidence_mechanisms: list[dict]) -> dict:
    """(2) MECHANISMS_PRESENT: all mechanism verbs in prediction appear in evidence?"""
    pred_tokens = set(re.findall(r"\b[a-z]+\b", prediction_text.lower()))
    pred_mech_verbs = pred_tokens & set(CAUSAL_VERBS.keys())
    ev_mech_verbs = {m["predicate"].lower() for m in evidence_mechanisms}
    # Also collect verb lemmas from source sentences
    for m in evidence_mechanisms:
        sent = m.get("source_sentence", "").lower()
        for w in re.findall(r"\b[a-z]+\b", sent):
            if w in CAUSAL_VERBS:
                ev_mech_verbs.add(CAUSAL_VERBS[w].lower())
    new_verbs = pred_mech_verbs - {v for v in pred_mech_verbs if any(
        ev_v in v or v in ev_v for ev_v in ev_mech_verbs
    )}
    return {
        "check": "MECHANISMS_PRESENT",
        "passed": len(new_verbs) == 0,
        "prediction_mechanism_verbs": sorted(pred_mech_verbs),
        "evidence_mechanism_verbs": sorted(ev_mech_verbs),
        "new_verbs_in_prediction": sorted(new_verbs),
    }


def check_3_causal_edges_present(prediction_text: str,
                                  evidence_causal_edges: list[dict]) -> dict:
    """(3) CAUSAL_EDGES_PRESENT: every (S, V, O) triple in prediction maps
    to an existing causal edge in evidence."""
    # Extract SVO triples from the prediction text
    from discovery_fabric.v1_13_gate2.structured_evidence_extractor import (
        _split_simple_sentences, _extract_subject_predicate_object
    )
    pred_sentences = _split_simple_sentences(prediction_text)
    pred_triples = []
    for sent in pred_sentences:
        svo = _extract_subject_predicate_object(sent)
        if svo:
            subj, verb, obj = svo
            pred_triples.append({
                "subject": subj.lower(),
                "predicate": verb,
                "object": obj.lower(),
            })

    if not pred_triples:
        # No triples extracted → can't establish entailment this way
        return {
            "check": "CAUSAL_EDGES_PRESENT",
            "passed": False,  # cannot confirm encoding
            "prediction_triples": [],
            "unmatched_triples": [],
            "reason": "no SVO triples extracted from prediction",
        }

    # Build evidence edge index: set of (subj_tokens, type, obj_tokens)
    ev_edges_indexed = []
    for e in evidence_causal_edges:
        subj_toks = _tokenize_subject_object(e["cause"])
        obj_toks = _tokenize_subject_object(e["effect"])
        ev_edges_indexed.append({
            "subject_tokens": sorted(subj_toks),
            "type": e["type"],
            "object_tokens": sorted(obj_toks),
        })

    unmatched = []
    for pt in pred_triples:
        subj_toks = _tokenize_subject_object(pt["subject"])
        obj_toks = _tokenize_subject_object(pt["object"])
        # Try to find a matching evidence edge
        matched = False
        for ev in ev_edges_indexed:
            # Subject overlap: at least 1 token in common (or subset)
            subj_overlap = subj_toks & set(ev["subject_tokens"])
            obj_overlap = obj_toks & set(ev["object_tokens"])
            # Type match: same type, or one is more specific
            type_match = (pt["predicate"] == ev["type"] or
                          pt["predicate"] in {"EXHIBITS", "ENABLES"} or
                          ev["type"] in {"EXHIBITS", "ENABLES"})
            if subj_overlap and obj_overlap and type_match:
                matched = True
                break
        if not matched:
            unmatched.append(pt)

    return {
        "check": "CAUSAL_EDGES_PRESENT",
        "passed": len(unmatched) == 0,
        "prediction_triples": pred_triples,
        "unmatched_triples": unmatched,
    }


def check_4_combination_already_implied(prediction_text: str,
                                          evidence_combinations: list[dict],
                                          evidence_entities: set[str]) -> dict:
    """(4) COMBINATION_ALREADY_IMPLIED: prediction proposes combination X+Y→Z,
    where {X, Y} already appears in evidence combinations, OR both X and Y
    are independently attested in evidence (trivial conjunction)."""
    # Detect combination phrases in prediction
    combo_patterns = [
        r"\b(\w+)\s+(?:and|combined with|plus|with|\+)\s+(\w+)\b",
        r"\b(\w+)-(\w+)\b",  # hyphenated: "LiCoO2-graphite"
    ]
    pred_combos = []
    text_lower = prediction_text.lower()
    for pat in combo_patterns:
        for m in re.finditer(pat, text_lower):
            a, b = m.group(1), m.group(2)
            if a in STOPWORDS or b in STOPWORDS:
                continue
            if len(a) < 3 or len(b) < 3:
                continue
            pred_combos.append((_normalize_entity(a), _normalize_entity(b)))

    if not pred_combos:
        return {
            "check": "COMBINATION_ALREADY_IMPLIED",
            "passed": False,  # no combination in prediction
            "prediction_combinations": [],
            "reason": "no combination detected in prediction",
        }

    # Check each prediction combination against evidence
    ev_combo_pairs = []
    for ec in evidence_combinations:
        a = _normalize_entity(ec["a"])
        b = _normalize_entity(ec["b"])
        ev_combo_pairs.append(frozenset({a, b}))

    all_implied = True
    implied_details = []
    for a, b in pred_combos:
        pair = frozenset({a, b})
        in_explicit = pair in ev_combo_pairs
        # Both entities independently attested?
        both_in_evidence = (a in evidence_entities and b in evidence_entities)
        implied = in_explicit or both_in_evidence
        implied_details.append({
            "pair": sorted([a, b]),
            "in_explicit_combinations": in_explicit,
            "both_entities_in_evidence": both_in_evidence,
            "implied": implied,
        })
        if not implied:
            all_implied = False

    # Sort evidence_combinations output deterministically
    ev_combo_pairs_sorted = sorted([sorted(list(p)) for p in ev_combo_pairs])

    return {
        "check": "COMBINATION_ALREADY_IMPLIED",
        "passed": all_implied,
        "prediction_combinations": [sorted(list(p)) for p in pred_combos],
        "evidence_combinations": ev_combo_pairs_sorted,
        "details": implied_details,
    }


def check_5_constraint_already_stated(prediction_units_range: str,
                                       evidence_constraints: list[dict]) -> dict:
    """(5) CONSTRAINT_ALREADY_STATED: prediction's quantitative constraint is
    already in evidence's constraints list, modulo unit equivalence."""
    # Extract numeric bounds from prediction
    pred_bounds = _extract_numeric_bounds(prediction_units_range)
    if pred_bounds is None:
        return {
            "check": "CONSTRAINT_ALREADY_STATED",
            "passed": False,  # no numeric constraint in prediction
            "prediction_bounds": None,
            "reason": "no numeric constraint in prediction",
        }

    low, high = pred_bounds
    # Compare against evidence constraints
    for ec in evidence_constraints:
        if ec.get("type") != "NUMERIC":
            continue
        ev_val = ec.get("value")
        if ev_val is None:
            continue
        # Check if evidence value falls within prediction's range
        # (prediction constraint re-states evidence constraint)
        try:
            ev_val = float(ev_val)
        except (TypeError, ValueError):
            continue
        if low <= ev_val <= high:
            return {
                "check": "CONSTRAINT_ALREADY_STATED",
                "passed": True,
                "prediction_bounds": [low, high],
                "matched_evidence_constraint": ec,
            }

    return {
        "check": "CONSTRAINT_ALREADY_STATED",
        "passed": False,
        "prediction_bounds": [low, high],
        "evidence_numeric_constraints": [c for c in evidence_constraints if c.get("type") == "NUMERIC"],
    }


def check_6_prediction_derivable_without_new_relation(
        c1: dict, c2: dict, c3: dict) -> dict:
    """(6) PREDICTION_DERIVABLE_WITHOUT_NEW_RELATION: composite of (1), (2), (3)."""
    derivable = c1["passed"] and c2["passed"] and c3["passed"]
    return {
        "check": "PREDICTION_DERIVABLE_WITHOUT_NEW_RELATION",
        "passed": derivable,
        "components": {
            "entities_present": c1["passed"],
            "mechanisms_present": c2["passed"],
            "causal_edges_present": c3["passed"],
        },
    }


def _extract_numeric_bounds(text: str) -> tuple[float, float] | None:
    text = text or ""
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:-|to|\u2013)\s*(-?\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r"(?:>=?|greater than|above|more than|at least)\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        v = float(m.group(1))
        return v, math.inf
    m = re.search(r"(?:<=?|less than|below|under|at most)\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        v = float(m.group(1))
        return -math.inf, v
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    if len(nums) >= 1:
        v = float(nums[0])
        return v, v
    return None


# ---------------------------------------------------------------------------
# Top-level classification
# ---------------------------------------------------------------------------

def classify_prediction(receipt: dict, evidence_object: dict) -> dict:
    """Classify a prediction receipt against structured evidence.

    Returns:
      {
        "classification": "RECONSTRUCTION" | "PARTIALLY_NOVEL" | "GENUINE_NOVEL_PREDICTION",
        "information_content_score": float,   # 0.0 = full reconstruction, 1.0 = fully novel
        "checks": {check_name: result_dict, ...},
        "encoded_count": int,                # how many of the 6 checks passed
        "reason": str,
      }
    """
    prediction_text = " ".join([
        receipt.get("hypothesis", ""),
        receipt.get("prediction", ""),
    ])
    prediction_entities = _entity_set(
        extract_entities(prediction_text)["all"]
    )
    evidence_entities = _entity_set(evidence_object.get("entities", []))

    c1 = check_1_entities_present(prediction_entities, evidence_entities)
    c2 = check_2_mechanisms_present(prediction_text, evidence_object.get("mechanisms", []))
    c3 = check_3_causal_edges_present(prediction_text, evidence_object.get("causal_edges", []))
    c4 = check_4_combination_already_implied(prediction_text,
                                              evidence_object.get("combinations", []),
                                              evidence_entities)
    c5 = check_5_constraint_already_stated(receipt.get("units_range", ""),
                                            evidence_object.get("constraints", []))
    c6 = check_6_prediction_derivable_without_new_relation(c1, c2, c3)

    checks = {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5, "c6": c6}

    # Count how many checks indicate encoding
    encoded_count = sum(1 for c in [c1, c2, c3, c4, c5, c6] if c["passed"])

    # Information-content score: 1.0 = fully novel, 0.0 = full reconstruction
    ic_score = 1.0 - (encoded_count / 6.0)

    # Classification
    # RECONSTRUCTION if any of (3, 4, 5, 6) is True (encoded)
    # OR if encoded_count >= 4
    reconstruction = (c3["passed"] or c4["passed"] or c5["passed"] or c6["passed"]
                      or encoded_count >= 4)
    if reconstruction:
        classification = "RECONSTRUCTION"
        reason = (f"prediction encoded by evidence: "
                  f"c3={c3['passed']}, c4={c4['passed']}, "
                  f"c5={c5['passed']}, c6={c6['passed']}, "
                  f"encoded_count={encoded_count}/6")
    elif encoded_count >= 2:
        classification = "PARTIALLY_NOVEL"
        reason = f"prediction partially encoded: encoded_count={encoded_count}/6"
    else:
        classification = "GENUINE_NOVEL_PREDICTION"
        reason = f"prediction introduces genuinely new relation: encoded_count={encoded_count}/6"

    return {
        "classification": classification,
        "information_content_score": round(ic_score, 4),
        "encoded_count": encoded_count,
        "encoded_count_max": 6,
        "checks": checks,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Test the entailment test on the original V1.13 receipts (for sanity check).
    The actual Gate 2 evaluation runs on the new leakage-controlled receipts.
    """
    V1_13_RECEIPTS = REPO / "discovery_fabric/v1_13/receipts"
    EVIDENCE_DIR = REPO / "discovery_fabric/v1_13_gate2/evidence_objects"

    receipts = sorted(V1_13_RECEIPTS.glob("PRED-*.json"))
    print(f"Testing entailment test on {len(receipts)} original V1.13 receipts...\n")

    from collections import Counter
    classifications = Counter()
    for rp in receipts:
        receipt = json.load(open(rp))
        cid = receipt["candidate_id"]
        m = re.match(r"PRED-(PB-\d+)-", cid)
        if not m:
            continue
        case_id = m.group(1)
        ev_path = EVIDENCE_DIR / f"{case_id}.json"
        if not ev_path.exists():
            continue
        ev_obj = json.load(open(ev_path))
        result = classify_prediction(receipt, ev_obj)
        classifications[result["classification"]] += 1
        print(f"  {cid}: {result['classification']} (IC={result['information_content_score']}, encoded={result['encoded_count']}/6)")

    print(f"\nClassification summary (original V1.13 receipts):")
    for cls, n in classifications.most_common():
        print(f"  {cls}: {n}")
    print(f"\nNote: these are ORIGINAL V1.13 receipts. Gate 2 will generate new")
    print(f"leakage-controlled receipts and re-classify them.")


if __name__ == "__main__":
    main()
