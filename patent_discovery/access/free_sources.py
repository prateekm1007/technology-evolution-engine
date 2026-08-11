"""
Patent free-source adapters — unified schema.

Each adapter returns the same normalized schema. Missing fields are 'UNAVAILABLE',
never fabricated.

SOURCES TESTED:
- BigQueryPatentAdapter: BLOCKED (requires Google Cloud project + credentials)
- EPOOpsAdapter: BLOCKED (requires OAuth; LOD endpoint returns metadata only, no patent content)
- EPOLODAdapter: PARTIAL (SPARQL endpoint works but only returns CPC classification data, not patent records)
- USPTOAdapter: BLOCKED (ODP API requires key; bulkdata.uspto.gov DNS doesn't resolve)
- WIPOAdapter: BLOCKED (patentscope.wipo.int returns 403 Forbidden)
- IndiaPatentAdapter: BLOCKED (ipsearch.ipindia.gov.in DNS doesn't resolve; main site is HTML only)
- ChinaPatentAdapter: BLOCKED (pss-system.cponline.cnipa.gov.cn connection fails)

HONEST STATUS: All free patent data routes are blocked in this environment.
See PATENT_FREE_ACCESS_MATRIX_V1.md for full test results.
"""
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import socket
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


UNAVAILABLE = "UNAVAILABLE"
UA = "PatentDiscoveryEngine/2.0 (mailto:patent-discovery@example.org)"


def _fetch(url: str, headers: dict = None, data: bytes = None, timeout: float = 15.0,
           max_retries: int = 2, method: str = None) -> tuple:
    """Fetch URL with retries. Returns (content_bytes, status, error)."""
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs, data=data, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.status, None
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:
                pass
            if e.code == 429 and attempt < max_retries:
                time.sleep(2.0 * (2 ** attempt))
                continue
            return body, e.code, f"HTTP {e.code}"
        except (urllib.error.URLError, socket.timeout) as e:
            if attempt < max_retries:
                time.sleep(1.0 * (2 ** attempt))
                continue
            return b"", 0, f"network: {str(e)[:100]}"
        except Exception as e:
            return b"", 0, f"error: {type(e).__name__}: {str(e)[:100]}"
    return b"", 0, "max_retries"


def _raw_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalized_record(source_db: str, jurisdiction: str, pub_num: str,
                       raw_content: bytes, **fields) -> dict:
    """Build a normalized record. Missing fields are UNAVAILABLE."""
    record = {
        "source_database": source_db,
        "jurisdiction": jurisdiction,
        "publication_number": pub_num,
        "application_number": fields.get("application_number", UNAVAILABLE),
        "priority_numbers": fields.get("priority_numbers", UNAVAILABLE),
        "publication_date": fields.get("publication_date", UNAVAILABLE),
        "filing_date": fields.get("filing_date", UNAVAILABLE),
        "title": fields.get("title", UNAVAILABLE),
        "abstract": fields.get("abstract", UNAVAILABLE),
        "claims": fields.get("claims", UNAVAILABLE),
        "description": fields.get("description", UNAVAILABLE),
        "inventors": fields.get("inventors", UNAVAILABLE),
        "assignees": fields.get("assignees", UNAVAILABLE),
        "classifications": fields.get("classifications", UNAVAILABLE),
        "citations": fields.get("citations", UNAVAILABLE),
        "family_identifiers": fields.get("family_identifiers", UNAVAILABLE),
        "legal_status": fields.get("legal_status", UNAVAILABLE),
        "source_uri": fields.get("source_uri", UNAVAILABLE),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "raw_content_sha256": _raw_hash(raw_content),
    }
    return record


# === BigQuery adapter ===

