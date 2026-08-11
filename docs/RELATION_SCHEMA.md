# RELATION_SCHEMA.md

## Relation extraction schema (DR-41)

### ExtractedRelation

```python
@dataclass
class ExtractedRelation:
    subject: ExtractedEntity    # the source entity
    relation: str               # the verb (canonicalized)
    obj: ExtractedEntity        # the target entity
    confidence: float           # extraction confidence (0-1)
    source_sentence: str        # the sentence containing the relation
    dependency_path: List[str]  # dependency parse path
```

### Relation extraction pipeline

1. **Dependency parsing** (spaCy): extract subject-verb-object triples
2. **Implicit causal patterns**: regex patterns for causal language
   (e.g., "X causes Y", "X enables Y", "X determines Y")
3. **Negation handling**: skip relations with "without affecting"
4. **Deduplication**: same (subject, verb, object) → count once
5. **Role assignment**: subject = cause, object = effect (or reverse
   for passive voice)

### Forbidden

- Token adjacency extraction (DR-41)
- Phrase matching without dependency parsing
- Regex-first discovery (patterns supplement, not replace, dep parsing)

### Verb canonicalization

Verbs are stemmed to canonical form:
- `causes` → `cause`
- `reduces` → `reduce`
- `enables` → `enable`
- `determines` → `determine`

### PASS criteria

- Relation F1 ≥ target (Gen 3: F1 ≥ 0.85)
- Precision ≥ target
- Recall ≥ target
- Duplicate rate below threshold
