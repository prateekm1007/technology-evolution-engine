# REACHABILITY_API_SPEC

**Status:** Phase 16 Deliverable 4.
**Location:** repo root.
**Phase:** 16.

> The system accepts an idea and produces an executable blueprint.
> — CEO directive, Phase 16A

---

## Purpose

This document defines the API for querying the reachability engine.
It specifies the inputs, outputs, and protocol for Layers 4 and 5
of the architecture (Reachability estimation and Explanation).

This is a specification, not an implementation. No API server is
built in Phase 16.

---

## Schema

### ReachabilityEstimate (Layer 4 output)

```typescript
interface ReachabilityEstimate {
    state: string

    bottlenecks: string[]

    constraints: string[]

    reachablePossibilities: string[]

    confidence: number
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `state` | string | yes | A description of the current landscape state. References the StateVector (per STATE_TRANSITION_MODEL.md). |
| `bottlenecks` | string[] | yes | The active bottlenecks (per BOTTLENECK_REGISTRY.md) that are currently blocking reachability. Empty array = no bottlenecks. |
| `constraints` | string[] | yes | The active constraints (per CONSTRAINT_CATALOG.md) that bound what is possible. Empty array = no constraints. |
| `reachablePossibilities` | string[] | yes | The combinations or events that are currently reachable given the state, bottlenecks, and constraints. Empty array = nothing reachable. |
| `confidence` | float [0, 1] | yes | The engine's confidence in the estimate. Based on: (a) classifier confidence, (b) instrument statistical status, (c) state estimation completeness. |

---

## API endpoints

### Query: estimate reachability

**Input:**

```typescript
interface ReachabilityQuery {
    query: string              // natural-language or structured query
    domain: string             // the domain context
    timeHorizon: number        // years
    stateVector?: StateVector  // optional; if not provided, engine estimates from data
}
```

**Output:** `ReachabilityEstimate`

**Protocol:**

```
1. Classify the query (CLASSIFICATION_PROTOCOL.md)
   → ClassificationResult

2. Select instruments (INSTRUMENT_INTERFACE.md)
   → Instrument[] (whose supportedClasses include the classified class)

3. Filter instruments by limitations
   → Instrument[] (whose limitations do not exclude the current state)

4. Run remaining instruments
   → per-instrument estimates

5. Combine estimates
   → ReachabilityEstimate (combination protocol below)

6. Generate explanation (EXPLANATION_PROTOCOL.md)
   → Explanation
```

### Combination protocol

When multiple instruments produce estimates, they are combined:

- **reachablePossibilities:** union of all instruments' reachable possibilities.
- **bottlenecks:** union of all instruments' detected bottlenecks.
- **constraints:** intersection of all instruments' constraints (a constraint is active only if ALL instruments agree).
- **confidence:** minimum of all instruments' confidences (conservative — the estimate is only as confident as the least-confident instrument).

If instruments disagree (one says reachable, another says not), the disagreement is recorded in the explanation (Layer 5), and the confidence is halved.

---

### Query: explain estimate

**Input:** `ReachabilityEstimate`

**Output:**

```typescript
interface Explanation {
    mechanism: string

    evidence: string[]

    assumptions: string[]

    boundaries: string[]
}
```

(See EXPLANATION_PROTOCOL.md for details.)

---

## Example queries and responses

### Example 1: Li-ion EV (1995)

**Query:**
```json
{
  "query": "Is a Li-ion EV with BMS reachable within 5 years?",
  "domain": "li_ion",
  "timeHorizon": 5,
  "stateVector": {
    "capabilityState": 0.6,
    "scientificState": 0.8,
    "manufacturingState": 0.4,
    "institutionalState": 0.3,
    "economicState": 0.2,
    "regulatoryState": 0.3,
    "coordinationState": 0.5,
    "infrastructureState": 0.2
  }
}
```

**Classification:** EMERGENCE (STATE_OF_CHARGE_MONITORING rising) + RECOMBINATION (combination becoming reachable)

**Instruments selected:** INST-001 (frozen formula — supports EMERGENCE + RECOMBINATION)

**Response:**
```json
{
  "state": "Li-ion landscape in 1995: STATE_OF_CHARGE_MONITORING at TRL 9 (just matured), cost $3000/kWh (economic bottleneck), no charging infrastructure.",
  "bottlenecks": ["cost ($3000/kWh blocks mass market)", "no charging infrastructure"],
  "constraints": ["thermal runaway threshold (physical)", "cost per kWh > $1000 (economic)"],
  "reachablePossibilities": [
    "Li-ion with BMS in fleet EVs (EES + INTERCALATION + SoC)"
  ],
  "confidence": 0.6
}
```

### Example 2: Telecom 5G (2018)

**Query:**
```json
{
  "query": "Is 5G mmWave deployment reachable within 5 years?",
  "domain": "telecommunications",
  "timeHorizon": 5
}
```

**Classification:** COORDINATION (3GPP Release 15) + SCALING (infrastructure deployment)

**Instruments selected:** NONE. INST-001 (frozen formula) does not support COORDINATION or SCALING. No other instruments are registered.

**Response:**
```json
{
  "state": "5G mmWave landscape in 2018: WIRELESS_PROTOCOL at TRL 9 (plateaued since 1985), SPECTRUM_UTILIZATION re-rising for mmWave (TRL 5, non-monotonic). 3GPP Release 15 frozen.",
  "bottlenecks": ["mmWave range/blockage (physical)", "small cell density required (infrastructure)", "spectrum auction timing (regulatory)"],
  "constraints": ["coordination_state not measurable by INST-001", "infrastructure_state not in frozen formula"],
  "reachablePossibilities": [],
  "confidence": 0.0
}
```

**Note:** The engine correctly reports that it CANNOT estimate this query. No instrument supports the COORDINATION + SCALING classes. This is honest — the frozen formula (INST-001) is the only registered instrument, and it does not apply. The confidence is 0.0.

---

## What this API does NOT do

- It does not implement the API server. This is a specification, not a deployment.
- It does not define authentication, rate limiting, or persistence. Those are operational concerns, not architectural.
- It does not define how the engine handles concurrent queries. That is a runtime concern.
- It does not modify the frozen formula. INST-001 is the only registered instrument; queries it cannot handle return confidence 0.0.

---

## Pre-stated falsifier (EP-4)

**Claim:** The ReachabilityEstimate schema captures all information needed to answer "what becomes possible next?"

**Falsifier:** A query where the ReachabilityEstimate is insufficient — i.e., a decision-maker needs information not in the estimate (state, bottlenecks, constraints, reachable possibilities, confidence) to act.

**Status:** PENDING. No queries have been run (no implementation).
