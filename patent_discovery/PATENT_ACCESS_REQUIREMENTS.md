# PATENT_ACCESS_REQUIREMENTS

**Date:** 2026-08-11
**Status:** BLOCKED — credentials required to proceed
**Directive:** CTO Patent Discovery / Invention Engine V2, Section 3

> "If credentials are required: STOP and produce PATENT_ACCESS_REQUIREMENTS.md"
>
> "Do not silently substitute Crossref."

---

## Summary

The patent discovery engine requires credentials for at least one of the following sources to begin real patent data ingestion. No credential-free path to real patent data is available in the current environment (Google Patents web is blocked; USPTO bulk data requires download infrastructure not available here).

---

## Required Credentials (Priority Order)

### Priority 1: EPO OPS OAuth Credentials (MOST IMPACTFUL)

| Item | Value |
|---|---|
| **Service** | EPO Open Patent Services (OPS) |
| **Credential needed** | OAuth 2.0 consumer key + consumer secret |
| **Registration URL** | https://www.epo.org/service-support/ordering/products/ops/ordering.html |
| **Cost** | Free |
| **Quota** | ~4 GB/week (registered fair use) |
| **Permitted use** | Research, non-commercial; fair use quota |
| **Data coverage** | EPO + 100+ national offices via INPADOC (includes US, CN, IN, EP, WO, JP, KR, and more) |
| **Fields available** | Biblio, full text, claims, descriptions, citations, legal status, family (INPADOC), INPADOC family |
| **Authentication method** | OAuth 2.0: POST to `https://ops.epo.org/3.2/auth/accesstoken` with consumer key:secret (base64), receive bearer token, use in Authorization header |
| **Why this is priority 1** | Single credential unlocks 100+ jurisdictions including all 3 required countries (US, CN, IN) via INPADOC |

**What this enables:**
- Real patent records from US, CN, IN, EPO, WIPO, JP, KR, and 90+ other jurisdictions
- Patent family reconstruction via INPADOC family data
- Full text, claims, and citations
- Legal status tracking
- Citation graph (backward and forward)
- The complete data needed for the CTO's vision

**What to provide:**
```
EPO_OPS_CONSUMER_KEY=xxxxxxxxxxxx
EPO_OPS_CONSUMER_SECRET=xxxxxxxxxxxx
```

---

### Priority 2: USPTO Open Data Portal API Key

| Item | Value |
|---|---|
| **Service** | USPTO Open Data Portal (ODP) API |
| **Credential needed** | API key (passed in `x-api-key` header) |
| **Registration URL** | https://data.uspto.gov/api/developer-portal |
| **Cost** | Free |
| **Quota** | Per API key (undocumented; contact USPTO for limits) |
| **Permitted use** | Research, non-commercial |
| **Data coverage** | US patents and published applications |
| **Fields available** | Patent number, title, abstract, inventors, assignees, CPC/IPC classifications, citations, claims, legal status, office actions |
| **Authentication method** | API key in `x-api-key` HTTP header |
| **Why this is priority 2** | Provides the richest US patent data with office actions (needed for claim/failure gap analysis — Discovery Mode 2) |

**What this enables:**
- Deep US patent data including prosecution history (office actions, rejections, amendments)
- Essential for Discovery Mode 2 (Claim → Failure Gap) and Mode 9 (Patent Family Evolution)
- Structured JSON (easier to process than EPO XML)

**What to provide:**
```
USPTO_ODP_API_KEY=xxxxxxxxxxxx
```

---

### Priority 3: Google Cloud Account (for Google Patents BigQuery)

| Item | Value |
|---|---|
| **Service** | Google BigQuery — `patents-public-data.patents.publications` dataset |
| **Credential needed** | Google Cloud service account JSON key |
| **Registration URL** | https://console.cloud.google.com/ (create account, enable BigQuery API) |
| **Cost** | Free tier: 1 TB/month query, 10 GB/month storage |
| **Quota** | 1 TB/month free query |
| **Permitted use** | Research; BigQuery terms of service |
| **Data coverage** | 100+ jurisdictions (US, CN, IN, EP, WO, JP, KR, and more) |
| **Fields available** | Publication number, title, abstract, claims, description, inventors, assignees, classifications, citations, family (via priority), filing/grant dates |
| **Authentication method** | Google Cloud service account JSON key (set `GOOGLE_APPLICATION_CREDENTIALS` env var) |
| **Why this is priority 3** | Broadest coverage in a single source; free tier is generous; SQL interface is flexible |

