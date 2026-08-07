# PRELIMINARY MEASUREMENT VERDICT

## Verdict: NOT TRUSTWORTHY

## Canonical status (cycle 257)

This file remains the CANONICAL measurement verdict. The FINAL verdict
has not been earned — see FINAL_VERDICT_BLOCKED.md for the gate-by-gate
breakdown. Cycle 257 tightened the gate vocabulary: 0/4 gates have
reached SCIENCE_PASS. Gate A=INSTRUMENTATION_SCAFFOLD_PASS,
Gate B=SENSITIVITY_ANALYSIS_PASS, Gate C=WEAK_STATISTICAL_PASS,
Gate D=AI_SURROGATE_REVIEW_FAIL.

## Evidence

| Metric | Value |
|---|---|
| Exact F1 (all entities) | 0.0000 |
| Token F1 (all entities) | 0.9744 |
| Fuzzy F1 (all entities) | 0.0000 |
| Synonym F1 (all entities) | 1.0000 |
| Discovery F1 (shared, synonyms) | 0.8571 |
| Recognition F1 (all, synonyms) | 1.0000 |
| Proposal-locus inflation | +0.1429 |
| FP floor (synonym match) | 1.0000 |
| UNSAFE synonyms | 1 |

## Issues

- FP floor = 1.0000 (>5% threshold)
- Proposal-locus inflation = +0.1429
- 1 UNSAFE synonyms
- Exact match F1 = 0 (all credit from fuzzy/synonym)

## P0 finding (cycle 257): DR-91 F1 formula inflation

The F1 numbers above use the DR-91 convention `f1 = 2*recall/(1+recall)`,
which assumes precision = recall (i.e. no false positives). This is
non-standard and INFLATES scores whenever the candidate pool contains
entities that don't match any gold bridge.

The HONEST F1 formula `f1 = 2*p*r/(p+r)` (standard) gives significantly
lower numbers for every claim. See reports/historical_recalibration.json
for the side-by-side comparison.

**P0 rule (cycle 257, F-145)**: No future F1 claim may use the DR-91
convention without also reporting the honest F1. The honest F1 is the
canonical number; the DR-91 number is reported only for backward
compatibility with historical claims.

## Per-proposal F1 (cycle 256, DR-99)

The aggregate F1 of 0.8571 above is the system-level score. The
per-proposal F1 (mean across N=40 individual proposals, DR-99) is
0.1500. These measure different things and should not be conflated:

- Aggregate F1 = 0.8571: "of the 20 gold bridges, 17/20 are matched
  by at least one entity in the shared pool" (DR-91 convention,
  inflated by ignoring FP).
- Per-proposal F1 = 0.1500: "of 40 individual proposals, 15% match
  their gold bridge" (honest, with FP counted).

The per-proposal F1 is below the useful-performance threshold of 0.30
established in cycle 257. The matcher produces non-zero signal, but
the signal is weak — most proposals do not match the gold bridge.

