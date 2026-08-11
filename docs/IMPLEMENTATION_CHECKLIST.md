# IMPLEMENTATION_CHECKLIST.md

**Technology Evolution Engine (TEE)**

**Status:** Cycle 189+

**Operating rule:** Everything is implemented through autocommands, commits, tests, and CI.

**Forbidden:** Manual modification, hidden fixes, local-only patches, silent benchmark changes, undocumented score adjustments.

---

# 0. Global release gates (must always pass)

```text
[ ] CI passes
[ ] All tests pass
[ ] No duplicate source of truth exists
[ ] FAILURES.md updated if a failure occurred
[ ] Benchmark score generated from committed code
[ ] No benchmark contains hardcoded scores
[ ] No benchmark depends on itself
[ ] Provenance exists for all claims
[ ] Re-audit remains independent
[ ] Discovery outcomes remain separate from extractor outcomes
```

---

# 1. Repository structure (must remain stable)

```text
technology-evolution-engine/
│
├── CONSTITUTION.md
├── MASTER_PROTOCOL.md
├── EPISTEMIC_ENGINE.md
├── ANTI_ENTROPY.md
├── FAILURES.md
├── AUDITOR_SCORECARD_12.md
│
├── docs/
│   ├── EXTRACTION_ARCHITECTURE.md
│   ├── ENTITY_SCHEMA.md
│   ├── RELATION_SCHEMA.md
│   ├── MECHANISM_STATUS.md
│   └── REAUDIT_SPEC.md
│
├── scripts/
│   ├── ingest_documents.py
│   ├── extract_entities.py
│   ├── extract_relations.py
│   ├── classify_mechanisms.py
│   ├── provenance.py
│   ├── reaudit_loop.py
│   ├── nine_tenths_loop_v2.py          # SINGLE scorer
│   ├── generate_12_category_scorecard.py # SINGLE 12-cat generator
│   └── ...
│
├── benchmarks/
│   ├── extractor_benchmarks.py
│   └── ...
│
├── tests/
│   └── ...
│
└── data/
```

---

# 2. Governance layer

## Files

```text
CONSTITUTION.md
MASTER_PROTOCOL.md
EPISTEMIC_ENGINE.md
ANTI_ENTROPY.md
FAILURES.md
```

---

### DO

```text
✓ append new failures
✓ append lessons learned
✓ add new invariants
✓ strengthen existing rules
```

---

### DO NOT

```text
✗ rewrite history
✗ remove failures
✗ change scores retroactively
✗ modify constitutional rules casually
```

---

### PASS

```text
[ ] historical consistency maintained
[ ] append-only behavior preserved
[ ] CI passes
```

---

# 3. DR-39: Document Ingestion

## File

```text
scripts/ingest_documents.py
```

---

### Required outputs

```python
CanonicalDocument
Paragraph
Citation
Table
Figure
Equation
```

---

### Required capabilities

```text
[ ] section extraction
[ ] paragraph extraction
[ ] citation extraction
[ ] table extraction
[ ] figure extraction
[ ] equation extraction
[ ] provenance hash
[ ] retrieval timestamp
```

---

### Failure conditions

```text
✗ missing source span
✗ missing timestamps
✗ broken document hierarchy
```

---

### PASS

```text
[ ] 100% parser tests pass
[ ] provenance exists
[ ] PDF replay succeeds
```

---

# 4. DR-40: Entity Extraction

## File

```text
scripts/extract_entities.py
```

---

### Required capabilities

```text
[ ] zero-shot extraction
[ ] canonicalization
[ ] stopword filtering
[ ] POS filtering
[ ] entity normalization
```

---

### Forbidden

```text
✗ hardcoded discovery vocabularies
✗ regex-first extraction
```

---

### PASS

```text
[ ] precision target reached (Gen 2: P ≥ 0.92)
[ ] recall target reached (Gen 2: R ≥ 0.90)
[ ] blind-domain test succeeds
```

---

# 5. DR-41: Relation Extraction

## File

```text
scripts/extract_relations.py
```

---

### Required capabilities

```text
[ ] dependency parsing
[ ] negation handling
[ ] duplicate removal
[ ] role assignment
[ ] relation scoring
[ ] provenance generation
```

---

### Forbidden

```text
✗ token adjacency extraction
✗ phrase matching
✗ regex-first discovery
```

---

### PASS

