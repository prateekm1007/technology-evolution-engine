# REAUDIT_SPEC.md

## Re-audit specification (DR-44)

### Overview

The re-audit loop is the adversarial verification layer. Every discovery
claim must be independently re-audited using a DIFFERENT vocabulary and
DIFFERENT retrieval than the original extraction.

### Required outputs

```text
UPHELD     — the original claim is confirmed by independent re-audit
OVERTURNED — the original claim is refuted by independent re-audit
UNRESOLVED — the re-audit cannot confirm or refute (insufficient evidence)
```

### Requirements

1. **Independent vocabulary**: the re-audit uses a vocabulary_hash that
   must differ from the original extraction's vocabulary.
2. **Independent retrieval**: the re-audit performs its own literature
   search, not a replay of the original.
3. **Evidence logging**: all re-audit evidence is logged to the predictions
   ledger with timestamp, vocabulary_hash, and verdict.
4. **Source comparison**: the re-audit compares the claim's sources against
   the re-audit's independently-retrieved sources.

### Forbidden

- Self-validation (the extractor cannot verify its own claims)
- Same-search replay (the re-audit must use a different search)
- Benchmark contamination (re-audit must not see the original's evidence)

### PASS criteria

- UPHELD path passes: a genuinely novel claim is upheld
- OVERTURNED path passes: a known-published claim is overturned
- UNRESOLVED path passes: an ambiguous claim is marked unresolved

### Vocabulary hash integrity

Every re-audit entry must have a non-empty vocabulary_hash. The hash is
computed from the re-audit's search terms, NOT the original's. An empty
hash (SHA-256 of empty string) indicates a broken re-audit and is flagged
by `test_vocabulary_hash_integrity.py`.
