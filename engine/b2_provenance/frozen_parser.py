#!/usr/bin/env python3
"""b2_provenance/frozen_parser.py — Frozen mechanical parser for candidate extraction.

Per B2_REVISION_R5_1.md (FATAL 2 fix):

    The parser must be:
    - Deterministic (no RNG, no LLM, no network calls)
    - Source code SHA-256 committed
    - Configuration SHA-256 committed
    - Version recorded in every provenance entry

The derivation invariant is:
    SHA256(FrozenParser(raw_output, parser_config).candidate(rank))
    ==
    candidate_sha256

This module provides:
    - parse_candidates(raw_output) -> list of candidate texts
    - get_parser_sha256() -> SHA-256 of this source file
    - get_parser_config_sha256() -> SHA-256 of the parser configuration
    - verify_derivation(raw_output_sha256, parser_sha256, parser_config_sha256,
                         candidate_rank, candidate_sha256) -> bool

The parser is intentionally simple: it expects the raw output to contain
candidates in a structured format (one candidate per section, marked by
delimiters). The exact format is frozen in PARSER_CONFIG.
"""
import hashlib
import re
from pathlib import Path
from typing import List, Optional


# --------------------------------------------------------------------
# Parser configuration (FROZEN).
#
# The configuration defines:
# - The delimiter that separates candidates in the raw output
# - The maximum number of candidates to extract (K=3 per R5.2)
# - Minimum and maximum candidate text length
#
# Any change to this configuration requires a new preregistration
# amendment and a new SHA-256.
# --------------------------------------------------------------------
PARSER_CONFIG = {
    "candidate_delimiter": "---CANDIDATE---",
    "max_candidates": 3,
    "min_candidate_length": 10,
    "max_candidate_length": 10000,
    "encoding": "utf-8",
}

# The parser source file path (for SHA-256 computation).
PARSER_SOURCE_PATH = Path(__file__).resolve()


def get_parser_sha256() -> str:
    """Compute SHA-256 of this parser's source code.

    This is the parser version identifier. It is recorded in every
    provenance entry. If the parser source changes, this hash changes,
    and all provenance entries must be re-evaluated.
    """
    source_bytes = PARSER_SOURCE_PATH.read_bytes()
    return hashlib.sha256(source_bytes).hexdigest()