```text
[ ] relation F1 ≥ target (Gen 3: F1 ≥ 0.85)
[ ] precision ≥ target
[ ] recall ≥ target
[ ] duplicate rate below threshold
```

---

# 6. DR-42: Mechanism Classification

## File

```text
scripts/classify_mechanisms.py
```

---

### Required status classes

```text
associative
asserted
plausibility-checked
verified
contradicted
```

---

### Rules

```text
[ ] weakest-link rule enforced
[ ] contradicted chains never promoted
[ ] verified edges require provenance
```

---

### PASS

```text
[ ] chain scoring passes
[ ] contradiction propagation passes
```

---

# 7. DR-43: Provenance

## File

```text
scripts/provenance.py
```

---

### Required fields

```python
source_id
section
char_start
char_end
retrieval_timestamp
verification_timestamp
provenance_hash
publication_date
prediction_lock_time
```

---

### Required invariants

```python
publication_date < prediction_lock_time

retrieval_timestamp <= verification_timestamp
```

---

### Failure cases

```text
✗ char_start = 0 interpreted as missing
✗ missing source identifier
✗ missing timestamp
```

---

### PASS

```text
[ ] provenance tests pass
[ ] temporal invariants pass
[ ] replay succeeds
```

---

# 8. DR-44: Re-audit Loop

## File

```text
scripts/reaudit_loop.py
```

---

### Required outputs

```text
UPHELD
OVERTURNED
UNRESOLVED
```

---

### Requirements

```text
[ ] independent vocabulary
[ ] independent retrieval
[ ] evidence logging
[ ] source comparison
```

---

### Forbidden

```text
✗ self-validation
✗ same-search replay
✗ benchmark contamination
```

---

### PASS

```text
[ ] upheld path passes
[ ] overturned path passes
[ ] unresolved path passes
```

---

# 9. DR-45: Discovery Filtering

---

### Requirements

```text
[ ] generic scientific word filtering
[ ] noise suppression
[ ] false-positive measurement
```

---

### Forbidden

```text
✗ shared generic terminology
✗ bridge inflation
```

---

### PASS

```text
[ ] false-positive rate below threshold
```

---

# 10. DR-46: Benchmark Pipeline

## File

```text
benchmarks/extractor_benchmarks.py
```

---

### Required benchmark groups

```text
[ ] document parsing quality
[ ] entity precision
[ ] entity recall
[ ] relation precision
[ ] relation recall
[ ] mechanism accuracy
[ ] re-audit overturn rate
```

---

### Forbidden

```text
✗ discovery counts
✗ novelty scores
✗ bridge counts
✗ subjective grading
```

---

### PASS

```text
[ ] benchmark reproducibility passes
[ ] benchmark independence passes
```

---

# 11. Duplicate-source-of-truth protection

---

### Forbidden patterns

```text
✗ scorer_v1.py
✗ scorer_v2.py
✗ real_causal.py
✗ real_causal_v2.py
✗ old_engine/
✗ new_engine/
```

---

### Required tests

```text
[ ] single scorer (test_no_duplicate_sources_of_truth.py)
[ ] single scorecard generator
[ ] single causal engine
[ ] single benchmark pipeline
```

---

# 12. Regression suite

Every failure becomes a permanent test.

```text
Failure
      ↓
Diagnosis
      ↓
Fix
      ↓
Regression test
      ↓
Commit
      ↓
FAILURES.md
```

---

# 13. Release checklist

```text
[ ] code complete
[ ] tests complete
[ ] benchmark complete
[ ] scorecard generated
[ ] provenance validated
[ ] re-audit executed
[ ] failures recorded
[ ] CI passes
[ ] commit pushed
```

---

# 14. Absolute rules

```text
NO MANUAL EDITING

NO MANUAL SCORING

NO SELF-GRADING

NO DUPLICATE SOURCES OF TRUTH

NO RETROACTIVE HISTORY EDITING

NO CONSTITUTIONAL CHANGES WITHOUT FAILURE EVIDENCE
```

---

# 15. Enforcement

This checklist is enforced by CI via `tests/test_implementation_checklist.py`.
The test verifies:

1. All DR-39..DR-46 files exist
2. All required docs exist
3. No duplicate sources of truth
4. Single scorer, single scorecard generator
5. FAILURES.md is append-only (no removals)
6. Benchmark scores are generated from committed code
7. No hardcoded scores in benchmarks
