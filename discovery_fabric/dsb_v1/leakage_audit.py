"""
DSB V1 — Leakage Audit
=======================

Verifies that the payload the generator receives contains NONE of:
  - any withheld fact (verbatim or near-verbatim)
  - any forbidden term (the discovery name, etc.)
  - any future terminology (terms that emerged post-discovery)
  - any breakthrough_relationship text (verbatim or near-verbatim)
  - any answer_mechanism text (verbatim or near-verbatim)
  - any historical_source identifier

The audit is deterministic and reproducible. Every payload must pass before
the generator is allowed to run on it.

AUDIT CHECKS:
  L1. No forbidden_term appears in the payload (case-insensitive substring).
  L2. No future_terminology appears in the payload.
  L3. No withheld_fact appears in the payload (verbatim or with >=80% term overlap).
  L4. No breakthrough_relationship text appears in the payload.
  L5. No answer_mechanism text appears in the payload.
  L6. No historical_source identifier (Nobel year, paper year + author combo) leaks.
  L7. Payload hash is valid (payload not modified after building).

If ANY check fails, the audit reports a CRITICAL leakage finding and the
generator MUST refuse to run on that payload.
"""
import json
import re
import hashlib
from pathlib import Path
from typing import Any

import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from discovery_fabric.dsb_v1.payload_builder import build_payload_text, verify_payload
from discovery_fabric.dsb_v1.case_schema import load_case


# Generic stopwords excluded from term-overlap calculations
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
}


def _content_terms(text: str) -> set[str]:
    """Tokenize text into content terms (lowercase, alpha, len>=3, no stopwords)."""
    tokens = re.findall(r"[a-z][a-z0-9_-]{2,}", (text or "").lower())
    return {t for t in tokens if t not in STOPWORDS}


def _term_overlap_ratio(a: str, b: str) -> float:
    """Compute the Jaccard-like overlap ratio between two texts' content terms."""
    ta = _content_terms(a)
    tb = _content_terms(b)
    if not ta:
        return 0.0
    return len(ta & tb) / len(ta)


# =============================================================================
# Audit checks
# =============================================================================

def check_L1_no_forbidden_terms(payload_text: str, case: dict) -> dict:
    """L1. No forbidden_term appears in the payload (case-insensitive)."""
    text_lower = payload_text.lower()
    violations = []
    for term in case.get("forbidden_terms", []):
        if term.lower() in text_lower:
            violations.append(term)
    return {
        "check": "L1_no_forbidden_terms",
        "passed": len(violations) == 0,
        "violations": violations,
    }


def check_L2_no_future_terminology(payload_text: str, case: dict) -> dict:
    """L2. No future_terminology appears in the payload."""
    text_lower = payload_text.lower()
    violations = []
    for term in case.get("future_terminology", []):
        if term.lower() in text_lower:
            violations.append(term)
    return {
        "check": "L2_no_future_terminology",
        "passed": len(violations) == 0,
        "violations": violations,
    }


def check_L3_no_withheld_facts(payload_text: str, case: dict) -> dict:
    """L3. No withheld_fact appears in the payload (verbatim or >=80% overlap)."""
    violations = []
    for wf in case.get("withheld_facts", []):
        # Verbatim check (case-insensitive)
        if wf.lower() in payload_text.lower():
            violations.append({"withheld_fact": wf[:100], "match_type": "verbatim"})
            continue
        # Near-verbatim: high term overlap
        overlap = _term_overlap_ratio(wf, payload_text)
        if overlap >= 0.80:
            violations.append({"withheld_fact": wf[:100], "match_type": "high_overlap",
                               "overlap_ratio": round(overlap, 3)})
    return {
        "check": "L3_no_withheld_facts",
        "passed": len(violations) == 0,
        "violations": violations,
    }


def check_L4_no_breakthrough_text(payload_text: str, case: dict) -> dict:
    """L4. No breakthrough_relationship text appears in the payload."""
    bt = case.get("breakthrough_relationship", "")
    if not bt:
        return {"check": "L4_no_breakthrough_text", "passed": True, "violations": []}
    # Verbatim substring check
    if bt.lower() in payload_text.lower():
        return {"check": "L4_no_breakthrough_text", "passed": False,
                "violations": [{"match_type": "verbatim"}]}
    # High overlap check
    overlap = _term_overlap_ratio(bt, payload_text)
    if overlap >= 0.75:
        return {"check": "L4_no_breakthrough_text", "passed": False,
                "violations": [{"match_type": "high_overlap", "overlap_ratio": round(overlap, 3)}]}
    return {"check": "L4_no_breakthrough_text", "passed": True, "violations": []}


def check_L5_no_answer_mechanism(payload_text: str, case: dict) -> dict:
    """L5. No answer_mechanism text appears in the payload."""
    am = case.get("answer_mechanism", "")
    if not am:
        return {"check": "L5_no_answer_mechanism", "passed": True, "violations": []}
    if am.lower() in payload_text.lower():
        return {"check": "L5_no_answer_mechanism", "passed": False,
                "violations": [{"match_type": "verbatim"}]}
    overlap = _term_overlap_ratio(am, payload_text)
    if overlap >= 0.75:
        return {"check": "L5_no_answer_mechanism", "passed": False,
                "violations": [{"match_type": "high_overlap", "overlap_ratio": round(overlap, 3)}]}
    return {"check": "L5_no_answer_mechanism", "passed": True, "violations": []}


