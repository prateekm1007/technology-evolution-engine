# FINAL VERDICT BLOCKED

## Status: NOT TRUSTWORTHY (FINAL verdict not yet earned)

Gates with SCIENCE_PASS: 0/4

**Cycle 257 tightening**: FINAL verdict requires SCIENCE_PASS on
ALL gates. INSTRUMENTATION_SCAFFOLD_PASS, SENSITIVITY_ANALYSIS_PASS,
WEAK_STATISTICAL_PASS, AI_SURROGATE_REVIEW_FAIL, and BLOCKED all
block eligibility. These verdict tiers mean the gate's
instrumentation runs but does not prove the scientific claim.

## Blocking gates

- **A**: A: verdict_tier=INSTRUMENTATION_SCAFFOLD_PASS — instrumentation/scaffold pass only, NOT SCIENCE_PASS. The gate runs and produces signal but does not prove the scientific claim.
- **B**: B: verdict_tier=SENSITIVITY_ANALYSIS_PASS — instrumentation/scaffold pass only, NOT SCIENCE_PASS. The gate runs and produces signal but does not prove the scientific claim.
- **C**: C: verdict_tier=WEAK_STATISTICAL_PASS — instrumentation/scaffold pass only, NOT SCIENCE_PASS. The gate runs and produces signal but does not prove the scientific claim.
- **D**: D: AI_SURROGATE_REVIEW_FAIL — AI surrogate review did not pass. accept_rate=0.0, overall_mean=2.2381

## Gate summary

| Gate | Name | Verdict | Verdict tier |
|---|---|---|---|
| A | External baselines | PASS | INSTRUMENTATION_SCAFFOLD_PASS |
| B | Historical re-calibration | PASS | SENSITIVITY_ANALYSIS_PASS |
| C | N≥30 proposal evaluation | PASS | WEAK_STATISTICAL_PASS |
| D | Tier-2 / AI surrogate review | FAIL | AI_SURROGATE_REVIEW_FAIL |

## What this means

The PRELIMINARY verdict (NOT TRUSTWORTHY) remains in effect.
The measurement system has NOT earned the FINAL verdict because
zero gates have reached SCIENCE_PASS. The instrumentation runs,
but the scientific claims are not proven.

## What is required to unblock

- **Gate A (External baselines)**: Cycle 257 finding: the
  current BM25 baseline is lexical/oracle-assisted (uses the
  gold bridge as the query). Repair requires implementing
  true external baselines that propose bridges WITHOUT seeing
  gold labels.
- **Gate B (Historical re-calibration)**: Cycle 257 finding:
  this is a sensitivity analysis, not a full recalibration.
  Repair requires reconstructing each historical cycle's
  original gold data, matcher version, and scoring formula.
  Also: P0 finding — DR-91 F1 formula `2r/(1+r)` inflates
  scores; future F1 claims must use honest `2pr/(p+r)`.
- **Gate C (N≥30 proposal evaluation)**: Cycle 257 finding:
  the PASS criterion was too weak. Distinguishability from
  FP=1.0 is necessary but not sufficient. Useful proposal
  performance requires per-proposal honest F1 mean ≥ 0.30;
  observed 0.1500. Repair requires reworking the matcher to
  produce higher per-proposal F1.
- **Gate D (AI surrogate review)**: AI surrogate reviewer
  (AI_SURROGATE_001, Tier-1.5 pre-screen) reviewed 6
  proposals and REJECTED all 6. The proposals are
  'template-level shared-term hypotheses, not mature
  scientific discovery claims.' Per cycle 257 design,
  AI specialist review is accepted (end-to-end AI loop),
  but the proposals did not pass. Repair requires
  reworking the ProposalComposer to produce domain-grounded
  hypotheses with concrete mechanisms, not shared vocabulary.

## What is NOT blocked

The scaffolding for all four gates is complete. The measurement
infrastructure is in place. The remaining work is:
- Repair Gate A with true external baselines (no oracle)
- Repair Gate B with full historical recalibration + honest F1
- Repair Gate C with useful-performance threshold (≥0.30 mean F1)
- Repair Gate D with reworked ProposalComposer (or human review)
- Document formula inflation as P0 concern for any future F1 claim
