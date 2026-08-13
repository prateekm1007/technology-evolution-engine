"""
V4 REAL connectors for the contrarian high-signal corpora (Issue #5 V4).

Per CEO/CTO contrarian strategy: "don't read what people have already decided
is worth publishing. Read the friction. Read the failures. Read the arguments."

Three new REAL connectors:

1. HuggingFacePatentConnector — retrieves REAL US patent records from the
   allenai/us-patents dataset via the HuggingFace datasets-server rows API.
   This unblocks patent ingestion WITHOUT needing EPO OAuth or USPTO API keys.
   The dataset contains 8M+ US patent grants/applications (1976-2025) with
   filing_date, patent_type, and full text (title + abstract + claims).

2. ClinicalTrialsGovConnector — retrieves REAL clinical trial records from
   ClinicalTrials.gov API v2, including the "whyStopped" field for terminated
   trials. This is the contrarian "Cemetery" corpus: structured biomedical
   failure data that no one else uses for discovery.

3. SecEdgarConnector — retrieves REAL 10-K filings from SEC EDGAR full-text
   search. The "Risk Factors" section of 10-K filings is pure constraint data:
   what companies are legally terrified of.

All three connectors implement EvidenceConnector (8 methods + 8 properties).
All three retrieve REAL records via LIVE HTTP. No synthetic data.
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
from .real_connectors import _http_get, USER_AGENT


# =====================================================================
# HuggingFace Patent Connector — REAL US patents via datasets-server
# =====================================================================

class HuggingFacePatentConnector(EvidenceConnector):
    """REAL US patent connector via HuggingFace datasets-server.

    Retrieves actual patent records from allenai/us-patents (8M+ US patents,
    1976-2025, ODC-BY license). This bypasses the EPO/USPTO auth requirement
    by using a pre-processed open dataset.

    The dataset fields are: corpus_id, filing_date, patent_type, text.
    The 'text' field contains title + abstract + claims concatenated.
    """
    resumable = True; idempotent = True; checkpointed = True
    rate_limit_aware = True; retry_safe = True; content_addressed = True
    provenance_preserving = True; observable = True

    CONNECTOR_VERSION = "huggingface-patents-v4-1.0"
    DATASET = "allenai/us-patents"
    BASE_URL = "https://datasets-server.huggingface.co"

    def __init__(self, source: Source, failure_log: Optional[FailureLog] = None):
        super().__init__(source, failure_log)
        self._status = "IMPLEMENTED"
        self._records_retrieved = 0

    def discover(self) -> dict:
        try:
            url = f"https://huggingface.co/api/datasets/{self.DATASET}"
            status, body, _ = _http_get(url, timeout=15)
            data = json.loads(body)
            return {
                "source": self.source.source_id,
                "status": "REACHABLE",
                "dataset": self.DATASET,
                "downloads": data.get("downloads"),
                "license": "odc-by",
            }
        except Exception as e:
            return {"source": self.source.source_id, "status": "UNREACHABLE",
                    "error": str(e)[:200]}

    def fetch_metadata(self, record_ids: list[str]) -> list[dict]:
        # The datasets-server doesn't support arbitrary ID lookup; use offset pagination
        return []

    def fetch_content(self, record_id: str) -> Optional[bytes]:
        return None

    def fetch_updates(self, checkpoint: Checkpoint, *, max_records: int = 100) -> tuple[list[HarvestedRecord], Checkpoint]:
        """Fetch patent records via the datasets-server rows API."""
        records: list[HarvestedRecord] = []
        harvested_at = now_iso()
        offset = int(checkpoint.cursor or "0")
        # The datasets-server returns rows in chunks; we page through
        url = (f"{self.BASE_URL}/rows?dataset={urllib.parse.quote(self.DATASET)}"
               f"&config=default&split=train&offset={offset}&length={min(max_records, 100)}")
        try:
            status, body, _ = _http_get(url, timeout=30)
            data = json.loads(body)
            rows = data.get("rows", [])
            for row in rows:
                raw = row.get("row", {})
                normalized = self.normalize(raw)
                raw_bytes = json.dumps(raw, sort_keys=True).encode()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()
                norm_hash = hashlib.sha256(
                    json.dumps(normalized, sort_keys=True, default=str).encode()
                ).hexdigest()
                records.append(HarvestedRecord(
                    record_id=normalized["patent_id"],
                    source_id=self.source.source_id,
                    harvested_at=harvested_at,
                    raw_payload_hash=raw_hash,
                    normalized=normalized,
                    normalized_hash=norm_hash,
                    raw_payload=raw_bytes,
                    connector_version=self.CONNECTOR_VERSION,
                    language="en",
                    provenance={"endpoint": url, "dataset": self.DATASET,
                                "row_idx": row.get("row_idx")},
                ))
            checkpoint.records_harvested += len(records)
            checkpoint.cursor = str(offset + len(rows))
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
        """Normalize a HuggingFace patent row into canonical patent form.

        The raw row has: corpus_id (int), filing_date (string YYYYMMDD or empty),
        patent_type (GRANT/APPLICATION), text (title + abstract + claims).
        """
        corpus_id = str(raw.get("corpus_id", ""))
        filing_date_raw = str(raw.get("filing_date", ""))
        # filing_date is YYYYMMDD format; convert to ISO
        filing_date = ""
        if len(filing_date_raw) == 8:
            filing_date = f"{filing_date_raw[:4]}-{filing_date_raw[4:6]}-{filing_date_raw[6:8]}"
        elif len(filing_date_raw) == 10:
            filing_date = filing_date_raw  # already ISO
        text = raw.get("text", "") or ""
        # The text field contains title, abstract, claims concatenated.
        # We don't have explicit separators, so we store the full text and
        # extract a title heuristic (first line or first sentence)
        title = ""
        abstract = ""
        if text:
            lines = text.strip().split("\n", 1)
            title = lines[0][:300].strip()
            if len(lines) > 1:
                # Abstract is typically the next paragraph
                rest = lines[1].strip()
                # Take first ~500 chars as abstract approximation
                abstract = rest[:500]
        return {
            "patent_id": f"hfpatent:{corpus_id}",
            "corpus_id": corpus_id,
            "filing_date": filing_date,
            "patent_type": raw.get("patent_type", ""),
            "title": title,
            "abstract": abstract,
            "fulltext": text[:5000],  # truncate for storage
            "jurisdiction": "US",
            "source": "huggingface_us_patents",
            "is_secondary": False,  # this IS the primary patent data (from USPTO, repackaged)
            "primary_authority": "USPTO",
        }

    def get_provenance(self, record_id: str) -> ProvenanceChain:
        return ProvenanceChain(
            record_id=record_id, source_id=self.source.source_id,
            harvested_at=now_iso(), raw_payload_hash="", normalized_hash="",
            source_endpoint=self.BASE_URL, source_version=self.CONNECTOR_VERSION,
            credentials_used="none (ODC-BY open dataset)",
        )

    def content_hash(self, normalized: dict) -> str:
        return content_hash_dict(normalized)

    def health_check(self) -> HealthReport:
        t0 = time.monotonic()
        try:
            url = f"{self.BASE_URL}/rows?dataset={urllib.parse.quote(self.DATASET)}&config=default&split=train&offset=0&length=1"
            status, body, _ = _http_get(url, timeout=15, retries=2)
            data = json.loads(body)
            latency = (time.monotonic() - t0) * 1000
            if data.get("rows"):
                self._status = "PROBED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="OK", latency_ms=latency,
                    http_status=status, metadata={"dataset": self.DATASET},
                )
            else:
                self._status = "FAILED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="SOURCE_CHANGED", latency_ms=latency,
                    http_status=status, error_detail="no rows in response",
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


# =====================================================================
# ClinicalTrials.gov Connector — REAL failure corpus
# =====================================================================

class ClinicalTrialsGovConnector(EvidenceConnector):
    """REAL ClinicalTrials.gov connector. Retrieves clinical trial records
    including the "whyStopped" field for terminated trials.

    Per CEO contrarian strategy: "This is the largest, most structured dataset
    of human biomedical failure in existence. Your engine should parse the
    'why stopped' tags to build a causal graph of biological constraints."
    """
    resumable = True; idempotent = True; checkpointed = True
    rate_limit_aware = True; retry_safe = True; content_addressed = True
    provenance_preserving = True; observable = True

    CONNECTOR_VERSION = "clinicaltrials-v4-1.0"
    BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(self, source: Source, failure_log: Optional[FailureLog] = None):
        super().__init__(source, failure_log)
        self._status = "IMPLEMENTED"
        self._records_retrieved = 0

    def discover(self) -> dict:
        try:
            url = f"{self.BASE_URL}/studies?query.term=battery&pageSize=1"
            status, body, _ = _http_get(url, timeout=15)
            data = json.loads(body)
            return {
                "source": self.source.source_id,
                "status": "REACHABLE",
                "sample_nct": data.get("studies", [{}])[0].get("nctId", "") if data.get("studies") else "",
            }
        except Exception as e:
            return {"source": self.source.source_id, "status": "UNREACHABLE",
                    "error": str(e)[:200]}

    def fetch_metadata(self, record_ids: list[str]) -> list[dict]:
        records = []
        for rid in record_ids:
            try:
                url = f"{self.BASE_URL}/studies/{rid}"
                status, body, _ = _http_get(url, timeout=15)
                raw = json.loads(body)
                normalized = self.normalize(raw)
                records.append(normalized)
                self._records_retrieved += 1
                if self._records_retrieved >= 1:
                    self._status = "OPERATIONAL"
            except Exception as e:
                if self.failure_log:
                    self.failure_log.record(self.source.source_id, "API_BLOCKED",
                                             f"fetch_metadata {rid}: {e}")
        return records

    def fetch_content(self, record_id: str) -> Optional[bytes]:
        try:
            url = f"{self.BASE_URL}/studies/{record_id}"
            status, body, _ = _http_get(url, timeout=15)
            return body
        except Exception:
            return None

    def fetch_updates(self, checkpoint: Checkpoint, *, max_records: int = 100) -> tuple[list[HarvestedRecord], Checkpoint]:
        """Fetch clinical trial records. The query is stored in checkpoint.last_error."""
        records: list[HarvestedRecord] = []
        harvested_at = now_iso()
        query = checkpoint.last_error or "battery"
        page_token = checkpoint.cursor or ""
        # Build URL with optional status filter for terminated trials (failure corpus)
        status_filter = ""
        if query.startswith("TERMINATED:"):
            status_filter = "&filter.overallStatus=TERMINATED"
            query = query[len("TERMINATED:"):]
        url = (f"{self.BASE_URL}/studies?query.term={urllib.parse.quote(query)}"
               f"&pageSize={min(max_records, 100)}{status_filter}")
        if page_token:
            url += f"&pageToken={page_token}"
        try:
            status, body, _ = _http_get(url, timeout=30)
            data = json.loads(body)
            studies = data.get("studies", [])
            next_token = data.get("nextPageToken", "")
            for raw in studies:
                normalized = self.normalize(raw)
                raw_bytes = json.dumps(raw, sort_keys=True).encode()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()
                norm_hash = hashlib.sha256(
                    json.dumps(normalized, sort_keys=True, default=str).encode()
                ).hexdigest()
                records.append(HarvestedRecord(
                    record_id=normalized["trial_id"],
                    source_id=self.source.source_id,
                    harvested_at=harvested_at,
                    raw_payload_hash=raw_hash,
                    normalized=normalized,
                    normalized_hash=norm_hash,
                    raw_payload=raw_bytes,
                    connector_version=self.CONNECTOR_VERSION,
                    language="en",
                    provenance={"endpoint": url},
                ))
            checkpoint.records_harvested += len(records)
            checkpoint.cursor = next_token
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
        """Normalize a ClinicalTrials.gov study into canonical form."""
        proto = raw.get("protocolSection", {})
        status_mod = proto.get("statusModule", {})
        ident = proto.get("identificationModule", {})
        design = proto.get("designModule", {})
        conditions = proto.get("conditionsModule", {})
        arms = proto.get("armsInterventionsModule", {})
        return {
            "trial_id": f"clinicaltrials:{raw.get('nctId', '')}",
            "nct_id": raw.get("nctId", ""),
            "brief_title": ident.get("briefTitle", ""),
            "official_title": ident.get("officialTitle", ""),
            "overall_status": status_mod.get("overallStatus", ""),
            "why_stopped": status_mod.get("whyStopped", ""),  # THE FAILURE SIGNAL
            "phase": design.get("phases", ""),
            "study_type": design.get("studyType", ""),
            "conditions": conditions.get("conditions", []),
            "interventions": [i.get("name", "") for i in arms.get("interventions", [])],
            "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
            "completion_date": status_mod.get("completionDateStruct", {}).get("date", ""),
            "lead_org": ident.get("organization", {}).get("fullName", ""),
            "org_study_id": ident.get("orgStudyId", ""),
            "source": "clinicaltrials_gov",
            "evidence_type": "clinical_trial",
        }

    def get_provenance(self, record_id: str) -> ProvenanceChain:
        return ProvenanceChain(
            record_id=record_id, source_id=self.source.source_id,
            harvested_at=now_iso(), raw_payload_hash="", normalized_hash="",
            source_endpoint=self.BASE_URL, source_version=self.CONNECTOR_VERSION,
            credentials_used="none (public domain)",
        )

    def content_hash(self, normalized: dict) -> str:
        return content_hash_dict(normalized)

    def health_check(self) -> HealthReport:
        t0 = time.monotonic()
        try:
            url = f"{self.BASE_URL}/studies?query.term=battery&pageSize=1"
            status, body, _ = _http_get(url, timeout=15, retries=2)
            data = json.loads(body)
            latency = (time.monotonic() - t0) * 1000
            if data.get("studies"):
                self._status = "PROBED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="OK", latency_ms=latency,
                    http_status=status,
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


# =====================================================================
# SEC EDGAR Connector — REAL risk factor / constraint corpus
# =====================================================================

class SecEdgarConnector(EvidenceConnector):
    """REAL SEC EDGAR connector. Retrieves 10-K filings via full-text search.

    Per CEO contrarian strategy: "The 'Risk Factors' section of a 10-K filing
    is a pure, unfiltered signal of systemic and market constraints."
    """
    resumable = True; idempotent = True; checkpointed = True
    rate_limit_aware = True; retry_safe = True; content_addressed = True
    provenance_preserving = True; observable = True

    CONNECTOR_VERSION = "secedgar-v4-1.0"
    BASE_URL = "https://efts.sec.gov/LATEST/search-index"

    def __init__(self, source: Source, failure_log: Optional[FailureLog] = None):
        super().__init__(source, failure_log)
        self._status = "IMPLEMENTED"
        self._records_retrieved = 0

    def discover(self) -> dict:
        try:
            url = f"{self.BASE_URL}?q=%22lithium+battery%22"
            status, body, _ = _http_get(url, timeout=15,
                                          headers={"User-Agent": "TEE-Fabric/1.0 test@example.com"})
            data = json.loads(body)
            hits = data.get("hits", {}).get("total", {}).get("value", 0)
            return {"source": self.source.source_id, "status": "REACHABLE",
                    "hits": hits}
        except Exception as e:
            return {"source": self.source.source_id, "status": "UNREACHABLE",
                    "error": str(e)[:200]}

    def fetch_metadata(self, record_ids: list[str]) -> list[dict]:
        return []

    def fetch_content(self, record_id: str) -> Optional[bytes]:
        # Fetch the actual filing from sec.gov
        try:
            url = f"https://www.sec.gov/Archives/edgar/data/{record_id}"
            status, body, _ = _http_get(url, timeout=20,
                                          headers={"User-Agent": "TEE-Fabric/1.0 test@example.com"})
            return body
        except Exception:
            return None

    def fetch_updates(self, checkpoint: Checkpoint, *, max_records: int = 100) -> tuple[list[HarvestedRecord], Checkpoint]:
        """Fetch 10-K filings via EDGAR full-text search."""
        records: list[HarvestedRecord] = []
        harvested_at = now_iso()
        query = checkpoint.last_error or "lithium battery"
        # EDGAR full-text search API
        url = (f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(query)}"
               f"&dateRange=custom&startdt=2023-01-01&enddt=2025-12-31"
               f"&forms=10-K&hits={min(max_records, 100)}")
        try:
            status, body, _ = _http_get(url, timeout=30,
                                          headers={"User-Agent": "TEE-Fabric/1.0 test@example.com"})
            data = json.loads(body)
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                raw = hit.get("_source", {})
                normalized = self.normalize(raw, hit.get("_id", ""))
                raw_bytes = json.dumps(raw, sort_keys=True).encode()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()
                norm_hash = hashlib.sha256(
                    json.dumps(normalized, sort_keys=True, default=str).encode()
                ).hexdigest()
                records.append(HarvestedRecord(
                    record_id=normalized["filing_id"],
                    source_id=self.source.source_id,
                    harvested_at=harvested_at,
                    raw_payload_hash=raw_hash,
                    normalized=normalized,
                    normalized_hash=norm_hash,
                    raw_payload=raw_bytes,
                    connector_version=self.CONNECTOR_VERSION,
                    language="en",
                    provenance={"endpoint": url, "hit_score": hit.get("_score", 0)},
                ))
            checkpoint.records_harvested += len(records)
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

    def normalize(self, raw: dict, doc_id: str) -> dict:
        """Normalize an EDGAR search hit into canonical form."""
        return {
            "filing_id": f"secedgar:{doc_id}",
            "doc_id": doc_id,
            "company": raw.get("display_names", [""])[0] if raw.get("display_names") else "",
            "form_type": raw.get("form", ""),
            "filing_date": raw.get("file_date", ""),
            "period": raw.get("period", ""),
            "description": raw.get("description", "")[:500],
            "entity_name": raw.get("entity_name", ""),
            "cik": str(raw.get("ciks", [""])[0]) if raw.get("ciks") else "",
            "inc_state": raw.get("inc_state", ""),
            "sic": str(raw.get("sic", "")),
            "source": "sec_edgar",
            "evidence_type": "failure_record",  # risk factors are constraint/failure data
        }

    def get_provenance(self, record_id: str) -> ProvenanceChain:
        return ProvenanceChain(
            record_id=record_id, source_id=self.source.source_id,
            harvested_at=now_iso(), raw_payload_hash="", normalized_hash="",
            source_endpoint=self.BASE_URL, source_version=self.CONNECTOR_VERSION,
            credentials_used="none (public domain)",
        )

    def content_hash(self, normalized: dict) -> str:
        return content_hash_dict(normalized)

    def health_check(self) -> HealthReport:
        t0 = time.monotonic()
        try:
            url = f"{self.BASE_URL}?q=%22lithium+battery%22"
            status, body, _ = _http_get(url, timeout=15,
                                          headers={"User-Agent": "TEE-Fabric/1.0 test@example.com"})
            data = json.loads(body)
            latency = (time.monotonic() - t0) * 1000
            hits = data.get("hits", {}).get("total", {}).get("value", 0)
            if hits > 0:
                self._status = "PROBED"
                return HealthReport(
                    source_id=self.source.source_id, checked_at=now_iso(),
                    reachable=True, probe_result="OK", latency_ms=latency,
                    http_status=status, metadata={"hits": hits},
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


# =====================================================================
# Registry
# =====================================================================

V4_REAL_CONNECTOR_REGISTRY = {
    "src:huggingface_patents": HuggingFacePatentConnector,
    "src:ct_gov": ClinicalTrialsGovConnector,
    "src:sec_edgar": SecEdgarConnector,
}


def get_v4_connector(source_id: str, failure_log: Optional[FailureLog] = None) -> Optional[EvidenceConnector]:
    """Look up and instantiate a V4 connector by source_id."""
    from .source_registry import SOURCES
    src = next((s for s in SOURCES if s.source_id == source_id), None)
    if not src:
        return None
    cls = V4_REAL_CONNECTOR_REGISTRY.get(source_id)
    if not cls:
        return None
    return cls(src, failure_log=failure_log)
