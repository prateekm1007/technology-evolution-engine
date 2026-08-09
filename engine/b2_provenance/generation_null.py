#!/usr/bin/env python3
"""b2_provenance/generation_null.py — Generation null (fair baseline).

Per B2_REVISION_R5_2.md (FATAL 1 fix) and B2_REVISION_R5_2.md (SERIOUS 1-3):

    The generation null is a FAIR baseline that:
    - Receives the same source pair as the engine
    - Shares the same extraction/abstraction prefix
    - Produces candidates in the SAME schema (including a mechanism)
    - Has the same candidate budget (exactly 3, rank-paired)
    - Does NOT use CrossDomainTransferEngine or HypothesisGenerationEngine
    - CAN pass Gate A/C/B (unlike the old retrieval null)

    ENGINE:     extraction → abstraction → TRANSFER → GENERATION → candidate
    NULL:       extraction → abstraction → CONCATENATION → candidate

    They differ ONLY in the downstream generation mechanism.

The null produces raw output in the parser format (---CANDIDATE--- delimiters)
so it goes through the SAME provenance spine as the engine:
    raw output → content-addressed blob → frozen parser → candidate(rank) →
    candidate SHA → derivation verification → append-only ledger

IMMUTABILITY:
    The null's raw output is stored via content-addressed storage BEFORE
    any human sees it. The generation is recorded in an immutable
    CANDIDATE_GENERATED ledger event. No researcher may select, rewrite,
    or discard null candidates.

UNIVERSAL SEED (per B2_IMPLEMENTATION_INVARIANTS.md):
    seed = SHA256(preregistration_id || case_id || "downstream")
    This is the SAME seed the engine uses for downstream generation.
    arm_id is NOT part of the seed → strictest paired counterfactual.
"""
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from .content_addressed_storage import store_raw_output, compute_sha256
from .frozen_parser import (
    parse_candidates,
    get_candidate_by_rank,
    compute_candidate_sha256,
    verify_derivation,
    PARSER_CONFIG,
)
from .provenance_ledger import ProvenanceLedger


# --------------------------------------------------------------------
# Frozen configuration for the null generation procedure.
# Any change requires a new preregistration amendment and SHA-256.
# --------------------------------------------------------------------
NULL_CONFIG = {
    "n_candidates": 3,  # Exactly 3 (R5.2 SERIOUS 1 fix)
    "candidate_delimiter": PARSER_CONFIG["candidate_delimiter"],
    "relationship_template": "{a_abstraction} is related to {b_abstraction}",
    "mechanism_template_with_shared": (
        "Both involve {shared_entity}. "
        "{a_abstraction} occurs in domain A. "
        "{b_abstraction} occurs in domain B. "
        "They may be connected through {shared_entity}."
    ),
    "mechanism_template_no_shared": (
        "Both domains involve related phenomena. "
        "{a_abstraction} occurs in domain A. "
        "{b_abstraction} occurs in domain B. "
        "No shared entity was identified."
    ),
}


def compute_universal_seed(preregistration_id: str, case_id: str,
                            stage_id: str = "downstream") -> str:
    """Compute the universal invocation seed.

    Per B2_IMPLEMENTATION_INVARIANTS.md:
        seed = SHA256(preregistration_id || case_id || stage_id)

    arm_id is NOT included → same seed for engine and null for the
    same case+stage. This is the strictest paired counterfactual.

    Args:
        preregistration_id: the frozen protocol SHA
        case_id: e.g., "CASE-001"
        stage_id: "downstream" for generation (default)

    Returns:
        64-character hex string (SHA-256)
    """
    data = f"{preregistration_id}|{case_id}|{stage_id}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_shared_entity(abstraction_a: str, abstraction_b: str) -> Optional[str]:
    """Deterministically compute the shared entity/concept between two abstractions.

    Per B2_REVISION_R5_2.md (SERIOUS 3 fix):
        shared_entity = FirstEntity(SortedIntersection(
            Entities(A), Entities(B), StopwordList, EntityDictionary))

    This is a SIMPLIFIED deterministic implementation for the initial
    implementation. The full implementation will use:
    - spaCy en_core_web_sm for NER
    - Frozen canonicalization (lowercase → strip punctuation → singularize)
    - NLTK English stopword list
    - Preregistered entity dictionary

    For now, this uses a simple token-based intersection to establish
    the deterministic pipeline. The NER/dictionary components will be
    integrated in a follow-up implementation step.

    Args:
        abstraction_a: abstracted mechanism text from domain A
        abstraction_b: abstracted mechanism text from domain B

    Returns:
        The shared entity string, or None if no shared entity found.
    """
    # Frozen stopword set (simplified — will be replaced by NLTK list)
    STOPWORDS = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "dare", "ought", "used", "this", "that", "these",
        "those", "i", "you", "he", "she", "it", "we", "they", "what",
        "which", "who", "when", "where", "why", "how", "all", "each",
        "every", "both", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "just", "also", "through", "into", "out", "up", "down",
        "about", "above", "below", "over", "under", "again", "further",
        "then", "once", "here", "there", "both", "each", "its", "their",
        "his", "her", "our", "your", "my", "me", "him", "them", "us",
    })

    # Canonicalize: lowercase, strip punctuation, split into tokens
    def canonicalize_tokens(text: str) -> List[str]:
        """Extract canonical tokens from text."""
        # Lowercase
        text = text.lower()
        # Strip punctuation (keep only alphanumeric and spaces)
        cleaned = ""
        for ch in text:
            if ch.isalnum() or ch.isspace():
                cleaned += ch
            else:
                cleaned += " "
        # Split into tokens
        tokens = cleaned.split()
        # Filter: length >= 4, not a stopword
        return [t for t in tokens if len(t) >= 4 and t not in STOPWORDS]

    tokens_a = set(canonicalize_tokens(abstraction_a))
    tokens_b = set(canonicalize_tokens(abstraction_b))

    # Intersection
    intersection = tokens_a & tokens_b

    if not intersection:
        return None

    # Sort alphabetically (deterministic tie-break)
    sorted_intersection = sorted(intersection)

    # Return first entity
    return sorted_intersection[0]


