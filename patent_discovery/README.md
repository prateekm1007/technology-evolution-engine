# Patent Discovery Mining — V1

A parallel invention-discovery laboratory beneath the eventual ChatGPT/Claude-style interface.

## Objective

Mine patent literature from the United States, China, and India to identify **candidate technological discoveries and invention opportunities** that are not obvious from looking at individual patents.

The target is NOT "find interesting patents." The target is:

> Find technical opportunities hiding in the structure of the patent landscape — unresolved problems, abandoned approaches, contradictory claims, capability gaps, mechanism transfers, unexplained performance differences, and combinations of technologies that appear technically plausible but are not yet adequately realized.

## Isolation Boundary

This workstream is **strictly isolated** from:
- `discovery_experiment/` (North Star frozen experiment)
- `independent_corpus/` (independent scientific corpus)
- `novelty_audit/` (frozen 3-database novelty search)

No artifacts from this workstream may be mixed into those directories. No artifacts from those directories may be imported here except read-only references to the protocol design.

## Pipeline

```
PATENT CORPUS
      ↓
FAMILY RECONSTRUCTION
      ↓
MECHANISM EXTRACTION
      ↓
TECHNOLOGY GRAPH
      ↓
GAPS / CONTRADICTIONS / ANOMALIES
      ↓
CROSS-DOMAIN TRANSFER
      ↓
HYPOTHESIS
      ↓
PRIOR-ART FIREWALL
      ↓
FALSIFIABLE PREDICTION
      ↓
EXPERIMENT
      ↓
INDEPENDENT VALIDATION
```

## Discovery Modes

1. Technology Trajectory Gaps
2. Claim → Failure Gaps
3. Cross-Domain Transfer (most important)
4. Contradiction Mining
5. Performance Anomalies
6. Abandoned / Neglected Paths
7. Citation-Time Discontinuities
8. Claimed But Under-Explained Mechanisms
9. Patent Family Evolution
10. Three-Country Asymmetry

## Epistemic Categories (NEVER COLLAPSE)

| Category | Definition |
|---|---|
| OBSERVED | Directly stated or measurable from the patent |
| INFERRED | Reasonable interpretation from multiple patent records |
| HYPOTHESIS | A proposed explanation |
| DISCOVERY CANDIDATE | A hypothesis that survives internal consistency + prior-art screening |
| VERIFIED DISCOVERY | **NOT ALLOWED at this stage** — requires independent external evidence |
| INVENTION CANDIDATE | A technically plausible mechanism that produces a new falsifiable prediction |

## Anti-Hallucination Rule

Every substantive statement must trace to:

```
patent_id → document → passage/claim/figure → extracted fact
```

No LLM-generated statement can become evidence merely because it sounds plausible.

## Prior-Art Firewall

Every candidate is automatically searched against:
1. Patent families
2. Cited prior art
3. Backward citations
4. Forward citations (where available)
5. Patent-family equivalents
6. Scientific literature (where available)

Outcomes:
- `REDISCOVERY` — exact proposed mechanism already exists
- `ADJACENT_PRIOR_ART` — closely related mechanism exists
- `UNVERIFIED_ABSENCE` — no relevant evidence found

**Never automatically label `NEW INVENTION`.**

## Scoring (Multi-Dimensional, No Magic Score)

- mechanistic_coherence
- evidence_strength
- cross_domain_transferability
- unexplained_anomaly
- prior_art_distance
- falsifiability
- experimental_tractability
- potential_impact
- uncertainty

Individual dimensions remain visible. Dimensions are NOT collapsed into one score until evidence supports it.

## Pilot

**500 patent families** across:
- Countries: US, China, India
- Domains: materials, energy, mechanical systems, electronics, computing/AI, biotechnology, chemical processes, manufacturing

The pilot is **infrastructure validation**, not scientific evidence of discovery capability.

## Directory Structure

```
patent_discovery/
├── README.md                    (this file)
├── PROTOCOL_V1.md               (detailed protocol)
├── SOURCES.md                   (patent data sources)
├── graph/                       (patent knowledge graph)
├── ingestion/                   (patent ingestion adapters)
├── families/                    (patent family reconstruction)
├── claims/                      (claim extraction)
├── mechanisms/                  (mechanism extraction)
├── anomalies/                   (performance anomalies)
├── transfer_candidates/         (cross-domain transfer candidates)
├── discovery_candidates/        (discovery candidates)
├── experiments/                 (experiment designs)
├── prior_art/                   (prior-art firewall results)
├── reports/                     (analysis reports)
└── tests/                       (tests)
```

## Status

- **Phase:** Infrastructure + Pilot
- **Started:** 2026-08-11
- **Pilot target:** 500 patent families
- **Pilot purpose:** Validate ingestion, family deduplication, mechanism extraction, graph construction, and discovery mode execution — NOT to claim discoveries