def get_parser_config_sha256() -> str:
    """Compute SHA-256 of the parser configuration.

    The configuration is serialized as a canonical JSON string
    (sorted keys, compact separators) and hashed.
    """
    import json
    config_str = json.dumps(PARSER_CONFIG, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(config_str.encode("utf-8")).hexdigest()


def get_parser_version() -> dict:
    """Return the full parser version information."""
    return {
        "parser_sha256": get_parser_sha256(),
        "parser_config_sha256": get_parser_config_sha256(),
        "parser_source_path": str(PARSER_SOURCE_PATH),
        "parser_config": PARSER_CONFIG.copy(),
    }


def parse_candidates(raw_output: str) -> List[str]:
    """Parse candidates from raw engine/null output.

    The parser is DETERMINISTIC:
    - No RNG
    - No LLM calls
    - No network calls
    - No external state
    - Same input always produces same output

    The raw output is expected to contain candidates separated by
    PARSER_CONFIG["candidate_delimiter"]. The first
    PARSER_CONFIG["max_candidates"] eligible candidates are returned.

    A candidate is "eligible" if:
    - It is non-empty after stripping whitespace
    - Its length is between min_candidate_length and max_candidate_length

    Args:
        raw_output: the raw output string from the engine or null

    Returns:
        List of candidate text strings (at most max_candidates).

    Raises:
        ValueError: if raw_output is empty.
    """
    if not raw_output:
        raise ValueError("Cannot parse candidates from empty raw output")

    delimiter = PARSER_CONFIG["candidate_delimiter"]
    max_candidates = PARSER_CONFIG["max_candidates"]
    min_len = PARSER_CONFIG["min_candidate_length"]
    max_len = PARSER_CONFIG["max_candidate_length"]

    # Split by delimiter.
    parts = raw_output.split(delimiter)

    # The first part (before the first delimiter) is preamble, skip it.
    # Subsequent parts are candidate text.
    candidates = []
    for part in parts[1:]:  # skip preamble
        candidate = part.strip()
        if not candidate:
            continue
        if len(candidate) < min_len:
            continue
        if len(candidate) > max_len:
            # Per audit round 46 (SERIOUS): reject overlong candidates
            # rather than truncating. Truncation silently modifies the
            # candidate before hashing, creating a provenance ambiguity.
            # The parser must NOT transform candidates — it only selects
            # eligible ones. Overlong candidates are INELIGIBLE and skipped.
            # The parser continues looking for the next eligible candidate.
            continue
        candidates.append(candidate)
        if len(candidates) >= max_candidates:
            break

    return candidates


def get_candidate_by_rank(raw_output: str, rank: int) -> Optional[str]:
    """Get the candidate at the given rank (1-indexed) from raw output.

    Args:
        raw_output: the raw output string
        rank: 1-indexed candidate rank (1, 2, or 3)

    Returns:
        The candidate text, or None if no candidate at that rank.
    """
    if rank < 1:
        return None
    candidates = parse_candidates(raw_output)
    if rank > len(candidates):
        return None
    return candidates[rank - 1]


def compute_candidate_sha256(raw_output: str, rank: int) -> Optional[str]:
    """Compute the SHA-256 of the candidate at the given rank.

    This is the core of the derivation invariant:
        SHA256(FrozenParser(raw_output).candidate(rank)) == candidate_sha256

    Args:
        raw_output: the raw output string
        rank: 1-indexed candidate rank

    Returns:
        The SHA-256 of the candidate text, or None if no candidate at that rank.
    """
    candidate = get_candidate_by_rank(raw_output, rank)
    if candidate is None:
        return None
    return hashlib.sha256(candidate.encode("utf-8")).hexdigest()


def verify_derivation(
    raw_output: str,
    expected_candidate_sha256: str,
    rank: int,
    expected_parser_sha256: Optional[str] = None,
    expected_parser_config_sha256: Optional[str] = None,
) -> bool:
    """Verify that a candidate was deterministically derived from raw output.

    The derivation invariant:
        SHA256(FrozenParser(raw_output, config).candidate(rank))
        ==
        expected_candidate_sha256

    Additionally, if expected_parser_sha256 and expected_parser_config_sha256
    are provided, verify that the current parser matches the expected version.

    Args:
        raw_output: the raw output string
        expected_candidate_sha256: the expected SHA-256 of the candidate
        rank: 1-indexed candidate rank
        expected_parser_sha256: if provided, verify parser source matches
        expected_parser_config_sha256: if provided, verify parser config matches

    Returns:
        True if derivation is verified.

    Raises:
        AssertionError: if derivation fails or parser version mismatches.
    """
    # Verify parser version if expected hashes are provided.
    if expected_parser_sha256 is not None:
        actual_parser_sha = get_parser_sha256()
        assert actual_parser_sha == expected_parser_sha256, (
            f"Parser version mismatch: expected {expected_parser_sha256[:16]}..., "
            f"got {actual_parser_sha[:16]}... The parser source has changed "
            f"since the provenance entry was created."
        )

    if expected_parser_config_sha256 is not None:
        actual_config_sha = get_parser_config_sha256()
        assert actual_config_sha == expected_parser_config_sha256, (
            f"Parser config mismatch: expected {expected_parser_config_sha256[:16]}..., "
            f"got {actual_config_sha[:16]}... The parser configuration has changed."
        )

    # Compute the candidate hash from the raw output.
    actual_candidate_sha = compute_candidate_sha256(raw_output, rank)
    if actual_candidate_sha is None:
        raise AssertionError(
            f"Derivation verification FAILED: no candidate at rank {rank} "
            f"in the raw output."
        )

    assert actual_candidate_sha == expected_candidate_sha256, (
        f"Derivation verification FAILED: candidate at rank {rank} has hash "
        f"{actual_candidate_sha[:16]}... but expected "
        f"{expected_candidate_sha256[:16]}... The candidate was NOT "
        f"deterministically derived from this raw output."
    )

    return True