def construct_candidate(abstraction_a: str, abstraction_b: str) -> str:
    """Construct a single null candidate from two abstractions.

    The candidate is in the common schema:
        relationship: "<A> is related to <B>"
        mechanism: "Both involve <shared>. <A> occurs in domain A. ..."

    The candidate text combines relationship and mechanism into a
    single string that the parser can extract.

    Args:
        abstraction_a: abstracted mechanism from domain A
        abstraction_b: abstracted mechanism from domain B

    Returns:
        The candidate text string.
    """
    shared_entity = compute_shared_entity(abstraction_a, abstraction_b)

    relationship = NULL_CONFIG["relationship_template"].format(
        a_abstraction=abstraction_a,
        b_abstraction=abstraction_b,
    )

    if shared_entity is not None:
        mechanism = NULL_CONFIG["mechanism_template_with_shared"].format(
            shared_entity=shared_entity,
            a_abstraction=abstraction_a,
            b_abstraction=abstraction_b,
        )
    else:
        mechanism = NULL_CONFIG["mechanism_template_no_shared"].format(
            a_abstraction=abstraction_a,
            b_abstraction=abstraction_b,
        )

    # Combine into candidate text
    candidate = f"RELATIONSHIP: {relationship}\nMECHANISM: {mechanism}"
    return candidate


def generate_null_raw_output(
    abstracted_mechanisms_a: List[str],
    abstracted_mechanisms_b: List[str],
) -> str:
    """Generate the null's raw output containing exactly 3 candidates.

    Per B2_REVISION_R5_2.md (SERIOUS 1 fix):
        Candidate 1 = (A1, B1) — top-ranked from each
        Candidate 2 = (A2, B2) — second-ranked from each
        Candidate 3 = (A3, B3) — third-ranked from each

    Per B2_IMPLEMENTATION_INVARIANTS.md (Invariant 2):
        If abstraction lists are empty → NULL_GENERATION_FAILURE

    The raw output is in parser format (---CANDIDATE--- delimiters)
    so it goes through the SAME provenance spine as the engine.

    Args:
        abstracted_mechanisms_a: ranked list of abstractions from domain A
        abstracted_mechanisms_b: ranked list of abstractions from domain B

    Returns:
        Raw output string with 3 candidates separated by delimiters.

    Raises:
        ValueError: (NULL_GENERATION_FAILURE) if either abstraction
                    list is empty (fail-closed, no fabricated candidates).
    """
    # Fail-closed: empty abstractions
    if not abstracted_mechanisms_a or not abstracted_mechanisms_b:
        raise ValueError(
            "NULL_GENERATION_FAILURE: NO_REQUIRED_ABSTRACTION. "
            f"abstraction_a has {len(abstracted_mechanisms_a)} entries, "
            f"abstraction_b has {len(abstracted_mechanisms_b)} entries. "
            f"Cannot generate null candidates without abstractions. "
            f"The case fails closed — no fabricated candidates."
        )

    delimiter = NULL_CONFIG["candidate_delimiter"]
    n_candidates = NULL_CONFIG["n_candidates"]

    # Rank-paired candidate generation with deterministic padding
    candidates = []
    for rank in range(n_candidates):
        # Get abstraction at this rank, with padding if needed
        a_idx = min(rank, len(abstracted_mechanisms_a) - 1)
        b_idx = min(rank, len(abstracted_mechanisms_b) - 1)
        abstraction_a = abstracted_mechanisms_a[a_idx]
        abstraction_b = abstracted_mechanisms_b[b_idx]

        candidate = construct_candidate(abstraction_a, abstraction_b)
        candidates.append(candidate)

    # Build raw output in parser format
    preamble = "---NULL GENERATION OUTPUT---\n"
    parts = [preamble]
    for candidate in candidates:
        parts.append(delimiter)
        parts.append(candidate)
        parts.append("\n")

    raw_output = "".join(parts)
    return raw_output


