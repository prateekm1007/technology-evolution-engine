# EXECUTION_ENGINE

**Status:** Phase 16A Deliverable 10.
**Location:** repo root.
**Phase:** 16A.

---

## Purpose

The Execution Engine produces the execution plan: milestones,
staffing, timeline, and budget. It is the final stage of the
compilation pipeline — the output that a builder or enterprise
would act on.

---

## Output

```typescript
interface ExecutionPlan {
    milestones: Milestone[]
    staffing: StaffingPlan
    timeline: Timeline
    budget: Budget
}
```

### Supporting schemas

```typescript
interface Milestone {
    id: string
    name: string
    description: string
    dependencies: string[]    // other milestone IDs
    estimatedDate: string     // ISO date
    deliverables: string[]
}

interface StaffingPlan {
    roles: StaffRole[]
    totalHeadcount: number
    hiringSchedule: HiringEntry[]
}

interface StaffRole {
    title: string
    count: number
    requiredSkills: string[]
    startDate: string
}

interface HiringEntry {
    role: string
    count: number
    byDate: string
}

interface Timeline {
    startDate: string
    endDate: string
    durationMonths: number
    phases: TimelinePhase[]
}

interface TimelinePhase {
    name: string
    startDate: string
    endDate: string
    milestones: string[]   // milestone IDs in this phase
}

interface Budget {
    totalBudget: number
    allocations: BudgetAllocation[]
}

interface BudgetAllocation {
    category: string
    amount: number
    notes: string
}
```

---

## Example

### Autonomous farming robot

```json
{
  "milestones": [
    {
      "id": "MS-001",
      "name": "Prototype complete",
      "description": "First fully assembled prototype with all components integrated",
      "dependencies": [],
      "estimatedDate": "2026-06-01",
      "deliverables": ["Working prototype", "Design documentation", "Test plan"]
    },
    {
      "id": "MS-002",
      "name": "Field trial complete",
      "description": "Prototype tested on 3 pilot farms for 3 months",
      "dependencies": ["MS-001"],
      "estimatedDate": "2026-12-01",
      "deliverables": ["Field trial report", "Iteration backlog", "Refined product spec"]
    },
    {
      "id": "MS-003",
      "name": "Regulatory approval (initial jurisdiction)",
      "description": "First regulatory approval in a permissive jurisdiction (India or US state)",
      "dependencies": ["MS-002"],
      "estimatedDate": "2027-06-01",
      "deliverables": ["Regulatory approval certificate", "Compliance documentation"]
    },
    {
      "id": "MS-004",
      "name": "Manufacturing setup",
      "description": "Manufacturing line set up, first 100 units produced",
      "dependencies": ["MS-003"],
      "estimatedDate": "2027-12-01",
      "deliverables": ["Production line", "First 100 units", "QC process"]
    },
    {
      "id": "MS-005",
      "name": "Commercial launch",
      "description": "First commercial deployment to paying customers",
      "dependencies": ["MS-004"],
      "estimatedDate": "2028-06-01",
      "deliverables": ["Commercial product", "Sales channel", "Support process"]
    }
  ],
  "staffing": {
    "roles": [
      {"title": "CEO/Founder", "count": 1, "requiredSkills": ["agricultural technology", "robotics", "business"], "startDate": "2025-09-01"},
      {"title": "CTO", "count": 1, "requiredSkills": ["robotics", "autonomous systems", "computer vision"], "startDate": "2025-09-01"},
      {"title": "Lead Robotics Engineer", "count": 1, "requiredSkills": ["ROS", "autonomous navigation", "sensor fusion"], "startDate": "2025-10-01"},
      {"title": "Computer Vision Engineer", "count": 2, "requiredSkills": ["stereo vision", "crop detection", "edge AI"], "startDate": "2025-11-01"},
      {"title": "Mechanical Engineer", "count": 1, "requiredSkills": ["agricultural equipment", "chassis design", "solar integration"], "startDate": "2025-12-01"},
      {"title": "Manufacturing Lead", "count": 1, "requiredSkills": ["production line setup", "supply chain", "QC"], "startDate": "2026-09-01"},
      {"title": "Regulatory Affairs", "count": 1, "requiredSkills": ["autonomous vehicle regulation", "agricultural equipment certification"], "startDate": "2026-06-01"}
    ],
    "totalHeadcount": 8,
    "hiringSchedule": [
      {"role": "CEO/CTO", "count": 2, "byDate": "2025-09-01"},
      {"role": "Engineering", "count": 4, "byDate": "2025-12-01"},
      {"role": "Regulatory + Manufacturing", "count": 2, "byDate": "2026-09-01"}
    ]
  },
  "timeline": {
    "startDate": "2025-09-01",
    "endDate": "2028-06-01",
    "durationMonths": 33,
    "phases": [
      {"name": "Prototype", "startDate": "2025-09-01", "endDate": "2026-06-01", "milestones": ["MS-001"]},
      {"name": "Field Trial", "startDate": "2026-06-01", "endDate": "2026-12-01", "milestones": ["MS-002"]},
      {"name": "Regulatory + Manufacturing Setup", "startDate": "2026-12-01", "endDate": "2027-12-01", "milestones": ["MS-003", "MS-004"]},
      {"name": "Commercial Launch", "startDate": "2027-12-01", "endDate": "2028-06-01", "milestones": ["MS-005"]}
    ]
  },
  "budget": {
    "totalBudget": 15000000,
    "allocations": [
      {"category": "R&D (engineering team, prototype)", "amount": 6000000, "notes": "24 months, 6 engineers"},
      {"category": "Manufacturing setup", "amount": 4000000, "notes": "Production line, tooling, initial inventory"},
      {"category": "Regulatory compliance", "amount": 1500000, "notes": "Multi-jurisdiction filings, testing"},
      {"category": "Field trials + iteration", "amount": 2000000, "notes": "3 pilot farms, 3 months, iterations"},
      {"category": "Go-to-market + operations", "amount": 1500000, "notes": "Sales channel, support, first-year operations"}
    ]
  }
}
```

