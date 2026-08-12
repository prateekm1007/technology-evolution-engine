# PROXY_PIPELINE_DEMONSTRATION

**STATUS: FAILED / LIMITED EXPERIMENT — PRESERVED AS FORENSIC EVIDENCE**
**Relabeled:** 2026-08-11 per CTO Directive V2 Section 27
**Original label:** PATENT_DISCOVERY_PILOT_REPORT_V1 (withdrawn)

> This is NOT a patent discovery pilot. It is a document-processing scaffold that used Crossref patent-literature as a proxy because all direct patent APIs were blocked. It provides NO evidence of real global patent discovery capability. Preserved as a failed/limited experiment per CTO directive. Do not cite as evidence of discovery capability.

---

## Honest Status

**This pilot is INFRASTRUCTURE VALIDATION, not scientific evidence of discovery capability.**

The pilot successfully validated the end-to-end pipeline (ingestion → family dedup → mechanism extraction → knowledge graph → discovery modes → prior-art firewall). However, the pilot used **Crossref patent-literature as a proxy** for direct patent records because all major patent APIs (Google Patents, PatentsView/USPTO, EPO OPS) were rate-limited or blocked in this environment.

---

## 1. Pilot Ingestion

### Target
500 patent families across:
- 8 technology domains (materials, energy, mechanical, electronics, computing/AI, biotech, chemical, manufacturing)
- 3 countries (US, CN, IN)

### Actual Source
**Crossref** — searched for patent-related literature using domain-specific queries including the keyword "patent".

### Honest Limitation
Direct patent APIs were unavailable:
| API | Status | Result |
|---|---|---|
| Google Patents (xhr/query) | HTTP 503 after ~5 calls | Blocked |
| PatentsView / USPTO ODP | Migrated to new endpoint; returns HTML not JSON | Unusable |
| EPO OPS | HTTP 403 — Fair Use policy violation | Blocked |
| OpenAlex | HTTP 429 — budget exhausted | Blocked |
| Crossref | Operational | **Used as proxy** |

### Ingestion Results

| Metric | Value |
|---|---|
| Records fetched | 504 |
| Unique records (deduplicated) | 504 |
| With abstracts | 78 (15.5%) |
| With citations | 189 (37.5%) |
| By domain | 63 per domain × 8 domains = 504 |
| By country (proxy) | XX: 317, US: 147, EU: 39, CN: 1, IN: 0 |
| Elapsed time | 20.7 seconds |

### Country Coverage — Honest Disclosure

The pilot **failed to achieve balanced US/CN/IN coverage**. The country labels in this pilot are inferred from Crossref publisher fields, NOT from patent office filings. True three-country (US/CN/IN) patent analysis requires direct patent API access which was unavailable.

**The three-country asymmetry analysis (Discovery Mode 10) in this pilot is NOT scientifically valid** because the underlying data does not contain real CN or IN patent records. Any asymmetry findings reflect Crossref coverage bias, not patent landscape reality.

---

## 2. Family Deduplication

| Metric | Value |
|---|---|
| Records before dedup | 504 |
| Unique patent_ids | 504 |
| Duplicates removed | 0 |

**Note:** True patent family deduplication (grouping US + CN + IN filings of the same invention) requires priority application numbers, which Crossref records do not reliably contain. The pilot deduplicated by patent_id only. A production system with direct patent API access would perform family-level dedup using priority numbers.

---

## 3. Mechanism Extraction

### LLM-Based Extraction
| Metric | Value |
|---|---|
| Patents with abstracts (eligible) | 78 |
| LLM extraction attempted | 10 |
| LLM mechanisms extracted | 0 |
| Status | `z-ai-web-dev-sdk not available` (Python module not found in this context) |

### Keyword-Based Extraction (Fallback)
| Metric | Value |
|---|---|
| Patents processed | 78 |
| Keyword mechanisms extracted | 66 |
| Unique mechanism types | 12 |
| Extraction method | keyword matching in abstracts |
| Epistemic category | OBSERVED (keyword presence is directly measurable) |