class NullGenerationResult:
    """Result of null generation for a single case.

    Contains the raw output, candidate list, and provenance information.
    """

    def __init__(
        self,
        case_id: str,
        raw_output: str,
        raw_output_sha256: str,
        raw_output_blob_path: str,
        candidates: List[str],
        candidate_sha256s: List[str],
        invocation_seed: str,
    ):
        self.case_id = case_id
        self.raw_output = raw_output
        self.raw_output_sha256 = raw_output_sha256
        self.raw_output_blob_path = raw_output_blob_path
        self.candidates = candidates
        self.candidate_sha256s = candidate_sha256s
        self.invocation_seed = invocation_seed

    def n_candidates(self) -> int:
        return len(self.candidates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "raw_output_sha256": self.raw_output_sha256,
            "raw_output_blob_path": self.raw_output_blob_path,
            "n_candidates": self.n_candidates(),
            "candidate_sha256s": self.candidate_sha256s,
            "invocation_seed": self.invocation_seed,
        }


def generate_null_candidates(
    case_id: str,
    abstracted_mechanisms_a: List[str],
    abstracted_mechanisms_b: List[str],
    preregistration_id: str,
) -> NullGenerationResult:
    """Generate null candidates and store them through the provenance spine.

    This is the main entry point for null generation. It:
    1. Computes the universal seed (same as engine)
    2. Generates the raw output (3 rank-paired candidates)
    3. Stores the raw output in content-addressed storage
    4. Parses candidates with the frozen parser
    5. Computes candidate SHA-256s
    6. Returns a NullGenerationResult with all provenance info

    The caller is responsible for appending the CANDIDATE_GENERATED
    events to the provenance ledger.

    Args:
        case_id: e.g., "CASE-001"
        abstracted_mechanisms_a: ranked abstractions from domain A
        abstracted_mechanisms_b: ranked abstractions from domain B
        preregistration_id: the frozen protocol SHA

    Returns:
        NullGenerationResult with raw output, candidates, and provenance.

    Raises:
        ValueError: if abstractions are empty (NULL_GENERATION_FAILURE).
    """
    # 1. Compute universal seed (same as engine)
    seed = compute_universal_seed(preregistration_id, case_id, "downstream")

    # 2. Generate raw output (3 rank-paired candidates)
    raw_output = generate_null_raw_output(
        abstracted_mechanisms_a, abstracted_mechanisms_b
    )

    # 3. Store raw output in content-addressed storage
    blob_path, raw_sha = store_raw_output(case_id, "null", raw_output)

    # 4. Parse candidates with the frozen parser
    candidates = parse_candidates(raw_output)

    # 5. Compute candidate SHA-256s
    candidate_sha256s = [
        compute_sha256(c.encode("utf-8")) for c in candidates
    ]

    return NullGenerationResult(
        case_id=case_id,
        raw_output=raw_output,
        raw_output_sha256=raw_sha,
        raw_output_blob_path=blob_path,
        candidates=candidates,
        candidate_sha256s=candidate_sha256s,
        invocation_seed=seed,
    )


def record_null_in_ledger(
    ledger: ProvenanceLedger,
    result: NullGenerationResult,
    engine_version: str,
    provider: str,
    model: str,
    prompt_hash: str,
    source_pair_sha256: str,
    generation_timestamp: str,
) -> List[Dict[str, Any]]:
    """Record null candidates in the provenance ledger.

    Creates a CANDIDATE_GENERATED event for each null candidate.
    These events are immutable and linked in the hash chain.

    Args:
        ledger: the provenance ledger
        result: the NullGenerationResult from generate_null_candidates
        engine_version: git commit SHA of the null generation code
        provider: "ZAI" (same as engine)
        model: "glm-4-plus" (same as engine)
        prompt_hash: SHA-256 of the frozen null prompt
        source_pair_sha256: SHA-256 of (source_a, source_b)
        generation_timestamp: ISO 8601 timestamp

    Returns:
        List of created ledger entries.
    """
    entries = []
    for rank, (candidate, candidate_sha) in enumerate(
        zip(result.candidates, result.candidate_sha256s), start=1
    ):
        entry = ledger.append_candidate_entry(
            case_id=result.case_id,
            arm="null",
            candidate_rank=rank,
            raw_output_sha256=result.raw_output_sha256,
            raw_output_blob_path=result.raw_output_blob_path,
            candidate_sha256=candidate_sha,
            candidate_text=candidate,
            generation_timestamp=generation_timestamp,
            engine_version=engine_version,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            source_pair_sha256=source_pair_sha256,
            invocation_seed=result.invocation_seed,
        )
        entries.append(entry)
    return entries
