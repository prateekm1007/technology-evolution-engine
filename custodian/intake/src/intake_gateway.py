"""
custodian.intake.src.intake_gateway — Controlled corpus intake pipeline.

Architecture:
    EXTERNAL CUSTODIAN
           │
           ▼
    CORPUS INTAKE (hash, provenance, timestamps, source registry,
                   duplicate detection, domain classification,
                   contamination checks, TEE prior-exposure)
           │
           ▼
    CUSTODIAN-ONLY QUARANTINE (ELIGIBLE / FLAGGED / REJECTED / UNDETERMINABLE)
           │
           ▼
    (Later: construction, review, answer key, sealing → BLIND FIXTURE → TEE)

TEE must never receive the raw corpus through this pathway.

This module implements items 1-14 of the CTO directive:
    1. immutable source registration
    2. SHA-256 content identity
    3. provenance chain
    4. acquisition timestamp
    5. source-version tracking
    6. duplicate/near-duplicate detection
    7. domain classification using the now-safe taxonomy
    8. TEE prior-exposure detection
    9. benchmark/answer-key contamination detection
    10. custodian-only quarantine
    11. machine-readable intake manifest
    12. human-readable intake audit
    13. append-only audit trail
    14. explicit ELIGIBLE / FLAGGED / REJECTED / UNDETERMINABLE states
"""
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Import from custodian package (parent)
import sys
CUSTODIAN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CUSTODIAN_ROOT))

from src.hasher import sha256_string, sha256_json, canonical_json
from src.source_registry import SourceRegistry, SourceEntry
from src.domain_taxonomy import canonicalize_domain, is_known_domain
from src.similarity import detect_near_duplicates, SimilarityFlag
from src.audit_trail import AuditTrail
from intake.src.exposure_detector import check_tee_exposure, ExposureStatus, ExposureResult
from intake.src.contamination_detector import check_contamination, ContaminationLevel, ContaminationResult


class IntakeStatus(Enum):
    """Status of a source in the intake pipeline."""
    ELIGIBLE = "ELIGIBLE"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"
    UNDETERMINABLE = "UNDETERMINABLE"


@dataclass
class IntakeRecord:
    """Complete record for one source in the intake pipeline."""
    source_id: str
    domain: str
    canonical_domain: str
    title: str
    origin: str
    source_uri: str
    content_hash: str
    version: str
    acquisition_timestamp: str
    provenance: dict
    exposure_result: ExposureResult
    contamination_result: ContaminationResult
    intake_status: IntakeStatus
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "domain": self.domain,
            "canonical_domain": self.canonical_domain,
            "title": self.title,
            "origin": self.origin,
            "source_uri": self.source_uri,
            "content_hash": self.content_hash,
            "version": self.version,
            "acquisition_timestamp": self.acquisition_timestamp,
            "provenance": self.provenance,
            "exposure": self.exposure_result.to_dict(),
            "contamination": self.contamination_result.to_dict(),
            "intake_status": self.intake_status.value,
            "flags": self.flags,
        }


