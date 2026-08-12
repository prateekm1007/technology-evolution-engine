# IP India Access Investigation

## Endpoints

| URL | DNS resolves? | HTTP status | Notes |
|---|---|---|---|
| `https://ipindia.gov.in/` | Yes | 200 | Main site, HTML only |
| `https://ipsearch.ipindia.gov.in/` | **No (NXDOMAIN)** | N/A | InPASS search system — DNS fails |
| `http://ipindia.nic.in/` | **No (NXDOMAIN)** | N/A | Old domain — DNS fails |

## API Availability
**No public REST API.** IP India provides only web-based search interfaces.

## Search System
The InPASS (Indian Patent Advanced Search System) at `ipsearch.ipindia.gov.in` is the official search interface. However, **DNS resolution fails** for this subdomain in this environment. This may be:
- Environment-specific DNS restriction
- Temporary DNS issue
- Subdomain decommissioned

The main site (`ipindia.gov.in`) loads successfully but does not provide a search API — only links to the search subdomain and HTML pages.

## Downloadable Datasets
**None publicly available.** IP India does not provide bulk data downloads.

## Lawful Automated Retrieval Options
1. **Web scraping** of the InPASS search interface (if DNS resolves) — would require respectful delays, no CAPTCHA bypass
2. **Manual search** via web browser — human-only
3. **EPO OPS INPADOC** — includes Indian patent records via INPADOC family data (requires EPO OAuth)
4. **Google Patents** — covers IN patents (but CAPTCHA blocked in this env)

## Coverage Available via Fallbacks
- EPO OPS with INPADOC: Indian patent bibliographic data, legal status, family linkage
- Google Patents BigQuery: Indian patent full text, claims (if Google Cloud access available)

## Registration
Not applicable — no API registration available from IP India.

## Verdict
**BLOCKED.** No API. Search subdomain DNS fails. The only path to Indian patent data in this environment is via EPO OPS (INPADOC) or Google Patents BigQuery — both of which require credentials.

## Recommendation
Indian patent data should be obtained via EPO OPS INPADOC once EPO OAuth credentials are available. This is the same credential that unlocks 100+ jurisdictions. No separate IP India registration is needed.