**12 mechanism types identified:**
electrochemical, photovoltaic, catalytic, thermal, mechanical, electromagnetic, chemical synthesis, additive manufacturing, neural network, gene editing, semiconductor, nanoparticle

---

## 4. Knowledge Graph

| Entity | Count |
|---|---|
| Patents | 504 |
| Mechanisms | 12 |
| Materials | 0 (LLM extraction failed) |
| Domains | 8 |
| Countries | 4 (proxy labels) |

| Edge Type | Count |
|---|---|
| USES_MECHANISM | 66 |
| CITES | 4,977 |
| **Total edges** | **5,043** |

---

## 5. Discovery Mode Analysis

### Candidates Generated: 44

| Discovery Mode | Candidates |
|---|---|
| Mode 3: Cross-Domain Transfer | 31 |
| Mode 5: Performance Anomalies | 6 |
| Mode 10: Three-Country Asymmetry | 7 |
| Modes 1, 2, 4, 6, 7, 8, 9 | 0 (not implemented in pilot) |

### Prior-Art Firewall Results

| Firewall Label | Count |
|---|---|
| ADJACENT_PRIOR_ART | 18 |
| UNVERIFIED_ABSENCE | 13 |
| SKIPPED (no mechanism) | 13 |

**No candidate was labeled `NEW INVENTION`.** This is by design — the protocol prohibits that label.

### Novelty Status

| Status | Count |
|---|---|
| UNVERIFIED | 37 |
| ABSENCE_OF_EVIDENCE | 7 |

**No candidate was labeled `NOVEL`.** Absence was correctly labeled `ABSENCE_OF_EVIDENCE`, never `NOVEL`.

---

## 6. Required Pilot Metrics

| # | Metric | Value |
|---|---|---|
| 1 | Number ingested | 504 |
| 2 | Number successfully family-deduplicated | 504 (by patent_id; true family dedup pending) |
| 3 | Number with claims | 0 (Crossref records do not contain patent claims) |
| 4 | Number with citations | 189 |
| 5 | Number with usable technical text | 78 (abstracts) |
| 6 | Number of mechanisms extracted | 66 keyword + 0 LLM = 66 total |
| 7 | Number of anomalies | 6 |
| 8 | Number of transfer candidates | 31 |
| 9 | Number of candidate inventions | 0 (no candidate reached INVENTION CANDIDATE status) |
| 10 | Number rejected as rediscovery | 0 |
| 11 | Number requiring human review | 44 (all candidates) |

---

## 7. Honest Assessment

### What Worked
- ✅ Pipeline architecture is sound (ingestion → dedup → extraction → graph → discovery modes → firewall)
- ✅ Knowledge graph schema is functional (504 patents, 12 mechanisms, 5,043 edges)
- ✅ Prior-art firewall correctly labeled candidates (18 ADJACENT_PRIOR_ART, 13 UNVERIFIED_ABSENCE)
- ✅ Absence correctly labeled `ABSENCE_OF_EVIDENCE` — never `NOVEL`
- ✅ No candidate was labeled `NEW INVENTION` or `VERIFIED DISCOVERY`
- ✅ Epistemic categories preserved (OBSERVED ≠ INFERRED ≠ HYPOTHESIS)
- ✅ Scoring is multi-dimensional (no magic score)
- ✅ Isolation from North Star experiment maintained

