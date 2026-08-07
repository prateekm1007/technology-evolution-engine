# Synonym Policy

## Status: ACTIVE — all synonyms must justify their existence

## Principle

Every synonym in the benchmark's synonym map must:
1. Be justified by domain logic (not just "it improves the score")
2. Be documented with: origin, when added, why, which benchmark requires it
3. Be audited for score impact (does removing it change the F1?)
4. Be marked SAFE, QUESTIONABLE, or UNSAFE

## Current State (DR-91 Phase III)

- Total synonyms: 20
- SAFE: 19 (no score impact when removed)
- UNSAFE: 1 (exists only to inflate benchmark score)
- QUESTIONABLE: 0

## Rule

**No synonym may be added to improve benchmark performance.** If removing a synonym changes the F1, it must be justified by domain logic, not score optimization. UNSAFE synonyms must be removed or justified.

## Audit Procedure

For every synonym:
1. Remove it from the map
2. Re-run the benchmark
3. If F1 drops: mark QUESTIONABLE
4. If no domain logic justification: mark UNSAFE
5. If F1 unchanged: mark SAFE

## Forbidden

- Adding synonyms to fix discovery misses without domain justification
- Adding synonyms that only appear in gold bridges (circular)
- Adding synonyms to make a specific benchmark pass
