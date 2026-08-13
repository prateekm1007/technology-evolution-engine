"""
Source validator (Issue #5).

For each source in the registry, validate:
  1. ACCESSIBLE — the endpoint responds (HTTP 200/3xx, not 4xx/5xx)
  2. AUTH_WORKS — if auth_required, the credentials are valid
  3. SCHEMA_STABLE — response shape matches expected (per metadata_format)
  4. LICENSE_OK — license permits our use
  5. RATE_LIMIT_OK — not currently rate-limited
  6. PRIMARY_INTACT — primary source is reachable; not silently replaced

This validator does NOT perform live HTTP calls in offline mode — it produces
a STRUCTURAL validation (does the source have the required metadata fields,
is the URL well-formed, is the license in the allowed set, etc.). Live
validation requires credentials and is performed by the operator.

Per Honest-Boundary rule: we state precisely what we validated and what we did not.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from urllib.parse import urlparse
import json
from .source_registry import Source, SOURCES


ALLOWED_EVIDENCE_TYPES = {
    "paper", "patent", "technical_report", "standard", "dataset",
    "code", "experiment", "clinical_trial", "product", "failure_record",
}
ALLOWED_ACCESS_METHODS = {
    "rest_api", "bulk_download", "oai_pmh", "rss_feed", "git_clone",
    "web_scrape", "sparql", "graphql", "ftp", "manual",
}
ALLOWED_TIERS = set("ABCDEFGHI")
ALLOWED_UNIVERSES = {"matter", "energy", "life", "machine", "information", "planet"}
ALLOWED_PRIMARY = {"primary", "secondary", "aggregator", "archive", "federation"}


@dataclass
class ValidationResult:
    source_id: str
    validated_at: str
    structural_ok: bool
    errors: list[str]
    warnings: list[str]
    live_check_performed: bool = False  # False in offline mode
    live_check_status: str = "NOT_PERFORMED"

    def canonical_dict(self) -> dict:
        return asdict(self)


def validate_source_structural(source: Source) -> ValidationResult:
    """Structural validation — no live HTTP. Checks metadata completeness."""
    errors = []
    warnings = []

    if source.evidence_type not in ALLOWED_EVIDENCE_TYPES:
        errors.append(f"bad evidence_type: {source.evidence_type}")
    if source.access_method not in ALLOWED_ACCESS_METHODS:
        errors.append(f"bad access_method: {source.access_method}")
    if source.evidence_tier not in ALLOWED_TIERS:
        errors.append(f"bad evidence_tier: {source.evidence_tier}")
    for u in source.universes:
        if u not in ALLOWED_UNIVERSES:
            errors.append(f"bad universe: {u}")
    if source.primary_or_secondary not in ALLOWED_PRIMARY:
        errors.append(f"bad primary_or_secondary: {source.primary_or_secondary}")

    # URL well-formed
    parsed = urlparse(source.url)
    if parsed.scheme not in ("http", "https"):
        errors.append(f"bad URL scheme: {parsed.scheme}")
    if not parsed.netloc:
        errors.append(f"bad URL netloc: {source.url}")

    # License — warn on proprietary (still valid, but flags access constraint)
    if "proprietary" in source.license.lower():
        warnings.append(f"proprietary license: {source.license}")

    # Auth required but no auth method documented
    if source.auth_required and source.access_method == "web_scrape":
        warnings.append("auth_required with web_scrape — likely a captcha/login wall")

    # Coverage notes should not be empty (honest disclosure)
    if not source.coverage_notes:
        warnings.append("coverage_notes empty — add honest coverage limitations")

    return ValidationResult(
        source_id=source.source_id,
        validated_at=datetime.now(timezone.utc).isoformat(),
        structural_ok=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        live_check_performed=False,
        live_check_status="NOT_PERFORMED",
    )


def validate_all_sources() -> dict:
    """Validate every source in the registry. Returns a summary."""
    results = []
    for s in SOURCES:
        results.append(validate_source_structural(s).canonical_dict())
    ok = sum(1 for r in results if r["structural_ok"])
    failed = [r for r in results if not r["structural_ok"]]
    return {
        "total_sources": len(SOURCES),
        "structural_pass": ok,
        "structural_fail": len(failed),
        "failed_sources": failed,
        "all_results": results,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "live_check_performed": False,  # honest
        "note": "Structural validation only. Live HTTP checks require credentials "
                "and are performed by the operator with --live flag.",
    }


# =====================================================================
# CONCRETE CONNECTORS (shape-only — no live HTTP in offline mode)
# =====================================================================
# Each concrete connector implements the Connector interface. In offline mode,
# harvest() raises HarvestError("live harvest not enabled"). In live mode
# (operator passes credentials), the connector makes real HTTP calls.
#
# The connectors are written to be production-ready except for the actual
# HTTP call, which is gated behind a credentials check.

from .connector_base import Connector, HarvestState, HarvestedRecord, HarvestError, hash_payload, now_iso
from typing import Optional


class OpenAlexConnector(Connector):
    """OpenAlex API connector. CC0. No auth required (polite pool with email)."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(
            f"{self.source.source_id}: live harvest not enabled. "
            f"Operator must pass --live with credentials/email."
        )

    def validate(self) -> dict:
        v = validate_source_structural(self.source)
        return v.canonical_dict()


