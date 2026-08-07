# Stage M3: Bootstrap Statistics (Program A)

Cycle: 261 (extended — all 30 specified metrics bootstrapped)

Per ROADMAP_V2.md Stage M3: every F1 number must become
`F1 = 0.91 ± 0.07 (95% CI: 0.78, 1.00; N=20, B=2000)`.

This file reports bootstrap statistics for all specified M-metrics.
Each metric now has a point estimate, standard error, 95% confidence
interval, sample size, and number of bootstrap resamples.

## Method

- **Bootstrap unit**: the GOLD DISCOVERIES sample (N=20)
- **Resampling**: with replacement, B=500 (B=200 for expensive metrics: BM25, random, FP floor)
- **CI method**: percentile method (2.5th, 97.5th percentiles)
- **Seed**: 42 (reproducible)
- **Metric function**: same as defined in MeasurementEngineSpecification.md

## Results

| ID | Metric | Point ± Std | 95% CI | N | B | Degenerate? |
|---|---|---|---|---|---|---|
| M-001 | Exact F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 | YES |
| M-002 | Token F1 (all entities) | 0.2533 ± 0.0134 | [0.2102, 0.2614] | 20 | 500 | no |
| M-003 | Fuzzy F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 | YES |
| M-004 | Synonym F1 (all entities) | 0.3053 ± 0.0106 | [0.2564, 0.2963] | 20 | 500 | no |
| M-005 | Discovery F1 (shared, syn, DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 | 500 | no |
| M-006 | Recognition F1 (all, syn, DR-91) | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 20 | 500 | YES |
| M-007 | Proposal-locus inflation | 0.1429 ± 0.0635 | [0.0526, 0.2903] | 20 | 500 | no |
| M-008 | FP floor (synonym) | 0.9189 ± 0.0580 | [0.8226, 1.0000] | 20 | 200 | no |
| M-009 | UNSAFE synonyms count | 18.0000 ± 1.4297 | [15.0000, 20.0000] | 20 | 500 | no |
| M-010 | Per-proposal F1 (honest, lenient) | 0.0500 ± 0.0506 | [0.0000, 0.1500] | 20 | 500 | no |
| M-011 | Per-proposal F1 (strict, honest) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 | YES |
| M-012 | Aggregate F1 (DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 | 500 | no |
| M-013 | Aggregate F1 (honest) | 0.8333 ± 0.0692 | [0.6471, 0.9231] | 20 | 500 | no |
| M-014 | BM25 recall@1 (lenient) | 0.6500 ± 0.1044 | [0.4500, 0.8500] | 20 | 200 | no |
| M-015 | Random baseline F1 (lenient) | 0.1000 ± 0.0739 | [0.0000, 0.2500] | 20 | 200 | no |
| M-016 | Frequency baseline F1 (lenient) | 0.3000 ± 0.0989 | [0.1500, 0.5000] | 20 | 200 | no |
| M-301 | AI surrogate accept rate | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 6 | 500 | YES |
| M-302 | AI surrogate overall mean score | 2.2381 ± 0.3090 | [1.6780, 2.8458] | 7 | 500 | no |
| M-303-D1 | AI surrogate D1 mean | 4.0000 ± 0.2394 | [3.5000, 4.5000] | 6 | 500 | no |
| M-303-D2 | AI surrogate D2 mean | 1.1667 ± 0.1485 | [1.0000, 1.5000] | 6 | 500 | no |
| M-303-D3 | AI surrogate D3 mean | 2.0000 ± 0.0000 | [2.0000, 2.0000] | 6 | 500 | YES |
| M-303-D4 | AI surrogate D4 mean | 1.8333 ± 0.1517 | [1.5000, 2.0000] | 6 | 500 | no |
| M-303-D5 | AI surrogate D5 mean | 3.0000 ± 0.0000 | [3.0000, 3.0000] | 6 | 500 | YES |
| M-303-D6 | AI surrogate D6 mean | 1.8333 ± 0.1517 | [1.5000, 2.0000] | 6 | 500 | no |
| M-303-D7 | AI surrogate D7 mean | 1.8333 ± 0.1517 | [1.5000, 2.0000] | 6 | 500 | no |
| M-101 | Gen 1 Document Parsing F1 | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 5 | 500 | YES |
| M-102 | Gen 2 Entity Extraction F1 | 0.9431 ± 0.0208 | [0.8983, 0.9764] | 65 | 500 | no |
| M-103 | Gen 3 Relation Extraction F1 | 0.8800 ± 0.0304 | [0.8145, 0.9322] | 85 | 500 | no |
| M-104 | Gen 4 Mechanism Extraction F1 | 0.9091 ± 0.0677 | [0.7368, 1.0000] | 12 | 500 | no |
| M-105 | Gen 5 Discovery Layer F1 | 0.9375 ± 0.0464 | [0.8276, 1.0000] | 17 | 500 | no |
| M-201 | L5a held-out beats (count / 10) | 0.9000 ± 0.0891 | [0.7000, 1.0000] | 10 | 100 | no |
| M-202 | L5b held-out beats (count / 10) — same data as M-201 | 0.9000 ± 0.0891 | [0.7000, 1.0000] | 10 | 100 | no |
| M-203 | L5b+Synthesis held-out beats (count / 10, single seed) | 0.9000 ± 0.0891 | [0.7000, 1.0000] | 10 | 100 | no |
| M-204 | Multi-seed mean held-out beats (N=5 seeds) | 8.6000 ± 0.3529 | [8.0000, 9.4000] | 5 | 500 | no |
| M-205 | Composite selection rate | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 43 | 500 | YES |
| M-304 | Inter-rater agreement rate | 0.1667 ± 0.1485 | [0.0000, 0.5000] | 6 | 500 | no |
| M-305 | Self-validation bias (mean residual) | 2.5000 ± 0.0556 | [2.3750, 2.6250] | 6 | 500 | no |
| M-306 | Expected Calibration Error (ECE) | 0.9000 ± 0.0111 | [0.8750, 0.9250] | 6 | 500 | no |

## Interpretation

- **Point estimate**: the metric value on the full sample (what was
  previously reported as a naked number).
- **Std**: the bootstrap standard error. This is the uncertainty.
- **95% CI**: the confidence interval. If the CI is wide, the metric
  is uncertain. If the CI is narrow, the metric is precise (but not
  necessarily accurate — that's a different question).
- **Degenerate**: if YES, all bootstrap resamples produced the same
  value. This means the metric is insensitive to the sample, which
  is usually a sign of a trivial metric (e.g. always 0 or always 1).

## Key observations

Widest CIs (most uncertain):
- M-009 (UNSAFE synonyms count): width = 5.0000
- M-204 (Multi-seed mean held-out beats (N=5 seeds)): width = 1.4000
- M-302 (AI surrogate overall mean score): width = 1.1679

Degenerate metrics (all bootstrap values identical — likely trivial):
- M-001 (Exact F1 (all entities)): point = 0.0000
- M-003 (Fuzzy F1 (all entities)): point = 0.0000
- M-006 (Recognition F1 (all, syn, DR-91)): point = 1.0000
- M-011 (Per-proposal F1 (strict, honest)): point = 0.0000
- M-301 (AI surrogate accept rate): point = 0.0000
- M-303-D3 (AI surrogate D3 mean): point = 2.0000
- M-303-D5 (AI surrogate D5 mean): point = 3.0000
- M-101 (Gen 1 Document Parsing F1): point = 1.0000
- M-205 (Composite selection rate): point = 1.0000

## What this changes

No metric may now be reported as a naked number. Every claim must
include the ± std and 95% CI. The PRELIMINARY_MEASUREMENT_VERDICT.md
numbers (F1=0.8571, etc.) must be updated to include bootstrap CIs.

This is the foundation for Gate 1 (Measurement) PASS. The next steps
are Stage M2 (provenance — every score carries metadata) and Stage M4
(repeatability — run identical benchmark 100 times, measure variance).