class BigQueryPatentAdapter:
    """Google BigQuery patents-public-data dataset adapter.

    REQUIRES: Google Cloud service account JSON key.
    Free tier: 1 TB/month query, 10 GB/month storage.
    Dataset: patents-public-data.patents.publications
    Coverage: 100+ jurisdictions (US, CN, IN, EP, WO, JP, KR, etc.)

    Status in this environment: BLOCKED (no Google Cloud credentials available).
    """
    name = "bigquery"
    requires_credential = True
    credential_type = "Google Cloud service account JSON key"
    free_quota = "1 TB/month query, 10 GB/month storage"

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path
        self.client = None
        if credentials_path:
            try:
                from google.cloud import bigquery
                self.client = bigquery.Client.from_service_account_json(credentials_path)
            except Exception as e:
                self.init_error = str(e)

    def is_available(self) -> bool:
        return self.client is not None

    def search(self, query: str, limit: int = 10) -> List[dict]:
        if not self.is_available():
            return []
        sql = f"""
        SELECT publication_number, title_localized, abstract_localized,
               inventors_harmonized, assignee_harmonized, filing_date,
               publication_date, country_code, family_id
        FROM `patents-public-data.patents.publications`
        WHERE LOWER(title_localized) LIKE '%{query.lower()}%'
        LIMIT {limit}
        """
        try:
            results = self.client.query(sql).result()
            records = []
            for row in results:
                records.append(_normalized_record(
                    "bigquery", row.country_code, row.publication_number, b"",
                    title=row.title_localized,
                    abstract=row.abstract_localized,
                    inventors=row.inventors_harmonized,
                    assignees=row.assignee_harmonized,
                    filing_date=str(row.filing_date),
                    publication_date=str(row.publication_date),
                    family_identifiers=[row.family_id] if row.family_id else [],
                ))
            return records
        except Exception:
            return []

    def get_by_publication_number(self, pub_num: str) -> Optional[dict]:
        if not self.is_available():
            return None
        # Similar SQL query
        return None


# === EPO OPS adapter ===

class EPOOpsAdapter:
    """EPO Open Patent Services adapter.

    REQUIRES: OAuth 2.0 (consumer key + secret).
    Free threshold: ~4 GB/week for registered users.
    Coverage: EPO + 100+ national offices via INPADOC.
    Provides: biblio, full text, claims, descriptions, citations, legal status, family.

    Status in this environment: BLOCKED (returns 403 Fair Use without OAuth).
    """
    name = "epo_ops"
    requires_credential = True
    credential_type = "OAuth 2.0 consumer key + secret"
    free_quota = "~4 GB/week for registered users"
    base_url = "https://ops.epo.org/3.2/rest-services"
    token_url = "https://ops.epo.org/3.2/auth/accesstoken"

    def __init__(self, consumer_key: str = None, consumer_secret: str = None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token = None
        self.token_expiry = 0

    def is_available(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret)

    def _get_token(self) -> bool:
        if not self.is_available():
            return False
        import base64
        creds = f"{self.consumer_key}:{self.consumer_secret}".encode()
        auth = base64.b64encode(creds).decode()
        body = b"grant_type=client_credentials"
        content, status, err = _fetch(
            self.token_url,
            headers={"Authorization": f"Basic {auth}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data=body, method="POST"
        )
        if status == 200:
            data = json.loads(content)
            self.token = data.get("access_token")
            self.token_expiry = time.time() + data.get("expires_in", 1200)
            return True
        return False

    def search(self, query: str, limit: int = 10) -> List[dict]:
        if not self.is_available():
            return []
        if time.time() >= self.token_expiry:
            if not self._get_token():
                return []
        url = f"{self.base_url}/published-data/search?q=ti={urllib.parse.quote(query)}&Range=1-{limit}"
        content, status, err = _fetch(
            url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        )
        if status != 200:
            return []
        # Parse EPO OPS JSON response into normalized records
        # (Implementation omitted — adapter not available in this environment)
        return []


# === EPO LOD adapter (partial — SPARQL endpoint only) ===

class EPOLODAdapter:
    """EPO Linked Open Data adapter.

    FREE (no credentials required) but LIMITED:
    - SPARQL endpoint at https://data.epo.org/linked-data/query works
    - Only returns CPC classification data and ontology metadata
    - Does NOT return actual patent records (those require lod.apps.epo.org which returns 403)

    Useful for: CPC classification lookup, ontology queries.
    NOT useful for: patent search, claims, citations, family data.
    """
    name = "epo_lod"
    requires_credential = False
    free_quota = "No quota (limited data)"
    sparql_url = "https://data.epo.org/linked-data/query"

    def is_available(self) -> bool:
        return True

    def sparql(self, query: str) -> dict:
        """Run a SPARQL query against EPO LOD."""
        content, status, err = _fetch(
            self.sparql_url,
            headers={"Accept": "application/sparql-results+json"},
            data=urllib.parse.urlencode({"query": query}).encode(),
            method="POST"
        )
        if status == 200:
            try:
                return {"status": "success", "data": json.loads(content)}
            except Exception:
                return {"status": "error", "error": "parse failure"}
        return {"status": "error", "error": err, "http_status": status}

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """EPO LOD cannot search patents. Returns empty list."""
        return []


# === USPTO adapter ===

class USPTOAdapter:
    """USPTO Open Data Portal adapter.

    REQUIRES: API key (x-api-key header).
    Coverage: US patents and applications.
    Provides: patent number, title, abstract, claims, classifications, citations, legal status.

    Status in this environment: BLOCKED (returns 401 without API key).
    bulkdata.uspto.gov does NOT resolve via DNS in this environment.
    """
    name = "uspto"
    requires_credential = True
    credential_type = "USPTO ODP API key"
    free_quota = "Per API key (undocumented)"
    base_url = "https://api.uspto.gov/api/v1"

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 10) -> List[dict]:
        if not self.is_available():
            return []
        url = f"{self.base_url}/patent/applications/search?query={urllib.parse.quote(query)}&rows={limit}"
        content, status, err = _fetch(
            url, headers={"x-api-key": self.api_key, "Accept": "application/json"}
        )
        if status != 200:
            return []
        # Parse USPTO response
        return []


# === WIPO adapter ===

class WIPOAdapter:
    """WIPO PATENTSCOPE adapter.

    REQUIRES: WIPO account with API access.
    Coverage: PCT applications + national phase entries.
    Provides: PCT publication number, title, abstract, claims, description.

    Status in this environment: BLOCKED (returns 403 Forbidden).
    """
    name = "wipo"
    requires_credential = True
    credential_type = "WIPO PATENTSCOPE API key"
    free_quota = "Per account (undocumented)"
    base_url = "https://patentscope.wipo.int/search/ws/rest"

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 10) -> List[dict]:
        return []


