# SIMULATION_ENGINE

**Status:** Phase 16A Deliverable 9.
**Location:** repo root.
**Phase:** 16A.

---

## Purpose

The Simulation Engine answers five questions about an idea:

```text
Can it work?

Can it be built?

Can it be financed?

Can it be regulated?

Can it be scaled?
```

Each question is answered by running the appropriate downstream
engines and synthesizing their outputs into a simulation result.

---

## Schema

```typescript
interface Simulation {
    question: "CAN_WORK" | "CAN_BUILD" | "CAN_FINANCE" | "CAN_REGULATE" | "CAN_SCALE"
    answer: boolean
    confidence: number
    evidence: string[]
    blockingFactors: string[]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|---|---|---|---|
| `question` | enum | yes | One of the 5 questions. |
| `answer` | boolean | yes | true = yes; false = no. |
| `confidence` | float [0, 1] | yes | Confidence in the answer. 0 = uncertain; 1 = certain. |
| `evidence` | string[] | yes | The evidence supporting the answer. Cites specific engine outputs. |
| `blockingFactors` | string[] | yes | If answer is false, what blocks it. If answer is true, what would need to be true for it to remain true. |

---

## The five simulations

### Simulation 1: CAN_WORK

**Question:** Can the idea function physically and logically?

**Inputs:**
- COMPONENT_ENGINE: components and their maturity
- DEPENDENCY_GRAPH: causal relationships
- WORLD_MODEL: scientific and technological state

**Protocol:**
1. Check if all components have maturity ≥ 0.5 (TRL ≥ 4.5).
2. Check if the dependency graph is acyclic (valid DAG).
3. Check if the scientific state supports the required physics.
4. If all checks pass: answer = true. If any fails: answer = false, blockingFactors = failed checks.

### Simulation 2: CAN_BUILD

**Question:** Can the idea be manufactured at the required quality and scale?

**Inputs:**
- MANUFACTURING_ENGINE: manufacturing plan, suppliers, tolerances
- COMPONENT_ENGINE: component alternatives
- WORLD_MODEL: manufacturing state

**Protocol:**
1. Check if all materials have suppliers (no sole-source without alternative).
2. Check if all tolerances are achievable (manufacturing state ≥ required tolerance difficulty).
3. Check if yield is ≥ 90% (estimated from tolerance complexity).
4. If all checks pass: answer = true. If any fails: answer = false.

### Simulation 3: CAN_FINANCE

**Question:** Can the idea be financed to break-even?

**Inputs:**
- ECONOMIC_ENGINE: capital requirement, break-even period
- WORLD_MODEL: economic state
- CONSTRAINT_ENGINE: capital constraints

**Protocol:**
1. Check if capitalRequirement is ≤ available capital (from economic state).
2. Check if breakEvenPeriod ≤ market window (from constraint engine, TIME constraint).
3. Check if expectedRevenue > operatingCost (positive unit economics).
4. If all checks pass: answer = true. If any fails: answer = false.

### Simulation 4: CAN_REGULATE

**Question:** Can the idea achieve regulatory approval?

**Inputs:**
- REGULATORY_ENGINE: jurisdictions, authorities, requirements, risks
- WORLD_MODEL: regulatory state
- CONSTRAINT_ENGINE: regulatory constraints

**Protocol:**
1. For each Regulation with risk > 0.7: flag as blocking.
2. Check if the regulatory state supports the required pathway.
3. If no blocking regulations: answer = true. If any blocking: answer = false.

### Simulation 5: CAN_SCALE

**Question:** Can the idea scale to market-relevant volume?

**Inputs:**
- MANUFACTURING_ENGINE: assembly steps, throughput
- ECONOMIC_ENGINE: unit cost at scale
- WORLD_MODEL: infrastructure state
- CONSTRAINT_ENGINE: infrastructure constraints

**Protocol:**
1. Check if manufacturing throughput can meet market demand.
2. Check if unit cost at scale is ≤ willingness-to-pay.
3. Check if infrastructure state supports deployment (e.g., charging stations, cell towers).
4. If all checks pass: answer = true. If any fails: answer = false.

---

## Example

### Autonomous farming robot

```json
[
  {
    "question": "CAN_WORK",
    "answer": true,
    "confidence": 0.85,
    "evidence": [
      "All components have maturity ≥ 0.8 (TRL ≥ 7.2)",
      "Dependency graph is acyclic",
      "Scientific state 0.9 supports autonomous navigation and solar power"
    ],
    "blockingFactors": []
  },
  {
    "question": "CAN_BUILD",
    "answer": true,
    "confidence": 0.7,
    "evidence": [
      "All materials have suppliers (GPS module is sole-source but available)",
      "Tolerances are achievable with standard agricultural equipment manufacturing",
      "Estimated yield ≥ 95% (tolerances are not tight)"
    ],
    "blockingFactors": ["GPS module sole-source (Trimble/u-blox) — supply chain risk"]
  },
  {
    "question": "CAN_FINANCE",
    "answer": true,
    "confidence": 0.6,
    "evidence": [
      "Capital requirement $15M is within agricultural robotics VC range",
      "Break-even 2.1 years is within market window (5 years)",
      "Unit economics positive: $12K revenue > $5K operating cost"
    ],
    "blockingFactors": ["Break-even assumes 1000 units/year — requires aggressive market entry"]
  },
  {
    "question": "CAN_REGULATE",
    "answer": true,
    "confidence": 0.5,
    "evidence": [
      "US states: autonomous vehicle permits available (varies by state, risk 0.6)",
      "EU: CE marking + Machinery Directive achievable (risk 0.5)",
      "India: permissive regulatory environment (risk 0.1)"
    ],
    "blockingFactors": ["US state-by-state permitting adds complexity", "EPA certification if pesticide application"]
  },
  {
    "question": "CAN_SCALE",
    "answer": false,
    "confidence": 0.7,
    "evidence": [
      "Manufacturing throughput feasible for 10K units/year",
      "Unit cost $45K is above small-farm willingness-to-pay ($20-30K range)",
      "Rural infrastructure (cellular, power) is adequate but not universal"
    ],
    "blockingFactors": ["Unit cost too high for small farms — leasing model required", "Rural cellular coverage gaps limit fleet coordination"]
  }
]
```

**Overall feasibility:** 4 of 5 simulations pass. CAN_SCALE is the
blocking factor. The idea is feasible for large farms but not for
small farms without a leasing model.

---

## What this engine does NOT do

- It does not run actual physics simulations. It checks component maturity and dependency validity.
- It does not guarantee success. It estimates feasibility based on available evidence.
- It does not handle uncertainty in inputs. Each simulation uses point estimates; Monte Carlo simulation is future work.
- It does not modify the frozen formula.

---

## Pre-stated falsifier (EP-4)

**Claim:** The 5 questions (CAN_WORK, CAN_BUILD, CAN_FINANCE, CAN_REGULATE, CAN_SCALE) cover all dimensions of feasibility.

**Falsifier:** A feasibility question that is not covered by any of the 5 — e.g., "Can it be marketed?" or "Can it be insured?" or "Can it be maintained?"

**Status:** PENDING. The 5 questions may need extension. Marketing, insurance, and maintenance are candidate sixth/seventh/eighth questions.
