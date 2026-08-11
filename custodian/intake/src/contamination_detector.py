"""
custodian.intake.src.contamination_detector — Benchmark/answer-key contamination detection.

Searches for:
- answer-key-like material (ground_truth, expected_mechanism, etc.)
- existing hypothesis/solution language
- benchmark identifiers (DXP-, HO-, ADV-)
- known TEE outputs
- duplicated source pairs
- near-duplicate documents
- papers that explicitly discuss the intended bridge
- metadata revealing the intended relationship

Flags, does not discard. The custodian needs the complete audit trail.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class ContaminationLevel(Enum):
    CLEAN = "CLEAN"
    FLAGGED = "FLAGGED"
    CONTAMINATED = "CONTAMINATED"


@dataclass
class ContaminationResult:
    """Result of contamination check for one source."""
    source_id: str
    level: ContaminationLevel
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "level": self.level.value,
            "flags": self.flags,
        }


# Patterns that indicate answer-key leakage
ANSWER_KEY_PATTERNS = [
    r'ground_truth\s*[:=]',
    r'expected_mechanism\s*[:=]',
    r'expected_label\s*[:=]',
    r'expected_direction\s*[:=]',
    r'expected_magnitude\s*[:=]',
    r'falsifier\s*[:=]',
    r'causal_variable\s*[:=]',
    r'answer_key',
    r'reference_solution',
    r'verification_key',
]

# Benchmark identifiers that indicate leakage
BENCHMARK_ID_PATTERNS = [
    r'DXP-\d+',
    r'HO-\d+',
    r'ADV-\d+',
    r'SENT-\d+',
    r'TEE-BENCHMARK',
]

# Hypothesis/solution language patterns
HYPOTHESIS_PATTERNS = [
    r'the mechanism (is|involves|consists of)',
    r'the correct (hypothesis|answer|mechanism)',
    r'the expected (prediction|outcome|result)',
    r'this (is|represents) a (genuine|correct|true) cross-source',
    r'the transfer (is|should be)',
    r'hypothesis\s*:\s*h-\d+',
]

# Metadata revealing intended relationship
RELATIONSHIP_REVEAL_PATTERNS = [
    r'source_a.*source_b.*transfer',
    r'bridge\s+between.*source',
    r'intended.*(connection|bridge|transfer)',
    r'expected.*cross-domain',
    r'should.*discover',
    r'tee.*(should|expected|will).*(find|discover|generate)',
]


def check_contamination(
    source_id: str,
    content: str,
    known_tee_outputs: Optional[List[str]] = None,
) -> ContaminationResult:
    """Check source content for benchmark/answer-key contamination.

    Args:
        source_id: ID of the source being checked
        content: Full text content of the source
        known_tee_outputs: List of known TEE output strings to search for

    Returns:
        ContaminationResult with level and flags
    """
    result = ContaminationResult(
        source_id=source_id,
        level=ContaminationLevel.CLEAN,
    )

    content_lower = content.lower()

    # 1. Check for answer-key-like material
    for pattern in ANSWER_KEY_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result.flags.append(f"ANSWER_KEY_PATTERN: '{pattern}' found {len(matches)} time(s)")
            result.level = ContaminationLevel.CONTAMINATED

    # 2. Check for benchmark identifiers
    for pattern in BENCHMARK_ID_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result.flags.append(f"BENCHMARK_IDENTIFIER: '{matches[0]}' found in content")
            result.level = ContaminationLevel.CONTAMINATED

    # 3. Check for hypothesis/solution language
    for pattern in HYPOTHESIS_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result.flags.append(f"HYPOTHESIS_LANGUAGE: '{pattern}' found")
            if result.level == ContaminationLevel.CLEAN:
                result.level = ContaminationLevel.FLAGGED

    # 4. Check for relationship-revealing metadata
    for pattern in RELATIONSHIP_REVEAL_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result.flags.append(f"RELATIONSHIP_REVEAL: '{pattern}' found")
            if result.level == ContaminationLevel.CLEAN:
                result.level = ContaminationLevel.FLAGGED

    # 5. Check for known TEE outputs in the content
    if known_tee_outputs:
        for tee_output in known_tee_outputs:
            if tee_output and tee_output.lower() in content_lower:
                result.flags.append(f"TEE_OUTPUT_FOUND: '{tee_output[:50]}...' in content")
                result.level = ContaminationLevel.CONTAMINATED

    # 6. Check for explicit bridge discussion
    bridge_patterns = [
        r'this paper (shows|demonstrates|proves) that.*can be applied to',
        r'we (apply|transfer|adapt).*from.*to',
        r'biomimetic.*application',
        r'bioinspired.*design',
    ]
    for pattern in bridge_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            result.flags.append(f"EXPLICIT_BRIDGE_DISCUSSION: '{pattern}' found")
            if result.level == ContaminationLevel.CLEAN:
                result.level = ContaminationLevel.FLAGGED

    if result.level == ContaminationLevel.CLEAN and not result.flags:
        result.flags.append("No contamination indicators found")

    return result
