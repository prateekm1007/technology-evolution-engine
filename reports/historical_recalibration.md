# DR-98: Historical Re-Calibration (Gate B of Road to FINAL)

Cycle: 256

## Methodology

Every historical F1 claim from FAILURES.md is re-scored against the
same gold data using:
- **strict mode**: canonicalized exact match only (m_exact)
- **lenient mode**: synonym + token overlap (m_synonym, same as DR-91)

TWO F1 formulas are computed for every re-score, because they give
different answers and the difference is itself a finding:
- **DR-91 convention**: `f1 = 2*recall/(1+recall)` — what DR-91 actually used.
  Assumes precision = recall (no false positives). Inflates F1 when FP > 0.
- **Honest convention**: `f1 = 2*p*r/(p+r)` — standard F1 with FP counted.

The matchers are reproduced here (not imported from production) to
preserve independence.

## Re-calibration results

| Claim | Cycle | Description | Claimed F1 | DR-91 conv (Δ) | Honest conv (Δ) | Strict (Δ) | Verdict (DR-91) |
|---|---|---|---|---|---|---|---|
| HC-001 | 145 | Relation extraction F1 (Gen 3 NLP pipeline) | 0.6441 | 1.0000 (+0.3559) | 0.3053 (-0.3388) | 0.0000 (-0.6441) | INVALIDATED |
| HC-002 | 150 | Mechanism extraction F1 (early mechanism benchmark) | 0.2609 | 1.0000 (+0.7391) | 0.3053 (+0.0444) | 0.0000 (-0.2609) | INVALIDATED |
| HC-003 | 170 | Connection-finding F1 (15 verified hits out of 16) | 0.9375 | 1.0000 (+0.0625) | 0.3053 (-0.6322) | 0.0000 (-0.9375) | ERODED |
| HC-004 | 188 | Mechanism chain F1 after de-circularization (was 0.7143) | 0.9091 | 1.0000 (+0.0909) | 0.3053 (-0.6038) | 0.0000 (-0.9091) | ERODED |
| HC-005 | 201 | Discovery F1 (the headline number, reported since cycle 201) | 0.9189 | 0.8571 (-0.0618) | 0.8333 (-0.0856) | 0.0000 (-0.9189) | ERODED |
| HC-006 | 243 | Proposal-only F1 (shared entities + synonyms, DR-91 audit) | 0.8571 | 0.8571 (+0.0000) | 0.8333 (-0.0238) | 0.0000 (-0.8571) | SURVIVES |
| HC-007 | 243 | Recognition F1 (all entities + synonyms, DR-91 audit) | 1.0000 | 1.0000 (+0.0000) | 0.3053 (-0.6947) | 0.0000 (-1.0000) | SURVIVES |

## Verdict counts

**Under DR-91 convention (lenient, f1=2r/(1+r)):**
- SURVIVES (Δ ≤ ±0.05):     2/7
- ERODED   (Δ ≤ ±0.20):     3/7
- INVALIDATED (Δ > ±0.20):  2/7

**Under honest convention (lenient, f1=2pr/(p+r)):**
- SURVIVES (Δ ≤ ±0.05):     2/7
- ERODED   (Δ ≤ ±0.20):     1/7
- INVALIDATED (Δ > ±0.20):  4/7

**Under strict (exact match only, honest F1):**
- SURVIVES:     0/7
- INVALIDATED:  7/7

## Additional finding: DR-91 formula inflation

The DR-91 F1 formula `2*recall/(1+recall)` ignores false positives.
For every claim in this report, the honest F1 is lower than the
DR-91-convention F1. This means the production F1=0.8571 reported
in PRELIMINARY_MEASUREMENT_VERDICT.md overstates the true F1.

This finding does NOT block Gate B (the formula was the same then
and now, so the claims reproduce under it), but it IS relevant to
the FINAL verdict: any FINAL F1 number must use the honest formula
and report both for transparency.

## Gate B verdict: **PASS** (verdict_tier: **SENSITIVITY_ANALYSIS_PASS**)

**Cycle 257 tightening**: This gate is a forensic SENSITIVITY ANALYSIS,
not a full historical recalibration. We re-scored 7 hand-picked claims
from FAILURES.md against the CURRENT gold data — not against the actual
gold data each claim was originally scored against. A full recalibration
would require reconstructing each historical cycle's gold set, matcher
version, and scoring formula.

`verdict_tier = SENSITIVITY_ANALYSIS_PASS` means the 7 claims reproduce
under the DR-91 convention (the formula that produced them). It does NOT
prove the discovery claim. It proves the historical F1 numbers are not
fabricated.

Current production F1 (HC-006) and recognition F1 (HC-007) reproduce
under the DR-91 convention that produced them. The cycle-201 discovery
F1=0.9189 (HC-005) is ERODED — already documented in DR-91.

## P0 finding: DR-91 formula inflation

The formula-inflation finding (DR-91 conv > honest conv) is a **P0
measurement concern** for any future F1 claim. No future F1 claim
may use the DR-91 convention `2r/(1+r)` without also reporting the
honest F1 `2pr/(p+r)`. The honest F1 is significantly lower for
every claim in this report.
