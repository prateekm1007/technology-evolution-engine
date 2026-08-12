# PATENT_FREE_ACCESS_MATRIX_V1

**Date:** 2026-08-11
**Method:** Mechanically tested every free patent data route per CTO Directive V2
**Status:** FREE_ACCESS_EXHAUSTED

---

## Summary

All free patent data sources have been mechanically tested in this environment. **None can return actual patent records without credentials.** The EPO LOD endpoint is the only free endpoint that responds successfully, but it returns only CPC classification data and ontology metadata — not patent records.

**DATA_GATE: FAILED** — 0 real patent families retrieved, 0 jurisdictions covered.

---

## Test Results Matrix

| # | Source | DNS resolves? | HTTP status | Auth required | Returns patent records? |
|---|---|---|---|---|---|
| 1 | BigQuery public patents dataset | ✓ | 401 Unauthorized | Google Cloud OAuth | NO — anonymous access forbidden |
| 2 | EPO OPS REST API | ✓ | 403 Fair Use | OAuth 2.0 (key+secret) | NO — 403 without auth |
| 3 | EPO LOD SPARQL | ✓ | 200 OK | None | NO — returns only CPC/ontology data |
| 4 | USPTO ODP API | ✓ | 401 Unauthorized | API key | NO — 401 without key |
| 5 | USPTO bulk data (bulkdata.uspto.gov) | ✗ DNS fails | N/A | N/A | NO — DNS does not resolve |
| 6 | USPTO PEDS (ped.uspto.gov) | ✗ DNS fails | N/A | N/A | NO — DNS does not resolve |
| 7 | WIPO PATENTSCOPE | ✓ | 200 (HTML only) | Account | NO — API returns 403, HTML page inaccessible |
| 8 | IP India main (ipindia.gov.in) | ✓ | 200 (HTML only) | None | NO — HTML page only, no API |
| 9 | IP India search (ipsearch.ipindia.gov.in) | ✗ DNS fails | N/A | N/A | NO — DNS does not resolve |
| 10 | CNIPA English (english.cnipa.gov.cn) | ✓ | 200 (HTML only) | None | NO — HTML page only, no API |
| 11 | CNIPA PSS (pss-system.cponline.cnipa.gov.cn) | ✓ | 0 (connection fails) | None | NO — connection fails |
| 12 | Google Patents (patents.google.com) | ✓ | 503 → CAPTCHA | None (rate-limited) | NO — CAPTCHA blocked |
| 13 | Lens.org API | ✓ | 401 Unauthorized | API key | NO — 401 without key |

---

## Per-Source Analysis

### 1. Google BigQuery Public Patent Datasets

| Item | Value |
|---|---|
| Dataset ID | `patents-public-data.patents.publications` |
| Anonymous access | **Not possible** — BigQuery requires a Google Cloud project to bill queries to |
| Free tier | 1 TB/month query, 10 GB/month storage (requires Google Cloud account) |
| Coverage | 100+ jurisdictions (US, CN, IN, EP, WO, JP, KR, etc.) |
| Fields | Full text, claims, descriptions, citations, classifications, family via priority |
| Required credential | Google Cloud service account JSON key |
| Registration | https://console.cloud.google.com/ (free account, no payment needed for free tier) |
| Test result | `401 Unauthorized` for anonymous API calls |
| Verdict | **BLOCKED** without Google Cloud account. Free tier is generous once registered. |

### 2. EPO OPS (Open Patent Services)

| Item | Value |
|---|---|
| Endpoint | `https://ops.epo.org/3.2/rest-services/` |
| Auth | OAuth 2.0 (consumer key + secret → bearer token) |
| Free threshold | ~4 GB/week for registered users |
| Coverage | EPO + 100+ national offices via INPADOC (US, CN, IN, EP, WO, JP, KR, etc.) |
| Fields | Biblio, full text, claims, descriptions, citations, legal status, INPADOC family |
| Required credential | EPO OPS consumer key + consumer secret |
| Registration | https://www.epo.org/service-support/ordering/products/ops/ordering.html (free) |
| Test result | `403 Fair Use policy violation` for ALL endpoints without OAuth |
| Verdict | **BLOCKED** without OAuth credentials. Free threshold is generous once registered. |

### 3. EPO LOD (Linked Open Data)

| Item | Value |
|---|---|
| SPARQL endpoint | `https://data.epo.org/linked-data/query` |
| Auth | None required |
| Coverage | CPC classification scheme, ontology metadata, baseline dataset creation records |
| Fields | CPC class/subclass/group titles, ontology definitions |
| Test result | `200 OK` — SPARQL queries work |
| Verdict | **PARTIAL** — works but returns only CPC classification data, NOT patent records. The actual patent data requires `lod.apps.epo.org` which returns `403`. |

**Honest assessment:** EPO LOD is useful for CPC classification lookup but cannot be used as a patent data source.

### 4. USPTO Open Data Portal (ODP) API

| Item | Value |
|---|---|
| Endpoint | `https://api.uspto.gov/api/v1/` |
| Auth | API key (`x-api-key` header) |
| Free tier | Per API key (quota undocumented) |
| Coverage | US patents and applications |
| Fields | Patent number, title, abstract, claims, classifications, citations, legal status |
| Required credential | USPTO ODP API key |
| Registration | https://data.uspto.gov/api/developer-portal (free) |
| Test result | `401 Unauthorized` without API key |
| Verdict | **BLOCKED** without API key. |

### 5. USPTO Bulk Data

| Item | Value |
|---|---|
| URL | `https://bulkdata.uspto.gov/` |
| Auth | None required |
| Coverage | US patents and applications (full text XML/JSON) |
| Test result | **DNS does not resolve** in this environment (`bulkdata.uspto.gov` NXDOMAIN) |
| Verdict | **BLOCKED** — DNS resolution fails. May be environment-specific network restriction. |

