# Discovery Evidence Fabric — Milestone Report

**Date:** 2026-08-11
**Workstream:** Discovery Evidence Fabric V1 (parallel to frozen TEE benchmark)
**Isolation:** Strictly separated from `discovery_experiment/` (TEE) and `independent_corpus/`

---

## Executive Summary

The Discovery Evidence Fabric is operational. Real scientific evidence has been retrieved from 4 live APIs, normalized to a unified schema, built into a knowledge graph, and analyzed by 4 discovery operators. 58 cross-domain candidates were generated, each with prior-art firewall and adversarial review.

**No candidate is labeled INVENTION_CANDIDATE** — per protocol, that state requires evidence and novelty checks that have not yet been completed.

---

## Milestone 1: Real Evidence Retrieval

| Metric | Value |
|---|---|
| Real EvidenceItems retrieved | **7,032** |
| Sources | 4 (Crossref, arXiv, Europe PMC, PubMed) |
| Domains covered | 8 (materials, energy, biotechnology, computing, mechanical, chemical, environmental, neuroscience) |
| With abstracts | ~1,500+ |
| With authors | ~5,000+ |
| With publication dates | ~6,000+ |
| Provenance preserved | ✅ Every item (source, source_id, retrieval_timestamp, content_hash, source_uri) |
| Content hash | SHA-256 per item + canonical record hash |
| Epistemic state | OBSERVED (all items are real publications) |
| Proprietary bulk corpus cloned? | **No** — external-evidence architecture |

### By Source
| Source | Count |
|---|---|
| Crossref | 1,900 |
| Europe PMC | 1,850 |
| PubMed | 1,832 |
| arXiv | 1,450 |

### By Domain
| Domain | Count |
|---|---|
| materials | 1,000 |
| energy | 1,000 |
| chemical | 1,000 |
| environmental | 1,000 |
| mechanical | 982 |
| biotechnology | 800 |
| computing | 750 |
| neuroscience | 500 |

---

## Milestone 2: Knowledge Graph

| Entity | Count |
|---|---|
| Papers | 7,032 |
| Domains | 8 |
| Sources | 4 |
| Authors | 16,417 |
| Organizations | 1,179 |
| Mechanisms | 18 |
| Materials | 23 |
| Processes | 15 |
| **Total edges** | **47,066** |

### Edges by Type
| Edge Type | Count |
|---|---|
| AUTHORED_BY | 23,975 |
| CITES | 7,412 |
| USES_MECHANISM | 6,764 |
| PUBLISHED_BY | 5,430 |
| USES_MATERIAL | 3,032 |
| USES_PROCESS | 453 |

### Mechanism Types Extracted (18)
electrochemical_process, photovoltaic_conversion, catalytic_process, thermal_process, mechanical_process, electromagnetic_process, chemical_synthesis, additive_manufacturing, neural_computation, genetic_engineering, surface_modification, nanostructure_engineering, polymer_engineering, semiconductor_process, biological_process, fluid_dynamics, optical_process, acoustic_process

---

## Milestone 3: Discovery Candidates

| Discovery Mode | Candidates |
|---|---|
| Mode 1: Cross-Domain Transfer | 6 |
| Mode 3: Functional Analogy | 21 |
| Mode 10: Patent Whitespace | 20 |
| Mode 14: Temporal Gap | 11 |
| **Total** | **58** |

### Prior-Art Firewall Results
| Status | Count |
|---|---|
| ADJACENT_PRIOR_ART | 17 |
| UNVERIFIED_ABSENCE | 20 |
| SKIPPED (no mechanism) | 21 |

### Epistemic States
| State | Count |
|---|---|
| CANDIDATE_CONNECTION | 26 |
| ANALOGY | 21 |
| INFERRED | 11 |
| INVENTION_CANDIDATE | **0** (correct — prohibited at this stage) |

---

## Anti-Hallucination Firewall

Every candidate with an absence claim carries:
- `absence_label`: "ABSENCE_OF_EVIDENCE" (never "NOVEL")
- `absence_note`: explains that absence may be due to search coverage
- `search_universe`: documents what was searched
- `limitations`: documents extraction limitations

**No candidate claims "Nobody has done this."** All absence claims are labeled `ABSENCE_OF_EVIDENCE` with documented search universe and limitations.

---

## Adversarial Review

Every candidate has an adversarial review checklist:
- `is_mechanism_transferable`: UNASSESSED
- `is_analogy_superficial`: "LIKELY — keyword-based extraction does not establish mechanistic bridge"
- `is_effect_already_known`: UNASSESSED
- `hidden_prior_art`: "UNASSESSED — requires full-text patent search"
- `physical_constraint_prevents_transfer`: UNASSESSED
- `is_effect_correlation_not_causation`: UNASSESSED
- `alternative_explanation`: UNASSESSED
- `can_be_falsified`: "PENDING — requires falsifiable prediction first"
- `killing_experiment`: PENDING

---

## What Works

- ✅ External-evidence architecture (no proprietary corpus cloned)
- ✅ 4 live source connectors operational (Crossref, arXiv, Europe PMC, PubMed)
- ✅ Normalized EvidenceItem schema with full provenance
- ✅ Knowledge graph with 47,066 edges
- ✅ 4 discovery modes implemented
- ✅ Prior-art firewall functional
- ✅ Adversarial review checklist on every candidate
- ✅ Anti-hallucination firewall (absence labeled ABSENCE_OF_EVIDENCE, never NOVEL)
- ✅ Epistemic states preserved (no silent promotion)
- ✅ Zero INVENTION_CANDIDATE labels (correct for this stage)
- ✅ Isolation from TEE benchmark maintained

## What Doesn't Work Yet

- ❌ Patent connectors (all require credentials — documented in PATENT_ACCESS_REQUIREMENTS.md)
- ❌ OpenAlex and Semantic Scholar (rate-limited/budget exhausted)
- ❌ LLM-based mechanism extraction (structured INPUT→PROCESS→OUTPUT not yet implemented)
- ❌ 11 of 15 discovery modes not yet implemented
- ❌ Full adversarial review (checklist present but assessments are UNASSESSED)
- ❌ Falsifiable predictions (all candidates have PENDING predictions)

---

## Next Steps

1. **More evidence**: Continue retrieval to reach 10,000+ objects (OpenAlex budget resets midnight UTC)
2. **Patent connectors**: Add when credentials available (EPO OPS is highest priority)
3. **Structured mechanism extraction**: Implement INPUT → PROCESS → INTERMEDIATE STATE → OUTPUT → CONSTRAINT → MEASURED EFFECT
4. **More discovery modes**: Implement modes 2, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15
5. **LLM-assisted hypothesis generation**: Use frontier LLM for mechanism reasoning and cross-domain bridge analysis
6. **Full adversarial review**: Assess each candidate against the checklist
7. **Manual inspection**: Review strongest 20 candidates for technical coherence

---

## Isolation Confirmation

- TEE frozen experiment: **UNTOUCHED**
- Independent scientific corpus: **UNTOUCHED**
- Frozen 728-query manifest: **UNTOUCHED** (hash `235741c8...` verified)
- 182-pair pairability packet: **UNTOUCHED**
- Discovery Fabric: **separate directory, separate evidence, separate graph**

The discovery engine interrogates the external world. The TEE benchmark remains the frozen yardstick. They do not contaminate each other.
