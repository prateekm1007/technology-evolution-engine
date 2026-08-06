# ENTITY_SCHEMA.md

## Entity extraction schema (DR-40)

### ExtractedEntity

```python
@dataclass
class ExtractedEntity:
    text: str           # the entity text as it appears in the source
    label: str          # entity type (concept, material, property, etc.)
    start: int          # character offset in source text
    end: int            # character offset end
    confidence: float   # extraction confidence (0-1)
    aliases: List[str]  # alternative forms (abbreviations, etc.)
    properties: Dict    # additional metadata
```

### Entity types

- `concept` — scientific concept (general)
- `material` — a material or substance
- `property` — a measurable property
- `quantity` — a numerical quantity
- `state` — a state of matter or system state
- `process` — a physical/chemical process

### Canonicalization

All entity text is canonicalized for matching:
1. Lowercase
2. Replace spaces/hyphens with underscores
3. Strip leading articles (the, a, an)
4. Remove possessives

### Forbidden

- Hardcoded discovery vocabularies (DR-40)
- Regex-first extraction (use spaCy NER + dependency parsing)
- Pattern-only entities without NER validation

### PASS criteria

- Precision target reached (Gen 2: P ≥ 0.92)
- Recall target reached (Gen 2: R ≥ 0.90)
- Blind-domain test succeeds (entities extracted from unseen domains)
