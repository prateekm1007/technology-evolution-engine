# CLASSIFICATION_PROTOCOL

**Status:** Phase 16 Deliverable 2.
**Location:** repo root.
**Phase:** 16.

> Never ask "What will happen?" Ask "What kind of process is this?"
> — CEO directive, Phase 15, Principle 2

---

## Purpose

This document defines the protocol for classifying a process before
any instrument runs. Per REACHABILITY_CONSTITUTION.md Rule 1
(classification before prediction), classification is a hard gate:
no instrument runs until the process class is identified.

The classifier itself is NOT built in Phase 16. This document
defines the PROTOCOL — the inputs, outputs, and rules. The
classifier implementation is a future phase.

---

## Schema

```typescript
interface ClassificationResult {
    class:
        | "DISCOVERY"
        | "EMERGENCE"
        | "SCALING"
        | "COORDINATION"
        | "RECOMBINATION";

    confidence: number;

    evidence: string[];
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `class` | enum | yes | One of the 5 classes from PROCESS_CLASSIFIER.md. |
| `confidence` | float [0, 1] | yes | The classifier's confidence in the assignment. 0 = no confidence; 1 = certain. Confidence < 0.5 triggers UNCLASSIFIED status (see below). |
| `evidence` | string[] | yes | The observable features that led to the classification. Must cite specific state variables (per STATE_SPACE.md) and their values. Must be checkable from data, not interpretive. |

### UNCLASSIFIED status

If `confidence < 0.5`, the classification result is treated as
UNCLASSIFIED. No instrument runs. The event is recorded in
BOUNDARY_REGISTRY.md as a NEW_PATTERN candidate.

This is a safety valve: if the classifier cannot confidently assign
a class, the system does not guess. It records the uncertainty and
stops.

---

## Classification inputs

The classifier takes:

```typescript
interface ClassificationInput {
    query: string;              // the natural-language or structured query
    stateVector: StateVector;  // the current state (per STATE_SPACE.md)
    domain: string;             // the domain context
    timeHorizon: number;        // the prediction horizon in years
}
```

The classifier uses the `stateVector` and `domain` to determine
which class the process belongs to. The `query` provides context.
The `timeHorizon` affects classification (Discovery has a 10-20+
year horizon; Scaling has a 1-5 year horizon).

---

## Classification rules

The classifier applies the following rules, in order. The first
rule that fires determines the class. If no rule fires, the result
is UNCLASSIFIED.

### Rule 1: DISCOVERY

**Fires when:**
- `stateVector.scientificState` indicates a recent publication or experimental result (paradigm_acceptance = fringe or contested)
- The query references a scientific paper, patent, or experimental result
- No capability in the query has TRL ≥ 5 (the discovery is upstream of capability maturity)

**Confidence:** based on the scientific_state measurement quality (publication count, citation velocity, replication status).

### Rule 2: EMERGENCE

**Fires when:**
- At least one capability in the query has TRL < 7 at T-k and TRL ≥ 7 at T (rising)
- The velocity `dTRL/dt > 0.20` for at least one capability
- The query references a capability crossing a maturity threshold

**Confidence:** based on the velocity magnitude (higher velocity = higher confidence).

### Rule 3: SCALING

**Fires when:**
- All capabilities in the query are at TRL 9 at T-1
- The query references a quantitative metric improving (transistor count, data rate, cost per unit)
- No capability crosses a maturity threshold
- No standards-body or regulatory event is referenced

**Confidence:** based on the manufacturing_state and economic_state measurement quality.

### Rule 4: COORDINATION

**Fires when:**
- All capabilities in the query are at TRL ≥ 7 at T-1
- The query references a standards body, regulatory authority, or industry consortium
- `stateVector.coordinationState` or `stateVector.regulatoryState` indicates an active process

**Confidence:** based on the coordination_state or regulatory_state measurement quality.

### Rule 5: RECOMBINATION

**Fires when:**
- All capabilities in the query are at TRL ≥ 7 at T-1
- The combination is graph-distance ≤ 2 from existing realized combinations
- No capability is rising (velocity = 0 for all capabilities)
- No standards-body or regulatory event is referenced

**Confidence:** based on the adjacency measurement (closer = higher confidence).

### Dominance resolution

If multiple rules fire, the dominance rule (from PROCESS_CLASSIFIER.md)
applies: the class whose absence would have prevented the event
dominates.

Priority order (when dominance cannot be resolved by absence):
1. DISCOVERY (upstream of everything)
2. EMERGENCE (capability formation is the trigger)
3. COORDINATION (consensus enables deployment)
4. RECOMBINATION (combination becomes reachable)
5. SCALING (optimization within mature capability)

---

## Classification protocol

```
┌─────────────────────────────┐
│ Input: query + stateVector  │
│ + domain + timeHorizon      │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Apply Rule 1 (DISCOVERY)    │
│ Fires? ──── yes ───→ DISCOVERY
│     │                        │
│     no                       │
│     ▼                        │
│ Apply Rule 2 (EMERGENCE)    │
│ Fires? ──── yes ───→ EMERGENCE
│     │                        │
│     no                       │
│     ▼                        │
│ Apply Rule 3 (SCALING)       │
│ Fires? ──── yes ───→ SCALING
│     │                        │
│     no                       │
│     ▼                        │
│ Apply Rule 4 (COORDINATION) │
│ Fires? ──── yes ───→ COORDINATION
│     │                        │
│     no                       │
│     ▼                        │
│ Apply Rule 5 (RECOMBINATION)│
│ Fires? ──── yes ───→ RECOMBINATION
│     │                        │
│     no                       │
│     ▼                        │
│ UNCLASSIFIED                 │
│ (confidence < 0.5)          │
│ → record in BOUNDARY_REGISTRY│
│   as NEW_PATTERN candidate  │
└─────────────────────────────┘
```

---

## What this protocol does NOT do

- It does not implement the classifier. The rules are specified; the implementation (decision tree, learned model, or human judgment) is a future phase.
- It does not guarantee correct classification. The classifier may assign the wrong class, causing the wrong instrument to run. This is detected through backtest (low precision) and recorded in BOUNDARY_REGISTRY.md.
- It does not handle temporal evolution (an event transitioning between classes over time — see OPEN_QUESTIONS.md Q-004).
- It does not modify the frozen formula. INST-001 is registered for EMERGENCE + RECOMBINATION; if the classifier assigns these classes, INST-001 runs.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 5 rules (DISCOVERY, EMERGENCE, SCALING, COORDINATION, RECOMBINATION) correctly classify all events in the project's registries.

**Falsifier:** An event that the classifier assigns to the wrong class (causing the wrong instrument to run and producing a wrong prediction) OR an event that fires no rule (UNCLASSIFIED) but later turns out to belong to one of the 5 classes.

**Status:** PENDING. The classifier is not implemented, so no events have been classified yet.
