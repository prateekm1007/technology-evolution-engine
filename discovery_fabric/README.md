# Discovery Evidence Fabric V1

A world-class global scientific + patent discovery engine that continuously interrogates external knowledge infrastructures while preserving provenance, licensing, epistemic state, and reproducibility.

## Core Principle

GitHub repositories are NOT the corpus. They are connectors, parsers, schemas, retrieval clients, query infrastructure. We build an **external-evidence architecture** — the model is the reasoning layer over external memory, not the database itself.

## Architecture

```
                    CHATGPT / CLAUDE INTERFACE
                              │
                              ▼
                    DISCOVERY ORCHESTRATOR
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       SCIENCE SEARCH    PATENT SEARCH     GRAPH SEARCH
             │                │                │
       Crossref/arXiv    USPTO/EPO/       citations /
       Europe PMC/PubMed CN/IN sources    relationships
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    EVIDENCE NORMALIZER
                              │
                              ▼
                     MECHANISM KNOWLEDGE
                           GRAPH
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
          ANALOGY         CONTRADICTION      GAP
          ENGINE            ENGINE          ENGINE
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                     DISCOVERY ENGINE
                              │
                     PRIOR-ART FIREWALL
                              │
                       EVIDENCE REPORT
```

## Working Sources (Tested 2026-08-11)

| Source | Status | Auth | Coverage |
|---|---|---|---|
| Crossref | ✅ Operational | None (polite pool) | 150M+ scientific works |
| arXiv | ✅ Operational | None | 2.4M+ preprints (physics, CS, math, biology) |
| Europe PMC | ✅ Operational | None | 40M+ biomedical publications |
| PubMed E-utilities | ✅ Operational | None | 36M+ biomedical citations |
| OpenAlex | ⏳ Rate-limited (resets midnight UTC) | API key | 250M+ works |
| Semantic Scholar | ⏳ Rate-limited | API key | 200M+ papers |
| USPTO ODP | ❌ Needs API key | API key | US patents |
| EPO OPS | ❌ Needs OAuth | OAuth | 100+ jurisdictions |
| Google Patents | ❌ CAPTCHA blocked | None | 100+ jurisdictions |

**Four sources are operational right now.** That's enough for the first 10,000 evidence objects milestone.

## Epistemic States (NEVER COLLAPSE)

```
OBSERVED → INFERRED → ANALOGY → CANDIDATE_CONNECTION → MECHANISTIC_HYPOTHESIS → EXPERIMENTAL_PROPOSAL → INVENTION_CANDIDATE
```

## Anti-Hallucination Firewall

Never output: "Nobody has done this."
Instead output: "No matching evidence was found within the searched universe." with search universe, queries, databases, time range, timestamp, result count, limitations.

## Isolation

This system is **completely separate** from the frozen TEE benchmark. The discovery engine queries the external world; TEE measures whether it actually discovered anything. They never contaminate each other.

## First Milestone

**10,000 real scientific evidence objects** retrieved through Crossref + arXiv + Europe PMC + PubMed, normalized, hashed, provenance-preserved, and queryable.
