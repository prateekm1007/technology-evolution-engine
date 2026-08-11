# VALIDATION_CONSTITUTION — Phase 8A

**Status:** constitutional document (validation framework).
**Location:** repo root.
**Phase:** 8A (per CEO directive: transform the capability engine into a falsifiable scientific instrument).

> The objective is no longer: 'Build the invention engine.'
> The objective is now: 'Determine whether an invention engine is possible.'
> — CEO directive, Phase 8

This document defines what it means for the CAPABILITY_MODEL to be
a falsifiable scientific instrument rather than an interesting
architecture. It defines the questions that must be answered, the
evidence that must be collected, and the conditions under which the
model is considered validated or invalidated.

---

## 1. The five required questions

Per CEO directive, the validation constitution must answer:

### Q1: What would prove us wrong?

A specific prediction the model makes that, if it fails, invalidates
the model. Without this, the model is unfalsifiable — it can explain
anything after the fact but predicts nothing.

**Example:** If the model predicts that {FAST_CHARGING, THERMAL_MANAGEMENT}
is a reachable combination as of 2010, and no fast-charging battery
with thermal management was commercially available by 2020, the
prediction failed. If the model cannot explain WHY it failed (which
assumption or principle was violated), the model is invalid.

### Q2: What observations would invalidate the model?

Specific observations that, if made, would prove the model's
principles or assumptions are wrong.

**Example:** If a battery is observed that stores energy electrochemically
WITHOUT ion transport (violating P-001: charge conservation), P-001 is
wrong. This is extremely unlikely (it would violate physics), but the
principle is stated as falsifiable.

**Example:** If CPC codes are observed to systematically misclassify
patents (A-001 falsified), the EMBODIED_IN evidence is unreliable.

### Q3: Which assumptions are load-bearing?

An assumption is load-bearing if the model's predictions change when
the assumption is removed. Non-load-bearing assumptions can be wrong
without affecting the model.

All 5 assumptions (A-001 through A-005) are potentially load-bearing.
The backtest will determine which ones actually are. An assumption
that is NOT load-bearing should be retired (it adds complexity
without affecting predictions).

### Q4: Which principles are domain-specific?

Per CEO Rule 2, every principle has a scope. A principle is
domain-specific if it applies only within a narrow domain (e.g.,
P-002 "lattice insertion" applies only to Li-ion). A principle
that is universal (e.g., P-001 "charge conservation") is stronger
but also harder to falsify.

The transferability test (Phase 8E) will determine which principles
survive outside electrochemical energy storage.

### Q5: Which predictions would distinguish the models?

A prediction that both the CAPABILITY_MODEL and the
CO_OCCURRENCE_MODEL make, but that comes out differently, is a
distinguishing prediction. If no distinguishing predictions exist,
the models are empirically equivalent and the architectural pivot
was unnecessary.

**Example:** The CAPABILITY_MODEL predicts that {ION_TRANSPORT,
THERMAL_MANAGEMENT} is a reachable combination because both are
REQUIRED by FAST_CHARGING (structural necessity). The
CO_OCCURRENCE_MODEL predicts based on whether "ion transport" and
"thermal management" co-occur in patent text. If the patents use
different vocabulary (e.g., "electrolyte conductivity" instead of
"ion transport"), the CO_OCCURRENCE_MODEL misses it but the
CAPABILITY_MODEL (using CPC codes) catches it. This is a
distinguishing prediction.

---

## 2. The validation contract

The model is considered VALIDATED only when ALL of the following hold:

1. **At least one prediction has been made BEFORE the outcome was
   known.** (Not retrospective.)

2. **At least one prediction has FAILED.** (A model that only
   succeeds has not been tested.)

3. **Every failure has been explained.** (Which assumption or
   principle was violated?)

4. **Every success has been checked for false positives.** (How
   many other things did the model flag that didn't happen?)

5. **The model distinguishes itself from the CO_OCCURRENCE_MODEL.**
   (At least one distinguishing prediction exists and has been
   tested.)

6. **The principles transfer to at least one other domain.**
   (Phase 8E.)

7. **The assumptions have been tested for load-bearing status.**
   (Phase 8B.)

Until all 7 conditions hold, the model is PROVISIONAL, not VALIDATED.

---

## 3. The invalidation contract

The model is considered INVALIDATED if ANY of the following occur:

1. **Ontology explosion:** node/edge types exceed ONTOLOGY_FREEZE caps.
2. **Inability to explain predictions:** the model flags a combination
   but cannot trace why.
3. **Deterioration of precision:** CAPABILITY_MODEL precision <
   CO_OCCURRENCE_MODEL precision.
4. **Excessive false positives:** FP rate higher than
   CO_OCCURRENCE_MODEL.
5. **Inability to replay results:** same input produces different
   output.
6. **Inability to trace evidence:** nodes/edges lack evidence citations.
7. **Assumptions proven wrong without model revision:** an assumption
   is falsified (per its falsification criterion) but the model is not
   updated.

If any of these occur, the model is invalid. The architectural pivot
has not paid off. H0 (the CO_OCCURRENCE_MODEL is sufficient) is
reinstated.

---

## 4. What this document does NOT do

- It does NOT authorize implementation (Phase 7 frozen; Phase 8 is
  definition, not construction).
- It does NOT define the backtest mechanics (that's
  BACKTEST_PROTOCOL.md).
- It does NOT define failure recording (that's Phase 8B).
- It does NOT define counterfactual reasoning (that's Phase 8C).
- It defines the VALIDATION CONTRACT: what conditions must hold for
  the model to be trusted, and what conditions invalidate it.
