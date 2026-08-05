# EXTRACTION_ARCHITECTURE.md

DR-38 through DR-46: The layered extractor specification.

Per CEO directive: "do not stop till we reach 9/10 in every benchmark."

## Architecture: documents → structure → entities → relations → mechanisms → constraints → discoveries → audits

### DR-38 — Retire regex as the core extractor
- Regex kept as narrow fallback for local pattern cleanup only
- Regex-first extraction paths marked DEPRECATED
- Replace with: document structure parsing → section extraction → entity recognition → relation extraction
- Exit criterion: blind-discovery over a domain outside regex pattern library produces structured document, entities, and candidate relations

### DR-39 — Build a real document parsing layer
- Canonical document object: sections, paragraphs, tables, figures/captions, citations, equations, provenance
- External systems: GROBID, MinerU, Camelot/Excalibur
- Exit criterion: random scientific PDF → structured document with section boundaries, tables, citations

### DR-40 — Replace fixed entity patterns with zero-shot entity extraction
- Keep: entity canonicalization, scientific stopword filtering
- Delete: hardcoded entity vocabularies as main discovery path
- Replace with: GLiNER/GLiNER2 zero-shot, SciSpacy/BERN2 normalization
- Exit criterion: same-domain blind test yields meaningful canonical entities without manual specification

### DR-41 — Replace flat relation matching with open-domain relation extraction
- Keep: bridge detection over graph, shared-entity detection
- Delete: token adjacency / regex phrase relation extraction
- Replace with: dependency-path extraction (primary), neural/open IE (second pass)
- External systems: Ollie, OpenNRE, GLiREL
- Exit criterion: relation extraction on new domain produces lower noise than current bridge detector

### DR-42 — Add mechanism/status classification
- Every edge tagged: associative | asserted | plausibility-checked | verified | contradicted
- No edge enters graph without status tag and provenance
- Exit criterion: no edge without status + provenance

### DR-43 — Make the extractor provenance-aware
- Per-entity and per-relation provenance: source_id, page/section, char offsets, retrieval timestamp, provenance hash
- publication_date < prediction_lock_time invariant (EPISTEMIC_ENGINE.md §2.2)
- Exit criterion: every claim, entity, relation traceable to source span + timestamped retrieval

### DR-44 — Add adversarial re-audit as mandatory downstream stage
- Trail audit (ledger) + world audit (independent web search)
- Symmetric verdict model (EPISTEMIC_ENGINE.md §3)
- vocabulary_hash checked against original extraction
- Exit criterion: re-audit returns upheld/overturned/unresolved with evidence + vocabulary hash

### DR-45 — Make generic-scientific-word filtering explicit
- Explicit filter layer before bridge scoring
- Measurable false-shared-entity rate
- Exit criterion: cross-domain blind tests no longer produce shared generic science words

### DR-46 — Introduce extraction benchmarks that measure the right thing
- Benchmark buckets: document parsing quality, entity precision/recall, relation precision/recall, mechanism-status accuracy, world-audit overturn rate
- Delete: benchmarks that only count entities or edges
- Exit criterion: extractor has its own benchmark suite, separate from discovery outcomes

## Shortest path to 9/10
1. Retire regex as primary
2. Build document parsing
3. Add zero-shot entity extraction
4. Add open-domain relation extraction
5. Tag mechanism status and provenance
6. Add world-audit
7. Benchmark the extractor separately from discovery

## Files to add
1. docs/EXTRACTION_ARCHITECTURE.md (this file)
2. docs/ENTITY_SCHEMA.md
3. docs/RELATION_SCHEMA.md
4. docs/MECHANISM_STATUS.md
5. docs/REAUDIT_SPEC.md
6. scripts/ingest_documents.py
7. scripts/extract_entities.py
8. scripts/extract_relations.py
9. scripts/classify_mechanisms.py
10. scripts/reaudit_loop.py (exists, extend)
