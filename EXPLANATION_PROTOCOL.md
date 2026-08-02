# EXPLANATION_PROTOCOL

**Status:** Phase 16 Deliverable 5.
**Location:** repo root.
**Phase:** 16.

> If you can explain why the correct predictions were correct and
> why the incorrect predictions were incorrect, then you are moving
> toward M5. If you cannot, you are merely curve-fitting.
> — CEO directive, Phase 13 (carried forward)

---

## Purpose

This document defines how the reachability engine explains its
estimates. Per REACHABILITY_CONSTITUTION.md Rule 3 (mechanisms
before formulas), every estimate must cite the mechanism that
produced it. Per EP-5 (no self-grading), the explanation is
machine-generated but must be reviewable by an independent process.

This is Layer 5 of the architecture (Explanation). It sits above
reachability estimation (Layer 4).

---

## Schema

```typescript
interface Explanation {
    mechanism: string

    evidence: string[]

    assumptions: string[]

    boundaries: string[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `mechanism` | string | yes | The MECH-XXX identifier from MECHANISM_REGISTRY_V2.md that produced this estimate. If multiple mechanisms contributed, list the dominant one (per PROCESS_CLASSIFIER.md dominance rule). |
| `evidence` | string[] | yes | The observable features that led to the estimate. Must cite specific state variables (per STATE_SPACE.md) and their values. Must be checkable from data. Minimum 2 evidence entries. |
| `assumptions` | string[] | yes | The assumptions the estimate relies on. Must be explicit. If an assumption is violated, the estimate may be wrong. Minimum 1 assumption. |
| `boundaries` | string[] | yes | The conditions under which this estimate does NOT apply. References the instrument's limitations (per INSTRUMENT_INTERFACE.md). Must be non-empty. |

---

## Explanation generation protocol

### Step 1: Identify the mechanism

The explanation starts with the mechanism that produced the
estimate. This is recorded by the instrument when it runs.

### Step 2: Cite evidence

The evidence is the specific state variable values that triggered
the mechanism. For example:

- "capabilityState: STATE_OF_CHARGE_MONITORING at TRL 9 (velocity 0.67, 1990-1995)"
- "coordinationState: 3GPP Release 8 frozen in December 2008"
- "manufacturingState: cost per kWh = $300 (2010), below the $1000 threshold"

Evidence must be checkable from the project's registries or from
public data.

### Step 3: State assumptions

The assumptions are what the estimate takes for granted. For
example:

- "Assumption: the capability trajectory continues at the current velocity."
- "Assumption: no regulatory change blocks deployment."
- "Assumption: the coordination process completes within the time horizon."

Assumptions are the load-bearing conditions. If any assumption is
violated, the estimate may be wrong.

### Step 4: State boundaries

The boundaries are the conditions under which the estimate does
NOT apply. For the frozen formula (INST-001):

- "Boundary: does not detect Scaling events (zero velocity)."
- "Boundary: does not handle non-monotonic TRL (re-rise problem)."
- "Boundary: velocity threshold > 0.20 calibrated to Li-ion."

Boundaries reference the instrument's limitations.

---

## Example explanations

### Example 1: Li-ion EV (1995)

```json
{
  "mechanism": "MECH-E001 (rising capability crosses maturity threshold) + MECH-R002 (enabling capability makes combination reachable)",
  "evidence": [
    "capabilityState: STATE_OF_CHARGE_MONITORING rose from TRL 4 (1990) to TRL 9 (1995), velocity 1.0 (highest in registry)",
    "capabilityState: ELECTROCHEMICAL_ENERGY_STORAGE at TRL 9 (stable since 1991)",
    "capabilityState: INTERCALATION at TRL 9 (stable since 1991)",
    "adjacency: combination {EES, INTERCALATION, SoC} at graph distance 1 from existing {EES, INTERCALATION}"
  ],
  "assumptions": [
    "Assumption: cost per kWh ($3000 in 1995) does not block fleet EV deployment (fleet operators can absorb high cost).",
    "Assumption: no regulatory barrier to Li-ion in vehicles (UN38.3 not yet in force, but fleet EVs are not consumer transport).",
    "Assumption: an OEM is willing to build a Li-ion EV (agency is present)."
  ],
  "boundaries": [
    "Boundary: INST-001 does not predict the SPECIFIC event (Nissan Altra 1997); it predicts the COMBINATION becomes reachable.",
    "Boundary: INST-001 does not detect Scaling or Coordination events; if the event is scaling-driven, this estimate does not apply.",
    "Boundary: velocity threshold > 0.20; STATE_OF_CHARGE_MONITORING velocity is 1.0, well above threshold — this is a high-confidence estimate."
  ]
}
```

### Example 2: Telecom 5G (2018)

```json
{
  "mechanism": "NONE — no registered instrument supports COORDINATION + SCALING",
  "evidence": [
    "classificationResult: COORDINATION + SCALING (confidence 0.8)",
    "instrumentSelection: INST-001 REJECTED (supportedClasses = [EMERGENCE, RECOMBINATION])",
    "no other instruments registered"
  ],
  "assumptions": [
    "Assumption: the engine's inability to estimate is reported honestly (confidence 0.0)."
  ],
  "boundaries": [
    "Boundary: the reachability engine has instruments for only 2 of 5 process classes (EMERGENCE + RECOMBINATION).",
    "Boundary: queries involving COORDINATION, SCALING, or DISCOVERY return confidence 0.0 until instruments for those classes are built.",
    "Boundary: this is not a prediction failure — it is a coverage gap. The engine is honest about what it cannot estimate."
  ]
}
```

---

## Explanation quality (per EP-5)

Per EP-5 (no self-grading), the explanation must be reviewable by
an independent process. The explanation is machine-generated; the
grading is done by:

1. **External adversaries** (Phase 14F: Historian, Economist, Physicist, Statistician) — review explanations for accuracy, completeness, and honesty.
2. **The human reviewer** — grades explanations against a pre-agreed rubric (not yet defined).

Until independent grading occurs, explanations are PROVISIONAL —
they may be useful as input to a decision but should not be
treated as evidence.

---

## What this protocol does NOT do

- It does not implement the explanation generator. The protocol is specified; the implementation is a future phase.
- It does not grade the explanations. Grading is done by an independent process (per EP-5).
- It does not guarantee that explanations are correct. An explanation can be well-formed but wrong (citing the wrong mechanism, or relying on a violated assumption). Correctness is checked through backtest and adversarial review.
- It does not modify the frozen formula. INST-001's explanations cite MECH-E001 and MECH-R001/R002.

---

## Pre-stated falsifier (EP-4)

**Claim:** The Explanation schema (mechanism + evidence + assumptions + boundaries) is sufficient for an independent reviewer to evaluate whether an estimate is trustworthy.

**Falsifier:** An estimate whose explanation is complete (all 4 fields populated, minimum counts met) but that an independent reviewer cannot evaluate — i.e., the reviewer needs information not in the explanation to judge trustworthiness.

**Status:** PENDING. No independent review has occurred (Phase 14F not yet run). The explanation schema may need extension based on reviewer feedback.
