# EPO OPS Access Investigation

## Endpoint
`https://ops.epo.org/3.2/rest-services/`

## Authentication
OAuth 2.0 with consumer key + consumer secret.
- Token URL: `https://ops.epo.org/3.2/auth/accesstoken`
- Grant type: `client_credentials`
- Token is base64-encoded `key:secret` in Authorization header
- Bearer token returned, valid ~20 minutes

## Test Results (No Credentials)

| Endpoint | HTTP | Result |
|---|---|---|
| `GET /service-info` | 403 | Fair Use policy violation |
| `GET /published-data/search?q=ti=battery` | 403 | Fair Use policy violation |
| `GET /published-data/search/biblio?q=ti=battery&Range=1-1` | 403 | Fair Use policy violation |
| `GET /published-data/publication/epodoc/EP1000000/biblio` | 403 | Fair Use policy violation |

**All endpoints return 403 without OAuth credentials.** The "Fair Use" threshold is only available to registered users with OAuth tokens.

## Free Threshold (Registered)
- ~4 GB/week query volume
- Free for research/non-commercial use
- Registration: https://www.epo.org/service-support/ordering/products/ops/ordering.html

## Coverage (Once Registered)
- EPO patents
- 100+ national offices via INPADOC, including:
  - US (USPTO)
  - CN (CNIPA)
  - IN (IP India)
  - JP (JPO)
  - KR (KIPO)
  - EP (EPO)
  - WO (WIPO PCT)
  - And 90+ other jurisdictions

## Fields Available
- Bibliographic data (title, abstract, inventors, applicants, dates)
- Full text (description, claims)
- Citations (examiner and applicant)
- Legal status (INPADOC)
- Patent family (INPADOC family — links equivalent filings across jurisdictions)
- Classification (CPC, IPC)
- Application and priority data

## Registration Instructions
1. Go to https://www.epo.org/service-support/ordering/products/ops/ordering.html
2. Create an EPO user account (free)
3. Register for OPS access
4. Receive consumer key and consumer secret
5. Use these to obtain OAuth bearer tokens
6. Use bearer token in `Authorization: Bearer <token>` header

## Fallback If EPO OPS Fails
- WIPO PATENTSCOPE (for PCT data)
- Google Patents BigQuery (for bulk data)
- Individual national offices (USPTO, CNIPA, IP India)

## Verdict
**REQUIRES_CREDENTIAL.** EPO OPS OAuth credentials (consumer key + secret) are needed. Free registration is available. Once registered, this is the single most impactful credential — unlocks 100+ jurisdictions including US, CN, and IN via INPADOC.
