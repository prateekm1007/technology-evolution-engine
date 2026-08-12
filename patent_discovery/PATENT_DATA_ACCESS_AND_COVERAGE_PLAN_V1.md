# PATENT_DATA_ACCESS_AND_COVERAGE_PLAN_V1

**Date:** 2026-08-11
**Author:** Coder
**Directive:** CTO Patent Discovery / Invention Engine V2, Section 28
**Status:** CREDENTIALS REQUIRED — cannot proceed without authorization

---

## Executive Summary

**No Tier 1 or Tier 2 patent data source is accessible in the current environment without credentials.** All four required jurisdictions (US, CN, IN, EPO/WIPO) require either API keys, OAuth registration, or bulk data download arrangements that are not available in this sandboxed environment.

Per CTO directive Section 3: "If credentials are required: STOP and produce `PATENT_ACCESS_REQUIREMENTS.md`."

This document is the access plan. The companion document `PATENT_ACCESS_REQUIREMENTS.md` documents the specific credentials needed.

---

## Source-by-Source Test Results

### 1. USPTO Open Data Portal (ODP)

| Item | Value |
|---|---|
| URL | `https://api.uspto.gov/api/v1/patent/applications/search` |
| Test query | `?query=battery&rows=1` |
| HTTP status | **401 Unauthorized** |
| Response | `{"message":"Unauthorized"}` |
| Auth required | **Yes — API key** |
| Registration | https://data.uspto.gov/api/developer-portal |
| Cost | Free for basic tier |
| Fields available | Patent number, title, abstract, inventors, assignees, classifications, citations, claims (varies by endpoint) |
| Rate limit | Per API key (undocumented in public docs) |
| Fallback if unavailable | USPTO bulk data download (see §2) |

### 2. USPTO PatentsView API (legacy)

| Item | Value |
|---|---|
| URL | `https://api.patentsview.org/patents/query` (legacy), `https://search.patentsview.org/api/v1/patent/` (new) |
| Test query | POST with query body |
| HTTP status | **000 (connection failed) / 301 redirect to ODP** |
| Response | PatentsView has migrated to USPTO ODP. Legacy endpoint returns 301. New endpoint returns empty response. |
| Auth required | **Yes — migrating to ODP API key** |
| Registration | https://patentsview.org/ |
| Cost | Free |
| Fields available | Patent number, title, abstract, inventors, assignees, CPC/IPC classifications, citations, claims |
| Fallback if unavailable | USPTO ODP (see §1) |

### 3. EPO Open Patent Services (OPS)

| Item | Value |
|---|---|
| URL | `https://ops.epo.org/3.2/rest-services/` |
| Test query | `published-data/search/biblio?q=ti=battery&Range=1-1` |
| HTTP status | **403 Forbidden — Fair Use policy violation** |
| Response | "This request has been rejected due to the violation of Fair Use policy" |
| Auth required | **Yes — OAuth 2.0 (consumer key + secret)** |
| Registration | https://www.epo.org/service-support/ordering/products/ops/ordering.html |
| Cost | Free for fair use (quota-limited) |
| Quota | 4 requests/week for unregistered; registered: ~4 GB/week |
| Fields available | Biblio, full text, claims, descriptions, citations, legal status, family (INPADOC) |
| Coverage | EPO + 100+ national offices via INPADOC |
| Fallback if unavailable | WIPO PATENTSCOPE (see §4) |

### 4. WIPO PATENTSCOPE

| Item | Value |
|---|---|
| URL | `https://patentscope.wipo.int/search/ws/rest/searchService/search` |
| Test query | `?query=battery&start=0&rows=1` |
| HTTP status | **403 Forbidden** |
| Response | HTML error page "ERROR 403 FORBIDDEN" |
| Auth required | **Yes — WIPO account + API access** |
| Registration | https://patentscope.wipo.int/en/registration/ |
| Cost | Free for registered users |
| Fields available | PCT applications, national phase entries, biblio, claims, descriptions |
| Coverage | PCT (WIPO) + national phase entries |
| Fallback if unavailable | EPO OPS (see §3) |

### 5. CNIPA (China National Intellectual Property Administration)