**What this enables:**
- Bulk patent analysis across 100+ jurisdictions
- SQL-based filtering and aggregation (no rate limits, no pagination)
- Family deduplication via priority claims
- The most efficient path to the 10,000+ patent family milestone

**What to provide:**
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```
Or provide the JSON key content directly.

---

### Priority 4: WIPO PATENTSCOPE API Access

| Item | Value |
|---|---|
| **Service** | WIPO PATENTSCOPE Search API |
| **Credential needed** | WIPO account with API access |
| **Registration URL** | https://patentscope.wipo.int/en/registration/ |
| **Cost** | Free |
| **Quota** | Per account (undocumented) |
| **Permitted use** | Research; WIPO terms of use |
| **Data coverage** | PCT applications + national phase entries |
| **Fields available** | PCT publication number, title, abstract, claims, description, inventors, applicants, classifications |
| **Authentication method** | Session-based or API key (undocumented in public docs) |
| **Why this is priority 4** | PCT coverage is valuable but largely redundant with EPO OPS (which includes PCT via INPADOC) |

**What to provide:**
```
WIPO_PATENTSCOPE_API_KEY=xxxxxxxxxxxx
```

---

## What Was Tested and Failed (No Credentials)

| Source | Test | Result |
|---|---|---|
| USPTO ODP | `GET /api/v1/patent/applications/search?query=battery` | 401 Unauthorized |
| USPTO PatentsView (legacy) | `POST /patents/query` | 301 redirect to ODP |
| USPTO PatentsView (new) | `POST /api/v1/patent/` | Empty response / connection failed |
| EPO OPS | `GET /rest-services/published-data/search/biblio?q=ti=battery` | 403 Fair Use violation |
| WIPO PATENTSCOPE | `GET /search/ws/rest/searchService/search` | 403 Forbidden |
| CNIPA web | `GET http://english.cnipa.gov.cn` | 200 (HTML only, no API) |
| IP India web | `GET https://ipindia.gov.in` | 200 (HTML only, no API) |
| Google Patents (web) | `GET https://patents.google.com/patent/US11234567B2/en` | 503 → CAPTCHA block |
| Google Patents (search API) | `GET /xhr/query?url=...` | 503 after ~5 calls |
| OpenAlex | `GET /works?search=...` | 429 budget exhausted |
| Crossref | `GET /works?query=...` | 200 (but NOT a patent source) |

---

## What the Coder Will NOT Do

1. **Will NOT use Crossref as a patent corpus** (per CTO directive Section 2)
2. **Will NOT use synthetic/mock patent data** (per CTO directive Section 22)
3. **Will NOT claim invention discovery without real patent data** (per CTO directive Section 22)
4. **Will NOT scrape Google Patents aggressively** (rate-limited; unreliable)
5. **Will NOT silently substitute one source for another** (per CTO directive Section 3)

---

## What the Coder WILL Do Once Credentials Are Provided

### With EPO OPS credentials (Priority 1):
1. Build EPO OPS OAuth adapter (token refresh, rate-limit handling, checkpoint/resume)
2. Fetch one real patent from each of: US, CN, IN, EP, WO
3. Produce `PATENT_DATA_GATE_V1.md` with real patent identifiers, hashes, and provenance
4. Scale to 100 real patent families
5. Run data quality gate checks
6. Proceed to discovery mining if gate passes

### With USPTO ODP credentials (Priority 2):
1. Build USPTO ODP adapter
2. Fetch US patents with claims, office actions, legal status
3. Enable Discovery Mode 2 (Claim → Failure Gap) with prosecution history

### With Google Cloud credentials (Priority 3):
1. Build BigQuery adapter
2. Bulk query 100+ jurisdictions
3. Efficiently scale to 10,000+ patent families
4. Run family deduplication via priority claims

---

## Standing Down

The coder has produced this requirements document per CTO directive. No further patent discovery work will be attempted until credentials are provided or the custodian directs an alternative path.

**The Crossref proxy experiment is preserved as `PROXY_PIPELINE_DEMONSTRATION` — a failed/limited experiment that proves the document-processing scaffold exists but provides no evidence of real patent discovery capability.**

The North Star frozen experiment and independent scientific corpus remain untouched.
