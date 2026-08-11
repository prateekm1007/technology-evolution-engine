# USPTO ODP Access Investigation

## Endpoint
`https://api.uspto.gov/api/v1/`

## Authentication
API key in `x-api-key` HTTP header.

## Test Results (No Credentials)

| Endpoint | HTTP | Result |
|---|---|---|
| `GET /api/v1/patent/applications/search?query=battery&rows=1` | 401 | Unauthorized |
| `GET /api/v1/patent/grants/search?query=battery&rows=1` | 403 | Missing Authentication Token |
| `GET /api/v1/datasets` | 403 | Missing Authentication Token |

## Bulk Data

| URL | DNS resolves? | Status |
|---|---|---|
| `https://bulkdata.uspto.gov/` | **No** (NXDOMAIN) | DNS resolution fails in this environment |
| `https://ped.uspto.gov/` | **No** (NXDOMAIN) | DNS resolution fails in this environment |
| `https://search.patentsview.org/` | **No** (NXDOMAIN) | DNS resolution fails in this environment |

**Note:** `bulkdata.uspto.gov`, `ped.uspto.gov`, and `search.patentsview.org` do not resolve via DNS in this environment. This may be an environment-specific network restriction. These endpoints are documented as public USPTO services but are unreachable here.

## Registration (For API Key)
1. Go to https://data.uspto.gov/api/developer-portal
2. Create a USPTO developer account
3. Register an application
4. Receive API key
5. Use API key in `x-api-key` header

## Coverage (Once Registered)
- US patents (granted)
- US patent applications (published)
- US prosecution history (office actions, rejections, amendments) — via PEDS if accessible

## Fields Available
- Patent number, title, abstract
- Inventors, assignees
- CPC and IPC classifications
- Citations (backward and forward)
- Claims (full text)
- Legal status
- Office actions (PEDS — if accessible)

## Free Tier
- Free with registration
- Rate limits per API key (undocumented in public docs)

## Fallback If USPTO Fails
- EPO OPS (INPADOC includes US patent records)
- Google Patents BigQuery (includes US patents)
- USPTO bulk data download (if DNS resolves — currently fails in this env)

## Verdict
**REQUIRES_CREDENTIAL.** USPTO ODP API key is needed. Additionally, the bulk data subdomains (bulkdata.uspto.gov, ped.uspto.gov) have DNS resolution failures in this environment, suggesting a network-level block that may require alternative network access to bypass.
