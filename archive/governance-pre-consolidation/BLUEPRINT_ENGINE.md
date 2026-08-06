# BLUEPRINT_ENGINE

**Status:** Phase 16A Deliverable 1.
**Location:** repo root.
**Phase:** 16A.

> The objective is not prediction. The objective is compilation.
> The system accepts an idea and produces an executable blueprint.
> — CEO directive, Phase 16A

---

## Purpose

The Blueprint Engine transforms an idea into a structured Blueprint
object. It is the entry point of the compilation pipeline. Per
Rule 3: "We are no longer building a chatbot. We are building a
compiler."

The Blueprint Engine does NOT generate ideas. It transforms ideas
that are input into structured objects that downstream engines
(Component, Constraint, World Model, etc.) can operate on.

---

## Input

```typescript
interface IdeaInput {
    title: string
    description: string
    objectives: string[]
    constraints: string[]
}
```

### Example

```json
{
  "title": "Autonomous farming robot",
  "description": "Solar-powered autonomous farming system",
  "objectives": [],
  "constraints": []
}
```

---

## Output

```typescript
interface BlueprintOutput {
    blueprintId: string
    feasibilityScore: number
    components: Component[]
    dependencies: Dependency[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `blueprintId` | string | yes | Unique identifier (BP-XXX). |
| `feasibilityScore` | float [0, 1] | yes | Composite score from downstream engines. 0 = infeasible; 1 = fully feasible. Computed from: classification confidence × instrument confidence × (1 - constraint severity) × economic viability. |
| `components` | Component[] | yes | From COMPONENT_ENGINE.md. The physical/logical components needed. |
| `dependencies` | Dependency[] | yes | From DEPENDENCY_GRAPH.md. The causal relationships between components. |

---

## Core Blueprint object (composite)

The full Blueprint (referenced by BLUEPRINT_ENGINE, assembled from
all downstream engines):

```typescript
interface Blueprint {
    id: string

    title: string

    summary: string

    classification: ClassificationResult[]

    stateVector: StateVector

    constraints: Constraint[]

    dependencies: Dependency[]

    components: Component[]

    simulations: Simulation[]

    regulations: Regulation[]

    economics: EconomicsModel

    manufacturing: ManufacturingModel

    executionPlan: ExecutionPlan

    riskModel: RiskModel
}
```

Each field is produced by a downstream engine:
- `classification` ← CLASSIFICATION_PROTOCOL.md
- `stateVector` ← WORLD_MODEL.md
- `constraints` ← CONSTRAINT_ENGINE.md
- `dependencies` ← DEPENDENCY_GRAPH.md
- `components` ← COMPONENT_ENGINE.md
- `simulations` ← SIMULATION_ENGINE.md
- `regulations` ← REGULATORY_ENGINE.md
- `economics` ← ECONOMIC_ENGINE.md
- `manufacturing` ← MANUFACTURING_ENGINE.md
- `executionPlan` ← EXECUTION_ENGINE.md
- `riskModel` ← (composite from all engines)

---

## Compilation pipeline

```
IdeaInput
    │
    ▼
┌──────────────────┐
│ BLUEPRINT_ENGINE │ ← entry point
│  (this document)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CLASSIFICATION   │ ← classify the idea's process
│ _PROTOCOL        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ WORLD_MODEL       │ ← estimate current state
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ COMPONENT_ENGINE │ ← break idea into components
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ DEPENDENCY_GRAPH │ ← build causal graph
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CONSTRAINT_ENGINE│ ← find obstacles
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SIMULATION_ENGINE│ ← can it work? be built? financed?
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ REGULATORY_ENGINE │ ← regulatory pathway
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ECONOMIC_ENGINE  │ ← economics model
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ MANUFACTURING    │ ← manufacturing plan
│ _ENGINE          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ EXECUTION_ENGINE │ ← execution plan
└────────┬─────────┘
         │
         ▼
    Blueprint
```

---

## What this engine does NOT do

- It does not generate ideas. Ideas are inputs.
- It does not predict. It compiles.
- It does not implement the downstream engines. It orchestrates them.
- It does not modify the frozen formula. INST-001 may be used during classification if the idea involves Emergence or Recombination.

---

## Pre-stated falsifier (EP-4)

**Claim:** The Blueprint schema captures all information needed to evaluate an idea's feasibility and produce an execution plan.

**Falsifier:** An idea whose Blueprint is complete (all fields populated) but that a decision-maker cannot evaluate — i.e., the Blueprint is missing a field needed for the decision.

**Status:** PENDING. No Blueprint has been compiled (no implementation).
