# CEMETERY — Phase 9E

**Status:** constitutional document (the system preserves its mistakes).
**Location:** repo root.
**Phase:** 9E.

> The system should preserve its mistakes.
> — CEO directive, Phase 9E

## Schema

```typescript
interface FailureCase {
    caseId: string;
    hypothesis: string;
    failureMode: string;
    lesson: string;
    consequence: string;
}
```

---

## FAIL-001: Co-occurrence as primitive

**Hypothesis:** Shared component labels between patents predict
invention (convergence score → invention).

**Failure mode:** The convergence score saturated at
d(shared)/d(total) = 0.00 for two consecutive cycles. More ingestion
did not produce more shared components — it diluted the overlap
ratio. The primitive (co-occurrence) measured vocabulary similarity,
not enablement.

**Lesson:** Co-occurrence ≠ enablement. Two patents can share
"electrode" and have nothing causally to do with each other. Two
patents can share zero vocabulary and be one unlock apart.

**Consequence:** Architectural pivot from CO_OCCURRENCE_MODEL to
CAPABILITY_MODEL (Phase 6). The CO_OCCURRENCE_MODEL is preserved
as baseline (v4.2, 669 nodes) for backtesting.

---

## FAIL-002: Normalization as the bottleneck

**Hypothesis:** The convergence score's saturation was caused by a
normalization gap (H1/H2/H3 from Phase 5.F). Fixing normalization
would move the plateau.

**Failure mode:** The external review revealed that normalization
would only move the plateau slightly higher before it reappeared.
The saturation was structural (wrong primitive), not data-driven
(wrong normalization). H0 (no intervention) was the correct answer
at the normalization level.

**Lesson:** When the primitive is wrong, optimizing the primitive's
implementation is wasted effort. The bottleneck was not "insufficient
normalization" — it was "insufficient model."

**Consequence:** H0 (no intervention) won at the normalization level.
The question shifted from "which normalization approach?" to "should
we be optimizing convergence at all?" The architectural pivot followed.

---

## FAIL-003: ENABLES as an edge type

**Hypothesis:** ENABLES edges capture causal enablement between
capabilities (e.g., "sintering ENABLES ion transport").

**Failure mode:** The edge audit (Phase 7 audit) revealed that all 4
ENABLES edges were too broad or misclassified. ENABLES requires
historical counterfactual evidence ("B would NOT have appeared
without A") — evidence that is not available from patent text alone.

**Lesson:** ENABLES is a strong causal claim. It requires more
evidence than classification or structural inference. Suspended
per CEO Decision 2 (Phase 7C.1).

**Consequence:** ENABLES suspended. Only 4 edge types authorized
(EMBODIED_IN, REQUIRES, CONSTRAINS, REGULATED_BY).

---

## FAIL-004: SUBSTITUTES_FOR as an edge type

**Hypothesis:** SUBSTITUTES_FOR edges capture substitutability
between capabilities (e.g., "conversion reaction SUBSTITUTES_FOR
intercalation").

**Failure mode:** Substitutability is "notoriously difficult to
establish." Conversion reactions and intercalation are fundamentally
different mechanisms — you choose one or the other, they are
alternatives, not substitutes in the same design.

**Lesson:** Substitutability requires a specific context, evidence
that A serves B's function, and evidence that the substitution
doesn't introduce unacceptable degradation.

**Consequence:** SUBSTITUTES_FOR suspended. The edge was removed
from the trusted graph v2.0.

---

## FAIL-005: 10 capabilities sufficient for electrochemical storage

**Hypothesis:** The 10 capabilities in the reduced catalog cover
the electrochemical energy storage vertical.

**Failure mode:** Stress test A-002 (Phase 9A) revealed that 5
real-world innovations (solid-state, sodium-ion, recycling,
grid-scale, conversion-type) cannot be expressed with the 10
capabilities. The scope reduction was too aggressive.

**Lesson:** The model's scope is narrower than claimed. It covers
"Li-ion intercalation batteries," not "electrochemical energy
storage." The vertical name overstates the capability catalog's
coverage.

**Consequence:** The vertical should be narrowed to "Li-ion
intercalation batteries" OR the catalog should be expanded
(requiring CEO authorization per ONTOLOGY_FREEZE.md).

---

## FAIL-006: REQUIRES INTERCALATION as a universal invariant

**Hypothesis:** ELECTROCHEMICAL_ENERGY_STORAGE REQUIRES INTERCALATION
holds across 1990-2026.

**Failure mode:** Stress test A-003 (Phase 9A) revealed that at
T=1990, the dominant chemistry was lead-acid (no intercalation).
The edge is specific to Li-ion (post-1991), not universal.

**Lesson:** Structural invariants must be checked for temporal
stability. An edge that is true today may have been false in the
past. TemporalState is not optional — it is required for every
structural edge.

**Consequence:** EDGE-026 is over-generalized. The principle
P-002 (scope: Li-ion only) is correct, but the edge applies the
principle to all electrochemical storage. The edge should be
narrowed or scoped temporally.

---

## FAIL-007: 5 patents as a representative sample

**Hypothesis:** The 5 selected patents represent the electrochemical
energy storage domain.

**Failure mode:** Stress test A-004 (Phase 9A) revealed the sample
is biased toward Li-ion-adjacent technologies. Missing: lead-acid,
NiMH, sodium-ion, Li-S, Li-air, supercapacitors, recycling, grid-scale.

**Lesson:** 5 patents from one sub-domain is not a representative
sample of a broader domain. The backtest results will be valid for
Li-ion-adjacent predictions only.

**Consequence:** Backtest results must be qualified. Predictions
about non-Li-ion technologies cannot be made from this sample.

---

## FAIL-008: 5 constraints as the most important

**Hypothesis:** The 5 constraints capture the most important
limitations for the vertical.

**Failure mode:** Stress test A-005 (Phase 9A) revealed that the
Samsung Note 7 failure was caused by separator integrity (a
manufacturing constraint) that is NOT in the 5-constraint catalog.
Manufacturing constraints were dropped in the scope reduction.

**Lesson:** Manufacturing constraints are load-bearing for real-world
battery failures. Dropping them makes the model unable to explain
major historical failures.

**Consequence:** Manufacturing constraints should be reinstated or
the model's scope should exclude manufacturing-dependent predictions.

---

## Summary

| Case | Hypothesis | Lesson |
|---|---|---|
| FAIL-001 | Co-occurrence predicts invention | Co-occurrence ≠ enablement |
| FAIL-002 | Normalization fixes saturation | Wrong primitive, not wrong normalization |
| FAIL-003 | ENABLES captures causality | ENABLES requires counterfactual evidence |
| FAIL-004 | SUBSTITUTES_FOR captures substitutability | Substitutability is notoriously hard |
| FAIL-005 | 10 capabilities sufficient | Scope is narrower than claimed |
| FAIL-006 | REQUIRES INTERCALATION universal | Invariant not stable across time |
| FAIL-007 | 5 patents representative | Sample is Li-ion-biased |
| FAIL-008 | 5 constraints most important | Manufacturing constraints missing |

These failures are not defeats. They are discoveries. Each one
narrows the model's scope honestly and tells the next cycle what
to fix. A model that has never failed has never been tested.