| Item | Value |
|---|---|
| URL | `http://english.cnipa.gov.cn` (web interface) |
| Test query | HTTP GET to homepage |
| HTTP status | **200 (HTML page loads)** |
| API available | **No public REST API for bulk patent search** |
| Access method | Web search interface only (http://pss-system.cponline.cnipa.gov.cn/) |
| Auth required | **Yes — CNIPA account for advanced search** |
| Registration | http://english.cnipa.gov.cn/ |
| Cost | Free |
| Fields available | CN patent numbers, titles, abstracts, claims, citations (via web interface) |
| Coverage | China patents and utility models |
| Fallback if unavailable | EPO OPS (INPADOC includes CN data), Google Patents (Tier 3) |

### 6. IP India (Indian Patent Office)

| Item | Value |
|---|---|
| URL | `https://ipindia.gov.in` (web interface) |
| Test query | HTTP GET to homepage |
| HTTP status | **200 (HTML page loads)** |
| API available | **No public REST API for bulk patent search** |
| Access method | Web search interface only (InPASS — Indian Patent Advanced Search System) |
| Auth required | **No for basic search; account for advanced features** |
| Registration | https://ipindia.gov.in/ |
| Cost | Free |
| Fields available | IN patent numbers, titles, abstracts, claims, citations (via web interface) |
| Coverage | India patents and applications |
| Fallback if unavailable | EPO OPS (INPADOC includes IN data), Google Patents (Tier 3) |

### 7. Google Patents (Tier 3 — secondary source)

| Item | Value |
|---|---|
| URL | `https://patents.google.com/` (web), `https://patents.google.com/xhr/query` (search API) |
| Test query | Individual patent page + search API |
| HTTP status | **503 Service Unavailable** (after ~5 calls), then CAPTCHA block page |
| Auth required | No, but rate-limited aggressively |
| Coverage | Aggregates US, CN, IN, EP, WO, and 100+ jurisdictions |
| Fields available | Full text, claims, citations, classifications, family linkages |
| Fallback if unavailable | None at Tier 3 |
| **HONEST ASSESSMENT** | **Blocked in this environment after initial smoke test. Cannot be relied upon for production.** |

### 8. OpenAlex (supplementary — scientific literature, not patents)

| Item | Value |
|---|---|
| URL | `https://api.openalex.org/works` |
| HTTP status | **429 Too Many Requests — budget exhausted** |
| Reset | Midnight UTC |
| Use case | Scientific literature cross-reference (not patent data) |

### 9. Crossref (supplementary — scientific literature, NOT patents)

| Item | Value |
|---|---|
| URL | `https://api.crossref.org/works` |
| HTTP status | **200 (operational)** |
| Use case | Scientific literature only. **NOT a patent source.** Per CTO directive: "Never use Crossref as the patent corpus." |
| Current role | Was incorrectly used as proxy in the relabeled PROXY_PIPELINE_DEMONSTRATION. That experiment is preserved as a failed/limited experiment. |

---

## Answers to the 12 Required Questions

### 1. How will we obtain US patent data?

**Primary:** USPTO Open Data Portal API (`https://api.uspto.gov/api/v1/`) — requires API key registration at https://data.uspto.gov/api/developer-portal.

**Secondary:** USPTO PatentsView (migrating to ODP) — same auth.

**Bulk fallback:** USPTO bulk data downloads at https://bulkdata.uspto.gov/ (no API key required for bulk download; large files, nightly/weekly updates).

**Current status:** BLOCKED — no API key available. Bulk download is the only credential-free path.

### 2. How will we obtain CN patent data?

**Primary:** CNIPA web search system (http://pss-system.cponline.cnipa.gov.cn/) — web interface, no public API.

**Secondary:** EPO OPS (INPADOC includes CN patent records) — requires EPO OAuth credentials.

**Tertiary:** Google Patents (Tier 3) — covers CN patents but rate-limited.

**Current status:** BLOCKED — no API access, no CNIPA credentials, Google Patents blocked.

### 3. How will we obtain IN patent data?

**Primary:** IP India InPASS web search (https://ipsearch.ipindia.gov.in/) — web interface, no public API.

**Secondary:** EPO OPS (INPADOC includes IN patent records) — requires EPO OAuth credentials.

**Tertiary:** Google Patents (Tier 3) — covers IN patents but rate-limited.

**Current status:** BLOCKED — no API access, Google Patents blocked.

### 4. How will we obtain EPO/WIPO data?

**EPO:** EPO OPS API (`https://ops.epo.org/3.2/rest-services/`) — requires OAuth 2.0 consumer key + secret. Registration at https://www.epo.org/service-support/ordering/products/ops/ordering.html. Free for fair use (~4 GB/week quota).

**WIPO:** PATENTSCOPE API (`https://patentscope.wipo.int/search/ws/rest/`) — requires WIPO account with API access. Registration at https://patentscope.wipo.int/en/registration/.

**Current status:** BLOCKED — no EPO OAuth credentials, no WIPO API credentials.

### 5. Which APIs require credentials?

| API | Auth type | Required credential |
|---|---|---|
| USPTO ODP | API key (header: `x-api-key`) | API key from https://data.uspto.gov/api/developer-portal |
| USPTO PatentsView | API key (migrating to ODP) | Same as ODP |
| EPO OPS | OAuth 2.0 (consumer key + secret → bearer token) | EPO OPS account at https://www.epo.org/service-support/ordering/products/ops/ordering.html |
| WIPO PATENTSCOPE | WIPO account + API key | WIPO account at https://patentscope.wipo.int/en/registration/ |
| CNIPA | Web account (for advanced search) | CNIPA account at http://english.cnipa.gov.cn/ |
| IP India | Web account (optional for basic search) | IP India account at https://ipindia.gov.in/ |
| Google Patents | None (but rate-limited) | N/A (blocked after ~5 calls) |

### 6. Which official bulk datasets are available?

| Source | URL | Format | Access |
|---|---|---|---|
| USPTO Bulk Data | https://bulkdata.uspto.gov/ | XML, JSON | **Free, no API key** |
| EPO OPS Bulk | https://www.epo.org/service-support/ordering.html | XML | Paid (subscription) |
| WIPO PCT Bulk | https://www.wipo.int/pct/en/textprocessing/ | XML | Free for PCT data |
| CNIPA Bulk | Not publicly available via API | — | N/A |
| IP India Bulk | Not publicly available via API | — | N/A |
| Google Patents Bulk | https://console.cloud.google.com/marketplace/details/google_patents_public_datasets | BigQuery | **Free (Google BigQuery public dataset)** |

**Note:** USPTO Bulk Data and Google Patents BigQuery public dataset are the two credential-free paths for bulk patent access. However, USPTO bulk data is large XML files (nightly/weekly dumps), and Google Patents BigQuery requires a Google Cloud account (free tier available).

### 7. What are the quotas?

| Source | Quota |
|---|---|
| USPTO ODP | Per API key (undocumented; contact USPTO for limits) |
| EPO OPS | 4 GB/week for registered users |
| WIPO PATENTSCOPE | Per account (undocumented) |
| Google Patents | ~5 calls before rate limit (no documented quota) |
| USPTO Bulk Data | No quota (bulk download) |
| Google Patents BigQuery | 1 TB/month free query (BigQuery free tier) |

### 8. What are the licensing/use constraints?

| Source | License | Use constraint |
|---|---|---|
| USPTO | Public domain (US government work) | No restriction |
| EPO | EPO data license | Attribution required; fair use quota |
| WIPO | WIPO data license | Attribution required; PCT data free |
| CNIPA | CNIPA terms of use | Research/non-commercial use |
| IP India | IP India terms | Research/non-commercial use |
| Google Patents | Google Terms of Service | No bulk scraping; API not officially provided |

### 9. What fields are available?

| Field | USPTO | EPO OPS | WIPO | CNIPA | IP India | Google Patents |
|---|---|---|---|---|---|---|
| Patent number | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Title | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Abstract | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Claims | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Full description | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Inventors | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Assignees | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Classifications (CPC/IPC) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Citations (backward) | ✓ | ✓ | ✓ | partial | partial | ✓ |
| Citations (forward) | ✓ | ✓ | — | — | — | ✓ |
| Family (INPADOC) | partial | ✓ | partial | — | — | partial |
| Legal status | ✓ | ✓ | partial | ✓ | ✓ | partial |
| Office actions | ✓ | — | — | — | — | — |

### 10. What is the fallback if each source fails?

| Source | Fallback |
|---|---|
| USPTO ODP API | USPTO Bulk Data download (https://bulkdata.uspto.gov/) |
| EPO OPS | WIPO PATENTSCOPE (for PCT data); Google Patents BigQuery |
| WIPO PATENTSCOPE | EPO OPS; Google Patents BigQuery |
| CNIPA web | EPO OPS (INPADOC); Google Patents BigQuery |
| IP India web | EPO OPS (INPADOC); Google Patents BigQuery |
| Google Patents web | Google Patents BigQuery (different infrastructure) |

**Ultimate fallback:** Google Patents BigQuery public dataset (`patents-public-data.patents.publications`) — covers 100+ jurisdictions, free via BigQuery free tier (1 TB/month). Requires Google Cloud account.

### 11. How will raw documents be preserved?

- Every fetched patent record is stored as a JSON file in `patent_discovery/ingestion/raw/`
- Each record includes: `source`, `source_url`, `retrieval_timestamp`, `raw_response_hash`
- Raw HTML/XML responses are preserved in `patent_discovery/ingestion/raw_html/` (for audit trail)
- A manifest file (`ingestion_manifest.jsonl`) records every fetch attempt with status, timestamp, and hash
- Checkpoint/resume is supported via the manifest

### 12. How will provenance be cryptographically sealed?

- Every ingested patent record gets a `record_hash` (SHA-256 of canonical JSON)
- Every batch of ingested records gets a `batch_hash` (SHA-256 of all record hashes, sorted)
- A `provenance_chain.json` file records: source, query, timestamp, record_count, batch_hash, previous_batch_hash (chain)
- The provenance chain is append-only — new batches reference the previous batch hash
- A daily `provenance_seal.json` is produced with the final batch hash of the day, signed with a custodian key (when available)

---

## Data Quality Gate (Section 22)

The data gate cannot be passed in the current environment. The gate requires:

| Gate criterion | Status |
|---|---|
| ≥100 real patent families | ❌ 0 (no API access) |
| ≥3 jurisdictions represented | ❌ 0 (no API access) |
| ≥80% have claims or equivalent | ❌ N/A |
| ≥80% have usable technical text | ❌ N/A |
| Family deduplication demonstrated | ❌ N/A |
| Citation graph demonstrated | ❌ N/A |
| Provenance recorded | ❌ N/A |
| Source URLs recorded | ❌ N/A |
| Retrieval timestamps recorded | ❌ N/A |
| Raw source hashes recorded | ❌ N/A |
| Rate-limit handling tested | ❌ N/A |
| Checkpoint/resume tested | ❌ N/A |

**DATA_GATE_FAILED** — cannot proceed to discovery mining.

---

## Recommendation

The credential-free paths available in this environment are:

1. **USPTO Bulk Data download** (https://bulkdata.uspto.gov/) — large XML/JSON files, no API key
2. **Google Patents BigQuery public dataset** — requires Google Cloud account (free tier)
3. **Google Patents web scraping** — blocked in this environment (503/CAPTCHA)

To proceed with the CTO's vision, the custodian must authorize one of:

**Option A:** Provide EPO OPS OAuth credentials (consumer key + secret). This unlocks EPO + INPADOC (covers 100+ jurisdictions including CN and IN). This is the single most impactful credential.

**Option B:** Provide USPTO ODP API key. This unlocks structured US patent data with claims, citations, and legal status.

**Option C:** Provide Google Cloud account credentials. This unlocks the Google Patents BigQuery public dataset (100+ jurisdictions, free 1 TB/month query tier).

**Option D:** Authorize bulk download from https://bulkdata.uspto.gov/ (no credentials needed, but large file sizes may exceed environment storage/time limits).

---

## Conclusion

The patent discovery engine cannot operate without real patent data. The Crossref proxy experiment (now relabeled `PROXY_PIPELINE_DEMONSTRATION`) is preserved as evidence that the document-processing scaffold works, but it is NOT patent discovery.

The companion document `PATENT_ACCESS_REQUIREMENTS.md` lists the exact credentials needed to proceed.
