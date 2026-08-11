# PROTOCOL_V1 — Patent Discovery Mining

## 1. Scope

This protocol governs the patent discovery mining workstream. It is separate from and does not modify:
- The North Star frozen experiment (Gate A / Gate B)
- The independent scientific corpus
- The frozen 728-query novelty manifest
- The 182-pair pairability packet

## 2. Patent Sources (Authoritative)

### United States
- **USPTO Patent Public Search** — primary search interface
- **USPTO Open Data Portal** — bulk data access
- **PatentsView API** — research-grade patent datasets (primary programmatic source for pilot)

### China
- **CNIPA official patent search/analysis system** — primary
- Multilingual access available
- Programmatic access is limited; pilot uses family-equivalent records from US filings with CN priority

### India
- **IP India / Indian Patent Office public search** — primary
- Programmatic access is limited; pilot uses family-equivalent records from US filings with IN priority

### Third-Party Cross-Validation
Third-party databases may be used for cross-validation only. The originating patent record must remain identifiable.

## 3. Pilot Design

### Sample Size
500 patent families.

### Stratification

| Dimension | Strata |
|---|---|
| Country | US, China (via family), India (via family) |
| Technology domain | materials, energy, mechanical systems, electronics, computing/AI, biotechnology, chemical processes, manufacturing |

### Sampling Method
Deterministic seed-based sampling from PatentsView API. No cherry-picking. No filtering for "interesting" patents.

### Pilot Purpose
**Infrastructure validation only.** The pilot proves the pipeline works end-to-end. It is NOT scientific evidence of discovery capability.

## 4. Pipeline Stages

### Stage 1: Ingestion
- Fetch patent records from authoritative sources
- Record: patent_id, country, filing_date, grant_date, title, abstract, claims, specifications, classifications, inventors, assignees, citations
- Classify each fetch: SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR

### Stage 2: Family Reconstruction
- Group patents into families using priority application numbers
- Deduplicate: one invention appearing in US + CN + IN = ONE family, not three
- Record family lineage: priority → international → national → continuations → divisionals → grants → improvements

### Stage 3: Mechanism Extraction
- Extract from each patent: claimed mechanism, function, material, process, problem solved, performance metrics
- Every extracted fact traces to: patent_id → passage/claim/figure
- LLM-assisted extraction is labeled as INFERRED, not OBSERVED

### Stage 4: Knowledge Graph Construction
Entities: Patent, PatentFamily, Inventor, Assignee, Country, Technology, Mechanism, Material, Process, Problem, PerformanceMetric, Citation, Classification, Claim, Embodiment, FailureMode

Edges: CLAIMS, IMPLEMENTS, CITES, IMPROVES, DEPENDS_ON, USES_MATERIAL, USES_PROCESS, SOLVES, FAILS_ON, DERIVES_FROM, RELATED_TO, TRANSFER_CANDIDATE

### Stage 5: Discovery Mode Analysis
Run all 10 discovery modes (see README.md). Each mode produces candidates with evidence traces.

### Stage 6: Prior-Art Firewall
For every candidate, search:
1. Patent families
2. Cited prior art
3. Backward citations
4. Forward citations (where available)
5. Patent-family equivalents
6. Scientific literature (where available)

Label: REDISCOVERY / ADJACENT_PRIOR_ART / UNVERIFIED_ABSENCE

### Stage 7: Candidate Scoring
Score each candidate on 9 independent dimensions. Do NOT collapse into one score.

### Stage 8: Report Generation
Produce 6 reports (see README.md required outputs).

## 5. Epistemic Rules

### Never Collapse Categories
- OBSERVED ≠ INFERRED ≠ HYPOTHESIS ≠ DISCOVERY CANDIDATE ≠ VERIFIED DISCOVERY
- VERIFIED DISCOVERY is NOT ALLOWED at this stage
- INVENTION CANDIDATE requires a new falsifiable prediction

### Anti-Hallucination
Every substantive statement traces to: patent_id → document → passage/claim/figure → extracted fact. No exceptions.

### Absence of Evidence
A technology not appearing in Indian patents does NOT mean it is novel in India. Every absence is labeled `ABSENCE_OF_EVIDENCE`, never `NOVEL`.

### Similarity ≠ Transferability
"Both use surfaces" is worthless. "Same transport phenomenon under comparable boundary conditions" is potentially interesting. Every cross-domain transfer candidate must contain a mechanistic bridge.

## 6. Scoring Dimensions

| Dimension | Question |
|---|---|
| mechanistic_coherence | Does the proposed mechanism make physical/chemical/biological sense? |
| evidence_strength | How many independent patent records support this? |
| cross_domain_transferability | Is the mechanism mature in one domain and absent in another? |
| unexplained_anomaly | Does this explain a performance gap or contradiction? |
| prior_art_distance | How far is the closest prior art? |
| falsifiability | Can the hypothesis be tested? |
| experimental_tractability | Can the experiment be run at reasonable cost? |
| potential_impact | If true, how significant? |
| uncertainty | How much don't we know? |

Each dimension scored 0-100 independently. No weighted sum. No magic score.

## 7. Output Quality Bar

> A system producing 10,000 vague invention ideas has failed.
> A system producing 5 technically coherent, evidence-backed, falsifiable invention hypotheses is vastly more interesting.

The pilot will report honest counts. If the pipeline produces zero candidates, that is an honest result.

## 8. Prohibitions

- Do NOT claim any discovery is validated
- Do NOT label absence as novelty
- Do NOT collapse epistemic categories
- Do NOT use LLM output as evidence without a patent-text trace
- Do NOT collapse scoring dimensions into one score
- Do NOT optimize for candidate count
- Do NOT touch the North Star frozen experiment
- Do NOT modify the independent scientific corpus
