"""
V5 FDA Medical Device Connectors (Issue #5 V5, directive D).

8 FDA medical device connectors per CTO directive:
  FDA 510(k)        — premarket notification
  FDA PMA           — premarket approval
  FDA De Novo       — novel device classification
  FDA MAUDE         — adverse event reports
  FDA Recalls       — device recalls
  FDA Registration  — device establishment registration/listing
  FDA Classification — device classification
  FDA PAS           — post-approval studies

All use the openFDA API (https://api.fda.gov), which is public domain,
no auth required, rate-limited to 240 requests/minute per IP.

Per CTO: "Medical devices should become one of our highest-priority
intersection domains because they naturally connect nearly every evidence
ecosystem we're building."
"""
from __future__ import annotations
import json
import hashlib
import urllib.parse
import time
from typing import Optional
from datetime import datetime, timezone

from .evidence_connector import (EvidenceConnector, Checkpoint, HealthReport,
                                  ProvenanceChain, content_hash_dict, now_iso)
from .connector_base import HarvestedRecord, HarvestError
from .source_registry import Source
from .failure_recorder import FailureLog
from .real_connectors import _http_get
from .evidence_classes import get_evidence_class


class OpenFdaConnector(EvidenceConnector):
    """Base class for openFDA medical device connectors.

    All openFDA endpoints share the same API structure:
      https://api.fda.gov/device/<endpoint>.json?search=<query>&limit=<n>
    """
    resumable = True; idempotent = True; checkpointed = True
    rate_limit_aware = True; retry_safe = True; content_addressed = True
    provenance_preserving = True; observable = True

    CONNECTOR_VERSION = "openfda-v5-1.0"
    BASE_URL = "https://api.fda.gov/device"
    ENDPOINT = ""  # overridden by subclasses

    def __init__(self, source: Source, failure_log: Optional[FailureLog] = None):
        super().__init__(source, failure_log)
        self._status = "IMPLEMENTED"
        self._records_retrieved = 0

    def discover(self) -> dict:
        try:
            url = f"{self.BASE_URL}/{self.ENDPOINT}.json?limit=1"
            status, body, _ = _http_get(url, timeout=15)
            data = json.loads(body)
            return {"source": self.source.source_id, "status": "REACHABLE",
                    "endpoint": self.ENDPOINT}
        except Exception as e:
            return {"source": self.source.source_id, "status": "UNREACHABLE",
                    "error": str(e)[:200]}

    def fetch_metadata(self, record_ids: list[str]) -> list[dict]:
        return []

    def fetch_content(self, record_id: str) -> Optional[bytes]:
        return None

    def fetch_updates(self, checkpoint: Checkpoint, *, max_records: int = 100) -> tuple[list[HarvestedRecord], Checkpoint]:
        records: list[HarvestedRecord] = []
        harvested_at = now_iso()
        query = checkpoint.last_error or ""  # search query
        skip = int(checkpoint.cursor or "0")
        # Build URL
        base = f"{self.BASE_URL}/{self.ENDPOINT}.json?"
        if query:
            base += f"search={urllib.parse.quote(query)}&"
        base += f"limit={min(max_records, 100)}&skip={skip}"
        try:
            status, body, _ = _http_get(base, timeout=30)
            data = json.loads(body)
            results = data.get("results", [])
            for raw in results:
                normalized = self.normalize(raw)
                raw_bytes = json.dumps(raw, sort_keys=True).encode()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()
                norm_hash = hashlib.sha256(
                    json.dumps(normalized, sort_keys=True, default=str).encode()
                ).hexdigest()
                records.append(HarvestedRecord(
                    record_id=normalized["record_id"],
                    source_id=self.source.source_id,
                    harvested_at=harvested_at,
                    raw_payload_hash=raw_hash,
                    normalized=normalized,
                    normalized_hash=norm_hash,
                    raw_payload=raw_bytes,
                    connector_version=self.CONNECTOR_VERSION,
                    language="en",
                    provenance={"endpoint": base},
                ))
            checkpoint.records_harvested += len(records)
            checkpoint.cursor = str(skip + len(results))
            checkpoint.last_success_at = harvested_at
            if records:
                self._status = "OPERATIONAL"
                self._records_retrieved += len(records)
            return records, checkpoint
        except Exception as e:
            if self.failure_log:
                self.failure_log.record(self.source.source_id, "NETWORK_ERROR",
                                         f"fetch_updates: {str(e)[:300]}")
            self._status = "FAILED"
            checkpoint.last_error = str(e)
            return records, checkpoint

    def normalize(self, raw: dict) -> dict:
        """Override in subclasses. Base returns the raw dict with record_id."""
        return {"record_id": f"{self.ENDPOINT}:{raw.get('id', raw.get('k_number', raw.get('pma_number', hash(str(raw)))))}",
                "raw": raw, "source": self.source.source_id,
                "evidence_class": get_evidence_class(self.source.source_id)}

    def get_provenance(self, record_id: str) -> ProvenanceChain:
        return ProvenanceChain(
            record_id=record_id, source_id=self.source.source_id,
            harvested_at=now_iso(), raw_payload_hash="", normalized_hash="",
            source_endpoint=f"{self.BASE_URL}/{self.ENDPOINT}",
            source_version=self.CONNECTOR_VERSION,
            credentials_used="none (public domain)",
        )

    def content_hash(self, normalized: dict) -> str:
        return content_hash_dict(normalized)

    def health_check(self) -> HealthReport:
        t0 = time.monotonic()
        try:
            url = f"{self.BASE_URL}/{self.ENDPOINT}.json?limit=1"
            status, body, _ = _http_get(url, timeout=15, retries=2)
            data = json.loads(body)
            latency = (time.monotonic() - t0) * 1000
            if data.get("results") is not None:
                self._status = "PROBED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="OK", latency_ms=latency,
                    http_status=status, metadata={"endpoint": self.ENDPOINT},
                )
            else:
                self._status = "FAILED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="SOURCE_CHANGED", latency_ms=latency,
                    http_status=status,
                )
        except Exception as e:
            latency = (time.monotonic() - t0) * 1000
            self._status = "FAILED"
            return HealthReport(
                source_id=self.source.source_id, checked_at=now_iso(),
                reachable=False, probe_result="TEMPORARILY_UNAVAILABLE",
                latency_ms=latency, error_detail=str(e)[:200],
            )

    @property
    def operational_status(self) -> str:
        return self._status


