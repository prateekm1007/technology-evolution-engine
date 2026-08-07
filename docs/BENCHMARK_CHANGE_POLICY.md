# Benchmark Change Policy

## Status: ACTIVE — all benchmark changes require FAILURES.md entry

## Principle

Benchmarks are scientific instruments. Changing them without documentation destroys the ability to compare results across time.

## Rule (Law 7: Historical Permanence)

No benchmark may be silently altered. Any change requires:
1. A FAILURES.md entry documenting the change
2. An independent rerun of the benchmark
3. External justification (why the change is necessary)
4. Documentation of the delta (old score vs new score)

## Forbidden

- Changing gold sets to improve scores
- Weakening benchmarks to silence reds
- Adding synonyms to improve scores
- Changing thresholds without FAILURES.md entry
- Deleting failures
- Renaming benchmarks to avoid comparison
- Changing expected outputs

## Required for Any Change

```
FAILURES.md entry with:
  - What changed
  - Why it changed
  - Old score
  - New score
  - Delta
  - Justification
  - Independent verification
```

## CI Enforcement

Tests must verify:
- Gold set immutability (hash check)
- Synonym map audit (no additions without justification)
- Threshold freeze (FROZEN_THRESHOLDS match observed values)
- No gold leakage (gold phrases not in matcher code)