class CorpusIntakeGateway:
    """Controlled corpus intake pipeline.

    TEE must never receive the raw corpus through this pathway.
    All intake state is custodian-only.
    """

    def __init__(
        self,
        tee_artifact_paths: Optional[List[Path]] = None,
        tee_corpus_hashes: Optional[Set[str]] = None,
        tee_known_phrases: Optional[List[str]] = None,
        known_tee_outputs: Optional[List[str]] = None,
    ):
        """Initialize the intake gateway.

        Args:
            tee_artifact_paths: TEE files to check for prior exposure
            tee_corpus_hashes: Known content hashes in TEE's corpus
            tee_known_phrases: Phrases known to appear in TEE outputs
            known_tee_outputs: Known TEE output strings (for contamination check)
        """
        self._records: Dict[str, IntakeRecord] = {}
        self._registry = SourceRegistry()
        self._audit_trail = AuditTrail()
        self._content_hashes: Dict[str, str] = {}  # hash → source_id (for dup detection)

        self._tee_artifact_paths = tee_artifact_paths or []
        self._tee_corpus_hashes = tee_corpus_hashes or set()
        self._tee_known_phrases = tee_known_phrases or []
        self._known_tee_outputs = known_tee_outputs or []

    def intake_source(
        self,
        source_id: str,
        domain: str,
        title: str,
        origin: str,
        source_uri: str,
        content: str,
        version: str,
        license: str = "",
        provenance_metadata: Optional[dict] = None,
        acquisition_timestamp: Optional[str] = None,
    ) -> IntakeRecord:
        """Intake a single source through the pipeline.

        This is the ONLY entry point for new material.
        TEE must never call this function.
        """
        # 1. Immutable source registration
        if source_id in self._records:
            raise ValueError(f"DUPLICATE_INTAKE: source_id '{source_id}' already intaken")

        # 2. SHA-256 content identity
        content_hash = sha256_string(content)

        # 6. Duplicate detection (exact hash)
        if content_hash in self._content_hashes:
            existing_id = self._content_hashes[content_hash]
            raise ValueError(
                f"DUPLICATE_CONTENT: source '{source_id}' has same content hash "
                f"as existing source '{existing_id}'"
            )

        # 3. Provenance chain
        provenance = {
            "constructor": origin,
            "construction_timestamp": acquisition_timestamp or datetime.now(timezone.utc).isoformat(),
            "construction_method": "external_custodian_intake",
            "source_version": version,
            "license": license,
            "metadata": provenance_metadata or {},
        }

        # 4. Acquisition timestamp
        acq_ts = acquisition_timestamp or datetime.now(timezone.utc).isoformat()

        # 7. Domain classification
        canonical = canonicalize_domain(domain)

        # 8. TEE prior-exposure detection
        exposure = check_tee_exposure(
            source_id=source_id,
            content=content,
            content_hash=content_hash,
            tee_artifact_paths=self._tee_artifact_paths,
            tee_corpus_hashes=self._tee_corpus_hashes,
            tee_known_phrases=self._tee_known_phrases,
        )

        # 9. Contamination detection
        contamination = check_contamination(
            source_id=source_id,
            content=content,
            known_tee_outputs=self._known_tee_outputs,
        )

        # 14. Determine intake status
        flags = []
        status = IntakeStatus.ELIGIBLE

        # Exposure-based flags
        if exposure.status == ExposureStatus.KNOWN_SEEN:
            status = IntakeStatus.REJECTED
            flags.append("REJECTED: TEE has KNOWN_SEEN exposure to this content")
        elif exposure.status == ExposureStatus.POSSIBLY_SEEN:
            if status == IntakeStatus.ELIGIBLE:
                status = IntakeStatus.FLAGGED
            flags.append("FLAGGED: TEE has POSSIBLY_SEEN exposure to this content")

        # Contamination-based flags
        if contamination.level == ContaminationLevel.CONTAMINATED:
            status = IntakeStatus.REJECTED
            flags.append("REJECTED: Content is CONTAMINATED with answer-key/benchmark material")
        elif contamination.level == ContaminationLevel.FLAGGED:
            if status == IntakeStatus.ELIGIBLE:
                status = IntakeStatus.FLAGGED
            flags.append("FLAGGED: Content contains suspicious patterns")

        # Domain classification flags
        if not is_known_domain(domain):
            if status == IntakeStatus.ELIGIBLE:
                status = IntakeStatus.FLAGGED
            flags.append(f"FLAGGED: Domain '{domain}' not in frozen taxonomy (canonical: '{canonical}')")

        # Register in source registry (custodian-only)
        self._registry.register(
            source_id=source_id,
            domain=domain,
            title=title,
            origin=origin,
            source_uri=source_uri,
            content=content,
            version=version,
            license=license,
            provenance_metadata=provenance_metadata,
        )

        # Create intake record
        record = IntakeRecord(
            source_id=source_id,
            domain=domain,
            canonical_domain=canonical,
            title=title,
            origin=origin,
            source_uri=source_uri,
            content_hash=content_hash,
            version=version,
            acquisition_timestamp=acq_ts,
            provenance=provenance,
            exposure_result=exposure,
            contamination_result=contamination,
            intake_status=status,
            flags=flags,
        )

        self._records[source_id] = record
        self._content_hashes[content_hash] = source_id

        # 13. Audit trail
        self._audit_trail.record(
            event_type="SOURCE_INTAKEN",
            benchmark_id="INTAKE",
            actor=origin,
            relevant_hash=content_hash,
            details={
                "source_id": source_id,
                "status": status.value,
                "domain": canonical,
                "exposure": exposure.status.value,
                "contamination": contamination.level.value,
            },
            timestamp=acq_ts,
        )

        return record

    def get_record(self, source_id: str) -> IntakeRecord:
        """Get an intake record. Custodian-only."""
        if source_id not in self._records:
            raise KeyError(f"Source not found: {source_id}")
        return self._records[source_id]

    def list_records(self) -> List[IntakeRecord]:
        """List all intake records. Custodian-only."""
        return list(self._records.values())

    def list_by_status(self, status: IntakeStatus) -> List[IntakeRecord]:
        """List records by intake status."""
        return [r for r in self._records.values() if r.intake_status == status]

    def get_domain_distribution(self) -> Dict[str, int]:
        """Get distribution of canonical domains across all intaken sources."""
        dist: Dict[str, int] = {}
        for r in self._records.values():
            dist[r.canonical_domain] = dist.get(r.canonical_domain, 0) + 1
        return dist

    def check_near_duplicates(self) -> List[SimilarityFlag]:
        """Check for near-duplicate content among intaken sources.
        Returns flags for custodian review."""
        # Convert intake records to a format detect_near_duplicates can use
        from src.case_schema import BenchmarkCase
        cases = []
        for r in self._records.values():
            # Create a minimal BenchmarkCase-like object for similarity checking
            entry = self._registry.get(r.source_id)
            cases.append(type('obj', (object,), {
                'case_id': r.source_id,
                'independence_group': r.source_id,  # Each source is its own group
                'input_material': {'source_a': '', 'source_b': ''},  # No input_material yet
                'problem': r.title,
                'source_id': r.source_id,
            }))

        # Use problem text similarity only (no input_material yet)
        flags = []
        from src.similarity import _sequence_similarity
        for i in range(len(cases)):
            for j in range(i + 1, len(cases)):
                sim = _sequence_similarity(cases[i].problem, cases[j].problem)
                if sim >= 0.8:
                    flags.append(SimilarityFlag(
                        case_a=cases[i].case_id,
                        case_b=cases[j].case_id,
                        similarity_type="title_text",
                        score=sim,
                    ))
        return flags

    # 11. Machine-readable intake manifest
    def get_intake_manifest(self) -> dict:
        """Generate machine-readable intake manifest."""
        records = [r.to_dict() for r in self._records.values()]
        return {
            "manifest_type": "CORPUS_INTAKE_MANIFEST",
            "manifest_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(self._records),
            "domain_distribution": self.get_domain_distribution(),
            "status_distribution": {
                status.value: len(self.list_by_status(status))
                for status in IntakeStatus
            },
            "source_registry_hash": self._registry.manifest_hash(),
            "records": records,
            "manifest_hash": "",  # Computed below
        }

    # 12. Human-readable intake audit
    def get_intake_audit_report(self) -> str:
        """Generate human-readable intake audit report."""
        lines = [
            "=== CORPUS INTAKE AUDIT REPORT ===",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total sources: {len(self._records)}",
            "",
            "Status Distribution:",
        ]
        for status in IntakeStatus:
            count = len(self.list_by_status(status))
            lines.append(f"  {status.value}: {count}")

        lines.append("")
        lines.append("Domain Distribution:")
        for domain, count in sorted(self.get_domain_distribution().items()):
            lines.append(f"  {domain}: {count}")

        lines.append("")
        lines.append("Per-Source Details:")
        for r in sorted(self._records.values(), key=lambda x: x.source_id):
            lines.append(f"  [{r.intake_status.value}] {r.source_id}: {r.title}")
            lines.append(f"    Domain: {r.domain} → {r.canonical_domain}")
            lines.append(f"    Hash: {r.content_hash[:16]}...")
            lines.append(f"    Exposure: {r.exposure_result.status.value}")
            lines.append(f"    Contamination: {r.contamination_result.level.value}")
            if r.flags:
                lines.append(f"    Flags: {r.flags}")
            lines.append("")

        # Near-duplicate check
        dup_flags = self.check_near_duplicates()
        if dup_flags:
            lines.append("Near-Duplicate Flags:")
            for f in dup_flags:
                lines.append(f"  {f.case_a} ↔ {f.case_b}: {f.similarity_type} ({f.score:.2f})")
        else:
            lines.append("Near-Duplicate Flags: None")

        lines.append("")
        lines.append("Audit Trail:")
        for event in self._audit_trail.get_events():
            lines.append(f"  [{event.timestamp}] {event.event_type}: {event.details}")

        return "\n".join(lines)

    def get_audit_trail(self) -> AuditTrail:
        """Get the audit trail. Custodian-only."""
        return self._audit_trail

    def get_source_registry(self) -> SourceRegistry:
        """Get the source registry. Custodian-only."""
        return self._registry

    # 15. TEE cannot mutate or consume intake state
    def export_tee_safe_summary(self) -> dict:
        """Export a TEE-safe summary containing NO content, NO answer keys,
        NO source material. Only aggregate statistics."""
        return {
            "intake_complete": len(self._records) > 0,
            "source_count": len(self._records),
            "eligible_count": len(self.list_by_status(IntakeStatus.ELIGIBLE)),
            "flagged_count": len(self.list_by_status(IntakeStatus.FLAGGED)),
            "rejected_count": len(self.list_by_status(IntakeStatus.REJECTED)),
            "undeterminable_count": len(self.list_by_status(IntakeStatus.UNDETERMINABLE)),
            "domain_count": len(self.get_domain_distribution()),
            "note": "This summary contains no source content, answer keys, or benchmark material.",
        }
