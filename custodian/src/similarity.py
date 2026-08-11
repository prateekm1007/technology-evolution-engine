"""
custodian.src.similarity — Near-duplicate detection for benchmark cases.

This is a REVIEW FLAG system, not an automatic scientific truth oracle.
It flags potential duplicates for custodian adjudication.

HARDENING #2-3: Near-duplicate detection + scientific independence.
"""
import re
from dataclasses import dataclass
from typing import List, Set, Tuple
from difflib import SequenceMatcher


@dataclass
class SimilarityFlag:
    """A flagged potential duplicate between two cases."""
    case_a: str
    case_b: str
    similarity_type: str  # "input_material", "problem", "high_jaccard"
    score: float


def _tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase word tokens."""
    return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _sequence_similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_near_duplicates(cases, similarity_threshold: float = 0.8) -> List[SimilarityFlag]:
    """Detect potential near-duplicates among cases.

    Flags cases that have:
    - High input_material similarity (Jaccard on tokens)
    - High problem text similarity (SequenceMatcher)
    - Identical source_id (same underlying source)

    These are REVIEW FLAGS, not blocking errors. The custodian must
    adjudicate whether flagged pairs are genuinely independent.

    Args:
        cases: List of BenchmarkCase objects
        similarity_threshold: Jaccard/sequence ratio above which to flag (default 0.8)

    Returns:
        List of SimilarityFlag objects
    """
    flags = []

    # Pre-compute token sets for input_material
    case_tokens = []
    for c in cases:
        source_a = c.input_material.get("source_a", "")
        source_b = c.input_material.get("source_b", "")
        combined = source_a + " " + source_b
        case_tokens.append(_tokenize(combined))

    # Compare all pairs
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            ci = cases[i]
            cj = cases[j]

            # Skip same independence_group (already caught by validator)
            if ci.independence_group == cj.independence_group:
                continue

            # Check input_material Jaccard similarity
            jac = _jaccard_similarity(case_tokens[i], case_tokens[j])
            if jac >= similarity_threshold:
                flags.append(SimilarityFlag(
                    case_a=ci.case_id,
                    case_b=cj.case_id,
                    similarity_type="input_material_jaccard",
                    score=jac,
                ))

            # Check problem text similarity
            prob_sim = _sequence_similarity(ci.problem, cj.problem)
            if prob_sim >= similarity_threshold:
                flags.append(SimilarityFlag(
                    case_a=ci.case_id,
                    case_b=cj.case_id,
                    similarity_type="problem_text",
                    score=prob_sim,
                ))

            # Check same source_id (different independence_group but same source)
            if ci.source_id == cj.source_id:
                flags.append(SimilarityFlag(
                    case_a=ci.case_id,
                    case_b=cj.case_id,
                    similarity_type="same_source_id",
                    score=1.0,
                ))

    return flags