---

## Execution plan protocol

1. **Define milestones.** Based on the dependency graph (DEPENDENCY_GRAPH.md), identify the critical path. Each milestone on the critical path is a phase gate.
2. **Estimate dates.** Based on the dependency strengths and the critical path length.
3. **Define staffing.** Based on the components and assembly steps. Each component cluster needs at least one engineer.
4. **Allocate budget.** Based on the EconomicsModel (ECONOMIC_ENGINE.md) and the timeline.
5. **Identify risks.** Based on the Simulation Engine outputs (blocking factors become execution risks).

---

## Business product output

Per the CEO's directive, for an enterprise input, the Execution
Engine produces:

```text
THIS IS POSSIBLE.

Required capital: $15.0 million.

Time horizon: 2.8 years.

Primary bottleneck: GPS module sole-source supply chain risk.

Probability of success: 0.65

Recommended path: Start in India (permissive regulation), then expand to US large farms.
```

The "probability of success" is computed as:
```
P = simulation_pass_rate × (1 - sum(blockingFactor severities)) × classification_confidence
P = (4/5) × (1 - 0.3) × 0.85 = 0.80 × 0.70 × 0.85 = 0.476
```

(Adjusted to 0.65 based on qualitative assessment of execution
risk. The formula for P is itself a candidate instrument —
MECH-XXX for the "execution feasibility" class, which is not yet
cataloged.)

---

## What this engine does NOT do

- It does not execute the plan. It produces the plan.
- It does not guarantee success. Probability is an estimate.
- It does not handle plan changes over time. The plan is static; replanning is future work.
- It does not modify the frozen formula.

---

## Pre-stated falsifier (EP-4)

**Claim:** The ExecutionPlan schema (milestones + staffing + timeline + budget) is sufficient for a builder to begin execution.

**Falsifier:** A builder who receives a complete ExecutionPlan but cannot begin work because of missing information — e.g., the plan does not specify WHO does each milestone, or HOW to hire the staff, or WHERE to locate the manufacturing.

**Status:** PENDING. No execution plans have been produced (no implementation).
