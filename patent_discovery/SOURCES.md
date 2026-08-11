# Patent Data Sources

## Authoritative Sources (Primary)

### United States

| Source | Access | Use |
|---|---|---|
| USPTO Patent Public Search | Web interface | Manual verification |
| USPTO Open Data Portal | Bulk data | Bulk ingestion |
| PatentsView API | REST API (JSON) | **Primary programmatic source for pilot** |

**PatentsView API endpoint:** `https://api.patentsview.org/patents/query`
- Returns: patent number, title, abstract, claims, inventors, assignees, classifications, citations, filing/grant dates
- Rate limit: documented; pilot uses respectful delays
- Coverage: US patents and published applications

### China

| Source | Access | Use |
|---|---|---|
| CNIPA official patent search system | Web interface | Manual verification |
| CNIPA multilingual access | Web interface | Cross-language verification |

**Programmatic access limitation:** CNIPA does not provide a public REST API for bulk patent search. The pilot handles this by:
1. Using US patents that claim CN priority (family linkage)
2. Recording CN family members where identifiable from US filings
3. Labeling CN coverage as `PARTIAL_VIA_FAMILY_LINKAGE`

**Honest limitation:** Direct CNIPA bulk access requires alternative arrangements beyond this pilot's scope.

### India

| Source | Access | Use |
|---|---|---|
| IP India public patent search | Web interface | Manual verification |
| Indian Patent Office public resources | Web interface | Cross-verification |

**Programmatic access limitation:** IP India does not provide a public REST API for bulk patent search. The pilot handles this by:
1. Using US patents that claim IN priority (family linkage)
2. Recording IN family members where identifiable from US filings
3. Labeling IN coverage as `PARTIAL_VIA_FAMILY_LINKAGE`

### Third-Party (Cross-Validation Only)

Third-party databases (e.g., commercial patent analytics platforms) may be used for cross-validation only. The originating patent record must remain identifiable. Third-party data is NEVER used as the primary source.

## Source Hierarchy

```
1. Authoritative source (USPTO / CNIPA / IP India)
       ↓
2. Patent family linkage (connect US ↔ CN ↔ IN)
       ↓
3. Third-party cross-validation (where needed)
       ↓
4. Manual verification (for high-value candidates)
```

## Coverage Honesty

| Country | Pilot coverage | Method |
|---|---|---|
| US | Direct | PatentsView API |
| CN | Partial via family | US patents with CN priority |
| IN | Partial via family | US patents with IN priority |

**The pilot does NOT claim comprehensive CN or IN coverage.** Any three-country asymmetry analysis (Discovery Mode 10) is labeled with this limitation.
