# Matching Specification

## Status: PRELIMINARY — under DR-91 reconstruction

## The Problem

The production benchmark uses `_bridge_matches()` with 3 strategies:
1. Substring match
2. Token overlap (≥1 shared 4+ char token)
3. Synonym map (20 entries)

**All 3 are too permissive.** With 143 entities, the false-positive floor = 1.0 (any bridge matches something). The matching cannot distinguish discoveries from noise.

## Independent Matchers (DR-91 Phase I)

Four independent matchers implemented in `audit/stage_minus1/exact_matcher.py`:

| Mode | Logic | F1 (all entities) | F1 (shared only) |
|------|-------|-------------------|-------------------|
| exact_normalized | Exact string after canonicalization | 0.0000 | 0.0000 |
| exact_token | Substring OR ≥1 shared 4+ char token | 0.9744 | 0.7879 |
| fuzzy | Character bigram Jaccard ≥0.85 | 0.0000 | 0.0000 |
| synonym | Token + synonym map | 1.0000 | 0.8571 |

## Discovery vs Recognition

- **Recognition F1** (all entities + synonyms): 1.0000
- **Discovery F1** (shared entities + synonyms): 0.8571
- **Inflation**: +0.1429

Recognition and Discovery must NEVER be combined into one score.

## Required Changes

1. **Deprecate entity-based matching** for discovery scoring (FP=1.0)
2. **Use proposal-based matching** once Proposal Composer Gen1 is available
3. **Require FP < 5%** for any matcher to be considered trustworthy
4. **Bootstrap CIs** on all F1 scores
5. **No synonym may be added** without SYNONYM_POLICY.md justification
