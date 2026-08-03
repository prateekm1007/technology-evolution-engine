# STATE_TRANSITION_MODEL

**Status:** Phase 16 Deliverable 3.
**Location:** repo root.
**Phase:** 16.

> State before trajectory.
> — REACHABILITY_CONSTITUTION.md, Rule 2

---

## Purpose

This document defines how state vectors transition over time. The
frozen formula uses trajectories (dTRL/dt) without grounding them
in state. This document defines the state-first model: the system's
state at time T determines what is reachable; the transition from
state(T) to state(T+1) is governed by mechanisms (per
MECHANISM_REGISTRY_V2.md).

This is Layer 1 of the architecture (State estimation). It sits
below classification (Layer 2) and instrument selection (Layer 3).

---

## Schema

```typescript
interface StateVector {
    capabilityState: number
    scientificState: number
    manufacturingState: number
    institutionalState: number
    economicState: number
    regulatoryState: number
    coordinationState: number
    infrastructureState: number
}
```

Each field is a normalized score [0, 1] representing the state of
that dimension. 0 = absent/impossible; 1 = mature/universal.

### Why single numbers (not vectors per dimension)

Each state dimension is a composite (per STATE_SPACE.md). For
example, capability_state is (TRL, generation, sub-capability,
active/legacy). The StateVector uses a single normalized number
per dimension for interoperability across instruments. The
underlying composite is accessible via the state estimator (not
defined in this document).

---

## State transitions

A state transition is:

```typescript
interface StateTransition {
    fromState: StateVector
    toState: StateVector
    deltaTime: number  // years
    mechanism: string  // MECH-XXX from MECHANISM_REGISTRY_V2.md
    trigger: string    // what caused the transition
}
```

### Transition rules

1. **State does not change without a mechanism.** A state transition
   requires a mechanism (per MECHANISM_REGISTRY_V2.md) to fire.
   Without a mechanism, the state is stable.

2. **Mechanisms are gated by constraints.** A mechanism fires only
   if its constraints are absent. If a constraint is active, the
   mechanism does not fire, and the state does not transition.

3. **Transitions are observable.** Every transition must produce
   an observable change in at least one state variable. A
   transition with no observable change is not a transition.

4. **Transitions are directional.** State can increase (capability
   matures, cost declines) or decrease (capability is superseded,
   cost rises). The frozen formula assumes monotonic increase; this
   model does not.

---

## Transition examples

### Example 1: Emergence (Li-ion, 1990-1995)

```json
{
  "fromState": {
    "capabilityState": 0.4,
    "scientificState": 0.8,
    "manufacturingState": 0.5,
    "institutionalState": 0.3,
    "economicState": 0.2,
    "regulatoryState": 0.4,
    "coordinationState": 0.5,
    "infrastructureState": 0.3
  },
  "toState": {
    "capabilityState": 0.8,
    "scientificState": 0.8,
    "manufacturingState": 0.6,
    "institutionalState": 0.4,
    "economicState": 0.25,
    "regulatoryState": 0.5,
    "coordinationState": 0.5,
    "infrastructureState": 0.35
  },
  "deltaTime": 5,
  "mechanism": "MECH-E001",
  "trigger": "STATE_OF_CHARGE_MONITORING rises from TRL 4 to TRL 9"
}
```

### Example 2: Coordination (Telecom, 2008-2009)

```json
{
  "fromState": {
    "capabilityState": 0.9,
    "scientificState": 0.9,
    "manufacturingState": 0.8,
    "institutionalState": 0.7,
    "economicState": 0.7,
    "regulatoryState": 0.6,
    "coordinationState": 0.8,
    "infrastructureState": 0.7
  },
  "toState": {
    "capabilityState": 0.9,
    "scientificState": 0.9,
    "manufacturingState": 0.8,
    "institutionalState": 0.9,
    "economicState": 0.7,
    "regulatoryState": 0.8,
    "coordinationState": 0.95,
    "infrastructureState": 0.75
  },
  "deltaTime": 1,
  "mechanism": "MECH-C001",
  "trigger": "3GPP Release 8 frozen (LTE standard)"
}
```

Note: capabilityState does not change (already at 0.9 = TRL 9).
The transition is in coordinationState and institutionalState.

### Example 3: Scaling (Semiconductors, 1971-1985)

```json
{
  "fromState": {
    "capabilityState": 0.9,
    "scientificState": 0.9,
    "manufacturingState": 0.5,
    "institutionalState": 0.6,
    "economicState": 0.4,
    "regulatoryState": 0.7,
    "coordinationState": 0.6,
    "infrastructureState": 0.5
  },
  "toState": {
    "capabilityState": 0.9,
    "scientificState": 0.9,
    "manufacturingState": 0.7,
    "institutionalState": 0.6,
    "economicState": 0.5,
    "regulatoryState": 0.7,
    "coordinationState": 0.6,
    "infrastructureState": 0.6
  },
  "deltaTime": 14,
  "mechanism": "MECH-S001",
  "trigger": "Manufacturing yield improvement, cost decline from $3000 to $1000 per unit"
}
```

Note: capabilityState does not change. The transition is in
manufacturingState and economicState.

---

## State estimation protocol

Estimating the state vector at time T requires:

1. **capabilityState:** Read TRL from TRAJECTORY_REGISTRY.md (or equivalent). Normalize: TRL/9.
2. **scientificState:** Count publications, citations, replications. NOT IMPLEMENTED.
3. **manufacturingState:** Read yield, defect density, throughput. PARTIALLY IMPLEMENTED (cost data only).
4. **institutionalState:** Read standards-body phase, consortium maturity. NOT IMPLEMENTED.
5. **economicState:** Read cost per unit, market size. PARTIALLY IMPLEMENTED (cost data only).
6. **regulatoryState:** Read approval status, testing phase. NOT IMPLEMENTED.
7. **coordinationState:** Read consensus progress, patent landscape. NOT IMPLEMENTED.
8. **infrastructureState:** Read deployment density, capacity. NOT IMPLEMENTED.

7 of 8 dimensions are NOT IMPLEMENTED or partially implemented.
The state estimation protocol is specified; the data collection
is not.

---

## What this model does NOT do

- It does not predict state transitions. It records them. Prediction is downstream (Layer 4 — Reachability estimation).
- It does not implement the state estimator. The estimator reads data and produces StateVector values; this document defines the schema.
- It does not claim the 8 dimensions are independent. Some may be correlated (as cost_bonus was correlated with velocity in the Phase 12 ablation). Correlation is detected through backtest.
- It does not modify the frozen formula. The formula uses dTRL/dt (a trajectory), not the full StateVector. This model is the foundation for future instruments that DO use the full StateVector.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 8-dimensional StateVector captures all state needed to determine reachability.

**Falsifier:** A reachability-changing event whose state cannot be represented as a transition in this 8-dimensional space — i.e., an event that changes reachability without changing any of the 8 state variables.

**Status:** PENDING. No such event has been identified. But 7 of 8 dimensions are not implemented, so the model is largely untestable until data collection occurs.
