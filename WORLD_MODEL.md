# WORLD_MODEL

**Status:** Phase 16A Deliverable 4.
**Location:** repo root.
**Phase:** 16A.

> State before trajectory.
> — REACHABILITY_CONSTITUTION.md, Rule 2

---

## Purpose

The World Model is the system's representation of the current state
of the world. It provides the StateVector that all engines read
when evaluating an idea. Per REACHABILITY_CONSTITUTION.md Rule 2,
state estimation precedes trajectory analysis.

The World Model is Layer 1 of the architecture. It sits below
classification (Layer 2) and instrument selection (Layer 3).

---

## State vector

```typescript
interface StateVector {
    scientificState: number
    technologicalState: number
    manufacturingState: number
    regulatoryState: number
    economicState: number
    coordinationState: number
    infrastructureState: number
}
```

**Note:** The CEO's Phase 16A directive specifies 7 dimensions here
(scientific, technological, manufacturing, regulatory, economic,
coordination, infrastructure). The Phase 15 STATE_SPACE.md
specified 8 dimensions (capability, scientific, manufacturing,
institutional, economic, regulatory, coordination, infrastructure).

The difference: Phase 15 separates `capabilityState` (TRL) from
`institutionalState` (standards body phase). Phase 16A merges them
into `technologicalState` and does not include `institutionalState`
as a separate dimension.

For consistency, the World Model uses the CEO's 7-dimension schema.
The mapping to Phase 15's 8-dimension schema is:

| Phase 16A (7 dimensions) | Phase 15 (8 dimensions) |
|---|---|
| scientificState | scientificState |
| technologicalState | capabilityState + institutionalState (merged) |
| manufacturingState | manufacturingState |
| regulatoryState | regulatoryState |
| economicState | economicState |
| coordinationState | coordinationState |
| infrastructureState | infrastructureState |

The merger of capabilityState and institutionalState into
technologicalState is a simplification. It may lose resolution
(institutional state and capability maturity are different things).
This is a known trade-off, documented per EP-2 (a check is scoped
to exactly what it checks).

---

## Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `scientificState` | float [0, 1] | yes | State of scientific understanding. 0 = no science; 1 = consensus. |
| `technologicalState` | float [0, 1] | yes | State of technology maturity (TRL + institutional readiness merged). |
| `manufacturingState` | float [0, 1] | yes | State of manufacturing capability (yield, throughput, process maturity). |
| `regulatoryState` | float [0, 1] | yes | State of regulatory approval (pathway, testing, approval status). |
| `economicState` | float [0, 1] | yes | State of economics (cost, market size, willingness-to-pay). |
| `coordinationState` | float [0, 1] | yes | State of multi-actor coordination (standards, consortium, patents). |
| `infrastructureState` | float [0, 1] | yes | State of deployment infrastructure (density, capacity, coverage). |

Each value is normalized [0, 1] for interoperability across engines.

---

## World Model estimation

The World Model is estimated from Layer 0 (Reality):

```
Layer 0 (Reality):
  events, papers, patents, prices, organizations, laws,
  institutions, infrastructure, people
        │
        ▼
┌─────────────────────┐
│ State Estimators    │
│ (one per dimension) │
└────────┬────────────┘
         │
         ▼
    StateVector
```

Each dimension has a state estimator that reads Layer 0 data and
produces a normalized score. The estimators are NOT IMPLEMENTED in
Phase 16A. This document defines the schema; the estimators are
future work.

---

## Example World Model

### Autonomous farming robot (2025)

```json
{
  "scientificState": 0.9,
  "technologicalState": 0.85,
  "manufacturingState": 0.8,
  "regulatoryState": 0.4,
  "economicState": 0.6,
  "coordinationState": 0.5,
  "infrastructureState": 0.7
}
```

Interpretation:
- scientificState 0.9: the science of autonomous robots, computer vision, and solar power is well-understood.
- technologicalState 0.85: the technology (sensors, motors, GPS, processors, batteries, comms) is mature (TRL ≥ 8).
- manufacturingState 0.8: the components can be manufactured at scale.
- regulatoryState 0.4: autonomous vehicle regulations for agricultural use are permissive in some jurisdictions but not others.
- economicState 0.6: unit economics are marginal — solar-powered autonomous robots are expensive but operating costs are low.
- coordinationState 0.5: no industry consortium for agricultural robotics; standards are fragmented.
- infrastructureState 0.7: cellular coverage in rural areas is adequate but not universal; GPS is universal.

---

## What this model does NOT do

- It does not predict future states. It estimates the current state. Future-state prediction is the Simulation Engine's job.
- It does not implement the state estimators. The estimators read Layer 0 data; this document defines the output schema.
- It does not claim the 7 dimensions are independent. Some may be correlated (as cost_bonus was correlated with velocity).
- It does not modify the frozen formula. The formula uses dTRL/dt (a trajectory of capabilityState), not the full StateVector.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 7-dimensional StateVector captures all state needed to evaluate an idea's reachability.

**Falsifier:** An idea whose reachability depends on a state variable not in the 7 dimensions — e.g., an idea that requires knowing the geopolitical state (wars, sanctions, trade agreements) or the talent state (availability of skilled engineers).

**Status:** PENDING. The 7 dimensions may need extension. Phase 15's 8-dimension schema included `institutionalState` separately; Phase 16A merges it into `technologicalState`. If this merger loses resolution, the falsifier fires.

The 9th constraint class in CONSTRAINT_ENGINE.md is "talent" — if talent emerges as a state variable (not just a constraint), an 8th state dimension may be needed.
