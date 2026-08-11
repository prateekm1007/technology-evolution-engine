"""
custodian.intake.src.exposure_detector — TEE prior-exposure detection.

For every candidate source, classify whether TEE has previously seen it:
    UNSEEN         — no trace found in TEE artifacts
    POSSIBLY_SEEN  — partial match found (e.g., similar title, shared terms)
    KNOWN_SEEN     — exact match found in TEE artifacts
    UNDETERMINABLE — cannot determine (e.g., search index unavailable)

The custodian decides eligibility. This module flags, does not decide.
"""
import hashlib
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ExposureStatus(Enum):
    """TEE prior-exposure status.

    IMPORTANT: UNSEEN means 'No exposure was detected within the defined
    evidence universe.' It does NOT mean 'TEE has never encountered this
    information.' The evidence universe is finite and may be incomplete.
    """
    UNSEEN = "UNSEEN"  # No exposure detected within the checked evidence universe
    POSSIBLY_SEEN = "POSSIBLY_SEEN"  # Partial match found (similar content, shared terms)
    KNOWN_SEEN = "KNOWN_SEEN"  # Exact match found in checked TEE artifacts
    UNDETERMINABLE = "UNDETERMINABLE"  # Cannot determine (e.g., search index unavailable)


@dataclass
class ExposureResult:
    """Result of TEE prior-exposure check for one source.

    IMPORTANT: 'UNSEEN' means no exposure was detected within the checked
    evidence universe (checked_locations). It does NOT mean TEE has never
    encountered this information. The evidence universe is finite.
    """
    source_id: str
    content_hash: str
    status: ExposureStatus
    evidence: List[str] = field(default_factory=list)
    checked_locations: List[str] = field(default_factory=list)
    evidence_universe_disclaimer: str = "UNSEEN means no exposure detected within the checked evidence universe, NOT that TEE has never encountered this information."

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "content_hash": self.content_hash,
            "status": self.status.value,
            "status_disclaimer": self.evidence_universe_disclaimer,
            "evidence": self.evidence,
            "checked_locations": self.checked_locations,
        }


def _hash_file(filepath: Path) -> Optional[str]:
    """Hash a file's content. Returns None if file doesn't exist."""
    if not filepath.exists():
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _hash_string(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def check_tee_exposure(
    source_id: str,
    content: str,
    content_hash: str,
    tee_artifact_paths: List[Path],
    tee_corpus_hashes: Optional[Set[str]] = None,
    tee_known_phrases: Optional[List[str]] = None,
) -> ExposureResult:
    """Check whether TEE has previously seen this source material.

    Args:
        source_id: ID of the source being checked
        content: Full text content of the source
        content_hash: SHA-256 of the content
        tee_artifact_paths: List of file paths to check (TEE worklogs, outputs, etc.)
        tee_corpus_hashes: Set of known content hashes in TEE's corpus
        tee_known_phrases: List of phrases known to appear in TEE outputs

    Returns:
        ExposureResult with status and evidence
    """
    result = ExposureResult(
        source_id=source_id,
        content_hash=content_hash,
        status=ExposureStatus.UNSEEN,
    )

    # 1. Check exact content hash against TEE corpus hashes
    if tee_corpus_hashes:
        result.checked_locations.append("tee_corpus_hashes")
        if content_hash in tee_corpus_hashes:
            result.status = ExposureStatus.KNOWN_SEEN
            result.evidence.append(f"EXACT_HASH_MATCH: content hash {content_hash[:16]}... found in TEE corpus")
            return result

    # 2. Check TEE artifact files for exact content hash
    for path in tee_artifact_paths:
        result.checked_locations.append(str(path))
        if not path.exists():
            continue

        # Check if the hash appears in the file (e.g., in a manifest or log)
        try:
            with open(path, 'r', errors='ignore') as f:
                file_content = f.read()

            if content_hash in file_content:
                result.status = ExposureStatus.KNOWN_SEEN
                result.evidence.append(f"HASH_IN_FILE: {content_hash[:16]}... found in {path}")
                return result

            # Check for content overlap (first 200 chars as fingerprint)
            content_fingerprint = content[:200].strip()
            if content_fingerprint and content_fingerprint in file_content:
                result.status = ExposureStatus.KNOWN_SEEN
                result.evidence.append(f"CONTENT_OVERLAP: first 200 chars found in {path}")
                return result
        except Exception:
            result.checked_locations.append(f"{path} (read error)")

    # 3. Check for known TEE phrases in the source content
    if tee_known_phrases:
        result.checked_locations.append("tee_known_phrases")
        content_lower = content.lower()
        matches = []
        for phrase in tee_known_phrases:
            if phrase.lower() in content_lower:
                matches.append(phrase)

        if matches:
            if result.status == ExposureStatus.UNSEEN:
                result.status = ExposureStatus.POSSIBLY_SEEN
            result.evidence.append(f"KNOWN_PHRASE_MATCH: found {len(matches)} TEE phrases: {matches[:5]}")

    # 4. If we checked everything and found nothing
    if result.status == ExposureStatus.UNSEEN and not result.evidence:
        result.evidence.append("No traces found in checked TEE artifacts")

    return result
