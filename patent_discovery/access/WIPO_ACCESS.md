# WIPO PATENTSCOPE Access Investigation

## Endpoints

| URL | DNS resolves? | HTTP status | Notes |
|---|---|---|---|
| `https://patentscope.wipo.int/` | Yes | 200 (redirect to /search/) | Main page redirects to search |
| `https://patentscope.wipo.int/search/` | Yes | 403 Forbidden | Search page returns 403 |
| `https://patentscope.wipo.int/search/ws/rest/searchService/search` | Yes | 403 Forbidden | REST API returns 403 |

## API Availability
WIPO PATENTSCOPE has a documented REST API, but **all endpoints return 403 Forbidden** in this environment. The API requires:
- A WIPO user account
- API access enabled on the account
- Authentication (session-based or API key)

## Test Results

| Endpoint | HTTP | Result |
|---|---|---|
| `GET /` | 200 | HTML redirect to /search/ |
| `GET /search/` | 403 | Forbidden |
| `GET /search/en/search.jsf` | 403 | Forbidden |
| `GET /search/en/result.jsf?query=LED` | 403 | Forbidden |
| `GET /search/ws/rest/searchService/search?query=LED&rows=1` | 403 | Forbidden |

## Coverage (Once Registered)
- PCT international applications
- National phase entries in PCT contracting states
- Biblio, abstract, claims, description (for PCT applications)
- Family relationships via priority claims

## Fields Available
- PCT publication number
- Title (multiple languages)
- Abstract (multiple languages)
- Claims
- Description
- Inventors
- Applicants
- Classifications (IPC)
- Citations
- Family relationships

## Registration
1. Go to https://patentscope.wipo.int/en/registration/
2. Create a WIPO account (free)
3. Enable API access (if available for the account type)
4. Use credentials for API authentication

## Free Tier
- Free for registered users
- Quota: per account (undocumented in public docs)

## Downloadable Data
- WIPO PCT bulk data: https://www.wipo.int/pct/en/textprocessing/ (XML format)
- Not tested in this investigation (would require download infrastructure)

## Fallback If WIPO Fails
- EPO OPS (includes PCT data via INPADOC)
- Google Patents BigQuery (includes PCT publications)

## Verdict
**BLOCKED.** All PATENTSCOPE endpoints return 403. WIPO account registration is required. PCT data is largely redundant with EPO OPS (which includes PCT via INPADOC), so WIPO is lower priority than EPO OPS.

## Recommendation
WIPO PATENTSCOPE is Priority 4 — useful but largely redundant with EPO OPS. If EPO OPS credentials are obtained, WIPO adds marginal value (mainly for PCT-specific metadata and search syntax). If only one credential can be obtained, it should be EPO OPS, not WIPO.
