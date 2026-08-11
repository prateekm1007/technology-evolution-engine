# PRELIMINARY MEASUREMENT VERDICT

## Verdict: NOT TRUSTWORTHY

## Canonical status (cycle 270)

This file is the CANONICAL measurement verdict. The FINAL verdict
has not been earned — see FINAL_VERDICT_BLOCKED.md for the gate-by-gate
breakdown.

**Cycle 270 update (F-158):** BRIDGE_SYNONYMS was removed (circular
validation — 19/20 gold bridges were direct keys). All F1 values below
were regenerated with empty synonym map (m_synonym falls back to
m_token, which is substring + token overlap only). Discovery capability
F1 dropped from 0.9189 to 0.5714. Discovery F1 (shared) dropped from
0.8571 to 0.7879. These are the honest, non-circular values.

**Cycle 269 update (F-157):** M-010 per-proposal F1 was repaired to
use ALL shared entities (was: first shared entity only). Current
value: 0.6500 (was 0.7500 with circular synonyms, 0.10-0.20 with
first-entity-only + circular synonyms).

## Evidence (with bootstrap 95% CIs, cycle 270 — non-circular)

Per ROADMAP_V2.md Stage M3: no naked numbers. Every metric reports
point estimate ± bootstrap std with 95% CI, N, B. Full results in
reports/bootstrap_statistics.json. All values below are from the
cycle-270 bootstrap run with empty BRIDGE_SYNONYMS (non-circular).

| Metric | Point ± Std | 95% CI | N | B |
|---|---|---|---|---|
| Exact F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 |
| Token F1 (all entities) | 0.2533 ± 0.0134 | [0.2102, 0.2614] | 20 | 500 |
| Fuzzy F1 (all entities) | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 |
| Synonym F1 (all entities) | 0.2533 ± 0.0134 | [0.2102, 0.2614] | 20 | 500 |
| Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 |
| Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | [0.9189, 1.0000] | 20 | 500 |
| Proposal-locus inflation | 0.1864 ± 0.0809 | [0.0526, 0.3548] | 20 | 500 |
| FP floor (token, syn empty) | 0.9189 ± 0.0978 | [0.6667, 1.0000] | 20 | 200 |
| UNSAFE synonyms count | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 20 | 500 |
| Per-proposal F1 (ALL shared, honest) | 0.6500 ± 0.1081 | [0.4500, 0.8500] | 20 | 500 |
| Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 |
| Aggregate F1 (honest) | 0.7647 ± 0.0875 | [0.5455, 0.8947] | 20 | 500 |
| BM25 recall@1 (lenient) | 0.6500 ± 0.1044 | [0.4500, 0.8500] | 20 | 200 |
| Random baseline F1 (lenient) | 0.1000 ± 0.0739 | [0.0000, 0.2500] | 20 | 200 |
| Frequency baseline F1 (lenient) | 0.3000 ± 0.0989 | [0.1500, 0.5000] | 20 | 200 |
| AI surrogate accept rate | 0.0000 ± 0.0000 | [0.0000, 0.0000] | 6 | 500 |
| AI surrogate overall mean score | 2.2381 ± 0.3090 | [1.6780, 2.8458] | 7 | 500 |

Note: "Synonym F1" now equals "Token F1" (0.2533) because
BRIDGE_SYNONYMS is empty — m_synonym falls back to m_token. This is
correct and expected.

Note: "UNSAFE synonyms count" is now 0 because BRIDGE_SYNONYMS is
empty — there are no synonyms to audit. This is correct.

Note: "Recognition F1" is now 0.9744 (was 1.0000 with circular
synonyms). It is NO LONGER DEGENERATE — the metric can now
discriminate. This is a genuine improvement from removing circularity.

## Historical evidence (BEFORE cycle 270 — for before/after comparison)

The values below are from the cycle-259 bootstrap run WITH circular
BRIDGE_SYNONYMS. They are preserved here for before/after comparison
only. They are NOT current. Do not cite them as current measurements.

| Metric | Value (circular, pre-cycle-270) | Current (non-circular) |
|---|---|---|
| Synonym F1 (all entities) | 0.3053 | 0.2533 |
| Discovery F1 (shared, syn, DR-91) | 0.8571 | 0.7879 |
| Recognition F1 (all, syn, DR-91) | 1.0000 (DEGENERATE) | 0.9744 (NOT degenerate) |
| FP floor (token, syn empty) | 0.9189 | 0.9189 (unchanged) |
| UNSAFE synonyms count | 18 | 0 |
| Per-proposal F1 (ALL shared) | 0.7500 | 0.6500 |
| Aggregate F1 (DR-91) | 0.8571 | 0.7879 |
| Aggregate F1 (honest) | 0.8333 | 0.7647 |

## Issues (current, non-circular)

- FP floor = 0.9189 (CI touches 1.0) — still above 5% threshold
- Proposal-locus inflation = +0.1864 (recognition scores higher than discovery)
- Exact match F1 = 0 (all credit from token overlap)
- UNSAFE synonyms = 0 (BRIDGE_SYNONYMS is empty — no synonyms to audit)

## P0 finding (cycle 257): DR-91 F1 formula inflation

The F1 numbers use the DR-91 convention `f1 = 2*recall/(1+recall)`,
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

## Discovery capability score (regenerated from source, cycle 270)

- F1 = 0.5714 (was 0.9189 with circular synonyms)
- Score = 6/10 (was 9/10)
- TP=8, FP=0, FN=12
- Precision=1.0, Recall=0.40
- Source: benchmarks/reports/discovery_capability_score.json (regenerated by execution)
- AUDITOR_SCORECARD.md has been regenerated to match

## Per-proposal F1 (cycle 269-270)

The aggregate F1 of 0.7879 above is the system-level score. The
per-proposal F1 (mean across N=20 gold bridges, using ALL shared
entities as candidates) is 0.6500. These measure different things:

- Aggregate F1 = 0.7879: "of the 20 gold bridges, ~15/20 are matched
  by at least one entity in the shared pool" (DR-91 convention,
  inflated by ignoring FP).
- Per-proposal F1 = 0.6500: "of 20 gold bridges, 65% are matched by
  at least one shared entity" (honest, using ALL shared entities).

The per-proposal F1 is above the useful-performance threshold of 0.30
established in cycle 257. The matcher produces meaningful signal.