def check_L6_no_source_identifiers(payload_text: str, case: dict) -> dict:
    """L6. No historical_source identifier leaks (Nobel year, author + year combos)."""
    source = case.get("historical_source", "")
    text_lower = payload_text.lower()
    violations = []
    # Extract all 4-digit years from source
    source_years = re.findall(r"\b(?:19|20)\d{2}\b", source)
    for yr in source_years:
        if yr in text_lower:
            violations.append({"year": yr})
    # Check for "Nobel" mention
    if "nobel" in text_lower:
        violations.append({"term": "nobel"})
    # Check for author surnames. We extract candidates from the source and
    # filter out common journal/venue words. A candidate is flagged as an
    # author only if it appears in the source FOLLOWED by a 4-digit year
    # (e.g., "Brahmer 2012", "Kariko/Weissman, 2005"). This avoids false
    # positives on capitalized chemical names like "Sodium" or "Argonaute"
    # that happen to appear in the source.
    author_year_matches = re.findall(r"\b([A-Z][a-z]+)\s*[,/]?\s*((?:19|20)\d{2})\b", source)
    flagged_authors = set()
    for author, _year in author_year_matches:
        common_words = {"Science", "Cell", "Nature", "NEJM", "New", "England",
                        "Journal", "Phase", "Trial", "ECHO"}
        if author in common_words:
            continue
        if author.lower() in STOPWORDS:
            continue
        # Check if author name appears in payload (case-sensitive)
        if re.search(rf"\b{re.escape(author)}\b", payload_text):
            flagged_authors.add(author)
    for a in sorted(flagged_authors):
        violations.append({"author": a})
    return {
        "check": "L6_no_source_identifiers",
        "passed": len(violations) == 0,
        "violations": violations[:10],
    }


def check_L7_payload_hash(payload: dict) -> dict:
    """L7. Payload hash is valid (payload not modified after building)."""
    return {
        "check": "L7_payload_hash",
        "passed": verify_payload(payload),
    }


# =============================================================================
# Top-level audit
# =============================================================================

def audit_payload(payload: dict, case: dict) -> dict:
    """Run all 7 leakage checks on a payload.

    Returns a sealed audit report. If ANY check fails, the audit is CRITICAL
    and the generator MUST refuse to run on this payload.
    """
    payload_text = build_payload_text(payload)

    checks = [
        check_L1_no_forbidden_terms(payload_text, case),
        check_L2_no_future_terminology(payload_text, case),
        check_L3_no_withheld_facts(payload_text, case),
        check_L4_no_breakthrough_text(payload_text, case),
        check_L5_no_answer_mechanism(payload_text, case),
        check_L6_no_source_identifiers(payload_text, case),
        check_L7_payload_hash(payload),
    ]

    n_passed = sum(1 for c in checks if c["passed"])
    n_failed = sum(1 for c in checks if not c["passed"])
    overall_pass = n_failed == 0

    return {
        "audit_type": "DSB_V1_LEAKAGE_AUDIT",
        "payload_id": payload.get("payload_id"),
        "case_id": case.get("case_id"),
        "arm": payload.get("arm"),
        "n_checks": len(checks),
        "n_passed": n_passed,
        "n_failed": n_failed,
        "overall_pass": overall_pass,
        "severity": "OK" if overall_pass else "CRITICAL",
        "checks": checks,
    }


def audit_all_payloads() -> dict:
    """Audit all payloads (20 cases × 4 arms = 80 payloads)."""
    REPO = Path(__file__).resolve().parents[2]
    real_dir = REPO / "discovery_fabric/dsb_v1/cases/real"
    fab_dir = REPO / "discovery_fabric/dsb_v1/cases/fabricated"
    arms = ["LLM_only", "mechanism_only", "combination", "full_system"]

    from discovery_fabric.dsb_v1.payload_builder import build_payload

    audits = []
    for d in [real_dir, fab_dir]:
        for case_path in sorted(d.glob("DSB-*.json")):
            case = load_case(case_path)
            for arm in arms:
                payload = build_payload(case, arm)
                audit = audit_payload(payload, case)
                audits.append(audit)

    n_total = len(audits)
    n_pass = sum(1 for a in audits if a["overall_pass"])
    n_fail = n_total - n_pass
    return {
        "audit_type": "DSB_V1_LEAKAGE_AUDIT_ALL",
        "n_payloads": n_total,
        "n_pass": n_pass,
        "n_fail": n_fail,
        "overall_pass": n_fail == 0,
        "audits": audits,
    }


def main():
    """Run the leakage audit on all 80 payloads."""
    print("=" * 72)
    print("DSB V1 — LEAKAGE AUDIT")
    print("=" * 72)
    print()

    result = audit_all_payloads()
    print(f"Payloads audited: {result['n_payloads']}")
    print(f"  PASS: {result['n_pass']}")
    print(f"  FAIL: {result['n_fail']}")
    print(f"  Overall: {'PASS' if result['overall_pass'] else 'FAIL'}")
    print()

    if not result["overall_pass"]:
        print("FAILURES:")
        for a in result["audits"]:
            if not a["overall_pass"]:
                print(f"  [{a['payload_id']}] severity={a['severity']}")
                for c in a["checks"]:
                    if not c["passed"]:
                        print(f"    {c['check']}: {c.get('violations', [])[:3]}")

    return result


if __name__ == "__main__":
    main()
