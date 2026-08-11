# Stage M7: Failure Envelope (Program A)

Cycle: 265

Per ROADMAP_V2.md Stage M7: instead of 'When does it work?'
answer 'When does it fail?' Every evaluator must have a
Failure Envelope document.

Per AP-1: run it, don't reason about it. Per AP-5: every
failure envelope must be a file on disk.

## What was done

Generated 38 failure envelope documents in
`reports/failure_envelopes/`, one per metric with M3 bootstrap data.
Each envelope synthesizes data from:
- M3 (bootstrap): baseline, CI, degenerate flag
- M4 (repeatability): CV, verdict, deterministic flag
- M6 (sensitivity): FRAGILE perturbations
- M1 (specification): curated known failure modes, boundary conditions
- DR-91 audit: FP floor, formula inflation findings

## Summary statistics

- Total metrics with failure envelopes: 38
- Degenerate (M3): 9
- Has FRAGILE perturbations (M6): 2
- M4 repeatability tested: 8
- M4 UNSTABLE: 1
- All have known failure modes: YES
- All have boundary conditions: YES
- All have repair recommendations: YES

## Per-metric failure envelope index

| Metric | Name | Baseline | Degenerate | M4 Verdict | FRAGILE count |
|---|---|---|---|---|---|
| M-001 | Exact F1 (all entities) | 0.0000 | True | NOT_TESTED | 0 |
| M-002 | Token F1 (all entities) | 0.2533 | False | NOT_TESTED | 0 |
| M-003 | Fuzzy F1 (all entities) | 0.0000 | True | NOT_TESTED | 0 |
| M-004 | Synonym F1 (all entities) | 0.2533 | False | NOT_TESTED | 0 |
| M-005 | Discovery F1 (shared, syn, DR-91) | 0.7879 | False | DETERMINISTIC | 1 |
| M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 | False | NOT_TESTED | 0 |
| M-007 | Proposal-locus inflation | 0.1865 | False | NOT_TESTED | 0 |
| M-008 | FP floor (synonym) | 0.9189 | False | STABLE | 0 |
| M-009 | UNSAFE synonyms count | 0.0000 | True | NOT_TESTED | 0 |
| M-010 | Per-proposal F1 (honest, lenient, ALL sh | 0.6500 | False | NOT_TESTED | 0 |
| M-011 | Per-proposal F1 (strict, honest) | 0.0000 | True | NOT_TESTED | 0 |
| M-012 | Aggregate F1 (DR-91) | 0.7879 | False | NOT_TESTED | 0 |
| M-013 | Aggregate F1 (honest) | 0.7647 | False | DETERMINISTIC | 1 |
| M-014 | BM25 recall@1 (lenient) | 0.3000 | False | NOT_TESTED | 0 |
| M-015 | Random baseline F1 (lenient) | 0.0500 | False | NOT_TESTED | 0 |
| M-016 | Frequency baseline F1 (lenient) | 0.1000 | False | NOT_TESTED | 0 |
| M-101 | Gen 1 Document Parsing F1 | 1.0000 | True | NOT_TESTED | 0 |
| M-102 | Gen 2 Entity Extraction F1 | 0.9431 | False | NOT_TESTED | 0 |
| M-103 | Gen 3 Relation Extraction F1 | 0.8800 | False | NOT_TESTED | 0 |
| M-104 | Gen 4 Mechanism Extraction F1 | 0.9091 | False | NOT_TESTED | 0 |
| M-105 | Gen 5 Discovery Layer F1 | 0.9375 | False | NOT_TESTED | 0 |
| M-201 | L5a held-out beats (count / 10) | 0.9000 | False | ACCEPTABLE | 0 |
| M-202 | L5b held-out beats (count / 10) — same d | 0.9000 | False | NOT_TESTED | 0 |
| M-203 | L5b+Synthesis held-out beats (count / 10 | 0.9000 | False | ACCEPTABLE | 0 |
| M-204 | Multi-seed mean held-out beats (N=5 seed | 8.6000 | False | NOT_TESTED | 0 |
| M-205 | Composite selection rate | 1.0000 | True | NOT_TESTED | 0 |
| M-301 | AI surrogate accept rate | 0.0000 | True | NOT_TESTED | 0 |
| M-302 | AI surrogate overall mean score | 2.2381 | False | NOT_TESTED | 0 |
| M-303-D1 | AI surrogate D1 mean | 4.0000 | False | NOT_TESTED | 0 |
| M-303-D2 | AI surrogate D2 mean | 1.1667 | False | NOT_TESTED | 0 |
| M-303-D3 | AI surrogate D3 mean | 2.0000 | True | NOT_TESTED | 0 |
| M-303-D4 | AI surrogate D4 mean | 1.8333 | False | NOT_TESTED | 0 |
| M-303-D5 | AI surrogate D5 mean | 3.0000 | True | NOT_TESTED | 0 |
| M-303-D6 | AI surrogate D6 mean | 1.8333 | False | NOT_TESTED | 0 |
| M-303-D7 | AI surrogate D7 mean | 1.8333 | False | NOT_TESTED | 0 |
| M-304 | Inter-rater agreement rate | 0.1667 | False | UNSTABLE | 0 |
| M-305 | Self-validation bias (mean residual) | 2.5000 | False | STABLE | 0 |
| M-306 | Expected Calibration Error (ECE) | 0.9000 | False | STABLE | 0 |

## Gate M7 verdict: **PASS**

All metrics have complete failure envelope documents with
known failure modes, boundary conditions, and repair recommendations.

## Key findings across all envelopes

### Most fragile metrics (from M6)

- **M-005** (Discovery F1 (shared, syn, DR-91)): 1 FRAGILE perturbation(s)
- **M-013** (Aggregate F1 (honest)): 1 FRAGILE perturbation(s)

### Degenerate metrics (from M3)

- **M-001** (Exact F1 (all entities)): baseline = 0.0000 (no variance)
- **M-003** (Fuzzy F1 (all entities)): baseline = 0.0000 (no variance)
- **M-009** (UNSAFE synonyms count): baseline = 0.0000 (no variance)
- **M-011** (Per-proposal F1 (strict, honest)): baseline = 0.0000 (no variance)
- **M-101** (Gen 1 Document Parsing F1): baseline = 1.0000 (no variance)
- **M-205** (Composite selection rate): baseline = 1.0000 (no variance)
- **M-301** (AI surrogate accept rate): baseline = 0.0000 (no variance)
- **M-303-D3** (AI surrogate D3 mean): baseline = 2.0000 (no variance)
- **M-303-D5** (AI surrogate D5 mean): baseline = 3.0000 (no variance)

### Metrics with UNSTABLE repeatability (from M4)

- **M-304** (Inter-rater agreement rate): CV = 0.6364

### Top repair priorities

1. **M-008 (FP floor)**: FP floor = 0.92 (CI touches 1.0). The matcher
   cannot discriminate. This is the #1 repair priority for the entire
   measurement system.
2. **M-010 (per-proposal F1)**: FRAGILE to input perturbation (-75%).
   Uses only first shared entity — brittle. Repair: use all shared entities.
3. **M-105 (Gen 5 Discovery F1)**: DR-91 invalidated. FORBIDDEN to report
   as naked F1. Must report alongside M-008 and M-005/M-013.
4. **M-305 (self-validation bias)**: +2.50 bias (100% overestimate).
   Internal evaluator not trustworthy. Replace with calibrated external.
5. **M-201/M-202 (search beats)**: Code drift. Documented baselines stale.
   Update from 2/10 and 5/10 to M4 means (8.3/10, 8.3/10).
