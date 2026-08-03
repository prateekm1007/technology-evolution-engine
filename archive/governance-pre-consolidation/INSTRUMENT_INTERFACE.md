# INSTRUMENT_INTERFACE

**Status:** Phase 16 Deliverable 1.
**Location:** repo root.
**Phase:** 16.

> Nothing predictive is built. Nothing is optimized. Nothing is
> deployed. Only interfaces are defined.
> — CEO directive, Phase 16

---

## Purpose

This document defines the interface that every instrument (formula,
detector, estimator) in the reachability engine must implement.
The frozen formula `score = max(dTRL/dt) × adjacency` is the first
instrument. Future instruments (for Scaling, Coordination,
Discovery) must implement this interface to be accepted into the
engine.

Per REACHABILITY_CONSTITUTION.md Rule 3 (mechanisms before formulas):
every instrument must cite the mechanism it is an instrument for.
An instrument without a cited mechanism is rejected.

---

## Schema

```typescript
interface Instrument {
    id: string;

    supportedClasses: string[];

    supportedStates: string[];

    limitations: string[];
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | INST-XXX identifier. Sequential. |
| `supportedClasses` | string[] | yes | Which process classes (from PROCESS_CLASSIFIER.md) this instrument can be applied to. Must be non-empty. An instrument that supports all 5 classes is suspect — it probably has no boundary (violates REACHABILITY_CONSTITUTION.md Rule 4). |
| `supportedStates` | string[] | yes | Which state dimensions (from STATE_SPACE.md) this instrument reads as input. Must be non-empty. The frozen formula reads only capability_state. |
| `limitations` | string[] | yes | The conditions under which this instrument does NOT apply. This is the instrument's boundary statement (per REACHABILITY_CONSTITUTION.md Rule 4). Must be non-empty. |

### Extended schema (for instrument registration)

When an instrument is registered in the engine, additional fields
are recorded:

```typescript
interface RegisteredInstrument extends Instrument {
    mechanismId: string;        // from MECHANISM_REGISTRY_V2.md
    formulaReference: string;   // commit hash or file path
    boundaryStatement: string;  // from BOUNDARY_THEOREM.md or equivalent
    testedOnDomains: string[];  // domains where this instrument has been backtested
    statisticalStatus: {
        precision: number;
        recall: number;
        mcnemarP: number;
        n: number;
    };
}
```

---

## The first registered instrument

### INST-001: Frozen Formula (velocity × adjacency)

| Field | Value |
|---|---|
| id | INST-001 |
| supportedClasses | ["EMERGENCE", "RECOMBINATION"] |
| supportedStates | ["capability_state"] |
| limitations | ["Does not detect Scaling events (zero velocity, mature capabilities)", "Does not detect Coordination events (no coordination_state variable)", "Does not detect Discovery events (no scientific_state variable)", "Does not handle non-monotonic TRL (re-rise problem, telecom generation transitions)", "Velocity threshold > 0.20 is calibrated to Li-ion; too strict for domains with 1-TRL-per-5-year granularity", "Not statistically significant in any tested domain (Li-ion p=0.2188, semiconductors p=0.5000, telecom p=0.5000)"] |
| mechanismId | MECH-E001, MECH-R001, MECH-R002 |
| formulaReference | FORMULA_B_FROZEN.md, scripts/run_ablation.py |
| boundaryStatement | BOUNDARY_THEOREM.md |
| testedOnDomains | ["li_ion", "photovoltaics", "semiconductors", "telecommunications"] |
| statisticalStatus | {precision: 0.0357, recall: 0.20, mcnemarP: 0.2188, n: 14} (Li-ion only) |

---

## Instrument lifecycle

```
┌─────────────────────┐
│ Mechanism identified│
│ (MECHANISM_REGISTRY │
│  _V2.md)            │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Instrument designed │
│ (implements this    │
│  interface)         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Boundary stated     │
│ (limitations field  │
│  non-empty)         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Backtest run        │
│ (on at least 1      │
│  domain)            │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Statistical status  │
│ recorded            │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Instrument          │
│ registered          │
│ (INST-XXX assigned) │
└─────────────────────┘
```

### Lifecycle rules

1. **No instrument without a mechanism.** Per REACHABILITY_CONSTITUTION.md Rule 3, the mechanism must be cataloged in MECHANISM_REGISTRY_V2.md before the instrument is designed.
2. **No instrument without a boundary.** Per Rule 4, the `limitations` field must be non-empty. An instrument claiming to apply everywhere is rejected.
3. **No instrument without a backtest.** The instrument must be run on at least 1 domain with a recorded statistical status. Instruments without backtests are PROVISIONAL — they may be used for exploration but not for production reachability estimates.
4. **No instrument without a falsifier.** Per EP-4, the instrument's claim (that it detects its supportedClasses via its supportedStates) must have a pre-stated falsifier in EVIDENCE_FALSIFIERS.md.

---

## Instrument selection (Layer 3 of the architecture)

When the reachability engine receives a query, it:

1. Classifies the query (Layer 2 — CLASSIFICATION_PROTOCOL.md).
2. Selects instruments whose `supportedClasses` include the classified class.
3. Filters instruments whose `limitations` exclude the current state.
4. Runs the remaining instruments.
5. Combines their outputs (Layer 4 — REACHABILITY_API_SPEC.md).

### Selection example

Query: "Is a 5G mmWave deployment in rural India reachable within 5 years?"

Classification: COORDINATION (standards-body consensus for 5G NR) + SCALING (infrastructure deployment)

Candidate instruments:
- INST-001 (frozen formula): supportedClasses = [EMERGENCE, RECOMBINATION]. Does NOT include COORDINATION or SCALING. REJECTED.
- INST-002 (hypothetical coordination instrument): supportedClasses = [COORDINATION]. ACCEPTED.
- INST-003 (hypothetical scaling instrument): supportedClasses = [SCALING]. ACCEPTED.

In this example, INST-001 (the frozen formula) is correctly rejected because the query is a Coordination + Scaling problem, not an Emergence + Recombination problem. The frozen formula would produce a wrong estimate.

---

## What this interface does NOT do

- It does not define how instruments compute their estimates. That is the instrument's internal design, not the interface's concern.
- It does not define how multiple instruments' outputs are combined. That is REACHABILITY_API_SPEC.md (Layer 4).
- It does not define how instruments are discovered. That is the engine's runtime concern.
- It does not modify the frozen formula. INST-001 is registered with its existing limitations.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every reachability-changing mechanism (per MECHANISM_REGISTRY_V2.md) can be detected by an instrument implementing this interface.

**Falsifier:** A mechanism whose detection requires inputs or outputs not expressible in this interface. Specifically: a mechanism that needs a state variable not in `supportedStates`, or that produces a class not in `supportedClasses`, or that has no boundary (applies everywhere — violating Rule 4).

**Status:** PENDING. No such mechanism has been identified. But only 1 of 9 mechanisms has a registered instrument (INST-001 for MECH-E001/R001/R002). The other 6 mechanisms need instruments — whether those instruments can implement this interface is untested.