### What Did Not Work
- ❌ Direct patent API access (all major APIs blocked/rate-limited)
- ❌ Three-country coverage (no real CN or IN patent records)
- ❌ LLM mechanism extraction (z-ai-web-dev-sdk not available in Python context)
- ❌ Claims extraction (Crossref records don't contain patent claims)
- ❌ True family deduplication (no priority application numbers)
- ❌ 7 of 10 discovery modes not implemented (Modes 1, 2, 4, 6, 7, 8, 9)

### What This Pilot Proves
The infrastructure is **functional but data-constrained**. Given direct patent API access, the same pipeline would:
1. Fetch real US/CN/IN patent records with claims, citations, and family data
2. Extract mechanisms via LLM (requires SDK availability)
3. Build a richer knowledge graph with materials, processes, and failure modes
4. Run all 10 discovery modes
5. Produce candidates with real mechanistic bridges (not just keyword overlap)

### What This Pilot Does NOT Prove
- ❌ That the engine can discover anything novel
- ❌ That the 10 discovery modes produce useful candidates
- ❌ That the prior-art firewall is effective at catching rediscovery
- ❌ That the scoring dimensions correlate with invention quality

**All of these require a production run with real patent data.**

---

## 8. Candidate Sample

### Example: Cross-Domain Transfer Candidate

```json
{
  "candidate_id": "CDM3-...",
  "discovery_type": "CROSS_DOMAIN_TRANSFER",
  "source_domain": "energy",
  "target_domain": "materials",
  "mechanism": "lithium-based",
  "source_patents": ["CR-10.1016/j.est.2024.112894", ...],
  "evidence": [
    {
      "type": "mechanism_present_in_source",
      "domain": "energy",
      "patent_ids": ["CR-10.1016/j.est.2024.112894"],
      "epistemic": "OBSERVED"
    },
    {
      "type": "mechanism_absent_in_target",
      "domain": "materials",
      "epistemic": "ABSENCE_OF_EVIDENCE"
    }
  ],
  "cross_domain_bridge": "NOT_YET_ESTABLISHED — requires mechanistic bridge, not mere similarity",
  "novelty_status": "UNVERIFIED",
  "patentability_status": "UNASSESSED",
  "prior_art_firewall": "ADJACENT_PRIOR_ART"
}
```

**Note the cross_domain_bridge is `NOT_YET_ESTABLISHED`.** This is correct — the pilot did not attempt mechanistic bridge analysis. A candidate without a mechanistic bridge is NOT an invention candidate. It is a hypothesis at best.

---

## 9. Recommendation

To make this pilot scientifically meaningful:

1. **Obtain direct patent API access:**
   - USPTO Open Data Portal API key
   - EPO OPS API key (with Fair Use compliance)
   - CNIPA bulk data access (if available)
   - IP India bulk data access (if available)

2. **Re-run pilot with real patent records** covering US/CN/IN across 8 domains

3. **Enable LLM mechanism extraction** (install z-ai-web-dev-sdk in the execution environment)

4. **Implement remaining 7 discovery modes** (Modes 1, 2, 4, 6, 7, 8, 9)

5. **Run prior-art firewall** with full citation graph (not just abstract keyword match)

6. **Have human reviewers evaluate** the 44 candidates for technical coherence

---

## 10. Files Produced

| File | Contents |
|---|---|
| `patent_discovery/README.md` | Workstream overview |
| `patent_discovery/PROTOCOL_V1.md` | Detailed protocol |
| `patent_discovery/SOURCES.md` | Patent data sources |
| `patent_discovery/ingestion/google_patents_adapter.py` | Google Patents adapter (blocked by 503) |
| `patent_discovery/ingestion/patentsview_adapter.py` | PatentsView adapter (API migrated) |
| `patent_discovery/pilot_runner_v3.py` | Pilot runner using Crossref proxy |
| `patent_discovery/discovery_analyzer.py` | Discovery mode analyzer |
| `patent_discovery/families/pilot_patents.jsonl` | 504 patent-literature records |
| `patent_discovery/families/pilot_families.json` | Deduplicated family file |
| `patent_discovery/mechanisms/extracted_mechanisms.json` | 66 keyword-extracted mechanisms |
| `patent_discovery/graph/knowledge_graph.json` | Knowledge graph (504 patents, 5,043 edges) |
| `patent_discovery/discovery_candidates/candidates.json` | 44 discovery candidates |
| `patent_discovery/reports/pilot_stats.json` | Ingestion statistics |
| `patent_discovery/reports/discovery_summary.json` | Analysis summary |

---

## Conclusion

> A system producing 10,000 vague invention ideas has failed.
> A system producing 5 technically coherent, evidence-backed, falsifiable invention hypotheses is vastly more interesting.

This pilot produced **0 invention candidates** and **0 verified discoveries**. It produced **44 unverified candidates** requiring human review, of which **31 are cross-domain transfer hypotheses** without established mechanistic bridges.

This is an honest result. The infrastructure works. The data is insufficient. The next step is real patent data, not more infrastructure.