# === India patent adapter ===

class IndiaPatentAdapter:
    """IP India / InPASS adapter.

    NO public API. Web search interface at ipsearch.ipindia.gov.in (DNS does not resolve in this environment).
    Main site ipindia.gov.in is HTML only.

    Status in this environment: BLOCKED (DNS resolution fails for search subdomain).
    """
    name = "india"
    requires_credential = False
    free_quota = "Web search (no API)"
    base_url = "https://ipsearch.ipindia.gov.in"

    def is_available(self) -> bool:
        # Test DNS resolution
        try:
            socket.gethostbyname("ipsearch.ipindia.gov.in")
            return True
        except Exception:
            return False

    def search(self, query: str, limit: int = 10) -> List[dict]:
        return []


# === China patent adapter ===

class ChinaPatentAdapter:
    """CNIPA patent adapter.

    NO public API. Web search interface at pss-system.cponline.cnipa.gov.cn
    (connection fails in this environment despite DNS resolving).

    Status in this environment: BLOCKED (connection fails).
    """
    name = "china"
    requires_credential = False
    free_quota = "Web search (no API)"
    base_url = "http://pss-system.cponline.cnipa.gov.cn"

    def is_available(self) -> bool:
        # Test connectivity
        content, status, err = _fetch(self.base_url, timeout=8.0, max_retries=0)
        return status == 200

    def search(self, query: str, limit: int = 10) -> List[dict]:
        return []


# === Registry ===

ADAPTERS = {
    "bigquery": BigQueryPatentAdapter,
    "epo_ops": EPOOpsAdapter,
    "epo_lod": EPOLODAdapter,
    "uspto": USPTOAdapter,
    "wipo": WIPOAdapter,
    "india": IndiaPatentAdapter,
    "china": ChinaPatentAdapter,
}


def get_adapter(name: str, **kwargs):
    """Get an adapter instance by name."""
    cls = ADAPTERS.get(name)
    if not cls:
        return None
    return cls(**kwargs)


def list_adapters() -> List[Dict[str, Any]]:
    """List all adapters and their availability status."""
    result = []
    for name, cls in ADAPTERS.items():
        result.append({
            "name": name,
            "requires_credential": cls.requires_credential,
            "credential_type": getattr(cls, "credential_type", None),
            "free_quota": getattr(cls, "free_quota", None),
        })
    return result
