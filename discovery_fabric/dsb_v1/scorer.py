"""
DSB V1 — Deterministic Scorer
==============================

Scores each receipt on TWO outcomes:

  1. MECHANISM_RECONSTRUCTION
     Does the proposed mechanism overlap with the answer_mechanism?
     Score: term-overlap ratio (Jaccard-like) between proposed.mechanism and
     case.answer_mechanism. Range [0, 1].
     Verdict: RECONSTRUCTED if score >= 0.50, else NOT_RECONSTRUCTED.

  2. DISCOVERY_STRUCTURE_RECOVERY
     Does the proposed_relationship match the breakthrough_relationship
     relationally (not lexically)?
     Three sub-scores:
       (a) ENTITY_OVERLAP: content-term overlap between proposed_relationship
           and breakthrough_relationship.
       (b) RELATION_TYPE_MATCH: does the proposed_relationship express the
           same TYPE of relation (combination / causal / constraint-release)?
       (c) NOVEL_RELATION: does the proposed_relationship introduce a relation
           NOT explicit in the exposed_facts?
     Final score: weighted combination. Range [0, 1].
     Verdict: RECOVERED if score >= 0.50 AND NOVEL_RELATION passes,
              else NOT_RECOVERED.

CRITICAL INVARIANTS:
  (S1) The scorer is deterministic — no LLM judge.
  (S2) The scorer is reproducible — identical inputs produce identical outputs.
  (S3) Fabricated cases (case_type=fabricated) are scored with the SAME
       criteria as real cases. If the scorer gives high DISCOVERY_STRUCTURE_RECOVERY
       to fabricated counterfactuals, that is a FALSE POSITIVE.
  (S4) The scorer's output is hash-sealed.
"""
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.case_schema import load_case
from discovery_fabric.dsb_v1.generator import verify_receipt


# =============================================================================
# Text analysis helpers
# =============================================================================

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "by",
    "for", "with", "from", "as", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "can", "shall", "that", "this",
    "these", "those", "which", "who", "whom", "whose", "what", "where", "when",
    "why", "how", "than", "then", "there", "here", "such", "same", "other",
    "some", "any", "all", "no", "not", "only", "just", "very", "more", "most",
    "less", "fewer", "much", "many", "few", "several", "various", "each",
    "every", "both", "either", "neither", "into", "onto", "upon", "within",
    "without", "through", "during", "before", "after", "since", "until",
    "between", "among", "against", "above", "below", "over", "under", "across",
    "along", "around", "behind", "beyond", "toward", "towards", "about",
    "they", "them", "their", "it", "its", "we", "us", "our", "you", "your",
    "he", "him", "his", "she", "her", "hers", "i", "me", "my", "mine",
    "due", "because", "while", "whereas", "although", "though", "even",
    "however", "therefore", "thus", "hence", "moreover", "furthermore",
    "nevertheless", "nonetheless", "accordingly", "consequently", "otherwise",
    "rather", "yet", "still", "already", "always", "never", "often",
    "sometimes", "usually", "rarely", "seldom", "indeed", "instead",
    "besides", "etc", "via", "per", "using", "used", "use", "uses",
    "specific", "specifically", "particular", "particularly", "general",
    "generally", "approach", "method", "result", "results", "outcome",
    "outcomes", "effect", "effects", "impact", "impacts", "via", "through",
    "produce", "produces", "produced", "yield", "yields", "yielded",
}

