# PRELIMINARY MEASUREMENT VERDICT

## Verdict: NOT TRUSTWORTHY

## Canonical status (cycle 259)

This file remains the CANONICAL measurement verdict. The FINAL verdict
has not been earned — see FINAL_VERDICT_BLOCKED.md for the gate-by-gate
breakdown. Cycle 259 added Stage M3 (Bootstrap Statistics): every
metric now has a 95% CI. Cycle 257 tightened the gate vocabulary:
0/4 gates have reached SCIENCE_PASS. Gate 1 is IN PROGRESS (M3 PASS,
M1 63%). Gate A=INSTRUMENTATION_SCAFFOLD_PASS,
Gate B=SENSITIVITY_ANALYSIS_PASS, Gate C=WEAK_STATISTICAL_PASS,
Gate D=AI_SURROGATE_REVIEW_FAIL.

## Evidence (with bootstrap 95% CIs, cycle 259)

Per ROADMAP_V2.md Stage M3: no naked numbers. Every metric now reports
point estimate ± bootstrap std with 95% CI, N, B. Full results in
reports/bootstrap_statistics.json.

| Metric | Point ± Std | 95% CI | N | B |
|---|---|---|---|---|
| Exact F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 |
| Token F1 (all entities) | 0.2533 ± 0.0134 | [0.2102, 0.2614] | 20 | 500 |
| Fuzzy F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 |
| Synonym F1 (all entities) | 0.3053 ± 0.0106 | [0.2564, 0.2963] | 20 | 500 |
| Discovery F1 (shared, syn, DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 | 500 |
| Recognition F1 (all, syn, DR-91) | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 20 | 500 |
| Proposal-locus inflation | 0.1429 ± 0.0635 | [0.0526, 0.2903] | 20 | 500 |
| FP floor (synonym) | 0.9189 ± 0.0559 | [0.7879, 1.0000] | 20 | 200 |
| UNSAFE synonyms count | 18.0000 ± 1.4297 | [15.0000, 20.0000] | 20 | 500 |
| Per-proposal F1 (honest, lenient) | 0.1000 ± 0.0683 | [0.0000, 0.2500] | 20 | 500 |
| Aggregate F1 (DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 | 500 |
| Aggregate F1 (honest) | 0.8333 ± 0.0692 | [0.6471, 0.9231] | 20 | 500 |
| BM25 recall@1 (lenient) | 0.6500 ± 0.1044 | [0.4500, 0.8500] | 20 | 200 |
| Random baseline F1 (lenient) | 0.1000 ± 0.0739 | [0.0000, 0.2500] | 20 | 200 |
| Frequency baseline F1 (lenient) | 0.3000 ± 0.0989 | [0.1500, 0.5000] | 20 | 200 |
| AI surrogate accept rate | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 6 | 500 |
| AI surrogate overall mean score | 2.2381 ± 0.3090 | [1.6780, 2.8458] | 7 | 500 |

Note: cycle 259 bootstrap re-derived the values from scratch using the
honest F1 formula (2*p*r/(p+r)) for F1 metrics. Some values differ from
the cycle 257 PRELIMINARY because cycle 257 used the DR-91 convention
(2*recall/(1+recall)) for some metrics. Both are reported here for
transparency. The honest formula is canonical (P0 rule, F-145).

## Old evidence (cycle 257, for historical reference)

| Metric | Value (DR-91 convention) |
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

