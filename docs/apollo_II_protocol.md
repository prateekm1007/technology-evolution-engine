# Apollo-II Protocol: Corpus Expansion Plan

## Objective

Expand the corpus from 20 documents to 150+ documents across 3+ distinct
domains to exercise the discovery algorithms meaningfully.

## Current State (20 documents)

- 10 USPTO/PCT patents (battery, radiative cooling, graphene, MOF, etc.)
- 10 arXiv papers (thermoelectric, piezoelectric, desalination, etc.)
- All real (fetched live, URLs HTTP 200, no fabricated data)
- All parsed by the edge extractor (mechanism-level, not keyword-level)

## Target State (150+ documents)

### Phase 1: Sodium-Ion Batteries (50 documents)
- 25 USPTO patents (cathode, anode, electrolyte)
- 15 CNIPA patents (hard carbon, biomass, manufacturing)
- 10 arXiv papers (Na storage mechanism, P2/O3 transition)

### Phase 2: Nitrogen Fixation (50 documents)
- 20 USPTO patents (Haber-Bosch, electrochemical NRR, plasma)
- 15 CNIPA patents (catalyst, electrode, electrolyzer)
- 15 arXiv papers (Bi2Te3-NRR, metal tellurides, Mo-based)

### Phase 3: Radiative Cooling (50 documents)
- 20 USPTO patents (metamaterial, paint, photonic structure)
- 15 CNIPA patents (building material, coating)
- 15 arXiv papers (BaSO4, PDMS, daytime sub-ambient)

## Quality Criteria

1. All documents must be real (fetched live via web-search + web-reader)
2. Patent IDs must NOT form arithmetic sequences (PR-20)
3. All URLs must return HTTP 200 (PR-19)
4. Each document must have: title, source URL, retrieval date, abstract
5. The edge extractor must extract ≥3 nodes per document

## Timeline

- Phase 1: 2 days (fetch + parse + verify)
- Phase 2: 2 days
- Phase 3: 2 days
- Total: ~6 days of fetching + parsing

## Why This Matters

The cycle 42-43 acid tests showed that 20 documents produce trivial
combinatorial results (140 "bridges" that are all transitive paths through
shared topics). A 150-document corpus across 3 domains will:
- Exercise Swanson bridge search with genuinely disconnected literatures
- Exercise Gentner structure mapping with 3+ step cross-domain chains
- Exercise Altshuller contradiction search with real increase/decrease pairs
- Enable the Apollo Test to find genuine cross-domain connections
