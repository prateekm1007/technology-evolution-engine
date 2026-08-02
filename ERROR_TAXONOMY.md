# ERROR_TAXONOMY — Phase 8A

**Status:** constitutional document (classification of prediction errors).
**Location:** repo root.
**Phase:** 8A.

This document defines the types of errors the model can make, what
each type means, and which assumption or principle is likely violated
for each type.

---

## 1. Error types

| Error type | What happened | What it means | Likely violated |
|---|---|---|---|
| FALSE POSITIVE | Model predicted a combination would become reachable; it didn't | The model over-predicted. Either a constraint was missed, a capability's readiness was overestimated, or the combination wasn't actually reachable. | A constraint (missing), A-002 (capability insufficient), A-005 (constraint missing) |
| FALSE NEGATIVE | A combination became reachable; the model didn't predict it | The model under-predicted. Either a capability was missing from the catalog, a constraint was over-applied, or the structural edges were wrong. | A-002 (capability missing), A-003 (invariant wrong), P-xxx (principle wrong) |
| MISPLACED CONFIDENCE | Model predicted with high confidence; outcome was the opposite | The model's confidence calibration is wrong. The structural edges or evidence are misleading. | A-001 (CPC ≈ capability), P-xxx (principle scope too narrow/broad) |
| UNEXPLAINED | Model cannot trace why a prediction was made | Provenance chain is broken. The graph has edges without justifications or principles without scope. | EVIDENCE_PROTOCOL violation, CAUSALITY_POLICY violation |

---

## 2. Error severity

| Severity | Meaning | Action |
|---|---|---|
| CRITICAL | The model's core assumptions or principles are wrong | Model is invalidated. H0 reinstated. |
| MAJOR | A specific assumption or principle is wrong | The assumption/principle is retired or revised. Model continues with correction. |
| MINOR | The model missed an edge case | Edge case documented. Model continues unchanged. |
| INFORMATIONAL | The model was right but for the wrong reason | Record the alternative explanation. The model got lucky; it shouldn't count as validation. |

---

## 3. The most dangerous error

**INFORMATIONAL** is the most dangerous because it looks like success
but isn't. The model predicted correctly, but the REASON it predicted
correctly was wrong — the structural edge was misapplied, the
principle was out of scope, or the evidence was misinterpreted.

A model that succeeds for the wrong reasons is worse than a model
that fails honestly, because:
- Failure prompts correction.
- "Success" reinforces the wrong reasoning.
- The next prediction (made for the same wrong reason) will fail.

Per the CEO's directive: "Every successful prediction is evidence.
Every failed prediction is also evidence." But a successful prediction
with a wrong provenance chain is FALSE evidence — it looks like
validation but is actually a bug.

---

## 4. What this document does NOT do

- It does NOT define how to record failures (that's Phase 8B:
  evidence/failures/).
- It does NOT define how to explain failures (that's Phase 8C:
  counterfactual protocol).
- It defines the TYPES of errors and their implications for the
  model's validity.
