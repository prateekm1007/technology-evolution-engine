# MODEL_MATURITY — Phase 9 Post-Stress-Test

**Status:** constitutional document (maturity assessment).
**Location:** repo root.
**Phase:** 9 (per CEO Instruction 4).

> My assessment is that the current state is approximately M1,
> approaching M2. That is not criticism. It is progress.
> — CEO directive, Phase 9

---

## Maturity levels

| Level | Name | Meaning | Achieved? |
|---|---|---|---|
| M0 | Hypothesis | The model is a proposed explanation. No structure, no evidence. | ✅ Passed |
| M1 | Structured observations | The model has nodes, edges, evidence, justifications, principles. It is structured but untested. | ✅ **Current** |
| M2 | Reproducible evidence | The model produces deterministic, reproducible predictions. The frozen-time backtest has been run. Results are recorded. | Approaching |
| M3 | Predictive capability | The model's predictions have been tested against real outcomes. It beats the NULL_MODEL and the CO_OCCURRENCE_MODEL. | Not started |
| M4 | Transferability | The model's method transfers to a second domain (photovoltaics). Principles survive outside the original vertical. | Not started |
| M5 | Scientific theory | The model is a validated scientific theory. It has survived falsification attempts, adversarial review, and transferability testing. It makes predictions that are confirmed by reality. | Not started |

---

## Current state: M1 (Structured observations)

The model has:
- ✅ 20 nodes (10 capabilities, 5 constraints, 5 patents)
- ✅ 37 edges, each with an EdgeJustification
- ✅ 11 principles, each with scope and exceptions
- ✅ 5 assumptions, each with falsification criteria
- ✅ 4 authorized edge types (ENABLES and SUBSTITUTES_FOR suspended)
- ✅ Evidence edges separated from structural edges
- ✅ Ordinal confidence labels (EXPLICIT/IMPLIED/STRUCTURAL/SPECULATIVE)
- ✅ Four-layer architecture (Constitutional / Experimental / Observation / Epistemic)
- ✅ Stress tests completed (4/5 assumptions falsified; 8/11 principles survived)
- ✅ 8 failure cases recorded in CEMETERY.md

The model does NOT have:
- ❌ Frozen-time backtest results (not yet run)
- ❌ Precision/recall measurements (requires backtest)
- ❌ Comparison to NULL_MODEL (not yet implemented)
- ❌ Comparison to EXPERT_MODEL (requires human expert)
- ❌ Transferability test (second vertical not authorized)
- ❌ Outcome validation (predictions have not been tested against reality)

---

## What M2 requires

To advance from M1 to M2 (Reproducible evidence):

1. **Run the frozen-time backtest** (BACKTEST_PROTOCOL.md).
   - Freeze the graph at T = 1995, 2000, 2005, 2010, 2015, 2020.
   - Generate predictions (ranked reachable combinations).
   - Evaluate at T+5 to T+10.
   - Record precision, recall, false positives, false negatives.

2. **Implement the NULL_MODEL** (RIVAL_MODEL_PROTOCOL.md).
   - Random selection of capability combinations.
   - Compare precision/recall to the CAPABILITY_MODEL.
   - If CAPABILITY_MODEL doesn't beat NULL_MODEL → IC-001 met → theory fails.

3. **Record failures** (evidence/failures/).
   - Every false positive and false negative.
   - Each failure explained per COUNTERFACTUAL_PROTOCOL.md.
   - Each failure reviewed per ADVERSARIAL_REVIEW_PROTOCOL.md.

4. **Update falsified assumptions** (ASSUMPTION_LIFECYCLE.md).
   - IC-006 is AT RISK: 4/5 assumptions falsified but not yet replaced.
   - The model must be updated before the backtest runs.

---

## What M3 requires

To advance from M2 to M3 (Predictive capability):

1. The model beats the NULL_MODEL on precision.
2. The model beats the CO_OCCURRENCE_MODEL on precision.
3. The model beats the CO_OCCURRENCE_MODEL on false positives.
4. The model's predictions are interpretable (provenance chain complete).
5. The model's predictions are reproducible (same input → same output).

---

## What M4 requires

To advance from M3 to M4 (Transferability):

1. The method transfers to photovoltaics (second vertical).
2. Principles that are domain-general survive.
3. Principles that are domain-specific are correctly scoped.
4. The model beats the NULL_MODEL in the second domain.

---

## What M5 requires

To advance from M4 to M5 (Scientific theory):

1. The model has survived multiple falsification attempts.
2. The model has survived adversarial review (all 4 roles).
3. The model has survived transferability testing.
4. The model makes predictions confirmed by reality.
5. The model's failures are explained and the model was updated.

---

## The honest framing

The model is at M1. It is structured, honest about its limitations,
and has been stress-tested. But it has not yet been validated against
reality. No prediction has been tested. No comparison to random has
been made. The model could still be noise.

This is not a failure. It is the correct state for a model that
has been built carefully but not yet tested. The next step is M2:
run the backtest.
