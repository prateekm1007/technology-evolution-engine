# DR-97: External Baselines (Gate A of Road to FINAL)

Cycle: 256

## Honest comparison protocol

Two matching modes are run for every baseline, because comparing
strict baselines against lenient production is the same kind of
measurement error that DR-91 was created to prevent.

- **Strict mode**: baselines score with canonicalized exact match only.
  Production under strict mode scores F1=0.0000 (per DR-91 audit).
- **Lenient mode**: baselines use production's synonym+token rules.
  Production under lenient mode scores F1=0.8571, but the FP floor
  is 1.0000 (per DR-91 audit). The fair bar is: production must beat
  the *lenient* baselines.

## Strict-mode results (all scorers score 0.0)

| Baseline | F1 |
|---|---|
| BM25 (strict) | 0.0000 |
| Random (strict, mean of 100) | 0.0000 |
| Frequency (strict) | 0.0000 |
| Production (strict, DR-91) | 0.0000 |

## Lenient-mode results (the honest comparison)

| Baseline | F1 | Δ vs production | Verdict |
|---|---|---|---|
| BM25 (lenient) | 0.6500 | +0.2071 | PRODUCTION_BEATS_BASELINE |
| Random (lenient) | 0.0950 | +0.7621 | PRODUCTION_BEATS_BASELINE |
| Frequency (lenient) | 0.3000 | +0.5571 | PRODUCTION_BEATS_BASELINE |
| Production (lenient) | 0.8571 | — | reference |
| FP floor (lenient, DR-91) | 1.0000 | +0.1429 | ceiling |

## Gate A verdict: **PASS** (verdict_tier: **INSTRUMENTATION_SCAFFOLD_PASS**)

**Cycle 257 tightening**: This gate is a LEXICAL/ORACLE-ASSISTED BASELINE
SANITY CHECK, not a full external-baseline validation. The BM25 baseline
uses the gold bridge text as the query (oracle), which is not how a true
external baseline would work. A true external baseline proposes bridges
WITHOUT seeing gold labels.

`verdict_tier = INSTRUMENTATION_SCAFFOLD_PASS` means the instrumentation
runs and produces a non-trivial signal (production beats random+lenient
by Δ=+0.7621), but it does NOT prove the discovery claim. To earn
`SCIENCE_PASS`, this gate would need to be repaired with true external
baselines that propose bridges without gold labels.

Production beats all baselines on specific-bridge matching,
by Δ=+0.7621 over random+lenient. Production IS doing more than
random retrieval. But this is lexical/oracle-assisted, not a true
external baseline validation.

**IMPORTANT CAVEAT — this does NOT override DR-91's FP floor finding.**

- DR-91 measured: 'does the matcher accept non-bridge entities from
  the pool as gold?' → YES 100% of the time (FP floor = 1.0)
- DR-97 measures:  'does production beat baselines at picking the
  bridge concept specifically?' → YES, by +0.7621 over random+lenient

These are different failure modes. Production is doing SOMETHING
more than random, but it is ALSO accepting non-bridge entities
at the FP floor. Both findings stand.