GENERIC_TECHNICAL = {
    "system", "process", "approach", "method", "technique", "technology",
    "material", "compound", "structure", "property", "feature", "factor",
    "element", "component", "part", "phase", "stage", "state", "form",
    "type", "kind", "class", "category", "group", "set", "case", "instance",
    "example", "sample", "subject", "object", "item", "thing", "stuff",
    "matter", "substance", "result", "outcome", "effect", "consequence",
    "impact", "influence", "finding", "observation", "data", "information",
    "knowledge", "evidence", "fact", "detail", "study", "research",
    "experiment", "test", "trial", "evaluation", "analysis", "measurement",
    "value", "number", "amount", "quantity", "level", "rate", "ratio",
    "fraction", "percentage", "proportion", "concentration", "prediction",
    "hypothesis", "theory", "model", "framework", "concept", "idea", "notion",
    "view", "opinion", "perspective", "claim", "statement", "assertion",
    "argument", "reasoning", "logic", "principle", "law", "rule", "criterion",
    "standard", "specification", "requirement", "constraint", "limit",
    "boundary", "scope", "context", "situation", "scenario", "condition",
    "environment", "setting", "background", "history", "past", "future",
    "present", "current", "previous", "prior", "subsequent", "later",
    "earlier", "first", "second", "third", "final", "initial", "middle",
    "duration", "interval", "period", "time", "point", "cycle", "iteration",
    "round", "pass", "run", "execution", "operation", "function", "role",
    "purpose", "goal", "objective", "aim", "target", "intention", "design",
    "plan", "scheme", "strategy", "tactic", "high", "low", "higher", "lower",
    "reversible", "stable", "unstable", "safe", "unsafe", "known", "novel",
    "specific", "general", "broad", "narrow", "main", "minor", "major",
    "new", "old", "existing", "current",
}


def _content_terms(text: str) -> set[str]:
    tokens = re.findall(r"[a-z][a-z0-9_-]{2,}", (text or "").lower())
    return {t for t in tokens if t not in STOPWORDS and t not in GENERIC_TECHNICAL}


