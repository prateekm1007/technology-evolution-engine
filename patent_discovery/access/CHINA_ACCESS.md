# CNIPA (China) Access Investigation

## Endpoints

| URL | DNS resolves? | HTTP status | Notes |
|---|---|---|---|
| `http://english.cnipa.gov.cn/` | Yes | 200 | English site, HTML only |
| `http://pss-system.cponline.cnipa.gov.cn/` | Yes | 0 (connection fails) | PSS search system — DNS resolves but connection fails |

## API Availability
**No public REST API.** CNIPA provides only web-based search interfaces.

## Search System
The Patent Search System (PSS) at `pss-system.cponline.cnipa.gov.cn` is the official search interface. DNS resolves to a valid IP, but **connection attempts fail** (HTTP 0). This may be:
- Server-side blocking of non-Chinese IPs
- Network-level restriction in this environment
- Server temporarily unavailable

The English main site (`english.cnipa.gov.cn`) loads successfully but does not provide a search API — only links to the PSS search system and HTML pages.

## Downloadable Datasets
**None publicly available via API.** CNIPA does not provide bulk data downloads through public APIs.

## Lawful Automated Retrieval Options
1. **Web scraping** of the PSS search interface (if connection works) — would require respectful delays, no CAPTCHA bypass
2. **Manual search** via web browser — human-only
3. **EPO OPS INPADOC** — includes Chinese patent records via INPADOC family data (requires EPO OAuth)
4. **Google Patents** — covers CN patents (but CAPTCHA blocked in this env)

## Coverage Available via Fallbacks
- EPO OPS with INPADOC: Chinese patent bibliographic data, legal status, family linkage
- Google Patents BigQuery: Chinese patent full text, claims (if Google Cloud access available)

## Registration
Not applicable for API access. CNIPA account registration is available on the website but only provides web search features, not API access.

## Verdict
**BLOCKED.** No API. PSS search system connection fails. The only path to Chinese patent data in this environment is via EPO OPS (INPADOC) or Google Patents BigQuery — both of which require credentials.

## Recommendation
Chinese patent data should be obtained via EPO OPS INPADOC once EPO OAuth credentials are available. This is the same credential that unlocks 100+ jurisdictions. No separate CNIPA registration is needed.

## EPO/WIPO Coverage of Chinese Patents
EPO INPADOC includes:
- CN patent publications (bibliographic data)
- CN legal status events
- CN family relationships (priority claims)
- CN citations (where available)

What INPADOC does NOT include for CN patents:
- Full text in Chinese (only English translations where available)
- Detailed prosecution history (office actions)
- CN-specific legal status nuances

For full Chinese patent text, Google Patents BigQuery is the fallback (covers CN full text and claims).