class Fda510kConnector(OpenFdaConnector):
    ENDPOINT = "510k"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fda510k:{raw.get('k_number', '')}",
            "k_number": raw.get("k_number", ""),
            "device_name": raw.get("device_name", ""),
            "applicant": raw.get("applicant", ""),
            "decision_code": raw.get("decision_code", ""),
            "decision_date": raw.get("decision_date", ""),
            "product_code": raw.get("product_code", ""),
            "review_advisory_committee": raw.get("advisory_committee", ""),
            "statement_or_summary": raw.get("statement_or_summary", ""),
            "clearance_type": raw.get("clearance_type", ""),
            "source": "fda_510k",
            "evidence_class": "DEVICE_REGULATORY_ACTION",
            "evidence_type": "device_510k",
        }


class FdaPmaConnector(OpenFdaConnector):
    ENDPOINT = "pma"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaPma:{raw.get('pma_number', '')}:{raw.get('supplement_number', '0')}",
            "pma_number": raw.get("pma_number", ""),
            "supplement_number": raw.get("supplement_number", ""),
            "applicant": raw.get("applicant", ""),
            "generic_name": raw.get("generic_name", ""),
            "trade_name": raw.get("trade_name", ""),
            "decision_code": raw.get("decision_code", ""),
            "decision_date": raw.get("decision_date", ""),
            "advisory_committee": raw.get("advisory_committee", ""),
            "expedited_review_flag": raw.get("expedited_review_flag", ""),
            "product_code": raw.get("product_code", ""),
            "source": "fda_pma",
            "evidence_class": "DEVICE_REGULATORY_ACTION",
            "evidence_type": "device_pma",
        }


class FdaDenovoConnector(OpenFdaConnector):
    ENDPOINT = "denovo"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaDenovo:{raw.get('denovo_number', raw.get('k_number', ''))}",
            "denovo_number": raw.get("denovo_number", ""),
            "k_number": raw.get("k_number", ""),
            "device_name": raw.get("device_name", ""),
            "classification_name": raw.get("classification_name", ""),
            "applicant": raw.get("applicant", ""),
            "decision_date": raw.get("decision_date", ""),
            "product_code": raw.get("product_code", ""),
            "source": "fda_denovo",
            "evidence_class": "DEVICE_REGULATORY_ACTION",
            "evidence_type": "device_denovo",
        }