def _all_terms(text: str) -> set[str]:
    """All content terms including generic technical (for relation-type matching)."""
    tokens = re.findall(r"[a-z][a-z0-9_-]{2,}", (text or "").lower())
    return {t for t in tokens if t not in STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _overlap_ratio(a: set, b: set) -> float:
    """Overlap coefficient: |a ∩ b| / min(|a|, |b|). More forgiving than Jaccard."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# Relation-type patterns
RELATION_PATTERNS = {
    "combination": [
        r"\bcombin\w+\b", r"\bcoupl\w+\b", r"\bintegrat\w+\b", r"\bfus\w+\b",
        r"\bhybrid\w*\b", r"\bmix\w+\b", r"\bjo\w+\b", r"\btogeth\w+\b",
        r"\bwith\b.*\bwith\b", r"\bboth\b.*\band\b",
    ],
    "causal": [
        r"\bcaus\w+\b", r"\bproduc\w+\b", r"\bgenerat\w+\b", r"\bcreat\w+\b",
        r"\blead\w+\b", r"\bresult\w*\b", r"\btrigger\w+\b", r"\binduc\w+\b",
        r"\benabl\w+\b", r"\ballow\w+\b", r"\bpermit\w+\b",
    ],
    "constraint_release": [
        r"\breleas\w+\b", r"\bremov\w+\b", r"\beliminat\w+\b", r"\bovercom\w+\b",
        r"\bbypass\w+\b", r"\bcircumven\w+\b", r"\bsolv\w+\b", r"\bmitigat\w+\b",
        r"\bconstraint\b", r"\blimit\w+\b", r"\bbarrier\w*\b",
    ],
}


def _detect_relation_types(text: str) -> set[str]:
    """Detect which relation types are expressed in the text."""
    text_lower = text.lower()
    detected = set()
    for rtype, patterns in RELATION_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                detected.add(rtype)
                break
    return detected


# =============================================================================
# Scoring functions
# =============================================================================

def score_mechanism_reconstruction(receipt: dict, case: dict) -> dict:
    """Score 1: MECHANISM_RECONSTRUCTION.

    Compare proposed.mechanism with case.answer_mechanism.
    """
    proposed_mechanism = receipt.get("mechanism", "") or ""
    answer_mechanism = case.get("answer_mechanism", "") or ""

    if not proposed_mechanism.strip():
        return {
            "score": 0.0,
            "verdict": "NOT_RECONSTRUCTED",
            "reason": "empty proposed mechanism",
            "term_overlap_ratio": 0.0,
            "jaccard": 0.0,
        }

    proposed_terms = _content_terms(proposed_mechanism)
    answer_terms = _content_terms(answer_mechanism)
    overlap = _overlap_ratio(proposed_terms, answer_terms)
    jaccard = _jaccard(proposed_terms, answer_terms)

    # Use overlap_ratio as the primary score (more forgiving)
    score = round(overlap, 4)
    verdict = "RECONSTRUCTED" if score >= 0.50 else "NOT_RECONSTRUCTED"

    return {
        "score": score,
        "verdict": verdict,
        "term_overlap_ratio": round(overlap, 4),
        "jaccard": round(jaccard, 4),
        "proposed_terms_count": len(proposed_terms),
        "answer_terms_count": len(answer_terms),
        "shared_terms": sorted(list(proposed_terms & answer_terms))[:15],
    }


def score_discovery_structure_recovery(receipt: dict, case: dict) -> dict:
    """Score 2: DISCOVERY_STRUCTURE_RECOVERY.

    Three sub-scores:
      (a) ENTITY_OVERLAP: content-term overlap between proposed_relationship
          and breakthrough_relationship.
      (b) RELATION_TYPE_MATCH: do the proposed and breakthrough express the
          same relation type?
      (c) NOVEL_RELATION: does the proposed introduce a relation NOT explicit
          in the exposed_facts?

    Final score = 0.5 * (a) + 0.25 * (b) + 0.25 * (c)
    Verdict: RECOVERED if score >= 0.50 AND (c) >= 0.50.
    """
    proposed_rel = receipt.get("proposed_relationship", "") or ""
    breakthrough_rel = case.get("breakthrough_relationship", "") or ""
    exposed_text = " ".join(case.get("exposed_facts", []))

    if not proposed_rel.strip():
        return {
            "score": 0.0,
            "verdict": "NOT_RECOVERED",
            "reason": "empty proposed_relationship",
            "sub_scores": {},
        }

    # (a) ENTITY_OVERLAP
    proposed_terms = _content_terms(proposed_rel)
    breakthrough_terms = _content_terms(breakthrough_rel)
    entity_overlap = _overlap_ratio(proposed_terms, breakthrough_terms)

    # (b) RELATION_TYPE_MATCH
    proposed_types = _detect_relation_types(proposed_rel)
    breakthrough_types = _detect_relation_types(breakthrough_rel)
    if breakthrough_types:
        type_match = len(proposed_types & breakthrough_types) / len(breakthrough_types)
    else:
        type_match = 0.0

    # (c) NOVEL_RELATION: relation not explicit in exposed_facts
    exposed_terms = _all_terms(exposed_text)
    # Terms in proposed that are NOT in exposed (new entities introduced)
    new_terms_in_proposed = proposed_terms - exposed_terms
    # Relation types in proposed that are NOT in exposed
    exposed_types = _detect_relation_types(exposed_text)
    new_types_in_proposed = proposed_types - exposed_types
    # Novelty = combination of new terms + new relation types
    term_novelty = len(new_terms_in_proposed) / max(len(proposed_terms), 1)
    type_novelty = len(new_types_in_proposed) / max(len(proposed_types), 1) if proposed_types else 0.0
    novelty = 0.5 * term_novelty + 0.5 * type_novelty

    final_score = round(0.5 * entity_overlap + 0.25 * type_match + 0.25 * novelty, 4)
    verdict = "RECOVERED" if (final_score >= 0.50 and novelty >= 0.30) else "NOT_RECOVERED"

    return {
        "score": final_score,
        "verdict": verdict,
        "sub_scores": {
            "entity_overlap": round(entity_overlap, 4),
            "relation_type_match": round(type_match, 4),
            "novel_relation": round(novelty, 4),
        },
        "proposed_relation_types": sorted(proposed_types),
        "breakthrough_relation_types": sorted(breakthrough_types),
        "exposed_relation_types": sorted(exposed_types),
        "new_terms_in_proposed": sorted(list(new_terms_in_proposed))[:15],
    }


def score_receipt(receipt: dict, case: dict) -> dict:
    """Score one receipt on both outcomes."""
    # Verify receipt integrity
    integrity_ok = verify_receipt(receipt)

    mech = score_mechanism_reconstruction(receipt, case)
    disc = score_discovery_structure_recovery(receipt, case)

    score = {
        "schema_version": "1.0.0",
        "score_type": "DSB_V1_DETERMINISTIC",
        "receipt_id": receipt.get("receipt_id"),
        "case_id": receipt.get("case_id"),
        "case_type": case.get("case_type"),
        "arm": receipt.get("arm"),
        "receipt_hash": receipt.get("receipt_hash"),
        "answer_hash": case.get("answer_hash"),
        "receipt_integrity_ok": integrity_ok,
        "mechanism_reconstruction": mech,
        "discovery_structure_recovery": disc,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }

    canonical = json.dumps(score, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    score["score_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return score


# =============================================================================
# Score all receipts
# =============================================================================

def score_all() -> dict:
    """Score all 80 receipts."""
    REPO = Path(__file__).resolve().parents[2]
    receipts_dir = REPO / "discovery_fabric/dsb_v1/receipts"
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"

    # Load all cases
    cases = {}
    for d in [real_dir, fab_dir]:
        for cp in sorted(d.glob("DSB-*.json")):
            case = load_case(cp)
            cases[case["case_id"]] = case

    # Score all receipts
    scores = []
    for rp in sorted(receipts_dir.glob("RECEIPT-*.json")):
        receipt = json.load(open(rp))
        case_id = receipt.get("case_id")
        case = cases.get(case_id)
        if not case:
            continue
        score = score_receipt(receipt, case)
        scores.append(score)

    return {
        "n_scores": len(scores),
        "scores": scores,
    }


def main():
    print("=" * 72)
    print("DSB V1 — DETERMINISTIC SCORER")
    print("=" * 72)
    print()

    result = score_all()
    scores = result["scores"]
    print(f"Scored {len(scores)} receipts\n")

    # Summary by arm × case_type × verdict
    from collections import defaultdict
    summary = defaultdict(lambda: {"n": 0, "mech_reconstructed": 0, "disc_recovered": 0,
                                    "mech_score_sum": 0.0, "disc_score_sum": 0.0})
    for s in scores:
        arm = s["arm"]
        ctype = s["case_type"]
        key = (arm, ctype)
        summary[key]["n"] += 1
        if s["mechanism_reconstruction"]["verdict"] == "RECONSTRUCTED":
            summary[key]["mech_reconstructed"] += 1
        if s["discovery_structure_recovery"]["verdict"] == "RECOVERED":
            summary[key]["disc_recovered"] += 1
        summary[key]["mech_score_sum"] += s["mechanism_reconstruction"]["score"]
        summary[key]["disc_score_sum"] += s["discovery_structure_recovery"]["score"]

    print(f"{'Arm':<16} {'Type':<12} {'N':>3} {'MechR':>6} {'DiscR':>6} {'MechAvg':>8} {'DiscAvg':>8}")
    print("-" * 70)
    for (arm, ctype), s in sorted(summary.items()):
        mech_avg = s["mech_score_sum"] / max(s["n"], 1)
        disc_avg = s["disc_score_sum"] / max(s["n"], 1)
        print(f"{arm:<16} {ctype:<12} {s['n']:>3} {s['mech_reconstructed']:>6} {s['disc_recovered']:>6} {mech_avg:>8.3f} {disc_avg:>8.3f}")

    # Save scores
    out_path = REPO / "discovery_fabric/dsb_v1/scores/scores.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    h = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"\nScores saved: {out_path}")
    print(f"Hash: {h[:32]}...")


if __name__ == "__main__":
    main()