### 6. WIPO PATENTSCOPE

| Item | Value |
|---|---|
| URL | `https://patentscope.wipo.int/` |
| Auth | WIPO account (for API); none for web |
| Coverage | PCT applications + national phase entries |
| Test result | Main page returns 200 (HTML); API endpoints return `403 Forbidden` |
| Verdict | **BLOCKED** for API access. Web interface is human-only, not suitable for automated retrieval. |

### 7. IP India / InPASS

| Item | Value |
|---|---|
| Main site | `https://ipindia.gov.in/` — 200 OK (HTML only) |
| Search system | `https://ipsearch.ipindia.gov.in/` — **DNS does not resolve** |
| API | No public API |
| Coverage | India patents and applications |
| Test result | Main site accessible but search subdomain DNS fails |
| Verdict | **BLOCKED** — no API, search system DNS fails. Web-only interface. |

### 8. CNIPA

| Item | Value |
|---|---|
| English site | `http://english.cnipa.gov.cn/` — 200 OK (HTML only) |
| PSS search | `http://pss-system.cponline.cnipa.gov.cn/` — DNS resolves but **connection fails** |
| API | No public API |
| Coverage | China patents, utility models, designs |
| Test result | English site accessible but search system connection fails |
| Verdict | **BLOCKED** — no API, search system connection fails. Web-only interface. |

### 9. Google Patents

| Item | Value |
|---|---|
| URL | `https://patents.google.com/` |
| Auth | None (rate-limited) |
| Coverage | 100+ jurisdictions (aggregated from USPTO, EPO, WIPO, CNIPA, etc.) |
| Test result | `503 Service Unavailable` → CAPTCHA block page after ~5 calls |
| Verdict | **BLOCKED** — CAPTCHA/rate-limit makes automated retrieval impossible. Not a Tier 1 source anyway. |

### 10. Lens.org

| Item | Value |
|---|---|
| API | `https://api.lens.org/patent/search` |
| Auth | API key (Bearer token) |
| Free tier | Limited free quota for registered users |
| Test result | `401 Unauthorized` without API key |
| Verdict | **BLOCKED** without API key. |

---

## What "Free" Actually Means Here

| Source | Truly free (no registration)? | Free with registration? |
|---|---|---|
| BigQuery | No (needs Google Cloud account) | Yes (free tier 1 TB/month) |
| EPO OPS | No (needs OAuth) | Yes (free threshold ~4 GB/week) |
| EPO LOD | Yes (no registration) | N/A (but returns no patent records) |
| USPTO ODP | No (needs API key) | Yes (free with registration) |
| USPTO Bulk | Yes (no registration) | N/A (but DNS fails in this env) |
| WIPO | No (needs account for API) | Yes (free with registration) |
| IP India | Yes (web only) | N/A (no API at all) |
| CNIPA | Yes (web only) | N/A (no API at all) |
| Google Patents | Yes (rate-limited) | N/A (CAPTCHA blocked) |

---

## Conclusion

**No free patent data source can return actual patent records in this environment without registration.**

The credential-free paths are:
1. **EPO LOD** — works but returns only CPC classification data, not patents
2. **USPTO Bulk Data** — DNS does not resolve in this environment (likely network restriction)
3. **Google Patents** — CAPTCHA blocked after smoke test
4. **IP India / CNIPA web** — HTML only, no API, search subdomains fail

The registration-required free paths (any one unlocks real patent data):
1. **EPO OPS OAuth** (consumer key + secret) — most impactful, 100+ jurisdictions
2. **USPTO ODP API key** — richest US patent data
3. **Google Cloud account** — BigQuery patents dataset, 100+ jurisdictions
4. **WIPO account** — PCT data

**Per CTO directive: I have exhausted all free routes. The 100-family data gate cannot be met without credentials.**

---

## What Was NOT Done (Per CTO Directive)

- ❌ No synthetic data generated
- ❌ No Crossref substitution for patents
- ❌ No CAPTCHA bypassing
- ❌ No rate-limit bypassing
- ❌ No invention claims made
- ❌ No fabricating family relationships
- ❌ No treating failed queries as empty results

## What WAS Done

- ✅ All 10 free patent data sources mechanically tested
- ✅ DNS resolution tested for every hostname
- ✅ HTTP status codes recorded for every endpoint
- ✅ EPO LOD SPARQL endpoint confirmed working (returns CPC data, not patents)
- ✅ Unified adapter architecture built (`free_sources.py`)
- ✅ Source health report generated (`PATENT_SOURCE_HEALTH_REPORT_V1.json`)
- ✅ Unified gate script created (`scripts/patent_free_data_gate.sh`)
- ✅ Per-source access documents prepared (see below)

## Files Produced

| File | Contents |
|---|---|
| `patent_discovery/access/free_sources.py` | Unified adapter architecture (7 adapters) |
| `patent_discovery/access/PATENT_SOURCE_HEALTH_REPORT_V1.json` | Machine-readable health report |
| `patent_discovery/access/PATENT_FREE_ACCESS_MATRIX_V1.md` | This document |
| `patent_discovery/access/EPO_OPS_ACCESS.md` | EPO OPS access investigation |
| `patent_discovery/access/USPTO_ODP_ACCESS.md` | USPTO ODP access investigation |
| `patent_discovery/access/INDIA_ACCESS.md` | IP India access investigation |
| `patent_discovery/access/CHINA_ACCESS.md` | CNIPA access investigation |
| `patent_discovery/access/WIPO_ACCESS.md` | WIPO PATENTSCOPE access investigation |
| `scripts/patent_free_data_gate.sh` | One-command unified gate script |