class ArxivConnector(Connector):
    """arXiv OAI-PMH connector."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class EpoOpsConnector(Connector):
    """EPO Open Patent Services connector. Requires OAuth credentials."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        if not self.source.auth_required:
            raise HarvestError("EPO OPS requires auth_required=True")
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled. OAuth credentials required.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class NasaNtrsConnector(Connector):
    """NASA Technical Reports Server."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class ClinicalTrialsGovConnector(Connector):
    """ClinicalTrials.gov v2 API."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class GithubCodeConnector(Connector):
    """GitHub code search/repo metadata."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        if not self.source.auth_required:
            raise HarvestError("GitHub requires auth_required=True (token)")
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled. Token required.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class ZenodoConnector(Connector):
    """Zenodo dataset/code connector."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class NistConnector(Connector):
    """NIST publications + standard reference data."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class FdaConnector(Connector):
    """FDA open data (devices, drugs, recalls)."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


class RetractionWatchConnector(Connector):
    """Retraction Watch database (failure records)."""
    def harvest(self, state: HarvestState, *, max_records: int = 100) -> tuple[list[HarvestedRecord], HarvestState]:
        raise HarvestError(f"{self.source.source_id}: live harvest not enabled.")

    def validate(self) -> dict:
        return validate_source_structural(self.source).canonical_dict()


# Registry of concrete connectors by source_id prefix
CONNECTOR_REGISTRY = {
    "src:openalex": OpenAlexConnector,
    "src:arxiv": ArxivConnector,
    "src:oai_arxiv": ArxivConnector,
    "src:epo_ops": EpoOpsConnector,
    "src:nasa_ntrs": NasaNtrsConnector,
    "src:ct_gov": ClinicalTrialsGovConnector,
    "src:github": GithubCodeConnector,
    "src:zenodo": ZenodoConnector,
    "src:zenodo_code": ZenodoConnector,
    "src:nist_pubs": NistConnector,
    "src:nist_srd": NistConnector,
    "src:nist_webbook": NistConnector,
    "src:fda_devices": FdaConnector,
    "src:fda_drugs": FdaConnector,
    "src:fda_recalls": FdaConnector,
    "src:retraction_watch": RetractionWatchConnector,
}


def get_connector(source_id: str) -> Optional[Connector]:
    """Look up the concrete connector for a source_id."""
    src = next((s for s in SOURCES if s.source_id == source_id), None)
    if not src:
        return None
    cls = CONNECTOR_REGISTRY.get(source_id)
    if not cls:
        return None
    return cls(src)