class FdaMaudeConnector(OpenFdaConnector):
    """MAUDE — adverse event reports. Per CTO: the 'Cemetery' corpus for devices."""
    ENDPOINT = "event"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaMaude:{raw.get('mdr_report_key', '')}",
            "mdr_report_key": raw.get("mdr_report_key", ""),
            "event_type": raw.get("event_type", ""),
            "report_source_code": raw.get("report_source_code", ""),
            "date_received": raw.get("date_received", ""),
            "date_report": raw.get("date_report", ""),
            "date_added": raw.get("date_added", ""),
            "device": raw.get("device", []),
            "patient": raw.get("patient", []),
            "text": raw.get("mdr_text", []),
            "source": "fda_maude",
            "evidence_class": "ADVERSE_EVENT",
            "evidence_type": "adverse_event",
        }


class FdaRecallsConnector(OpenFdaConnector):
    ENDPOINT = "recall"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaRecall:{raw.get('recall_number', hash(str(raw)))}",
            "recall_number": raw.get("recall_number", ""),
            "reason_for_recall": raw.get("reason_for_recall", ""),
            "classification": raw.get("classification", ""),
            "status": raw.get("status", ""),
            "product_description": raw.get("product_description", ""),
            "recalling_firm": raw.get("recalling_firm", ""),
            "recall_initiation_date": raw.get("recall_initiation_date", ""),
            "termination_date": raw.get("termination_date", ""),
            "product_quantity": raw.get("product_quantity", ""),
            "source": "fda_recalls",
            "evidence_class": "MARKET_SIGNAL",
            "evidence_type": "device_recall",
        }


class FdaClassificationConnector(OpenFdaConnector):
    ENDPOINT = "classification"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaClass:{raw.get('product_code', '')}",
            "product_code": raw.get("product_code", ""),
            "device_name": raw.get("device_name", ""),
            "device_class": raw.get("device_class", ""),
            "regulation_number": raw.get("regulation_number", ""),
            "medical_specialty": raw.get("medical_specialty", ""),
            "review_panel": raw.get("review_panel", ""),
            "definition": raw.get("definition", ""),
            "submission_type": raw.get("submission_type", ""),
            "source": "fda_classification",
            "evidence_class": "DEVICE_REGULATORY_ACTION",
            "evidence_type": "device_classification",
        }


# Registration and PAS use different endpoints
class FdaRegistrationConnector(OpenFdaConnector):
    ENDPOINT = "reglist"
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaReg:{raw.get('registration_number', raw.get('fei_number', hash(str(raw))))}",
            "registration_number": raw.get("registration_number", ""),
            "fei_number": raw.get("fei_number", ""),
            "name": raw.get("name", ""),
            "city": raw.get("city", ""),
            "state": raw.get("state", ""),
            "country": raw.get("country", ""),
            "source": "fda_registration",
            "evidence_class": "DEVICE_REGULATORY_ACTION",
            "evidence_type": "device_registration",
        }


class FdaPasConnector(OpenFdaConnector):
    """Post-Approval Studies. Uses a different URL structure."""
    ENDPOINT = "pas"
    BASE_URL = "https://api.fda.gov/device"  # may need adjustment
    def normalize(self, raw: dict) -> dict:
        return {
            "record_id": f"fdaPas:{raw.get('pas_number', hash(str(raw)))}",
            "pas_number": raw.get("pas_number", ""),
            "pma_number": raw.get("pma_number", ""),
            "applicant": raw.get("applicant", ""),
            "study_title": raw.get("study_title", ""),
            "study_status": raw.get("study_status", ""),
            "source": "fda_pas",
            "evidence_class": "CLINICAL_EVIDENCE",
            "evidence_type": "post_approval_study",
        }


# Registry of V5 FDA connectors
V5_FDA_CONNECTOR_REGISTRY = {
    "src:fda_510k": Fda510kConnector,
    "src:fda_pma": FdaPmaConnector,
    "src:fda_denovo": FdaDenovoConnector,
    "src:fda_maude": FdaMaudeConnector,
    "src:fda_recalls": FdaRecallsConnector,
    "src:fda_classification": FdaClassificationConnector,
    "src:fda_registration": FdaRegistrationConnector,
    "src:fda_pas": FdaPasConnector,
}


def get_fda_connector(source_id: str, failure_log: Optional[FailureLog] = None) -> Optional[EvidenceConnector]:
    from .source_registry import SOURCES
    src = next((s for s in SOURCES if s.source_id == source_id), None)
    if not src:
        return None
    cls = V5_FDA_CONNECTOR_REGISTRY.get(source_id)
    if not cls:
        return None
    return cls(src, failure_log=failure_log)
